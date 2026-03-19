"""Contract tests for BaseWatcher and FileSystemWatcher classes.

These tests verify that the classes have correct interfaces:
- Method signatures
- Parameter names and types
- Return types
- Inheritance relationships
"""

from pathlib import Path


class TestBaseWatcherContract:
    """Contract tests for BaseWatcher abstract class."""

    def test_watcher_interface(self):
        """Verify FileSystemWatcher inherits from BaseWatcher."""
        from src.base_watcher import BaseWatcher
        from src.filesystem_watcher import FileSystemWatcher

        assert issubclass(FileSystemWatcher, BaseWatcher)

    def test_watcher_initialization(self):
        """Verify __init__ accepts vault_path, dry_run, interval parameters."""
        import inspect

        from src.base_watcher import BaseWatcher

        sig = inspect.signature(BaseWatcher.__init__)
        params = list(sig.parameters.keys())

        # Should have self, vault_path, dry_run, interval
        assert "vault_path" in params
        assert "dry_run" in params
        assert "interval" in params

    def test_check_for_updates_signature(self):
        """Verify check_for_updates() returns list[Path]."""
        import inspect

        from src.base_watcher import BaseWatcher

        sig = inspect.signature(BaseWatcher.check_for_updates)
        return_annotation = sig.return_annotation

        # Should return list[Path]
        assert return_annotation == list[Path]

    def test_create_action_file_signature(self):
        """Verify create_action_file() returns Path."""
        import inspect

        from src.base_watcher import BaseWatcher

        sig = inspect.signature(BaseWatcher.create_action_file)
        return_annotation = sig.return_annotation

        # Should return Path
        assert return_annotation == Path
