"""Unit tests for GmailWatcher class."""

import json
import os
import sqlite3
import time
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from src.metrics.collector import MetricsCollector
from src.utils.circuit_breaker import PersistentCircuitBreaker
from src.watchers.gmail_watcher import (
    GmailRateLimitExceededError,
    GmailSessionExpiredError,
    GmailWatcher,
)


class TestGmailWatcher:
    """Unit tests for GmailWatcher."""

    @pytest.fixture
    def tmp_vault(self, tmp_path):
        """Create temporary vault directory."""
        vault = tmp_path / "vault"
        vault.mkdir()
        (vault / "Needs_Action").mkdir()
        (vault / "Logs").mkdir()
        (vault / "Dashboard.md").write_text("# Dashboard\n", encoding="utf-8")
        return vault

    @pytest.fixture
    def mock_credentials(self):
        """Mock OAuth2 credentials."""
        creds = MagicMock()
        creds.expired = False
        creds.valid = True
        return creds

    @pytest.fixture
    def gmail_watcher(self, tmp_vault, monkeypatch):
        """Create GmailWatcher instance with mocked dependencies."""
        monkeypatch.setenv("GMAIL_OAUTH_TOKEN", json.dumps({
            "token": "fake_token",
            "refresh_token": "fake_refresh",
            "token_uri": "https://oauth2.googleapis.com/token",
            "client_id": "fake_client",
            "client_secret": "fake_secret",
            "scopes": ["https://www.googleapis.com/auth/gmail.readonly"],
        }))

        watcher = GmailWatcher(
            vault_path=str(tmp_vault),
            dry_run=True,
            interval=120,
        )
        return watcher

    def test_check_returns_unread_important(
        self, gmail_watcher, mock_credentials, monkeypatch
    ):
        """Verify check_for_updates returns only unread and important messages."""
        # Mock Gmail API
        mock_messages = [
            {"id": "msg1", "threadId": "thread1"},
            {"id": "msg2", "threadId": "thread2"},
        ]
        
        # Create mock service with proper side effect for get()
        mock_service = MagicMock()
        mock_service.users().messages().list().execute.return_value = {
            "messages": mock_messages
        }

        # Mock full message responses - use call_args to track which message is being fetched
        call_order = {"count": 0}
        
        def get_message(*args, **kwargs):
            call_order["count"] += 1
            if call_order["count"] == 1:
                return {
                    "id": "msg1",
                    "threadId": "thread1",
                    "snippet": "Test snippet 1",
                    "payload": {
                        "headers": [
                            {"name": "From", "value": "sender@example.com"},
                            {"name": "To", "value": "me@example.com"},
                            {"name": "Subject", "value": "Test Subject"},
                            {"name": "Date", "value": "2026-04-01T10:00:00Z"},
                        ]
                    },
                }
            else:
                return {
                    "id": "msg2",
                    "threadId": "thread2",
                    "snippet": "Test snippet 2",
                    "payload": {
                        "headers": [
                            {"name": "From", "value": "sender2@example.com"},
                            {"name": "To", "value": "me@example.com"},
                            {"name": "Subject", "value": "Test Subject 2"},
                            {"name": "Date", "value": "2026-04-01T11:00:00Z"},
                        ]
                    },
                }

        mock_service.users().messages().get().execute.side_effect = get_message

        # Mock credentials and build
        monkeypatch.setattr(gmail_watcher, "_get_credentials", lambda: mock_credentials)

        with patch("src.watchers.gmail_watcher.build", return_value=mock_service):
            result = gmail_watcher._check_for_updates_impl()

        # Verify results - both messages should be returned
        assert len(result) == 2
        
        # Verify message IDs are present (order may vary)
        message_ids = [msg["message_id"] for msg in result]
        assert "msg1" in message_ids
        assert "msg2" in message_ids
        
        # Verify API was called with correct query (at least once)
        mock_service.users().messages().list.assert_called_with(
            userId="me", q="is:unread is:important", maxResults=10
        )

    def test_filters_processed_ids(self, gmail_watcher, mock_credentials, monkeypatch, tmp_vault):
        """Verify already processed message IDs are filtered out."""
        # Add message to processed DB
        db_path = tmp_vault.parent / "data" / "processed_emails.db"
        db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO processed_emails (message_id) VALUES (?)",
            ("msg1",),
        )
        conn.commit()
        conn.close()

        # Mock Gmail API returning already processed message
        mock_service = MagicMock()
        mock_service.users().messages().list().execute.return_value = {
            "messages": [{"id": "msg1", "threadId": "thread1"}]
        }

        monkeypatch.setattr(gmail_watcher, "_get_credentials", lambda: mock_credentials)

        with patch("src.watchers.gmail_watcher.build", return_value=mock_service):
            result = gmail_watcher._check_for_updates_impl()

        # Should return empty list (all messages already processed)
        assert len(result) == 0

    def test_action_file_format(self, gmail_watcher, tmp_vault, monkeypatch):
        """Verify action file format matches spec.md Appendix A."""
        message_data = {
            "message_id": "test_msg_123",
            "from": "sender@example.com",
            "to": "me@example.com",
            "subject": "Test Subject",
            "date": "2026-04-01T10:00:00Z",
            "snippet": "Test snippet",
        }

        # Create action file
        gmail_watcher.dry_run = False
        action_path = gmail_watcher.create_action_file(message_data)

        # Verify file exists
        assert action_path.exists()
        assert action_path.parent == tmp_vault / "Needs_Action"
        assert action_path.suffix == ".md"
        assert action_path.name.startswith("EMAIL_")

        # Verify content
        content = action_path.read_text(encoding="utf-8")

        # Check YAML frontmatter
        assert "---" in content
        assert "type: email" in content
        assert "from: sender@example.com" in content
        assert "to: me@example.com" in content
        assert "subject: Test Subject" in content
        assert "priority: high" in content
        assert "status: pending" in content
        assert "message_id: test_msg_123" in content

        # Check suggested actions section
        assert "## Suggested Actions" in content
        assert "- [ ]" in content

    def test_header_extraction(self, gmail_watcher, mock_credentials, monkeypatch):
        """Verify email headers are correctly extracted."""
        mock_service = MagicMock()
        mock_service.users().messages().list().execute.return_value = {
            "messages": [{"id": "msg1", "threadId": "thread1"}]
        }

        mock_full_msg = {
            "id": "msg1",
            "threadId": "thread1",
            "snippet": "Test snippet",
            "payload": {
                "headers": [
                    {"name": "From", "value": "sender@example.com"},
                    {"name": "To", "value": "me@example.com"},
                    {"name": "Subject", "value": "Test Subject"},
                    {"name": "Date", "value": "Wed, 1 Apr 2026 10:00:00 +0000"},
                ]
            },
        }
        mock_service.users().messages().get().execute.return_value = mock_full_msg

        monkeypatch.setattr(gmail_watcher, "_get_credentials", lambda: mock_credentials)

        with patch("src.watchers.gmail_watcher.build", return_value=mock_service):
            result = gmail_watcher._check_for_updates_impl()

        assert len(result) == 1
        assert result[0]["from"] == "sender@example.com"
        assert result[0]["to"] == "me@example.com"
        assert result[0]["subject"] == "Test Subject"
        assert "1 Apr 2026" in result[0]["date"]

    def test_session_expiry(self, gmail_watcher, mock_credentials, monkeypatch):
        """Verify OAuth2 session expiry is detected and handled."""
        from google.auth.exceptions import RefreshError
        from googleapiclient.errors import HttpError

        # Mock HTTP 401 error (unauthorized)
        mock_response = MagicMock()
        mock_response.status = 401

        mock_service = MagicMock()
        mock_service.users().messages().list().execute.side_effect = HttpError(
            mock_response, b"Unauthorized"
        )

        monkeypatch.setattr(gmail_watcher, "_get_credentials", lambda: mock_credentials)

        with patch("src.watchers.gmail_watcher.build", return_value=mock_service):
            with pytest.raises(GmailSessionExpiredError):
                gmail_watcher._check_for_updates_impl()

    def test_quota_exceeded_backoff(self, gmail_watcher, mock_credentials, monkeypatch):
        """Verify rate limiting is enforced."""
        from googleapiclient.errors import HttpError

        # Mock HTTP 429 error (rate limit exceeded)
        mock_response = MagicMock()
        mock_response.status = 429

        mock_service = MagicMock()
        mock_service.users().messages().list().execute.side_effect = HttpError(
            mock_response, b"Rate Limit Exceeded"
        )

        monkeypatch.setattr(gmail_watcher, "_get_credentials", lambda: mock_credentials)

        with patch("src.watchers.gmail_watcher.build", return_value=mock_service):
            with pytest.raises(GmailRateLimitExceededError):
                gmail_watcher._check_for_updates_impl()

    def test_network_failure_retry(self, gmail_watcher, mock_credentials, monkeypatch):
        """Verify network failures are handled gracefully."""
        mock_service = MagicMock()
        mock_service.users().messages().list().execute.side_effect = Exception(
            "Network error"
        )

        monkeypatch.setattr(gmail_watcher, "_get_credentials", lambda: mock_credentials)

        with patch("src.watchers.gmail_watcher.build", return_value=mock_service):
            with pytest.raises(Exception):
                gmail_watcher._check_for_updates_impl()

    def test_circuit_breaker_trips(self, gmail_watcher, mock_credentials, monkeypatch):
        """Verify circuit breaker trips after consecutive failures."""
        from googleapiclient.errors import HttpError
        import sqlite3

        # Mock consistent failures
        mock_response = MagicMock()
        mock_response.status = 500

        mock_service = MagicMock()
        mock_service.users().messages().list().execute.side_effect = HttpError(
            mock_response, b"Internal Server Error"
        )

        monkeypatch.setattr(gmail_watcher, "_get_credentials", lambda: mock_credentials)

        # Create a fresh circuit breaker for this test (bypass global registry)
        from src.utils.circuit_breaker import PersistentCircuitBreaker
        import tempfile
        import os
        
        # Use temp database for test isolation
        tmpdir = tempfile.mkdtemp()
        temp_db = os.path.join(tmpdir, "test_circuit_breaker.db")
        test_breaker = PersistentCircuitBreaker(
            name="test_gmail_api",
            failure_threshold=5,
            recovery_timeout=60,
            db_path=temp_db,
        )
        
        # Replace watcher's circuit breaker
        gmail_watcher.circuit_breaker = test_breaker

        try:
            with patch("src.watchers.gmail_watcher.build", return_value=mock_service):
                # Trigger multiple failures using check_for_updates (which wraps with circuit breaker)
                exceptions_raised = 0
                for i in range(6):
                    try:
                        result = gmail_watcher.check_for_updates()
                    except Exception as e:
                        exceptions_raised += 1

                # Verify circuit breaker is now open or has high failure count
                is_open = test_breaker.is_open()
                failure_count = test_breaker.failure_count
                
                # At least one of these should be true (circuit opens after 5 failures)
                assert is_open or failure_count >= 5, f"Circuit breaker not tripped: is_open={is_open}, failure_count={failure_count}"
        finally:
            # Clean up: close SQLite connections and remove temp files
            import shutil
            # Force close any SQLite connections by garbage collecting
            import gc
            gc.collect()
            # Remove temp directory (ignore errors on Windows)
            shutil.rmtree(tmpdir, ignore_errors=True)

    def test_metrics_emitted(self, gmail_watcher, mock_credentials, monkeypatch):
        """Verify metrics are emitted during check."""
        mock_service = MagicMock()
        mock_service.users().messages().list().execute.return_value = {
            "messages": [{"id": "msg1", "threadId": "thread1"}]
        }

        mock_full_msg = {
            "id": "msg1",
            "threadId": "thread1",
            "snippet": "Test",
            "payload": {
                "headers": [
                    {"name": "From", "value": "sender@example.com"},
                    {"name": "To", "value": "me@example.com"},
                    {"name": "Subject", "value": "Test"},
                    {"name": "Date", "value": "2026-04-01T10:00:00Z"},
                ]
            },
        }
        mock_service.users().messages().get().execute.return_value = mock_full_msg

        monkeypatch.setattr(gmail_watcher, "_get_credentials", lambda: mock_credentials)

        # Mock metrics collector
        mock_collector = MagicMock(spec=MetricsCollector)
        gmail_watcher.metrics = mock_collector

        with patch("src.watchers.gmail_watcher.build", return_value=mock_service):
            gmail_watcher._check_for_updates_impl()

        # Verify metrics were recorded
        assert mock_collector.record_histogram.called
        assert mock_collector.increment_counter.called

        # Check specific metrics
        calls = [call[0][0] for call in mock_collector.record_histogram.call_args_list]
        assert "gmail_watcher_check_duration" in calls

    def test_rate_limiting(self, gmail_watcher, monkeypatch):
        """Verify rate limiting is enforced."""
        # Set very low rate limit for testing
        gmail_watcher._rate_limit_max = 2
        gmail_watcher._rate_limit_calls = []

        # First two calls should succeed
        assert gmail_watcher._check_rate_limit() is True
        assert gmail_watcher._check_rate_limit() is True

        # Third call should fail (rate limited)
        assert gmail_watcher._check_rate_limit() is False

    def test_empty_returns_list(self, gmail_watcher, mock_credentials, monkeypatch):
        """Verify empty list returned when no new messages."""
        mock_service = MagicMock()
        mock_service.users().messages().list().execute.return_value = {
            "messages": []
        }

        monkeypatch.setattr(gmail_watcher, "_get_credentials", lambda: mock_credentials)

        with patch("src.watchers.gmail_watcher.build", return_value=mock_service):
            result = gmail_watcher._check_for_updates_impl()

        assert result == []
        assert isinstance(result, list)


