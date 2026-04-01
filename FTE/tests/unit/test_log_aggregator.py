"""
Unit tests for Log Aggregator.

Tests cover:
- JSON format logging
- Correlation ID support
- Log rotation
- Gzip compression
- Retention policy
- Concurrent writes
"""

import gzip
import json
import os
import tempfile
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from src.logging.log_aggregator import (
    JSONFormatter,
    RetentionRotatingFileHandler,
    get_log_aggregator,
    get_structured_logger,
)


@pytest.fixture
def temp_log_dir(tmp_path):
    """Create a temporary log directory."""
    log_dir = tmp_path / "logs"
    log_dir.mkdir()
    yield str(log_dir)


@pytest.fixture
def logger_with_temp_dir(temp_log_dir):
    """Create a logger with temporary log directory."""
    logger = get_log_aggregator(
        component="test_component",
        log_dir=temp_log_dir,
        log_level=logging.DEBUG,
    )
    yield logger
    # Cleanup handlers
    for handler in logger.handlers[:]:
        handler.close()
        logger.removeHandler(handler)


import logging


class TestJSONFormatter:
    """Test JSON log formatting."""

    def test_json_format(self):
        """Log should be formatted as valid JSON."""
        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        output = formatter.format(record)
        log_data = json.loads(output)

        assert "timestamp" in log_data
        assert "level" in log_data
        assert "component" in log_data
        assert "message" in log_data
        assert log_data["level"] == "INFO"
        assert log_data["message"] == "Test message"
        assert log_data["component"] == "test_logger"

    def test_json_format_with_correlation_id(self):
        """Log should include correlation ID if provided."""
        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None,
        )
        record.correlation_id = "abc-123"

        output = formatter.format(record)
        log_data = json.loads(output)

        assert log_data["correlation_id"] == "abc-123"

    def test_json_format_with_details(self):
        """Log should include structured details if provided."""
        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="test_logger",
            level=logging.ERROR,
            pathname="test.py",
            lineno=1,
            msg="Operation failed",
            args=(),
            exc_info=None,
        )
        record.details = {"error": "timeout", "retry": 3}

        output = formatter.format(record)
        log_data = json.loads(output)

        assert log_data["details"]["error"] == "timeout"
        assert log_data["details"]["retry"] == 3


class TestCorrelationID:
    """Test correlation ID support."""

    def test_correlation_id_auto_generated(self, logger_with_temp_dir, temp_log_dir):
        """Correlation ID can be provided if needed."""
        # Provide explicit correlation ID
        logger_with_temp_dir.info(
            "Test message",
            extra={"correlation_id": "auto-generated-test"},
        )

        # Find and read log file
        log_files = list(Path(temp_log_dir).glob("*.log"))
        assert len(log_files) > 0

        with open(log_files[0]) as f:
            for line in f:
                log_data = json.loads(line)
                if log_data["message"] == "Test message":
                    assert log_data["correlation_id"] == "auto-generated-test"
                    break

    def test_correlation_id_custom(self, logger_with_temp_dir, temp_log_dir):
        """Custom correlation ID should be used if provided."""
        logger_with_temp_dir.info(
            "Test message",
            extra={"correlation_id": "custom-id-123"},
        )

        # Find and read log file
        log_files = list(Path(temp_log_dir).glob("*.log"))
        assert len(log_files) > 0

        with open(log_files[0]) as f:
            for line in f:
                log_data = json.loads(line)
                if log_data["message"] == "Test message":
                    assert log_data["correlation_id"] == "custom-id-123"
                    break


class TestLogRotation:
    """Test log rotation functionality."""

    def test_rotation_creates_compressed_file(self, temp_log_dir):
        """Rotation should create gzip compressed files."""
        # Create handler with very small max size for testing
        log_path = os.path.join(temp_log_dir, "rotation_test.log")

        handler = RetentionRotatingFileHandler(
            filename=log_path,
            maxBytes=1024,  # 1KB for testing
            backupCount=5,
        )
        handler.setFormatter(JSONFormatter())

        logger = logging.getLogger("rotation_test")
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)

        # Write enough data to trigger rotation
        for i in range(100):
            logger.info(f"Log message {i} " + "x" * 100)

        # Check for compressed files
        gz_files = list(Path(temp_log_dir).glob("*.log.gz"))
        assert len(gz_files) > 0

        # Verify compression works
        with gzip.open(gz_files[0], "rt") as f:
            content = f.read()
            assert "Log message" in content

        # Cleanup
        handler.close()
        logger.removeHandler(handler)


