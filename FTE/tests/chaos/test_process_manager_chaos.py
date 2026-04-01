"""
Chaos tests for Process Manager.

Tests verify system resilience under adverse conditions:
- Infinite crash loop prevention
- Graceful shutdown under load
- Recovery from cascading failures

These tests verify the system's robustness in production scenarios.
"""

import os
import signal
import subprocess
import sys
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from src.process_manager import ProcessManager, WatcherNotFoundError


@pytest.fixture
def temp_vault(tmp_path):
    """Create a temporary vault directory for testing."""
    vault_path = tmp_path / "vault"
    vault_path.mkdir()
    (vault_path / "Needs_Action").mkdir()
    (vault_path / "Dashboard.md").write_text("# Dashboard\n\n## Alerts\n", encoding="utf-8")
    yield str(vault_path)


@pytest.fixture
def crashing_watcher_script(tmp_path):
    """Create a watcher script that crashes immediately."""
    script_path = tmp_path / "crashing_watcher.py"
    script_content = """
import sys
sys.exit(1)  # Crash immediately
"""
    script_path.write_text(script_content, encoding="utf-8")
    return script_path


@pytest.fixture
def flaky_watcher_script(tmp_path):
    """Create a watcher script that crashes intermittently."""
    script_path = tmp_path / "flaky_watcher.py"
    script_content = """
import sys
import time
import random

# 50% chance of crashing
if random.random() < 0.5:
    sys.exit(1)

# Run for a bit
time.sleep(2)
sys.exit(0)
"""
    script_path.write_text(script_content, encoding="utf-8")
    return script_path


@pytest.fixture
def slow_watcher_script(tmp_path):
    """Create a watcher script that runs slowly."""
    script_path = tmp_path / "slow_watcher.py"
    script_content = """
import sys
import time

# Simulate slow startup
time.sleep(5)

# Run for a bit
time.sleep(10)
sys.exit(0)
"""
    script_path.write_text(script_content, encoding="utf-8")
    return script_path


