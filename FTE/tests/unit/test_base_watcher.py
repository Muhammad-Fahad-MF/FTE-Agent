"""Unit tests for BaseWatcher class."""

from pathlib import Path

from src.base_watcher import BaseWatcher


class TestBaseWatcher:
    """Unit tests for BaseWatcher abstract class."""

    def test_base_watcher_initialization(self, tmp_path):
        """Verify BaseWatcher initializes with correct attributes."""

        # Create concrete implementation for testing
        class TestWatcher(BaseWatcher):
            def check_for_updates(self) -> list[Path]:
                return []

        watcher = TestWatcher(vault_path=str(tmp_path), dry_run=True, interval=30)

        assert watcher.vault_path == tmp_path
        assert watcher.dry_run is True
        assert watcher.interval == 30
        assert len(watcher.processed_files) == 0

    def test_create_action_file_dry_run(self, tmp_path, caplog):
        """Verify create_action_file respects dry_run mode."""
        from src.base_watcher import BaseWatcher

        class TestWatcher(BaseWatcher):
            def check_for_updates(self) -> list[Path]:
                return []

        watcher = TestWatcher(vault_path=str(tmp_path), dry_run=True, interval=60)

        # Create test file
        test_file = tmp_path / "Inbox" / "test.txt"
        test_file.parent.mkdir()
        test_file.write_text("test content")

        # Call create_action_file in dry_run mode
        action_path = watcher.create_action_file(test_file)

        # File should not be created in dry_run mode
        assert not action_path.exists()
        # But path should be returned
        assert action_path.name.startswith("FILE_test_")
        assert action_path.name.endswith(".md")

    def test_create_action_file_creates_file(self, tmp_path):
        """Verify create_action_file creates file with correct content."""

        class TestWatcher(BaseWatcher):
            def check_for_updates(self) -> list[Path]:
                return []

        watcher = TestWatcher(vault_path=str(tmp_path), dry_run=False, interval=60)

        # Create test file
        test_file = tmp_path / "Inbox" / "test.txt"
        test_file.parent.mkdir()
        test_file.write_text("test content")

        # Call create_action_file
        action_path = watcher.create_action_file(test_file)

        # File should be created
        assert action_path.exists()

        # Verify content
        content = action_path.read_text()
        assert "---" in content
        assert "type: file_drop" in content
        # Handle both Windows and Unix path separators
        assert "source:" in content and (
            "Inbox/test.txt" in content or "Inbox\\test.txt" in content
        )
        assert "created:" in content
        assert "status: pending" in content
        assert "## Content" in content
        assert "## Suggested Actions" in content

    def test_create_action_file_outside_vault(self, tmp_path):
        """Verify create_action_file handles files outside vault."""

        class TestWatcher(BaseWatcher):
            def check_for_updates(self) -> list[Path]:
                return []

        watcher = TestWatcher(vault_path=str(tmp_path), dry_run=False, interval=60)

        # Create test file outside vault
        test_file = Path("C:/outside/test.txt")

        # Should use filename only when outside vault
        action_path = watcher.create_action_file(test_file)

        # File should be created with just filename in source
        assert action_path.exists()
        content = action_path.read_text()
        assert "source: test.txt" in content

    def test_run_method(self, tmp_path, monkeypatch):
        """Verify run method executes main loop."""

        class TestWatcher(BaseWatcher):
            def __init__(self, vault_path, dry_run=False, interval=1):
                super().__init__(vault_path, dry_run, interval)
                self.check_count = 0

            def check_for_updates(self) -> list[Path]:
                self.check_count += 1
                # Stop after 2 checks
                if self.check_count >= 2:
                    # Create stop file to halt
                    stop_file = self.vault_path / "STOP"
                    stop_file.touch()
                return []

        watcher = TestWatcher(vault_path=str(tmp_path), dry_run=True, interval=1)

        # Run should execute loop and halt on STOP file
        watcher.run()

        # Should have checked at least once
        assert watcher.check_count >= 1
