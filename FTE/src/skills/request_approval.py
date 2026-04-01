"""Request Approval Skill for creating and managing HITL approval requests.

Usage:
    from src.skills.request_approval import RequestApprovalSkill

    skill = RequestApprovalSkill()
    
    # Create approval request
    approval_path = skill.create_approval_request(
        action={"type": "email", "to": "user@example.com", "subject": "Test"},
        reason="New contact requires approval",
        risk_level="medium"
    )
    
    # Check for expired approvals
    expired = skill.check_expiry()
    if expired:
        skill.flag_expired(expired)
"""

import os
import sys
import time
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Optional

import yaml

from .base_skill import BaseSkill

# Cross-platform file locking
if sys.platform == "win32":
    import msvcrt

    def _lock_file_windows(f):
        """Lock file on Windows."""
        try:
            msvcrt.locking(f.fileno(), msvcrt.LK_LOCK, 1)
            return True
        except OSError:
            return False

    def _unlock_file_windows(f):
        """Unlock file on Windows."""
        try:
            f.seek(0)
            msvcrt.locking(f.fileno(), msvcrt.LK_UNLCK, 1)
        except OSError:
            pass
else:
    import fcntl

    def _lock_file_unix(f):
        """Lock file on Unix."""
        try:
            fcntl.flock(f.fileno(), fcntl.LOCK_EX)
            return True
        except OSError:
            return False

    def _unlock_file_unix(f):
        """Unlock file on Unix."""
        try:
            fcntl.flock(f.fileno(), fcntl.LOCK_UN)
        except OSError:
            pass


class ApprovalRequiredError(Exception):
    """Raised when approval is required for an action."""

    pass


class ApprovalExpiredError(Exception):
    """Raised when an approval request has expired."""

    pass


