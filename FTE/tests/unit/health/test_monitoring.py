"""
Unit tests for FTE-Agent Resource Monitoring
Coverage: ResourceMonitor, MetricsCollector, AlertThresholds
"""

from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from src.health.monitoring import (
    AlertThresholds,
    MetricsCollector,
    ResourceMetrics,
    ResourceMonitor,
)


class TestResourceMetrics:
    """Tests for ResourceMetrics dataclass."""

    def test_to_dict(self):
        """Test conversion to dictionary."""
        metrics = ResourceMetrics(
            timestamp="2026-04-02T08:15:30Z",
            cpu_percent=45.5,
            memory_percent=62.3,
            memory_used_gb=7.5,
            memory_total_gb=12.0,
            disk_percent=71.2,
            disk_free_gb=57.8,
            disk_total_gb=200.0,
        )

        data = metrics.to_dict()

        assert data["timestamp"] == "2026-04-02T08:15:30Z"
        assert data["cpu_percent"] == 45.5
        assert data["memory_percent"] == 62.3
        assert data["disk_percent"] == 71.2


class TestAlertThresholds:
    """Tests for AlertThresholds configuration."""

    def test_cpu_thresholds(self):
        """Test CPU threshold values."""
        assert AlertThresholds.CPU_WARNING == 80.0
        assert AlertThresholds.CPU_CRITICAL == 95.0

    def test_memory_thresholds(self):
        """Test memory threshold values."""
        assert AlertThresholds.MEMORY_WARNING == 80.0
        assert AlertThresholds.MEMORY_CRITICAL == 95.0

    def test_disk_thresholds(self):
        """Test disk threshold values."""
        assert AlertThresholds.DISK_WARNING == 80.0
        assert AlertThresholds.DISK_CRITICAL == 90.0


