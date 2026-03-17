"""AuditLogger for structured JSON logging with rotation."""

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional


class AuditLogger:
    """Structured audit logger with JSONL output and log rotation.
    
    Logs all operations to vault/Logs/audit_YYYY-MM-DD.jsonl with
    required schema fields for observability and compliance.
    
    Attributes:
        component: Name of the component using this logger.
        log_path: Directory path for log files.
        dry_run: If True, log actions without writing files.
    """

    def __init__(self, component: str, log_path: str = "vault/Logs/", dry_run: bool = False) -> None:
        """Initialize the audit logger.
        
        Args:
            component: Name of the component (e.g., 'filesystem_watcher').
            log_path: Directory path for log files. Defaults to 'vault/Logs/'.
            dry_run: If True, log actions without writing files. Defaults to False.
        """
        self.component = component
        self.log_path = Path(log_path)
        self.dry_run = dry_run
        self._ensure_log_directory()

    def _ensure_log_directory(self) -> None:
        """Create log directory if it doesn't exist."""
        if not self.dry_run:
            self.log_path.mkdir(parents=True, exist_ok=True)

    def _get_log_file(self) -> Path:
        """Get the current log file path based on today's date."""
        date_str = datetime.now().strftime("%Y-%m-%d")
        return self.log_path / f"audit_{self.component}_{date_str}.jsonl"

    def log(
        self,
        level: str,
        action: str,
        details: dict,
        correlation_id: Optional[str] = None
    ) -> None:
        """Write a log entry to the JSONL file.
        
        Args:
            level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
            action: Action type (e.g., 'file_detected', 'action_created').
            details: Contextual data dictionary.
            correlation_id: Optional UUID to track requests across components.
        """
        if self.dry_run:
            return

        entry = {
            "timestamp": datetime.now().isoformat(),
            "level": level,
            "component": self.component,
            "action": action,
            "dry_run": self.dry_run,
            "correlation_id": correlation_id or str(uuid.uuid4()),
            "details": details
        }

        log_file = self._get_log_file()
        with open(log_file, 'a') as f:
            f.write(json.dumps(entry) + '\n')

    def info(self, action: str, details: dict) -> None:
        """Log an INFO level message.
        
        Args:
            action: Action type.
            details: Contextual data dictionary.
        """
        self.log(level="INFO", action=action, details=details)

    def error(
        self,
        action: str,
        details: dict,
        exc: Optional[Exception] = None
    ) -> None:
        """Log an ERROR level message with optional exception.
        
        Args:
            action: Action type.
            details: Contextual data dictionary.
            exc: Optional exception to include in log.
        """
        error_details = details.copy()
        if exc:
            error_details["exception_type"] = type(exc).__name__
            error_details["exception_message"] = str(exc)
        
        self.log(level="ERROR", action=action, details=error_details)

    def rotate_logs(self, max_age_days: int = 7, max_size_mb: int = 100) -> None:
        """Rotate log files older than max_age_days or larger than max_size_mb.
        
        Args:
            max_age_days: Maximum age in days before rotation. Defaults to 7.
            max_size_mb: Maximum file size in MB before rotation. Defaults to 100.
        """
        if self.dry_run:
            return

        from datetime import timedelta
        
        cutoff_date = datetime.now() - timedelta(days=max_age_days)
        max_size_bytes = max_size_mb * 1024 * 1024

        for log_file in self.log_path.glob("audit_*.jsonl"):
            should_archive = False
            
            # Check file age
            file_mtime = datetime.fromtimestamp(log_file.stat().st_mtime)
            if file_mtime < cutoff_date:
                should_archive = True
            
            # Check file size
            if log_file.stat().st_size > max_size_bytes:
                should_archive = True
            
            if should_archive:
                archived_path = log_file.with_suffix(".jsonl.archived")
                log_file.rename(archived_path)
