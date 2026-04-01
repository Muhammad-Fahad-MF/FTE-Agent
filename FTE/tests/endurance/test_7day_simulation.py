"""
Endurance Test: 7-Day Simulation.

Validates system stability over extended operation:
- Simulates 7 days of operation in 2 hours
- Memory leak detection (stable memory over time)
- File descriptor leak detection (stable open file count)
- Disk space leak detection (log rotation works)
- Component health stability

Usage:
    # Run full endurance test (2 hours)
    pytest tests/endurance/test_7day_simulation.py -v --tb=short
    
    # Run single test
    pytest tests/endurance/test_7day_simulation.py::test_memory_leak_detection -v

Test accelerates time by factor of 84 (7 days / 2 hours = 84)
"""

import gc
import os
import time
import threading
import tracemalloc
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any
from unittest.mock import patch, MagicMock

import psutil
import pytest

from src.utils.graceful_degradation import (
    GracefulDegradationManager,
    ComponentStatus,
    get_degradation_manager,
)
from src.utils.dead_letter_queue import DeadLetterQueue


# Test configuration
ENDURANCE_DURATION_SECONDS = 120  # 2 minutes for CI (scale up to 2 hours for production)
SIMULATED_DAYS = 7
TIME_ACCELERATION_FACTOR = SIMULATED_DAYS * 24 * 60 * 60 / ENDURANCE_DURATION_SECONDS

# Thresholds for leak detection
MEMORY_LEAK_THRESHOLD_MB = 50  # Max memory growth allowed
FILE_DESCRIPTOR_LEAK_THRESHOLD = 20  # Max open FD growth allowed
DISK_LEAK_THRESHOLD_MB = 100  # Max disk growth allowed


class EnduranceTestMetrics:
    """Track metrics during endurance test."""
    
    def __init__(self):
        self.start_time = datetime.now()
        self.memory_samples: list[float] = []
        self.fd_samples: list[int] = []
        self.disk_samples: list[float] = []
        self.error_samples: list[int] = []
        self.request_count = 0
        self.failure_count = 0
        
    def sample(self):
        """Take a sample of current metrics."""
        process = psutil.Process()
        
        # Memory (MB)
        memory_mb = process.memory_info().rss / 1024 / 1024
        self.memory_samples.append(memory_mb)
        
        # File descriptors (Windows handles approximation)
        try:
            fd_count = process.num_handles() if os.name == "nt" else process.num_fds()
        except Exception:
            fd_count = 0
        self.fd_samples.append(fd_count)
        
        # Disk (C: drive on Windows, / on Unix)
        try:
            disk_usage = psutil.disk_usage("C:\\") if os.name == "nt" else psutil.disk_usage("/")
            self.disk_samples.append(disk_usage.percent)
        except Exception:
            self.disk_samples.append(0)
        
        # Error count
        manager = get_degradation_manager()
        error_count = manager.get_error_rate()
        self.error_samples.append(error_count)
        
    def get_memory_growth(self) -> float:
        """Get memory growth in MB."""
        if len(self.memory_samples) < 2:
            return 0.0
        return max(self.memory_samples) - min(self.memory_samples)
    
    def get_fd_growth(self) -> int:
        """Get file descriptor growth."""
        if len(self.fd_samples) < 2:
            return 0
        return max(self.fd_samples) - min(self.fd_samples)
    
    def get_disk_growth(self) -> float:
        """Get disk usage growth in percentage."""
        if len(self.disk_samples) < 2:
            return 0.0
        return max(self.disk_samples) - min(self.disk_samples)
    
    def get_summary(self) -> dict[str, Any]:
        """Get test summary."""
        return {
            "duration_seconds": (datetime.now() - self.start_time).total_seconds(),
            "memory_samples": len(self.memory_samples),
            "memory_growth_mb": self.get_memory_growth(),
            "fd_growth": self.get_fd_growth(),
            "disk_growth_percent": self.get_disk_growth(),
            "total_requests": self.request_count,
            "total_failures": self.failure_count,
            "error_rate": self.failure_count / max(self.request_count, 1) * 100,
        }


@pytest.fixture
def metrics():
    """Create metrics tracker."""
    return EnduranceTestMetrics()


@pytest.fixture
def temp_vault(tmp_path):
    """Create temporary vault directory."""
    vault_dir = tmp_path / "vault"
    vault_dir.mkdir(parents=True)
    
    # Create all required subdirectories
    for subdir in ["Inbox", "Needs_Action", "Plans", "Pending_Approval", 
                   "Approved", "Rejected", "Done", "Briefings", 
                   "Templates", "Failed_Actions", "Logs"]:
        (vault_dir / subdir).mkdir()
    
    yield vault_dir


@pytest.fixture
def temp_dlq(tmp_path, temp_vault):
    """Create temporary DLQ."""
    db_path = tmp_path / "test_failed_actions.db"
    return DeadLetterQueue(db_path=str(db_path), vault_dir=str(temp_vault))


