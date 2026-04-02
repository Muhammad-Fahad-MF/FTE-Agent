"""Instagram Handler - Instagram Graph API integration via instagrapi."""

import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from ...audit_logger import AuditLogger
from ...utils.dev_mode import check_dev_mode


class InstagramHandler:
    """Handler for Instagram posting and analytics."""
    
    def __init__(self) -> None:
        """Initialize Instagram handler."""
        self.logger = AuditLogger(component="instagram_handler")
        
        # Configuration from environment
        self.username = os.getenv("INSTAGRAM_USERNAME")
        self.password = os.getenv("INSTAGRAM_PASSWORD")
        
        # Rate limiting: 25 posts per day
        self.post_count = 0
        self.rate_limit_window = timedelta(days=1)
        self.window_start = datetime.now()
        self.max_posts_per_day = 25
        
        # Client will be initialized on authenticate
        self.client: Any | None = None
        self.is_authenticated = False
    
    def authenticate(self) -> bool:
        """Authenticate with Instagram.
        
        Returns:
            True if authentication successful
        """
        if not all([self.username, self.password]):
            self.logger.log(
                "ERROR",
                "instagram_missing_credentials",
                {},
            )
            return False
        
        try:
            # Import instagrapi here to avoid dependency issues if not installed
            from instagrapi import Client
            
            self.client = Client()
            self.client.login(self.username, self.password)
            
            self.is_authenticated = True
            
            self.logger.log(
                "INFO",
                "instagram_authenticated",
                {"username": self.username},
            )
            
            return True
            
        except ImportError:
            self.logger.log(
                "ERROR",
                "instagram_library_not_installed",
                {"message": "instagrapi not installed. Run: pip install instagrapi"},
            )
            return False
        except Exception as error:
            self.logger.log(
                "ERROR",
                "instagram_auth_error",
                {"error": str(error)},
            )
            return False
    
    def check_rate_limit(self) -> tuple[bool, int]:
        """Check if within rate limit (25 posts per day).
        
        Returns:
            Tuple of (is_within_limit, seconds_until_reset)
        """
        now = datetime.now()
        
        # Reset window if expired
        if now - self.window_start >= self.rate_limit_window:
            self.post_count = 0
            self.window_start = now
        
        if self.post_count >= self.max_posts_per_day:
            seconds_remaining = int(
                (self.window_start + self.rate_limit_window - now).total_seconds()
            )
            return False, seconds_remaining
        
        return True, 0
    
    def post_instagram(
        self,
        image_path: str,
        caption: str = "",
        dry_run: bool = False,
    ) -> dict[str, Any]:
        """Create Instagram media post.
        
        Args:
            image_path: Path to image file
            caption: Post caption text
            dry_run: If True, log without posting
            
        Returns:
            dict with media_id on success, error details on failure
        """
        # Validate DEV_MODE
        if not dry_run:
            check_dev_mode()
        
        # Check rate limit
        within_limit, seconds_remaining = self.check_rate_limit()
        if not within_limit:
            return {
                "success": False,
                "error": "Rate limit exceeded",
                "retry_after": seconds_remaining,
            }
        
        # Validate image path
        image_file = Path(image_path)
        if not image_file.exists():
            return {
                "success": False,
                "error": f"Image not found: {image_path}",
            }
        
        if dry_run:
            self.logger.log(
                "INFO",
                "instagram_post_dry_run",
                {"image_path": image_path, "caption_length": len(caption)},
                dry_run=True,
            )
            return {
                "success": True,
                "dry_run": True,
                "message": "Post would be created (dry-run mode)",
            }
        
        try:
            if not self.is_authenticated:
                if not self.authenticate():
                    return {"success": False, "error": "Instagram authentication failed"}
            
            if not self.client:
                return {"success": False, "error": "Instagram client not initialized"}
            
            # Upload photo
            media = self.client.photo_upload(
                path=str(image_file),
                caption=caption,
            )
            
            if media:
                self.post_count += 1
                
                self.logger.log(
                    "INFO",
                    "instagram_post_created",
                    {"media_id": media.pk, "caption_length": len(caption)},
                )
                
                return {
                    "success": True,
                    "media_id": str(media.pk),
                    "code": media.code,
                }
            else:
                return {
                    "success": False,
                    "error": "Instagram upload returned no media",
                }
                
        except Exception as error:
            self.logger.log(
                "ERROR",
                "instagram_post_error",
                {"error": str(error)},
            )
            return {"success": False, "error": str(error)}
    
    def get_instagram_insights(
        self,
        media_id: str,
    ) -> dict[str, Any]:
        """Get Instagram media insights.
        
        Args:
            media_id: Instagram media ID
            
        Returns:
            dict with engagement metrics
        """
        try:
            if not self.is_authenticated:
                if not self.authenticate():
                    return {"success": False, "error": "Instagram authentication failed"}
            
            if not self.client:
                return {"success": False, "error": "Instagram client not initialized"}
            
            # Get media info
            media = self.client.media_info(media_id)
            
            if media:
                analytics = {
                    "likes": media.like_count,
                    "comments": media.comment_count,
                    "saves": getattr(media, "save_count", 0),  # May not be available
                }
                
                self.logger.log(
                    "INFO",
                    "instagram_insights_retrieved",
                    {"media_id": media_id, **analytics},
                )
                
                return {"success": True, **analytics}
            else:
                return {
                    "success": False,
                    "error": "Media not found",
                }
                
        except Exception as error:
            self.logger.log(
                "ERROR",
                "instagram_insights_error",
                {"media_id": media_id, "error": str(error)},
            )
            return {"success": False, "error": str(error)}
