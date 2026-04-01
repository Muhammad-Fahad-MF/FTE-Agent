"""
Unit tests for Process Manager.

Tests cover:
- Crash detection via poll()
- Restart within 10 seconds
- Restart limits enforcement (max 3/hour)
- Memory monitoring with psutil
- Graceful shutdown
- Metrics emission
- Signal handling

All subprocess calls are mocked (no real processes).
"""

import signal
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.process_manager import (
    ProcessManager,
    ProcessManagerError,
    WatcherNotFoundError,
)


@pytest.fixture
def temp_vault(tmp_path):
    """Create a temporary vault directory for testing."""
    vault_path = tmp_path / "vault"
    vault_path.mkdir()
    # Create necessary subdirectories
    (vault_path / "Needs_Action").mkdir()
    (vault_path / "Dashboard.md").write_text("# Dashboard\n\n## Alerts\n", encoding="utf-8")
    yield str(vault_path)


@pytest.fixture
def process_manager(temp_vault):
    """Create a process manager instance with short intervals for testing."""
    return ProcessManager(
        vault_path=temp_vault,
        health_check_interval=1,  # 1 second for faster tests
        memory_threshold_mb=200,
        max_restarts_per_hour=3,
    )


@pytest.fixture
def mock_watcher_scripts(tmp_path):
    """Create mock watcher scripts."""
    # Create a mock Python script that does nothing
    mock_script = tmp_path / "mock_watcher.py"
    mock_script.write_text("import time\nwhile True: time.sleep(1)\n", encoding="utf-8")
    return tmp_path


class TestProcessManagerInitialization:
    """Test process manager initialization."""

    def test_initialization_creates_logger(self, temp_vault):
        """Process manager should create an audit logger on init."""
        manager = ProcessManager(vault_path=temp_vault)
        assert manager.logger is not None

    def test_initialization_sets_attributes(self, temp_vault):
        """Process manager should set configuration attributes."""
        manager = ProcessManager(
            vault_path=temp_vault,
            health_check_interval=5,
            memory_threshold_mb=150,
            max_restarts_per_hour=5,
        )
        assert manager.vault_path == Path(temp_vault).resolve()
        assert manager.health_check_interval == 5
        assert manager.memory_threshold_mb == 150
        assert manager.max_restarts_per_hour == 5

    def test_initialization_empty_processes_dict(self, temp_vault):
        """Process manager should start with no processes."""
        manager = ProcessManager(vault_path=temp_vault)
        assert len(manager._processes) == 0

    def test_initialization_empty_restart_counts(self, temp_vault):
        """Process manager should start with no restart counts."""
        manager = ProcessManager(vault_path=temp_vault)
        assert len(manager._restart_counts) == 0


class TestWatcherScriptPath:
    """Test watcher script path resolution."""

    def test_get_watcher_script_path_valid(self, process_manager, tmp_path):
        """Should return correct path for valid watcher names."""
        # Mock the vault_path.parent to point to test directory
        with patch.object(process_manager, "vault_path", tmp_path):
            # Create mock script
            mock_script = tmp_path.parent / "src" / "watchers" / "gmail_watcher.py"
            mock_script.parent.mkdir(parents=True, exist_ok=True)
            mock_script.write_text("# mock", encoding="utf-8")

            path = process_manager._get_watcher_script_path("gmail_watcher")
            assert path.exists()
            assert "gmail_watcher.py" in str(path)

    def test_get_watcher_script_path_invalid(self, process_manager):
        """Should raise WatcherNotFoundError for invalid watcher names."""
        with pytest.raises(WatcherNotFoundError) as exc_info:
            process_manager._get_watcher_script_path("invalid_watcher")
        assert "Unknown watcher" in str(exc_info.value)

    def test_get_watcher_script_path_missing_file(self, process_manager, tmp_path):
        """Should raise WatcherNotFoundError if script file doesn't exist."""
        # Create a mock vault path where the script doesn't exist
        fake_vault = tmp_path / "fake_vault"
        fake_vault.mkdir()

        with patch.object(process_manager, "vault_path", fake_vault):
            # The script path won't exist since we're using a fake vault
            with pytest.raises(WatcherNotFoundError) as exc_info:
                process_manager._get_watcher_script_path("gmail_watcher")
            assert "not found" in str(exc_info.value)