class RequestApprovalSkill(BaseSkill):
    """Skill for creating and managing Human-in-the-Loop approval requests.

    Creates approval request files in vault/Pending_Approval/ with:
    - YAML frontmatter with 8 required fields
    - 24-hour expiry from creation
    - Risk level assessment
    - Clear approval/rejection instructions

    Attributes:
        vault_dir: Base directory for vault storage
        pending_approval_dir: Directory for pending approvals
        dashboard_path: Path to Dashboard.md
        expiry_hours: Hours until approval expires (default: 24)
    """

    VALID_STATUSES = ["pending", "approved", "rejected", "expired"]
    VALID_RISK_LEVELS = ["low", "medium", "high", "critical"]

    def __init__(
        self,
        dry_run: bool = False,
        correlation_id: Optional[str] = None,
        vault_dir: Optional[Path] = None,
    ) -> None:
        """Initialize request approval skill.

        Args:
            dry_run: If True, log actions without executing
            correlation_id: Unique ID for tracking
            vault_dir: Base vault directory (default: FTE/vault)
        """
        super().__init__(dry_run=dry_run, correlation_id=correlation_id)

        # Resolve vault directory
        if vault_dir is None:
            vault_dir = Path(__file__).parent.parent.parent / "vault"
        self.vault_dir = Path(vault_dir).resolve()

        self.pending_approval_dir = self.vault_dir / "Pending_Approval"
        self.approved_dir = self.vault_dir / "Approved"
        self.rejected_dir = self.vault_dir / "Rejected"
        self.dashboard_path = self.vault_dir / "Dashboard.md"
        self.expiry_hours = 24

        # Ensure directories exist
        self._ensure_directories()

    def _ensure_directories(self) -> None:
        """Create necessary directories if they don't exist."""
        for directory in [
            self.pending_approval_dir,
            self.approved_dir,
            self.rejected_dir,
        ]:
            directory.mkdir(parents=True, exist_ok=True)

    def _acquire_lock(self, file_path: Path):
        """Acquire file lock for concurrent write safety."""
        try:
            f = open(file_path, "a")
            if sys.platform == "win32":
                _lock_file_windows(f)
            else:
                _lock_file_unix(f)
            return f
        except Exception as e:
            self.logger.log(
                "WARNING",
                "lock_acquisition_failed",
                {"file": str(file_path), "error": str(e)},
                correlation_id=self.correlation_id,
            )
            return None

    def _release_lock(self, lock_file) -> None:
        """Release file lock."""
        if lock_file:
            try:
                if sys.platform == "win32":
                    _unlock_file_windows(lock_file)
                else:
                    _unlock_file_unix(lock_file)
                lock_file.close()
            except Exception as e:
                self.logger.log(
                    "WARNING",
                    "lock_release_failed",
                    {"error": str(e)},
                    correlation_id=self.correlation_id,
                )

    def _load_template(self) -> str:
        """Load approval request template.

        Returns:
            Template content as string
        """
        template_path = self.vault_dir / "Templates" / "approval_request_template.md"

        if template_path.exists():
            return template_path.read_text(encoding="utf-8")

        # Fallback to embedded template
        return """---
type: approval_request
action: {{ACTION_TYPE}}
action_details: {{ACTION_DETAILS}}
created: {{CREATED_DATE}}
expires: {{EXPIRES_DATE}}
status: pending
risk_level: {{RISK_LEVEL}}
reason: {{REASON}}
---

# Approval Request: {{ACTION_TYPE}}

## Request Details

| Field | Value |
|-------|-------|
| **Action Type** | {{ACTION_TYPE}} |
| **Created** | {{CREATED_DATE}} |
| **Expires** | {{EXPIRES_DATE}} (24 hours from creation) |
| **Risk Level** | {{RISK_LEVEL}} |
| **Status** | ⏳ Pending |

## Reason for Approval

{{REASON}}

## Action Details

{{ACTION_DETAILS}}

## Decision

**Instructions:**
- To **APPROVE**: Change `status: pending` to `status: approved` and save
- To **REJECT**: Change `status: pending` to `status: rejected` and add reason below
- Approval expires after 24 hours (see `expires` field)

---

### Approval Record

| Decision | Date | Authorized By | Notes |
|----------|------|---------------|-------|
| ⏳ Pending | - | - | Awaiting user decision |

**Rejection Reason** (if applicable):

{{REJECTION_REASON}}

---

**Metadata:**
- File: `vault/Pending_Approval/APPROVAL_{{TIMESTAMP}}.md`
- Correlation ID: `{{CORRELATION_ID}}`
- Source: {{SOURCE_FILE}}
"""

    def _generate_filename(self, action_type: str) -> str:
        """Generate unique filename for approval request.

        Args:
            action_type: Type of action requiring approval

        Returns:
            Filename in format APPROVAL_<type>_<timestamp>_<uuid>.md
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        sanitized_type = "".join(
            c for c in action_type.replace(" ", "_") if c.isalnum() or c == "_"
        ).upper()
        return f"APPROVAL_{sanitized_type}_{timestamp}_{unique_id}.md"

    def create_approval_request(
        self,
        action: dict[str, Any],
        reason: str,
        risk_level: str = "medium",
        source_file: Optional[Path] = None,
    ) -> Path:
        """Create an approval request file.

        Args:
            action: Dict with action details (type, to, subject, etc.)
            reason: Reason why approval is required
            risk_level: One of low, medium, high, critical
            source_file: Optional path to source action file

        Returns:
            Path to created approval request file

        Raises:
            ValueError: If risk_level is invalid
            RuntimeError: If file creation fails
        """
        start_time = time.time()

        # Validate risk level
        if risk_level not in self.VALID_RISK_LEVELS:
            raise ValueError(
                f"Invalid risk_level: {risk_level}. Must be one of {self.VALID_RISK_LEVELS}"
            )

        # Get action type
        action_type = action.get("type", "unknown")

        # Generate timestamps
        created = datetime.now()
        expires = created + timedelta(hours=self.expiry_hours)
        created_iso = created.isoformat()
        expires_iso = expires.isoformat()
        timestamp = created.strftime("%Y%m%d_%H%M%S")

        # Generate YAML frontmatter
        frontmatter = {
            "type": "approval_request",
            "action": action_type,
            "action_details": action,
            "created": created_iso,
            "expires": expires_iso,
            "status": "pending",
            "risk_level": risk_level,
            "reason": reason,
        }

        # Generate content
        template = self._load_template()
        action_details_yaml = yaml.dump(action, default_flow_style=False, indent=2)

        content = template.replace("{{ACTION_TYPE}}", action_type).replace(
            "{{ACTION_DETAILS}}", action_details_yaml
        ).replace(
            "{{CREATED_DATE}}", created_iso
        ).replace(
            "{{EXPIRES_DATE}}", expires_iso
        ).replace(
            "{{RISK_LEVEL}}", risk_level
        ).replace(
            "{{REASON}}", reason
        ).replace(
            "{{TIMESTAMP}}", timestamp
        ).replace(
            "{{CORRELATION_ID}}", self.correlation_id
        ).replace(
            "{{SOURCE_FILE}}", str(source_file) if source_file else "N/A"
        ).replace(
            "{{REJECTION_REASON}}", ""
        )

        # Generate filename and path
        filename = self._generate_filename(action_type)
        approval_path = self.pending_approval_dir / filename

        if self.dry_run:
            self.logger.log(
                "INFO",
                "dry_run_approval_request",
                {
                    "filename": filename,
                    "action_type": action_type,
                    "risk_level": risk_level,
                    "expires": expires_iso,
                },
                correlation_id=self.correlation_id,
            )
            self.emit_metric("approval_request_duration", time.time() - start_time)
            self.emit_metric("approval_request_count", 1.0, {"dry_run": "true"})
            return approval_path

        # Write file with locking
        lock_file = None
        try:
            # Ensure directory exists
            self.pending_approval_dir.mkdir(parents=True, exist_ok=True)

            # Write file
            approval_path.write_text(content, encoding="utf-8")

            self.logger.log(
                "INFO",
                "approval_request_created",
                {
                    "file": str(approval_path),
                    "action_type": action_type,
                    "risk_level": risk_level,
                    "expires": expires_iso,
                },
                correlation_id=self.correlation_id,
            )

            # Emit metrics
            duration = time.time() - start_time
            self.emit_metric("approval_request_duration", duration)
            self.emit_metric("approval_request_count", 1.0, {"action_type": action_type})

            return approval_path

        except Exception as e:
            self.logger.log(
                "ERROR",
                "approval_request_creation_failed",
                {"file": str(approval_path), "error": str(e)},
                correlation_id=self.correlation_id,
            )
            self.emit_metric("approval_request_errors", 1.0)
            raise RuntimeError(f"Failed to create approval request: {e}") from e

    def check_expiry(self) -> list[Path]:
        """Check for expired approval requests.

        Returns:
            List of paths to expired approval files
        """
        start_time = time.time()
        expired_files = []
        now = datetime.now()

        try:
            # Scan pending approvals
            for approval_file in self.pending_approval_dir.glob("APPROVAL_*.md"):
                try:
                    content = approval_file.read_text(encoding="utf-8")
                    # Parse YAML frontmatter
                    match = content.split("---", 2)
                    if len(match) < 2:
                        continue

                    frontmatter = yaml.safe_load(match[1])
                    expires_str = frontmatter.get("expires")

                    if expires_str:
                        expires = datetime.fromisoformat(expires_str)
                        if now > expires:
                            expired_files.append(approval_file)

                except Exception as e:
                    self.logger.log(
                        "WARNING",
                        "expiry_check_failed",
                        {"file": str(approval_file), "error": str(e)},
                        correlation_id=self.correlation_id,
                    )

            duration = time.time() - start_time
            self.emit_metric("approval_expiry_check_duration", duration)
            self.emit_metric(
                "approval_expired_count", float(len(expired_files))
            )

            if expired_files:
                self.logger.log(
                    "WARNING",
                    "expired_approvals_found",
                    {"count": len(expired_files), "files": [str(f) for f in expired_files]},
                    correlation_id=self.correlation_id,
                )

            return expired_files

        except Exception as e:
            self.logger.log(
                "ERROR",
                "expiry_check_failed",
                {"error": str(e)},
                correlation_id=self.correlation_id,
            )
            self.emit_metric("approval_expiry_check_errors", 1.0)
            return []

    def flag_expired(self, expired_files: list[Path]) -> None:
        """Flag expired approvals in Dashboard.md.

        Args:
            expired_files: List of expired approval file paths
        """
        if not expired_files:
            return

        start_time = time.time()

        # Update status in expired files
        for approval_file in expired_files:
            try:
                content = approval_file.read_text(encoding="utf-8")
                
                # Update frontmatter status to expired
                match = content.split("---", 2)
                if len(match) >= 2:
                    frontmatter = yaml.safe_load(match[1])
                    frontmatter["status"] = "expired"
                    
                    # Rebuild content with updated frontmatter
                    new_frontmatter = yaml.dump(frontmatter, default_flow_style=False, indent=2)
                    content = f"---\n{new_frontmatter}---\n{match[2] if len(match) > 2 else ''}"
                    
                    approval_file.write_text(content, encoding="utf-8")
                    
                    self.logger.log(
                        "WARNING",
                        "approval_flagged_expired",
                        {"file": str(approval_file)},
                        correlation_id=self.correlation_id,
                    )

            except Exception as e:
                self.logger.log(
                    "ERROR",
                    "approval_flag_expired_failed",
                    {"file": str(approval_file), "error": str(e)},
                    correlation_id=self.correlation_id,
                )

        # Update Dashboard.md
        self._update_dashboard_expired_alert(expired_files)

        duration = time.time() - start_time
        self.emit_metric("approval_flag_expired_duration", duration)

    def _update_dashboard_expired_alert(self, expired_files: list[Path]) -> None:
        """Update Dashboard.md with expired approval alerts.

        Args:
            expired_files: List of expired approval file paths
        """
        dashboard_alert = f"\n\n## ⚠️ EXPIRED APPROVALS ALERT - {datetime.now().isoformat()}\n\n"
        dashboard_alert += f"**{len(expired_files)} approval(s) have expired:**\n\n"

        for approval_file in expired_files:
            dashboard_alert += f"- `{approval_file.name}`\n"

        dashboard_alert += "\n**Action Required:** Please review and process these approvals.\n"

        try:
            if self.dashboard_path.exists():
                content = self.dashboard_path.read_text(encoding="utf-8")
                # Append alert
                content += dashboard_alert
                self.dashboard_path.write_text(content, encoding="utf-8")
            else:
                # Create dashboard with alert
                self.dashboard_path.write_text(
                    f"# FTE-Agent Dashboard\n{dashboard_alert}", encoding="utf-8"
                )

            self.logger.log(
                "WARNING",
                "dashboard_updated_expired_approvals",
                {"count": len(expired_files)},
                correlation_id=self.correlation_id,
            )

        except Exception as e:
            self.logger.log(
                "ERROR",
                "dashboard_update_failed",
                {"error": str(e)},
                correlation_id=self.correlation_id,
            )

    def get_approval_status(self, approval_file: Path) -> Optional[str]:
        """Get the status of an approval request.

        Args:
            approval_file: Path to approval file

        Returns:
            Status string (pending/approved/rejected/expired) or None if not found
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
                "approval_status_check_failed",
                {"file": str(approval_file), "error": str(e)},
                correlation_id=self.correlation_id,
            )
            return None

    def execute(
        self,
        action: dict[str, Any],
        reason: str,
        risk_level: str = "medium",
        source_file: Optional[Path] = None,
    ) -> Path:
        """Execute the approval request skill.

        Args:
            action: Dict with action details
            reason: Reason why approval is required
            risk_level: One of low, medium, high, critical
            source_file: Optional path to source action file

        Returns:
            Path to created approval request file
        """
        return self.create_approval_request(
            action=action, reason=reason, risk_level=risk_level, source_file=source_file
        )
