"""
WhatsApp Watcher - Monitor WhatsApp Web for keyword messages.

This module implements a WhatsApp watcher that:
- Monitors WhatsApp Web every 30 seconds (configurable)
- Creates action files for messages with keywords (urgent, asap, invoice, payment, help)
- Preserves browser session across restarts
- Implements circuit breaker for Playwright resilience
- Emits metrics for monitoring
- Handles session expiry gracefully

Usage:
    watcher = WhatsAppWatcher(vault_path="vault/", dry_run=False)
    watcher.run()

Dependencies:
    pip install playwright
    playwright install  # Install browser binaries
"""

import asyncio
import re
import time
from datetime import datetime
from pathlib import Path
from typing import Any

from playwright.async_api import (
    Browser,
    BrowserContext,
    Page,
    Playwright,
    async_playwright,
)
from playwright.async_api import (
    TimeoutError as PlaywrightTimeoutError,
)

from ..base_watcher import BaseWatcher
from ..metrics.collector import MetricsCollector, get_metrics_collector
from ..utils.circuit_breaker import (
    CircuitBreakerOpenError,
    PersistentCircuitBreaker,
    get_circuit_breaker,
)


class WhatsAppSessionExpiredError(Exception):
    """Raised when WhatsApp Web session is expired."""

    pass


