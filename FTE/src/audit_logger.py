"""AuditLogger for structured JSON logging with rotation and 90-day retention.

This module implements comprehensive audit logging with:
- Complete 14-field JSON schema (Gold Tier compliant)
- Daily rotation at midnight
- 90-day retention policy
- File size cap at 100MB
- Query and export utilities
"""

import json
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any


class AuditLogger:
    """Structured audit logger with JSONL output and log rotation.

    Logs all operations to vault/Logs/YYYY-MM-DD.jsonl with
    required 14-field schema for Gold Tier compliance.

    Schema fields:
        - timestamp: ISO-8601 timestamp
        - level: DEBUG|INFO|WARNING|ERROR|CRITICAL
        - component: Component name (watcher, skill, mcp_server, etc.)
        - action: Action type (file_created, approval_requested, etc.)
        - dry_run: Boolean indicating dry-run mode
        - correlation_id: UUID for tracking across components
        - domain: personal|business
        - target: Resource being acted upon
        - parameters: Action-specific parameters dict
        - approval_status: auto|human|none
        - approved_by: User ID if human-approved
        - result: success|failure|pending
        - error: Error message if failed
        - details: Additional contextual data

    Attributes:
        component: Name of the component using this logger.
        log_path: Directory path for log files.
        dry_run: If True, log actions without writing files.
        retention_days: Number of days to retain logs (default: 90).
    """

    def __init__(
        self,
        component: str,
        log_path: str = "vault/Logs/",
        dry_run: bool = False,
        retention_days: int = 90,
    ) -> None:
        """Initialize the audit logger.

        Args:
            component: Name of the component (e.g., 'filesystem_watcher').
            log_path: Directory path for log files. Defaults to 'vault/Logs/'.
            dry_run: If True, log actions without writing files. Defaults to False.
            retention_days: Number of days to retain logs. Defaults to 90.
        """
        self.component = component
        self.log_path = Path(log_path)
        self.dry_run = dry_run
        self.retention_days = retention_days
        self._ensure_log_directory()

    def _ensure_log_directory(self) -> None:
        """Create log directory if it doesn't exist."""
        if not self.dry_run:
            self.log_path.mkdir(parents=True, exist_ok=True)

    def _get_log_file(self) -> Path:
        """Get the current log file path based on today's date.

        Returns:
            Path to log file: vault/Logs/YYYY-MM-DD.jsonl
        """
        date_str = datetime.now().strftime("%Y-%m-%d")
        return self.log_path / f"{date_str}.jsonl"

    def _create_log_entry(
        self,
        level: str,
        action: str,
        details: dict[str, Any],
        dry_run: bool = False,
        correlation_id: str | None = None,
        domain: str = "personal",
        target: str | None = None,
        parameters: dict[str, Any] | None = None,
        approval_status: str = "none",
        approved_by: str | None = None,
        result: str = "success",
        error: str | None = None,
    ) -> dict[str, Any]:
        """Create log entry with all 14 required Gold Tier fields.

        Args:
            level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
            action: Action type (e.g., 'file_detected', 'action_created').
            details: Contextual data dictionary.
            dry_run: Whether in dry-run mode.
            correlation_id: UUID for tracking across components.
            domain: Domain type (personal|business).
            target: Resource being acted upon.
            parameters: Action-specific parameters.
            approval_status: Approval status (auto|human|none).
            approved_by: User ID if human-approved.
            result: Result status (success|failure|pending).
            error: Error message if failed.

        Returns:
            Dictionary with all 14 required fields.
        """
        return {
            "timestamp": datetime.now().isoformat(),
            "level": level,
            "component": self.component,
            "action": action,
            "dry_run": dry_run,
            "correlation_id": correlation_id or str(uuid.uuid4()),
            "domain": domain,
            "target": target,
            "parameters": parameters or {},
            "approval_status": approval_status,
            "approved_by": approved_by,
            "result": result,
            "error": error,
            "details": details,
        }

    def log(
        self,
        level: str,
        action: str,
        details: dict[str, Any],
        dry_run: bool = False,
        correlation_id: str | None = None,
        domain: str = "personal",
        target: str | None = None,
        parameters: dict[str, Any] | None = None,
        approval_status: str = "none",
        approved_by: str | None = None,
        result: str = "success",
        error: str | None = None,
    ) -> None:
        """Write a log entry to the JSONL file with 14-field schema.

        Args:
            level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
            action: Action type (e.g., 'file_detected', 'action_created').
            details: Contextual data dictionary.
            dry_run: Whether in dry-run mode. Defaults to False.
            correlation_id: Optional UUID to track requests across components.
            domain: Domain type (personal|business). Defaults to 'personal'.
            target: Resource being acted upon. Defaults to None.
            parameters: Action-specific parameters. Defaults to empty dict.
            approval_status: Approval status (auto|human|none). Defaults to 'none'.
            approved_by: User ID if human-approved. Defaults to None.
            result: Result status (success|failure|pending). Defaults to 'success'.
            error: Error message if failed. Defaults to None.
        """
        if self.dry_run or dry_run:
            return

        entry = self._create_log_entry(
            level=level,
            action=action,
            details=details,
            dry_run=dry_run,
            correlation_id=correlation_id,
            domain=domain,
            target=target,
            parameters=parameters,
            approval_status=approval_status,
            approved_by=approved_by,
            result=result,
            error=error,
        )

        log_file = self._get_log_file()
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")

    def info(self, action: str, details: dict[str, Any]) -> None:
        """Log an INFO level message.

        Args:
            action: Action type.
            details: Contextual data dictionary.
        """
        self.log(level="INFO", action=action, details=details)

    def warning(self, action: str, details: dict[str, Any]) -> None:
        """Log a WARNING level message.

        Args:
            action: Action type.
            details: Contextual data dictionary.
        """
        self.log(level="WARNING", action=action, details=details)

    def error(
        self,
        action: str,
        details: dict[str, Any],
        exc: Exception | None = None,
    ) -> None:
        """Log an ERROR level message with optional exception.

        Args:
            action: Action type.
            details: Contextual data dictionary.
            exc: Optional exception to include in log.
        """
        error_details = details.copy()
        if exc:
            import traceback

            error_details["exception"] = str(exc)
            error_details["stack_trace"] = traceback.format_exc()

        self.log(level="ERROR", action=action, details=error_details)

    def rotate_logs(self, max_age_days: int | None = None, max_size_mb: int = 100) -> None:
        """Rotate log files older than max_age_days or larger than max_size_mb.

        Implements Gold Tier 90-day retention policy:
        - Logs older than 90 days are automatically deleted
        - Log files capped at 100MB with warning at 80MB
        - Daily rotation at midnight

        Args:
            max_age_days: Maximum age in days before rotation. 
                          Defaults to self.retention_days (90).
            max_size_mb: Maximum file size in MB before rotation. 
                         Defaults to 100.
        """
        if self.dry_run:
            return

        # Use instance retention_days if not specified
        if max_age_days is None:
            max_age_days = self.retention_days

        cutoff_date = datetime.now() - timedelta(days=max_age_days)
        max_size_bytes = max_size_mb * 1024 * 1024
        warning_size_bytes = 80 * 1024 * 1024  # 80MB warning threshold

        deleted_count = 0
        rotated_count = 0

        for log_file in self.log_path.glob("*.jsonl"):
            should_delete = False
            should_rotate = False

            # Check file age - delete if older than retention period
            file_mtime = datetime.fromtimestamp(log_file.stat().st_mtime)
            if file_mtime < cutoff_date:
                should_delete = True

            # Check file size - rotate if too large
            if log_file.stat().st_size > max_size_bytes:
                should_rotate = True
            elif log_file.stat().st_size > warning_size_bytes:
                self.warning(
                    "log_file_size_warning",
                    {
                        "file": str(log_file),
                        "size_mb": log_file.stat().st_size / (1024 * 1024),
                        "threshold_mb": 80,
                    },
                )

            if should_delete:
                log_file.unlink()
                deleted_count += 1
                self.info(
                    "log_file_deleted",
                    {
                        "file": str(log_file),
                        "age_days": (datetime.now() - file_mtime).days,
                        "reason": f"older than {max_age_days} days",
                    },
                )
            elif should_rotate:
                archived_path = log_file.with_suffix(".jsonl.archived")
                log_file.rename(archived_path)
                rotated_count += 1
                self.info(
                    "log_file_rotated",
                    {
                        "file": str(log_file),
                        "archived": str(archived_path),
                        "reason": f"larger than {max_size_mb}MB",
                    },
                )

        # Delete archived logs older than retention period
        for archived_log in self.log_path.glob("*.archived"):
            file_mtime = datetime.fromtimestamp(archived_log.stat().st_mtime)
            if file_mtime < cutoff_date:
                archived_log.unlink()
                deleted_count += 1

        if deleted_count > 0 or rotated_count > 0:
            self.info(
                "log_rotation_completed",
                {
                    "deleted_count": deleted_count,
                    "rotated_count": rotated_count,
                    "retention_days": max_age_days,
                    "max_size_mb": max_size_mb,
                },
            )

    def query_logs(
        self,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        action: str | None = None,
        result: str | None = None,
        level: str | None = None,
        domain: str | None = None,
        correlation_id: str | None = None,
    ) -> list[dict[str, Any]]:
        """Query audit logs with filters.

        Args:
            start_date: Filter logs from this date. Defaults to 90 days ago.
            end_date: Filter logs until this date. Defaults to now.
            action: Filter by action type.
            result: Filter by result (success|failure|pending).
            level: Filter by log level.
            domain: Filter by domain (personal|business).
            correlation_id: Filter by correlation ID.

        Returns:
            List of matching log entries.
        """
        if start_date is None:
            start_date = datetime.now() - timedelta(days=self.retention_days)
        if end_date is None:
            end_date = datetime.now()

        results = []

        # Iterate through all log files in date range
        current_date = start_date
        while current_date <= end_date:
            date_str = current_date.strftime("%Y-%m-%d")
            log_file = self.log_path / f"{date_str}.jsonl"

            if log_file.exists():
                try:
                    with open(log_file, encoding="utf-8") as f:
                        for line in f:
                            entry = json.loads(line.strip())

                            # Apply filters
                            if action and entry.get("action") != action:
                                continue
                            if result and entry.get("result") != result:
                                continue
                            if level and entry.get("level") != level:
                                continue
                            if domain and entry.get("domain") != domain:
                                continue
                            if correlation_id and entry.get("correlation_id") != correlation_id:
                                continue

                            results.append(entry)
                except (json.JSONDecodeError, IOError) as e:
                    self.error(
                        "log_file_read_error",
                        {"file": str(log_file), "error": str(e)},
                    )

            current_date += timedelta(days=1)

        return results

    def export_logs(
        self,
        output_path: str,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        format: str = "json",
    ) -> Path:
        """Export audit logs to a file.

        Args:
            output_path: Path to export file.
            start_date: Filter logs from this date. Defaults to 90 days ago.
            end_date: Filter logs until this date. Defaults to now.
            format: Export format ('json' or 'csv'). Defaults to 'json'.

        Returns:
            Path to exported file.
        """
        logs = self.query_logs(start_date=start_date, end_date=end_date)
        output_file = Path(output_path)

        if format == "json":
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(logs, f, indent=2)
        elif format == "csv":
            import csv

            if logs:
                fieldnames = list(logs[0].keys())
                with open(output_file, "w", encoding="utf-8", newline="") as f:
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(logs)

        self.info(
            "logs_exported",
            {
                "output_path": str(output_file),
                "count": len(logs),
                "format": format,
            },
        )

        return output_file