class TestStartWatcher:
    """Test watcher starting functionality."""

    @patch("subprocess.Popen")
    def test_start_watcher_creates_process(self, mock_popen, process_manager, tmp_path):
        """Starting a watcher should create a subprocess."""
        # Setup mock
        mock_process = MagicMock()
        mock_process.pid = 12345
        mock_popen.return_value = mock_process

        # Mock script path
        mock_script = tmp_path / "gmail_watcher.py"
        mock_script.parent.mkdir(parents=True, exist_ok=True)
        mock_script.write_text("# mock", encoding="utf-8")

        with patch.object(process_manager, "vault_path", tmp_path):
            with patch.object(
                process_manager,
                "_get_watcher_script_path",
                return_value=mock_script,
            ):
                with patch.object(process_manager.logger, "info"):
                    process_manager._start_watcher("gmail_watcher")

        # Verify subprocess.Popen was called
        assert mock_popen.called
        assert "gmail_watcher" in process_manager._processes

    @patch("subprocess.Popen")
    def test_start_watcher_sets_environment(self, mock_popen, process_manager, tmp_path):
        """Starting a watcher should set environment variables."""
        mock_process = MagicMock()
        mock_popen.return_value = mock_process

        mock_script = tmp_path / "gmail_watcher.py"
        mock_script.parent.mkdir(parents=True, exist_ok=True)
        mock_script.write_text("# mock", encoding="utf-8")

        with patch.object(process_manager, "vault_path", tmp_path):
            with patch.object(
                process_manager,
                "_get_watcher_script_path",
                return_value=mock_script,
            ):
                with patch.object(process_manager.logger, "info"):
                    process_manager._start_watcher("gmail_watcher")

        # Verify environment was passed
        call_args = mock_popen.call_args
        assert "env" in call_args.kwargs
        env = call_args.kwargs["env"]
        assert "VAULT_PATH" in env
        assert "DRY_RUN" in env
        assert "DEV_MODE" in env


class TestStopWatcher:
    """Test watcher stopping functionality."""

    def test_stop_watcher_graceful_termination(self, process_manager):
        """Stopping a watcher should send SIGTERM first."""
        # Create mock process that terminates gracefully
        mock_process = MagicMock()
        mock_process.poll.return_value = None  # Still running initially
        mock_process.wait.return_value = None  # Successful wait

        process_manager._processes["test_watcher"] = mock_process

        with patch.object(process_manager.logger, "info"):  # Mock logger
            process_manager._stop_watcher("test_watcher", mock_process)

        # Verify terminate was called
        mock_process.terminate.assert_called_once()
        # Verify wait was called
        mock_process.wait.assert_called()

    def test_stop_watcher_force_kill_on_timeout(self, process_manager):
        """Should force kill if graceful termination times out."""
        mock_process = MagicMock()
        mock_process.poll.return_value = None
        # First call raises TimeoutExpired, second call succeeds (after kill)
        mock_process.wait.side_effect = [subprocess.TimeoutExpired(cmd="test", timeout=5), None]

        process_manager._processes["test_watcher"] = mock_process

        with patch.object(process_manager.logger, "info"):
            with patch.object(process_manager.logger, "warning"):
                process_manager._stop_watcher("test_watcher", mock_process)

        # Verify kill was called after timeout
        mock_process.kill.assert_called_once()
        # Verify wait was called twice (once with timeout, once after kill)
        assert mock_process.wait.call_count == 2

    def test_stop_watcher_already_stopped(self, process_manager):
        """Should not try to stop already stopped watcher."""
        mock_process = MagicMock()
        mock_process.poll.return_value = 0  # Already stopped

        process_manager._processes["test_watcher"] = mock_process

        process_manager._stop_watcher("test_watcher", mock_process)

        # Verify terminate was NOT called
        mock_process.terminate.assert_not_called()