class WhatsAppWatcher(BaseWatcher):
    """
    WhatsApp watcher for monitoring keyword messages.

    Attributes:
        vault_path: Root path of the vault directory.
        dry_run: If True, log actions without creating files.
        interval: Check interval in seconds (default: 30).
        keywords: List of keywords to filter messages
                  (default: urgent, asap, invoice, payment, help).
    """

    def __init__(
        self,
        vault_path: str,
        dry_run: bool = False,
        interval: int = 30,
        keywords: list[str] | None = None,
        headless: bool = True,
    ) -> None:
        """
        Initialize WhatsApp watcher.

        Args:
            vault_path: Root path of the vault directory.
            dry_run: If True, log actions without creating files.
            interval: Check interval in seconds (default: 30).
            keywords: List of keywords to filter
                      (default: urgent, asap, invoice, payment, help).
            headless: Run browser in headless mode (default: True).
        """
        super().__init__(vault_path, dry_run, interval)

        # Ensure data and session directories exist
        self.data_path = self.vault_path.parent / "data"
        self.data_path.mkdir(parents=True, exist_ok=True)

        self.session_path = self.vault_path / "whatsapp_session"
        self.session_path.mkdir(parents=True, exist_ok=True)

        # Initialize metrics collector
        metrics_db_path = str(self.data_path / "metrics.db")
        self.metrics: MetricsCollector = get_metrics_collector(db_path=metrics_db_path)

        # Initialize circuit breaker
        circuit_breaker_db_path = str(self.data_path / "circuit_breakers.db")
        self.circuit_breaker: PersistentCircuitBreaker = get_circuit_breaker(
            name="whatsapp_api",
            failure_threshold=5,
            recovery_timeout=60,
            fallback=self._whatsapp_fallback,
            db_path=circuit_breaker_db_path,
        )

        # Browser state
        self._playwright: Playwright | None = None
        self._browser: Browser | None = None
        self._context: BrowserContext | None = None
        self._page: Page | None = None

        # Keywords for filtering
        self.keywords = keywords or ["urgent", "asap", "invoice", "payment", "help"]
        self.headless = headless

        # Load keywords from Company_Handbook.md if exists
        self._load_keywords_config()

        # Session state
        self._session_valid: bool | None = None

        self.logger.info(
            "whatsapp_watcher_initialized",
            {
                "vault_path": str(self.vault_path),
                "dry_run": self.dry_run,
                "interval": interval,
                "keywords": self.keywords,
                "headless": self.headless,
            },
        )

    def _load_keywords_config(self) -> None:
        """Load keyword configuration from Company_Handbook.md."""
        handbook_path = self.vault_path / "Company_Handbook.md"
        if handbook_path.exists():
            try:
                content = handbook_path.read_text(encoding="utf-8")
                # Look for [WhatsApp] section and keywords
                match = re.search(
                    r"\[WhatsApp\].*?keywords\s*=\s*([^\n]+)",
                    content,
                    re.DOTALL | re.IGNORECASE,
                )
                if match:
                    keywords_str = match.group(1).strip()
                    # Parse comma-separated keywords
                    self.keywords = [k.strip().lower() for k in keywords_str.split(",")]
                    self.logger.info(
                        "whatsapp_keywords_loaded",
                        {"keywords": self.keywords},
                    )
            except Exception as e:
                self.logger.log(
                    "WARNING",
                    "whatsapp_keywords_load_failed",
                    {"error": str(e)},
                )

    def _whatsapp_fallback(self) -> list[dict[str, Any]]:
        """Fallback function when circuit breaker is open."""
        self.logger.log(
            "WARNING",
            "whatsapp_circuit_open",
            {"message": "Using fallback - returning empty list"},
        )
        return []

    async def _init_browser(self) -> None:
        """Initialize Playwright browser and context."""
        try:
            # Start Playwright
            self._playwright = await async_playwright().start()

            # Launch browser
            self._browser = await self._playwright.chromium.launch(
                headless=self.headless,
                args=[
                    "--disable-gpu",
                    "--no-sandbox",
                    "--disable-dev-shm-usage",
                ],
            )

            # Try to recover session
            session_storage = self.session_path / "storage.json"
            if session_storage.exists():
                self._context = await self._browser.new_context(
                    storage_state=str(session_storage),
                    user_data_dir=str(self.session_path),
                )
                self.logger.info(
                    "whatsapp_session_recovered",
                    {"session_path": str(self.session_path)},
                )
            else:
                self._context = await self._browser.new_context(
                    user_data_dir=str(self.session_path),
                )
                self.logger.info(
                    "whatsapp_new_session_created",
                    {"session_path": str(self.session_path)},
                )

            # Set viewport
            await self._context.set_viewport_size({"width": 1280, "height": 720})

            # Create page
            self._page = await self._context.new_page()
            self._page.set_default_timeout(30000)  # 30 seconds

        except Exception as e:
            self.logger.error(
                "whatsapp_browser_init_failed",
                {"error": str(e)},
            )
            raise

    async def _close_browser(self) -> None:
        """Close browser and cleanup resources."""
        try:
            if self._page:
                await self._page.close()
            if self._context:
                await self._context.close()
            if self._browser:
                await self._browser.close()
            if self._playwright:
                await self._playwright.stop()

            self._page = None
            self._context = None
            self._browser = None
            self._playwright = None

            self.logger.info("whatsapp_browser_closed")
        except Exception as e:
            self.logger.error(
                "whatsapp_browser_close_failed",
                {"error": str(e)},
            )

    async def _save_session(self) -> None:
        """Save browser session to disk."""
        if not self._context:
            return

        try:
            await self._context.storage_state(path=str(self.session_path / "storage.json"))
            self.logger.info(
                "whatsapp_session_saved",
                {"session_path": str(self.session_path)},
            )
        except Exception as e:
            self.logger.error(
                "whatsapp_session_save_failed",
                {"error": str(e)},
            )

    async def _recover_session(self) -> bool:
        """
        Check if session is valid.

        Returns:
            True if session is valid, False if expired.
        """
        if not self._page:
            return False

        try:
            # Navigate to WhatsApp Web
            await self._page.goto("https://web.whatsapp.com", wait_until="domcontentloaded")
            await self._page.wait_for_timeout(5000)  # Wait 5 seconds for load

            # Check if main chat pane is visible (indicates logged in)
            # WhatsApp Web has different selectors, try multiple
            selectors = [
                'div[data-testid="default-user"]',  # Welcome screen
                'div[data-testid="chat-list"]',  # Chat list
                'span[data-testid="message-text"]',  # Messages
            ]

            for selector in selectors:
                try:
                    await self._page.wait_for_selector(selector, timeout=3000)
                    # If we get here without timeout, session is valid
                    self._session_valid = True
                    return True
                except PlaywrightTimeoutError:
                    continue

            # If no selector found, check for QR code (not logged in)
            qr_selector = 'canvas[data-testid="qr-code"]'
            if await self._page.query_selector(qr_selector):
                self._session_valid = False
                return False

            # Default to valid if we can't determine
            self._session_valid = True
            return True

        except Exception as e:
            self.logger.error(
                "whatsapp_session_check_failed",
                {"error": str(e)},
            )
            self._session_valid = False
            return False

    def _filter_by_keywords(self, messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """
        Filter messages by keywords.

        Args:
            messages: List of message dicts with 'message' key.

        Returns:
            List of messages containing keywords.
        """
        filtered = []
        for msg in messages:
            message_text = msg.get("message", "").lower()
            contact_name = msg.get("contact_name", "").lower()

            matched_keywords = []
            for keyword in self.keywords:
                if keyword.lower() in message_text or keyword.lower() in contact_name:
                    matched_keywords.append(keyword)

            if matched_keywords:
                msg["keywords_matched"] = matched_keywords
                filtered.append(msg)

        return filtered

    async def _check_for_updates_impl(self) -> list[dict[str, Any]]:
        """
        Implementation of check_for_updates.

        Returns:
            List of message metadata dicts.
        """
        start_time = time.perf_counter()
        correlation_id = str(time.time())

        try:
            # Initialize browser if needed
            if not self._page:
                await self._init_browser()

            # Check session validity
            session_valid = await self._recover_session()
            if not session_valid:
                self.logger.log(
                    "WARNING",
                    "whatsapp_session_expired",
                    {},
                )
                raise WhatsAppSessionExpiredError("WhatsApp Web session expired")

            # Navigate to WhatsApp Web
            await self._page.goto("https://web.whatsapp.com", wait_until="domcontentloaded")
            await self._page.wait_for_timeout(3000)  # Wait for content to load

            # Extract last 10 messages from visible chat
            messages = []
            try:
                # Wait for message container
                await self._page.wait_for_selector(
                    'div[data-testid="chat-list"] div[role="row"]',
                    timeout=5000,
                )

                # Get message rows
                message_rows = await self._page.query_selector_all(
                    'div[data-testid="chat-list"] div[role="row"]'
                )

                # Extract last 10 messages
                for row in message_rows[-10:]:
                    try:
                        # Extract contact name
                        contact_elem = await row.query_selector('span[data-testid="meta-title"]')
                        contact_name = (
                            await contact_elem.inner_text() if contact_elem else "Unknown"
                        )

                        # Extract message preview
                        message_elem = await row.query_selector(
                            'span[data-testid="message-preview"]'
                        )
                        message_text = await message_elem.inner_text() if message_elem else ""

                        # Extract timestamp
                        time_elem = await row.query_selector(
                            'span[data-testid="message-preview-time"]'
                        )
                        timestamp = await time_elem.inner_text() if time_elem else ""

                        # Extract phone number (simplified - from contact name)
                        phone = re.sub(r"[^\d+]", "", contact_name) or "unknown"

                        messages.append(
                            {
                                "from": phone,
                                "contact_name": contact_name,
                                "message": message_text,
                                "received": timestamp,
                                "keywords_matched": [],
                            }
                        )
                    except Exception as e:
                        self.logger.debug(f"Failed to extract message: {e}")
                        continue

            except PlaywrightTimeoutError:
                self.logger.log(
                    "WARNING",
                    "whatsapp_message_container_not_found",
                    {},
                )
                # No messages or not logged in
                return []

            # Filter by keywords
            filtered_messages = self._filter_by_keywords(messages)

            # Save session
            await self._save_session()

            # Record metrics
            duration = time.perf_counter() - start_time
            self.metrics.record_histogram(
                "whatsapp_watcher_check_duration",
                duration,
                tags={"correlation_id": correlation_id},
            )
            self.metrics.increment_counter(
                "whatsapp_watcher_items_processed",
                len(filtered_messages),
                tags={"correlation_id": correlation_id},
            )

            self.logger.info(
                "whatsapp_check_completed",
                {
                    "messages_scanned": len(messages),
                    "messages_matched": len(filtered_messages),
                    "duration_seconds": duration,
                },
            )

            return filtered_messages

        except PlaywrightTimeoutError as e:
            self.logger.error(
                "whatsapp_timeout_error",
                {"error": str(e)},
            )
            self.metrics.increment_counter(
                "whatsapp_watcher_errors",
                tags={"correlation_id": correlation_id, "error_type": "timeout"},
            )
            raise

        except Exception as e:
            self.logger.error(
                "whatsapp_check_failed",
                {"error": str(e)},
            )
            self.metrics.increment_counter(
                "whatsapp_watcher_errors",
                tags={"correlation_id": correlation_id, "error_type": "general"},
            )
            raise

    def check_for_updates(self) -> list[dict[str, Any]]:
        """
        Check for new WhatsApp messages with keywords.

        Wraps the implementation with circuit breaker protection.

        Returns:
            List of message metadata dicts.
        """
        try:
            # Run async code in sync context
            return asyncio.run(self.circuit_breaker.call(self._check_for_updates_impl))
        except CircuitBreakerOpenError:
            self.logger.log(
                "WARNING",
                "whatsapp_circuit_breaker_open",
                {"message": "Skipping WhatsApp check"},
            )
            return []
        except WhatsAppSessionExpiredError as e:
            self.logger.log(
                "WARNING",
                "whatsapp_session_expired",
                {"error": str(e)},
            )
            # Update Dashboard.md with expiry alert
            self._update_dashboard_session_expiry("WhatsApp")
            return []
        except Exception as e:
            self.logger.error(
                "whatsapp_check_error",
                {"error": str(e)},
            )
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
                alert = (
                    f"\n## ⚠️ Session Expired: {service}\n"
                    f"{service} session expired. Please re-authenticate.\n"
                )

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
        Create action file for WhatsApp message.

        Args:
            message_data: Message metadata dict with keys:
                - from (phone number)
                - contact_name
                - message
                - received
                - keywords_matched

        Returns:
            Path to created action file.
        """
        phone = message_data.get("from", "unknown")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Sanitize phone number for filename (digits only)
        safe_phone = re.sub(r"[^\d]", "", phone) or "unknown"
        action_filename = f"WHATSAPP_{safe_phone}_{timestamp}.md"

        needs_action_dir = self.vault_path / "Needs_Action"
        needs_action_dir.mkdir(parents=True, exist_ok=True)
        action_path = needs_action_dir / action_filename

        # Create YAML frontmatter per spec.md Section 6.2
        frontmatter = f"""---
type: whatsapp
from: {message_data.get("from", "")}
contact_name: {message_data.get("contact_name", "")}
message: {message_data.get("message", "")[:200]}  # Truncate for frontmatter
received: {message_data.get("received", "")}
keywords: {", ".join(message_data.get("keywords_matched", []))}
status: pending
created: {datetime.now().isoformat()}
---

## WhatsApp Message

**From:** {message_data.get("contact_name", "")} ({message_data.get("from", "")})
**Received:** {message_data.get("received", "")}
**Matched Keywords:** {", ".join(message_data.get("keywords_matched", []))}

---

## Message Content

{message_data.get("message", "")}

---

## Suggested Actions

- [ ] Review and respond to message
- [ ] Take necessary action based on keywords
- [ ] Mark as complete when done

---

## Notes

"""

        if self.dry_run:
            self.logger.log(
                "INFO",
                "action_file_dry_run",
                {
                    "would_create": str(action_path),
                    "from": message_data.get("from", ""),
                    "keywords": message_data.get("keywords_matched", []),
                },
                dry_run=True,
            )
            return action_path

        # Write action file
        action_path.write_text(frontmatter, encoding="utf-8")

        # Log action
        self.logger.log(
            "INFO",
            "whatsapp_action_file_created",
            {
                "action_file": str(action_path),
                "from": message_data.get("from", ""),
                "keywords": message_data.get("keywords_matched", []),
            },
        )

        return action_path

    def run(self) -> None:
        """
        Main watcher loop.

        Continuously monitors WhatsApp Web and creates action files.
        Stops when STOP file is detected or session expires.
        """
        self.logger.log(
            "INFO",
            "whatsapp_watcher_started",
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
                except WhatsAppSessionExpiredError:
                    self.logger.log(
                        "WARNING",
                        "whatsapp_session_expired_stopping",
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
            self.logger.log("INFO", "whatsapp_watcher_stopped", {"reason": "keyboard_interrupt"})
        finally:
            # Cleanup browser
            try:
                asyncio.run(self._close_browser())
            except Exception as e:
                self.logger.error(
                    "whatsapp_browser_cleanup_failed",
                    {"error": str(e)},
                )
            self.logger.log("INFO", "whatsapp_watcher_stopped", {"reason": "normal"})


def main() -> None:
    """Entry point for WhatsApp Watcher."""
    import argparse

    parser = argparse.ArgumentParser(description="WhatsApp Watcher")
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
        default=30,
        help="Check interval in seconds (default: 30)",
    )
    parser.add_argument(
        "--headful",
        action="store_true",
        help="Run browser in headful mode (default: headless)",
    )
    parser.add_argument(
        "--keywords",
        type=str,
        default=None,
        help="Comma-separated keywords to filter (default: urgent,asap,invoice,payment,help)",
    )

    args = parser.parse_args()

    # Parse keywords if provided
    keywords = None
    if args.keywords:
        keywords = [k.strip() for k in args.keywords.split(",")]

    watcher = WhatsAppWatcher(
        vault_path=args.vault_path,
        dry_run=args.dry_run,
        interval=args.interval,
        keywords=keywords,
        headless=not args.headful,
    )
    watcher.run()


if __name__ == "__main__":
    main()
