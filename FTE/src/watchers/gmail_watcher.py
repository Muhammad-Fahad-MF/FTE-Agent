"""
Gmail Watcher - Monitor Gmail for unread/important emails.

This module implements a Gmail watcher that:
- Monitors Gmail every 2 minutes (configurable)
- Creates action files for new unread/important emails
- Tracks processed message IDs to avoid duplicates
- Implements circuit breaker for API resilience
- Emits metrics for monitoring
- Handles OAuth2 session expiry
- Enforces rate limiting

Usage:
    watcher = GmailWatcher(vault_path="vault/", dry_run=False)
    watcher.run()
"""

import os
import re
import sqlite3
import threading
import time
import urllib.parse
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Optional

from google.auth.exceptions import RefreshError
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from ..audit_logger import AuditLogger
from ..base_watcher import BaseWatcher
from ..metrics.collector import MetricsCollector, get_metrics_collector
from ..utils.circuit_breaker import (
    CircuitBreakerOpenError,
    PersistentCircuitBreaker,
    get_circuit_breaker,
)


class GmailSessionExpiredError(Exception):
    """Raised when Gmail OAuth2 session is expired."""

    pass


class GmailRateLimitExceededError(Exception):
    """Raised when Gmail API rate limit is exceeded."""

    pass


class GmailWatcher(BaseWatcher):
    """
    Gmail watcher for monitoring unread/important emails.

    Attributes:
        vault_path: Root path of the vault directory.
        dry_run: If True, log actions without creating files.
        interval: Check interval in seconds (default: 120).
    """

    def __init__(
        self,
        vault_path: str,
        dry_run: bool = False,
        interval: int = 120,
    ) -> None:
        """
        Initialize Gmail watcher.

        Args:
            vault_path: Root path of the vault directory.
            dry_run: If True, log actions without creating files.
            interval: Check interval in seconds (default: 120).
        """
        super().__init__(vault_path, dry_run, interval)

        # Ensure data directory exists
        self.data_path = self.vault_path.parent / "data"
        self.data_path.mkdir(parents=True, exist_ok=True)

        # Initialize metrics collector
        metrics_db_path = str(self.data_path / "metrics.db")
        self.metrics: MetricsCollector = get_metrics_collector(db_path=metrics_db_path)

        # Initialize circuit breaker
        circuit_breaker_db_path = str(self.data_path / "circuit_breakers.db")
        self.circuit_breaker: PersistentCircuitBreaker = get_circuit_breaker(
            name="gmail_api",
            failure_threshold=5,
            recovery_timeout=60,
            fallback=self._gmail_api_fallback,
            db_path=circuit_breaker_db_path,
        )

        # Rate limiting
        self._rate_limit_lock = threading.Lock()
        self._rate_limit_calls: list[datetime] = []
        self._rate_limit_max = 100  # Default: 100 calls/hour
        self._rate_limit_window = 3600  # 1 hour in seconds

        # Load rate limit from Company_Handbook.md if exists
        self._load_rate_limit_config()

        # Initialize processed emails database
        self._init_processed_emails_db()

        self.logger.info(
            "gmail_watcher_initialized",
            {
                "vault_path": str(self.vault_path),
                "dry_run": self.dry_run,
                "interval": interval,
                "rate_limit": self._rate_limit_max,
            },
        )

    def _load_rate_limit_config(self) -> None:
        """Load rate limit configuration from Company_Handbook.md."""
        handbook_path = self.vault_path / "Company_Handbook.md"
        if handbook_path.exists():
            try:
                content = handbook_path.read_text(encoding="utf-8")
                # Look for [Gmail] section and rate_limit_calls_per_hour
                match = re.search(
                    r"\[Gmail\].*?rate_limit_calls_per_hour\s*=\s*(\d+)",
                    content,
                    re.DOTALL | re.IGNORECASE,
                )
                if match:
                    self._rate_limit_max = int(match.group(1))
                    self.logger.info(
                        "gmail_rate_limit_loaded",
                        {"rate_limit": self._rate_limit_max},
                    )
            except Exception as e:
                self.logger.log(
                    "WARNING",
                    "gmail_rate_limit_load_failed",
                    {"error": str(e)},
                )

    def _init_processed_emails_db(self) -> None:
        """Initialize SQLite database for tracking processed emails."""
        db_path = self.vault_path.parent / "data" / "processed_emails.db"
        db_path.parent.mkdir(parents=True, exist_ok=True)

        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS processed_emails (
                message_id TEXT PRIMARY KEY,
                processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                action_file TEXT
            )
        """
        )
        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_processed_at ON processed_emails(processed_at)
        """
        )
        conn.commit()
        conn.close()

        self._db_path = db_path
        self.logger.info("gmail_processed_emails_db_initialized", {"db_path": str(db_path)})

    def _get_db_connection(self) -> sqlite3.Connection:
        """Get database connection."""
        return sqlite3.connect(str(self._db_path))

    def _is_processed(self, message_id: str) -> bool:
        """
        Check if message has already been processed.

        Args:
            message_id: Gmail message ID.

        Returns:
            True if already processed, False otherwise.
        """
        try:
            conn = self._get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT 1 FROM processed_emails WHERE message_id = ?",
                (message_id,),
            )
            result = cursor.fetchone()
            conn.close()
            return result is not None
        except sqlite3.Error as e:
            self.logger.error(
                "gmail_check_processed_failed",
                {"message_id": message_id, "error": str(e)},
            )
            return False

    def _track_processed(self, message_id: str, action_file: Optional[str] = None) -> None:
        """
        Track a processed message.

        Args:
            message_id: Gmail message ID.
            action_file: Path to created action file (optional).
        """
        try:
            conn = self._get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT OR REPLACE INTO processed_emails (message_id, processed_at, action_file)
                VALUES (?, ?, ?)
            """,
                (message_id, datetime.now(), action_file),
            )
            conn.commit()
            conn.close()
        except sqlite3.Error as e:
            self.logger.error(
                "gmail_track_processed_failed",
                {"message_id": message_id, "error": str(e)},
            )

    def _cleanup_old_processed_ids(self, retention_days: int = 30) -> None:
        """
        Clean up old processed IDs.

        Args:
            retention_days: Number of days to retain (default: 30).
        """
        try:
            conn = self._get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                """
                DELETE FROM processed_emails
                WHERE processed_at < datetime('now', ?)
            """,
                (f"-{retention_days} days",),
            )
            conn.commit()
            deleted = cursor.rowcount
            conn.close()

            if deleted > 0:
                self.logger.info(
                    "gmail_processed_ids_cleaned",
                    {"deleted_count": deleted, "retention_days": retention_days},
                )
        except sqlite3.Error as e:
            self.logger.error(
                "gmail_cleanup_failed",
                {"error": str(e)},
            )

    def _check_rate_limit(self) -> bool:
        """
        Check if rate limit allows API call.

        Returns:
            True if call is allowed, False if rate limited.
        """
        with self._rate_limit_lock:
            now = datetime.now()
            window_start = now - timedelta(seconds=self._rate_limit_window)

            # Remove old calls outside the window
            self._rate_limit_calls = [
                call_time for call_time in self._rate_limit_calls if call_time > window_start
            ]

            # Check if under limit
            if len(self._rate_limit_calls) >= self._rate_limit_max:
                return False

            # Record this call
            self._rate_limit_calls.append(now)
            return True

    def _get_credentials(self) -> Optional[Credentials]:
        """
        Load OAuth2 credentials from environment.

        Returns:
            Credentials object or None if not configured.
        """
        token = os.environ.get("GMAIL_OAUTH_TOKEN")
        if not token:
            self.logger.log("WARNING", "gmail_oauth_token_missing", {"env_var": "GMAIL_OAUTH_TOKEN"})
            return None

        try:
            # Token should be JSON as stored by google.oauth2
            import json

            creds_data = json.loads(token)
            credentials = Credentials(
                token=creds_data.get("token"),
                refresh_token=creds_data.get("refresh_token"),
                token_uri=creds_data.get("token_uri"),
                client_id=creds_data.get("client_id"),
                client_secret=creds_data.get("client_secret"),
                scopes=creds_data.get("scopes", ["https://www.googleapis.com/auth/gmail.readonly"]),
            )

            # Refresh if expired
            if credentials.expired and credentials.refresh_token:
                credentials.refresh(Request())

            return credentials
        except Exception as e:
            self.logger.error(
                "gmail_credentials_load_failed",
                {"error": str(e)},
            )
            return None

    def _gmail_api_fallback(self) -> list[dict[str, Any]]:
        """Fallback function when circuit breaker is open."""
        self.logger.log(
            "WARNING",
            "gmail_api_circuit_open",
            {"message": "Using fallback - returning empty list"},
        )
        return []

    def _check_for_updates_impl(self) -> list[dict[str, Any]]:
        """
        Implementation of check_for_updates.

        Returns:
            List of message metadata dicts.
        """
        start_time = time.perf_counter()
        correlation_id = str(time.time())

        try:
            # Check rate limit
            if not self._check_rate_limit():
                self.logger.log(
                    "WARNING",
                    "gmail_rate_limit_exceeded",
                    {"rate_limit": self._rate_limit_max},
                )
                self.metrics.increment_counter(
                    "gmail_watcher_rate_limit_hits",
                    tags={"correlation_id": correlation_id},
                )
                return []

            # Get credentials
            credentials = self._get_credentials()
            if not credentials:
                self.logger.log("WARNING", "gmail_credentials_not_available", {})
                return []

            # Build Gmail API client
            service = build("gmail", "v1", credentials=credentials)

            # Query for unread and important messages
            query = "is:unread is:important"
            response = service.users().messages().list(userId="me", q=query, maxResults=10).execute()

            messages = response.get("messages", [])
            if not messages:
                self.logger.info(
                    "gmail_no_new_messages",
                    {"query": query},
                )
                return []

            # Fetch full message details
            result = []
            for msg in messages:
                msg_id = msg["id"]

                # Skip if already processed
                if self._is_processed(msg_id):
                    self.logger.info(
                        "gmail_message_already_processed",
                        {"message_id": msg_id},
                    )
                    continue

                # Get full message
                full_msg = service.users().messages().get(userId="me", id=msg_id, format="metadata").execute()

                # Extract headers
                headers = full_msg.get("payload", {}).get("headers", [])
                metadata = {h["name"]: h["value"] for h in headers}

                message_data = {
                    "message_id": msg_id,
                    "thread_id": full_msg.get("threadId"),
                    "from": metadata.get("From", ""),
                    "to": metadata.get("To", ""),
                    "subject": metadata.get("Subject", ""),
                    "date": metadata.get("Date", ""),
                    "snippet": full_msg.get("snippet", ""),
                }

                result.append(message_data)

            # Record metrics
            duration = time.perf_counter() - start_time
            self.metrics.record_histogram(
                "gmail_watcher_check_duration",
                duration,
                tags={"correlation_id": correlation_id},
            )
            self.metrics.increment_counter(
                "gmail_watcher_items_processed",
                len(result),
                tags={"correlation_id": correlation_id},
            )

            self.logger.info(
                "gmail_check_completed",
                {
                    "messages_found": len(result),
                    "duration_seconds": duration,
                },
            )

            return result

        except HttpError as e:
            if e.resp.status == 401:
                # OAuth2 token expired
                self.logger.log(
                    "WARNING",
                    "gmail_oauth_token_expired",
                    {"status": e.resp.status},
                )
                raise GmailSessionExpiredError(f"Gmail OAuth2 token expired: {e}")

            if e.resp.status == 429:
                # Rate limited
                self.logger.log(
                    "WARNING",
                    "gmail_rate_limited_by_api",
                    {"status": e.resp.status},
                )
                raise GmailRateLimitExceededError(f"Gmail API rate limit exceeded: {e}")

            # Other HTTP errors
            self.logger.error(
                "gmail_http_error",
                {"status": e.resp.status, "error": str(e)},
            )
            self.metrics.increment_counter(
                "gmail_watcher_errors",
                tags={"correlation_id": correlation_id, "error_type": "http_error"},
            )
            raise

        except RefreshError as e:
            self.logger.log(
                "WARNING",
                "gmail_token_refresh_failed",
                {"error": str(e)},
            )
            raise GmailSessionExpiredError(f"Gmail token refresh failed: {e}")

        except Exception as e:
            self.logger.error(
                "gmail_check_failed",
                {"error": str(e)},
            )
            self.metrics.increment_counter(
                "gmail_watcher_errors",
                tags={"correlation_id": correlation_id, "error_type": "general"},
            )
            raise

    def check_for_updates(self) -> list[dict[str, Any]]:
        """
        Check for new unread/important Gmail messages.

        Wraps the implementation with circuit breaker protection.

        Returns:
            List of message metadata dicts.
        """
        try:
            return self.circuit_breaker.call(self._check_for_updates_impl)
        except CircuitBreakerOpenError:
            self.logger.log(
                "WARNING",
                "gmail_circuit_breaker_open",
                {"message": "Skipping Gmail API call"},
            )
            return []
        except GmailSessionExpiredError as e:
            self.logger.log(
                "WARNING",
                "gmail_session_expired",
                {"error": str(e)},
            )
            # Update Dashboard.md with expiry alert
            self._update_dashboard_session_expiry("Gmail")
            return []
        except GmailRateLimitExceededError:
            return []

    def _update_dashboard_session_expiry(self, service: str) -> None:
        """
        Update Dashboard.md with session expiry alert.

        Args:
            service: Service name (Gmail, WhatsApp, etc.).
        """
        dashboard_path = self.vault_path / "Dashboard.md"
        try:
            if dashboard_path.exists():
                content = dashboard_path.read_text(encoding="utf-8")
                alert = f"\n## ⚠️ Session Expired: {service}\n{service} OAuth2 token expired. Please re-authenticate.\n"

                if f"Session Expired: {service}" not in content:
                    content += alert
                    if not self.dry_run:
                        dashboard_path.write_text(content, encoding="utf-8")

                self.logger.info(
                    "dashboard_updated_session_expiry",
                    {"service": service},
                )
        except Exception as e:
            self.logger.error(
                "dashboard_update_failed",
                {"service": service, "error": str(e)},
            )

    def create_action_file(self, message_data: dict[str, Any]) -> Path:
        """
        Create action file for Gmail message.

        Args:
            message_data: Message metadata dict with keys:
                - message_id
                - from
                - to
                - subject
                - date
                - snippet

        Returns:
            Path to created action file.
        """
        message_id = message_data.get("message_id", "unknown")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Sanitize message_id for filename
        safe_id = urllib.parse.quote(message_id, safe="")[:64]  # Limit length
        action_filename = f"EMAIL_{safe_id}_{timestamp}.md"

        needs_action_dir = self.vault_path / "Needs_Action"
        needs_action_dir.mkdir(parents=True, exist_ok=True)
        action_path = needs_action_dir / action_filename

        # Create YAML frontmatter per spec.md Appendix A
        frontmatter = f"""---