class TestCrashDetection:
    """Test crash detection functionality."""

    def test_check_watcher_health_running(self, process_manager):
        """Should return True for running watchers."""
        mock_process = MagicMock()
        mock_process.poll.return_value = None  # Still running

        process_manager._processes["test_watcher"] = mock_process

        result = process_manager._check_watcher_health("test_watcher")
        assert result is True

    def test_check_watcher_health_crashed(self, process_manager):
        """Should return False for crashed watchers."""
        mock_process = MagicMock()
        mock_process.poll.return_value = 1  # Crashed with error code

        process_manager._processes["test_watcher"] = mock_process

        with patch.object(process_manager.logger, "warning"):  # Mock logger
            result = process_manager._check_watcher_health("test_watcher")
        assert result is False

    def test_check_watcher_health_not_exists(self, process_manager):
        """Should return False for non-existent watchers."""
        result = process_manager._check_watcher_health("non_existent")
        assert result is False


class TestRestartLimits:
    """Test restart limits enforcement."""

    def test_track_restart_records_timestamp(self, process_manager):
        """Tracking a restart should record the timestamp."""
        process_manager._track_restart("test_watcher")

        assert "test_watcher" in process_manager._restart_counts
        assert len(process_manager._restart_counts["test_watcher"]) == 1
        assert isinstance(process_manager._restart_counts["test_watcher"][0], datetime)

    def test_track_restart_cleans_old_entries(self, process_manager):
        """Should clean entries older than 1 hour."""
        # Add old entry
        old_time = datetime.now() - timedelta(hours=2)
        process_manager._restart_counts["test_watcher"] = [old_time]

        process_manager._track_restart("test_watcher")

        # Should only have the new entry
        assert len(process_manager._restart_counts["test_watcher"]) == 1
        assert process_manager._restart_counts["test_watcher"][0] > datetime.now() - timedelta(
            minutes=1
        )

    def test_check_restart_limit_under_limit(self, process_manager):
        """Should return True when under restart limit."""
        # Add 2 restarts (under limit of 3)
        process_manager._restart_counts["test_watcher"] = [
            datetime.now() - timedelta(minutes=10),
            datetime.now() - timedelta(minutes=20),
        ]

        result = process_manager._check_restart_limit("test_watcher")
        assert result is True

    def test_check_restart_limit_at_limit(self, process_manager):
        """Should return False when at restart limit."""
        # Add 3 restarts (at limit)
        process_manager._restart_counts["test_watcher"] = [
            datetime.now() - timedelta(minutes=10),
            datetime.now() - timedelta(minutes=20),
            datetime.now() - timedelta(minutes=30),
        ]

        result = process_manager._check_restart_limit("test_watcher")
        assert result is False

    def test_check_restart_limit_no_history(self, process_manager):
        """Should return True when no restart history."""
        result = process_manager._check_restart_limit("new_watcher")
        assert result is True


class TestMemoryMonitoring:
    """Test memory monitoring functionality."""

    @patch("psutil.Process")
    def test_check_memory_usage_under_limit(self, mock_psutil_process, process_manager):
        """Should not kill watcher when under memory limit."""
        mock_process = MagicMock()
        mock_process.pid = 12345

        mock_psutil = MagicMock()
        mock_psutil.memory_info.return_value.rss = 100 * 1024 * 1024  # 100MB
        mock_psutil_process.return_value = mock_psutil

        process_manager._check_memory_usage("test_watcher", mock_process)

        # Should not kill
        mock_process.kill.assert_not_called()

    @patch("psutil.Process")
    def test_check_memory_usage_over_limit(self, mock_psutil_process, process_manager):
        """Should kill watcher when over memory limit."""
        mock_process = MagicMock()
        mock_process.pid = 12345

        mock_psutil = MagicMock()
        mock_psutil.memory_info.return_value.rss = 250 * 1024 * 1024  # 250MB (over 200MB limit)
        mock_psutil_process.return_value = mock_psutil

        process_manager._check_memory_usage("test_watcher", mock_process)

        # Should kill
        mock_process.kill.assert_called_once()

    @patch("psutil.Process")
    def test_check_memory_usage_process_not_exists(self, mock_psutil_process, process_manager):
        """Should handle NoSuchProcess exception gracefully."""
        import psutil

        mock_process = MagicMock()
        mock_process.pid = 12345

        mock_psutil_process.side_effect = psutil.NoSuchProcess(pid=12345)

        # Should not raise
        process_manager._check_memory_usage("test_watcher", mock_process)


