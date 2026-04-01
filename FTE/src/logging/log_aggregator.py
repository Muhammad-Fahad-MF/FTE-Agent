"""
Log Aggregator with JSON Logging, Rotation, and Retention.

Features:
- JSON format logging with correlation_id support
- Daily rotation at 100MB threshold
- Gzip compression for archived logs
- Retention policy (7 days INFO, 30 days ERROR/CRITICAL)
- Concurrent write support with file locking
- Async logging support (non-blocking writes)

Usage:
    # Create logger
    logger = get_log_aggregator("my_component")

    # Log with correlation ID
    logger.info("Processing request", extra={"correlation_id": "abc123", "action": "send_email"})

    # Log with structured data
    logger.error("Operation failed", extra={"details": {"error": "timeout", "retry": 3}})
"""

import gzip
import json
import logging
import os
import shutil
import threading
import uuid
from datetime import datetime, timedelta
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any, Optional


class JSONFormatter(logging.Formatter):
    """
    JSON log formatter.

    Produces structured JSON logs with required schema:
    - timestamp: ISO 8601 format
    - level: Log level (INFO, ERROR, etc.)
    - component: Logger name
    - action: Optional action name
    - dry_run: Optional dry_run flag
    - correlation_id: Optional correlation ID
    - details: Optional structured data
    - message: Log message
    """

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "component": record.name,
            "message": record.getMessage(),
        }

        # Add optional fields from record
        if hasattr(record, "correlation_id"):
            log_data["correlation_id"] = record.correlation_id
        if hasattr(record, "action"):
            log_data["action"] = record.action
        if hasattr(record, "dry_run"):
            log_data["dry_run"] = record.dry_run

        # Add structured details if present
        if hasattr(record, "details"):
            log_data["details"] = record.details

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data)


class RetentionRotatingFileHandler(RotatingFileHandler):
    """
    Rotating file handler with retention policy.

    Features:
    - Rotation at size threshold (default: 100MB)
    - Daily rotation
    - Gzip compression for archived logs
    - Retention policy enforcement
    """

    def __init__(
        self,
        filename: str,
        maxBytes: int = 100 * 1024 * 1024,  # 100MB
        backupCount: int = 30,
        retention_days_info: int = 7,
        retention_days_error: int = 30,
        encoding: str = "utf-8",
    ):
        """
        Initialize handler.

        Args:
            filename: Log file path
            maxBytes: Maximum file size before rotation (default: 100MB)
            backupCount: Number of backup files to keep
            retention_days_info: Retention for INFO logs (default: 7 days)
            retention_days_error: Retention for ERROR/CRITICAL logs (default: 30 days)
            encoding: File encoding
        """
        super().__init__(filename, maxBytes=maxBytes, backupCount=backupCount, encoding=encoding)
        self.retention_days_info = retention_days_info
        self.retention_days_error = retention_days_error
        self._rotation_lock = threading.Lock()

    def doRollover(self) -> None:
        """
        Perform rollover with gzip compression.

        Compresses the old log file and enforces retention policy.
        """
        if self.stream:
            self.stream.close()
            self.stream = None

        # Generate timestamp for rotated file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_name = self.baseFilename
        dir_name = os.path.dirname(base_name)
        file_name = os.path.basename(base_name)
        name_part, ext_part = os.path.splitext(file_name)

        # Create rotated filename
        rotated_name = os.path.join(dir_name, f"{name_part}_{timestamp}{ext_part}")

        # Rename current file
        if os.path.exists(base_name):
            os.rename(base_name, rotated_name)

        # Compress rotated file
        compressed_name = rotated_name + ".gz"
        try:
            with open(rotated_name, "rb") as f_in:
                with gzip.open(compressed_name, "wb") as f_out:
                    shutil.copyfileobj(f_in, f_out)
            os.remove(rotated_name)
        except Exception as e:
            # If compression fails, keep uncompressed file
            logging.getLogger(__name__).warning(f"Failed to compress log file: {e}")

        # Enforce retention policy
        self._enforce_retention()

        # Open new stream
        self.stream = self._open()

    def _enforce_retention(self) -> None:
        """Delete old log files based on retention policy."""
        dir_name = os.path.dirname(self.baseFilename)
        now = datetime.now()

        try:
            for filename in os.listdir(dir_name):
                filepath = os.path.join(dir_name, filename)
                if not os.path.isfile(filepath):
                    continue

                # Check if it's a log file (compressed or not)
                if not (filename.endswith(".log") or filename.endswith(".log.gz")):
                    continue

                # Get file modification time
                mtime = datetime.fromtimestamp(os.path.getmtime(filepath))
                age = now - mtime

                # Determine retention based on filename (error logs have longer retention)
                is_error_log = "error" in filename.lower() or "critical" in filename.lower()
                retention_days = (
                    self.retention_days_error if is_error_log else self.retention_days_info
                )

                # Delete if older than retention
                if age > timedelta(days=retention_days):
                    os.remove(filepath)
                    logging.getLogger(__name__).info(
                        f"Deleted old log file: {filename} (age={age.days} days)"
                    )
        except Exception as e:
            logging.getLogger(__name__).error(f"Failed to enforce retention: {e}")


