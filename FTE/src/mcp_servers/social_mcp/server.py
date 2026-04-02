"""SocialMCP Server - Unified social media API integration."""

import os
from typing import Any

from ...audit_logger import AuditLogger
from .facebook_handler import FacebookHandler
from .instagram_handler import InstagramHandler
from .linkedin_handler import LinkedInHandler
from .twitter_handler import TwitterHandler


class SocialMCPServer:
    """MCP Server for unified social media operations.
    
    Provides posting and analytics for LinkedIn, Twitter, Facebook, and Instagram.
    """
    
    def __init__(self) -> None:
        """Initialize SocialMCP server."""
        self.logger = AuditLogger(component="social_mcp_server")
        
        # Initialize platform handlers
        self.linkedin = LinkedInHandler()
        self.twitter = TwitterHandler()
        self.facebook = FacebookHandler()
        self.instagram = InstagramHandler()
        
        self.is_running = False
    
    def register_handlers(self) -> None:
        """Register all platform handlers."""
        self.logger.log(
            "INFO",
            "social_mcp_handlers_registered",
            {
                "platforms": [
                    "linkedin",
                    "twitter",
                    "facebook",
                    "instagram",
                ]
            },
        )
    
    async def start(self) -> bool:
        """Start SocialMCP server.
        
        Returns:
            True if startup successful
        """
        try:
            self.register_handlers()
            self.is_running = True
            
            self.logger.log(
                "INFO",
                "social_mcp_started",
                {"platforms": 4},
            )
            
            return True
            
        except Exception as error:
            self.logger.log(
                "ERROR",
                "social_mcp_start_failed",
                {"error": str(error)},
            )
            return False
    
    def get_platform_handler(self, platform: str) -> Any | None:
        """Get handler for specific platform.
        
        Args:
            platform: Platform name (linkedin, twitter, facebook, instagram)
            
        Returns:
            Platform handler or None if invalid platform
        """
        handlers = {
            "linkedin": self.linkedin,
            "twitter": self.twitter,
            "facebook": self.facebook,
            "instagram": self.instagram,
        }
        return handlers.get(platform)
    
    async def shutdown(self) -> None:
        """Gracefully shutdown the server."""
        self.is_running = False
        self.logger.log("INFO", "social_mcp_shutdown", {})