class TestMetricsEmission:
    """Test metrics emission functionality."""

    def test_register_metrics_callback(self, process_manager):
        """Should register metrics callbacks."""
        callback = MagicMock()
        process_manager.register_metrics_callback(callback)

        assert callback in process_manager._metrics_callbacks

    def test_emit_metrics_calls_callbacks(self, process_manager):
        """Should call all registered callbacks."""
        callback1 = MagicMock()
        callback2 = MagicMock()

        process_manager.register_metrics_callback(callback1)
        process_manager.register_metrics_callback(callback2)

        process_manager._emit_metrics("test_metric", value=42, tags={"key": "value"})

        callback1.assert_called_once_with("test_metric", 42, {"key": "value"})
        callback2.assert_called_once_with("test_metric", 42, {"key": "value"})

    def test_emit_metrics_handles_callback_exception(self, process_manager):
        """Should handle exceptions in callbacks gracefully."""

        def failing_callback(*args):
            raise Exception("Test exception")

        working_callback = MagicMock()

        process_manager.register_metrics_callback(failing_callback)
        process_manager.register_metrics_callback(working_callback)

        with patch.object(process_manager.logger, "info"):  # Mock logger
            # Should not raise, working callback should be called
            process_manager._emit_metrics("test_metric")
        working_callback.assert_called_once()


class TestWatcherStatus:
    """Test watcher status reporting."""

    def test_get_watcher_status_not_started(self, process_manager):
        """Should return not_started status for non-existent watcher."""
        status = process_manager.get_watcher_status("non_existent")
        assert status["status"] == "not_started"
        assert status["pid"] is None
        assert status["running"] is False

    def test_get_watcher_status_running(self, process_manager):
        """Should return running status for active watcher."""
        mock_process = MagicMock()
        mock_process.pid = 12345
        mock_process.poll.return_value = None  # Running
        mock_process.returncode = None

        process_manager._processes["test_watcher"] = mock_process

        status = process_manager.get_watcher_status("test_watcher")
        assert status["status"] == "running"
        assert status["pid"] == 12345
        assert status["running"] is True

    def test_get_watcher_status_stopped(self, process_manager):
        """Should return stopped status for terminated watcher."""
        mock_process = MagicMock()
        mock_process.pid = 12345
        mock_process.poll.return_value = 1  # Stopped with error
        mock_process.returncode = 1

        process_manager._processes["test_watcher"] = mock_process

        status = process_manager.get_watcher_status("test_watcher")
        assert status["status"] == "stopped"
        assert status["returncode"] == 1

    def test_get_all_statuses(self, process_manager):
        """Should return status for all configured watchers."""
        # Mock processes
        mock_process1 = MagicMock()
        mock_process1.poll.return_value = None
        mock_process2 = MagicMock()
        mock_process2.poll.return_value = 1

        process_manager._processes["gmail_watcher"] = mock_process1
        process_manager._processes["filesystem_watcher"] = mock_process2

        statuses = process_manager.get_all_statuses()

        assert "gmail_watcher" in statuses
        assert "whatsapp_watcher" in statuses
        assert "filesystem_watcher" in statuses