class TestGmailWatcherProcessedEmailsDB:
    """Tests for processed emails database."""

    @pytest.fixture
    def tmp_vault(self, tmp_path):
        """Create temporary vault directory."""
        vault = tmp_path / "vault"
        vault.mkdir()
        return vault

    def test_track_processed(self, tmp_vault, monkeypatch):
        """Verify _track_processed inserts message ID."""
        monkeypatch.setenv("GMAIL_OAUTH_TOKEN", json.dumps({
            "token": "fake",
            "refresh_token": "fake",
            "token_uri": "https://oauth2.googleapis.com/token",
            "client_id": "fake",
            "client_secret": "fake",
            "scopes": [],
        }))

        watcher = GmailWatcher(vault_path=str(tmp_vault), dry_run=True)

        # Track a message
        watcher._track_processed("test_msg_123", "/path/to/action.md")

        # Verify in database
        conn = watcher._get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT message_id, action_file FROM processed_emails WHERE message_id = ?",
            ("test_msg_123",),
        )
        row = cursor.fetchone()
        conn.close()

        assert row is not None
        assert row[0] == "test_msg_123"
        assert row[1] == "/path/to/action.md"

    def test_is_processed(self, tmp_vault, monkeypatch):
        """Verify _is_processed returns correct value."""
        monkeypatch.setenv("GMAIL_OAUTH_TOKEN", json.dumps({
            "token": "fake",
            "refresh_token": "fake",
            "token_uri": "https://oauth2.googleapis.com/token",
            "client_id": "fake",
            "client_secret": "fake",
            "scopes": [],
        }))

        watcher = GmailWatcher(vault_path=str(tmp_vault), dry_run=True)

        # Add message to DB
        watcher._track_processed("test_msg_456")

        # Verify is_processed returns True
        assert watcher._is_processed("test_msg_456") is True

        # Verify is_processed returns False for unknown message
        assert watcher._is_processed("unknown_msg") is False


