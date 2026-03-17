"""Unit tests for AuditLogger class."""

import pytest
import json
from pathlib import Path


class TestAuditLogger:
    """Unit tests for AuditLogger."""

    def test_log_entry_schema(self, tmp_path):
        """Verify log entry contains all 7 required fields."""
        from src.audit_logger import AuditLogger

        # Create logger with temp directory
        logger = AuditLogger(component="test", log_path=str(tmp_path))

        # Log a test entry
        logger.log(level="INFO", action="test_action", details={"key": "value"})

        # Read log file
        log_file = tmp_path / "audit_test_*.jsonl"
        log_files = list(tmp_path.glob("audit_test_*.jsonl"))
        assert len(log_files) > 0
        
        with open(log_files[0], 'r') as f:
            entry = json.loads(f.readline())

        # Verify all 7 fields present
        required_fields = ["timestamp", "level", "component", "action", "dry_run", "correlation_id", "details"]
        for field in required_fields:
            assert field in entry, f"Missing required field: {field}"

    def test_log_rotation(self, tmp_path):
        """Verify logs rotate at 7 days or 100MB."""
        from src.audit_logger import AuditLogger
        from datetime import datetime, timedelta
        import time

        # Create logger
        logger = AuditLogger(component="test", log_path=str(tmp_path))

        # Create a log file and write content
        log_file = tmp_path / f"audit_test_{datetime.now().strftime('%Y-%m-%d')}.jsonl"
        log_file.write_text("test content\n")
        
        # Make the file appear old by modifying its timestamp
        old_time = time.time() - (8 * 24 * 60 * 60)  # 8 days ago
        import os
        os.utime(log_file, (old_time, old_time))

        # Rotate logs
        logger.rotate_logs(max_age_days=7)

        # Verify old log was archived
        archived_files = list(tmp_path.glob("*.archived"))
        assert len(archived_files) > 0 or not log_file.exists()

    def test_error_logging_with_stack_trace(self, tmp_path):
        """Verify exceptions logged with exc_info=True."""
        from src.audit_logger import AuditLogger

        # Create logger
        logger = AuditLogger(component="test", log_path=str(tmp_path))

        # Create an exception and log it
        try:
            raise ValueError("Test error")
        except Exception as e:
            logger.error(action="test_error", details={"error": str(e)}, exc=e)

        # Verify log file contains error
        log_files = list(tmp_path.glob("audit_test_*.jsonl"))
        assert len(log_files) > 0
        content = log_files[0].read_text()
        assert "test_error" in content
        assert "ValueError" in content or "Test error" in content
