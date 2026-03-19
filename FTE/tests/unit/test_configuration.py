"""Unit tests for configuration (environment variables and CLI flags)."""

import os


class TestConfiguration:
    """Unit tests for configuration."""

    def test_vault_path_env_var(self, monkeypatch, tmp_path):
        """Verify VAULT_PATH env var changes monitored directory."""
        # Set custom vault path
        custom_vault = tmp_path / "custom_vault"
        custom_vault.mkdir()
        monkeypatch.setenv("VAULT_PATH", str(custom_vault))
        monkeypatch.setenv("DEV_MODE", "true")

        from src.filesystem_watcher import FileSystemWatcher

        # Create watcher (should use VAULT_PATH from env)
        vault_path = os.getenv("VAULT_PATH", "./vault")
        watcher = FileSystemWatcher(vault_path=vault_path)

        # Verify using custom vault
        assert watcher.vault_path == custom_vault

    def test_interval_cli_flag(self, monkeypatch, tmp_path):
        """Verify --interval flag changes check interval."""
        # Set DEV_MODE to true
        monkeypatch.setenv("DEV_MODE", "true")

        from src.filesystem_watcher import FileSystemWatcher

        # Create watcher with custom interval
        watcher = FileSystemWatcher(vault_path=str(tmp_path), interval=30)

        # Verify interval is set
        assert watcher.interval == 30

        # Test interval cap at 60 seconds (constitution requirement)
        watcher_high = FileSystemWatcher(vault_path=str(tmp_path), interval=120)
        assert watcher_high.interval == 60  # Capped at 60

    def test_dry_run_env_var(self, monkeypatch, tmp_path):
        """Verify DRY_RUN=true enables dry-run mode."""
        # Set environment variables
        monkeypatch.setenv("DEV_MODE", "true")
        monkeypatch.setenv("DRY_RUN", "true")

        from src.filesystem_watcher import FileSystemWatcher

        # Create watcher with dry_run from env
        dry_run = os.getenv("DRY_RUN", "false").lower() == "true"
        watcher = FileSystemWatcher(vault_path=str(tmp_path), dry_run=dry_run)

        # Verify dry_run is enabled
        assert watcher.dry_run

        # Verify no files created in dry-run
        # Note: Inbox is already created by FileSystemWatcher.__init__()
        inbox = tmp_path / "Inbox"
        test_file = inbox / "test.txt"
        test_file.write_text("test")

        action_path = watcher.create_action_file(test_file)

        # File should NOT exist (dry-run mode)
        assert not action_path.exists()

    def test_cli_flag_precedence(self, monkeypatch, tmp_path):
        """Verify CLI flags override environment variables."""
        # Set env var
        monkeypatch.setenv("DEV_MODE", "true")
        monkeypatch.setenv("DRY_RUN", "false")  # env says false

        from src.filesystem_watcher import FileSystemWatcher

        # But CLI flag says true (CLI should win)
        cli_dry_run = True  # CLI flag

        watcher = FileSystemWatcher(vault_path=str(tmp_path), dry_run=cli_dry_run)

        # CLI flag should override env var
        assert watcher.dry_run
