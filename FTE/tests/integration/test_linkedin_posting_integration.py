"""Integration tests for LinkedInPostingSkill."""

import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.skills.linkedin_posting import LinkedInPostingSkill


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
    (vault / "Done").mkdir()
    (vault / "linkedin_session").mkdir()
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


class TestLinkedInPostingIntegration:
    """Integration tests for LinkedInPostingSkill."""

    @patch("src.skills.base_skill.get_metrics_collector")
    @patch("src.skills.linkedin_posting.get_circuit_breaker")
    @patch.object(LinkedInPostingSkill, "_post_to_linkedin_async")
    def test_end_to_end_post_generation_and_approval(
        self,
        mock_post_async,
        mock_get_circuit_breaker,
        mock_get_metrics,
        monkeypatch,
        temp_vault,
        mock_circuit_breaker,
    ):
        """Test end-to-end: generates content, creates approval, posts on approval."""
        # Setup
        monkeypatch.setenv("DEV_MODE", "true")

        mock_get_metrics.return_value = mock_get_metrics
        mock_get_circuit_breaker.return_value = mock_circuit_breaker
        mock_post_async.return_value = {
            "status": "posted",
            "post_id": "test_post_123",
            "url": "https://linkedin.com/posts/test",
            "timestamp": "2026-04-01T12:00:00",
        }

        # Create Business_Goals.md
        goals = temp_vault / "Business_Goals.md"
        goals.write_text(
            """---
title: Business Goals 2026
---

# Business Goals

Increase market share by 10% through innovative AI solutions.

[hashtags]
- #AI
- #Innovation
"""
        )

        # Create Done/ achievement
        achievement = temp_vault / "Done" / "achievement1.md"
        achievement.write_text(
            """---
type: achievement
status: completed
---

# Achievement

Successfully launched AI assistant feature.
"""
        )

        skill = LinkedInPostingSkill(dry_run=False, vault_dir=temp_vault)

        # Generate content
        content = skill.generate_content()

        # Verify content generated
        assert content is not None
        assert len(content) > 0
        assert "#AI" in content or "#Innovation" in content

        # Post to LinkedIn
        result = skill.post_to_linkedin(content)

        # Verify post succeeded
        assert result["status"] == "posted"
        assert result["post_id"] == "test_post_123"

    @patch("src.skills.base_skill.get_metrics_collector")
    @patch("src.skills.linkedin_posting.get_circuit_breaker")
    def test_session_persists_across_restarts(
        self,
        mock_get_circuit_breaker,
        mock_get_metrics,
        monkeypatch,
        temp_vault,
        mock_circuit_breaker,
    ):
        """Test session storage.json survives restart."""
        # Setup
        monkeypatch.setenv("DEV_MODE", "true")

        mock_get_metrics.return_value = mock_get_metrics
        mock_get_circuit_breaker.return_value = mock_circuit_breaker

        # Create session file
        storage_file = temp_vault / "linkedin_session" / "storage.json"
        storage_file.write_text('{"cookies": [{"name": "test"}], "origins": []}')

        # Create first instance
        skill1 = LinkedInPostingSkill(dry_run=True, vault_dir=temp_vault)

        # Verify session valid
        assert skill1._is_session_valid() is True

        # Create second instance (simulates restart)
        skill2 = LinkedInPostingSkill(dry_run=True, vault_dir=temp_vault)

        # Verify session still valid
        assert skill2._is_session_valid() is True

        # Verify file exists
        assert storage_file.exists()
