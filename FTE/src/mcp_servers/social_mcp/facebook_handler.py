"""Facebook Handler - Facebook Graph API v18+ integration."""

import os
from datetime import datetime, timedelta
from typing import Any

import requests

from ...audit_logger import AuditLogger
from ...utils.dev_mode import check_dev_mode


class FacebookHandler:
    """Handler for Facebook posting and analytics."""
    
    def __init__(self) -> None:
        """Initialize Facebook handler."""
        self.logger = AuditLogger(component="facebook_handler")
        
        # Configuration from environment
        self.page_access_token = os.getenv("FACEBOOK_PAGE_ACCESS_TOKEN")
        self.page_id = os.getenv("FACEBOOK_PAGE_ID")
        
        # Rate limiting: 200 calls per hour
        self.call_count = 0
        self.rate_limit_window = timedelta(hours=1)
        self.window_start = datetime.now()
        self.max_calls_per_window = 200
        
        self.api_version = "v18.0"
        self.base_url = f"https://graph.facebook.com/{self.api_version}"
    
    def check_rate_limit(self) -> tuple[bool, int]:
        """Check if within rate limit (200 calls per hour).
        
        Returns:
            Tuple of (is_within_limit, seconds_until_reset)
        """
        now = datetime.now()
        
        # Reset window if expired
        if now - self.window_start >= self.rate_limit_window:
            self.call_count = 0
            self.window_start = now
        
        if self.call_count >= self.max_calls_per_window:
            seconds_remaining = int(
                (self.window_start + self.rate_limit_window - now).total_seconds()
            )
            return False, seconds_remaining
        
        return True, 0
    
    def post_facebook(
        self,
        page_id: str | None = None,
        content: str = "",
        image_url: str | None = None,
        dry_run: bool = False,
    ) -> dict[str, Any]:
        """Create Facebook page post.
        
        Args:
            page_id: Facebook Page ID (uses env default if None)
            content: Post content text
            image_url: Optional image URL to include
            dry_run: If True, log without posting
            
        Returns:
            dict with post_id on success, error details on failure
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
        
        page_id = page_id or self.page_id
        if not page_id:
            return {
                "success": False,
                "error": "Facebook Page ID not configured",
            }
        
        if not self.page_access_token:
            return {
                "success": False,
                "error": "Facebook Page Access Token not configured",
            }
        
        if dry_run:
            self.logger.log(
                "INFO",
                "facebook_post_dry_run",
                {"page_id": page_id, "content_length": len(content)},
                dry_run=True,
            )
            return {
                "success": True,
                "dry_run": True,
                "message": "Post would be created (dry-run mode)",
            }
        
        try:
            self.call_count += 1
            
            # Prepare post data
            post_data = {
                "message": content,
                "access_token": self.page_access_token,
            }
            
            if image_url:
                post_data["link"] = image_url
            
            # Create post
            response = requests.post(
                f"{self.base_url}/{page_id}/feed",
                data=post_data,
                timeout=30,
            )
            
            result = response.json()
            
            if response.status_code == 200 and "id" in result:
                post_id = result["id"]
                
                self.logger.log(
                    "INFO",
                    "facebook_post_created",
                    {"post_id": post_id, "page_id": page_id},
                )
                
                return {
                    "success": True,
                    "post_id": post_id,
                    "page_id": page_id,
                }
            else:
                self.logger.log(
                    "ERROR",
                    "facebook_post_failed",
                    {"status_code": response.status_code, "response": result},
                )
                return {
                    "success": False,
                    "error": f"Facebook API error: {response.status_code}",
                    "details": result,
                }
                
        except Exception as error:
            self.logger.log(
                "ERROR",
                "facebook_post_error",
                {"error": str(error)},
            )
            return {"success": False, "error": str(error)}
    
    def get_facebook_insights(
        self,
        page_id: str | None = None,
        post_id: str | None = None,
    ) -> dict[str, Any]:
        """Get Facebook page/post insights.
        
        Args:
            page_id: Facebook Page ID (uses env default if None)
            post_id: Optional specific post ID
            
        Returns:
            dict with reach and engagement metrics
        """
        page_id = page_id or self.page_id
        if not page_id:
            return {
                "success": False,
                "error": "Facebook Page ID not configured",
            }
        
        if not self.page_access_token:
            return {
                "success": False,
                "error": "Facebook Page Access Token not configured",
            }
        
        try:
            self.call_count += 1
            
            # Get insights
            insights_field = "insights.metric(page_engagement,page_posts_engaged,page_post_impressions)"
            
            response = requests.get(
                f"{self.base_url}/{page_id}",
                params={
                    "fields": insights_field,
                    "access_token": self.page_access_token,
                },
                timeout=30,
            )
            
            result = response.json()
            
            if response.status_code == 200:
                insights = result.get("insights", {}).get("data", [])
                
                analytics = {
                    "reach": 0,
                    "engagement": 0,
                }
                
                for metric in insights:
                    if metric["name"] == "page_post_impressions":
                        analytics["reach"] = sum(
                            v.get("value", 0) for v in metric.get("values", [])
                        )
                    elif metric["name"] == "page_engagement":
                        analytics["engagement"] = sum(
                            v.get("value", 0) for v in metric.get("values", [])
                        )
                
                self.logger.log(
                    "INFO",
                    "facebook_insights_retrieved",
                    {"page_id": page_id, **analytics},
                )
                
                return {"success": True, **analytics}
            else:
                return {
                    "success": False,
                    "error": f"Facebook API error: {response.status_code}",
                }
                
        except Exception as error:
            self.logger.log(
                "ERROR",
                "facebook_insights_error",
                {"page_id": page_id, "error": str(error)},
            )
            return {"success": False, "error": str(error)}
