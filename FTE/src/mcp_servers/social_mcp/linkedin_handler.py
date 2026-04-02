"""LinkedIn Handler - LinkedIn API integration via OAuth2."""

import os
from datetime import datetime, timedelta
from typing import Any

import requests

from ...audit_logger import AuditLogger
from ...utils.dev_mode import check_dev_mode


class LinkedInHandler:
    """Handler for LinkedIn posting and analytics."""
    
    def __init__(self) -> None:
        """Initialize LinkedIn handler."""
        self.logger = AuditLogger(component="linkedin_handler")
        
        # Configuration from environment
        self.client_id = os.getenv("LINKEDIN_CLIENT_ID")
        self.client_secret = os.getenv("LINKEDIN_CLIENT_SECRET")
        self.access_token = os.getenv("LINKEDIN_ACCESS_TOKEN")
        self.person_urn = os.getenv("LINKEDIN_PERSON_URN")
        
        # Rate limiting: 1 post per 24 hours
        self.last_post_time: datetime | None = None
        self.rate_limit_window = timedelta(hours=24)
    
    def authenticate(self) -> bool:
        """Authenticate with LinkedIn API.
        
        Returns:
            True if authentication successful
        """
        if not all([self.client_id, self.client_secret, self.access_token]):
            self.logger.log(
                "ERROR",
                "linkedin_missing_credentials",
                {},
            )
            return False
        
        # Validate token by making a test request
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            response = requests.get(
                "https://api.linkedin.com/v2/me",
                headers=headers,
                timeout=30,
            )
            
            if response.status_code == 200:
                self.logger.log(
                    "INFO",
                    "linkedin_authenticated",
                    {"person_urn": self.person_urn},
                )
                return True
            else:
                self.logger.log(
                    "ERROR",
                    "linkedin_auth_failed",
                    {"status_code": response.status_code},
                )
                return False
                
        except Exception as error:
            self.logger.log(
                "ERROR",
                "linkedin_auth_error",
                {"error": str(error)},
            )
            return False
    
    def check_rate_limit(self) -> tuple[bool, int]:
        """Check if within rate limit (1 post per 24 hours).
        
        Returns:
            Tuple of (is_within_limit, seconds_until_reset)
        """
        if not self.last_post_time:
            return True, 0
        
        now = datetime.now()
        elapsed = now - self.last_post_time
        
        if elapsed >= self.rate_limit_window:
            return True, 0
        
        seconds_remaining = int((self.rate_limit_window - elapsed).total_seconds())
        return False, seconds_remaining
    
    def post_linkedin(
        self,
        text: str,
        image_url: str | None = None,
        dry_run: bool = False,
    ) -> dict[str, Any]:
        """Create LinkedIn post.
        
        Args:
            text: Post text content
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
        
        if dry_run:
            self.logger.log(
                "INFO",
                "linkedin_post_dry_run",
                {"text_length": len(text), "image_url": image_url},
                dry_run=True,
            )
            return {
                "success": True,
                "dry_run": True,
                "message": "Post would be created (dry-run mode)",
            }
        
        try:
            # Create post
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json",
                "X-Restli-Protocol-Version": "2.0.0",
            }
            
            # Simple text post
            post_data = {
                "author": f"urn:li:person:{self.person_urn}",
                "lifecycleState": "PUBLISHED",
                "specificContent": {
                    "com.linkedin.ugc.ShareContent": {
                        "shareCommentary": {
                            "text": text
                        },
                        "shareMediaCategory": "NONE",
                    }
                },
                "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"},
            }
            
            response = requests.post(
                "https://api.linkedin.com/v2/ugcPosts",
                headers=headers,
                json=post_data,
                timeout=30,
            )
            
            if response.status_code == 201:
                # Extract post ID from response headers
                post_id = response.headers.get("X-RestLi-Id", "unknown")
                
                self.last_post_time = datetime.now()
                
                self.logger.log(
                    "INFO",
                    "linkedin_post_created",
                    {"post_id": post_id},
                )
                
                return {
                    "success": True,
                    "post_id": post_id,
                    "text_length": len(text),
                }
            else:
                self.logger.log(
                    "ERROR",
                    "linkedin_post_failed",
                    {"status_code": response.status_code, "response": response.text},
                )
                return {
                    "success": False,
                    "error": f"LinkedIn API error: {response.status_code}",
                    "details": response.text,
                }
                
        except Exception as error:
            self.logger.log(
                "ERROR",
                "linkedin_post_error",
                {"error": str(error)},
            )
            return {"success": False, "error": str(error)}
    
    def get_linkedin_analytics(
        self,
        post_id: str,
    ) -> dict[str, Any]:
        """Get LinkedIn post analytics.
        
        Args:
            post_id: LinkedIn post ID
            
        Returns:
            dict with engagement metrics
        """
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            
            # Get post statistics
            response = requests.get(
                f"https://api.linkedin.com/v2/socialActions/{post_id}",
                headers=headers,
                timeout=30,
            )
            
            if response.status_code == 200:
                data = response.json()
                
                analytics = {
                    "likes": data.get("likesSummary", {}).get("total", 0),
                    "comments": data.get("commentsSummary", {}).get("total", 0),
                    "shares": 0,  # Not directly available in this endpoint
                }
                
                self.logger.log(
                    "INFO",
                    "linkedin_analytics_retrieved",
                    {"post_id": post_id, **analytics},
                )
                
                return {"success": True, **analytics}
            else:
                return {
                    "success": False,
                    "error": f"LinkedIn API error: {response.status_code}",
                }
                
        except Exception as error:
            self.logger.log(
                "ERROR",
                "linkedin_analytics_error",
                {"post_id": post_id, "error": str(error)},
            )
            return {"success": False, "error": str(error)}
