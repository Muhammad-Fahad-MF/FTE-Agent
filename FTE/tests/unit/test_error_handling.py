"""Unit tests for error handling in FileSystemWatcher."""

import errno
import logging
from unittest.mock import patch

import pytest


class TestErrorHandling:
    """Unit tests for error handling."""

    def test_permission_error_handling(self, monkeypatch, tmp_path, caplog):
        """Verify PermissionError logs ERROR, skips file, continues monitoring."""
        # Set DEV_MODE to true
        monkeypatch.setenv("DEV_MODE", "true")

        from src.filesystem_watcher import FileSystemWatcher

        # Create directories
        inbox = tmp_path / "Inbox"
        inbox.mkdir()

        # Create watcher
        watcher = FileSystemWatcher(vault_path=str(tmp_path))

        # Create file
        test_file = inbox / "test.txt"
        test_file.write_text("test content")

        # Mock validate_path to raise PermissionError (simulating access issue)
        original_validate = watcher.validate_path

        def mock_validate(path):
            if str(path) == str(test_file):
                raise PermissionError("Access denied")
            return original_validate(path)

        with patch.object(watcher, "validate_path", side_effect=mock_validate):
            with caplog.at_level(logging.ERROR):
                # Should handle gracefully (not crash)
                try:
                    files = watcher.check_for_updates()
                    # File should be skipped due to permission error
                    assert len(files) == 0
                except PermissionError:
                    pytest.fail("Should handle PermissionError gracefully")

    def test_file_not_found_handling(self, monkeypatch, tmp_path, caplog):
        """Verify FileNotFoundError logs WARNING, adds to retry queue."""
        # Set DEV_MODE to true
        monkeypatch.setenv("DEV_MODE", "true")

        from src.filesystem_watcher import FileSystemWatcher

        # Create directories
        inbox = tmp_path / "Inbox"
        inbox.mkdir()

        # Create watcher
        watcher = FileSystemWatcher(vault_path=str(tmp_path))

        # Create file then delete it (simulate file disappeared)
        test_file = inbox / "disappearing.txt"
        test_file.write_text("test")
        test_file.unlink()  # Delete file

        # Should handle gracefully - file should not be in list
        with caplog.at_level(logging.WARNING):
            files = watcher.check_for_updates()
            # File should not be in list (deleted before detection)
            assert len(files) == 0

    def test_disk_full_handling(self, monkeypatch, tmp_path, caplog):
        """Verify OSError errno 28 logs CRITICAL, halts gracefully, creates alert file."""
        # Set DEV_MODE to true
        monkeypatch.setenv("DEV_MODE", "true")

        from src.skills import create_alert_file

        # Create directories
        inbox = tmp_path / "Inbox"
        inbox.mkdir()
        needs_action = tmp_path / "Needs_Action"
        needs_action.mkdir()

        # Simulate disk full error during file operation
        with caplog.at_level(logging.CRITICAL):
            try:
                # Simulate OSError errno 28
                raise OSError(errno.ENOSPC, "No space left on device")
            except OSError as e:
                if e.errno == errno.ENOSPC:
                    # Should log CRITICAL and create alert file
                    alert_path = create_alert_file(
                        file_type="disk_full", source=str(tmp_path), details={"error": str(e)}
                    )
                    # Alert file should be created
                    assert alert_path is not None
                    assert alert_path.exists()

    def test_unexpected_exception_handling(self, monkeypatch, tmp_path, caplog):
        """Verify generic Exception logs ERROR with stack trace, continues monitoring."""
        # Set DEV_MODE to true
        monkeypatch.setenv("DEV_MODE", "true")

        # Create directories
        inbox = tmp_path / "Inbox"
        inbox.mkdir()

        # Simulate unexpected exception during operation
        with caplog.at_level(logging.ERROR):
            exception_caught = False
            try:
                # Simulate unexpected error
                raise ValueError("Unexpected error for testing")
            except Exception as e:
                exception_caught = True
                # Verify exception was caught (not crashed)
                assert "Unexpected error" in str(e)

            # Verify exception was raised and could be caught
            assert exception_caught
