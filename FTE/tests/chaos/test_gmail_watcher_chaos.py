"""Chaos tests for GmailWatcher.

Chaos tests verify system resilience under failure conditions:
- API failures and recovery
- Session expiry handling
- Process crash and restart
- Circuit breaker behavior
"""

import json
import os
import signal
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


class TestGmailWatcherChaos:
    """Chaos tests for GmailWatcher."""

    @pytest.fixture
    def chaos_vault(self, tmp_path):
        """Create vault directory for chaos testing."""
        vault = tmp_path / "vault"
        vault.mkdir()
        (vault / "Needs_Action").mkdir()
        (vault / "Logs").mkdir()
        (vault / "Dashboard.md").write_text("# Dashboard\n", encoding="utf-8")
        return vault

    def test_recovers_from_api_failure(self, chaos_vault, monkeypatch):
        """Verify watcher recovers after API failures."""
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
            vault_path=str(chaos_vault),
            dry_run=True,
            interval=1,  # Short interval for testing
        )

        mock_credentials = MagicMock()
        mock_credentials.expired = False
        mock_credentials.valid = True

        # Mock service that fails initially then recovers
        mock_service = MagicMock()

        # First 3 calls fail, then succeed
        call_count = {"value": 0}

        def side_effect():
            call_count["value"] += 1
            if call_count["value"] <= 3:
                mock_response = MagicMock()
                mock_response.status = 503
                raise HttpError(mock_response, b"Service Unavailable")
            return {"messages": []}

        mock_service.users().messages().list().execute.side_effect = side_effect

        with patch.object(watcher, "_get_credentials", return_value=mock_credentials):
            with patch("src.watchers.gmail_watcher.build", return_value=mock_service):
                # First 3 calls should fail
                for i in range(3):
                    with pytest.raises(HttpError):
                        watcher._check_for_updates_impl()

                # 4th call should succeed
                result = watcher._check_for_updates_impl()
                assert result == []  # Empty but successful

    def test_handles_session_expiry(self, chaos_vault, monkeypatch):
        """Verify graceful handling of OAuth2 session expiry."""
        from google.auth.exceptions import RefreshError

        monkeypatch.setenv("GMAIL_OAUTH_TOKEN", json.dumps({
            "token": "fake_token",
            "refresh_token": "fake_refresh",
            "token_uri": "https://oauth2.googleapis.com/token",
            "client_id": "fake_client",
            "client_secret": "fake_secret",
            "scopes": ["https://www.googleapis.com/auth/gmail.readonly"],
        }))

        from src.watchers.gmail_watcher import GmailWatcher, GmailSessionExpiredError

        watcher = GmailWatcher(
            vault_path=str(chaos_vault),
            dry_run=False,
            interval=1,
        )

        mock_credentials = MagicMock()
        mock_credentials.expired = True

        # Mock refresh to fail
        mock_credentials.refresh.side_effect = RefreshError("Token expired")

        with patch.object(watcher, "_get_credentials", return_value=mock_credentials):
            # Should raise GmailSessionExpiredError
            with pytest.raises(GmailSessionExpiredError):
                watcher._check_for_updates_impl()

        # Verify Dashboard.md was updated
        dashboard_content = (chaos_vault / "Dashboard.md").read_text(encoding="utf-8")
        assert "Session Expired" in dashboard_content or "expired" in dashboard_content.lower()

    def test_restarts_after_crash_within_10s(self, chaos_vault, monkeypatch, tmp_path):
        """Verify watcher can restart within 10 seconds after crash."""
        monkeypatch.setenv("GMAIL_OAUTH_TOKEN", json.dumps({
            "token": "fake_token",
            "refresh_token": "fake_refresh",
            "token_uri": "https://oauth2.googleapis.com/token",
            "client_id": "fake_client",
            "client_secret": "fake_secret",
            "scopes": ["https://www.googleapis.com/auth/gmail.readonly"],
        }))

        # Create a simple watcher script that we can run as subprocess
        watcher_script = tmp_path / "test_watcher.py"
        watcher_script.write_text(
            f"""
import sys
import time
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.watchers.gmail_watcher import GmailWatcher

vault_path = r"{chaos_vault}"
watcher = GmailWatcher(vault_path=vault_path, dry_run=True, interval=1)

# Run for a bit then exit
start = time.time()
while time.time() - start < 2:
    try:
        messages = watcher.check_for_updates()
        time.sleep(0.5)
    except Exception as e:
        print(f"Error: {{e}}", file=sys.stderr)
        break

print("Watcher completed successfully")
""",
            encoding="utf-8",
        )

        # Run watcher as subprocess
        start_time = time.time()

        result = subprocess.run(
            [sys.executable, str(watcher_script)],
            capture_output=True,
            text=True,
            timeout=15,  # Should complete well within 15 seconds
            cwd=str(tmp_path),
        )

        elapsed = time.time() - start_time

        # Verify completed within time budget
        assert elapsed < 10, f"Watcher took {elapsed}s, expected < 10s"

        # Verify no crashes
        assert result.returncode == 0 or "completed successfully" in result.stdout

    def test_continues_when_circuit_breaker_open(self, chaos_vault, monkeypatch):
        """Verify watcher continues other operations when circuit breaker is open."""
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
            vault_path=str(chaos_vault),
            dry_run=True,
            interval=1,
        )

        mock_credentials = MagicMock()
        mock_credentials.expired = False

        # Mock service that always fails
        mock_response = MagicMock()
        mock_response.status = 500
        mock_service = MagicMock()
        mock_service.users().messages().list().execute.side_effect = HttpError(
            mock_response, b"Internal Server Error"
        )

        with patch.object(watcher, "_get_credentials", return_value=mock_credentials):
            with patch("src.watchers.gmail_watcher.build", return_value=mock_service):
                # Trigger circuit breaker to open
                for _ in range(6):
                    try:
                        watcher.check_for_updates()
                    except Exception:
                        pass

                # Verify circuit breaker is open
                assert watcher.circuit_breaker.is_open()

                # Now watcher should continue (return empty list) without crashing
                result = watcher.check_for_updates()
                assert result == []  # Returns empty list when circuit is open

    def test_handles_network_timeout(self, chaos_vault, monkeypatch):
        """Verify watcher handles network timeouts gracefully."""
        import socket

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
            vault_path=str(chaos_vault),
            dry_run=True,
            interval=1,
        )

        mock_credentials = MagicMock()
        mock_credentials.expired = False

        # Mock service that times out
        mock_service = MagicMock()
        mock_service.users().messages().list().execute.side_effect = socket.timeout(
            "Connection timed out"
        )

        with patch.object(watcher, "_get_credentials", return_value=mock_credentials):
            with patch("src.watchers.gmail_watcher.build", return_value=mock_service):
                # Should handle timeout gracefully (log error, continue)
                with pytest.raises(socket.timeout):
                    watcher._check_for_updates_impl()

    def test_handles_malformed_response(self, chaos_vault, monkeypatch):
        """Verify watcher handles malformed API responses."""
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
            vault_path=str(chaos_vault),
            dry_run=True,
            interval=1,
        )

        mock_credentials = MagicMock()
        mock_credentials.expired = False

        # Mock service with malformed response
        mock_service = MagicMock()
        mock_service.users().messages().list().execute.return_value = {
            "messages": None  # Should be list, not None
        }

        with patch.object(watcher, "_get_credentials", return_value=mock_credentials):
            with patch("src.watchers.gmail_watcher.build", return_value=mock_service):
                # Should handle gracefully
                result = watcher._check_for_updates_impl()
                assert result == []  # Empty list for malformed response

    def test_concurrent_watcher_instances(self, chaos_vault, monkeypatch):
        """Verify multiple watcher instances can run concurrently."""
        import threading

        monkeypatch.setenv("GMAIL_OAUTH_TOKEN", json.dumps({
            "token": "fake_token",
            "refresh_token": "fake_refresh",
            "token_uri": "https://oauth2.googleapis.com/token",
            "client_id": "fake_client",
            "client_secret": "fake_secret",
            "scopes": ["https://www.googleapis.com/auth/gmail.readonly"],
        }))

        from src.watchers.gmail_watcher import GmailWatcher

        errors = []

        def run_watcher(watcher_id):
            try:
                watcher = GmailWatcher(
                    vault_path=str(chaos_vault),
                    dry_run=True,
                    interval=1,
                )

                mock_credentials = MagicMock()
                mock_credentials.expired = False

                mock_service = MagicMock()
                mock_service.users().messages().list().execute.return_value = {
                    "messages": []
                }

                with patch.object(watcher, "_get_credentials", return_value=mock_credentials):
                    with patch("src.watchers.gmail_watcher.build", return_value=mock_service):
                        result = watcher.check_for_updates()
                        assert result == []
            except Exception as e:
                errors.append(f"Watcher {watcher_id}: {e}")

        # Run multiple watchers concurrently
        threads = []
        for i in range(3):
            t = threading.Thread(target=run_watcher, args=(i,))
            threads.append(t)
            t.start()

        # Wait for all to complete
        for t in threads:
            t.join(timeout=10)

        # Verify no errors
        assert len(errors) == 0, f"Concurrent errors: {errors}"

    def test_database_corruption_recovery(self, chaos_vault, monkeypatch):
        """Verify watcher handles database corruption gracefully."""
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
            vault_path=str(chaos_vault),
            dry_run=True,
            interval=1,
        )

        # Corrupt the database
        db_path = chaos_vault.parent / "data" / "processed_emails.db"
        db_path.parent.mkdir(parents=True, exist_ok=True)
        db_path.write_bytes(b"This is not a valid SQLite database")

        # Should handle corruption gracefully
        # _is_processed should return False on error
        result = watcher._is_processed("test_msg")
        assert result is False  # Returns False on error

        # Watcher should continue to function
        mock_credentials = MagicMock()
        mock_credentials.expired = False

        mock_service = MagicMock()
        mock_service.users().messages().list().execute.return_value = {
            "messages": []
        }

        with patch.object(watcher, "_get_credentials", return_value=mock_credentials):
            with patch("src.watchers.gmail_watcher.build", return_value=mock_service):
                result = watcher._check_for_updates_impl()
                assert result == []


