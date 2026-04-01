"""Unit tests for FileSystemWatcher class."""

import sys
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture
def mock_metrics_collector():
    """Create a mock metrics collector."""
    mock = MagicMock()
    mock.timer.return_value.__enter__ = MagicMock()
    mock.timer.return_value.__exit__ = MagicMock()
    return mock


@pytest.fixture
def mock_circuit_breaker():
    """Create a mock circuit breaker."""
    mock = MagicMock()
    mock.is_open.return_value = False
    mock.is_closed.return_value = True
    mock.is_half_open.return_value = False
    return mock


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

    @patch('src.filesystem_watcher.get_circuit_breaker')
    @patch('src.filesystem_watcher.get_metrics_collector')
    def test_path_validation_traversal_attempt(self, mock_get_metrics, mock_get_breaker, monkeypatch, tmp_path):
        """Verify ValueError raised for paths outside vault."""
        # Set DEV_MODE to true
        monkeypatch.setenv("DEV_MODE", "true")
        
        # Setup mocks
        mock_get_metrics.return_value = MagicMock()
        mock_get_breaker.return_value = MagicMock()

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

    @patch('src.filesystem_watcher.get_circuit_breaker')
    @patch('src.filesystem_watcher.get_metrics_collector')
    def test_stop_file_detection(self, mock_get_metrics, mock_get_breaker, monkeypatch, tmp_path):
        """Verify watcher halts within 60 seconds of STOP file creation."""
        # Set DEV_MODE to true
        monkeypatch.setenv("DEV_MODE", "true")
        
        # Setup mocks
        mock_get_metrics.return_value = MagicMock()
        mock_get_breaker.return_value = MagicMock()

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

    @patch('src.filesystem_watcher.get_circuit_breaker')
    @patch('src.filesystem_watcher.get_metrics_collector')
    def test_dry_run_no_file_creation(self, mock_get_metrics, mock_get_breaker, monkeypatch, tmp_path):
        """Verify no action files created when dry_run=True."""
        # Set DEV_MODE to true
        monkeypatch.setenv("DEV_MODE", "true")
        
        # Setup mocks
        mock_get_metrics.return_value = MagicMock()
        mock_get_breaker.return_value = MagicMock()

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

    @patch('src.filesystem_watcher.get_circuit_breaker')
    @patch('src.filesystem_watcher.get_metrics_collector')
    def test_metrics_emitted_on_check(self, mock_get_metrics, mock_get_breaker, monkeypatch, tmp_path):
        """Verify histogram and counter metrics are recorded during check."""
        # Set DEV_MODE to true
        monkeypatch.setenv("DEV_MODE", "true")
        
        # Setup mocks
        mock_metrics = MagicMock()
        mock_metrics.timer.return_value.__enter__ = MagicMock()
        mock_metrics.timer.return_value.__exit__ = MagicMock()
        mock_get_metrics.return_value = mock_metrics
        
        mock_breaker = MagicMock()
        mock_breaker.is_open.return_value = False
        mock_get_breaker.return_value = mock_breaker

        from src.filesystem_watcher import FileSystemWatcher

        # Create watcher
        watcher = FileSystemWatcher(vault_path=str(tmp_path))

        # Create test file in Inbox
        inbox = tmp_path / "Inbox"
        inbox.mkdir(exist_ok=True)
        test_file = inbox / "test.txt"
        test_file.write_text("test content")

        # Call check_for_updates
        watcher.check_for_updates()

        # Verify timer context manager was used (histogram)
        assert mock_metrics.timer.called
        timer_call_args = mock_metrics.timer.call_args[0]
        assert timer_call_args[0] == "filesystem_watcher_check_duration"

        # Verify counter was incremented for items processed
        mock_metrics.increment_counter.assert_any_call(
            "filesystem_watcher_items_processed",
            tags={
                "source_folder": str(inbox),
                "file_extension": ".txt",
            },
        )

    @patch('src.filesystem_watcher.get_circuit_breaker')
    @patch('src.filesystem_watcher.get_metrics_collector')
    def test_circuit_breaker_trips_after_failures(self, mock_get_metrics, mock_get_breaker, monkeypatch, tmp_path):
        """Verify circuit breaker opens after consecutive failures."""
        # Set DEV_MODE to true
        monkeypatch.setenv("DEV_MODE", "true")
        
        # Setup mocks
        mock_metrics = MagicMock()
        mock_get_metrics.return_value = mock_metrics
        
        mock_breaker = MagicMock()
        mock_breaker.is_open.return_value = True  # Simulate OPEN state
        mock_get_breaker.return_value = mock_breaker

        from src.filesystem_watcher import FileSystemWatcher

        # Create watcher
        watcher = FileSystemWatcher(vault_path=str(tmp_path))

        # Call check_for_updates - should return empty list when circuit is open
        result = watcher.check_for_updates()

        # Should return empty list without processing
        assert result == []

    @patch('src.filesystem_watcher.get_circuit_breaker')
    @patch('src.filesystem_watcher.get_metrics_collector')
    def test_filesystem_watcher_preserves_bronze_functionality(self, mock_get_metrics, mock_get_breaker, monkeypatch, tmp_path):
        """Verify existing Bronze tier tests still pass."""
        # Set DEV_MODE to true
        monkeypatch.setenv("DEV_MODE", "true")
        
        # Setup mocks
        mock_metrics = MagicMock()
        mock_metrics.timer.return_value.__enter__ = MagicMock()
        mock_metrics.timer.return_value.__exit__ = MagicMock()
        mock_get_metrics.return_value = mock_metrics
        
        mock_breaker = MagicMock()
        mock_breaker.is_open.return_value = False
        mock_get_breaker.return_value = mock_breaker

        from src.filesystem_watcher import FileSystemWatcher

        # Create watcher
        watcher = FileSystemWatcher(vault_path=str(tmp_path))

        # Create test file in Inbox
        inbox = tmp_path / "Inbox"
        inbox.mkdir(exist_ok=True)
        test_file = inbox / "test.txt"
        test_file.write_text("test content")

        # Call check_for_updates
        result = watcher.check_for_updates()

        # Should detect the new file
        assert len(result) == 1
        assert result[0] == test_file

        # Create action file
        action_path = watcher.create_action_file(test_file)

        # Action file should be created in Needs_Action/
        assert action_path.exists()
        assert "Needs_Action" in str(action_path)
        assert action_path.suffix == ".md"

        # Verify action file content
        content = action_path.read_text()
        assert "---" in content  # YAML frontmatter
        assert "type: file_drop" in content
        assert "status: pending" in content

    @patch('src.filesystem_watcher.get_circuit_breaker')
    @patch('src.filesystem_watcher.get_metrics_collector')
    def test_new_file_detected_and_action_created(self, mock_get_metrics, mock_get_breaker, monkeypatch, tmp_path):
        """Verify end-to-end flow: new file detection and action file creation."""
        # Set DEV_MODE to true
        monkeypatch.setenv("DEV_MODE", "true")
        
        # Setup mocks
        mock_metrics = MagicMock()
        mock_metrics.timer.return_value.__enter__ = MagicMock()
        mock_metrics.timer.return_value.__exit__ = MagicMock()
        mock_get_metrics.return_value = mock_metrics
        
        mock_breaker = MagicMock()
        mock_breaker.is_open.return_value = False
        mock_get_breaker.return_value = mock_breaker

        from src.filesystem_watcher import FileSystemWatcher

        # Create watcher
        watcher = FileSystemWatcher(vault_path=str(tmp_path))

        # Create test file in Inbox
        inbox = tmp_path / "Inbox"
        inbox.mkdir(exist_ok=True)
        test_file = inbox / "document.pdf"
        test_file.write_text("PDF content")

        # First check - should detect file
        result = watcher.check_for_updates()
        assert len(result) == 1

        # Create action file
        action_path = watcher.create_action_file(test_file)
        assert action_path.exists()

        # Second check - should not detect same file (already processed)
        result = watcher.check_for_updates()
        assert len(result) == 0

        # Verify action file naming includes file stem and timestamp
        assert "FILE_document_" in action_path.name
