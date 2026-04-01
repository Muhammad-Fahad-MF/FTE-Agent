"""Send Email Skill for Gmail API integration with approval workflow.

Usage:
    from src.skills.send_email import SendEmailSkill

    skill = SendEmailSkill()

    # Send email (requires approval for new contacts)
    result = skill.send_email(
        to="user@example.com",
        subject="Test Email",
        body="This is a test email",
        attachments=[]
    )

    # Draft email (no approval required)
    draft = skill.draft_email(
        to="user@example.com",
        subject="Draft Email",
        body="This is a draft"
    )

    # Dry run mode
    skill = SendEmailSkill(dry_run=True)
    result = skill.send_email(...)  # Logs without sending
"""

import base64
import os
import sqlite3
import sys
import time
from datetime import datetime, timedelta
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import Any, Optional

import yaml
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from ..utils.circuit_breaker import get_circuit_breaker, CircuitBreakerOpenError
from .base_skill import BaseSkill
from .request_approval import RequestApprovalSkill, ApprovalRequiredError


class GmailAPIError(Exception):
    """Raised when Gmail API call fails."""
    pass


class RateLimitExceededError(Exception):
    """Raised when rate limit is exceeded."""
    pass


class SendEmailSkill(BaseSkill):
    """Skill for sending and drafting emails via Gmail API.

    Features:
    - Send/draft emails via Gmail API
    - OAuth2 authentication
    - Approval workflow for new contacts
    - Rate limiting (max 100 calls/hour)
    - Circuit breaker protection
    - --dry-run mode for safe testing
    - Attachment support

    Attributes:
        dry_run: If True, log actions without executing
        correlation_id: Unique ID for tracking action across logs
        vault_dir: Base directory for vault storage
        known_contacts: Set of known email addresses from Company_Handbook.md
    """

    def __init__(
        self,
        dry_run: bool = False,
        correlation_id: Optional[str] = None,
        vault_dir: Optional[Path] = None,
    ) -> None:
        """Initialize send email skill.

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

        # Load known contacts from Company_Handbook.md
        self.known_contacts = self._load_known_contacts()

        # Initialize rate limiting (DB in vault_dir/../data/ to match test structure)
        data_dir = self.vault_dir.parent / "data"
        data_dir.mkdir(parents=True, exist_ok=True)
        self.rate_limit_db = data_dir / "email_rate_limit.db"
        self._init_rate_limit_db()

        # Initialize circuit breaker
        self.circuit_breaker = get_circuit_breaker(
            name="gmail_api",
            failure_threshold=5,
            recovery_timeout=60,
            fallback=self._gmail_api_fallback,
        )

        # Initialize approval skill
        self.approval_skill = RequestApprovalSkill(
            dry_run=dry_run,
            correlation_id=correlation_id,
            vault_dir=vault_dir,
        )

        # Rate limit configuration
        self.max_calls_per_hour = 100
        self._load_rate_limit_config()

    def _load_known_contacts(self) -> set[str]:
        """Load known contacts from Company_Handbook.md.

        Returns:
            Set of known email addresses
        """
        handbook_path = self.vault_dir / "Company_Handbook.md"
        known_contacts = set()

        if handbook_path.exists():
            try:
                content = handbook_path.read_text(encoding="utf-8")
                # Parse [Email] section for known_contacts list
                in_email_section = False
                for line in content.split("\n"):
                    if line.strip().startswith("[Email]"):
                        in_email_section = True
                        continue
                    if in_email_section:
                        if line.strip().startswith("["):
                            break
                        if "known_contacts" in line:
                            # Parse: known_contacts = ["email1@example.com", "email2@example.com"]
                            start = line.find("[")
                            end = line.find("]")
                            if start != -1 and end != -1:
                                contacts_str = line[start + 1 : end]
                                contacts = [
                                    c.strip().strip('"').strip("'")
                                    for c in contacts_str.split(",")
                                ]
                                known_contacts.update(c for c in contacts if c)
            except Exception as e:
                self.logger.log(
                    "WARNING",
                    "known_contacts_load_failed",
                    {"error": str(e)},
                    correlation_id=self.correlation_id,
                )

        return known_contacts

    def _load_rate_limit_config(self) -> None:
        """Load rate limit configuration from Company_Handbook.md."""
        handbook_path = self.vault_dir / "Company_Handbook.md"

        if handbook_path.exists():
            try:
                content = handbook_path.read_text(encoding="utf-8")
                # Parse [Gmail] section for rate_limit_calls_per_hour
                in_gmail_section = False
                for line in content.split("\n"):
                    if line.strip().startswith("[Gmail]"):
                        in_gmail_section = True
                        continue
                    if in_gmail_section:
                        if line.strip().startswith("["):
                            break
                        if "rate_limit_calls_per_hour" in line:
                            try:
                                value = int(line.split("=")[1].strip())
                                self.max_calls_per_hour = value
                            except (ValueError, IndexError):
                                pass
            except Exception as e:
                self.logger.log(
                    "WARNING",
                    "rate_limit_config_load_failed",
                    {"error": str(e)},
                    correlation_id=self.correlation_id,
                )

    def _init_rate_limit_db(self) -> None:
        """Initialize rate limit SQLite database."""
        try:
            conn = sqlite3.connect(self.rate_limit_db)
            cursor = conn.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS rate_limits (
                    id INTEGER PRIMARY KEY CHECK (id = 1),
                    call_count INTEGER DEFAULT 0,
                    window_start TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
            )
            # Initialize with default row
            cursor.execute(
                """
                INSERT OR IGNORE INTO rate_limits (id, call_count, window_start)
                VALUES (1, 0, ?)
            """,
                (datetime.now(),),
            )
            conn.commit()
            conn.close()
        except sqlite3.Error as e:
            self.logger.log(
                "ERROR",
                "rate_limit_db_init_failed",
                {"error": str(e)},
                correlation_id=self.correlation_id,
            )

    def _check_rate_limit(self) -> bool:
        """Check if rate limit allows another API call.

        Returns:
            True if call allowed, False if rate limited

        Raises:
            RateLimitExceededError: If rate limit exceeded
        """
        try:
            conn = sqlite3.connect(self.rate_limit_db)
            cursor = conn.cursor()

            # Get current rate limit state
            cursor.execute(
                "SELECT call_count, window_start FROM rate_limits WHERE id = 1"
            )
            row = cursor.fetchone()

            if not row:
                conn.close()
                return True

            call_count, window_start_str = row
            window_start = datetime.fromisoformat(window_start_str)
            now = datetime.now()

            # Check if window has expired (1 hour)
            if now - window_start >= timedelta(hours=1):
                # Reset counter
                cursor.execute(
                    """
                    UPDATE rate_limits
                    SET call_count = 1, window_start = ?, updated_at = ?
                    WHERE id = 1
                """,
                    (now, now),
                )
                conn.commit()
                conn.close()
                return True

            # Check if under limit
            if call_count < self.max_calls_per_hour:
                # Increment counter
                cursor.execute(
                    """
                    UPDATE rate_limits
                    SET call_count = ?, updated_at = ?
                    WHERE id = 1
                """,
                    (call_count + 1, now),
                )
                conn.commit()
                conn.close()
                return True

            # Rate limit exceeded
            conn.close()
            reset_time = window_start + timedelta(hours=1)
            raise RateLimitExceededError(
                f"Gmail rate limit exceeded ({self.max_calls_per_hour} calls/hour) - "
                f"retry after {reset_time.isoformat()}"
            )

        except RateLimitExceededError:
            raise
        except Exception as e:
            self.logger.log(
                "WARNING",
                "rate_limit_check_failed",
                {"error": str(e)},
                correlation_id=self.correlation_id,
            )
            # Fail open - allow call if check fails
            return True

    def _gmail_api_fallback(self) -> dict[str, Any]:
        """Fallback function when circuit breaker is open.

        Returns:
            Error dict indicating circuit breaker state
        """
        return {
            "status": "error",
            "error": "Circuit breaker open - Gmail API calls temporarily disabled",
            "message_id": None,
            "timestamp": datetime.now().isoformat(),
            "dry_run": self.dry_run,
        }

    def _get_credentials(self) -> Optional[Credentials]:
        """Get OAuth2 credentials for Gmail API.

        Returns:
            Credentials object or None if authentication fails

        Raises:
            GmailAPIError: If credentials cannot be loaded
        """
        # Load credentials from environment
        token = os.getenv("GMAIL_OAUTH_TOKEN")
        refresh_token = os.getenv("GMAIL_OAUTH_REFRESH_TOKEN")
        client_id = os.getenv("GMAIL_CLIENT_ID")
        client_secret = os.getenv("GMAIL_CLIENT_SECRET")

        if not all([token, refresh_token, client_id, client_secret]):
            raise GmailAPIError(
                "Gmail OAuth2 credentials not found. Set GMAIL_OAUTH_TOKEN, "
                "GMAIL_OAUTH_REFRESH_TOKEN, GMAIL_CLIENT_ID, GMAIL_CLIENT_SECRET in .env"
            )

        try:
            credentials = Credentials(
                token=token,
                refresh_token=refresh_token,
                client_id=client_id,
                client_secret=client_secret,
                token_uri="https://oauth2.googleapis.com/token",
            )

            # Refresh if expired
            if credentials.expired and credentials.refresh_token:
                credentials.refresh(Request())

            return credentials

        except Exception as e:
            raise GmailAPIError(f"Failed to load Gmail OAuth2 credentials: {e}")

    def _build_gmail_service(self) -> Any:
        """Build Gmail API service.

        Returns:
            Gmail API service object

        Raises:
            GmailAPIError: If service cannot be built
        """
        try:
            credentials = self._get_credentials()
            service = build("gmail", "v1", credentials=credentials)
            return service
        except Exception as e:
            raise GmailAPIError(f"Failed to build Gmail API service: {e}")

    def _check_approval_required(
        self,
        to: list[str] | str,
        attachments: list[Any],
    ) -> tuple[bool, str]:
        """Check if email requires approval.

        Args:
            to: Recipient email address(es)
            attachments: List of attachments

        Returns:
            Tuple of (requires_approval, reason)
        """
        # Normalize to list
        recipients = [to] if isinstance(to, str) else to

        # Check for new contacts
        for recipient in recipients:
            if recipient not in self.known_contacts:
                return True, f"New contact requires approval: {recipient}"

        # Check for bulk send (>5 recipients)
        if len(recipients) > 5:
            return True, f"Bulk send requires approval ({len(recipients)} recipients)"

        # Check for large attachments (>1MB)
        for attachment in attachments:
            if hasattr(attachment, "size") and attachment.size > 1024 * 1024:
                return True, f"Large attachment requires approval ({attachment.size} bytes)"

        return False, ""

    def _create_message(
        self,
        to: str,
        subject: str,
        body: str,
        attachments: Optional[list[Path]] = None,
    ) -> dict[str, Any]:
        """Create Gmail API message.

        Args:
            to: Recipient email address
            subject: Email subject
            body: Email body
            attachments: Optional list of attachment paths

        Returns:
            Gmail API message dict
        """
        message = MIMEMultipart()
        message["to"] = to
        message["subject"] = subject
        message.attach(MIMEText(body, "plain"))

        # Add attachments
        if attachments:
            for attachment_path in attachments:
                try:
                    with open(attachment_path, "rb") as f:
                        part = MIMEBase("application", "octet-stream")
                        part.set_payload(f.read())

                    from email import encoders

                    encoders.encode_base64(part)
                    part.add_header(
                        "Content-Disposition",
                        f"attachment; filename={attachment_path.name}",
                    )
                    message.attach(part)
                except Exception as e:
                    self.logger.log(
                        "WARNING",
                        "attachment_load_failed",
                        {"file": str(attachment_path), "error": str(e)},
                        correlation_id=self.correlation_id,
                    )

        # Encode message
        raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
        return {"raw": raw}

    def send_email(
        self,
        to: str | list[str],
        subject: str,
        body: str,
        attachments: Optional[list[Path]] = None,
    ) -> dict[str, Any]:
        """Send an email via Gmail API.

        Args:
            to: Recipient email address(es)
            subject: Email subject
            body: Email body
            attachments: Optional list of attachment file paths

        Returns:
            Dict with message_id, status, timestamp, dry_run

        Raises:
            GmailAPIError: If API call fails
            RateLimitExceededError: If rate limit exceeded
            ApprovalRequiredError: If approval required (new contact, bulk, large attachment)
        """
        start_time = time.time()
        attachments = attachments or []
        recipients = [to] if isinstance(to, str) else to

        # Validate DEV_MODE
        self.validate_dev_mode()

        # Check rate limit
        try:
            self._check_rate_limit()
        except RateLimitExceededError as e:
            self.logger.log(
                "WARNING",
                "rate_limit_exceeded",
                {"error": str(e)},
                correlation_id=self.correlation_id,
            )
            self.emit_metric("email_send_errors", 1.0, {"error_type": "rate_limit"})
            return {
                "status": "error",
                "error": str(e),
                "message_id": None,
                "timestamp": datetime.now().isoformat(),
                "dry_run": self.dry_run,
            }

        # Check approval requirements
        requires_approval, approval_reason = self._check_approval_required(
            recipients, attachments
        )

        if requires_approval and not self.dry_run:
            self.logger.log(
                "INFO",
                "approval_required",
                {"reason": approval_reason, "recipients": recipients},
                correlation_id=self.correlation_id,
            )

            # Create approval request
            approval_path = self.approval_skill.create_approval_request(
                action={
                    "type": "send_email",
                    "to": recipients,
                    "subject": subject,
                    "body": body,
                    "attachments": [str(a) for a in attachments],
                },
                reason=approval_reason,
                risk_level="medium",
            )

            self.emit_metric("email_send_duration", time.time() - start_time)
            self.emit_metric(
                "email_send_count", 1.0, {"status": "pending_approval", "to_domain": recipients[0].split("@")[-1]}
            )

            raise ApprovalRequiredError(
                f"Approval required: {approval_reason}. Request created at {approval_path}"
            )

        # Dry run mode
        if self.dry_run:
            self.logger.log(
                "INFO",
                "dry_run_email",
                {
                    "to": recipients,
                    "subject": subject,
                    "body_length": len(body),
                    "attachments": len(attachments),
                },
                correlation_id=self.correlation_id,
            )
            self.emit_metric("email_send_duration", time.time() - start_time)
            self.emit_metric("email_send_count", 1.0, {"dry_run": "true", "to_domain": recipients[0].split("@")[-1]})

            return {
                "status": "dry_run",
                "message": f"DRY RUN: Would send email to {recipients}",
                "message_id": None,
                "timestamp": datetime.now().isoformat(),
                "dry_run": True,
            }

        # Send email with circuit breaker protection
        try:
            result = self.circuit_breaker.call(
                self._send_email_via_api,
                recipients,
                subject,
                body,
                attachments,
            )

            duration = time.time() - start_time
            self.emit_metric("email_send_duration", duration)
            self.emit_metric("email_send_count", 1.0, {"to_domain": recipients[0].split("@")[-1]})

            self.logger.log(
                "INFO",
                "email_sent",
                {
                    "to": recipients,
                    "subject": subject,
                    "message_id": result.get("message_id"),
                    "duration_ms": int(duration * 1000),
                },
                correlation_id=self.correlation_id,
            )

            return result

        except CircuitBreakerOpenError as e:
            self.logger.log(
                "WARNING",
                "circuit_breaker_open",
                {"error": str(e)},
                correlation_id=self.correlation_id,
            )
            self.emit_metric("email_send_errors", 1.0, {"error_type": "circuit_breaker"})
            return {
                "status": "error",
                "error": str(e),
                "message_id": None,
                "timestamp": datetime.now().isoformat(),
                "dry_run": self.dry_run,
            }

        except GmailAPIError as e:
            self.logger.log(
                "ERROR",
                "email_send_failed",
                {"to": recipients, "subject": subject, "error": str(e)},
                correlation_id=self.correlation_id,
            )
            self.emit_metric("email_send_errors", 1.0, {"error_type": "gmail_api"})
            raise

    def _send_email_via_api(
        self,
        recipients: list[str],
        subject: str,
        body: str,
        attachments: list[Path],
    ) -> dict[str, Any]:
        """Send email via Gmail API (internal method with circuit breaker protection).

        Args:
            recipients: List of recipient email addresses
            subject: Email subject
            body: Email body
            attachments: List of attachment file paths

        Returns:
            Dict with message_id, status, timestamp

        Raises:
            GmailAPIError: If API call fails
        """
        try:
            service = self._build_gmail_service()
            to = ", ".join(recipients)
            message = self._create_message(to, subject, body, attachments)

            # Send message
            sent_message = (
                service.users()
                .messages()
                .send(userId="me", body=message)
                .execute()
            )

            return {
                "status": "sent",
                "message_id": sent_message.get("id"),
                "timestamp": datetime.now().isoformat(),
                "dry_run": False,
            }

        except HttpError as e:
            raise GmailAPIError(f"Gmail API error: {e}")
        except Exception as e:
            raise GmailAPIError(f"Failed to send email: {e}")

    def draft_email(
        self,
        to: str | list[str],
        subject: str,
        body: str,
        attachments: Optional[list[Path]] = None,
    ) -> dict[str, Any]:
        """Create a draft email (no approval required).

        Args:
            to: Recipient email address(es)
            subject: Email subject
            body: Email body
            attachments: Optional list of attachment file paths

        Returns:
            Dict with message_id, status, timestamp, dry_run

        Raises:
            GmailAPIError: If API call fails
        """
        start_time = time.time()
        attachments = attachments or []
        recipients = [to] if isinstance(to, str) else to

        # Validate DEV_MODE
        self.validate_dev_mode()

        # Check rate limit
        try:
            self._check_rate_limit()
        except RateLimitExceededError as e:
            self.logger.log(
                "WARNING",
                "rate_limit_exceeded",
                {"error": str(e)},
                correlation_id=self.correlation_id,
            )
            self.emit_metric("email_send_errors", 1.0, {"error_type": "rate_limit"})
            return {
                "status": "error",
                "error": str(e),
                "message_id": None,
                "timestamp": datetime.now().isoformat(),
                "dry_run": self.dry_run,
            }

        # Dry run mode
        if self.dry_run:
            self.logger.log(
                "INFO",
                "dry_run_draft",
                {
                    "to": recipients,
                    "subject": subject,
                    "body_length": len(body),
                },
                correlation_id=self.correlation_id,
            )
            self.emit_metric("email_send_duration", time.time() - start_time)
            self.emit_metric("email_send_count", 1.0, {"dry_run": "true", "type": "draft"})

            return {
                "status": "dry_run",
                "message": f"DRY RUN: Would create draft email to {recipients}",
                "message_id": None,
                "timestamp": datetime.now().isoformat(),
                "dry_run": True,
            }

        # Create draft with circuit breaker protection
        try:
            result = self.circuit_breaker.call(
                self._draft_email_via_api,
                recipients,
                subject,
                body,
                attachments,
            )

            duration = time.time() - start_time
            self.emit_metric("email_send_duration", duration)
            self.emit_metric("email_send_count", 1.0, {"type": "draft", "to_domain": recipients[0].split("@")[-1]})

            self.logger.log(
                "INFO",
                "draft_created",
                {
                    "to": recipients,
                    "subject": subject,
                    "message_id": result.get("message_id"),
                    "duration_ms": int(duration * 1000),
                },
                correlation_id=self.correlation_id,
            )

            return result

        except CircuitBreakerOpenError as e:
            self.logger.log(
                "WARNING",
                "circuit_breaker_open",
                {"error": str(e)},
                correlation_id=self.correlation_id,
            )
            self.emit_metric("email_send_errors", 1.0, {"error_type": "circuit_breaker"})
            return {
                "status": "error",
                "error": str(e),
                "message_id": None,
                "timestamp": datetime.now().isoformat(),
                "dry_run": self.dry_run,
            }

        except GmailAPIError as e:
            self.logger.log(
                "ERROR",
                "draft_creation_failed",
                {"to": recipients, "subject": subject, "error": str(e)},
                correlation_id=self.correlation_id,
            )
            self.emit_metric("email_send_errors", 1.0, {"error_type": "gmail_api"})
            raise

    def _draft_email_via_api(
        self,
        recipients: list[str],
        subject: str,
        body: str,
        attachments: list[Path],
    ) -> dict[str, Any]:
        """Create draft email via Gmail API (internal method).

        Args:
            recipients: List of recipient email addresses
            subject: Email subject
            body: Email body
            attachments: List of attachment file paths

        Returns:
            Dict with message_id, status, timestamp

        Raises:
            GmailAPIError: If API call fails
        """
        try:
            service = self._build_gmail_service()
            to = ", ".join(recipients)
            message = self._create_message(to, subject, body, attachments)

            # Create draft
            draft = (
                service.users()
                .drafts()
                .create(userId="me", body={"message": message})
                .execute()
            )

            return {
                "status": "draft",
                "message_id": draft.get("message", {}).get("id"),
                "draft_id": draft.get("id"),
                "timestamp": datetime.now().isoformat(),
                "dry_run": False,
            }

        except HttpError as e:
            raise GmailAPIError(f"Gmail API error: {e}")
        except Exception as e:
            raise GmailAPIError(f"Failed to create draft: {e}")

    def execute(
        self,
        to: str | list[str],
        subject: str,
        body: str,
        attachments: Optional[list[Path]] = None,
        draft: bool = False,
    ) -> dict[str, Any]:
        """Execute the send email skill.

        Args:
            to: Recipient email address(es)
            subject: Email subject
            body: Email body
            attachments: Optional list of attachment file paths
            draft: If True, create draft instead of sending

        Returns:
            Dict with message_id, status, timestamp, dry_run
        """
        if draft:
            return self.draft_email(to, subject, body, attachments)
        return self.send_email(to, subject, body, attachments)
