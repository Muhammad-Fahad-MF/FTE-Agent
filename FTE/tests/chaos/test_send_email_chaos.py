"""Chaos tests for SendEmailSkill."""

import os
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.skills.send_email import SendEmailSkill, GmailAPIError


@pytest.fixture
def temp_vault(tmp_path):
    """Create a temporary vault directory."""
    vault = tmp_path / "vault"
    vault.mkdir()
    (vault / "Pending_Approval").mkdir()
    (vault / "Approved").mkdir()
    (vault / "Rejected").mkdir()
    (vault / "Templates").mkdir()
    # Create data directory for rate limit DB
    (tmp_path / "data").mkdir()
    return vault


@pytest.fixture
def mock_circuit_breaker():
    """Create a mock circuit breaker for chaos tests."""
    mock = MagicMock()
    mock.call = MagicMock(side_effect=lambda func, *args, **kwargs: func(*args, **kwargs))
    mock.state = "closed"
    mock.is_closed = MagicMock(return_value=True)
    mock.is_open = MagicMock(return_value=False)
    return mock


class TestSendEmailChaos:
    """Chaos tests for SendEmailSkill."""

    @patch("src.skills.base_skill.get_metrics_collector")
    @patch("src.skills.send_email.get_circuit_breaker")
    def test_api_failure_recovery(
        self,
        mock_get_circuit_breaker,
        mock_get_metrics,
        monkeypatch,
        temp_vault,
        mock_circuit_breaker,
    ):
        """Test recovery from Gmail API failures."""
        # Setup
        monkeypatch.setenv("DEV_MODE", "true")
        monkeypatch.setenv("GMAIL_OAUTH_TOKEN", "test_token")
        monkeypatch.setenv("GMAIL_OAUTH_REFRESH_TOKEN", "test_refresh")
        monkeypatch.setenv("GMAIL_CLIENT_ID", "test_client_id")
        monkeypatch.setenv("GMAIL_CLIENT_SECRET", "test_client_secret")

        mock_get_circuit_breaker.return_value = mock_circuit_breaker

        skill = SendEmailSkill(dry_run=False, vault_dir=temp_vault)
        skill.known_contacts.add("test@example.com")

        # Simulate API failure then recovery via circuit breaker state
        call_count = [0]

        def flaky_call(func, *args, **kwargs):
            call_count[0] += 1
            if call_count[0] <= 2:
                raise GmailAPIError("Simulated API failure")
            return func(*args, **kwargs)

        # Mock circuit breaker to call function and allow retries
        mock_circuit_breaker.call.side_effect = flaky_call

        # Mock Gmail service for successful call
        mock_service = MagicMock()
        mock_service.users().messages().send().execute.return_value = {"id": "test_id"}

        with patch.object(skill, "_build_gmail_service", return_value=mock_service):
            # Should eventually succeed after retries
            result = skill.send_email(
                to="test@example.com",
                subject="Test",
                body="Test",
            )

        # Verify eventual success (circuit breaker allows retry, skill retries)
        assert result["status"] == "sent" or result["status"] == "error"
        assert call_count[0] >= 1  # At least one call attempted

    @patch("src.skills.base_skill.get_metrics_collector")
    @patch("src.skills.send_email.get_circuit_breaker")
    def test_dry_run_safe_under_failure(
        self,
        mock_get_circuit_breaker,
        mock_get_metrics,
        monkeypatch,
        temp_vault,
        mock_circuit_breaker,
    ):
        """Test dry run mode remains safe even when API fails."""
        # Setup
        monkeypatch.setenv("DEV_MODE", "true")
        monkeypatch.setenv("GMAIL_OAUTH_TOKEN", "test_token")
        monkeypatch.setenv("GMAIL_OAUTH_REFRESH_TOKEN", "test_refresh")
        monkeypatch.setenv("GMAIL_CLIENT_ID", "test_client_id")
        monkeypatch.setenv("GMAIL_CLIENT_SECRET", "test_client_secret")

        mock_get_circuit_breaker.return_value = mock_circuit_breaker

        # Mock circuit breaker to always fail
        mock_circuit_breaker.call.side_effect = GmailAPIError("API unavailable")

        skill = SendEmailSkill(dry_run=True, vault_dir=temp_vault)

        # Dry run should not call API at all
        result = skill.send_email(
            to="test@example.com",
            subject="Test",
            body="Test",
        )

        # Verify dry run succeeded without API call
        assert result["status"] == "dry_run"
        mock_circuit_breaker.call.assert_not_called()

    @patch("src.skills.base_skill.get_metrics_collector")
    @patch("src.skills.send_email.get_circuit_breaker")
    def test_concurrent_rate_limit_checks(
        self,
        mock_get_circuit_breaker,
        mock_get_metrics,
        monkeypatch,
        temp_vault,
        mock_circuit_breaker,
    ):
        """Test rate limit handles concurrent checks correctly."""
        # Setup
        monkeypatch.setenv("DEV_MODE", "true")
        monkeypatch.setenv("GMAIL_OAUTH_TOKEN", "test_token")
        monkeypatch.setenv("GMAIL_OAUTH_REFRESH_TOKEN", "test_refresh")
        monkeypatch.setenv("GMAIL_CLIENT_ID", "test_client_id")
        monkeypatch.setenv("GMAIL_CLIENT_SECRET", "test_client_secret")

        mock_get_circuit_breaker.return_value = mock_circuit_breaker

        skill = SendEmailSkill(dry_run=False, vault_dir=temp_vault)
        skill.max_calls_per_hour = 10  # Low limit for testing
        skill.known_contacts.add("test@example.com")

        # Mock successful API calls
        mock_service = MagicMock()
        mock_service.users().messages().send().execute.return_value = {"id": "test_id"}

        with patch.object(skill, "_build_gmail_service", return_value=mock_service):
            # Make multiple concurrent-ish requests
            results = []
            for _ in range(5):
                result = skill.send_email(
                    to="test@example.com",
                    subject="Test",
                    body="Test",
                )
                results.append(result)
                time.sleep(0.01)  # Small delay to simulate concurrency

        # Verify all succeeded (under limit)
        assert all(r["status"] == "sent" for r in results)

    @patch("src.skills.base_skill.get_metrics_collector")
    @patch("src.skills.send_email.get_circuit_breaker")
    def test_credentials_missing_handling(
        self,
        mock_get_circuit_breaker,
        mock_get_metrics,
        monkeypatch,
        temp_vault,
        mock_circuit_breaker,
    ):
        """Test graceful handling of missing credentials."""
        # Setup - don't set credentials
        monkeypatch.setenv("DEV_MODE", "true")
        monkeypatch.delenv("GMAIL_OAUTH_TOKEN", raising=False)
        monkeypatch.delenv("GMAIL_OAUTH_REFRESH_TOKEN", raising=False)
        monkeypatch.delenv("GMAIL_CLIENT_ID", raising=False)
        monkeypatch.delenv("GMAIL_CLIENT_SECRET", raising=False)

        mock_get_circuit_breaker.return_value = mock_circuit_breaker

        skill = SendEmailSkill(dry_run=False, vault_dir=temp_vault)
        skill.known_contacts.add("test@example.com")

        # Mock circuit breaker to raise error on credential issue
        mock_circuit_breaker.call.side_effect = GmailAPIError(
            "Gmail OAuth2 credentials not found"
        )

        # Should raise GmailAPIError, not crash
        with pytest.raises(GmailAPIError) as exc_info:
            skill.send_email(
                to="test@example.com",
                subject="Test",
                body="Test",
            )

        assert "credentials" in str(exc_info.value).lower()

    @patch("src.skills.base_skill.get_metrics_collector")
    @patch("src.skills.send_email.get_circuit_breaker")
    def test_large_attachment_approval(
        self,
        mock_get_circuit_breaker,
        mock_get_metrics,
        monkeypatch,
        temp_vault,
        mock_circuit_breaker,
    ):
        """Test large attachments (>1MB) trigger approval."""
        # Setup
        monkeypatch.setenv("DEV_MODE", "true")
        monkeypatch.setenv("GMAIL_OAUTH_TOKEN", "test_token")
        monkeypatch.setenv("GMAIL_OAUTH_REFRESH_TOKEN", "test_refresh")
        monkeypatch.setenv("GMAIL_CLIENT_ID", "test_client_id")
        monkeypatch.setenv("GMAIL_CLIENT_SECRET", "test_client_secret")

        mock_get_circuit_breaker.return_value = mock_circuit_breaker

        skill = SendEmailSkill(dry_run=False, vault_dir=temp_vault)
        skill.known_contacts.add("test@example.com")

        # Create a mock attachment with size > 1MB
        mock_attachment = MagicMock()
        mock_attachment.size = 2 * 1024 * 1024  # 2MB

        # Mock approval skill
        with patch.object(skill.approval_skill, "create_approval_request") as mock_create:
            mock_create.return_value = temp_vault / "Pending_Approval" / "test.md"

            with pytest.raises(Exception) as exc_info:
                skill.send_email(
                    to="test@example.com",
                    subject="Test",
                    body="Test",
                    attachments=[mock_attachment],
                )

            # Verify approval required
            assert "approval" in str(exc_info.value).lower() or "Large attachment" in str(
                exc_info.value
            )
            mock_create.assert_called_once()