class TestGmailWatcherRateLimiting:
    """Tests for rate limiting functionality."""

    @pytest.fixture
    def tmp_vault(self, tmp_path):
        """Create temporary vault directory."""
        vault = tmp_path / "vault"
        vault.mkdir()
        return vault

    def test_rate_limit_config_loaded(self, tmp_vault, monkeypatch):
        """Verify rate limit is loaded from Company_Handbook.md."""
        # Create Company_Handbook.md with rate limit
        handbook = tmp_vault / "Company_Handbook.md"
        handbook.write_text(
            """
# Company Handbook

[Gmail]
rate_limit_calls_per_hour = 50
""",
            encoding="utf-8",
        )

        monkeypatch.setenv("GMAIL_OAUTH_TOKEN", json.dumps({
            "token": "fake",
            "refresh_token": "fake",
            "token_uri": "https://oauth2.googleapis.com/token",
            "client_id": "fake",
            "client_secret": "fake",
            "scopes": [],
        }))

        watcher = GmailWatcher(vault_path=str(tmp_vault), dry_run=True)

        # Verify rate limit was loaded
        assert watcher._rate_limit_max == 50

    def test_rate_limit_window_cleanup(self, tmp_vault, monkeypatch):
        """Verify old rate limit calls are cleaned up."""
        monkeypatch.setenv("GMAIL_OAUTH_TOKEN", json.dumps({
            "token": "fake",
            "refresh_token": "fake",
            "token_uri": "https://oauth2.googleapis.com/token",
            "client_id": "fake",
            "client_secret": "fake",
            "scopes": [],
        }))

        watcher = GmailWatcher(vault_path=str(tmp_vault), dry_run=True)
        watcher._rate_limit_max = 10

        # Add old calls (outside window)
        from datetime import timedelta

        old_time = datetime.now() - timedelta(hours=2)
        watcher._rate_limit_calls = [old_time, old_time]

        # Should allow new calls (old ones outside window)
        assert watcher._check_rate_limit() is True


class TestGmailWatcherDashboard:
    """Tests for Dashboard.md updates."""

    @pytest.fixture
    def tmp_vault(self, tmp_path):
        """Create temporary vault directory."""
        vault = tmp_path / "vault"
        vault.mkdir()
        (vault / "Dashboard.md").write_text("# Dashboard\n", encoding="utf-8")
        return vault

    def test_dashboard_session_expiry_update(self, tmp_vault, monkeypatch):
        """Verify Dashboard.md is updated on session expiry."""
        monkeypatch.setenv("GMAIL_OAUTH_TOKEN", json.dumps({
            "token": "fake",
            "refresh_token": "fake",
            "token_uri": "https://oauth2.googleapis.com/token",
            "client_id": "fake",
            "client_secret": "fake",
            "scopes": [],
        }))

        watcher = GmailWatcher(vault_path=str(tmp_vault), dry_run=False)

        # Update dashboard
        watcher._update_dashboard_session_expiry("Gmail")

        # Verify update
        content = (tmp_vault / "Dashboard.md").read_text(encoding="utf-8")
        assert "Session Expired: Gmail" in content
        assert "OAuth2 token expired" in content
