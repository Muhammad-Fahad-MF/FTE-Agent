"""BaseWatcher abstract base class for file system monitoring.

This module defines the interface for all watcher implementations.
"""

from abc import ABC, abstractmethod
from pathlib import Path


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
        self.interval = interval

    @abstractmethod
    def check_for_updates(self) -> list[Path]:
        """Check for new or modified files in the vault.
        
        Returns:
            List of paths to files that need processing.
        """
        pass

    @abstractmethod
    def create_action_file(self, file_path: Path) -> Path:
        """Create an action file for a detected file.
        
        Args:
            file_path: Path to the file that needs processing.
            
        Returns:
            Path to the created action file.
        """
        pass