type: email
from: {message_data.get("from", "")}
to: {message_data.get("to", "")}
subject: {message_data.get("subject", "")}
received: {message_data.get("date", "")}
priority: high
status: pending
message_id: {message_id}
created: {datetime.now().isoformat()}
---

## Email Content

**From:** {message_data.get("from", "")}
**To:** {message_data.get("to", "")}
**Subject:** {message_data.get("subject", "")}
**Date:** {message_data.get("date", "")}

---

## Snippet

{message_data.get("snippet", "")}

---

## Suggested Actions

- [ ] Read and respond to email
- [ ] Archive email after processing
- [ ] Create follow-up task if needed

---

## Notes

"""

        if self.dry_run:
            self.logger.log(
                "INFO",
                "action_file_dry_run",
                {
                    "would_create": str(action_path),
                    "message_id": message_id,
                },
                dry_run=True,
            )
            return action_path

        # Write action file
        action_path.write_text(frontmatter, encoding="utf-8")

        # Track as processed
        self._track_processed(message_id, str(action_path))

        # Log action
        self.logger.log(
            "INFO",
            "gmail_action_file_created",
            {
                "action_file": str(action_path),
                "message_id": message_id,
                "subject": message_data.get("subject", ""),
            },
        )

        return action_path

    def run(self) -> None:
        """
        Main watcher loop.

        Continuously monitors Gmail and creates action files.
        Stops when STOP file is detected or session expires.
        """
        self.logger.log(
            "INFO",
            "gmail_watcher_started",
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
                    self.logger.log(
                        "WARNING",
                        "stop_file_detected",
                        {"stop_file": str(stop_file)},
                    )
                    break

                # Check for updates
                try:
                    messages = self.check_for_updates()
                    for message_data in messages:
                        self.create_action_file(message_data)
                except GmailSessionExpiredError:
                    self.logger.log(
                        "WARNING",
                        "gmail_session_expired_stopping",
                        {},
                    )
                    break
                except Exception as e:
                    self.logger.error(
                        "check_updates_error",
                        {"error": str(e)},
                    )

                # Sleep until next check
                time.sleep(self.interval)

        except KeyboardInterrupt:
            self.logger.log("INFO", "gmail_watcher_stopped", {"reason": "keyboard_interrupt"})
        finally:
            self.logger.log("INFO", "gmail_watcher_stopped", {"reason": "normal"})


def main() -> None:
    """Entry point for Gmail Watcher."""
    import argparse

    parser = argparse.ArgumentParser(description="Gmail Watcher")
    parser.add_argument(
        "--vault-path",
        type=str,
        default="vault/",
        help="Path to vault directory",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Log actions without creating files",
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=120,
        help="Check interval in seconds (default: 120)",
    )

    args = parser.parse_args()

    watcher = GmailWatcher(
        vault_path=args.vault_path,
        dry_run=args.dry_run,
        interval=args.interval,
    )
    watcher.run()


if __name__ == "__main__":
    main()
