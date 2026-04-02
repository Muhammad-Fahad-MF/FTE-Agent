"""WhatsAppMCP Handlers - WhatsApp Web messaging operations."""

import asyncio
from typing import Any

from playwright.async_api import TimeoutError as PlaywrightTimeoutError

from ...audit_logger import AuditLogger
from ...utils.dev_mode import check_dev_mode
from .server import WhatsAppMCPServer


class WhatsAppHandlers:
    """Handler functions for WhatsAppMCP operations."""
    
    def __init__(self, server: WhatsAppMCPServer) -> None:
        """Initialize WhatsApp handlers.
        
        Args:
            server: WhatsAppMCP server instance
        """
        self.server = server
        self.logger = AuditLogger(component="whatsapp_handlers")
    
    async def send_whatsapp(
        self,
        contact: str,
        message: str,
        dry_run: bool = False,
    ) -> dict[str, Any]:
        """Send message via WhatsApp Web.
        
        Args:
            contact: Contact name or phone number
            message: Message text to send
            dry_run: If True, log without sending
            
        Returns:
            dict with success status and message details
        """
        # Validate DEV_MODE
        if not dry_run:
            check_dev_mode()
        
        try:
            # Ensure server is running
            if not self.server.is_running:
                return {
                    "success": False,
                    "error": "WhatsAppMCP server not running",
                }
            
            page = self.server.get_page()
            if not page:
                return {
                    "success": False,
                    "error": "WhatsApp Web page not initialized",
                }
            
            if dry_run:
                self.logger.log(
                    "INFO",
                    "send_whatsapp_dry_run",
                    {"contact": contact, "message": message[:50] + "..." if len(message) > 50 else message},
                    dry_run=True,
                )
                return {
                    "success": True,
                    "dry_run": True,
                    "contact": contact,
                    "message": "Message would be sent (dry-run mode)",
                }
            
            # Ensure authenticated
            if not await self.server.ensure_authenticated():
                return {
                    "success": False,
                    "error": "WhatsApp session expired. Please scan QR code to login.",
                }
            
            # Find contact
            contact_found = await self._find_contact(page, contact)
            if not contact_found:
                return {
                    "success": False,
                    "error": f"Contact not found: {contact}",
                }
            
            # Type and send message
            await self._type_message(page, message)
            send_success = await self._send_message(page)
            
            if send_success:
                self.logger.log(
                    "INFO",
                    "whatsapp_message_sent",
                    {"contact": contact, "message_length": len(message)},
                )
                return {
                    "success": True,
                    "contact": contact,
                    "message_length": len(message),
                }
            else:
                return {
                    "success": False,
                    "error": "Failed to send message",
                }
            
        except PlaywrightTimeoutError as error:
            self.logger.log(
                "ERROR",
                "send_whatsapp_timeout",
                {"contact": contact, "error": str(error)},
            )
            return {
                "success": False,
                "error": f"Timeout: {str(error)}",
            }
        except Exception as error:
            self.logger.log(
                "ERROR",
                "send_whatsapp_error",
                {"contact": contact, "error": str(error)},
            )
            return {"success": False, "error": str(error)}
    
    async def _find_contact(self, page, contact: str) -> bool:
        """Find and open chat with contact.
        
        Args:
            page: Playwright page object
            contact: Contact name or phone number
            
        Returns:
            True if contact found, False otherwise
        """
        try:
            # Click on search box
            search_box = page.locator("div[contenteditable='true'][data-tab='3']")
            await search_box.first.click()
            await search_box.first.fill(contact)
            
            # Wait for search results
            await asyncio.sleep(1)
            
            # Click on first result
            first_result = page.locator("span[title]").first
            await first_result.click()
            
            # Wait for chat to load
            await asyncio.sleep(0.5)
            
            return True
            
        except Exception as error:
            self.logger.log(
                "ERROR",
                "whatsapp_contact_not_found",
                {"contact": contact, "error": str(error)},
            )
            return False
    
    async def _type_message(self, page, message: str) -> None:
        """Type message in chat input.
        
        Args:
            page: Playwright page object
            message: Message text to type
        """
        # Find message input
        message_box = page.locator(
            "div[contenteditable='true'][data-tab='10']"
        ).first
        
        await message_box.click()
        await message_box.fill(message)
    
    async def _send_message(self, page) -> bool:
        """Send typed message.
        
        Args:
            page: Playwright page object
            
        Returns:
            True if message sent successfully
        """
        try:
            # Find send button
            send_button = page.locator(
                "button[data-testid='compose-btn-send'][aria-label='Send message']"
            ).first
            
            await send_button.click()
            
            # Wait for message to be sent
            await asyncio.sleep(0.5)
            
            return True
            
        except Exception as error:
            self.logger.log(
                "ERROR",
                "whatsapp_send_failed",
                {"error": str(error)},
            )
            return False
