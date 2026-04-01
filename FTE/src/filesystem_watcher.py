"""FileSystemWatcher concrete implementation for monitoring vault/Inbox/."""

import argparse
import errno
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

from .base_watcher import BaseWatcher
from .metrics.collector import get_metrics_collector
from .utils.circuit_breaker import get_circuit_breaker


def get_config_from_env() -> dict[str, Any]:
    """Get configuration from environment variables.

    Returns:
        Dictionary with vault_path, dry_run, interval
    """
    return {
        "vault_path": os.getenv("VAULT_PATH", "./vault"),
        "dry_run": os.getenv("DRY_RUN", "false").lower() == "true",
        "interval": int(os.getenv("WATCHER_INTERVAL", "60")),
    }


class FileSystemWatcher(BaseWatcher):
    """Concrete implementation of BaseWatcher for file system monitoring.

    Monitors vault/Inbox/ for new files and creates action files
    in vault/Needs_Action/ when files are detected.

    Security Features:
        - DEV_MODE validation before initialization
        - Path traversal prevention
        - STOP file detection for emergency halt
        - Dry-run mode for safe testing
    """

    def __init__(
        self,
        vault_path: str | None = None,
        dry_run: bool | None = None,
        interval: int | None = None,
    ) -> None:
        """Initialize the file system watcher.

        Args:
            vault_path: Root path of the vault directory.
                Precedence: CLI > env var (VAULT_PATH) > default ('./vault')
            dry_run: If True, log actions without creating files.
                Precedence: CLI > env var (DRY_RUN) > default (False)
            interval: Check interval in seconds (max 60).
                Precedence: CLI > env var (WATCHER_INTERVAL) > default (60)

        Raises:
            SystemExit: If DEV_MODE environment variable is not set to 'true'.
        """
        # Get defaults from environment variables
        config = get_config_from_env()

        # CLI overrides env (parameters passed to __init__)
        if vault_path is not None:
            config["vault_path"] = vault_path
        if dry_run is not None:
            config["dry_run"] = dry_run
        if interval is not None:
            config["interval"] = interval

        # Validate DEV_MODE before any operations (security requirement)
        dev_mode = os.getenv("DEV_MODE", "false").lower()
        if dev_mode != "true":
            print(
                f"ERROR: DEV_MODE must be set to 'true' to run. "
                f"Current value: '{os.getenv('DEV_MODE', 'not set')}'. "
                f"Set DEV_MODE=true in your .env file or environment.",
                file=sys.stderr,
            )
            sys.exit(1)

        # Cap interval at 60 seconds (Constitution Principle XII)
        super().__init__(config["vault_path"], config["dry_run"], min(config["interval"], 60))
        self.inbox_path = self.vault_path / "Inbox"
        self.inbox_path.mkdir(parents=True, exist_ok=True)
        self._stop_file_path = self.vault_path / "STOP"

        # Initialize metrics collector
        self.metrics = get_metrics_collector()

        # Initialize circuit breaker for file operations
        self.circuit_breaker = get_circuit_breaker(
            name="filesystem_watcher",
            failure_threshold=5,
            recovery_timeout=60,
        )

        # Recovery: Re-scan Inbox/ for files modified in last 24 hours after restart
        self._recover_missed_files()

    def _recover_missed_files(self) -> None:
        """Re-scan Inbox/ for files modified in last 24 hours after restart.

        Files modified within the last 24 hours are added to processed_files
        to prevent re-processing. Files older than 24 hours are skipped with
        a WARNING log entry.
        """
        if not self.inbox_path.exists():
            return

        cutoff_time = time.time() - (24 * 60 * 60)  # 24 hours ago

        for file_path in self.inbox_path.iterdir():
            if file_path.is_file():
                mtime = file_path.stat().st_mtime
                if mtime > cutoff_time:
                    # File modified in last 24 hours, add to processed
                    file_key = (str(file_path), mtime)
                    self.processed_files.add(file_key)
                    self.logger.log(
                        "INFO",
                        "recovered_file",
                        {
                            "file": str(file_path),
                            "mtime": datetime.fromtimestamp(mtime).isoformat(),
                        },
                    )
                else:
                    # File older than 24 hours, skip with WARNING
                    self.logger.log(
                        "WARNING",
                        "skipped_old_file",
                        {
                            "file": str(file_path),
                            "mtime": datetime.fromtimestamp(mtime).isoformat(),
                        },
                    )

    def check_for_updates(self) -> list[Path]:
        """Check for new or modified files in vault/Inbox/.

        Returns:
            List of paths to files that need processing.
        """
        # Check circuit breaker state first
        if self.circuit_breaker.is_open():
            self.logger.log(
                "WARNING",
                "circuit_breaker_open",
                {
                    "circuit_breaker": "filesystem_watcher",
                    "message": "Circuit breaker OPEN - skipping FileSystem check",
                },
            )
            return []

        # Start timer for metrics
        with self.metrics.timer("filesystem_watcher_check_duration", tags={"source_folder": str(self.inbox_path)}):
            if not self.inbox_path.exists():
                return []

            new_files = []
            for file_path in self.inbox_path.iterdir():
                if file_path.is_file():
                    try:
                        # Check if already processed using path+mtime hash
                        file_key = (str(file_path), file_path.stat().st_mtime)
                        if file_key not in self.processed_files:
                            # This is a new or missed file
                            # Validate path (security)
                            self.validate_path(file_path)
                            new_files.append(file_path)
                            self.processed_files.add(file_key)

                            # Emit metrics for items processed
                            self.metrics.increment_counter(
                                "filesystem_watcher_items_processed",
                                tags={
                                    "source_folder": str(self.inbox_path),
                                    "file_extension": file_path.suffix,
                                },
                            )

                            # Log file detection
                            self.logger.log(
                                "INFO",
                                "file_detected",
                                {"file": str(file_path), "size": file_path.stat().st_size},
                            )

                    except PermissionError as e:
                        # Log ERROR, skip file, continue monitoring
                        self.logger.log(
                            "ERROR", "permission_error", {"file": str(file_path), "error": str(e)}
                        )
                        self.metrics.increment_counter(
                            "filesystem_watcher_errors",
                            tags={"error_type": "permission_error", "source_folder": str(self.inbox_path)},
                        )
                        continue

                    except FileNotFoundError as e:
                        # Log WARNING, file may have been deleted
                        self.logger.log(
                            "WARNING", "file_not_found", {"file": str(file_path), "error": str(e)}
                        )
                        continue

                    except OSError as e:
                        if e.errno == errno.ENOSPC:
                            # Disk full - log CRITICAL, halt gracefully, create alert file
                            self.logger.log(
                                "CRITICAL", "disk_full", {"error": str(e), "errno": e.errno}
                            )
                            self.metrics.increment_counter(
                                "filesystem_watcher_errors",
                                tags={"error_type": "disk_full", "source_folder": str(self.inbox_path)},
                            )
                            try:
                                from .skills import create_alert_file

                                create_alert_file(
                                    file_type="disk_full",
                                    source=str(file_path),
                                    details={"error": str(e)},
                                )
                            except Exception:
                                pass  # Can't create file if disk is full
                            # Halt gracefully
                            raise SystemExit(1) from None
                        else:
                            # Other OSError
                            self.logger.log(
                                "ERROR",
                                "os_error",
                                {"file": str(file_path), "error": str(e), "errno": e.errno},
                            )
                            self.metrics.increment_counter(
                                "filesystem_watcher_errors",
                                tags={"error_type": "os_error", "source_folder": str(self.inbox_path)},
                            )
                            continue

                    except Exception as e:
                        # Log ERROR with stack trace, continue monitoring
                        self.logger.log(
                            "ERROR", "unexpected_error", {"file": str(file_path), "error": str(e)}
                        )
                        self.metrics.increment_counter(
                            "filesystem_watcher_errors",
                            tags={"error_type": "unexpected", "source_folder": str(self.inbox_path)},
                        )
                        continue

            return new_files

    def create_action_file(self, file_path: Path) -> Path:
        """Create an action file for a detected file.

        Overrides BaseWatcher.create_action_file() with enhanced implementation
        that includes actual file content.

        Args:
            file_path: Path to the file that needs processing.

        Returns:
            Path to the created action file.

        Raises:
            ValueError: If file_path is outside vault directory.
        """
        # Validate path to prevent traversal attacks
        self.validate_path(file_path)

        # Create Needs_Action directory if it doesn't exist
        needs_action_path = self.vault_path / "Needs_Action"
        needs_action_path.mkdir(parents=True, exist_ok=True)

        # Generate action file path
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        action_filename = f"FILE_{file_path.stem}_{timestamp}.md"
        action_file_path = needs_action_path / action_filename

        # Calculate relative source path
        try:
            relative_source = str(file_path.relative_to(self.vault_path))
        except ValueError:
            relative_source = file_path.name

        # Generate action file content with YAML frontmatter
        content = self._generate_action_file_content(
            source_path=relative_source, file_path=file_path
        )

        # Write action file (unless in dry-run mode)
        if not self.dry_run:
            action_file_path.write_text(content, encoding="utf-8")

        # Log action
        self.logger.log(
            "INFO",
            "action_created",
            {"action_file": str(action_file_path), "source": str(file_path)},
        )

        return action_file_path

    def validate_path(self, file_path: Path) -> None:
        """Validate that a file path is within the vault directory.

        Args:
            file_path: Path to validate.

        Raises:
            ValueError: If path is outside vault directory (traversal attempt).
        """
        resolved_path = file_path.resolve()
        try:
            resolved_path.relative_to(self.vault_path)
        except ValueError:
            self.logger.log(
                "ERROR",
                "path_traversal_attempt",
                {"attempted_path": str(file_path), "vault_path": str(self.vault_path)},
            )
            raise ValueError(
                f"Path traversal detected: {file_path} is outside vault directory {self.vault_path}"
            ) from None

    def check_stop_file(self) -> bool:
        """Check if STOP file exists in vault.

        Returns:
            True if STOP file exists (should halt), False otherwise.
        """
        return self._stop_file_path.exists()

    def _generate_action_file_content(self, source_path: str, file_path: Path) -> str:
        """Generate content for action file with YAML frontmatter.

        Args:
            source_path: Relative path to source file.
            file_path: Absolute path to source file.

        Returns:
            Complete action file content with YAML frontmatter.
        """
        timestamp = datetime.now().isoformat()

        # Read file content if it exists and is readable
        content_text = ""
        try:
            if file_path.exists() and file_path.stat().st_size < 10 * 1024 * 1024:  # < 10MB
                content_text = file_path.read_text(encoding="utf-8")
        except (PermissionError, UnicodeDecodeError):
            content_text = "[Unable to read file content - may require manual review]"

        content = f"""---
type: file_drop
source: {source_path}
created: {timestamp}
status: pending
---

## Content
{content_text if content_text else "[File content not available]"}

## Suggested Actions
- [ ] Review this file
- [ ] Process as needed
- [ ] Move to Done when complete
"""
        return content


