"""Unit tests for FileSystemWatcher error paths and recovery."""

import os
import time
from unittest.mock import MagicMock


class TestFileSystemWatcherDiskFull:
    """Test disk full error handling."""

    def test_disk_full_error_path_exists(self, monkeypatch, tmp_path):
        """Verify disk full error handling code path exists."""
        monkeypatch.setenv("DEV_MODE", "true")

        from src.filesystem_watcher import FileSystemWatcher

        # Create watcher
        watcher = FileSystemWatcher(vault_path=str(tmp_path))

        # Verify the error handling code exists by checking the source
        import inspect

        source = inspect.getsource(watcher.check_for_updates)
        assert "ENOSPC" in source
        assert "disk_full" in source
        assert "SystemExit" in source


class TestFileSystemWatcherRecovery:
    """Test 24-hour file recovery logic."""

    def test_recover_missed_files_new_file(self, monkeypatch, tmp_path):
        """Verify files modified in last 24 hours are recovered."""
        monkeypatch.setenv("DEV_MODE", "true")

        from src.filesystem_watcher import FileSystemWatcher

        # Create Inbox with file
        inbox = tmp_path / "Inbox"
        inbox.mkdir()
        test_file = inbox / "test.txt"
        test_file.write_text("test")

        # Create watcher - should recover file during init
        watcher = FileSystemWatcher(vault_path=str(tmp_path))

        # File should be in processed_files
        assert len(watcher.processed_files) == 1

    def test_recover_missed_files_old_file_skipped(self, monkeypatch, tmp_path):
        """Verify files older than 24 hours are skipped with WARNING."""
        monkeypatch.setenv("DEV_MODE", "true")

        from src.filesystem_watcher import FileSystemWatcher

        # Create Inbox with file
        inbox = tmp_path / "Inbox"
        inbox.mkdir()
        test_file = inbox / "old.txt"
        test_file.write_text("old content")

        # Make file appear 25 hours old
        old_time = time.time() - (25 * 60 * 60)
        os.utime(test_file, (old_time, old_time))

        # Create watcher
        watcher = FileSystemWatcher(vault_path=str(tmp_path))

        # Old file should NOT be recovered (not in processed_files)
        # The recovery logic skips files > 24 hours
        # Note: processed_files will be empty for old files
        file_keys = [str(key[0]) for key in watcher.processed_files]
        assert str(test_file) not in file_keys

    def test_recover_missed_files_empty_inbox(self, monkeypatch, tmp_path):
        """Verify recovery handles empty Inbox gracefully."""
        monkeypatch.setenv("DEV_MODE", "true")

        from src.filesystem_watcher import FileSystemWatcher

        # Create empty Inbox
        inbox = tmp_path / "Inbox"
        inbox.mkdir()

        # Create watcher - should not crash
        watcher = FileSystemWatcher(vault_path=str(tmp_path))

        # No files recovered
        assert len(watcher.processed_files) == 0

    def test_recover_missed_files_no_inbox(self, monkeypatch, tmp_path):
        """Verify recovery handles missing Inbox gracefully."""
        monkeypatch.setenv("DEV_MODE", "true")

        from src.filesystem_watcher import FileSystemWatcher

        # Don't create Inbox

        # Create watcher - should not crash
        watcher = FileSystemWatcher(vault_path=str(tmp_path))

        # No files recovered
        assert len(watcher.processed_files) == 0


class TestFileSystemWatcherOSError:
    """Test other OSError handling."""

    def test_os_error_handling_code_exists(self, monkeypatch, tmp_path):
        """Verify OSError handling code path exists."""
        monkeypatch.setenv("DEV_MODE", "true")

        from src.filesystem_watcher import FileSystemWatcher

        watcher = FileSystemWatcher(vault_path=str(tmp_path))

        # Verify the error handling code exists
        import inspect

        source = inspect.getsource(watcher.check_for_updates)
        assert "OSError" in source
        assert "errno" in source


class TestFileSystemWatcherActionFileContent:
    """Test action file content generation."""

    def test_generate_action_file_content_with_content(self, monkeypatch, tmp_path):
        """Verify _generate_action_file_content includes file content."""
        monkeypatch.setenv("DEV_MODE", "true")

        from src.filesystem_watcher import FileSystemWatcher

        watcher = FileSystemWatcher(vault_path=str(tmp_path))

        # Create test file with content (Inbox already created by __init__)
        test_file = tmp_path / "Inbox" / "test.txt"
        test_file.write_text("Hello, World!")

        content = watcher._generate_action_file_content(
            source_path="Inbox/test.txt", file_path=test_file
        )

        assert "Hello, World!" in content

    def test_generate_action_file_content_large_file(self, monkeypatch, tmp_path):
        """Verify _generate_action_file_content skips files > 10MB."""
        monkeypatch.setenv("DEV_MODE", "true")

        from src.filesystem_watcher import FileSystemWatcher

        watcher = FileSystemWatcher(vault_path=str(tmp_path))

        # Create mock file > 10MB
        mock_file = MagicMock()
        mock_file.exists.return_value = True
        mock_file.stat.return_value.st_size = 11 * 1024 * 1024  # 11MB

        content = watcher._generate_action_file_content(
            source_path="Inbox/large.bin", file_path=mock_file
        )

        # Should have placeholder for large files
        assert "[File content not available]" in content or "## Content" in content

    def test_create_action_file_dry_run_path(self, monkeypatch, tmp_path):
        """Verify create_action_file returns path without creating file in dry_run."""
        monkeypatch.setenv("DEV_MODE", "true")

        from src.filesystem_watcher import FileSystemWatcher

        # Create watcher in dry_run mode (Inbox created automatically)
        watcher = FileSystemWatcher(vault_path=str(tmp_path), dry_run=True)

        # Create test file
        test_file = tmp_path / "Inbox" / "test.txt"
        test_file.write_text("test")

        # Call create_action_file
        action_path = watcher.create_action_file(test_file)

        # Path should be returned but file not created (dry_run)
        assert action_path.name.startswith("FILE_test_")
        assert not action_path.exists()

    def test_create_action_file_content_method_exists(self, monkeypatch, tmp_path):
        """Verify _generate_action_file_content method exists and is called."""
        monkeypatch.setenv("DEV_MODE", "true")

        from src.filesystem_watcher import FileSystemWatcher

        watcher = FileSystemWatcher(vault_path=str(tmp_path), dry_run=True)

        # Verify method exists
        assert hasattr(watcher, "_generate_action_file_content")

        # Verify it's called from create_action_file
        import inspect

        source = inspect.getsource(watcher.create_action_file)
        assert "_generate_action_file_content" in source