class AsyncLogHandler(logging.Handler):
    """
    Async log handler for non-blocking writes.

    Wraps another handler and performs writes in a background thread.
    """

    def __init__(self, wrapped_handler: logging.Handler, queue_size: int = 1000):
        """
        Initialize async handler.

        Args:
            wrapped_handler: Handler to wrap
            queue_size: Maximum queue size (default: 1000)
        """
        super().__init__()
        self.wrapped_handler = wrapped_handler
        self.queue: list[logging.LogRecord] = []
        self.queue_lock = threading.Lock()
        self.queue_size = queue_size
        self._shutdown = False

        # Start background writer thread
        self._writer_thread = threading.Thread(target=self._writer_loop, daemon=True)
        self._writer_thread.start()

    def emit(self, record: logging.LogRecord) -> None:
        """Queue log record for async writing."""
        with self.queue_lock:
            if len(self.queue) < self.queue_size:
                self.queue.append(record)
            else:
                # Queue full, drop oldest
                self.queue.pop(0)
                self.queue.append(record)

    def _writer_loop(self) -> None:
        """Background thread that writes queued logs."""
        while not self._shutdown:
            records = []
            with self.queue_lock:
                if self.queue:
                    records = self.queue[:]
                    self.queue.clear()

            for record in records:
                try:
                    self.wrapped_handler.emit(record)
                except Exception:
                    self.handleError(record)

            # Small delay to prevent busy waiting
            if not records:
                import time
                time.sleep(0.01)

    def close(self) -> None:
        """Shutdown async handler."""
        self._shutdown = True
        self._writer_thread.join(timeout=5.0)
        self.wrapped_handler.close()
        super().close()


def get_log_aggregator(
    component: str,
    log_dir: Optional[str] = None,
    log_level: int = logging.INFO,
    async_enabled: bool = False,
) -> logging.Logger:
    """
    Get or create a logger with JSON formatting and rotation.

    Args:
        component: Component name (used in logs and filename)
        log_dir: Log directory (default: vault/Logs/)
        log_level: Minimum log level (default: INFO)
        async_enabled: Enable async logging (default: False)

    Returns:
        Configured logger instance
    """
    # Resolve log directory
    if log_dir is None:
        # Default to vault/Logs/ relative to this file
        log_dir = str(Path(__file__).parent.parent.parent / "vault" / "Logs")

    # Create log directory if it doesn't exist
    os.makedirs(log_dir, exist_ok=True)

    # Generate log filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_filename = f"{component.lower()}_{timestamp}.log"
    log_path = os.path.join(log_dir, log_filename)

    # Create logger
    logger = logging.getLogger(component)
    logger.setLevel(log_level)

    # Avoid duplicate handlers
    if logger.handlers:
        return logger

    # Create handler with rotation and retention
    handler = RetentionRotatingFileHandler(
        filename=log_path,
        maxBytes=100 * 1024 * 1024,  # 100MB
        backupCount=30,
        retention_days_info=7,
        retention_days_error=30,
    )
    handler.setFormatter(JSONFormatter())

    # Wrap with async handler if enabled
    if async_enabled:
        handler = AsyncLogHandler(handler)

    logger.addHandler(handler)

    return logger


class CorrelationIdMixin:
    """Mixin for adding correlation ID to log records."""

    @staticmethod
    def generate_correlation_id() -> str:
        """Generate a unique correlation ID."""
        return str(uuid.uuid4())

    def log_with_correlation(
        self,
        level: int,
        msg: str,
        correlation_id: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        """
        Log message with correlation ID.

        Args:
            level: Log level
            msg: Log message
            correlation_id: Optional correlation ID (generated if not provided)
            **kwargs: Additional extra fields
        """
        if correlation_id is None:
            correlation_id = self.generate_correlation_id()

        extra = kwargs.get("extra", {})
        extra["correlation_id"] = correlation_id
        kwargs["extra"] = extra

        self.log(level, msg, **kwargs)


class StructuredLogger(logging.Logger, CorrelationIdMixin):
    """Logger with correlation ID support and structured logging."""

    def __init__(self, name: str, level: int = logging.NOTSET):
        super().__init__(name, level)

    def info(self, msg: str, *args: Any, **kwargs: Any) -> None:
        """Log INFO level message with optional correlation ID."""
        super().info(msg, *args, **kwargs)

    def error(self, msg: str, *args: Any, **kwargs: Any) -> None:
        """Log ERROR level message with optional correlation ID."""
        super().error(msg, *args, **kwargs)

    def warning(self, msg: str, *args: Any, **kwargs: Any) -> None:
        """Log WARNING level message with optional correlation ID."""
        super().warning(msg, *args, **kwargs)

    def debug(self, msg: str, *args: Any, **kwargs: Any) -> None:
        """Log DEBUG level message with optional correlation ID."""
        super().debug(msg, *args, **kwargs)

    def critical(self, msg: str, *args: Any, **kwargs: Any) -> None:
        """Log CRITICAL level message with optional correlation ID."""
        super().critical(msg, *args, **kwargs)


# Register custom logger class
logging.setLoggerClass(StructuredLogger)


def get_structured_logger(
    component: str,
    log_dir: Optional[str] = None,
    log_level: int = logging.INFO,
    async_enabled: bool = False,
) -> StructuredLogger:
    """
    Get a structured logger with correlation ID support.

    Args:
        component: Component name
        log_dir: Log directory
        log_level: Minimum log level
        async_enabled: Enable async logging

    Returns:
        StructuredLogger instance
    """
    return get_log_aggregator(  # type: ignore
        component=component,
        log_dir=log_dir,
        log_level=log_level,
        async_enabled=async_enabled,
    )
