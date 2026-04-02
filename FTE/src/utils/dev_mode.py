"""DEV_MODE validation utility.

This module provides utilities to validate DEV_MODE environment variable
before any external action, providing clear error messages when not set
and integration hooks for all skills.

Usage:
    from src.utils.dev_mode import check_dev_mode, validate_dev_mode_or_dry_run
    
    # Simple check
    if not check_dev_mode():
        raise PermissionError("DEV_MODE not enabled")
    
    # Check with dry-run bypass
    validate_dev_mode_or_dry_run(dry_run=True)  # OK even if DEV_MODE=false
"""

import os
import warnings
from typing import Any


class DEVModeNotEnabledError(Exception):
    """Raised when DEV_MODE is not enabled."""

    pass


def check_dev_mode() -> bool:
    """
    Check if DEV_MODE environment variable is enabled.

    Returns:
        True if DEV_MODE=true (case-insensitive), False otherwise.

    Example:
        >>> check_dev_mode()
        True  # If DEV_MODE=true
        False  # If DEV_MODE is not set or false
    """
    dev_mode = os.environ.get("DEV_MODE", "").lower()
    return dev_mode == "true"


def validate_dev_mode_or_dry_run(dry_run: bool = False) -> None:
    """
    Validate DEV_MODE is enabled or dry_run is True.

    Args:
        dry_run: If True, bypass DEV_MODE check with warning.

    Raises:
        DEVModeNotEnabledError: If DEV_MODE is not enabled and dry_run is False.

    Example:
        >>> validate_dev_mode_or_dry_run(dry_run=False)
        # Raises if DEV_MODE != true
        
        >>> validate_dev_mode_or_dry_run(dry_run=True)
        # OK, but logs warning
    """
    if dry_run:
        warnings.warn(
            "DEV_MODE validation bypassed with --dry-run flag. "
            "No external actions will be performed.",
            UserWarning,
            stacklevel=2,
        )
        return

    if not check_dev_mode():
        raise DEVModeNotEnabledError(
            "DEV_MODE not enabled. Set DEV_MODE=true to enable external actions. "
            "Example: export DEV_MODE=true (Linux/Mac) or "
            "$env:DEV_MODE='true' (PowerShell) or "
            "set DEV_MODE=true (Windows CMD)"
        )


def get_dev_mode_status() -> dict[str, Any]:
    """
    Get DEV_MODE status and configuration.

    Returns:
        Dictionary with status and environment variable value.

    Example:
        >>> get_dev_mode_status()
        {
            "enabled": True,
            "value": "true",
            "message": "DEV_MODE is enabled - external actions allowed"
        }
    """
    dev_mode_value = os.environ.get("DEV_MODE", "")
    enabled = dev_mode_value.lower() == "true"

    return {
        "enabled": enabled,
        "value": dev_mode_value,
        "message": (
            "DEV_MODE is enabled - external actions allowed"
            if enabled
            else "DEV_MODE is disabled - external actions blocked"
        ),
    }
