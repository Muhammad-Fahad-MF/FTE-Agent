"""
FTE-Agent Health Module
Purpose: Health endpoint, resource monitoring, and alerting for Cloud VM
Version: 1.0.0 (Platinum Tier)
"""

from .alerting import Alert, AlertManager
from .endpoint import HealthChecker, create_health_app
from .monitoring import MetricsCollector, ResourceMonitor

__all__ = [
    "create_health_app",
    "HealthChecker",
    "ResourceMonitor",
    "MetricsCollector",
    "AlertManager",
    "Alert",
]
