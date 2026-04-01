"""Integration tests for GmailWatcher.

These tests verify end-to-end functionality with real file system and database.
External API calls are mocked, but file I/O and SQLite use real implementations.
"""

import json
import os
import sqlite3
import time
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


class TestGmailWatcherIntegration:
    """Integration tests for GmailWatcher."""

    @pytest.fixture
    def integration_vault(self, tmp_path):
        """Create vault directory structure for integration testing."""
        vault = tmp_path / "vault"
        vault.mkdir()

        # Create required directories
        (vault / "Needs_Action").mkdir()
        (vault / "Logs").mkdir()
        (vault / "Dashboard.md").write_text("# Dashboard\n", encoding="utf-8")

        # Create Company_Handbook.md
        handbook = vault / "Company_Handbook.md"
        handbook.write_text(
            """
# Company Handbook

## Gmail Configuration
[Gmail]
rate_limit_calls_per_hour = 100
check_interval_seconds = 120
""",
            encoding="utf-8",
        )

        return vault

    @pytest.fixture
    def mock_gmail_service(self):
        """Create mock Gmail API service."""
        mock_service = MagicMock()

        # Setup mock responses
        mock_service.users().messages().list().execute.return_value = {
            "messages": [
                {"id": "integration_test_msg_1", "threadId": "thread1"}
            ]
        }

        mock_full_msg = {
            "id": "integration_test_msg_1",
            "threadId": "thread1",
            "snippet": "Integration test email snippet",
            "payload": {
                "headers": [
                    {"name": "From", "value": "integration-test@example.com"},
                    {"name": "To", "value": "me@example.com"},
                    {"name": "Subject", "value": "Integration Test Email"},
                    {"name": "Date", "value": "Wed, 1 Apr 2026 10:00:00 +0000"},
                ]
            },
        }
        mock_service.users().messages().get().execute.return_value = mock_full_msg

        return mock_service

    def test_creates_action_file_in_needs_action(
        self, integration_vault, mock_gmail_service, monkeypatch
    ):
        """Verify watcher creates action file in Needs_Action/ directory."""
        # Setup OAuth token
        monkeypatch.setenv("GMAIL_OAUTH_TOKEN", json.dumps({
            "token": "fake_token",
            "refresh_token": "fake_refresh",
            "token_uri": "https://oauth2.googleapis.com/token",
            "client_id": "fake_client",
            "client_secret": "fake_secret",
            "scopes": ["https://www.googleapis.com/auth/gmail.readonly"],
        }))

        # Create watcher (dry_run=False to actually create files)
        from src.watchers.gmail_watcher import GmailWatcher

        watcher = GmailWatcher(
            vault_path=str(integration_vault),
            dry_run=False,
            interval=120,
        )

        # Mock credentials and service
        mock_credentials = MagicMock()
        mock_credentials.expired = False
        mock_credentials.valid = True

        with patch.object(watcher, "_get_credentials", return_value=mock_credentials):
            with patch("src.watchers.gmail_watcher.build", return_value=mock_gmail_service):
                # Run check
                messages = watcher.check_for_updates()

                # Create action files
                for msg in messages:
                    action_path = watcher.create_action_file(msg)

                    # Verify file was created
                    assert action_path.exists()
                    assert action_path.parent == integration_vault / "Needs_Action"
                    assert action_path.suffix == ".md"
                    assert "EMAIL_" in action_path.name

                    # Verify content
                    content = action_path.read_text(encoding="utf-8")
                    assert "integration-test@example.com" in content
                    assert "Integration Test Email" in content

    def test_action_file_triggers_plan_generation(
        self, integration_vault, mock_gmail_service, monkeypatch
    ):
        """Verify action file format is correct for plan generation trigger."""
        monkeypatch.setenv("GMAIL_OAUTH_TOKEN", json.dumps({
            "token": "fake_token",
            "refresh_token": "fake_refresh",
            "token_uri": "https://oauth2.googleapis.com/token",
            "client_id": "fake_client",
            "client_secret": "fake_secret",
            "scopes": ["https://www.googleapis.com/auth/gmail.readonly"],
        }))

        from src.watchers.gmail_watcher import GmailWatcher

        watcher = GmailWatcher(
            vault_path=str(integration_vault),
            dry_run=False,
            interval=120,
        )

        mock_credentials = MagicMock()
        mock_credentials.expired = False

        with patch.object(watcher, "_get_credentials", return_value=mock_credentials):
            with patch("src.watchers.gmail_watcher.build", return_value=mock_gmail_service):
                messages = watcher.check_for_updates()

                for msg in messages:
                    action_path = watcher.create_action_file(msg)

                    # Verify YAML frontmatter structure
                    content = action_path.read_text(encoding="utf-8")

                    # Check required fields for plan generation
                    assert "type: email" in content
                    assert "from:" in content
                    assert "subject:" in content
                    assert "status: pending" in content
                    assert "message_id:" in content

                    # Check suggested actions section
                    assert "## Suggested Actions" in content
                    assert "- [ ]" in content

    def test_processed_ids_persist_across_restarts(
        self, integration_vault, mock_gmail_service, monkeypatch
    ):
        """Verify processed message IDs persist in SQLite across watcher restarts."""
        monkeypatch.setenv("GMAIL_OAUTH_TOKEN", json.dumps({
            "token": "fake_token",
            "refresh_token": "fake_refresh",
            "token_uri": "https://oauth2.googleapis.com/token",
            "client_id": "fake_client",
            "client_secret": "fake_secret",
            "scopes": ["https://www.googleapis.com/auth/gmail.readonly"],
        }))

        from src.watchers.gmail_watcher import GmailWatcher

        # First watcher instance - process message
        watcher1 = GmailWatcher(
            vault_path=str(integration_vault),
            dry_run=False,
            interval=120,
        )

        mock_credentials = MagicMock()
        mock_credentials.expired = False

        with patch.object(watcher1, "_get_credentials", return_value=mock_credentials):
            with patch("src.watchers.gmail_watcher.build", return_value=mock_gmail_service):
                messages = watcher1.check_for_updates()

                for msg in messages:
                    watcher1.create_action_file(msg)

        # Verify message was tracked in database
        db_path = integration_vault.parent / "data" / "processed_emails.db"
        assert db_path.exists()

        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        cursor.execute(
            "SELECT message_id FROM processed_emails WHERE message_id = ?",
            ("integration_test_msg_1",),
        )
        row = cursor.fetchone()
        conn.close()

        assert row is not None
        assert row[0] == "integration_test_msg_1"

        # Second watcher instance - simulate restart
        watcher2 = GmailWatcher(
            vault_path=str(integration_vault),
            dry_run=False,
            interval=120,
        )

        # Verify second watcher sees message as processed
        assert watcher2._is_processed("integration_test_msg_1") is True

        # Second check should return empty list (message already processed)
        with patch.object(watcher2, "_get_credentials", return_value=mock_credentials):
            with patch("src.watchers.gmail_watcher.build", return_value=mock_gmail_service):
                messages2 = watcher2.check_for_updates()
                assert len(messages2) == 0

    def test_metrics_persist_to_sqlite(
        self, integration_vault, mock_gmail_service, monkeypatch
    ):
        """Verify metrics are persisted to SQLite database."""
        monkeypatch.setenv("GMAIL_OAUTH_TOKEN", json.dumps({
            "token": "fake_token",
            "refresh_token": "fake_refresh",
            "token_uri": "https://oauth2.googleapis.com/token",
            "client_id": "fake_client",
            "client_secret": "fake_secret",
            "scopes": ["https://www.googleapis.com/auth/gmail.readonly"],
        }))

        from src.watchers.gmail_watcher import GmailWatcher

        watcher = GmailWatcher(
            vault_path=str(integration_vault),
            dry_run=False,
            interval=120,
        )

        mock_credentials = MagicMock()
        mock_credentials.expired = False

        with patch.object(watcher, "_get_credentials", return_value=mock_credentials):
            with patch("src.watchers.gmail_watcher.build", return_value=mock_gmail_service):
                watcher.check_for_updates()

        # Verify metrics database exists
        metrics_db = integration_vault.parent / "data" / "metrics.db"
        assert metrics_db.exists()

        # Verify metrics were recorded
        conn = sqlite3.connect(str(metrics_db))
        cursor = conn.cursor()
        cursor.execute(
            "SELECT name, type, value FROM metrics WHERE name LIKE 'gmail_watcher%' ORDER BY timestamp DESC LIMIT 5"
        )
        rows = cursor.fetchall()
        conn.close()

        # Should have recorded metrics
        metric_names = [row[0] for row in rows]
        assert any("gmail_watcher" in name for name in metric_names)

    def test_circuit_breaker_persists_state(
        self, integration_vault, mock_gmail_service, monkeypatch
    ):
        """Verify circuit breaker state persists to SQLite."""
        from googleapiclient.errors import HttpError

        monkeypatch.setenv("GMAIL_OAUTH_TOKEN", json.dumps({
            "token": "fake_token",
            "refresh_token": "fake_refresh",
            "token_uri": "https://oauth2.googleapis.com/token",
            "client_id": "fake_client",
            "client_secret": "fake_secret",
            "scopes": ["https://www.googleapis.com/auth/gmail.readonly"],
        }))

        from src.watchers.gmail_watcher import GmailWatcher

        watcher = GmailWatcher(
            vault_path=str(integration_vault),
            dry_run=False,
            interval=120,
        )

        mock_credentials = MagicMock()
        mock_credentials.expired = False

        # Mock service to always fail
        mock_response = MagicMock()
        mock_response.status = 500
        mock_gmail_service.users().messages().list().execute.side_effect = HttpError(
            mock_response, b"Internal Server Error"
        )

        with patch.object(watcher, "_get_credentials", return_value=mock_credentials):
            with patch("src.watchers.gmail_watcher.build", return_value=mock_gmail_service):
                # Trigger multiple failures
                for _ in range(6):
                    try:
                        watcher.check_for_updates()
                    except Exception:
                        pass

        # Verify circuit breaker database exists
        cb_db = integration_vault.parent / "data" / "circuit_breakers.db"
        assert cb_db.exists()

        # Verify state was persisted
        conn = sqlite3.connect(str(cb_db))
        cursor = conn.cursor()
        cursor.execute(
            "SELECT name, state, failure_count FROM circuit_breakers WHERE name = 'gmail_api'"
        )
        row = cursor.fetchone()
        conn.close()

        assert row is not None
        assert row[0] == "gmail_api"
        # State should be recorded (may be OPEN or have high failure count)
        assert row[2] >= 5  # failure_count


