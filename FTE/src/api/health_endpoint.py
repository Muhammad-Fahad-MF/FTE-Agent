"""
Health Endpoint API.

FastAPI-based health monitoring endpoints:
- GET /health - Component health status
- GET /metrics - Prometheus-format metrics
- GET /ready - Readiness check (503 if deps unhealthy)

Features:
- Authentication token for /metrics (optional)
- Rate limiting (max 60 requests/minute)
- Component health aggregation
- Prometheus metrics export

Usage:
    import uvicorn
    from src.api.health_endpoint import create_app
    
    app = create_app()
    uvicorn.run(app, host="0.0.0.0", port=8000)
"""

import os
import time
from collections import defaultdict
from datetime import datetime
from typing import Any, Optional

from fastapi import FastAPI, HTTPException, Request, Response, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse
import psutil

from src.utils.graceful_degradation import (
    get_degradation_manager,
    GracefulDegradationManager,
    ComponentStatus,
)
from src.metrics.collector import get_metrics_collector


# Rate limiting storage
_rate_limit_window: dict[str, list[float]] = defaultdict(list)
_rate_limit_window_seconds = 60
_rate_limit_max_requests = 60


def check_rate_limit(client_ip: str) -> bool:
    """
    Check if client has exceeded rate limit.
    
    Args:
        client_ip: Client IP address
        
    Returns:
        True if request allowed, False if rate limited
    """
    current_time = time.time()
    
    # Clean old entries
    _rate_limit_window[client_ip] = [
        t for t in _rate_limit_window[client_ip]
        if current_time - t < _rate_limit_window_seconds
    ]
    
    # Check limit
    if len(_rate_limit_window[client_ip]) >= _rate_limit_max_requests:
        return False
    
    # Record request
    _rate_limit_window[client_ip].append(current_time)
    return True


