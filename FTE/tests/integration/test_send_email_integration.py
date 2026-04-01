"""Integration tests for SendEmailSkill."""

import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.skills.send_email import SendEmailSkill


@pytest.fixture
def temp_vault(tmp_path):
    """Create a temporary vault directory."""
    vault = tmp_path / "vault"
    vault.mkdir()
    (vault / "Pending_Approval").mkdir()
    (vault / "Approved").mkdir()
    (vault / "Rejected").mkdir()
    (vault / "Templates").mkdir()
    (vault / "Logs").mkdir()
    # Create data directory for rate limit DB
    (tmp_path / "data").mkdir()
    return vault


@pytest.fixture
def mock_circuit_breaker():
    """Create a mock circuit breaker for integration tests."""
    mock = MagicMock()
    mock.call = MagicMock(side_effect=lambda func, *args, **kwargs: func(*args, **kwargs))
    mock.state = "closed"
    mock.is_closed = MagicMock(return_value=True)
    mock.is_open = MagicMock(return_value=False)
    return mock


class TestSendEmailIntegration:
    """Integration tests for SendEmailSkill."""

    @patch("src.skills.base_skill.get_metrics_collector")
    @patch("src.skills.send_email.get_circuit_breaker")
    def test_approval_workflow_integration(
        self,
        mock_get_circuit_breaker,
        mock_get_metrics,
        monkeypatch,
        temp_vault,
        mock_circuit_breaker,
    ):
        """Test approval workflow: new contact triggers approval request."""
        # Setup
        monkeypatch.setenv("DEV_MODE", "true")
        monkeypatch.setenv("GMAIL_OAUTH_TOKEN", "test_token")
        monkeypatch.setenv("GMAIL_OAUTH_REFRESH_TOKEN", "test_refresh")
        monkeypatch.setenv("GMAIL_CLIENT_ID", "test_client_id")
        monkeypatch.setenv("GMAIL_CLIENT_SECRET", "test_client_secret")

        mock_get_circuit_breaker.return_value = mock_circuit_breaker

        skill = SendEmailSkill(dry_run=False, vault_dir=temp_vault)

        # Create Company_Handbook.md with known contacts
        handbook = temp_vault / "Company_Handbook.md"
        handbook.write_text(
            """
# Company Handbook

[Email]
known_contacts = ["known@example.com"]
"""
        )

        # Reload known contacts
        skill.known_contacts = skill._load_known_contacts()

        # Mock approval skill to track calls
        with patch.object(skill.approval_skill, "create_approval_request") as mock_create:
            mock_create.return_value = temp_vault / "Pending_Approval" / "test.md"

            # Attempt to send to unknown contact
            with pytest.raises(Exception) as exc_info:
                skill.send_email(
                    to="unknown@example.com",
                    subject="Test",
                    body="Test",
                )

            # Verify approval request was created
            mock_create.assert_called_once()
            assert "approval" in str(exc_info.value).lower()

    @patch("src.skills.base_skill.get_metrics_collector")
    @patch("src.skills.send_email.get_circuit_breaker")
    def test_dry_run_preserves_state(
        self,
        mock_get_circuit_breaker,
        mock_get_metrics,
        monkeypatch,
        temp_vault,
        mock_circuit_breaker,
    ):
        """Test dry run mode doesn't modify external state."""
        # Setup
        monkeypatch.setenv("DEV_MODE", "true")
        monkeypatch.setenv("GMAIL_OAUTH_TOKEN", "test_token")
        monkeypatch.setenv("GMAIL_OAUTH_REFRESH_TOKEN", "test_refresh")
        monkeypatch.setenv("GMAIL_CLIENT_ID", "test_client_id")
        monkeypatch.setenv("GMAIL_CLIENT_SECRET", "test_client_secret")

        mock_get_circuit_breaker.return_value = mock_circuit_breaker

        skill = SendEmailSkill(dry_run=True, vault_dir=temp_vault)
        skill.known_contacts.add("test@example.com")

        # Execute dry run
        result = skill.send_email(
            to="test@example.com",
            subject="Test",
            body="Test",
        )

        # Verify
        assert result["status"] == "dry_run"
        assert mock_circuit_breaker.call.assert_not_called

    @patch("src.skills.base_skill.get_metrics_collector")
    @patch("src.skills.send_email.get_circuit_breaker")
    def test_rate_limit_persists_across_instances(
        self,
        mock_get_circuit_breaker,
        mock_get_metrics,
        monkeypatch,
        temp_vault,
        mock_circuit_breaker,
    ):
        """Test rate limit persists across skill instances."""
        # Setup
        monkeypatch.setenv("DEV_MODE", "true")
        monkeypatch.setenv("GMAIL_OAUTH_TOKEN", "test_token")
        monkeypatch.setenv("GMAIL_OAUTH_REFRESH_TOKEN", "test_refresh")
        monkeypatch.setenv("GMAIL_CLIENT_ID", "test_client_id")
        monkeypatch.setenv("GMAIL_CLIENT_SECRET", "test_client_secret")

        mock_get_circuit_breaker.return_value = mock_circuit_breaker

        # Create first instance and increment counter
        skill1 = SendEmailSkill(dry_run=False, vault_dir=temp_vault)

        # Manually set rate limit
        import sqlite3

        conn = sqlite3.connect(skill1.rate_limit_db)
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE rate_limits
            SET call_count = 50, window_start = datetime('now')
            WHERE id = 1
        """
        )
        conn.commit()
        conn.close()

        # Create second instance (should see same rate limit)
        skill2 = SendEmailSkill(dry_run=False, vault_dir=temp_vault)

        # Verify rate limit persisted
        conn = sqlite3.connect(skill2.rate_limit_db)
        cursor = conn.cursor()
        cursor.execute("SELECT call_count FROM rate_limits WHERE id = 1")
        count = cursor.fetchone()[0]
        conn.close()

        assert count == 50