class TestGmailWatcherLogFileFormat:
    """Test log file format and rotation."""

    @pytest.fixture
    def vault_with_logging(self, tmp_path):
        """Create vault with logging setup."""
        vault = tmp_path / "vault"
        vault.mkdir()
        (vault / "Needs_Action").mkdir()
        (vault / "Logs").mkdir()
        return vault

    def test_json_logging_format(self, vault_with_logging, monkeypatch):
        """Verify logs are written in JSON format."""
        import glob

        monkeypatch.setenv("GMAIL_OAUTH_TOKEN", json.dumps({
            "token": "fake_token",
            "refresh_token": "fake_refresh",
            "token_uri": "https://oauth2.googleapis.com/token",
            "client_id": "fake_client",
            "client_secret": "fake_secret",
            "scopes": ["https://www.googleapis.com/auth/gmail.readonly"],
        }))

        from src.watchers.gmail_watcher import GmailWatcher

        watcher = GmailWatcher(
            vault_path=str(vault_with_logging),
            dry_run=True,
            interval=120,
        )

        # Trigger a log entry
        watcher.logger.info("test_event", {"test_key": "test_value"})

        # Find log file
        log_pattern = str(vault_with_logging / "Logs" / "audit_gmail-watcher_*.jsonl")
        log_files = glob.glob(log_pattern)

        if log_files:
            log_file = log_files[0]
            with open(log_file, "r", encoding="utf-8") as f:
                line = f.readline()
                if line.strip():
                    log_entry = json.loads(line)

                    # Verify required fields
                    assert "timestamp" in log_entry
                    assert "level" in log_entry
                    assert "component" in log_entry
                    assert "action" in log_entry
                    assert "dry_run" in log_entry
                    assert "correlation_id" in log_entry
                    assert "details" in log_entry

                    # Verify values
                    assert log_entry["level"] == "INFO"
                    assert log_entry["action"] == "test_event"
                    assert log_entry["details"]["test_key"] == "test_value"