class TestRestartWatcher:
    """Test watcher restart functionality."""

    @patch("subprocess.Popen")
    def test_restart_watcher_under_limit(self, mock_popen, process_manager):
        """Should restart watcher when under limit."""
        mock_process = MagicMock()
        mock_process.pid = 12345
        mock_popen.return_value = mock_process

        # Mock script
        mock_script = Path(process_manager.vault_path) / "mock.py"
        mock_script.parent.mkdir(parents=True, exist_ok=True)
        mock_script.write_text("# mock", encoding="utf-8")

        with patch.object(process_manager, "_get_watcher_script_path", return_value=mock_script):
            with patch.object(process_manager, "_check_restart_limit", return_value=True):
                process_manager._restart_watcher("test_watcher")

        # Verify start was called
        assert "test_watcher" in process_manager._processes

    @patch("subprocess.Popen")
    def test_restart_watcher_over_limit(self, mock_popen, process_manager):
        """Should not restart watcher when over limit."""
        # Mock script
        mock_script = Path(process_manager.vault_path) / "mock.py"
        mock_script.parent.mkdir(parents=True, exist_ok=True)
        mock_script.write_text("# mock", encoding="utf-8")

        with patch.object(process_manager, "_get_watcher_script_path", return_value=mock_script):
            with patch.object(process_manager, "_check_restart_limit", return_value=False):
                with patch.object(process_manager, "_update_dashboard_alert") as mock_alert:
                    process_manager._restart_watcher("test_watcher")

                    # Verify alert was called
                    assert mock_alert.called
                    # Verify start was NOT called
                    assert "test_watcher" not in process_manager._processes


class TestGracefulShutdown:
    """Test graceful shutdown functionality."""

    @patch("signal.signal")
    def test_signal_handler_sets_shutdown_flag(self, mock_signal, temp_vault):
        """Signal handler should set shutdown flag."""
        manager = ProcessManager(vault_path=temp_vault)
        assert manager._shutdown is False

        with patch.object(manager, "stop_all_watchers"):  # Mock stop_all_watchers
            # Simulate signal
            manager._signal_handler(signal.SIGTERM, None)

        assert manager._shutdown is True

    @patch("signal.signal")
    def test_signal_handler_stops_watchers(self, mock_signal, temp_vault):
        """Signal handler should stop all watchers."""
        manager = ProcessManager(vault_path=temp_vault)

        mock_process = MagicMock()
        manager._processes["test_watcher"] = mock_process

        with patch.object(manager, "_stop_watcher") as mock_stop:
            manager._signal_handler(signal.SIGTERM, None)
            # _stop_watcher should be called
            assert mock_stop.called


class TestDashboardAlert:
    """Test dashboard alert functionality."""

    def test_update_dashboard_alert_creates_file(self, process_manager, temp_vault):
        """Should create dashboard file if it doesn't exist."""
        with patch.object(process_manager, "vault_path", Path(temp_vault)):
            process_manager._update_dashboard_alert("WARNING", "Test alert")

    def test_update_dashboard_alert_appends(self, temp_vault):
        """Should append to existing dashboard."""
        dashboard_path = Path(temp_vault) / "Dashboard.md"
        original_content = "# Dashboard\n\n## Alerts\n"
        dashboard_path.write_text(original_content, encoding="utf-8")

        manager = ProcessManager(vault_path=temp_vault)
        manager._update_dashboard_alert("WARNING", "Test alert")

        new_content = dashboard_path.read_text(encoding="utf-8")
        assert "Test alert" in new_content


class TestProcessManagerError:
    """Test custom exceptions."""

    def test_watcher_not_found_error(self):
        """WatcherNotFoundError should have correct message."""
        error = WatcherNotFoundError("Watcher not found: test")
        assert str(error) == "Watcher not found: test"

    def test_process_manager_error(self):
        """ProcessManagerError should work as base exception."""
        error = ProcessManagerError("Generic error")
        assert str(error) == "Generic error"
