"""Approval Handler for monitoring and processing approval requests.

Monitors Pending_Approval/, Approved/, and Rejected/ folders for file moves
and processes approval decisions with circuit breaker protection.

Usage:
    from src.approval_handler import ApprovalHandler
    
    handler = ApprovalHandler()
    handler.start()  # Start monitoring in background
    handler.stop()   # Stop monitoring
"""

import os
import sys
import time
import threading
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Optional

import yaml

from src.audit_logger import AuditLogger
from src.metrics.collector import get_metrics_collector
from src.utils.circuit_breaker import PersistentCircuitBreaker
from src.utils.dead_letter_queue import DeadLetterQueue


class ApprovalHandlerError(Exception):
    """Raised when approval handler encounters an error."""

    pass


class ApprovalDetectionError(Exception):
    """Raised when approval detection fails."""

    pass


class ApprovalHandler:
    """Handler for processing approval requests.

    Monitors vault folders for:
    - New approval requests in Pending_Approval/
    - Approved files moved to Approved/
    - Rejected files moved to Rejected/

    Detects file moves within 5 seconds (p95) and triggers callbacks.

    Attributes:
        vault_dir: Base vault directory
        check_interval: Seconds between folder checks (default: 2)
        detection_timeout: Max seconds for detection (p95 target: 5s)
    """

    def __init__(
        self,
        vault_dir: Optional[Path] = None,
        check_interval: float = 2.0,
        detection_timeout: float = 5.0,
    ) -> None:
        """Initialize approval handler.

        Args:
            vault_dir: Base vault directory (default: FTE/vault)
            check_interval: Seconds between folder checks
            detection_timeout: Target detection time in seconds
        """
        # Resolve vault directory
        if vault_dir is None:
            vault_dir = Path(__file__).parent.parent / "vault"
        self.vault_dir = Path(vault_dir).resolve()

        self.pending_approval_dir = self.vault_dir / "Pending_Approval"
        self.approved_dir = self.vault_dir / "Approved"
        self.rejected_dir = self.vault_dir / "Rejected"
        self.dashboard_path = self.vault_dir / "Dashboard.md"

        self.check_interval = check_interval
        self.detection_timeout = detection_timeout

        # Ensure directories exist
        self._ensure_directories()

        # Logger and metrics
        self.logger = AuditLogger(component="ApprovalHandler")
        self.metrics = get_metrics_collector()

        # Circuit breaker for file operations
        self.circuit_breaker = PersistentCircuitBreaker(
            name="approval_handler",
            failure_threshold=5,
            recovery_timeout=60,
        )

        # Dead Letter Queue for failed actions
        self.dlq = DeadLetterQueue(
            db_path=str(Path(__file__).parent.parent / "data" / "failed_actions.db"),
            vault_dir=str(self.vault_dir),
            max_retries=3,
        )

        # State tracking
        self._running = False
        self._monitor_thread: Optional[threading.Thread] = None
        self._known_files: set[str] = set()
        self._approval_callbacks: list[Callable[[Path], None]] = []
        self._rejection_callbacks: list[Callable[[Path], None]] = []

        # Metrics
        self._metrics_start_time: Optional[float] = None

    def _ensure_directories(self) -> None:
        """Create necessary directories if they don't exist."""
        for directory in [
            self.pending_approval_dir,
            self.approved_dir,
            self.rejected_dir,
        ]:
            directory.mkdir(parents=True, exist_ok=True)

    def register_approval_callback(self, callback: Callable[[Path], None]) -> None:
        """Register callback for approved files.

        Args:
            callback: Function to call with approved file path
        """
        self._approval_callbacks.append(callback)
        callback_name = getattr(callback, "__name__", str(callback))
        self.logger.log(
            "INFO",
            "approval_callback_registered",
            {"callback": callback_name},
        )

    def register_rejection_callback(self, callback: Callable[[Path], None]) -> None:
        """Register callback for rejected files.

        Args:
            callback: Function to call with rejected file path
        """
        self._rejection_callbacks.append(callback)
        callback_name = getattr(callback, "__name__", str(callback))
        self.logger.log(
            "INFO",
            "rejection_callback_registered",
            {"callback": callback_name},
        )

    def _scan_folder(self, folder: Path, pattern: str = "*.md") -> set[str]:
        """Scan folder for files.

        Args:
            folder: Directory to scan
            pattern: Glob pattern for files

        Returns:
            Set of filenames
        """
        try:
            return {f.name for f in folder.glob(pattern) if f.is_file()}
        except Exception as e:
            self.logger.log(
                "WARNING",
                "folder_scan_failed",
                {"folder": str(folder), "error": str(e)},
            )
            return set()

    def _detect_new_approvals(self) -> list[Path]:
        """Detect new approval requests in Pending_Approval/.

        Returns:
            List of new approval file paths
        """
        current_files = self._scan_folder(self.pending_approval_dir, "APPROVAL_*.md")
        new_files = current_files - self._known_files

        if new_files:
            self._known_files = current_files
            return [self.pending_approval_dir / f for f in new_files]

        return []

    def _detect_approved_files(self) -> list[Path]:
        """Detect files moved to Approved/ folder.

        Returns:
            List of approved file paths
        """
        approved_files = self._scan_folder(self.approved_dir, "APPROVAL_*.md")

        if approved_files:
            # Remove from known pending files
            self._known_files -= approved_files
            return [self.approved_dir / f for f in approved_files]

        return []

    def _detect_rejected_files(self) -> list[Path]:
        """Detect files moved to Rejected/ folder.

        Returns:
            List of rejected file paths
        """
        rejected_files = self._scan_folder(self.rejected_dir, "APPROVAL_*.md")

        if rejected_files:
            # Remove from known pending files
            self._known_files -= rejected_files
            return [self.rejected_dir / f for f in rejected_files]

        return []

    def _process_approval(self, approval_file: Path) -> None:
        """Process an approved file.

        Args:
            approval_file: Path to approved file
        """
        start_time = time.time()
        action_id = None

        try:
            self.logger.log(
                "INFO",
                "approval_detected",
                {"file": str(approval_file)},
            )

            # Read approval details for DLQ tracking
            approval_details = self.get_approval_details(approval_file)
            action_type = approval_details.get("type", "unknown_action") if approval_details else "unknown"

            # Call registered callbacks
            for callback in self._approval_callbacks:
                try:
                    callback(approval_file)
                except Exception as e:
                    self.logger.log(
                        "ERROR",
                        "approval_callback_failed",
                        {"callback": callback.__name__, "error": str(e)},
                    )
                    # Archive to DLQ on failure
                    action_id = self.dlq.archive_action(
                        original_action=action_type,
                        failure_reason=f"Approval callback failed: {str(e)}",
                        details={
                            "approval_file": str(approval_file),
                            "callback": callback.__name__,
                            "error_type": type(e).__name__,
                        },
                        original_metadata=approval_details,
                    )

            duration = time.time() - start_time
            self.metrics.increment_counter("approval_detection_count", 1.0)
            self.metrics.record_histogram("approval_detection_latency", duration)

            self.logger.log(
                "INFO",
                "approval_processed",
                {"file": str(approval_file), "duration_seconds": duration},
            )

        except Exception as e:
            self.logger.log(
                "ERROR",
                "approval_processing_failed",
                {"file": str(approval_file), "error": str(e)},
            )
            self.metrics.increment_counter("approval_processing_errors", 1.0)

            # Archive to DLQ on critical failure
            if action_id is None:
                self.dlq.archive_action(
                    original_action="approval_processing",
                    failure_reason=str(e),
                    details={
                        "approval_file": str(approval_file),
                        "error_type": type(e).__name__,
                    },
                )

    def _process_rejection(self, rejection_file: Path) -> None:
        """Process a rejected file.

        Args:
            rejection_file: Path to rejected file
        """
        start_time = time.time()
        action_id = None

        try:
            self.logger.log(
                "INFO",
                "rejection_detected",
                {"file": str(rejection_file)},
            )

            # Read rejection details for DLQ tracking
            rejection_details = self.get_approval_details(rejection_file)
            action_type = rejection_details.get("type", "unknown_action") if rejection_details else "unknown"

            # Call registered callbacks
            for callback in self._rejection_callbacks:
                try:
                    callback(rejection_file)
                except Exception as e:
                    self.logger.log(
                        "ERROR",
                        "rejection_callback_failed",
                        {"callback": callback.__name__, "error": str(e)},
                    )
                    # Archive to DLQ on failure
                    action_id = self.dlq.archive_action(
                        original_action=action_type,
                        failure_reason=f"Rejection callback failed: {str(e)}",
                        details={
                            "rejection_file": str(rejection_file),
                            "callback": callback.__name__,
                            "error_type": type(e).__name__,
                        },
                        original_metadata=rejection_details,
                    )

            duration = time.time() - start_time
            self.metrics.increment_counter("rejection_detection_count", 1.0)
            self.metrics.record_histogram("rejection_detection_latency", duration)

            self.logger.log(
                "INFO",
                "rejection_processed",
                {"file": str(rejection_file), "duration_seconds": duration},
            )

        except Exception as e:
            self.logger.log(
                "ERROR",
                "rejection_processing_failed",
                {"file": str(rejection_file), "error": str(e)},
            )
            self.metrics.increment_counter("rejection_processing_errors", 1.0)

            # Archive to DLQ on critical failure
            if action_id is None:
                self.dlq.archive_action(
                    original_action="rejection_processing",
                    failure_reason=str(e),
                    details={
                        "rejection_file": str(rejection_file),
                        "error_type": type(e).__name__,
                    },
                )

    def _monitor_loop(self) -> None:
        """Main monitoring loop."""
        self.logger.log(
            "INFO",
            "approval_monitoring_started",
            {
                "check_interval": self.check_interval,
                "detection_timeout": self.detection_timeout,
            },
        )

        while self._running:
            try:
                # Wrap in circuit breaker
                self.circuit_breaker.call(self._check_folders)

            except Exception as e:
                self.logger.log(
                    "ERROR",
                    "monitor_loop_error",
                    {"error": str(e)},
                )
                self.metrics.increment_counter("approval_monitor_errors", 1.0)

            time.sleep(self.check_interval)

        self.logger.log("INFO", "approval_monitoring_stopped", {})

    def _check_folders(self) -> None:
        """Check all folders for changes."""
        check_start = time.time()

        # Check for new approvals
        new_approvals = self._detect_new_approvals()
        for approval_file in new_approvals:
            self.logger.log(
                "INFO",
                "new_approval_request",
                {"file": str(approval_file)},
            )
            self.metrics.increment_counter("approval_request_received", 1.0)

        # Check for approved files
        approved_files = self._detect_approved_files()
        for approved_file in approved_files:
            self._process_approval(approved_file)

        # Check for rejected files
        rejected_files = self._detect_rejected_files()
        for rejected_file in rejected_files:
            self._process_rejection(rejected_file)

        check_duration = time.time() - check_start
        self.metrics.record_histogram("approval_check_duration", check_duration)

    def start(self) -> None:
        """Start monitoring approval folders."""
        if self._running:
            self.logger.log("WARNING", "monitor_already_running")
            return

        self._running = True
        self._metrics_start_time = time.time()

        # Initialize known files
        self._known_files = self._scan_folder(self.pending_approval_dir, "APPROVAL_*.md")

        # Start monitor thread
        self._monitor_thread = threading.Thread(
            target=self._monitor_loop,
            name="ApprovalHandler-Monitor",
            daemon=True,
        )
        self._monitor_thread.start()

        self.logger.log(
            "INFO",
            "approval_handler_started",
            {"check_interval": self.check_interval},
        )
        self.metrics.increment_counter("approval_handler_starts", 1.0)

    def stop(self) -> None:
        """Stop monitoring approval folders."""
        if not self._running:
            return

        self._running = False

        if self._monitor_thread:
            self._monitor_thread.join(timeout=10.0)
            self._monitor_thread = None

        self.logger.log("INFO", "approval_handler_stopped", {})
        self.metrics.increment_counter("approval_handler_stops", 1.0)

    def get_approval_details(self, approval_file: Path) -> Optional[dict[str, Any]]:
        """Get approval details from file.

        Args:
            approval_file: Path to approval file

        Returns:
            Dict with approval details or None if not found
        """
        try:
            if not approval_file.exists():
                return None

            content = approval_file.read_text(encoding="utf-8")
            match = content.split("---", 2)
            if len(match) < 2:
                return None

            frontmatter = yaml.safe_load(match[1])
            return frontmatter.get("action_details", {})

        except Exception as e:
            self.logger.log(
                "ERROR",
                "approval_details_read_failed",
                {"file": str(approval_file), "error": str(e)},
            )
            return None

    def get_approval_status(self, approval_file: Path) -> Optional[str]:
        """Get approval status from file.

        Args:
            approval_file: Path to approval file

        Returns:
            Status string or None if not found
        """
        try:
            if not approval_file.exists():
                return None

            content = approval_file.read_text(encoding="utf-8")
            match = content.split("---", 2)
            if len(match) < 2:
                return None

            frontmatter = yaml.safe_load(match[1])
            return frontmatter.get("status", "unknown")

        except Exception as e:
            self.logger.log(
                "ERROR",
                "approval_status_read_failed",
                {"file": str(approval_file), "error": str(e)},
            )
            return None

    def is_running(self) -> bool:
        """Check if handler is running.

        Returns:
            True if monitoring is active
        """
        return self._running


# Global instance for singleton access
_approval_handler: Optional[ApprovalHandler] = None


def get_approval_handler(
    vault_dir: Optional[Path] = None,
    check_interval: float = 2.0,
) -> ApprovalHandler:
    """Get or create the global approval handler instance.

    Args:
        vault_dir: Base vault directory
        check_interval: Seconds between folder checks

    Returns:
        ApprovalHandler instance
    """
    global _approval_handler
    if _approval_handler is None:
        _approval_handler = ApprovalHandler(
            vault_dir=vault_dir,
            check_interval=check_interval,
        )
    return _approval_handler
