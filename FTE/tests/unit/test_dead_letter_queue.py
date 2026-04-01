"""
Unit tests for Dead Letter Queue.

Tests cover:
- Archive action
- Retry tracking
- Manual reprocess
- SQLite persistence
- Query failed actions
"""

import json
import sqlite3
from pathlib import Path

import pytest

from src.utils.dead_letter_queue import DeadLetterQueue, DeadLetterQueueError


@pytest.fixture
def temp_db(tmp_path):
    """Create a temporary database for testing."""
    db_path = tmp_path / "test_failed_actions.db"
    yield str(db_path)


@pytest.fixture
def temp_vault(tmp_path):
    """Create a temporary vault directory."""
    vault_dir = tmp_path / "vault"
    vault_dir.mkdir()
    # Create Failed_Actions subdirectory
    (vault_dir / "Failed_Actions").mkdir()
    yield str(vault_dir)


@pytest.fixture
def dlq(temp_db, temp_vault):
    """Create DLQ instance with temporary storage."""
    return DeadLetterQueue(db_path=temp_db, vault_dir=temp_vault, max_retries=3)


class TestArchiveAction:
    """Test action archiving."""

    def test_archive_action(self, dlq, temp_db, temp_vault):
        """Should archive failed action to database and file."""
        action_id = dlq.archive_action(
            original_action="send_email",
            failure_reason="SMTP connection timeout",
            details={"to": "user@example.com"},
        )

        assert action_id is not None

        # Verify database
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM failed_actions WHERE id = ?", (action_id,))
        row = cursor.fetchone()
        conn.close()

        assert row is not None
        assert row[1] == "send_email"  # original_action
        assert row[2] == "SMTP connection timeout"  # failure_reason

        # Verify file
        file_path = Path(temp_vault) / "Failed_Actions" / f"DLQ_{action_id}.md"
        assert file_path.exists()

        with open(file_path) as f:
            content = f.read()
            assert "send_email" in content
            assert "SMTP connection timeout" in content

    def test_archive_action_with_metadata(self, dlq):
        """Should archive action with original metadata."""
        action_id = dlq.archive_action(
            original_action="send_whatsapp",
            failure_reason="Session expired",
            details={"contact": "+1234567890"},
            original_metadata={"message": "Hello", "priority": "high"},
        )

        actions = dlq.get_failed_actions(action_type="send_whatsapp")
        assert len(actions) == 1
        assert actions[0]["original_metadata"]["message"] == "Hello"


class TestRetryTracking:
    """Test retry count tracking."""

    def test_retry_tracking(self, dlq):
        """Should track retry count per action."""
        action_id = dlq.archive_action(
            original_action="test_action",
            failure_reason="First failure",
        )

        # Increment failure count
        dlq.increment_failure_count(action_id, "Second failure")

        count = dlq.get_retry_count(action_id)
        assert count == 2

    def test_increment_failure_count(self, dlq):
        """Should increment failure count correctly."""
        action_id = dlq.archive_action(
            original_action="test_action",
            failure_reason="First failure",
        )

        # Increment twice
        dlq.increment_failure_count(action_id, "Second failure")
        dlq.increment_failure_count(action_id, "Third failure")

        count = dlq.get_retry_count(action_id)
        assert count == 3

    def test_increment_nonexistent_action(self, dlq):
        """Should return False for nonexistent action."""
        result = dlq.increment_failure_count("nonexistent-id", "Failure")
        assert result is False


class TestManualReprocess:
    """Test manual reprocessing."""

    def test_manual_reprocess(self, dlq):
        """Should mark action for reprocessing."""
        action_id = dlq.archive_action(
            original_action="test_action",
            failure_reason="Temporary failure",
        )

        result = dlq.reprocess(action_id)
        assert result is True

        # Verify status changed
        actions = dlq.get_failed_actions(status="pending_reprocess")
        assert len(actions) == 1
        assert actions[0]["id"] == action_id

    def test_reprocess_exceeds_max_retries(self, dlq):
        """Should not reprocess if max retries exceeded."""
        action_id = dlq.archive_action(
            original_action="test_action",
            failure_reason="First failure",
        )

        # Increment to max retries
        dlq.increment_failure_count(action_id, "Second failure")
        dlq.increment_failure_count(action_id, "Third failure")

        # Try to reprocess
        result = dlq.reprocess(action_id)
        assert result is False

    def test_reprocess_nonexistent_action(self, dlq):
        """Should return False for nonexistent action."""
        result = dlq.reprocess("nonexistent-id")
        assert result is False