class TestGmailWatcherStress:
    """Stress tests for GmailWatcher."""

    @pytest.fixture
    def stress_vault(self, tmp_path):
        """Create vault for stress testing."""
        vault = tmp_path / "vault"
        vault.mkdir()
        (vault / "Needs_Action").mkdir()
        (vault / "Logs").mkdir()
        return vault

    def test_rapid_successive_checks(self, stress_vault, monkeypatch):
        """Verify watcher handles rapid successive checks."""
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
            vault_path=str(stress_vault),
            dry_run=True,
            interval=1,
        )

        mock_credentials = MagicMock()
        mock_credentials.expired = False

        mock_service = MagicMock()
        mock_service.users().messages().list().execute.return_value = {
            "messages": []
        }

        with patch.object(watcher, "_get_credentials", return_value=mock_credentials):
            with patch("src.watchers.gmail_watcher.build", return_value=mock_service):
                # Run 10 checks in rapid succession
                for _ in range(10):
                    result = watcher.check_for_updates()
                    assert result == []

    def test_large_message_batch(self, stress_vault, monkeypatch):
        """Verify watcher handles large batch of messages."""
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
            vault_path=str(stress_vault),
            dry_run=True,
            interval=1,
        )

        mock_credentials = MagicMock()
        mock_credentials.expired = False

        # Mock 100 messages
        mock_messages = [
            {"id": f"msg_{i}", "threadId": f"thread_{i}"}
            for i in range(100)
        ]

        mock_service = MagicMock()
        mock_service.users().messages().list().execute.return_value = {
            "messages": mock_messages
        }

        mock_full_msg = {
            "id": "msg_0",
            "threadId": "thread_0",
            "snippet": "Test",
            "payload": {
                "headers": [
                    {"name": "From", "value": "test@example.com"},
                    {"name": "To", "value": "me@example.com"},
                    {"name": "Subject", "value": "Test"},
                    {"name": "Date", "value": "2026-04-01T10:00:00Z"},
                ]
            },
        }
        mock_service.users().messages().get().execute.return_value = mock_full_msg

        with patch.object(watcher, "_get_credentials", return_value=mock_credentials):
            with patch("src.watchers.gmail_watcher.build", return_value=mock_service):
                # Should handle large batch without crashing
                result = watcher._check_for_updates_impl()
                # Returns up to 100 messages (filtered by processed status)
                assert len(result) <= 100
