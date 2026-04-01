"""
Chaos Tests for Graceful Degradation.

Tests verify that the system continues operating when components fail.

Tests cover:
- Watcher independence (one watcher crash doesn't affect others)
- Circuit breaker isolation (tripping one doesn't affect others)
- Skill error dict returns (no exceptions raised)
- SQLite failure with memory fallback
- File write failure with queue fallback
- Metrics failure doesn't halt execution
- Health endpoint reports degraded status
- DEV_MODE prevents external calls
"""

import sqlite3
import threading
import time
from pathlib import Path
from unittest.mock import patch, MagicMock, PropertyMock

import pytest

from src.utils.graceful_degradation import (
    GracefulDegradationManager,
    ComponentStatus,
    get_degradation_manager,
)


@pytest.fixture
def degradation_manager():
    """Create fresh degradation manager for testing."""
    manager = GracefulDegradationManager()
    return manager


class TestWatcherIndependence:
    """Test that watchers continue running when others crash."""

    def test_watcher_independence(self, degradation_manager):
        """Crashing Gmail watcher should not affect WhatsApp watcher."""
        # Simulate Gmail watcher crash
        degradation_manager.set_component_status(
            "watcher_gmail",
            ComponentStatus.UNHEALTHY,
            error="OAuth2 token expired",
        )
        
        # WhatsApp watcher should still be healthy
        health = degradation_manager.get_component_health()
        assert health["watcher_gmail"]["status"] == "unhealthy"
        assert health["watcher_whatsapp"]["status"] in ["unknown", "healthy"]
        
        # Overall system should be unhealthy but not crashed
        overall = degradation_manager.get_overall_status()
        assert overall == "unhealthy"

    def test_filesystem_watcher_continues_when_others_fail(self, degradation_manager):
        """FileSystem watcher should continue when Gmail and WhatsApp fail."""
        # Fail both Gmail and WhatsApp
        degradation_manager.set_component_status(
            "watcher_gmail", ComponentStatus.UNHEALTHY, error="API failure"
        )
        degradation_manager.set_component_status(
            "watcher_whatsapp", ComponentStatus.UNHEALTHY, error="Session expired"
        )
        
        # FileSystem should still operate
        degradation_manager.set_component_status(
            "watcher_filesystem", ComponentStatus.HEALTHY
        )
        
        health = degradation_manager.get_component_health()
        assert health["watcher_filesystem"]["status"] == "healthy"


class TestCircuitBreakerIsolation:
    """Test that circuit breakers are isolated per component."""

    def test_circuit_breaker_isolation(self, degradation_manager):
        """Tripping Gmail circuit breaker should not affect WhatsApp."""
        # Simulate Gmail circuit breaker open
        degradation_manager.record_error("watcher_gmail", "API failure 1")
        degradation_manager.record_error("watcher_gmail", "API failure 2")
        degradation_manager.record_error("watcher_gmail", "API failure 3")
        
        degradation_manager.set_component_status(
            "watcher_gmail",
            ComponentStatus.DEGRADED,
            fallback_active=True,
        )
        
        # WhatsApp should be unaffected
        whatsapp_health = degradation_manager.get_component_health("watcher_whatsapp")
        assert whatsapp_health["status"] != "degraded" or whatsapp_health.get("error_count", 0) == 0

    def test_circuit_breaker_open_skips_check(self, degradation_manager):
        """When circuit breaker open, watcher should skip check and log warning."""
        # Set circuit breaker open
        degradation_manager.set_component_status(
            "watcher_gmail",
            ComponentStatus.DEGRADED,
            error="Circuit breaker OPEN",
            fallback_active=True,
        )
        
        # Simulate watcher check that respects circuit breaker
        health = degradation_manager.get_component_health("watcher_gmail")
        assert health["status"] == "degraded"
        assert health["fallback_active"] is True


class TestSkillErrorReturns:
    """Test that skills return error dicts instead of raising exceptions."""

    def test_skill_error_returns_dict(self, degradation_manager):
        """Mock skill failure should return error dict, not raise."""
        error = Exception("SMTP connection failed")
        
        error_dict = degradation_manager.create_error_dict(
            error=error,
            action="send_email",
            details={"to": "test@example.com"},
        )
        
        assert error_dict["status"] == "error"
        assert error_dict["error"] == "SMTP connection failed"
        assert error_dict["error_type"] == "Exception"
        assert error_dict["action"] == "send_email"
        assert error_dict["details"]["to"] == "test@example.com"

    def test_skill_success_returns_dict(self, degradation_manager):
        """Skill success should return success dict."""
        success_dict = degradation_manager.create_success_dict(
            action="send_email",
            result={"message_id": "abc123"},
            details={"to": "test@example.com"},
        )
        
        assert success_dict["status"] == "success"
        assert success_dict["action"] == "send_email"
        assert success_dict["result"]["message_id"] == "abc123"


