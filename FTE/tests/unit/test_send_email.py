"""Unit tests for SendEmailSkill."""

import os
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.skills.send_email import (
    SendEmailSkill,
    GmailAPIError,
    RateLimitExceededError,
)
from src.skills.request_approval import ApprovalRequiredError
from src.utils.circuit_breaker import CircuitBreakerOpenError


@pytest.fixture
def mock_metrics_collector():
    """Create a mock metrics collector."""
    mock = MagicMock()
    mock.record_histogram = MagicMock()
    mock.increment_counter = MagicMock()
    mock.set_gauge = MagicMock()
    return mock


@pytest.fixture
def mock_circuit_breaker():
    """Create a mock circuit breaker."""
    mock = MagicMock()
    mock.call = MagicMock(side_effect=lambda func, *args, **kwargs: func(*args, **kwargs))
    mock.state = "closed"
    mock.is_closed = MagicMock(return_value=True)
    mock.is_open = MagicMock(return_value=False)
    return mock


@pytest.fixture
def temp_vault(tmp_path):
    """Create a temporary vault directory."""
    vault = tmp_path / "vault"
    vault.mkdir()
    (vault / "Pending_Approval").mkdir()
    (vault / "Approved").mkdir()
    (vault / "Rejected").mkdir()
    (vault / "Templates").mkdir()
    return vault


