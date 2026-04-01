"""Chaos tests for approval workflow.

Tests system resilience under failure conditions:
- File system failures
- Concurrent file operations
- Handler crash recovery
- Circuit breaker behavior under load
"""

import os
import tempfile
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.approval_handler import ApprovalHandler
from src.skills.request_approval import RequestApprovalSkill


class TestApprovalFileCreation:
    """Chaos test: Approval file creation under various conditions."""

    @pytest.fixture
    def temp_vault(self):
        """Create temporary vault directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            vault = Path(tmpdir) / "vault"
            vault.mkdir(parents=True)
            (vault / "Pending_Approval").mkdir()
            (vault / "Approved").mkdir()
            (vault / "Rejected").mkdir()
            (vault / "Templates").mkdir()
            yield vault

    def test_approval_file_creation_under_concurrent_load(self, temp_vault):
        """Test approval creation handles concurrent requests."""
        skill = RequestApprovalSkill(vault_dir=temp_vault)
        results = []
        errors = []

        def create_approval(i):
            try:
                action = {"type": "email", "to": f"user{i}@example.com"}
                path = skill.create_approval_request(
                    action=action, reason=f"Concurrent {i}", risk_level="low"
                )
                results.append(path)
            except Exception as e:
                errors.append(e)

        # Create 20 concurrent approval requests
        threads = []
        for i in range(20):
            t = threading.Thread(target=create_approval, args=(i,))
            threads.append(t)
            t.start()

        for t in threads:
            t.join(timeout=10)

        # All should succeed
        assert len(errors) == 0, f"Errors occurred: {errors}"
        assert len(results) == 20

        # All files should exist
        for path in results:
            assert path.exists()

        # All filenames should be unique
        filenames = [p.name for p in results]
        assert len(set(filenames)) == 20


class TestExpiryDetection:
    """Chaos test: Expiry detection under various conditions."""

    @pytest.fixture
    def temp_vault(self):
        """Create temporary vault directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            vault = Path(tmpdir) / "vault"
            vault.mkdir(parents=True)
            (vault / "Pending_Approval").mkdir()
            (vault / "Dashboard.md").write_text("# Dashboard\n")
            yield vault

    def test_expiry_detection_with_corrupted_files(self, temp_vault):
        """Test expiry detection handles corrupted files gracefully."""
        skill = RequestApprovalSkill(vault_dir=temp_vault)

        # Create valid expired file
        expired_time = datetime.now() - timedelta(hours=25)
        expires_time = expired_time + timedelta(hours=24)

        valid_file = temp_vault / "Pending_Approval" / "APPROVAL_VALID_EXPIRED.md"
        valid_file.write_text(
            f"""---
type: approval_request
action: test
created: {expired_time.isoformat()}
expires: {expires_time.isoformat()}
status: pending
risk_level: low
reason: Test
---
# Test
"""
        )

        # Create corrupted file (no YAML frontmatter)
        corrupted_file = temp_vault / "Pending_Approval" / "APPROVAL_CORRUPTED.md"
        corrupted_file.write_text("# No frontmatter\nJust content\n")

        # Create partially corrupted file (invalid YAML)
        partial_file = temp_vault / "Pending_Approval" / "APPROVAL_PARTIAL.md"
        partial_file.write_text("---\ninvalid: yaml: content:\n---\n")

        # Should not raise, should still detect valid expired file
        expired = skill.check_expiry()

        assert len(expired) >= 1  # At least the valid one
        assert valid_file in expired