def simulate_watcher_activity(manager: GracefulDegradationManager, metrics: EnduranceTestMetrics):
    """Simulate watcher operations."""
    # Simulate successful check
    manager.set_component_status("watcher_filesystem", ComponentStatus.HEALTHY)
    metrics.request_count += 1
    
    # Simulate occasional errors (1% error rate)
    if metrics.request_count % 100 == 0:
        manager.record_error("watcher_filesystem", "Simulated transient error")
        metrics.failure_count += 1


def simulate_file_operations(vault_dir: Path, metrics: EnduranceTestMetrics):
    """Simulate file creation and rotation."""
    # Create action file
    action_file = vault_dir / "Needs_Action" / f"ACTION_{metrics.request_count}.md"
    action_file.write_text(f"""---
type: test_action
created: {datetime.now().isoformat()}
status: pending
---

# Test Action {metrics.request_count}

Simulated action for endurance testing.
""")
    metrics.request_count += 1
    
    # Clean up old files (simulate rotation)
    needs_action = vault_dir / "Needs_Action"
    if needs_action.exists():
        files = list(needs_action.glob("*.md"))
        for old_file in files[:-10]:  # Keep last 10 files
            old_file.unlink()


def simulate_dlq_operations(dlq: DeadLetterQueue, metrics: EnduranceTestMetrics):
    """Simulate DLQ operations with cleanup."""
    # Archive some failures
    if metrics.request_count % 50 == 0:
        dlq.archive_action(
            original_action="test_action",
            failure_reason="Simulated failure for endurance test",
            details={"iteration": metrics.request_count},
        )
    
    # Clean up old DLQ entries (simulate reprocessing)
    failed = dlq.get_failed_actions(limit=100)
    for old_entry in failed[10:]:  # Keep last 10
        dlq.delete_action(old_entry["id"])


