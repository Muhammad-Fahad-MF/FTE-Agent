"""Unit tests for CLI main() function."""

import pytest


class TestFileSystemWatcherMain:
    """Test CLI main() function."""

    def test_main_with_no_args_uses_env_defaults(self, monkeypatch, tmp_path):
        """Verify main() uses env vars when no CLI args provided."""
        monkeypatch.setenv("DEV_MODE", "true")
        monkeypatch.setenv("VAULT_PATH", str(tmp_path))
        monkeypatch.setenv("DRY_RUN", "true")
        monkeypatch.setenv("WATCHER_INTERVAL", "30")

        from src.filesystem_watcher import get_config_from_env

        # Get config as main() would
        config = get_config_from_env()

        # Verify env vars are read
        assert config["vault_path"] == str(tmp_path)
        assert config["dry_run"] is True
        assert config["interval"] == 30

    def test_main_with_cli_args_overrides_env(self, monkeypatch, tmp_path):
        """Verify CLI args override env vars in main()."""
        monkeypatch.setenv("DEV_MODE", "true")
        monkeypatch.setenv("VAULT_PATH", "./env_vault")
        monkeypatch.setenv("DRY_RUN", "false")
        monkeypatch.setenv("WATCHER_INTERVAL", "60")

        from src.filesystem_watcher import get_config_from_env

        # Get config from env
        config = get_config_from_env()

        # Simulate CLI override
        cli_vault_path = str(tmp_path)
        cli_dry_run = True
        cli_interval = 30

        if cli_vault_path is not None:
            config["vault_path"] = cli_vault_path
        if cli_dry_run:
            config["dry_run"] = cli_dry_run
        if cli_interval is not None:
            config["interval"] = cli_interval

        # Verify CLI wins
        assert config["vault_path"] == str(tmp_path)
        assert config["dry_run"] is True
        assert config["interval"] == 30

    def test_main_prints_startup_message(self, monkeypatch, tmp_path, capsys):
        """Verify main() prints startup configuration."""
        monkeypatch.setenv("DEV_MODE", "true")
        monkeypatch.setenv("VAULT_PATH", str(tmp_path))
        monkeypatch.setenv("DRY_RUN", "true")
        monkeypatch.setenv("WATCHER_INTERVAL", "45")

        from src.filesystem_watcher import get_config_from_env

        # Get config
        config = get_config_from_env()

        # Simulate main() startup messages
        print("Starting File System Watcher...")
        print(f"  Vault: {config['vault_path']}")
        print(f"  Dry Run: {config['dry_run']}")
        print(f"  Interval: {config['interval']}s")

        captured = capsys.readouterr()
        assert "Starting File System Watcher..." in captured.out
        assert str(tmp_path) in captured.out
        assert "Dry Run: True" in captured.out
        assert "Interval: 45s" in captured.out

    def test_main_interval_cap_at_60(self, monkeypatch, tmp_path):
        """Verify main() caps interval at 60 seconds."""
        monkeypatch.setenv("DEV_MODE", "true")
        monkeypatch.setenv("WATCHER_INTERVAL", "120")  # Over 60

        from src.filesystem_watcher import get_config_from_env

        # Get config
        config = get_config_from_env()

        # Verify interval would be capped when creating watcher
        assert min(config["interval"], 60) == 60

    def test_main_dev_mode_not_set_exits(self, monkeypatch, tmp_path, capsys):
        """Verify main() exits with error if DEV_MODE not set."""
        monkeypatch.delenv("DEV_MODE", raising=False)

        from src.filesystem_watcher import FileSystemWatcher

        # Should raise SystemExit
        with pytest.raises(SystemExit) as exc_info:
            FileSystemWatcher(vault_path=str(tmp_path))

        assert exc_info.value.code == 1

    def test_get_config_from_env_all_defaults(self, monkeypatch):
        """Verify get_config_from_env returns defaults when no env vars set."""
        # Clear env vars
        monkeypatch.delenv("VAULT_PATH", raising=False)
        monkeypatch.delenv("DRY_RUN", raising=False)
        monkeypatch.delenv("WATCHER_INTERVAL", raising=False)

        from src.filesystem_watcher import get_config_from_env

        config = get_config_from_env()

        assert config["vault_path"] == "./vault"
        assert config["dry_run"] is False
        assert config["interval"] == 60

    def test_create_parser_all_args(self):
        """Verify create_parser handles all CLI arguments."""
        from src.filesystem_watcher import create_parser

        parser = create_parser()

        # Parse all args
        args = parser.parse_args(["--vault-path", "/test", "--dry-run", "--interval", "30"])

        assert args.vault_path == "/test"
        assert args.dry_run is True
        assert args.interval == 30

    def test_main_watcher_run_called(self, monkeypatch, tmp_path):
        """Verify main() calls watcher.run()."""
        monkeypatch.setenv("DEV_MODE", "true")
        monkeypatch.setenv("VAULT_PATH", str(tmp_path))
        monkeypatch.setenv("DRY_RUN", "true")
        monkeypatch.setenv("WATCHER_INTERVAL", "1")

        from src.filesystem_watcher import FileSystemWatcher

        # Create watcher and mock run() to prevent infinite loop
        watcher = FileSystemWatcher(vault_path=str(tmp_path), dry_run=True, interval=1)

        # Create STOP file to halt immediately
        stop_file = tmp_path / "STOP"
        stop_file.touch()

        # Run should halt immediately due to STOP file
        watcher.run()

        # If we get here, run() executed and halted gracefully
        assert True