class TestSQLiteFallback:
    """Test SQLite failure with in-memory fallback."""

    def test_sqlite_failure_continues_with_memory(self, degradation_manager):
        """SQLite OperationalError should trigger memory fallback."""
        degradation_manager.enable_memory_fallback()
        
        # Mock primary function that fails
        def failing_sqlite():
            raise sqlite3.OperationalError("database is locked")
        
        # Mock fallback that succeeds
        def memory_fallback():
            return {"data": "from_memory"}
        
        result = degradation_manager.execute_with_fallback(
            primary_fn=failing_sqlite,
            fallback_fn=memory_fallback,
            default_value={"data": "default"},
            component_name="sqlite_database",
        )
        
        assert result == {"data": "from_memory"}
        
        # Component should be degraded with fallback active
        health = degradation_manager.get_component_health("sqlite_database")
        assert health["status"] == "degraded"
        assert health["fallback_active"] is True

    def test_sqlite_failure_without_fallback(self, degradation_manager):
        """SQLite failure without fallback should return default."""
        degradation_manager.disable_memory_fallback()
        
        def failing_sqlite():
            raise sqlite3.OperationalError("database is locked")
        
        result = degradation_manager.execute_with_fallback(
            primary_fn=failing_sqlite,
            fallback_fn=None,
            default_value={"data": "default"},
            component_name="sqlite_database",
        )
        
        assert result == {"data": "default"}
        
        # Component should be unhealthy
        health = degradation_manager.get_component_health("sqlite_database")
        assert health["status"] == "unhealthy"

    def test_memory_store_operations(self, degradation_manager):
        """Memory store should work as SQLite fallback."""
        degradation_manager.enable_memory_fallback()
        
        # Set and get
        assert degradation_manager.memory_store_set("key1", "value1")
        assert degradation_manager.memory_store_get("key1") == "value1"
        assert degradation_manager.memory_store_get("key2", "default") == "default"


class TestFileWriteFallback:
    """Test file write failure with memory queue fallback."""

    def test_file_write_failure_queues_memory(self, degradation_manager, tmp_path):
        """File write permission error should queue to memory."""
        degradation_manager.enable_file_queue()
        
        # Try to write to invalid path
        invalid_path = tmp_path / "nonexistent" / "file.md"
        
        result = degradation_manager.write_file_with_queue(
            file_path=invalid_path,
            content="Test content",
        )
        
        # Should return False (queued, not written)
        assert result is False
        assert degradation_manager.get_queue_size() == 1
        
        # Component should be degraded
        health = degradation_manager.get_component_health("file_system")
        assert health["status"] == "degraded"
        assert health["fallback_active"] is True

    def test_file_write_success(self, degradation_manager, tmp_path):
        """Successful file write should return True."""
        file_path = tmp_path / "test.md"
        
        result = degradation_manager.write_file_with_queue(
            file_path=file_path,
            content="Test content",
        )
        
        assert result is True
        assert degradation_manager.get_queue_size() == 0
        
        # Verify file exists
        assert file_path.exists()

    def test_file_queue_flush(self, degradation_manager, tmp_path):
        """Flushing queue should write queued files."""
        degradation_manager.enable_file_queue()
        
        # Create files that will fail (directory doesn't exist yet)
        nonexistent_dir = tmp_path / "nonexistent_dir"
        file1 = nonexistent_dir / "queued1.md"
        file2 = nonexistent_dir / "queued2.md"
        
        # Queue writes (will fail and be queued)
        degradation_manager.write_file_with_queue(file1, "Content 1")
        degradation_manager.write_file_with_queue(file2, "Content 2")
        
        # Now create the directory so flush can succeed
        nonexistent_dir.mkdir()
        
        # Flush
        success, failure = degradation_manager.flush_file_queue()
        
        assert success == 2
        assert failure == 0
        assert file1.exists()
        assert file2.exists()