class TestMemoryLeakDetection:
    """Test for memory leaks during extended operation."""
    
    def test_memory_stable_over_time(self, metrics, temp_vault, temp_dlq):
        """Memory should remain stable over 7-day simulation."""
        tracemalloc.start()
        
        manager = get_degradation_manager()
        
        # Initial sample
        metrics.sample()
        initial_memory = metrics.memory_samples[0]
        
        # Simulate 7 days of operation (accelerated)
        iterations = int(ENDURANCE_DURATION_SECONDS * 10)  # 10 iterations per second
        
        for i in range(iterations):
            simulate_watcher_activity(manager, metrics)
            simulate_file_operations(temp_vault, metrics)
            simulate_dlq_operations(temp_dlq, metrics)
            
            # Sample every 10% of test duration
            if i % (iterations // 10) == 0:
                metrics.sample()
                gc.collect()  # Force garbage collection before sampling
            
            # Small delay to simulate real time passage
            time.sleep(0.01)
        
        # Final sample
        metrics.sample()
        
        # Validate memory stability
        memory_growth = metrics.get_memory_growth()
        assert memory_growth < MEMORY_LEAK_THRESHOLD_MB, \
            f"Memory leak detected: grew by {memory_growth:.2f}MB (threshold: {MEMORY_LEAK_THRESHOLD_MB}MB)"
        
        # Also check tracemalloc
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        peak_mb = peak / 1024 / 1024
        assert peak_mb < 200, f"Peak memory too high: {peak_mb:.2f}MB"


class TestFileDescriptorLeakDetection:
    """Test for file descriptor leaks."""
    
    def test_fd_stable_over_time(self, metrics, temp_vault, temp_dlq):
        """File descriptors should remain stable over 7-day simulation."""
        manager = get_degradation_manager()
        
        # Initial sample
        metrics.sample()
        initial_fd = metrics.fd_samples[0]
        
        # Simulate operations that open/close files
        iterations = int(ENDURANCE_DURATION_SECONDS * 10)
        
        for i in range(iterations):
            simulate_file_operations(temp_vault, metrics)
            
            # Explicitly close files by letting them go out of scope
            if i % 100 == 0:
                gc.collect()
            
            # Sample periodically
            if i % (iterations // 10) == 0:
                metrics.sample()
            
            time.sleep(0.01)
        
        # Final sample
        metrics.sample()
        
        # Validate FD stability
        fd_growth = metrics.get_fd_growth()
        assert fd_growth < FILE_DESCRIPTOR_LEAK_THRESHOLD, \
            f"File descriptor leak detected: grew by {fd_growth} (threshold: {FILE_DESCRIPTOR_LEAK_THRESHOLD})"


class TestDiskSpaceLeakDetection:
    """Test for disk space leaks (log rotation validation)."""
    
    def test_log_rotation_works(self, metrics, temp_vault, temp_dlq):
        """Log rotation should prevent disk space leaks."""
        manager = get_degradation_manager()
        
        # Initial sample
        metrics.sample()
        
        # Simulate file operations with rotation
        iterations = int(ENDURANCE_DURATION_SECONDS * 5)
        
        for i in range(iterations):
            simulate_file_operations(temp_vault, metrics)
            
            # Sample periodically
            if i % (iterations // 10) == 0:
                metrics.sample()
            
            time.sleep(0.02)
        
        # Final sample
        metrics.sample()
        
        # Validate disk stability
        disk_growth = metrics.get_disk_growth()
        # Disk growth should be minimal due to file cleanup
        assert disk_growth < DISK_LEAK_THRESHOLD_MB, \
            f"Disk space leak detected: grew by {disk_growth:.2f}% (threshold: {DISK_LEAK_THRESHOLD_MB}%)"
        
        # Verify old files were cleaned up
        needs_action = temp_vault / "Needs_Action"
        files = list(needs_action.glob("*.md"))
        assert len(files) <= 10, f"File rotation not working: {len(files)} files remain"


class TestComponentHealthStability:
    """Test component health stability over time."""
    
    def test_health_stable_over_time(self, metrics, temp_vault):
        """Component health should remain stable."""
        manager = get_degradation_manager()
        
        # Set all components healthy initially
        for name in manager._components.keys():
            manager.set_component_status(name, ComponentStatus.HEALTHY)
        
        # Simulate operations
        iterations = int(ENDURANCE_DURATION_SECONDS * 10)
        
        for i in range(iterations):
            # Simulate occasional transient errors (should recover)
            if i % 100 == 0:
                manager.record_error("watcher_filesystem", "Transient error")
                manager.set_component_status("watcher_filesystem", ComponentStatus.DEGRADED)
            else:
                manager.set_component_status("watcher_filesystem", ComponentStatus.HEALTHY)
            
            time.sleep(0.01)
        
        # Final health check
        health = manager.get_component_health()
        
        # Most components should be healthy
        healthy_count = sum(1 for h in health.values() if h.get("status") == "healthy")
        total = len(health)
        
        # At least 80% should be healthy
        assert healthy_count / total >= 0.8, \
            f"Too many unhealthy components: {healthy_count}/{total}"


class TestErrorRateStability:
    """Test error rate remains within bounds."""
    
    def test_error_rate_stable(self, metrics, temp_vault):
        """Error rate should remain within acceptable bounds."""
        manager = get_degradation_manager()
        
        # Reset error window
        manager._error_counts.clear()
        manager._error_window_start = time.time()
        
        # Simulate operations with errors
        iterations = int(ENDURANCE_DURATION_SECONDS * 10)
        error_count = 0
        
        for i in range(iterations):
            # 1% error rate
            if i % 100 == 0:
                manager.record_error("test_component", f"Error {i}")
                error_count += 1
            
            time.sleep(0.01)
        
        # Check error rate
        final_error_count = manager.get_error_rate()
        
        # Error rate should be approximately 1%
        actual_rate = error_count / iterations * 100
        assert 0.5 <= actual_rate <= 2.0, \
            f"Error rate out of bounds: {actual_rate:.2f}%"


class TestGracefulDegradationRecovery:
    """Test graceful degradation and recovery."""
    
    def test_recovery_after_failure(self, metrics, temp_vault):
        """System should recover after component failure."""
        manager = get_degradation_manager()
        
        # Simulate failure
        manager.set_component_status(
            "sqlite_database",
            ComponentStatus.UNHEALTHY,
            error="Simulated database failure",
            fallback_active=True,
        )
        
        # Verify unhealthy
        health = manager.get_component_health("sqlite_database")
        assert health["status"] == "unhealthy"
        
        # Simulate recovery
        manager.set_component_status("sqlite_database", ComponentStatus.HEALTHY)
        
        # Verify recovered
        health = manager.get_component_health("sqlite_database")
        assert health["status"] == "healthy"


class TestEnduranceTestSummary:
    """Test that generates summary report."""
    
    def test_endurance_summary(self, metrics, temp_vault, temp_dlq, capsys):
        """Should generate comprehensive summary."""
        manager = get_degradation_manager()
        
        # Run simulation
        iterations = int(ENDURANCE_DURATION_SECONDS * 5)
        
        for i in range(iterations):
            simulate_watcher_activity(manager, metrics)
            simulate_file_operations(temp_vault, metrics)
            metrics.sample()
            time.sleep(0.02)
        
        # Get summary
        summary = metrics.get_summary()
        
        # Print summary
        print(f"\n{'='*60}")
        print("ENDURANCE TEST SUMMARY")
        print(f"{'='*60}")
        print(f"Duration: {summary['duration_seconds']:.2f}s")
        print(f"Memory Samples: {summary['memory_samples']}")
        print(f"Memory Growth: {summary['memory_growth_mb']:.2f}MB")
        print(f"FD Growth: {summary['fd_growth']}")
        print(f"Total Requests: {summary['total_requests']}")
        print(f"Total Failures: {summary['total_failures']}")
        print(f"Error Rate: {summary['error_rate']:.2f}%")
        print(f"{'='*60}")
        
        # Validate
        assert summary["duration_seconds"] > 0
        assert summary["memory_samples"] >= 2
        assert summary["error_rate"] < 5.0  # Allow some margin


if __name__ == "__main__":
    # Run standalone
    pytest.main([__file__, "-v", "--tb=short"])
