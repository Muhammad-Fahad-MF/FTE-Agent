"""
FTE-Agent Health Endpoint
Purpose: FastAPI health endpoint for Cloud VM monitoring
Version: 1.0.0 (Platinum Tier)

Endpoints:
- GET /health: Health status, uptime, resources, watcher status
- GET /metrics: Prometheus-compatible metrics
- GET /ready: Kubernetes-style readiness probe
"""

import logging
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Response
from fastapi.responses import PlainTextResponse

from .monitoring import ResourceMonitor

logger = logging.getLogger(__name__)


class HealthChecker:
    """
    Health checker for FTE-Agent Cloud VM.

    Provides health status, uptime tracking, and resource metrics.
    """

    def __init__(self, vault_path: Path | None = None):
        """
        Initialize health checker.

        Args:
            vault_path: Path to vault directory (for watcher status)
        """
        self.start_time = time.time()
        self.vault_path = vault_path or Path.home() / "fte-agent" / "vault"
        self.resource_monitor = ResourceMonitor()
        self._last_metrics_update = 0
        self._cached_metrics: dict[str, Any] = {}
        self._metrics_cache_ttl = 10  # seconds

    def get_uptime(self) -> int:
        """Get uptime in seconds."""
        return int(time.time() - self.start_time)

    def get_status(self) -> str:
        """
        Determine overall health status.

        Returns:
            "healthy" | "degraded" | "unhealthy"
        """
        metrics = self._get_cached_metrics()

        # Check for unhealthy conditions
        if metrics.get("disk_percent", 0) > 90:
            return "unhealthy"
        if metrics.get("cpu_percent", 0) > 95 or metrics.get("memory_percent", 0) > 95:
            return "unhealthy"

        # Check for degraded conditions
        if metrics.get("cpu_percent", 0) > 80:
            return "degraded"
        if metrics.get("memory_percent", 0) > 80:
            return "degraded"

        return "healthy"

    def _get_cached_metrics(self) -> dict[str, Any]:
        """Get cached metrics (refresh if TTL expired)."""
        now = time.time()
        if now - self._last_metrics_update > self._metrics_cache_ttl:
            self._cached_metrics = self.resource_monitor.get_all_metrics()
            self._last_metrics_update = now
        return self._cached_metrics

    def get_health_data(self) -> dict[str, Any]:
        """
        Get complete health data.

        Returns:
            Dict with status, uptime, resources, watchers, last_sync
        """
        metrics = self._get_cached_metrics()

        return {
            "status": self.get_status(),
            "uptime_seconds": self.get_uptime(),
            "timestamp": datetime.now(UTC).isoformat(),
            "resources": {
                "cpu_percent": metrics.get("cpu_percent", 0),
                "memory_percent": metrics.get("memory_percent", 0),
                "disk_percent": metrics.get("disk_percent", 0),
                "disk_free_gb": metrics.get("disk_free_gb", 0),
            },
            "watchers": self._get_watcher_status(),
            "last_sync": self._get_last_sync_time(),
        }

    def _get_watcher_status(self) -> dict[str, str]:
        """
        Get watcher status.

        Returns:
            Dict with watcher names and their status
        """
        # TODO: Query actual watcher status from process manager
        # For now, return static status
        return {
            "gmail": "running",
            "whatsapp": "running",
            "filesystem": "running",
        }

    def _get_last_sync_time(self) -> str:
        """Get last vault sync timestamp."""
        # TODO: Query actual sync time from sync module
        return datetime.now(UTC).isoformat()

    def get_prometheus_metrics(self) -> str:
        """
        Get Prometheus-compatible metrics.

        Returns:
            Prometheus text format metrics
        """
        metrics = self._get_cached_metrics()
        uptime = self.get_uptime()
        status = self.get_status()

        # Convert status to numeric (healthy=1, degraded=2, unhealthy=3)
        status_code = {"healthy": 1, "degraded": 2, "unhealthy": 3}.get(status, 0)

        lines = [
            "# HELP fte_agent_uptime_seconds Agent uptime in seconds",
            "# TYPE fte_agent_uptime_seconds counter",
            f"fte_agent_uptime_seconds {uptime}",
            "",
            "# HELP fte_agent_status Health status (1=healthy, 2=degraded, 3=unhealthy)",
            "# TYPE fte_agent_status gauge",
            f"fte_agent_status {status_code}",
            "",
            "# HELP fte_agent_cpu_percent CPU usage percentage",
            "# TYPE fte_agent_cpu_percent gauge",
            f"fte_agent_cpu_percent {metrics.get('cpu_percent', 0)}",
            "",
            "# HELP fte_agent_memory_percent Memory usage percentage",
            "# TYPE fte_agent_memory_percent gauge",
            f"fte_agent_memory_percent {metrics.get('memory_percent', 0)}",
            "",
            "# HELP fte_agent_disk_percent Disk usage percentage",
            "# TYPE fte_agent_disk_percent gauge",
            f"fte_agent_disk_percent {metrics.get('disk_percent', 0)}",
            "",
            "# HELP fte_agent_disk_free_gb Free disk space in GB",
            "# TYPE fte_agent_disk_free_gb gauge",
            f"fte_agent_disk_free_gb {metrics.get('disk_free_gb', 0)}",
        ]

        return "\n".join(lines)


def create_health_app(vault_path: Path | None = None) -> FastAPI:
    """
    Create FastAPI health endpoint application.

    Args:
        vault_path: Path to vault directory

    Returns:
        FastAPI application with health endpoints
    """
    app = FastAPI(
        title="FTE-Agent Health",
        description="Health monitoring for FTE-Agent Cloud VM",
        version="1.0.0",
    )

    health_checker = HealthChecker(vault_path)

    @app.get("/health")
    async def health_check() -> dict[str, Any]:
        """
        Get health status.

        Returns:
            JSON with status, uptime, resources, watchers, last_sync
        """
        return health_checker.get_health_data()

    @app.get("/metrics")
    async def metrics() -> PlainTextResponse:
        """
        Get Prometheus-compatible metrics.

        Returns:
            Prometheus text format metrics
        """
        return PlainTextResponse(health_checker.get_prometheus_metrics())

    @app.get("/ready")
    async def readiness_probe() -> Response:
        """
        Kubernetes-style readiness probe.

        Returns:
            200 OK if ready, 503 if not ready
        """
        status = health_checker.get_status()
        if status == "unhealthy":
            return Response(
                content="Service unhealthy",
                status_code=503,
                media_type="text/plain",
            )
        return Response(
            content="Ready",
            status_code=200,
            media_type="text/plain",
        )

    @app.get("/")
    async def root() -> dict[str, Any]:
        """Root endpoint with API info."""
        return {
            "service": "FTE-Agent Health",
            "version": "1.0.0",
            "endpoints": "/health, /metrics, /ready",
        }

    return app


# For standalone execution
if __name__ == "__main__":
    import uvicorn

    app = create_health_app()
    uvicorn.run(app, host="127.0.0.1", port=8000)
