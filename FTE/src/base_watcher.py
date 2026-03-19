"""BaseWatcher abstract base class for file system monitoring.

This module defines the interface for all watcher implementations.
"""

import time
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path

from .audit_logger import AuditLogger


class BaseWatcher(ABC):
    """Abstract base class for file system watchers.

    Provides common functionality for monitoring file systems
    and creating action files when changes are detected.

    Attributes:
        vault_path: Root path of the vault directory.
        dry_run: If True, log actions without creating files.
        interval: Check interval in seconds (default: 60).
    """

    def __init__(self, vault_path: str, dry_run: bool = False, interval: int = 60) -> None:
        """Initialize the watcher.

        Args:
            vault_path: Root path of the vault directory.
            dry_run: If True, log actions without creating files. Defaults to False.
            interval: Check interval in seconds. Defaults to 60.
        """
        self.vault_path = Path(vault_path).resolve()
        self.dry_run = dry_run
        self.interval = min(interval, 60)  # Cap at 60 seconds per constitution
        self.logger = AuditLogger(component=self.__class__.__name__)
        self.processed_files: set[tuple[str, float]] = set()

    @abstractmethod
    def check_for_updates(self) -> list[Path]:
        """Check for new or modified files in the vault.

        Returns:
            List of paths to files that need processing.
        """
        pass

    def create_action_file(self, file_path: Path) -> Path:
        """Create an action file for a detected file.

        Args:
            file_path: Path to the file that needs processing.

        Returns:
            Path to the created action file.
        """
        # Generate action file path
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        needs_action = self.vault_path / "Needs_Action"
        needs_action.mkdir(parents=True, exist_ok=True)

        action_filename = f"FILE_{file_path.stem}_{timestamp}.md"
        action_path = needs_action / action_filename

        # Create YAML frontmatter
        try:
            relative_source = str(file_path.relative_to(self.vault_path))
        except ValueError:
            relative_source = file_path.name

        frontmatter = f"""---
type: file_drop
source: {relative_source}
created: {datetime.now().isoformat()}
status: pending
---

## Content
[File content or reference]

## Suggested Actions
- [ ] Process this file
- [ ] Move to Done when complete
"""

        if self.dry_run:
            self.logger.log(
                "INFO",
                "action_file_dry_run",
                {"would_create": str(action_path), "source": str(file_path)},
                dry_run=True,
            )
            return action_path

        # Write action file
        action_path.write_text(frontmatter, encoding="utf-8")

        # Log action
        self.logger.log(
            "INFO", "action_created", {"action_file": str(action_path), "source": str(file_path)}
        )

        return action_path

    def run(self) -> None:
        """Main watcher loop.

        Continuously monitors for updates and creates action files.
        Stops when STOP file is detected.
        """
        self.logger.log(
            "INFO",
            "watcher_started",
            {
                "vault_path": str(self.vault_path),
                "dry_run": self.dry_run,
                "interval": self.interval,
            },
        )

        try:
            while True:
                # Check for STOP file
                stop_file = self.vault_path / "STOP"
                if stop_file.exists():
                    self.logger.log("WARNING", "stop_file_detected", {"stop_file": str(stop_file)})
                    break

                # Check for updates
                try:
                    updates = self.check_for_updates()
                    for file_path in updates:
                        self.create_action_file(file_path)
                except Exception as e:
                    self.logger.error("check_updates_error", {"error": str(e)}, exc=e)

                # Sleep until next check
                time.sleep(self.interval)

        except KeyboardInterrupt:
            self.logger.log("INFO", "watcher_stopped", {"reason": "keyboard_interrupt"})
        finally:
            self.logger.log("INFO", "watcher_stopped", {"reason": "normal"})