def get_client_ip(request: Request) -> str:
    """Get client IP from request."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def create_app(
    metrics_auth_token: Optional[str] = None,
    enable_rate_limiting: bool = True,
) -> FastAPI:
    """
    Create FastAPI health endpoint app.
    
    Args:
        metrics_auth_token: Optional auth token for /metrics
        enable_rate_limiting: Enable rate limiting (default: True)
        
    Returns:
        FastAPI application
    """
    app = FastAPI(
        title="FTE Agent Health API",
        description="Health monitoring endpoints for FTE Agent",
        version="1.0.0",
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Store config in app state
    app.state.metrics_auth_token = metrics_auth_token or os.getenv("METRICS_AUTH_TOKEN")
    app.state.enable_rate_limiting = enable_rate_limiting
    app.state.degradation_manager = get_degradation_manager()
    
    @app.middleware("http")
    async def rate_limit_middleware(request: Request, call_next):
        """Apply rate limiting to all requests."""
        if not app.state.enable_rate_limiting:
            return await call_next(request)
        
        client_ip = get_client_ip(request)
        
        if not check_rate_limit(client_ip):
            return JSONResponse(
                status_code=429,
                content={
                    "error": "Rate limit exceeded",
                    "message": f"Max {_rate_limit_max_requests} requests per {_rate_limit_window_seconds}s",
                    "retry_after": _rate_limit_window_seconds,
                },
            )
        
        return await call_next(request)
    
    @app.get("/health", tags=["Health"])
    async def health_check() -> dict[str, Any]:
        """
        Get overall system health status.
        
        Returns health information for all monitored components.
        
        Response format:
        ```json
        {
            "status": "healthy|degraded|unhealthy",
            "timestamp": "2026-04-01T12:00:00",
            "components": {
                "watcher_gmail": {
                    "status": "healthy",
                    "last_check": "2026-04-01T12:00:00",
                    "error_count": 0,
                    "fallback_active": false
                }
            },
            "system": {
                "cpu_percent": 45.2,
                "memory_percent": 62.1,
                "disk_percent": 55.0
            }
        }
        ```
        """
        manager = app.state.degradation_manager
        
        # Get component health
        components = manager.get_component_health()
        
        # Get overall status
        overall_status = manager.get_overall_status()
        
        # Get system metrics
        system_info = {
            "cpu_percent": psutil.cpu_percent(interval=0.1),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_percent": psutil.disk_usage("/").percent if os.name != "nt" else psutil.disk_usage("C:\\").percent,
        }
        
        return {
            "status": overall_status,
            "timestamp": datetime.now().isoformat(),
            "components": components,
            "system": system_info,
        }
    
    @app.get("/metrics", tags=["Metrics"])
    async def metrics_endpoint(
        authorization: Optional[str] = Header(None),
        request: Request = None,
    ) -> Response:
        """
        Get Prometheus-format metrics.
        
        Optional authentication via Authorization header:
        Authorization: Bearer <token>
        
        Returns metrics in Prometheus exposition format:
        ```
        # HELP fte_component_health Component health status
        # TYPE fte_component_health gauge
        fte_component_health{component="watcher_gmail"} 1.0
        fte_component_health{component="watcher_whatsapp"} 1.0
        
        # HELP fte_system_cpu_percent CPU usage percentage
        # TYPE fte_system_cpu_percent gauge
        fte_system_cpu_percent 45.2
        
        # HELP fte_error_count_total Total error count
        # TYPE fte_error_count_total counter
        fte_error_count_total{component="watcher_gmail"} 5
        ```
        """
        # Check authentication if configured
        if app.state.metrics_auth_token:
            expected = f"Bearer {app.state.metrics_auth_token}"
            if authorization != expected:
                raise HTTPException(
                    status_code=401,
                    detail="Invalid or missing authentication token",
                )
        
        manager = app.state.degradation_manager
        
        # Get metrics collector (may fail in test environments)
        try:
            metrics_collector = get_metrics_collector()
        except Exception:
            metrics_collector = None
        
        # Build Prometheus format metrics
        lines = []
        
        # Component health metrics
        lines.append("# HELP fte_component_health Component health status (1=healthy, 0.5=degraded, 0=unhealthy)")
        lines.append("# TYPE fte_component_health gauge")
        
        components = manager.get_component_health()
        status_map = {
            "healthy": 1.0,
            "degraded": 0.5,
            "unhealthy": 0.0,
            "unknown": 0.0,
        }
        
        for name, health in components.items():
            status = health.get("status", "unknown")
            value = status_map.get(status, 0.0)
            lines.append(f'fte_component_health{{component="{name}"}} {value}')
        
        # Error count metrics
        lines.append("")
        lines.append("# HELP fte_error_count_total Total error count per component")
        lines.append("# TYPE fte_error_count_total counter")
        
        for name, health in components.items():
            error_count = health.get("error_count", 0)
            lines.append(f'fte_error_count_total{{component="{name}"}} {error_count}')
        
        # System metrics
        lines.append("")
        lines.append("# HELP fte_system_cpu_percent CPU usage percentage")
        lines.append("# TYPE fte_system_cpu_percent gauge")
        lines.append(f"fte_system_cpu_percent {psutil.cpu_percent(interval=0.1)}")
        
        lines.append("")
        lines.append("# HELP fte_system_memory_percent Memory usage percentage")
        lines.append("# TYPE fte_system_memory_percent gauge")
        lines.append(f"fte_system_memory_percent {psutil.virtual_memory().percent}")
        
        # Collector metrics
        try:
            collector_metrics = metrics_collector.get_prometheus_metrics()
            if collector_metrics:
                lines.append("")
                lines.append(collector_metrics)
        except Exception:
            pass  # Skip collector metrics if unavailable
        
        # Fallback active metrics
        lines.append("")
        lines.append("# HELP fte_fallback_active Fallback mechanism active (1=active, 0=inactive)")
        lines.append("# TYPE fte_fallback_active gauge")
        
        for name, health in components.items():
            fallback = 1.0 if health.get("fallback_active", False) else 0.0
            lines.append(f'fte_fallback_active{{component="{name}"}} {fallback}')
        
        content = "\n".join(lines) + "\n"
        
        return PlainTextResponse(
            content=content,
            media_type="text/plain; version=0.0.4; charset=utf-8",
        )
    
    @app.get("/ready", tags=["Health"])
    async def readiness_check() -> Response:
        """
        Check if service is ready to serve traffic.
        
        Returns 200 if all critical dependencies are healthy.
        Returns 503 if any critical dependency is unhealthy.
        
        Critical components:
        - sqlite_database
        - file_system
        - watcher_gmail (if configured)
        - watcher_whatsapp (if configured)
        - watcher_filesystem
        
        Response format (200):
        ```json
        {
            "status": "ready",
            "timestamp": "2026-04-01T12:00:00",
            "critical_components": {
                "sqlite_database": "healthy",
                "file_system": "healthy"
            }
        }
        ```
        
        Response format (503):
        ```json
        {
            "status": "not_ready",
            "timestamp": "2026-04-01T12:00:00",
            "unhealthy_components": ["sqlite_database"],
            "reason": "Critical dependency unhealthy"
        }
        ```
        """
        manager = app.state.degradation_manager
        components = manager.get_component_health()
        
        # Critical components for readiness
        critical_components = [
            "sqlite_database",
            "file_system",
            "watcher_filesystem",
        ]
        
        # Check critical components
        unhealthy = []
        critical_status = {}
        
        for name in critical_components:
            if name in components:
                status = components[name].get("status", "unknown")
                critical_status[name] = status
                if status in ["unhealthy", "unknown"]:
                    unhealthy.append(name)
        
        if unhealthy:
            return JSONResponse(
                status_code=503,
                content={
                    "status": "not_ready",
                    "timestamp": datetime.now().isoformat(),
                    "unhealthy_components": unhealthy,
                    "reason": "Critical dependency unhealthy",
                    "details": {name: critical_status.get(name, "not_checked") for name in unhealthy},
                },
            )
        
        return JSONResponse(
            status_code=200,
            content={
                "status": "ready",
                "timestamp": datetime.now().isoformat(),
                "critical_components": critical_status,
            },
        )
    
    @app.get("/live", tags=["Health"])
    async def liveness_check() -> dict[str, str]:
        """
        Simple liveness check.
        
        Returns 200 if service is running.
        Used by Kubernetes for pod health checks.
        """
        return {"status": "alive", "timestamp": datetime.now().isoformat()}
    
    @app.post("/health/reset", tags=["Health"])
    async def reset_health_status(component: Optional[str] = None) -> dict[str, Any]:
        """
        Reset health status for component(s).
        
        Args:
            component: Optional specific component to reset
            
        Returns:
            Status of reset operation
        """
        manager = app.state.degradation_manager
        
        if component:
            manager.set_component_status(component, ComponentStatus.UNKNOWN)
            return {"status": "reset", "component": component}
        
        # Reset all components
        for name in manager._components.keys():
            manager.set_component_status(name, ComponentStatus.UNKNOWN)
        
        return {"status": "reset", "components": "all"}
    
    @app.get("/health/config", tags=["Health"])
    async def get_health_config() -> dict[str, Any]:
        """Get health endpoint configuration."""
        return {
            "metrics_auth_enabled": app.state.metrics_auth_token is not None,
            "rate_limiting_enabled": app.state.enable_rate_limiting,
            "rate_limit_max_requests": _rate_limit_max_requests,
            "rate_limit_window_seconds": _rate_limit_window_seconds,
        }
    
    return app


# Create default app instance
app = create_app()


if __name__ == "__main__":
    import uvicorn
    
    # Run health endpoint
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info",
    )
