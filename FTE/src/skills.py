"""Python Skills for FTE-Agent.

Reusable functions for file operations that can be called by:
- Qwen Code CLI (via subprocess)
- Other Python modules (via import)
- CLI wrappers
"""

import os
from datetime import datetime
from pathlib import Path
from typing import Any

from .audit_logger import AuditLogger


def check_dev_mode() -> bool:
    """Validate DEV_MODE is set.

    Returns:
        True if DEV_MODE is "true"

    Raises:
        SystemExit: If DEV_MODE is not set
    """
    dev_mode = os.getenv("DEV_MODE", "false")
    if dev_mode != "true":
        print(f"ERROR: DEV_MODE must be 'true' (current: {dev_mode})")
        raise SystemExit(1)
    return True


def create_action_file(
    file_type: str, source: str, content: str = "", dry_run: bool = False
) -> str:
    """Create action file in Needs_Action/.

    Args:
        file_type: Type of action (file_drop, email, approval_request)
        source: Source path or identifier
        content: Optional content for action file
        dry_run: If True, log without creating file

    Returns:
        Path to created (or would-be created) action file
    """
    check_dev_mode()

    vault_path = Path(os.getenv("VAULT_PATH", "./vault"))
    needs_action = vault_path / "Needs_Action"
    needs_action.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    action_filename = f"{file_type.upper()}_{Path(source).stem}_{timestamp}.md"
    action_path = needs_action / action_filename

    frontmatter = f"""---
type: {file_type}
source: {source}
created: {datetime.now().isoformat()}
status: pending
---

## Content
{content}

## Suggested Actions
- [ ] Process this item
- [ ] Move to Done when complete
"""

    if dry_run:
        logger = AuditLogger(component="skills")
        logger.log(
            "INFO",
            "action_file_dry_run",
            {"would_create": str(action_path), "source": source},
            dry_run=True,
        )
        return str(action_path)

    action_path.write_text(frontmatter, encoding="utf-8")

    logger = AuditLogger(component="skills")
    logger.log("INFO", "action_created", {"action_file": str(action_path), "source": source})

    return str(action_path)


def log_audit(
    action: str, details: dict[str, Any], level: str = "INFO", dry_run: bool = False
) -> None:
    """Log audit entry.

    Args:
        action: Action type (file_created, action_executed, etc.)
        details: Additional context data
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        dry_run: If True, log to stdout instead of file
    """
    check_dev_mode()

    vault_path = Path(os.getenv("VAULT_PATH", "./vault"))
    log_path = vault_path / "Logs"
    logger = AuditLogger(component="skills", log_path=str(log_path))

    if dry_run:
        print(f"[DRY-RUN] {level}: {action} - {details}")
    else:
        logger.log(level, action, details, dry_run=dry_run)


def validate_path(file_path: str, vault_path: str) -> str:
    """Validate path is within vault.

    Args:
        file_path: Path to validate
        vault_path: Base vault directory

    Returns:
        Validated absolute path

    Raises:
        ValueError: If path is outside vault
    """
    check_dev_mode()

    file_abs = Path(file_path).resolve()
    vault_abs = Path(vault_path).resolve()

    try:
        file_abs.relative_to(vault_abs)
        return str(file_abs)
    except ValueError:
        raise ValueError(f"Path must be within vault: {file_path}") from None


def create_alert_file(
    file_type: str,
    source: str,
    details: dict[str, Any],
    severity: str = "critical",
) -> Path:
    """Create alert file for critical errors.

    Args:
        file_type: Type of alert (disk_full, security_incident, error_threshold)
        source: Source of the alert
        details: Error details including message and stack trace
        severity: Alert severity (critical, high, medium)

    Returns:
        Path to created alert file
    """
    check_dev_mode()

    vault_path = Path(os.getenv("VAULT_PATH", "./vault"))
    needs_action = vault_path / "Needs_Action"
    needs_action.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    alert_filename = f"ALERT_{file_type}_{timestamp}.md"
    alert_path = needs_action / alert_filename

    frontmatter = f"""---
type: alert
severity: {severity}
error_type: {file_type}
created: {datetime.now().isoformat()}
source: {source}
---

## Error Details

{details.get('error', 'Unknown error')}

## Stack Trace

{details.get('stack_trace', 'Not available')}

## Recommended Actions

- [ ] Investigate the root cause
- [ ] Resolve the issue (e.g., free disk space)
- [ ] Restart the watcher
- [ ] Move to Done when resolved
"""

    alert_path.write_text(frontmatter, encoding="utf-8")

    logger = AuditLogger(component="skills")
    logger.log(
        "CRITICAL",
        "alert_created",
        {"alert_file": str(alert_path), "error_type": file_type, "severity": severity},
    )

    return alert_path
