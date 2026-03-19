"""Unit tests for Python Skills module."""

from pathlib import Path

import pytest


class TestSkillsModule:
    """Unit tests for skills.py functions."""

    def test_check_dev_mode_success(self, monkeypatch):
        """Verify check_dev_mode returns True when DEV_MODE='true'."""
        monkeypatch.setenv("DEV_MODE", "true")
        from src.skills import check_dev_mode

        result = check_dev_mode()
        assert result is True

    def test_check_dev_mode_failure(self, monkeypatch):
        """Verify check_dev_mode raises SystemExit when DEV_MODE!='true'."""
        monkeypatch.setenv("DEV_MODE", "false")
        from src.skills import check_dev_mode

        with pytest.raises(SystemExit) as exc_info:
            check_dev_mode()
        assert exc_info.value.code == 1

    def test_create_action_file_dry_run(self, monkeypatch, tmp_path):
        """Verify create_action_file returns path but doesn't create file in dry_run mode."""
        monkeypatch.setenv("DEV_MODE", "true")
        monkeypatch.setenv("VAULT_PATH", str(tmp_path))

        from src.skills import create_action_file

        action_path = create_action_file("file_drop", "test.txt", "test content", dry_run=True)

        # Path should be returned
        assert action_path.endswith(".md")
        # File should NOT exist (dry-run)
        assert not Path(action_path).exists()

    def test_create_action_file_creates_file(self, monkeypatch, tmp_path):
        """Verify create_action_file creates file with correct frontmatter."""
        monkeypatch.setenv("DEV_MODE", "true")
        monkeypatch.setenv("VAULT_PATH", str(tmp_path))

        from src.skills import create_action_file

        action_path = create_action_file("file_drop", "test.txt", "test content", dry_run=False)

        # File should exist
        assert Path(action_path).exists()

        # Verify content
        content = Path(action_path).read_text()
        assert "type: file_drop" in content
        assert "source: test.txt" in content
        assert "status: pending" in content
        assert "## Content" in content
        assert "test content" in content

    def test_log_audit_dry_run(self, monkeypatch, capsys):
        """Verify log_audit prints to stdout in dry_run mode."""
        monkeypatch.setenv("DEV_MODE", "true")

        from src.skills import log_audit

        log_audit("test_action", {"key": "value"}, level="INFO", dry_run=True)

        captured = capsys.readouterr()
        assert "[DRY-RUN] INFO: test_action" in captured.out

    def test_log_audit_normal(self, monkeypatch, tmp_path):
        """Verify log_audit creates log file in normal mode."""
        monkeypatch.setenv("DEV_MODE", "true")
        monkeypatch.setenv("VAULT_PATH", str(tmp_path))

        from src.skills import log_audit

        log_audit("test_action", {"key": "value"}, level="INFO", dry_run=False)

        # Verify log file was created in Logs directory
        logs_path = tmp_path / "Logs"
        assert logs_path.exists()
        log_files = list(logs_path.glob("*.jsonl"))
        assert len(log_files) > 0

    def test_validate_path_valid(self, monkeypatch, tmp_path):
        """Verify validate_path returns resolved path for valid paths."""
        monkeypatch.setenv("DEV_MODE", "true")

        from src.skills import validate_path

        # Create a subdirectory
        subdir = tmp_path / "Inbox"
        subdir.mkdir()
        test_file = subdir / "test.txt"
        test_file.write_text("test")

        result = validate_path(str(test_file), str(tmp_path))

        # Should return resolved absolute path
        assert Path(result).is_absolute()
        assert str(tmp_path) in result

    def test_validate_path_invalid_traversal(self, monkeypatch, tmp_path):
        """Verify validate_path raises ValueError for path traversal attempts."""
        monkeypatch.setenv("DEV_MODE", "true")

        from src.skills import validate_path

        with pytest.raises(ValueError) as exc_info:
            validate_path("/etc/passwd", str(tmp_path))

        assert (
            "outside vault" in str(exc_info.value).lower()
            or "must be within vault" in str(exc_info.value).lower()
        )