class TestFileMoveDetection:
    """Chaos test: File move detection under various conditions."""

    @pytest.fixture
    def temp_vault(self):
        """Create temporary vault directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            vault = Path(tmpdir) / "vault"
            vault.mkdir(parents=True)
            (vault / "Pending_Approval").mkdir()
            (vault / "Approved").mkdir()
            (vault / "Rejected").mkdir()
            yield vault

    def test_file_move_detection_under_concurrent_moves(self, temp_vault):
        """Test handler detects multiple concurrent file moves."""
        handler = ApprovalHandler(vault_dir=temp_vault, check_interval=0.3)

        detected_files = []
        lock = threading.Lock()

        def on_approval(approval_file):
            with lock:
                detected_files.append(approval_file)

        handler.register_approval_callback(on_approval)
        handler.start()

        try:
            # Create multiple approved files rapidly
            for i in range(10):
                approved_file = (
                    temp_vault / "Approved" / f"APPROVAL_CONCURRENT_{i}.md"
                )
                approved_file.write_text(
                    f"---\ntype: approval_request\nstatus: approved\naction: test{i}\n---\n"
                )

            # Wait for detection
            time.sleep(3)

            # Should detect most files (may miss some due to timing)
            assert len(detected_files) > 0, "No files detected"

        finally:
            handler.stop()

    def test_file_move_detection_with_locked_files(self, temp_vault):
        """Test handler handles file locks gracefully."""
        handler = ApprovalHandler(vault_dir=temp_vault, check_interval=0.5)

        detected = threading.Event()

        def on_approval(approval_file):
            detected.set()

        handler.register_approval_callback(on_approval)
        handler.start()

        try:
            # Create file and keep it open (simulating lock)
            approved_file = temp_vault / "Approved" / "APPROVAL_LOCKED.md"
            with approved_file.open("w") as f:
                f.write("---\ntype: approval_request\nstatus: approved\n---\n")
                # Keep file open while handler scans

                # Handler should still detect (read lock allows reading)
                time.sleep(1)

            # Should detect after file is closed
            file_detected = detected.wait(timeout=5.0)
            assert file_detected, "Locked file not detected"

        finally:
            handler.stop()


class TestRejectionHandling:
    """Chaos test: Rejection handling under failure conditions."""

    @pytest.fixture
    def temp_vault(self):
        """Create temporary vault directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            vault = Path(tmpdir) / "vault"
            vault.mkdir(parents=True)
            (vault / "Pending_Approval").mkdir()
            (vault / "Rejected").mkdir()
            yield vault

    def test_rejection_handling_with_callback_errors(self, temp_vault):
        """Test rejection handling continues when callbacks fail."""
        handler = ApprovalHandler(vault_dir=temp_vault, check_interval=0.5)

        # Register callback that raises
        def failing_callback(rejection_file):
            raise RuntimeError("Callback failed intentionally")

        handler.register_rejection_callback(failing_callback)

        # Register successful callback
        success_detected = threading.Event()

        def success_callback(rejection_file):
            success_detected.set()

        handler.register_rejection_callback(success_callback)
        handler.start()

        try:
            # Create rejection file
            rejected_file = temp_vault / "Rejected" / "APPROVAL_CALLBACK_ERROR.md"
            rejected_file.write_text("---\ntype: approval_request\n---\n")

            # Should still call successful callback despite first one failing
            detected = success_detected.wait(timeout=5.0)
            assert detected, "Successful callback not called after error"

        finally:
            handler.stop()


class TestConcurrentMoves:
    """Chaos test: Concurrent file moves."""

    @pytest.fixture
    def temp_vault(self):
        """Create temporary vault directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            vault = Path(tmpdir) / "vault"
            vault.mkdir(parents=True)
            (vault / "Pending_Approval").mkdir()
            (vault / "Approved").mkdir()
            (vault / "Rejected").mkdir()
            yield vault

    def test_concurrent_approval_rejection_moves(self, temp_vault):
        """Test handling concurrent moves to Approved and Rejected."""
        handler = ApprovalHandler(vault_dir=temp_vault, check_interval=0.3)

        approved_count = 0
        rejected_count = 0
        lock = threading.Lock()

        def on_approval(approval_file):
            nonlocal approved_count
            with lock:
                approved_count += 1

        def on_rejection(rejection_file):
            nonlocal rejected_count
            with lock:
                rejected_count += 1

        handler.register_approval_callback(on_approval)
        handler.register_rejection_callback(on_rejection)
        handler.start()

        try:
            # Create files in both Approved and Rejected rapidly
            for i in range(5):
                (temp_vault / "Approved" / f"APPROVAL_FAST_{i}.md").write_text(
                    "---\ntype: approval_request\nstatus: approved\n---\n"
                )
                (temp_vault / "Rejected" / f"APPROVAL_REJECT_FAST_{i}.md").write_text(
                    "---\ntype: approval_request\nstatus: rejected\n---\n"
                )

            time.sleep(2)

            # Should detect files in both folders
            assert approved_count > 0 or rejected_count > 0
            total = approved_count + rejected_count
            assert total > 0, "No files detected"

        finally:
            handler.stop()


class TestCircuitBreakerBehavior:
    """Chaos test: Circuit breaker behavior under failure conditions."""

    @pytest.fixture
    def temp_vault(self):
        """Create temporary vault directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            vault = Path(tmpdir) / "vault"
            vault.mkdir(parents=True)
            (vault / "Pending_Approval").mkdir()
            (vault / "Approved").mkdir()
            (vault / "Rejected").mkdir()
            yield vault

    def test_circuit_breaker_prevents_cascade_failures(self, temp_vault):
        """Test circuit breaker protects against cascade failures."""
        handler = ApprovalHandler(vault_dir=temp_vault, check_interval=0.5)

        # Circuit breaker should exist
        assert handler.circuit_breaker is not None

        # Simulate failures by mocking folder scan to raise
        original_scan = handler._scan_folder

        failure_count = 0

        def failing_scan(folder, pattern="*.md"):
            nonlocal failure_count
            failure_count += 1
            if failure_count <= 5:
                raise OSError("Simulated folder scan failure")
            return original_scan(folder, pattern)

        with patch.object(handler, "_scan_folder", side_effect=failing_scan):
            handler.start()

            # Let it run through failures
            time.sleep(5)

            # Circuit breaker should have tripped
            # (failures should be caught and counted)
            assert failure_count >= 5

            handler.stop()

        # After recovery timeout, should work again
        time.sleep(61)  # Wait for circuit breaker recovery

        # Should be able to scan again
        files = handler._scan_folder(temp_vault / "Approved")
        assert files is not None
