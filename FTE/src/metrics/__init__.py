"""Metrics collection for FTE-Agent."""

from .collector import (
    MetricsCollector,
    get_metrics_collector,
    increment_counter,
    record_histogram,
    set_gauge,
    timer,
)

__all__ = [
    "MetricsCollector",
    "get_metrics_collector",
    "increment_counter",
    "record_histogram",
    "set_gauge",
    "timer",
]
