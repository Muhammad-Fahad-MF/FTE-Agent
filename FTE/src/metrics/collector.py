"""
Metrics Collector with Prometheus + SQLite Persistence.

Implements histogram, counter, gauge, and timer metrics with dual storage:
- In-memory Prometheus client for real-time monitoring
- SQLite database for historical analysis and persistence

Usage:
    # Create collector
    collector = MetricsCollector()

    # Record histogram
    collector.record_histogram("api_latency", 0.5)

    # Use timer context manager
    with collector.timer("operation_duration"):
        do_something()

    # Increment counter
    collector.increment_counter("requests_total")

    # Set gauge
    collector.set_gauge("memory_usage", 1024)

    # Export Prometheus format
    metrics = collector.export_prometheus()
"""

import logging
import sqlite3
import threading
import time
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge, Histogram, generate_latest

logger = logging.getLogger(__name__)

# Default metric buckets for histograms (in seconds)
DEFAULT_BUCKETS = (0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0)


class MetricsCollector:
    """
    Metrics collector with Prometheus client + SQLite persistence.

    Features:
    - Histogram, Counter, Gauge, Timer metric types
    - SQLite persistence for historical data
    - Prometheus format export
    - Thread-safe operations
    - Connection pooling
    """

    def __init__(
        self,
        db_path: Optional[str] = None,
        max_connections: int = 5,
    ):
        """
        Initialize metrics collector.

        Args:
            db_path: Path to SQLite database (default: data/metrics.db)
            max_connections: Maximum database connections in pool (default: 5)
        """
        self.db_path = db_path or str(Path(__file__).parent.parent / "data" / "metrics.db")
        self.max_connections = max_connections

        self._lock = threading.Lock()
        self._connection_pool: list[sqlite3.Connection] = []
        self._pool_lock = threading.Lock()

        # Prometheus metrics registry
        self._histograms: dict[str, Histogram] = {}
        self._counters: dict[str, Counter] = {}
        self._gauges: dict[str, Gauge] = {}

        # Initialize database
        self._init_db()

        logger.debug(f"MetricsCollector initialized (db={self.db_path})")

    def _init_db(self) -> None:
        """Initialize SQLite database schema."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    type TEXT NOT NULL,
                    value REAL NOT NULL,
                    tags TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
            )
            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_metrics_name ON metrics(name)
            """
            )
            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_metrics_timestamp ON metrics(timestamp)
            """
            )
            conn.commit()
        except sqlite3.Error as e:
            logger.error(f"Failed to initialize metrics database: {e}")
            raise
        finally:
            self._return_connection(conn)

    def _get_connection(self) -> sqlite3.Connection:
        """Get connection from pool."""
        with self._pool_lock:
            if self._connection_pool:
                return self._connection_pool.pop()

            # Create new connection if under limit
            if len(self._connection_pool) < self.max_connections:
                return sqlite3.connect(self.db_path, check_same_thread=False)

            # Pool exhausted, create new connection anyway (with warning)
            logger.warning("Connection pool exhausted, creating new connection")
            return sqlite3.connect(self.db_path, check_same_thread=False)

    def _return_connection(self, conn: sqlite3.Connection) -> None:
        """Return connection to pool."""
        with self._pool_lock:
            if len(self._connection_pool) < self.max_connections:
                self._connection_pool.append(conn)
            else:
                conn.close()

    def _get_or_create_histogram(self, name: str, buckets: Optional[tuple[float, ...]] = None) -> Histogram:
        """Get or create Prometheus histogram."""
        if name not in self._histograms:
            self._histograms[name] = Histogram(
                name,
                f"{name} histogram",
                buckets=buckets or DEFAULT_BUCKETS,
            )
        return self._histograms[name]

    def _get_or_create_counter(self, name: str) -> Counter:
        """Get or create Prometheus counter."""
        if name not in self._counters:
            self._counters[name] = Counter(name, f"{name} counter")
        return self._counters[name]

    def _get_or_create_gauge(self, name: str) -> Gauge:
        """Get or create Prometheus gauge."""
        if name not in self._gauges:
            self._gauges[name] = Gauge(name, f"{name} gauge")
        return self._gauges[name]

    def record_histogram(
        self,
        name: str,
        value: float,
        buckets: Optional[tuple[float, ...]] = None,
        tags: Optional[dict[str, str]] = None,
    ) -> None:
        """
        Record a histogram metric.

        Args:
            name: Metric name
            value: Value to record
            buckets: Custom bucket configuration
            tags: Optional tags (stored in SQLite)
        """
        # Record to Prometheus
        histogram = self._get_or_create_histogram(name, buckets)
        histogram.observe(value)

        # Persist to SQLite
        self._persist_metric(name, "histogram", value, tags)

    def increment_counter(
        self,
        name: str,
        value: float = 1.0,
        tags: Optional[dict[str, str]] = None,
    ) -> None:
        """
        Increment a counter metric.

        Args:
            name: Metric name
            value: Value to increment by (default: 1.0)
            tags: Optional tags
        """
        # Record to Prometheus
        counter = self._get_or_create_counter(name)
        counter.inc(value)

        # Persist to SQLite
        self._persist_metric(name, "counter", value, tags)

    def set_gauge(
        self,
        name: str,
        value: float,
        tags: Optional[dict[str, str]] = None,
    ) -> None:
        """
        Set a gauge metric.

        Args:
            name: Metric name
            value: Value to set
            tags: Optional tags
        """
        # Record to Prometheus
        gauge = self._get_or_create_gauge(name)
        gauge.set(value)

        # Persist to SQLite
        self._persist_metric(name, "gauge", value, tags)

    def inc_gauge(
        self,
        name: str,
        value: float = 1.0,
        tags: Optional[dict[str, str]] = None,
    ) -> None:
        """
        Increment a gauge metric.

        Args:
            name: Metric name
            value: Value to increment by (default: 1.0)
            tags: Optional tags
        """
        gauge = self._get_or_create_gauge(name)
        gauge.inc(value)

        # Persist to SQLite
        self._persist_metric(name, "gauge", value, tags)

    def dec_gauge(
        self,
        name: str,
        value: float = 1.0,
        tags: Optional[dict[str, str]] = None,
    ) -> None:
        """
        Decrement a gauge metric.

        Args:
            name: Metric name
            value: Value to decrement by (default: 1.0)
            tags: Optional tags
        """
        gauge = self._get_or_create_gauge(name)
        gauge.dec(value)

        # Persist to SQLite
        self._persist_metric(name, "gauge", -value, tags)

    @contextmanager
    def timer(
        self,
        name: str,
        buckets: Optional[tuple[float, ...]] = None,
        tags: Optional[dict[str, str]] = None,
    ):
        """
        Context manager for timing operations.

        Usage:
            with collector.timer("operation_duration"):
                do_something()

        Args:
            name: Metric name
            buckets: Custom histogram buckets
            tags: Optional tags
        """
        start_time = time.perf_counter()
        try:
            yield
        finally:
            duration = time.perf_counter() - start_time
            self.record_histogram(name, duration, buckets, tags)

    def _persist_metric(
        self,
        name: str,
        metric_type: str,
        value: float,
        tags: Optional[dict[str, str]] = None,
    ) -> None:
        """Persist metric to SQLite."""
        import json

        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO metrics (name, type, value, tags, timestamp)
                VALUES (?, ?, ?, ?, ?)
            """,
                (name, metric_type, value, json.dumps(tags or {}), datetime.now()),
            )
            conn.commit()
        except sqlite3.Error as e:
            logger.debug(f"Failed to persist metric '{name}': {e}")
        finally:
            self._return_connection(conn)

    def export_prometheus(self) -> str:
        """
        Export metrics in Prometheus format.

        Returns:
            Prometheus-formatted metrics string
        """
        try:
            return generate_latest().decode("utf-8")
        except Exception as e:
            logger.error(f"Failed to export Prometheus metrics: {e}")
            return ""

    def get_prometheus_content_type(self) -> str:
        """Get Prometheus content type for HTTP responses."""
        return CONTENT_TYPE_LATEST

    def query_metrics(
        self,
        name: Optional[str] = None,
        metric_type: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 1000,
    ) -> list[dict[str, Any]]:
        """
        Query metrics from SQLite.

        Args:
            name: Filter by metric name
            metric_type: Filter by type (histogram, counter, gauge)
            start_time: Filter by start time
            end_time: Filter by end time
            limit: Maximum results to return

        Returns:
            List of metric records
        """
        import json

        conn = self._get_connection()
        try:
            cursor = conn.cursor()

            query = "SELECT * FROM metrics WHERE 1=1"
            params: list[Any] = []

            if name:
                query += " AND name = ?"
                params.append(name)

            if metric_type:
                query += " AND type = ?"
                params.append(metric_type)

            if start_time:
                query += " AND timestamp >= ?"
                params.append(start_time)

            if end_time:
                query += " AND timestamp <= ?"
                params.append(end_time)

            query += " ORDER BY timestamp DESC LIMIT ?"
            params.append(limit)

            cursor.execute(query, params)
            rows = cursor.fetchall()

            results = []
            for row in rows:
                results.append(
                    {
                        "id": row[0],
                        "name": row[1],
                        "type": row[2],
                        "value": row[3],
                        "tags": json.loads(row[4]) if row[4] else {},
                        "timestamp": row[5],
                    }
                )

            return results
        except sqlite3.Error as e:
            logger.error(f"Failed to query metrics: {e}")
            return []
        finally:
            self._return_connection(conn)

    def cleanup_old_metrics(
        self,
        retention_days: int = 7,
    ) -> int:
        """
        Delete old metrics based on retention policy.

        Args:
            retention_days: Number of days to retain (default: 7)

        Returns:
            Number of records deleted
        """
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                DELETE FROM metrics
                WHERE timestamp < datetime('now', ?)
            """,
                (f"-{retention_days} days",),
            )
            conn.commit()
            deleted = cursor.rowcount
            logger.info(f"Cleaned up {deleted} old metrics (retention={retention_days} days)")
            return deleted
        except sqlite3.Error as e:
            logger.error(f"Failed to cleanup old metrics: {e}")
            return 0
        finally:
            self._return_connection(conn)


# Global default collector instance
_default_collector: Optional[MetricsCollector] = None
_default_lock = threading.Lock()


def get_metrics_collector(db_path: Optional[str] = None) -> MetricsCollector:
    """
    Get or create the default metrics collector.

    Args:
        db_path: Optional database path

    Returns:
        MetricsCollector instance
    """
    global _default_collector

    with _default_lock:
        if _default_collector is None:
            _default_collector = MetricsCollector(db_path=db_path)
        return _default_collector


def record_histogram(name: str, value: float, **kwargs: Any) -> None:
    """Record histogram metric using default collector."""
    get_metrics_collector().record_histogram(name, value, **kwargs)


def increment_counter(name: str, value: float = 1.0, **kwargs: Any) -> None:
    """Increment counter metric using default collector."""
    get_metrics_collector().increment_counter(name, value, **kwargs)


def set_gauge(name: str, value: float, **kwargs: Any) -> None:
    """Set gauge metric using default collector."""
    get_metrics_collector().set_gauge(name, value, **kwargs)


@contextmanager
def timer(name: str, **kwargs: Any):
    """Time operation using default collector."""
    with get_metrics_collector().timer(name, **kwargs):
        yield
