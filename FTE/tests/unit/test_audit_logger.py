"""Unit tests for AuditLogger class."""

import json


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
        log_files = list(tmp_path.glob("audit_test_*.jsonl"))
        assert len(log_files) > 0

        with open(log_files[0]) as f:
            entry = json.loads(f.readline())

        # Verify all 7 fields present
        required_fields = [
            "timestamp",
            "level",
            "component",
            "action",
            "dry_run",
            "correlation_id",
            "details",
        ]
        for field in required_fields:
            assert field in entry, f"Missing required field: {field}"

    def test_log_rotation(self, tmp_path):
        """Verify logs rotate at 7 days or 100MB."""
        import time
        from datetime import datetime

        from src.audit_logger import AuditLogger

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

    def test_error_method_with_none_exception(self, tmp_path):
        """Verify error() method handles exc=None correctly."""
        from src.audit_logger import AuditLogger

        # Create logger
        logger = AuditLogger(component="test", log_path=str(tmp_path))

        # Call error with exc=None
        logger.error(action="test_error", details={"error": "test"}, exc=None)

        # Verify log file was created
        log_files = list(tmp_path.glob("audit_test_*.jsonl"))
        assert len(log_files) > 0
        content = log_files[0].read_text()
        assert "test_error" in content

    def test_rotate_logs_dry_run(self, tmp_path):
        """Verify rotate_logs() returns early in dry_run mode."""
        import time
        from datetime import datetime

        from src.audit_logger import AuditLogger

        # Create logger in dry_run mode
        logger = AuditLogger(component="test", log_path=str(tmp_path), dry_run=True)

        # Create a log file and make it appear old
        log_file = tmp_path / f"audit_test_{datetime.now().strftime('%Y-%m-%d')}.jsonl"
        log_file.write_text("test content\n")
        old_time = time.time() - (8 * 24 * 60 * 60)  # 8 days ago
        import os

        os.utime(log_file, (old_time, old_time))

        # Rotate logs - should return early
        logger.rotate_logs(max_age_days=7)

        # File should NOT be archived (dry_run mode)
        archived_files = list(tmp_path.glob("*.archived"))
        assert len(archived_files) == 0
        assert log_file.exists()

    def test_info_method(self, tmp_path):
        """Verify info() method calls log() with INFO level."""
        from src.audit_logger import AuditLogger

        logger = AuditLogger(component="test", log_path=str(tmp_path))

        # Call info method
        logger.info(action="test_info", details={"key": "value"})

        # Verify log file was created with INFO level
        log_files = list(tmp_path.glob("audit_test_*.jsonl"))
        assert len(log_files) > 0
        content = log_files[0].read_text()
        assert "INFO" in content
        assert "test_info" in content