class TestPersistence:
    """Test SQLite persistence."""

    def test_persistence(self, temp_db, temp_vault):
        """Actions should persist to SQLite."""
        dlq1 = DeadLetterQueue(db_path=temp_db, vault_dir=temp_vault)
        action_id = dlq1.archive_action(
            original_action="persist_test",
            failure_reason="Test failure",
        )

        # Create new instance (simulating restart)
        dlq2 = DeadLetterQueue(db_path=temp_db, vault_dir=temp_vault)

        # Should find archived action
        actions = dlq2.get_failed_actions()
        assert len(actions) == 1
        assert actions[0]["id"] == action_id


class TestQueryFailedActions:
    """Test querying failed actions."""

    def test_query_failed_actions(self, dlq):
        """Should return list of failed actions."""
        dlq.archive_action("action_a", "Failure A")
        dlq.archive_action("action_b", "Failure B")
        dlq.archive_action("action_c", "Failure C")

        actions = dlq.get_failed_actions(limit=10)
        assert len(actions) == 3

    def test_query_with_limit(self, dlq):
        """Should respect limit parameter."""
        for i in range(10):
            dlq.archive_action(f"action_{i}", f"Failure {i}")

        actions = dlq.get_failed_actions(limit=5)
        assert len(actions) == 5

    def test_query_by_action_type(self, dlq):
        """Should filter by action type."""
        dlq.archive_action("send_email", "Email failure")
        dlq.archive_action("send_whatsapp", "WhatsApp failure")
        dlq.archive_action("send_email", "Another email failure")

        actions = dlq.get_failed_actions(action_type="send_email")
        assert len(actions) == 2
        assert all(a["original_action"] == "send_email" for a in actions)

    def test_query_by_status(self, dlq):
        """Should filter by status."""
        action_id = dlq.archive_action("test_action", "Failure")
        dlq.reprocess(action_id)

        failed = dlq.get_failed_actions(status="failed")
        pending = dlq.get_failed_actions(status="pending_reprocess")

        assert len(failed) == 0  # Status changed to pending
        assert len(pending) == 1


class TestDeleteAction:
    """Test action deletion."""

    def test_delete_action(self, dlq, temp_vault):
        """Should delete action from database and file."""
        action_id = dlq.archive_action(
            original_action="delete_test",
            failure_reason="Test failure",
        )

        # Verify exists
        actions = dlq.get_failed_actions()
        assert len(actions) == 1

        # Delete
        result = dlq.delete_action(action_id)
        assert result is True

        # Verify deleted
        actions = dlq.get_failed_actions()
        assert len(actions) == 0

        # Verify file deleted
        file_path = Path(temp_vault) / "Failed_Actions" / f"DLQ_{action_id}.md"
        assert not file_path.exists()

    def test_delete_nonexistent_action(self, dlq):
        """Should return False for nonexistent action."""
        result = dlq.delete_action("nonexistent-id")
        assert result is False


class TestRetryLimit:
    """Test retry limit enforcement."""

    def test_is_under_retry_limit(self, dlq):
        """Should correctly check retry limit."""
        action_id = dlq.archive_action(
            original_action="limit_test",
            failure_reason="First failure",
        )

        # Should be under limit initially
        assert dlq.is_under_retry_limit(action_id) is True

        # Increment to max
        dlq.increment_failure_count(action_id, "Second failure")
        dlq.increment_failure_count(action_id, "Third failure")

        # Should be at limit
        assert dlq.is_under_retry_limit(action_id) is False

    def test_is_under_retry_limit_nonexistent(self, dlq):
        """Should return False for nonexistent action."""
        result = dlq.is_under_retry_limit("nonexistent-id")
        assert result is False