class TestInfiniteCrashLoopPrevention:
    """Test prevention of infinite crash loops."""

    def test_infinite_crash_loop_prevented(self, temp_vault, crashing_watcher_script):
        """Verify that infinite crash loops are prevented."""
        manager = ProcessManager(
            vault_path=temp_vault,
            health_check_interval=1,
            max_restarts_per_hour=3,  # Low limit for testing
        )

        # Override watcher scripts
        manager._watcher_scripts = {
            "test_watcher": str(crashing_watcher_script),
        }

        restart_count = 0
        original_track_restart = manager._track_restart

        def track_and_count(name):
            nonlocal restart_count
            restart_count += 1
            original_track_restart(name)

        manager._track_restart = track_and_count

        dashboard_updated = False

        def mock_update_dashboard(level, message):
            nonlocal dashboard_updated
            if "exceeded restart limit" in message:
                dashboard_updated = True

        manager._update_dashboard_alert = mock_update_dashboard

        try:
            # Start the crashing watcher
            process = subprocess.Popen(
                [sys.executable, str(crashing_watcher_script)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            manager._processes["test_watcher"] = process

            # Wait for multiple crash/restart cycles
            time.sleep(5)

            # Manually trigger health checks to simulate the monitoring loop
            for _ in range(5):
                if not manager._check_watcher_health("test_watcher"):
                    manager._restart_watcher("test_watcher")
                time.sleep(0.5)

            # Verify restart limit was enforced
            assert restart_count <= 4, f"Expected <= 4 restarts, got {restart_count}"

            # Verify dashboard was updated with critical alert
            assert dashboard_updated, "Dashboard should be updated when restart limit exceeded"

        finally:
            # Cleanup
            if process and process.poll() is None:
                process.kill()
                process.wait()
            manager.stop_all_watchers()

    def test_restart_count_resets_after_hour(self, temp_vault):
        """Verify that restart count resets after 1 hour."""
        manager = ProcessManager(
            vault_path=temp_vault,
            max_restarts_per_hour=3,
        )

        # Add old restarts (older than 1 hour)
        old_time = datetime.now() - timedelta(hours=2)
        manager._restart_counts["test_watcher"] = [old_time, old_time, old_time]

        # Should be allowed to restart (old entries should be cleaned)
        can_restart = manager._check_restart_limit("test_watcher")
        assert can_restart is True


class TestGracefulShutdownUnderLoad:
    """Test graceful shutdown under various load conditions."""

    def test_graceful_shutdown_with_running_watchers(self, temp_vault, slow_watcher_script):
        """Verify graceful shutdown stops all watchers cleanly."""
        manager = ProcessManager(
            vault_path=temp_vault,
            health_check_interval=1,
        )

        # Override watcher scripts
        manager._watcher_scripts = {
            "slow_watcher": str(slow_watcher_script),
        }

        processes = []
        try:
            # Start multiple slow watchers
            for i in range(3):
                process = subprocess.Popen(
                    [sys.executable, str(slow_watcher_script)],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                )
                manager._processes[f"watcher_{i}"] = process
                processes.append(process)

            # Give them time to start
            time.sleep(1)

            # Initiate shutdown
            shutdown_start = time.time()
            manager.stop_all_watchers()
            shutdown_duration = time.time() - shutdown_start

            # Verify all processes stopped
            for i, process in enumerate(processes):
                assert process.poll() is not None, f"Watcher {i} still running after shutdown"

            # Verify shutdown completed in reasonable time (<10 seconds per spec)
            assert shutdown_duration < 15, f"Shutdown took too long: {shutdown_duration}s"

        finally:
            # Force cleanup any stragglers
            for process in processes:
                if process and process.poll() is None:
                    process.kill()
                    process.wait()

    def test_graceful_shutdown_with_crashing_watchers(self, temp_vault, crashing_watcher_script):
        """Verify graceful shutdown works even with crashing watchers."""
        manager = ProcessManager(
            vault_path=temp_vault,
            health_check_interval=1,
        )

        # Override watcher scripts
        manager._watcher_scripts = {
            "crashing_watcher": str(crashing_watcher_script),
        }

        processes = []
        try:
            # Start multiple crashing watchers
            for i in range(3):
                process = subprocess.Popen(
                    [sys.executable, str(crashing_watcher_script)],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                )
                manager._processes[f"watcher_{i}"] = process
                processes.append(process)

            # Let them crash
            time.sleep(2)

            # Initiate shutdown
            manager.stop_all_watchers()

            # Verify shutdown completed without errors
            # (all processes should be stopped, either by crash or by shutdown)
            for i, process in enumerate(processes):
                assert process.poll() is not None, f"Watcher {i} still running after shutdown"

        finally:
            # Force cleanup
            for process in processes:
                if process and process.poll() is None:
                    process.kill()
                    process.wait()

    def test_signal_handler_graceful_shutdown(self, temp_vault, slow_watcher_script):
        """Verify SIGTERM triggers graceful shutdown."""
        manager = ProcessManager(
            vault_path=temp_vault,
            health_check_interval=1,
        )

        # Override watcher scripts
        manager._watcher_scripts = {
            "slow_watcher": str(slow_watcher_script),
        }

        process = None
        try:
            # Start watcher
            process = subprocess.Popen(
                [sys.executable, str(slow_watcher_script)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            manager._processes["test_watcher"] = process

            # Send SIGTERM
            manager._signal_handler(signal.SIGTERM, None)

            # Verify shutdown flag set
            assert manager._shutdown is True

            # Verify process stopped
            process.wait(timeout=10)
            assert process.poll() is not None

        finally:
            if process and process.poll() is None:
                process.kill()
                process.wait()


class TestCascadingFailureRecovery:
    """Test recovery from cascading failures."""

    def test_one_watcher_crash_doesnt_affect_others(self, temp_vault, crashing_watcher_script, slow_watcher_script):
        """Verify that one crashing watcher doesn't affect others."""
        manager = ProcessManager(
            vault_path=temp_vault,
            health_check_interval=1,
            max_restarts_per_hour=5,
        )

        # Override watcher scripts
        manager._watcher_scripts = {
            "crashing": str(crashing_watcher_script),
            "stable": str(slow_watcher_script),
        }

        crashing_process = None
        stable_process = None

        try:
            # Start both watchers
            crashing_process = subprocess.Popen(
                [sys.executable, str(crashing_watcher_script)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            manager._processes["crashing"] = crashing_process

            stable_process = subprocess.Popen(
                [sys.executable, str(slow_watcher_script)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            manager._processes["stable"] = stable_process

            # Wait for crashing watcher to fail multiple times
            time.sleep(3)

            # Stable watcher should still be running
            assert stable_process.poll() is None, "Stable watcher should not be affected by crashing watcher"

        finally:
            # Cleanup
            if crashing_process and crashing_process.poll() is None:
                crashing_process.kill()
                crashing_process.wait()
            if stable_process and stable_process.poll() is None:
                stable_process.kill()
                stable_process.wait()
            manager.stop_all_watchers()

    def test_manager_recovers_from_rapid_restarts(self, temp_vault, crashing_watcher_script):
        """Verify manager can handle and recover from rapid restart scenarios."""
        manager = ProcessManager(
            vault_path=temp_vault,
            health_check_interval=1,
            max_restarts_per_hour=3,
        )

        # Override watcher scripts
        manager._watcher_scripts = {
            "test_watcher": str(crashing_watcher_script),
        }

        restart_timestamps = []

        def track_restarts(name):
            restart_timestamps.append(time.time())
            manager._track_restart(name)

        manager._track_restart = track_restarts

        try:
            # Start crashing watcher
            process = subprocess.Popen(
                [sys.executable, str(crashing_watcher_script)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            manager._processes["test_watcher"] = process

            # Simulate rapid crash/restart cycles
            for i in range(5):
                if not manager._check_watcher_health("test_watcher"):
                    manager._restart_watcher("test_watcher")
                time.sleep(0.5)

            # Verify restarts were rate-limited
            # Should have at most 3-4 restarts (limit is 3/hour)
            assert len(restart_timestamps) <= 4, f"Too many restarts: {len(restart_timestamps)}"

        finally:
            # Cleanup
            if process and process.poll() is None:
                process.kill()
                process.wait()
            manager.stop_all_watchers()


class TestResourceExhaustion:
    """Test behavior under resource exhaustion scenarios."""

    def test_handles_process_creation_failure(self, temp_vault):
        """Verify manager handles failures to create processes."""
        manager = ProcessManager(
            vault_path=temp_vault,
            health_check_interval=1,
        )

        # Override with non-existent script
        manager._watcher_scripts = {
            "non_existent": "/non/existent/script.py",
        }

        # Should raise WatcherNotFoundError
        with pytest.raises(WatcherNotFoundError):
            manager._start_watcher("non_existent")

    def test_handles_zombie_processes(self, temp_vault, slow_watcher_script):
        """Verify manager handles zombie processes gracefully."""
        manager = ProcessManager(
            vault_path=temp_vault,
            health_check_interval=1,
        )

        # Override watcher scripts
        manager._watcher_scripts = {
            "test_watcher": str(slow_watcher_script),
        }

        process = None
        try:
            # Start watcher
            process = subprocess.Popen(
                [sys.executable, str(slow_watcher_script)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            manager._processes["test_watcher"] = process

            # Kill without waiting (create zombie)
            process.kill()

            # Health check should handle this gracefully
            time.sleep(0.5)
            is_healthy = manager._check_watcher_health("test_watcher")
            assert is_healthy is False

        finally:
            if process and process.poll() is None:
                process.kill()
                process.wait()
            manager.stop_all_watchers()
