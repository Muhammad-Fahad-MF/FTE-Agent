"""FTE-Agent Services.

This package contains core services for the FTE-Agent:
- Orchestrator: Main coordination service
- Dashboard: Real-time system health dashboard
- RetryHandler: Exponential backoff retry logic
- CircuitBreaker: Fault tolerance pattern
"""

from .orchestrator import Orchestrator

__all__ = ["Orchestrator"]
