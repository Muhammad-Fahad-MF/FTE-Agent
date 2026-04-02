"""WhatsAppMCP Server - WhatsApp Web automation via Playwright."""

import asyncio
from typing import Any

from playwright.async_api import Browser, BrowserContext, Page, Playwright, async_playwright

from ...audit_logger import AuditLogger
from .session_manager import SessionManager


class WhatsAppMCPServer:
    """MCP Server for WhatsApp Web automation.
    
    Provides messaging capabilities via Playwright browser automation.
    """
    
    def __init__(self) -> None:
        """Initialize WhatsAppMCP server."""
        self.logger = AuditLogger(component="whatsapp_mcp_server")
        self.session_manager = SessionManager()
        
        self.playwright: Playwright | None = None
        self.browser: Browser | None = None
        self.context: BrowserContext | None = None
        self.page: Page | None = None
        
        self.whatsapp_url = "https://web.whatsapp.com"
        self.is_running = False
    
    async def start(self) -> bool:
        """Start WhatsAppMCP server and initialize browser.
        
        Returns:
            True if startup successful, False otherwise
        """
        try:
            self.playwright = await async_playwright().start()
            self.browser, self.context = await self.session_manager.initialize_browser(
                self.playwright
            )
            
            self.page = await self.context.new_page()
            await self.page.goto(self.whatsapp_url)
            
            # Wait for page load
            await self.page.wait_for_load_state("domcontentloaded")
            
            self.is_running = True
            
            self.logger.log(
                "INFO",
                "whatsapp_mcp_started",
                {"url": self.whatsapp_url},
            )
            
            return True
            
        except Exception as error:
            self.logger.log(
                "ERROR",
                "whatsapp_mcp_start_failed",
                {"error": str(error)},
            )
            return False
    
    async def ensure_authenticated(self) -> bool:
        """Ensure WhatsApp Web is authenticated.
        
        Returns:
            True if authenticated, False if login required
        """
        if not self.page:
            return False
        
        # Check if session expired
        if self.session_manager.detect_session_expiry(self.page):
            self.logger.log(
                "WARNING",
                "whatsapp_session_requires_login",
                {},
            )
            return False
        
        return True
    
    def get_page(self) -> Page | None:
        """Get current Playwright page.
        
        Returns:
            Page object or None if not initialized
        """
        return self.page
    
    async def shutdown(self) -> None:
        """Gracefully shutdown the server."""
        self.is_running = False
        
        if self.browser:
            await self.browser.close()
        
        if self.playwright:
            await self.playwright.stop()
        
        self.logger.log("INFO", "whatsapp_mcp_shutdown", {})