def create_parser() -> argparse.ArgumentParser:
    """Create argument parser for CLI.

    Returns:
        ArgumentParser with vault-path, dry-run, interval arguments
    """
    parser = argparse.ArgumentParser(
        description="FTE-Agent File System Watcher - Monitor Inbox/ for new files"
    )
    parser.add_argument(
        "--vault-path",
        type=str,
        default=None,
        help="Path to vault directory (default: ./vault or VAULT_PATH env var)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=None,
        help="Log intended actions without creating files (default: DRY_RUN env var)",
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=None,
        help="Check interval in seconds, max 60 (default: WATCHER_INTERVAL env var or 60)",
    )
    return parser


def main() -> None:
    """Main entry point for CLI."""
    parser = create_parser()
    args = parser.parse_args()

    # Get config from env (defaults)
    config = get_config_from_env()

    # CLI flags override env vars
    if args.vault_path is not None:
        config["vault_path"] = args.vault_path
    if args.dry_run:
        config["dry_run"] = args.dry_run
    if args.interval is not None:
        config["interval"] = args.interval

    # Create and run watcher
    watcher = FileSystemWatcher(
        vault_path=config["vault_path"], dry_run=config["dry_run"], interval=config["interval"]
    )

    print("Starting File System Watcher...")
    print(f"  Vault: {config['vault_path']}")
    print(f"  Dry Run: {config['dry_run']}")
    print(f"  Interval: {config['interval']}s")

    watcher.run()


if __name__ == "__main__":
    main()