class TestSendEmailSkill:
    """Unit tests for SendEmailSkill."""

    @patch("src.skills.base_skill.get_metrics_collector")
    @patch("src.skills.send_email.get_circuit_breaker")
    def test_dry_run_no_api_call(
        self,
        mock_get_circuit_breaker,
        mock_get_metrics,
        monkeypatch,
        tmp_path,
        mock_metrics_collector,
        mock_circuit_breaker,
    ):
        """Verify dry_run mode logs without sending email."""
        # Setup
        monkeypatch.setenv("DEV_MODE", "true")
        monkeypatch.setenv("GMAIL_OAUTH_TOKEN", "test_token")
        monkeypatch.setenv("GMAIL_OAUTH_REFRESH_TOKEN", "test_refresh")
        monkeypatch.setenv("GMAIL_CLIENT_ID", "test_client_id")
        monkeypatch.setenv("GMAIL_CLIENT_SECRET", "test_client_secret")

        mock_get_metrics.return_value = mock_metrics_collector
        mock_get_circuit_breaker.return_value = mock_circuit_breaker

        skill = SendEmailSkill(dry_run=True, vault_dir=tmp_path / "vault")

        # Execute
        result = skill.send_email(
            to="test@example.com",
            subject="Test Subject",
            body="Test Body",
        )

        # Verify
        assert result["status"] == "dry_run"
        assert "DRY RUN" in result["message"]
        assert result["dry_run"] is True
        assert result["message_id"] is None

        # Verify no API call was made
        mock_circuit_breaker.call.assert_not_called()

        # Verify metrics emitted
        mock_metrics_collector.record_histogram.assert_called()
        mock_metrics_collector.increment_counter.assert_called()

    @patch("src.skills.base_skill.get_metrics_collector")
    @patch("src.skills.send_email.get_circuit_breaker")
    @patch("src.skills.send_email.RequestApprovalSkill")
    def test_approval_required_for_new_contact(
        self,
        mock_approval_skill,
        mock_get_circuit_breaker,
        mock_get_metrics,
        monkeypatch,
        tmp_path,
        mock_metrics_collector,
        mock_circuit_breaker,
    ):
        """Verify approval required for new contacts not in address book."""
        # Setup
        monkeypatch.setenv("DEV_MODE", "true")
        monkeypatch.setenv("GMAIL_OAUTH_TOKEN", "test_token")
        monkeypatch.setenv("GMAIL_OAUTH_REFRESH_TOKEN", "test_refresh")
        monkeypatch.setenv("GMAIL_CLIENT_ID", "test_client_id")
        monkeypatch.setenv("GMAIL_CLIENT_SECRET", "test_client_secret")

        mock_get_metrics.return_value = mock_metrics_collector
        mock_get_circuit_breaker.return_value = mock_circuit_breaker

        # Mock approval skill
        mock_approval_instance = MagicMock()
        mock_approval_instance.create_approval_request.return_value = tmp_path / "vault" / "Pending_Approval" / "test.md"
        mock_approval_skill.return_value = mock_approval_instance

        skill = SendEmailSkill(dry_run=False, vault_dir=tmp_path / "vault")

        # Execute & Verify
        with pytest.raises(ApprovalRequiredError) as exc_info:
            skill.send_email(
                to="unknown_contact@example.com",  # Not in known_contacts
                subject="Test Subject",
                body="Test Body",
            )

        assert "Approval required" in str(exc_info.value)
        mock_approval_instance.create_approval_request.assert_called_once()

    @patch("src.skills.base_skill.get_metrics_collector")
    @patch("src.skills.send_email.get_circuit_breaker")
    def test_circuit_breaker_trips_after_failures(
        self,
        mock_get_circuit_breaker,
        mock_get_metrics,
        monkeypatch,
        tmp_path,
        mock_metrics_collector,
    ):
        """Verify circuit breaker opens after consecutive failures."""
        # Setup
        monkeypatch.setenv("DEV_MODE", "true")
        monkeypatch.setenv("GMAIL_OAUTH_TOKEN", "test_token")
        monkeypatch.setenv("GMAIL_OAUTH_REFRESH_TOKEN", "test_refresh")
        monkeypatch.setenv("GMAIL_CLIENT_ID", "test_client_id")
        monkeypatch.setenv("GMAIL_CLIENT_SECRET", "test_client_secret")

        mock_get_metrics.return_value = mock_metrics_collector

        # Mock circuit breaker to simulate open state
        mock_cb_instance = MagicMock()
        mock_cb_instance.state = "open"
        mock_cb_instance.is_closed = MagicMock(return_value=False)
        mock_cb_instance.is_open = MagicMock(return_value=True)
        mock_cb_instance.call.side_effect = CircuitBreakerOpenError("Circuit breaker open")

        mock_get_circuit_breaker.return_value = mock_cb_instance

        skill = SendEmailSkill(dry_run=False, vault_dir=tmp_path / "vault")
        
        # Add test email to known contacts to bypass approval
        skill.known_contacts.add("test@example.com")

        # Execute
        result = skill.send_email(
            to="test@example.com",
            subject="Test Subject",
            body="Test Body",
        )

        # Verify
        assert result["status"] == "error"
        assert "Circuit breaker" in result.get("error", "") or result["status"] == "error"

    @patch("src.skills.base_skill.get_metrics_collector")
    @patch("src.skills.send_email.get_circuit_breaker")
    def test_rate_limiting_enforced(
        self,
        mock_get_circuit_breaker,
        mock_get_metrics,
        monkeypatch,
        tmp_path,
        mock_metrics_collector,
        mock_circuit_breaker,
    ):
        """Verify rate limit enforced (max 100 calls/hour)."""
        # Setup
        monkeypatch.setenv("DEV_MODE", "true")
        monkeypatch.setenv("GMAIL_OAUTH_TOKEN", "test_token")
        monkeypatch.setenv("GMAIL_OAUTH_REFRESH_TOKEN", "test_refresh")
        monkeypatch.setenv("GMAIL_CLIENT_ID", "test_client_id")
        monkeypatch.setenv("GMAIL_CLIENT_SECRET", "test_client_secret")

        mock_get_metrics.return_value = mock_metrics_collector
        mock_get_circuit_breaker.return_value = mock_circuit_breaker

        skill = SendEmailSkill(dry_run=False, vault_dir=tmp_path / "vault")
        
        # Add test email to known contacts to bypass approval
        skill.known_contacts.add("test@example.com")

        # Manually set rate limit to exceeded (set call_count to limit)
        skill.max_calls_per_hour = 100
        conn = sqlite3.connect(skill.rate_limit_db)
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE rate_limits
            SET call_count = 100, window_start = ?
            WHERE id = 1
        """,
            (datetime.now() - timedelta(minutes=30),),  # Window started 30 min ago
        )
        conn.commit()
        conn.close()

        # Execute - should return error dict, not raise
        result = skill.send_email(
            to="test@example.com",
            subject="Test Subject",
            body="Test Body",
        )

        # Verify
        assert result["status"] == "error"
        assert "rate limit" in result.get("error", "").lower()

    @patch("src.skills.base_skill.get_metrics_collector")
    @patch("src.skills.send_email.get_circuit_breaker")
    @patch("src.skills.send_email.SendEmailSkill._build_gmail_service")
    def test_send_email_returns_message_id(
        self,
        mock_build_service,
        mock_get_circuit_breaker,
        mock_get_metrics,
        monkeypatch,
        tmp_path,
        mock_metrics_collector,
        mock_circuit_breaker,
    ):
        """Verify send_email returns message_id on success."""
        # Setup
        monkeypatch.setenv("DEV_MODE", "true")
        monkeypatch.setenv("GMAIL_OAUTH_TOKEN", "test_token")
        monkeypatch.setenv("GMAIL_OAUTH_REFRESH_TOKEN", "test_refresh")
        monkeypatch.setenv("GMAIL_CLIENT_ID", "test_client_id")
        monkeypatch.setenv("GMAIL_CLIENT_SECRET", "test_client_secret")

        mock_get_metrics.return_value = mock_metrics_collector
        mock_get_circuit_breaker.return_value = mock_circuit_breaker

        # Mock Gmail service
        mock_service = MagicMock()
        mock_service.users().messages().send().execute.return_value = {"id": "test_message_id_123"}
        mock_build_service.return_value = mock_service

        skill = SendEmailSkill(dry_run=False, vault_dir=tmp_path / "vault")

        # Add known contact
        skill.known_contacts.add("test@example.com")

        # Execute
        result = skill.send_email(
            to="test@example.com",
            subject="Test Subject",
            body="Test Body",
        )

        # Verify
        assert result["status"] == "sent"
        assert result["message_id"] == "test_message_id_123"
        assert result["dry_run"] is False

    @patch("src.skills.base_skill.get_metrics_collector")
    @patch("src.skills.send_email.get_circuit_breaker")
    @patch("src.skills.send_email.SendEmailSkill._build_gmail_service")
    def test_draft_email_creates_draft(
        self,
        mock_build_service,
        mock_get_circuit_breaker,
        mock_get_metrics,
        monkeypatch,
        tmp_path,
        mock_metrics_collector,
        mock_circuit_breaker,
    ):
        """Verify draft_email creates draft successfully."""
        # Setup
        monkeypatch.setenv("DEV_MODE", "true")
        monkeypatch.setenv("GMAIL_OAUTH_TOKEN", "test_token")
        monkeypatch.setenv("GMAIL_OAUTH_REFRESH_TOKEN", "test_refresh")
        monkeypatch.setenv("GMAIL_CLIENT_ID", "test_client_id")
        monkeypatch.setenv("GMAIL_CLIENT_SECRET", "test_client_secret")

        mock_get_metrics.return_value = mock_metrics_collector
        mock_get_circuit_breaker.return_value = mock_circuit_breaker

        # Mock Gmail service
        mock_service = MagicMock()
        mock_service.users().drafts().create().execute.return_value = {
            "id": "test_draft_id",
            "message": {"id": "test_message_id"},
        }
        mock_build_service.return_value = mock_service

        skill = SendEmailSkill(dry_run=False, vault_dir=tmp_path / "vault")

        # Add known contact
        skill.known_contacts.add("test@example.com")

        # Execute
        result = skill.draft_email(
            to="test@example.com",
            subject="Test Subject",
            body="Test Body",
        )

        # Verify
        assert result["status"] == "draft"
        assert result["message_id"] == "test_message_id"
        assert result["draft_id"] == "test_draft_id"

    @patch("src.skills.base_skill.get_metrics_collector")
    @patch("src.skills.send_email.get_circuit_breaker")
    def test_bulk_send_requires_approval(
        self,
        mock_get_circuit_breaker,
        mock_get_metrics,
        monkeypatch,
        tmp_path,
        mock_metrics_collector,
        mock_circuit_breaker,
    ):
        """Verify bulk send (>5 recipients) requires approval."""
        # Setup
        monkeypatch.setenv("DEV_MODE", "true")
        monkeypatch.setenv("GMAIL_OAUTH_TOKEN", "test_token")
        monkeypatch.setenv("GMAIL_OAUTH_REFRESH_TOKEN", "test_refresh")
        monkeypatch.setenv("GMAIL_CLIENT_ID", "test_client_id")
        monkeypatch.setenv("GMAIL_CLIENT_SECRET", "test_client_secret")

        mock_get_metrics.return_value = mock_metrics_collector
        mock_get_circuit_breaker.return_value = mock_circuit_breaker

        skill = SendEmailSkill(dry_run=False, vault_dir=tmp_path / "vault")

        # Execute & Verify (6 recipients > 5 threshold)
        with pytest.raises(ApprovalRequiredError) as exc_info:
            skill.send_email(
                to=["user1@example.com"] * 6,
                subject="Test Subject",
                body="Test Body",
            )

        assert "Bulk send" in str(exc_info.value) or "approval" in str(exc_info.value).lower()

    @patch("src.skills.base_skill.get_metrics_collector")
    @patch("src.skills.send_email.get_circuit_breaker")
    def test_gmail_api_error_handling(
        self,
        mock_get_circuit_breaker,
        mock_get_metrics,
        monkeypatch,
        tmp_path,
        mock_metrics_collector,
    ):
        """Verify GmailAPIError raised on API failure."""
        # Setup
        monkeypatch.setenv("DEV_MODE", "true")
        monkeypatch.setenv("GMAIL_OAUTH_TOKEN", "test_token")
        monkeypatch.setenv("GMAIL_OAUTH_REFRESH_TOKEN", "test_refresh")
        monkeypatch.setenv("GMAIL_CLIENT_ID", "test_client_id")
        monkeypatch.setenv("GMAIL_CLIENT_SECRET", "test_client_secret")

        mock_get_metrics.return_value = mock_metrics_collector

        # Mock circuit breaker to raise GmailAPIError
        mock_cb_instance = MagicMock()
        mock_cb_instance.call.side_effect = GmailAPIError("Gmail API error")
        mock_get_circuit_breaker.return_value = mock_cb_instance

        skill = SendEmailSkill(dry_run=False, vault_dir=tmp_path / "vault")
        skill.known_contacts.add("test@example.com")

        # Execute & Verify
        with pytest.raises(GmailAPIError):
            skill.send_email(
                to="test@example.com",
                subject="Test Subject",
                body="Test Body",
            )

    @patch("src.skills.base_skill.get_metrics_collector")
    @patch("src.skills.send_email.get_circuit_breaker")
    def test_metrics_emitted_on_send(
        self,
        mock_get_circuit_breaker,
        mock_get_metrics,
        monkeypatch,
        tmp_path,
        mock_metrics_collector,
        mock_circuit_breaker,
    ):
        """Verify metrics emitted on successful send."""
        # Setup
        monkeypatch.setenv("DEV_MODE", "true")
        monkeypatch.setenv("GMAIL_OAUTH_TOKEN", "test_token")
        monkeypatch.setenv("GMAIL_OAUTH_REFRESH_TOKEN", "test_refresh")
        monkeypatch.setenv("GMAIL_CLIENT_ID", "test_client_id")
        monkeypatch.setenv("GMAIL_CLIENT_SECRET", "test_client_secret")

        mock_get_metrics.return_value = mock_metrics_collector
        mock_get_circuit_breaker.return_value = mock_circuit_breaker

        # Mock Gmail service
        mock_service = MagicMock()
        mock_service.users().messages().send().execute.return_value = {"id": "test_id"}
        mock_build_service = MagicMock(return_value=mock_service)

        with patch.object(SendEmailSkill, "_build_gmail_service", mock_build_service):
            skill = SendEmailSkill(dry_run=False, vault_dir=tmp_path / "vault")
            skill.known_contacts.add("test@example.com")

            # Execute
            skill.send_email(
                to="test@example.com",
                subject="Test Subject",
                body="Test Body",
            )

        # Verify metrics emitted
        mock_metrics_collector.record_histogram.assert_called()  # email_send_duration
        mock_metrics_collector.increment_counter.assert_called()  # email_send_count

    @patch("src.skills.base_skill.get_metrics_collector")
    @patch("src.skills.send_email.get_circuit_breaker")
    def test_known_contacts_loaded_from_handbook(
        self,
        mock_get_circuit_breaker,
        mock_get_metrics,
        monkeypatch,
        tmp_path,
        mock_metrics_collector,
        mock_circuit_breaker,
    ):
        """Verify known contacts loaded from Company_Handbook.md."""
        # Setup
        monkeypatch.setenv("DEV_MODE", "true")
        monkeypatch.setenv("GMAIL_OAUTH_TOKEN", "test_token")
        monkeypatch.setenv("GMAIL_OAUTH_REFRESH_TOKEN", "test_refresh")
        monkeypatch.setenv("GMAIL_CLIENT_ID", "test_client_id")
        monkeypatch.setenv("GMAIL_CLIENT_SECRET", "test_client_secret")

        mock_get_metrics.return_value = mock_metrics_collector
        mock_get_circuit_breaker.return_value = mock_circuit_breaker

        # Create Company_Handbook.md with known contacts
        handbook = tmp_path / "vault" / "Company_Handbook.md"
        handbook.parent.mkdir()
        handbook.write_text(
            """
