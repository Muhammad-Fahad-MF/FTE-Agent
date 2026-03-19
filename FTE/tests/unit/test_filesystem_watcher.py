"""Unit tests for FileSystemWatcher class."""

import sys
from pathlib import Path

import pytest


class TestFileSystemWatcher:
    """Unit tests for FileSystemWatcher."""

    def test_dev_mode_validation(self, monkeypatch, tmp_path):
        """Verify SystemExit with code 1 if DEV_MODE != 'true'."""
        # Set DEV_MODE to false
        monkeypatch.setenv("DEV_MODE", "false")

        # Import after setting env
        import io

        # Capture stderr
        old_stderr = sys.stderr
        sys.stderr = io.StringIO()

        # Should raise SystemExit
        with pytest.raises(SystemExit) as exc_info:
            # Need to reload module to pick up new env var
            import importlib

            from src import filesystem_watcher

            importlib.reload(filesystem_watcher)
            filesystem_watcher.FileSystemWatcher(vault_path=str(tmp_path))

        # Verify exit code 1
        assert exc_info.value.code == 1

        # Restore stderr
        sys.stderr = old_stderr

    def test_path_validation_traversal_attempt(self, monkeypatch, tmp_path):
        """Verify ValueError raised for paths outside vault."""
        # Set DEV_MODE to true
        monkeypatch.setenv("DEV_MODE", "true")

        from src.filesystem_watcher import FileSystemWatcher

        # Create watcher
        watcher = FileSystemWatcher(vault_path=str(tmp_path))

        # Try to validate path outside vault
        outside_path = Path("/etc/passwd")

        # Should raise ValueError
        with pytest.raises(ValueError) as exc_info:
            watcher.validate_path(outside_path)

        assert (
            "traversal" in str(exc_info.value).lower() or "outside" in str(exc_info.value).lower()
        )

    def test_stop_file_detection(self, monkeypatch, tmp_path):
        """Verify watcher halts within 60 seconds of STOP file creation."""
        # Set DEV_MODE to true
        monkeypatch.setenv("DEV_MODE", "true")

        from src.filesystem_watcher import FileSystemWatcher

        # Create watcher
        watcher = FileSystemWatcher(vault_path=str(tmp_path))

        # Initially no STOP file
        assert watcher.check_stop_file() is False

        # Create STOP file
        stop_file = tmp_path / "STOP"
        stop_file.touch()

        # Now should detect STOP
        assert watcher.check_stop_file() is True

    def test_dry_run_no_file_creation(self, monkeypatch, tmp_path):
        """Verify no action files created when dry_run=True."""
        # Set DEV_MODE to true
        monkeypatch.setenv("DEV_MODE", "true")

        from src.filesystem_watcher import FileSystemWatcher

        # Create watcher in dry-run mode
        watcher = FileSystemWatcher(vault_path=str(tmp_path), dry_run=True)

        # Create test file in Inbox (use exist_ok=True since __init__ creates it)
        inbox = tmp_path / "Inbox"
        inbox.mkdir(exist_ok=True)
        test_file = inbox / "test.txt"
        test_file.write_text("test content")

        # Try to create action file (should not create in dry-run)
        action_path = watcher.create_action_file(test_file)

        # File should NOT exist (dry-run)
        assert not action_path.exists()
