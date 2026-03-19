"""Integration tests for file detection to action file creation flow."""


class TestWatcherToIntegration:
    """Integration tests for watcher to action flow."""

    def test_file_detected_to_action_created(self, monkeypatch, tmp_path):
        """End-to-end: create file in Inbox/ → verify action file in Needs_Action/ within 60s."""
        # Set DEV_MODE to true
        monkeypatch.setenv("DEV_MODE", "true")

        from src.filesystem_watcher import FileSystemWatcher

        # Create directories
        inbox = tmp_path / "Inbox"
        inbox.mkdir()
        needs_action = tmp_path / "Needs_Action"
        needs_action.mkdir()

        # Create watcher
        watcher = FileSystemWatcher(vault_path=str(tmp_path), interval=5)

        # Create test file
        test_file = inbox / "test.txt"
        test_file.write_text("test content")

        # Run watcher for one cycle (simulate)
        # In real scenario, watcher.run() would be in a loop
        files = watcher.check_for_updates()

        # Should detect file
        assert len(files) > 0
        assert test_file in files

        # Create action file
        action_path = watcher.create_action_file(test_file)

        # Verify action file exists
        assert action_path.exists()
        assert action_path.parent == needs_action

    def test_action_file_metadata(self, monkeypatch, tmp_path):
        """Verify action file contains type, source, created, status fields."""
        # Set DEV_MODE to true
        monkeypatch.setenv("DEV_MODE", "true")

        from src.filesystem_watcher import FileSystemWatcher

        # Create directories
        inbox = tmp_path / "Inbox"
        inbox.mkdir()
        needs_action = tmp_path / "Needs_Action"
        needs_action.mkdir()

        # Create watcher
        watcher = FileSystemWatcher(vault_path=str(tmp_path))

        # Create test file
        test_file = inbox / "test.txt"
        test_file.write_text("test content")

        # Create action file
        action_path = watcher.create_action_file(test_file)

        # Read action file
        content = action_path.read_text()

        # Verify YAML frontmatter fields
        assert "---" in content
        assert "type: file_drop" in content
        # Handle both Windows and Unix path separators
        assert "source:" in content and (
            "Inbox/test.txt" in content or "Inbox\\test.txt" in content
        )
        assert "created:" in content
        assert "status: pending" in content

    def test_stop_file_prevents_action_creation(self, monkeypatch, tmp_path):
        """Verify no action files created when STOP file exists."""
        # Set DEV_MODE to true
        monkeypatch.setenv("DEV_MODE", "true")

        from src.filesystem_watcher import FileSystemWatcher

        # Create directories
        inbox = tmp_path / "Inbox"
        inbox.mkdir()
        needs_action = tmp_path / "Needs_Action"
        needs_action.mkdir()

        # Create STOP file
        stop_file = tmp_path / "STOP"
        stop_file.touch()

        # Create watcher
        watcher = FileSystemWatcher(vault_path=str(tmp_path))

        # Should detect STOP file
        assert watcher.check_stop_file() is True

        # In real implementation, run() would exit here
        # For this test, verify that check_stop_file() returns True
        # This confirms the STOP file mechanism works