class TestResourceMonitor:
    """Tests for ResourceMonitor class."""

    @pytest.fixture
    def monitor(self):
        """Create ResourceMonitor instance."""
        return ResourceMonitor(log_path=Path("/tmp/test-logs"))

    @patch("src.health.monitoring.psutil")
    def test_get_cpu_percent(self, mock_psutil, monitor):
        """Test CPU percentage retrieval."""
        mock_psutil.cpu_percent.return_value = 45.5
        cpu = monitor.get_cpu_percent()
        assert cpu == 45.5
        mock_psutil.cpu_percent.assert_called_once_with(interval=1)

    @patch("src.health.monitoring.psutil")
    def test_get_memory_info(self, mock_psutil, monitor):
        """Test memory info retrieval."""
        mock_memory = Mock()
        mock_memory.percent = 62.3
        mock_memory.used = 7.5 * (1024**3)
        mock_memory.total = 12.0 * (1024**3)
        mock_psutil.virtual_memory.return_value = mock_memory

        info = monitor.get_memory_info()

        assert info["percent"] == 62.3
        assert info["used_gb"] == 7.5
        assert info["total_gb"] == 12.0

    @patch("src.health.monitoring.psutil")
    def test_get_disk_info(self, mock_psutil, monitor):
        """Test disk info retrieval."""
        mock_disk = Mock()
        mock_disk.percent = 71.2
        mock_disk.free = 57.8 * (1024**3)
        mock_disk.total = 200.0 * (1024**3)
        mock_psutil.disk_usage.return_value = mock_disk

        info = monitor.get_disk_info()

        assert info["percent"] == 71.2
        assert info["free_gb"] == 57.8
        assert info["total_gb"] == 200.0

    @patch("src.health.monitoring.psutil")
    def test_get_all_metrics(self, mock_psutil, monitor):
        """Test getting all metrics."""
        mock_psutil.cpu_percent.return_value = 45.5

        mock_memory = Mock()
        mock_memory.percent = 62.3
        mock_memory.used = 7.5 * (1024**3)
        mock_memory.total = 12.0 * (1024**3)
        mock_psutil.virtual_memory.return_value = mock_memory

        mock_disk = Mock()
        mock_disk.percent = 71.2
        mock_disk.free = 57.8 * (1024**3)
        mock_disk.total = 200.0 * (1024**3)
        mock_psutil.disk_usage.return_value = mock_disk

        metrics = monitor.get_all_metrics()

        assert "cpu_percent" in metrics
        assert "memory_percent" in metrics
        assert "disk_percent" in metrics
        assert metrics["cpu_percent"] == 45.5
        assert metrics["memory_percent"] == 62.3
        assert metrics["disk_percent"] == 71.2

    @patch.object(ResourceMonitor, "get_cpu_percent")
    @patch.object(ResourceMonitor, "get_memory_info")
    @patch.object(ResourceMonitor, "get_disk_info")
    def test_collect_metrics(
        self,
        mock_disk_info,
        mock_memory_info,
        mock_cpu_percent,
        monitor,
    ):
        """Test metrics collection."""
        mock_cpu_percent.return_value = 45.5
        mock_memory_info.return_value = {
            "percent": 62.3,
            "used_gb": 7.5,
            "total_gb": 12.0,
        }
        mock_disk_info.return_value = {
            "percent": 71.2,
            "free_gb": 57.8,
            "total_gb": 200.0,
        }

        metrics = monitor.collect_metrics()

        assert isinstance(metrics, ResourceMetrics)
        assert metrics.cpu_percent == 45.5
        assert metrics.memory_percent == 62.3
        assert metrics.disk_percent == 71.2
        assert metrics.timestamp is not None

    @patch.object(ResourceMonitor, "_send_alert")
    @patch.object(ResourceMonitor, "get_cpu_percent")
    def test_check_thresholds_cpu_warning(
        self,
        mock_cpu_percent,
        mock_send_alert,
        monitor,
    ):
        """Test CPU warning threshold."""
        mock_cpu_percent.return_value = 85.0  # Above WARNING (80)

        from src.health.monitoring import ResourceMetrics

        metrics = ResourceMetrics(
            timestamp=datetime.now(UTC).isoformat(),
            cpu_percent=85.0,
            memory_percent=50.0,
            memory_used_gb=6.0,
            memory_total_gb=12.0,
            disk_percent=60.0,
            disk_free_gb=80.0,
            disk_total_gb=200.0,
        )

        monitor._check_thresholds(metrics)

        mock_send_alert.assert_called_once()
        call_args = mock_send_alert.call_args[0]
        assert call_args[0] == "WARNING"
        assert "CPU usage high" in call_args[1]

    @patch.object(ResourceMonitor, "_send_alert")
    def test_check_thresholds_disk_critical(self, mock_send_alert, monitor):
        """Test disk critical threshold."""
        from src.health.monitoring import ResourceMetrics

        metrics = ResourceMetrics(
            timestamp=datetime.now(UTC).isoformat(),
            cpu_percent=40.0,
            memory_percent=50.0,
            memory_used_gb=6.0,
            memory_total_gb=12.0,
            disk_percent=95.0,  # Above CRITICAL (90)
            disk_free_gb=10.0,
            disk_total_gb=200.0,
        )

        monitor._check_thresholds(metrics)

        mock_send_alert.assert_called_once()
        call_args = mock_send_alert.call_args[0]
        assert call_args[0] == "CRITICAL"
        assert "Disk usage critical" in call_args[1]

    def test_send_alert_with_callback(self, monitor):
        """Test alert callback."""
        mock_callback = Mock()
        monitor.alert_callback = mock_callback

        monitor._send_alert("WARNING", "Test alert message")

        mock_callback.assert_called_once_with("WARNING", "Test alert message")

    @patch.object(ResourceMonitor, "collect_metrics")
    @patch.object(ResourceMonitor, "log_metrics")
    @patch("src.health.monitoring.time.sleep", side_effect=InterruptedError())
    def test_start_monitoring(
        self,
        mock_sleep,
        mock_log_metrics,
        mock_collect_metrics,
        monitor,
    ):
        """Test monitoring loop."""
        from src.health.monitoring import ResourceMetrics

        mock_metrics = ResourceMetrics(
            timestamp=datetime.now(UTC).isoformat(),
            cpu_percent=45.5,
            memory_percent=62.3,
            memory_used_gb=7.5,
            memory_total_gb=12.0,
            disk_percent=71.2,
            disk_free_gb=57.8,
            disk_total_gb=200.0,
        )
        mock_collect_metrics.return_value = mock_metrics

        # Should raise InterruptedError from time.sleep
        with pytest.raises(InterruptedError):
            monitor.start_monitoring()

        mock_collect_metrics.assert_called()
        mock_log_metrics.assert_called()

    def test_get_metrics_history(self, monitor):
        """Test metrics history retrieval."""
        from src.health.monitoring import ResourceMetrics

        # Add some metrics
        for i in range(3):
            metrics = ResourceMetrics(
                timestamp=datetime.now(UTC).isoformat(),
                cpu_percent=40.0 + i,
                memory_percent=50.0 + i,
                memory_used_gb=6.0 + i,
                memory_total_gb=12.0,
                disk_percent=60.0 + i,
                disk_free_gb=80.0 - i,
                disk_total_gb=200.0,
            )
            monitor._metrics_history.append(metrics)

        history = monitor.get_metrics_history()

        assert len(history) == 3
        assert all(isinstance(m, dict) for m in history)


class TestMetricsCollector:
    """Tests for MetricsCollector class."""

    @pytest.fixture
    def collector(self):
        """Create MetricsCollector instance."""
        return MetricsCollector()

    @patch.object(ResourceMonitor, "get_all_metrics")
    def test_collect(self, mock_get_metrics, collector):
        """Test metrics collection."""
        mock_get_metrics.return_value = {
            "cpu_percent": 45.5,
            "memory_percent": 62.3,
            "disk_percent": 71.2,
        }

        metrics = collector.collect()

        assert metrics["cpu_percent"] == 45.5
        assert metrics["memory_percent"] == 62.3

    @patch.object(ResourceMonitor, "get_all_metrics")
    def test_collect_with_timestamp(self, mock_get_metrics, collector):
        """Test metrics collection with timestamp."""
        mock_get_metrics.return_value = {
            "cpu_percent": 45.5,
            "memory_percent": 62.3,
            "disk_percent": 71.2,
        }

        metrics = collector.collect_with_timestamp()

        assert "timestamp" in metrics
        assert "cpu_percent" in metrics
        assert metrics["cpu_percent"] == 45.5