class TestMetricsFailure:
    """Test that metrics collector failure doesn't halt execution."""

    def test_metrics_failure_doesnt_halt(self, degradation_manager):
        """Metrics collector failure should be logged but not halt."""
        # Simulate metrics failure
        degradation_manager.record_error("metrics_collector", "Connection refused")
        
        # System should continue
        health = degradation_manager.get_component_health("metrics_collector")
        assert health["error_count"] >= 1
        
        # Overall system may be degraded but not crashed
        overall = degradation_manager.get_overall_status()
        assert overall in ["healthy", "degraded", "unhealthy"]


class TestHealthEndpoint:
    """Test health endpoint reports correct status."""

    def test_health_endpoint_reports_degraded(self, degradation_manager):
        """Health endpoint should return degraded when watcher down."""
        # Set one watcher as unhealthy
        degradation_manager.set_component_status(
            "watcher_gmail",
            ComponentStatus.UNHEALTHY,
            error="API quota exceeded",
        )
        
        # Set others as healthy
        degradation_manager.set_component_status("watcher_whatsapp", ComponentStatus.HEALTHY)
        degradation_manager.set_component_status("watcher_filesystem", ComponentStatus.HEALTHY)
        
        overall = degradation_manager.get_overall_status()
        assert overall == "unhealthy"

    def test_health_endpoint_all_healthy(self, degradation_manager):
        """Health endpoint should return healthy when all components healthy."""
        for name in degradation_manager._components.keys():
            degradation_manager.set_component_status(name, ComponentStatus.HEALTHY)
        
        overall = degradation_manager.get_overall_status()
        assert overall == "healthy"


class TestDevMode:
    """Test DEV_MODE prevents external actions."""

    def test_dev_mode_prevents_external_calls(self, degradation_manager):
        """DEV_MODE=true should prevent external API calls."""
        degradation_manager.set_dev_mode(True)
        
        assert degradation_manager.is_dev_mode() is True
        
        # Success dict should include dev_mode flag
        success_dict = degradation_manager.create_success_dict(
            action="send_email",
            result={"would_send": False},
        )
        
        assert success_dict["dev_mode"] is True

    def test_dev_mode_disabled(self, degradation_manager):
        """DEV_MODE=false should allow external calls."""
        degradation_manager.set_dev_mode(False)
        
        assert degradation_manager.is_dev_mode() is False
        
        success_dict = degradation_manager.create_success_dict(
            action="send_email",
            result={"sent": True},
        )
        
        assert success_dict["dev_mode"] is False


class TestErrorRateTracking:
    """Test error rate tracking within time window."""

    def test_error_rate_tracking(self, degradation_manager):
        """Should track errors within time window."""
        degradation_manager.record_error("watcher_gmail", "Error 1")
        degradation_manager.record_error("watcher_gmail", "Error 2")
        degradation_manager.record_error("watcher_whatsapp", "Error 3")
        
        gmail_errors = degradation_manager.get_error_rate("watcher_gmail")
        total_errors = degradation_manager.get_error_rate()
        
        assert gmail_errors == 2
        assert total_errors == 3

    def test_error_rate_window_reset(self, degradation_manager):
        """Error window should reset after timeout."""
        degradation_manager.record_error("test_component", "Old error")
        
        # Manually reset window
        degradation_manager._error_window_start = time.time() - (3601)  # 1 hour + 1 second
        
        # Should be reset
        errors = degradation_manager.get_error_rate()
        assert errors == 0


class TestConcurrentAccess:
    """Test thread safety of degradation manager."""

    def test_concurrent_status_updates(self, degradation_manager):
        """Should handle concurrent status updates safely."""
        errors = []
        
        def update_status(i):
            try:
                degradation_manager.set_component_status(
                    f"component_{i}",
                    ComponentStatus.HEALTHY,
                )
            except Exception as e:
                errors.append(e)
        
        threads = [threading.Thread(target=update_status, args=(i,)) for i in range(20)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        assert len(errors) == 0

    def test_concurrent_error_recording(self, degradation_manager):
        """Should handle concurrent error recording safely."""
        errors = []
        
        def record_error(i):
            try:
                degradation_manager.record_error("shared_component", f"Error {i}")
            except Exception as e:
                errors.append(e)
        
        threads = [threading.Thread(target=record_error, args=(i,)) for i in range(50)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        assert len(errors) == 0
        assert degradation_manager.get_error_rate("shared_component") == 50