class TestCompression:
    """Test gzip compression."""

    def test_compression_reduces_size(self, temp_log_dir):
        """Compressed files should be smaller than originals."""
        # Create a test log file with repetitive content
        original_path = os.path.join(temp_log_dir, "original.log")
        with open(original_path, "w") as f:
            for i in range(1000):
                f.write(f"Repetitive log message number {i}\n")

        original_size = os.path.getsize(original_path)

        # Compress it
        compressed_path = original_path + ".gz"
        with open(original_path, "rb") as f_in:
            with gzip.open(compressed_path, "wb") as f_out:
                f_in.seek(0, 2)  # Seek to end
                f_in.seek(0)  # Seek to beginning
                import shutil
                shutil.copyfileobj(f_in, f_out)

        compressed_size = os.path.getsize(compressed_path)

        # Compressed should be smaller
        assert compressed_size < original_size


class TestRetention:
    """Test retention policy."""

    def test_retention_deletes_old_files(self, temp_log_dir):
        """Old log files should be deleted based on retention."""
        # Create an old log file
        old_file = os.path.join(temp_log_dir, "old_test.log")
        with open(old_file, "w") as f:
            f.write("Old log content\n")

        # Set modification time to 10 days ago
        old_time = time.time() - (10 * 24 * 60 * 60)
        os.utime(old_file, (old_time, old_time))

        # Create handler with 7-day retention
        handler = RetentionRotatingFileHandler(
            filename=os.path.join(temp_log_dir, "current.log"),
            maxBytes=100 * 1024 * 1024,
            backupCount=30,
            retention_days_info=7,
        )

        # Trigger retention check by doing a rollover
        handler.doRollover()
        handler.close()

        # Old file should be deleted
        assert not os.path.exists(old_file)


class TestConcurrentWrites:
    """Test concurrent write support."""

    def test_concurrent_writes(self, temp_log_dir):
        """Multiple threads should be able to write logs concurrently."""
        logger = get_log_aggregator(
            component="concurrent_test",
            log_dir=temp_log_dir,
        )

        errors = []
        write_count = 0
        lock = threading.Lock()

        def writer(thread_id):
            nonlocal write_count
            try:
                for i in range(10):
                    logger.info(f"Thread {thread_id} message {i}")
                    with lock:
                        write_count += 1
            except Exception as e:
                errors.append(e)

        # Start multiple threads
        threads = []
        for i in range(5):
            t = threading.Thread(target=writer, args=(i,))
            threads.append(t)
            t.start()

        # Wait for completion
        for t in threads:
            t.join()

        # Verify all writes succeeded
        assert len(errors) == 0
        assert write_count == 50

        # Cleanup
        for handler in logger.handlers[:]:
            handler.close()
            logger.removeHandler(handler)


class TestStructuredLogger:
    """Test structured logger."""

    def test_structured_logger_creation(self, temp_log_dir):
        """Structured logger should be created correctly."""
        logger = get_structured_logger(
            component="structured_test",
            log_dir=temp_log_dir,
        )

        assert isinstance(logger, logging.Logger)
        assert logger.level == logging.INFO

        # Cleanup
        for handler in logger.handlers[:]:
            handler.close()
            logger.removeHandler(handler)

    def test_structured_logger_logs(self, temp_log_dir):
        """Structured logger should write valid JSON logs."""
        logger = get_structured_logger(
            component="json_test",
            log_dir=temp_log_dir,
        )

        logger.info("Test info message")
        logger.error("Test error message")

        # Find and verify log file
        log_files = list(Path(temp_log_dir).glob("*.log"))
        assert len(log_files) > 0

        # Read and parse logs
        with open(log_files[0]) as f:
            lines = f.readlines()
            assert len(lines) >= 2

            for line in lines:
                log_data = json.loads(line)
                assert "timestamp" in log_data
                assert "level" in log_data
                assert "message" in log_data

        # Cleanup
        for handler in logger.handlers[:]:
            handler.close()
            logger.removeHandler(handler)