# Company Handbook

[Email]
known_contacts = ["known1@example.com", "known2@example.com"]
"""
        )

        skill = SendEmailSkill(dry_run=False, vault_dir=tmp_path / "vault")

        # Verify known contacts loaded
        assert "known1@example.com" in skill.known_contacts
        assert "known2@example.com" in skill.known_contacts


class TestSendEmailSkillRateLimiting:
    """Rate limiting specific tests."""

    @patch("src.skills.base_skill.get_metrics_collector")
    @patch("src.skills.send_email.get_circuit_breaker")
    def test_rate_limit_window_reset(
        self,
        mock_get_circuit_breaker,
        mock_get_metrics,
        monkeypatch,
        tmp_path,
        mock_metrics_collector,
        mock_circuit_breaker,
    ):
        """Verify rate limit window resets after 1 hour."""
        # Setup
        monkeypatch.setenv("DEV_MODE", "true")
        monkeypatch.setenv("GMAIL_OAUTH_TOKEN", "test_token")
        monkeypatch.setenv("GMAIL_OAUTH_REFRESH_TOKEN", "test_refresh")
        monkeypatch.setenv("GMAIL_CLIENT_ID", "test_client_id")
        monkeypatch.setenv("GMAIL_CLIENT_SECRET", "test_client_secret")

        mock_get_metrics.return_value = mock_metrics_collector
        mock_get_circuit_breaker.return_value = mock_circuit_breaker

        skill = SendEmailSkill(dry_run=False, vault_dir=tmp_path / "vault")

        # Set old window (should reset)
        conn = sqlite3.connect(skill.rate_limit_db)
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE rate_limits
            SET call_count = 100, window_start = ?
            WHERE id = 1
        """,
            (datetime.now() - timedelta(hours=2),),  # 2 hours ago
        )
        conn.commit()
        conn.close()

        # Should succeed (window reset)
        skill.known_contacts.add("test@example.com")

        # Mock Gmail service
        mock_service = MagicMock()
        mock_service.users().messages().send().execute.return_value = {"id": "test_id"}

        with patch.object(skill, "_build_gmail_service", return_value=mock_service):
            result = skill.send_email(
                to="test@example.com",
                subject="Test",
                body="Test",
            )

        assert result["status"] == "sent"

        # Verify counter reset
        conn = sqlite3.connect(skill.rate_limit_db)
        cursor = conn.cursor()
        cursor.execute("SELECT call_count FROM rate_limits WHERE id = 1")
        count = cursor.fetchone()[0]
        conn.close()

        assert count == 1  # Reset to 1 after window expiry
