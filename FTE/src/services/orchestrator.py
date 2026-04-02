"""Orchestrator - Main service coordinating all watchers and skills.

This module implements the main orchestrator service that:
- Monitors /Vault/Needs_Action/ for new action files
- Monitors /Vault/Approved/ for approved actions to execute
- Triggers appropriate skills based on action file type
- Logs all operations with correlation_id
- Implements graceful shutdown on STOP file detection

Usage:
    from src.services.orchestrator import Orchestrator
    
    orchestrator = Orchestrator(vault_path="vault/")
    orchestrator.run()  # Start main loop
"""

import signal
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

import yaml

from ..audit_logger import AuditLogger
from ..utils.dev_mode import validate_dev_mode_or_dry_run
from ..utils.retry_handler import retry_with_backoff_sync


class Orchestrator:
    """Main orchestrator service for FTE-Agent.

    Coordinates all watchers and skills, processing action files
    from Needs_Action/ and executing approved actions from Approved/.

    Attributes:
        vault_path: Root path of the vault directory.
        dry_run: If True, log actions without executing.
        check_interval: Seconds between checks (default: 5).
        logger: Audit logger instance.
    """

    def __init__(
        self,
        vault_path: str,
        dry_run: bool = False,
        check_interval: int = 5,
    ) -> None:
        """Initialize orchestrator.

        Args:
            vault_path: Root path of the vault directory.
            dry_run: If True, log actions without executing.
            check_interval: Seconds between checks (default: 5).
        """
        self.vault_path = Path(vault_path).resolve()
        self.dry_run = dry_run
        self.check_interval = check_interval

        # Initialize logger
        self.logger = AuditLogger(
            component="Orchestrator",
            dry_run=dry_run,
        )

        # Define paths
        self.needs_action_dir = self.vault_path / "Needs_Action"
        self.approved_dir = self.vault_path / "Approved"
        self.pending_approval_dir = self.vault_path / "Pending_Approval"
        self.stop_file_path = self.vault_path / "STOP"

        # Ensure directories exist
        self._ensure_directories()

        # State tracking
        self._running = False
        self._processed_files: set[str] = set()

        # Register signal handlers for graceful shutdown
        self._register_signal_handlers()

        self.logger.log(
            "INFO",
            "orchestrator_started",
            {
                "vault_path": str(self.vault_path),
                "dry_run": self.dry_run,
                "check_interval": self.check_interval,
            },
        )

    def _ensure_directories(self) -> None:
        """Create necessary directories if they don't exist."""
        for directory in [
            self.needs_action_dir,
            self.approved_dir,
            self.pending_approval_dir,
        ]:
            directory.mkdir(parents=True, exist_ok=True)

    def _register_signal_handlers(self) -> None:
        """Register signal handlers for graceful shutdown."""

        def signal_handler(signum, frame):
            self.logger.log(
                "INFO",
                "signal_received",
                {"signal": signum},
            )
            self.shutdown()

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

    def _check_stop_file(self) -> bool:
        """Check if STOP file exists.

        Returns:
            True if STOP file detected, False otherwise.
        """
        return self.stop_file_path.exists()

    def _scan_folder(self, folder: Path, pattern: str = "*.md") -> list[Path]:
        """Scan folder for action files.

        Args:
            folder: Directory to scan.
            pattern: Glob pattern for files.

        Returns:
            List of file paths.
        """
        try:
            return [f for f in folder.glob(pattern) if f.is_file()]
        except Exception as e:
            self.logger.log(
                "WARNING",
                "folder_scan_failed",
                {"folder": str(folder), "error": str(e)},
            )
            return []

    def _read_action_file(self, action_file: Path) -> Optional[dict[str, Any]]:
        """Read action file and parse YAML frontmatter.

        Args:
            action_file: Path to action file.

        Returns:
            Dict with action details or None if parsing failed.
        """
        try:
            content = action_file.read_text(encoding="utf-8")
            parts = content.split("---", 2)

            if len(parts) < 2:
                return None

            frontmatter = yaml.safe_load(parts[1])
            return frontmatter

        except Exception as e:
            self.logger.log(
                "ERROR",
                "action_file_read_failed",
                {"file": str(action_file), "error": str(e)},
            )
            return None

    def _process_action_file(self, action_file: Path) -> bool:
        """Process a single action file.

        Args:
            action_file: Path to action file.

        Returns:
            True if processed successfully, False otherwise.
        """
        start_time = time.time()
        correlation_id = str(datetime.now().timestamp())

        try:
            # Read action file
            action_data = self._read_action_file(action_file)

            if not action_data:
                self.logger.log(
                    "WARNING",
                    "action_file_parse_failed",
                    {"file": str(action_file)},
                    correlation_id=correlation_id,
                )
                return False

            # Get action type
            action_type = action_data.get("type", "unknown")

            self.logger.log(
                "INFO",
                "action_file_processing",
                {
                    "file": str(action_file),
                    "type": action_type,
                },
                correlation_id=correlation_id,
            )

            # Route to appropriate handler based on type
            success = self._route_action(action_type, action_data, action_file)

            # Log result
            duration = time.time() - start_time
            if success:
                self.logger.log(
                    "INFO",
                    "action_file_processed",
                    {
                        "file": str(action_file),
                        "type": action_type,
                        "duration_seconds": duration,
                    },
                    correlation_id=correlation_id,
                    result="success",
                )
            else:
                self.logger.log(
                    "WARNING",
                    "action_file_processing_failed",
                    {
                        "file": str(action_file),
                        "type": action_type,
                        "duration_seconds": duration,
                    },
                    correlation_id=correlation_id,
                    result="failure",
                )

            return success

        except Exception as e:
            self.logger.log(
                "ERROR",
                "action_file_processing_failed",
                {
                    "file": str(action_file),
                    "error": str(e),
                    "error_type": type(e).__name__,
                },
                correlation_id=correlation_id,
                result="failure",
            )
            return False

    def _route_action(
        self,
        action_type: str,
        action_data: dict[str, Any],
        action_file: Path,
    ) -> bool:
        """Route action to appropriate handler.

        Args:
            action_type: Type of action (email, whatsapp, file, etc.).
            action_data: Action data from frontmatter.
            action_file: Path to action file.

        Returns:
            True if handled successfully.
        """
        # Route based on action type
        handlers = {
            "email": self._handle_email_action,
            "whatsapp": self._handle_whatsapp_action,
            "file_drop": self._handle_file_drop_action,
            "approval_request": self._handle_approval_request,
        }

        handler = handlers.get(action_type)

        if handler:
            return handler(action_data, action_file)
        else:
            self.logger.log(
                "WARNING",
                "unknown_action_type",
                {"type": action_type, "file": str(action_file)},
            )
            return False

    def _handle_email_action(
        self,
        action_data: dict[str, Any],
        action_file: Path,
    ) -> bool:
        """Handle email action.

        Args:
            action_data: Action data.
            action_file: Path to action file.

        Returns:
            True if handled successfully.
        """
        self.logger.log(
            "INFO",
            "email_action_routed",
            {"file": str(action_file)},
        )
        # TODO: Integrate with email skills
        return True

    def _handle_whatsapp_action(
        self,
        action_data: dict[str, Any],
        action_file: Path,
    ) -> bool:
        """Handle WhatsApp action.

        Args:
            action_data: Action data.
            action_file: Path to action file.

        Returns:
            True if handled successfully.
        """
        self.logger.log(
            "INFO",
            "whatsapp_action_routed",
            {"file": str(action_file)},
        )
        # TODO: Integrate with WhatsApp skills
        return True

    def _handle_file_drop_action(
        self,
        action_data: dict[str, Any],
        action_file: Path,
    ) -> bool:
        """Handle file drop action.

        Args:
            action_data: Action data.
            action_file: Path to action file.

        Returns:
            True if handled successfully.
        """
        self.logger.log(
            "INFO",
            "file_drop_action_routed",
            {"file": str(action_file)},
        )
        # TODO: Integrate with filesystem skills
        return True

    def _handle_approval_request(
        self,
        action_data: dict[str, Any],
        action_file: Path,
    ) -> bool:
        """Handle approval request action.

        Args:
            action_data: Action data.
            action_file: Path to action file.

        Returns:
            True if handled successfully.
        """
        self.logger.log(
            "INFO",
            "approval_request_routed",
            {"file": str(action_file)},
        )
        # TODO: Integrate with approval handler
        return True

    def _execute_approved_action(self, action_file: Path) -> bool:
        """Execute an approved action.

        Args:
            action_file: Path to approved action file.

        Returns:
            True if executed successfully.
        """
        correlation_id = str(datetime.now().timestamp())

        try:
            # Validate DEV_MODE before executing
            validate_dev_mode_or_dry_run(dry_run=self.dry_run)

            # Read action details
            action_data = self._read_action_file(action_file)

            if not action_data:
                return False

            self.logger.log(
                "INFO",
                "executing_approved_action",
                {
                    "file": str(action_file),
                    "type": action_data.get("type", "unknown"),
                },
                correlation_id=correlation_id,
            )

            # Execute based on type
            # TODO: Integrate with actual skill execution
            self.logger.log(
                "INFO",
                "approved_action_executed",
                {"file": str(action_file)},
                correlation_id=correlation_id,
                result="success",
            )

            return True

        except Exception as e:
            self.logger.log(
                "ERROR",
                "approved_action_execution_failed",
                {
                    "file": str(action_file),
                    "error": str(e),
                    "error_type": type(e).__name__,
                },
                correlation_id=correlation_id,
                result="failure",
            )
            return False

    def run(self) -> None:
        """Main orchestrator loop.

        Continuously monitors for action files and executes approved actions.
        Stops when STOP file is detected or signal received.
        """
        self._running = True

        self.logger.log(
            "INFO",
            "orchestrator_loop_started",
            {
                "check_interval": self.check_interval,
            },
        )

        try:
            while self._running:
                # Check for STOP file
                if self._check_stop_file():
                    self.logger.log(
                        "WARNING",
                        "stop_file_detected",
                        {"stop_file": str(self.stop_file_path)},
                    )
                    break

                # Process Needs_Action folder
                action_files = self._scan_folder(self.needs_action_dir)
                for action_file in action_files:
                    if action_file.name not in self._processed_files:
                        success = self._process_action_file(action_file)
                        if success:
                            self._processed_files.add(action_file.name)

                # Process Approved folder
                approved_files = self._scan_folder(self.approved_dir)
                for approved_file in approved_files:
                    if approved_file.name not in self._processed_files:
                        success = self._execute_approved_action(approved_file)
                        if success:
                            self._processed_files.add(approved_file.name)

                # Sleep until next check
                time.sleep(self.check_interval)

        except KeyboardInterrupt:
            self.logger.log(
                "INFO",
                "orchestrator_stopped",
                {"reason": "keyboard_interrupt"},
            )
        finally:
            self._running = False
            self.logger.log(
                "INFO",
                "orchestrator_stopped",
                {"reason": "normal"},
            )

    def shutdown(self) -> None:
        """Gracefully shutdown the orchestrator."""
        self.logger.log(
            "INFO",
            "orchestrator_shutdown",
            {},
        )
        self._running = False


def main() -> None:
    """Entry point for Orchestrator."""
    import argparse

    parser = argparse.ArgumentParser(description="FTE-Agent Orchestrator")
    parser.add_argument(
        "--vault-path",
        type=str,
        default="vault/",
        help="Path to vault directory",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Log actions without executing",
    )
    parser.add_argument(
        "--check-interval",
        type=int,
        default=5,
        help="Check interval in seconds (default: 5)",
    )

    args = parser.parse_args()

    orchestrator = Orchestrator(
        vault_path=args.vault_path,
        dry_run=args.dry_run,
        check_interval=args.check_interval,
    )
    orchestrator.run()


if __name__ == "__main__":
    main()
