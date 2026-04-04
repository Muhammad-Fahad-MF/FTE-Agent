"""
FTE-Agent Resource Monitoring
Purpose: Monitor CPU, memory, and disk utilization with psutil
Version: 1.0.0 (Platinum Tier)

Features:
- CPU usage monitoring (percentage)
- Memory usage monitoring (percentage, GB)
- Disk usage monitoring (percentage, free GB)
- Metrics logging every 60 seconds
- Alert thresholds (CPU >80%, Disk >90%)
"""

import logging
import time
from collections.abc import Callable
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import psutil

logger = logging.getLogger(__name__)


@dataclass
class ResourceMetrics:
    """Resource metrics data class."""

    timestamp: str
    cpu_percent: float
    memory_percent: float
    memory_used_gb: float
    memory_total_gb: float
    disk_percent: float
    disk_free_gb: float
    disk_total_gb: float

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


class AlertThresholds:
    """Alert threshold configuration."""

    CPU_WARNING = 80.0  # Percent
    CPU_CRITICAL = 95.0  # Percent
    MEMORY_WARNING = 80.0  # Percent
    MEMORY_CRITICAL = 95.0  # Percent
    DISK_WARNING = 80.0  # Percent
    DISK_CRITICAL = 90.0  # Percent


class ResourceMonitor:
    """
    Resource monitor for FTE-Agent Cloud VM.

    Monitors CPU, memory, and disk utilization.
    Logs metrics every 60 seconds.
    Generates alerts when thresholds are breached.
    """

    def __init__(
        self,
        log_path: Path | None = None,
        log_interval: int = 60,
        alert_callback: Callable[[str, str], None] | None = None,
    ):
        """
        Initialize resource monitor.

        Args:
            log_path: Path to log directory
            log_interval: Logging interval in seconds (default: 60)
            alert_callback: Callback for alerts (severity, message)
        """
        self.log_path = log_path or Path("/tmp/fte-agent/logs")
        self.log_interval = log_interval
        self.alert_callback = alert_callback
        self._last_log_time = 0
        self._metrics_history: list[ResourceMetrics] = []

    def get_cpu_percent(self) -> float:
        """Get CPU usage percentage."""
        return psutil.cpu_percent(interval=1)

    def get_memory_info(self) -> dict[str, float]:
        """
        Get memory information.

        Returns:
            Dict with percent, used_gb, total_gb
        """
        memory = psutil.virtual_memory()
        return {
            "percent": memory.percent,
            "used_gb": memory.used / (1024**3),
            "total_gb": memory.total / (1024**3),
        }

    def get_disk_info(self, path: str = "/") -> dict[str, float]:
        """
        Get disk information.

        Args:
            path: Path to check (default: root)

        Returns:
            Dict with percent, free_gb, total_gb
        """
        disk = psutil.disk_usage(path)
        return {
            "percent": disk.percent,
            "free_gb": disk.free / (1024**3),
            "total_gb": disk.total / (1024**3),
        }

    def get_all_metrics(self) -> dict[str, Any]:
        """
        Get all resource metrics.

        Returns:
            Dict with cpu, memory, disk metrics
        """
        cpu_percent = psutil.cpu_percent(interval=0.1)  # Non-blocking
        memory_info = self.get_memory_info()
        disk_info = self.get_disk_info()

        return {
            "cpu_percent": cpu_percent,
            "memory_percent": memory_info["percent"],
            "memory_used_gb": memory_info["used_gb"],
            "memory_total_gb": memory_info["total_gb"],
            "disk_percent": disk_info["percent"],
            "disk_free_gb": disk_info["free_gb"],
            "disk_total_gb": disk_info["total_gb"],
        }

    def collect_metrics(self) -> ResourceMetrics:
        """
        Collect and record metrics.

        Returns:
            ResourceMetrics object
        """
        now = datetime.now(UTC)
        cpu_percent = self.get_cpu_percent()
        memory_info = self.get_memory_info()
        disk_info = self.get_disk_info()

        metrics = ResourceMetrics(
            timestamp=now.isoformat(),
            cpu_percent=cpu_percent,
            memory_percent=memory_info["percent"],
            memory_used_gb=memory_info["used_gb"],
            memory_total_gb=memory_info["total_gb"],
            disk_percent=disk_info["percent"],
            disk_free_gb=disk_info["free_gb"],
            disk_total_gb=disk_info["total_gb"],
        )

        self._metrics_history.append(metrics)

        # Check thresholds and generate alerts
        self._check_thresholds(metrics)

        return metrics

    def _check_thresholds(self, metrics: ResourceMetrics) -> None:
        """
        Check metrics against thresholds and generate alerts.

        Args:
            metrics: ResourceMetrics object
        """
        # CPU alerts
        if metrics.cpu_percent >= AlertThresholds.CPU_CRITICAL:
            threshold = AlertThresholds.CPU_CRITICAL
            self._send_alert(
                "CRITICAL",
                f"CPU usage critical: {metrics.cpu_percent:.1f}% (threshold: {threshold}%)",
            )
        elif metrics.cpu_percent >= AlertThresholds.CPU_WARNING:
            threshold = AlertThresholds.CPU_WARNING
            self._send_alert(
                "WARNING",
                f"CPU usage high: {metrics.cpu_percent:.1f}% (threshold: {threshold}%)",
            )

        # Memory alerts
        if metrics.memory_percent >= AlertThresholds.MEMORY_CRITICAL:
            threshold = AlertThresholds.MEMORY_CRITICAL
            self._send_alert(
                "CRITICAL",
                f"Memory usage critical: {metrics.memory_percent:.1f}% (threshold: {threshold}%)",
            )
        elif metrics.memory_percent >= AlertThresholds.MEMORY_WARNING:
            threshold = AlertThresholds.MEMORY_WARNING
            self._send_alert(
                "WARNING",
                f"Memory usage high: {metrics.memory_percent:.1f}% (threshold: {threshold}%)",
            )

        # Disk alerts
        if metrics.disk_percent >= AlertThresholds.DISK_CRITICAL:
            threshold = AlertThresholds.DISK_CRITICAL
            self._send_alert(
                "CRITICAL",
                f"Disk usage critical: {metrics.disk_percent:.1f}% (threshold: {threshold}%)",
            )
        elif metrics.disk_percent >= AlertThresholds.DISK_WARNING:
            threshold = AlertThresholds.DISK_WARNING
            self._send_alert(
                "WARNING",
                f"Disk usage high: {metrics.disk_percent:.1f}% (threshold: {threshold}%)",
            )

    def _send_alert(self, severity: str, message: str) -> None:
        """
        Send alert via callback.

        Args:
            severity: Alert severity (WARNING, CRITICAL)
            message: Alert message
        """
        logger.warning(f"[{severity}] {message}")

        if self.alert_callback:
            self.alert_callback(severity, message)

    def log_metrics(self, metrics: ResourceMetrics) -> None:
        """
        Log metrics to file.

        Args:
            metrics: ResourceMetrics object
        """
        log_file = self.log_path / "resource_metrics.jsonl"
        log_file.parent.mkdir(parents=True, exist_ok=True)

        log_entry = {
            "timestamp": metrics.timestamp,
            "level": "INFO",
            "component": "resource_monitor",
            "metrics": metrics.to_dict(),
        }

        with open(log_file, "a") as f:
            import json

            f.write(json.dumps(log_entry) + "\n")

    def start_monitoring(self) -> None:
        """
        Start continuous monitoring loop.

        Logs metrics every log_interval seconds.
        """
        logger.info(f"Starting resource monitoring (interval: {self.log_interval}s)")

        try:
            while True:
                metrics = self.collect_metrics()
                self.log_metrics(metrics)

                logger.info(
                    f"Resources: CPU={metrics.cpu_percent:.1f}%, "
                    f"Memory={metrics.memory_percent:.1f}%, "
                    f"Disk={metrics.disk_percent:.1f}%"
                )

                time.sleep(self.log_interval)
        except KeyboardInterrupt:
            logger.info("Resource monitoring stopped")

    def get_metrics_history(self) -> list[dict[str, Any]]:
        """
        Get metrics history.

        Returns:
            List of metrics dictionaries
        """
        return [m.to_dict() for m in self._metrics_history]


class MetricsCollector:
    """
    Metrics collector for periodic collection.

    Simpler alternative to ResourceMonitor for one-off collections.
    """

    def __init__(self):
        """Initialize metrics collector."""
        self.monitor = ResourceMonitor()

    def collect(self) -> dict[str, Any]:
        """
        Collect current metrics.

        Returns:
            Dict with all metrics
        """
        return self.monitor.get_all_metrics()

    def collect_with_timestamp(self) -> dict[str, Any]:
        """
        Collect metrics with timestamp.

        Returns:
            Dict with metrics and timestamp
        """
        metrics = self.collect()
        metrics["timestamp"] = datetime.now(UTC).isoformat()
        return metrics
