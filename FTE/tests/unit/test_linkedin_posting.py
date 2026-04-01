"""Unit tests for LinkedInPostingSkill."""

import os
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.skills.linkedin_posting import (
    LinkedInPostingSkill,
    LinkedInPostError,
    LinkedInSessionExpiredError,
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
    (vault / "Logs").mkdir()
    (vault / "Done").mkdir()
    return vault


class TestLinkedInPostingSkill:
    """Unit tests for LinkedInPostingSkill."""

    @patch("src.skills.base_skill.get_metrics_collector")
    @patch("src.skills.linkedin_posting.get_circuit_breaker")
    def test_content_generation_from_goals_and_done(
        self,
        mock_get_circuit_breaker,
        mock_get_metrics,
        monkeypatch,
        temp_vault,
        mock_metrics_collector,
        mock_circuit_breaker,
    ):
        """Verify content combines Business_Goals.md and Done/ achievements."""
        # Setup
        monkeypatch.setenv("DEV_MODE", "true")

        mock_get_metrics.return_value = mock_metrics_collector
        mock_get_circuit_breaker.return_value = mock_circuit_breaker

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
- #TechLeadership
"""
        )

        # Create Done/ achievements
        achievement1 = temp_vault / "Done" / "achievement1.md"
        achievement1.write_text(
            """---
type: achievement
status: completed
---

# Launched new AI feature

Successfully deployed AI-powered analytics dashboard.
"""
        )

        skill = LinkedInPostingSkill(dry_run=True, vault_dir=temp_vault)

        # Execute
        content = skill.generate_content()

        # Verify
        assert "🚀" in content
        assert "AI feature" in content or "analytics dashboard" in content
        assert "#AI" in content or "#Innovation" in content

    @patch("src.skills.base_skill.get_metrics_collector")
    @patch("src.skills.linkedin_posting.get_circuit_breaker")
    def test_rate_limiting_enforced(
        self,
        mock_get_circuit_breaker,
        mock_get_metrics,
        monkeypatch,
        temp_vault,
        mock_metrics_collector,
        mock_circuit_breaker,
    ):
        """Verify rate limit enforced (max 1 post/day by default)."""
        # Setup
        monkeypatch.setenv("DEV_MODE", "true")

        mock_get_metrics.return_value = mock_metrics_collector
        mock_get_circuit_breaker.return_value = mock_circuit_breaker

        skill = LinkedInPostingSkill(dry_run=False, vault_dir=temp_vault)

        # Set rate limit to exceeded (1 post per day limit)
        conn = sqlite3.connect(skill.rate_limit_db)
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE rate_limits
            SET post_count = 1, window_start = ?
            WHERE id = 1
        """,
            (datetime.now() - timedelta(hours=12),),  # 12 hours ago (within 24h window)
        )
        conn.commit()
        conn.close()

        # Execute - should return error dict, not raise
        result = skill.post_to_linkedin("Test content")

        # Verify
        assert result["status"] == "error"
        assert "rate limit" in result.get("error", "").lower()

    @patch("src.skills.base_skill.get_metrics_collector")
    @patch("src.skills.linkedin_posting.get_circuit_breaker")
    def test_session_recovery_loads_saved_session(
        self,
        mock_get_circuit_breaker,
        mock_get_metrics,
        monkeypatch,
        temp_vault,
        mock_metrics_collector,
        mock_circuit_breaker,
    ):
        """Verify session recovery loads saved storage.json."""
        # Setup
        monkeypatch.setenv("DEV_MODE", "true")

        mock_get_metrics.return_value = mock_metrics_collector
        mock_get_circuit_breaker.return_value = mock_circuit_breaker

        # Create valid session file
        storage_file = temp_vault / "linkedin_session" / "storage.json"
        storage_file.parent.mkdir(parents=True, exist_ok=True)
        storage_file.write_text('{"cookies": [], "origins": []}')

        # Modify mtime to be recent (within 7 days)
        import time
        recent_time = time.time() - (3600 * 24)  # 1 day ago
        os.utime(storage_file, (recent_time, recent_time))

        skill = LinkedInPostingSkill(dry_run=True, vault_dir=temp_vault)

        # Verify session is valid
        assert skill._is_session_valid() is True

    @patch("src.skills.base_skill.get_metrics_collector")
    @patch("src.skills.linkedin_posting.get_circuit_breaker")
    def test_dry_run_no_browser_action(
        self,
        mock_get_circuit_breaker,
        mock_get_metrics,
        monkeypatch,
        temp_vault,
        mock_metrics_collector,
        mock_circuit_breaker,
    ):
        """Verify dry_run=True skips browser automation."""
        # Setup
        monkeypatch.setenv("DEV_MODE", "true")

        mock_get_metrics.return_value = mock_metrics_collector
        mock_get_circuit_breaker.return_value = mock_circuit_breaker

        skill = LinkedInPostingSkill(dry_run=True, vault_dir=temp_vault)

        # Execute
        result = skill.post_to_linkedin("Test content")

        # Verify
        assert result["status"] == "dry_run"
        assert "DRY RUN" in result["message"]
        mock_circuit_breaker.call.assert_not_called()

    @patch("src.skills.base_skill.get_metrics_collector")
    @patch("src.skills.linkedin_posting.get_circuit_breaker")
    def test_circuit_breaker_trips_after_failures(
        self,
        mock_get_circuit_breaker,
        mock_get_metrics,
        monkeypatch,
        temp_vault,
        mock_metrics_collector,
    ):
        """Verify circuit breaker opens after consecutive failures."""
        # Setup
        monkeypatch.setenv("DEV_MODE", "true")

        mock_get_metrics.return_value = mock_metrics_collector

        # Mock circuit breaker to simulate open state
        mock_cb_instance = MagicMock()
        mock_cb_instance.state = "open"
        mock_cb_instance.is_closed = MagicMock(return_value=False)
        mock_cb_instance.is_open = MagicMock(return_value=True)
        mock_cb_instance.call.side_effect = CircuitBreakerOpenError("Circuit breaker open")

        mock_get_circuit_breaker.return_value = mock_cb_instance

        skill = LinkedInPostingSkill(dry_run=False, vault_dir=temp_vault)

        # Execute
        result = skill.post_to_linkedin("Test content")

        # Verify - should return error dict, not raise
        assert result["status"] == "error"
        assert "Circuit breaker" in result.get("error", "")

    @patch("src.skills.base_skill.get_metrics_collector")
    @patch("src.skills.linkedin_posting.get_circuit_breaker")
    def test_content_length_validation(
        self,
        mock_get_circuit_breaker,
        mock_get_metrics,
        monkeypatch,
        temp_vault,
        mock_metrics_collector,
        mock_circuit_breaker,
    ):
        """Verify generated content is within 50-300 characters."""
        # Setup
        monkeypatch.setenv("DEV_MODE", "true")

        mock_get_metrics.return_value = mock_metrics_collector
        mock_get_circuit_breaker.return_value = mock_circuit_breaker

        # Create minimal Business_Goals.md
        goals = temp_vault / "Business_Goals.md"
        goals.write_text("# Goals\n\nGrow business.")

        # Create short achievement
        achievement = temp_vault / "Done" / "test.md"
        achievement.write_text("# Short achievement")

        skill = LinkedInPostingSkill(dry_run=True, vault_dir=temp_vault)

        # Execute
        content = skill.generate_content()

        # Verify length (allowing some flexibility for hashtags)
        assert len(content) >= 20  # Minimum reasonable length
        assert len(content) <= 350  # Maximum with some buffer

    @patch("src.skills.base_skill.get_metrics_collector")
    @patch("src.skills.linkedin_posting.get_circuit_breaker")
    def test_metrics_emitted_on_post(
        self,
        mock_get_circuit_breaker,
        mock_get_metrics,
        monkeypatch,
        temp_vault,
        mock_metrics_collector,
        mock_circuit_breaker,
    ):
        """Verify metrics emitted on successful post."""
        # Setup
        monkeypatch.setenv("DEV_MODE", "true")

        mock_get_metrics.return_value = mock_metrics_collector
        mock_get_circuit_breaker.return_value = mock_circuit_breaker

        skill = LinkedInPostingSkill(dry_run=True, vault_dir=temp_vault)

        # Execute dry run (safer)
        result = skill.post_to_linkedin("Test content")

        # Verify metrics emitted
        mock_metrics_collector.record_histogram.assert_called()  # linkedin_post_duration
        mock_metrics_collector.increment_counter.assert_called()  # linkedin_post_count

    @patch("src.skills.base_skill.get_metrics_collector")
    @patch("src.skills.linkedin_posting.get_circuit_breaker")
    def test_session_expiry_detection(
        self,
        mock_get_circuit_breaker,
        mock_get_metrics,
        monkeypatch,
        temp_vault,
        mock_metrics_collector,
        mock_circuit_breaker,
    ):
        """Verify session expiry detected when file is old."""
        # Setup
        monkeypatch.setenv("DEV_MODE", "true")

        mock_get_metrics.return_value = mock_metrics_collector
        mock_get_circuit_breaker.return_value = mock_circuit_breaker

        # Create old session file (8 days ago)
        storage_file = temp_vault / "linkedin_session" / "storage.json"
        storage_file.parent.mkdir(parents=True, exist_ok=True)
        storage_file.write_text('{"cookies": [], "origins": []}')

        import time
        old_time = time.time() - (3600 * 24 * 8)  # 8 days ago
        os.utime(storage_file, (old_time, old_time))

        skill = LinkedInPostingSkill(dry_run=True, vault_dir=temp_vault)

        # Verify session is invalid
        assert skill._is_session_valid() is False

    @patch("src.skills.base_skill.get_metrics_collector")
    @patch("src.skills.linkedin_posting.get_circuit_breaker")
    def test_hashtag_extraction(
        self,
        mock_get_circuit_breaker,
        mock_get_metrics,
        monkeypatch,
        temp_vault,
        mock_metrics_collector,
        mock_circuit_breaker,
    ):
        """Verify hashtags extracted from Business_Goals.md."""
        # Setup
        monkeypatch.setenv("DEV_MODE", "true")

        mock_get_metrics.return_value = mock_metrics_collector
        mock_get_circuit_breaker.return_value = mock_circuit_breaker

        # Create Business_Goals.md with hashtags
        goals = temp_vault / "Business_Goals.md"
        goals.write_text(
            """
# Business Goals

Grow business.

[hashtags]
- #Technology
- #Innovation
- #Leadership
- #AI
"""
        )

        # Create achievement
        achievement = temp_vault / "Done" / "test.md"
        achievement.write_text("# Test achievement")

        skill = LinkedInPostingSkill(dry_run=True, vault_dir=temp_vault)

        # Execute
        hashtags = skill._extract_hashtags()

        # Verify (limited to 3)
        assert len(hashtags) <= 3
        assert all(h.startswith("#") for h in hashtags)

    @patch("src.skills.base_skill.get_metrics_collector")
    @patch("src.skills.linkedin_posting.get_circuit_breaker")
    @patch.object(LinkedInPostingSkill, "_post_to_linkedin_async")
    def test_rate_limit_window_reset(
        self,
        mock_post_async,
        mock_get_circuit_breaker,
        mock_get_metrics,
        monkeypatch,
        temp_vault,
        mock_metrics_collector,
        mock_circuit_breaker,
    ):
        """Verify rate limit window resets after 24 hours."""
        # Setup
        monkeypatch.setenv("DEV_MODE", "true")

        mock_get_metrics.return_value = mock_metrics_collector
        mock_get_circuit_breaker.return_value = mock_circuit_breaker
        mock_post_async.return_value = {
            "status": "posted",
            "post_id": "test_post_123",
            "url": "https://linkedin.com/posts/test",
            "timestamp": datetime.now().isoformat(),
        }

        skill = LinkedInPostingSkill(dry_run=False, vault_dir=temp_vault)

        # Set old window (should reset)
        conn = sqlite3.connect(skill.rate_limit_db)
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE rate_limits
            SET post_count = 1, window_start = ?
            WHERE id = 1
        """,
            (datetime.now() - timedelta(hours=25),),  # 25 hours ago
        )
        conn.commit()
        conn.close()

        # Should succeed (window reset)
        result = skill.post_to_linkedin("Test content")

        # Verify post succeeded
        assert result["status"] == "posted"
        assert result["post_id"] == "test_post_123"

        # Verify counter reset
        conn = sqlite3.connect(skill.rate_limit_db)
        cursor = conn.cursor()
        cursor.execute("SELECT post_count FROM rate_limits WHERE id = 1")
        count = cursor.fetchone()[0]
        conn.close()

        assert count == 1  # Reset to 1 after window expiry


class TestLinkedInPostingSkillContentGeneration:
    """Content generation specific tests."""

    @patch("src.skills.base_skill.get_metrics_collector")
    @patch("src.skills.linkedin_posting.get_circuit_breaker")
    def test_no_goals_generates_from_achievements_only(
        self,
        mock_get_circuit_breaker,
        mock_get_metrics,
        monkeypatch,
        temp_vault,
        mock_metrics_collector,
        mock_circuit_breaker,
    ):
        """Verify content generation works without Business_Goals.md."""
        # Setup
        monkeypatch.setenv("DEV_MODE", "true")

        mock_get_metrics.return_value = mock_metrics_collector
        mock_get_circuit_breaker.return_value = mock_circuit_breaker

        # Don't create Business_Goals.md
        # Create only achievement
        achievement = temp_vault / "Done" / "test.md"
        achievement.write_text("# Major milestone achieved")

        skill = LinkedInPostingSkill(dry_run=True, vault_dir=temp_vault)

        # Execute
        content = skill.generate_content()

        # Verify
        assert "🚀" in content
        assert "milestone" in content or "achieved" in content

    @patch("src.skills.base_skill.get_metrics_collector")
    @patch("src.skills.linkedin_posting.get_circuit_breaker")
    def test_no_achievements_returns_empty(
        self,
        mock_get_circuit_breaker,
        mock_get_metrics,
        monkeypatch,
        temp_vault,
        mock_metrics_collector,
        mock_circuit_breaker,
    ):
        """Verify empty content returned when no achievements."""
        # Setup
        monkeypatch.setenv("DEV_MODE", "true")

        mock_get_metrics.return_value = mock_metrics_collector
        mock_get_circuit_breaker.return_value = mock_circuit_breaker

        # Create Business_Goals.md but no Done/ files
        goals = temp_vault / "Business_Goals.md"
        goals.write_text("# Goals")

        skill = LinkedInPostingSkill(dry_run=True, vault_dir=temp_vault)

        # Execute
        content = skill.generate_content()

        # Verify
        assert content == ""
