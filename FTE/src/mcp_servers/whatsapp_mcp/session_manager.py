"""WhatsAppMCP Session Manager - Persistent session storage and recovery."""

import json
import os
from datetime import datetime
from pathlib import Path

from playwright.async_api import Browser, BrowserContext, Playwright, async_playwright

from ...audit_logger import AuditLogger


class SessionManager:
    """Manage WhatsApp Web session persistence and recovery."""
    
    def __init__(self) -> None:
        """Initialize session manager."""
        self.logger = AuditLogger(component="whatsapp_session")
        
        # Session storage path
        vault_path = os.getenv("VAULT_PATH", "./vault")
        self.session_dir = Path(vault_path) / ".sessions" / "whatsapp"
        self.session_dir.mkdir(parents=True, exist_ok=True)
        
        self.session_file = self.session_dir / "session_data.json"
        self.user_data_dir = self.session_dir / "browser_profile"
        self.user_data_dir.mkdir(parents=True, exist_ok=True)
        
        self.last_activity: datetime | None = None
    
    async def initialize_browser(
        self, playwright: Playwright
    ) -> tuple[Browser, BrowserContext]:
        """Initialize browser with persistent context.
        
        Args:
            playwright: Playwright instance
            
        Returns:
            Tuple of (browser, context)
        """
        browser = await playwright.chromium.launch(
            headless=False,  # Show browser for QR code login
            args=[
                "--disable-dev-shm-usage",
                "--disable-accelerated-2d-canvas",
                "--no-first-run",
                "--no-zygote",
            ],
        )
        
        # Persistent context for session preservation
        context = await browser.new_context(
            user_data_dir=str(self.user_data_dir),
            viewport={"width": 1280, "height": 720},
        )
        
        self.logger.log(
            "INFO",
            "whatsapp_browser_initialized",
            {"user_data_dir": str(self.user_data_dir)},
        )
        
        return browser, context
    
    def save_session(self, session_data: dict) -> None:
        """Save session data to disk.
        
        Args:
            session_data: Session metadata to save
        """
        session_data["last_saved"] = datetime.now().isoformat()
        
        self.session_file.write_text(
            json.dumps(session_data, indent=2),
            encoding="utf-8",
        )
        
        self.logger.log(
            "INFO",
            "whatsapp_session_saved",
            {"session_file": str(self.session_file)},
        )
    
    def load_session(self) -> dict | None:
        """Load session data from disk.
        
        Returns:
            Session data dict or None if not found
        """
        if not self.session_file.exists():
            return None
        
        try:
            content = self.session_file.read_text(encoding="utf-8")
            session_data = json.loads(content)
            
            self.logger.log(
                "INFO",
                "whatsapp_session_loaded",
                {"session_file": str(self.session_file)},
            )
            
            return session_data
        except (json.JSONDecodeError, Exception) as error:
            self.logger.log(
                "ERROR",
                "whatsapp_session_load_failed",
                {"error": str(error)},
            )
            return None
    
    def detect_session_expiry(self, page) -> bool:
        """Detect if WhatsApp Web session has expired.
        
        Args:
            page: Playwright page object
            
        Returns:
            True if session expired, False otherwise
        """
        # Check for QR code (indicates logged out)
        qr_selector = "canvas[data-icon='qr']"
        if page.query_selector(qr_selector):
            self.logger.log(
                "WARNING",
                "whatsapp_session_expired",
                {"reason": "QR code detected"},
            )
            return True
        
        # Check for login button
        login_selector = "div[data-testid='login']"
        if page.query_selector(login_selector):
            self.logger.log(
                "WARNING",
                "whatsapp_session_expired",
                {"reason": "Login screen detected"},
            )
            return True
        
        return False
    
    def update_activity(self) -> None:
        """Update last activity timestamp."""
        self.last_activity = datetime.now()
    
    def get_session_status(self) -> dict:
        """Get current session status.
        
        Returns:
            Dict with session status information
        """
        return {
            "has_session": self.session_file.exists(),
            "last_activity": self.last_activity.isoformat() if self.last_activity else None,
            "session_dir": str(self.session_dir),
            "user_data_dir": str(self.user_data_dir),
        }
