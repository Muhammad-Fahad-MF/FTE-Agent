"""Twitter Handler - Twitter API v2 integration via tweepy."""

import os
from datetime import datetime, timedelta
from typing import Any

import tweepy

from ...audit_logger import AuditLogger
from ...utils.dev_mode import check_dev_mode


class TwitterHandler:
    """Handler for Twitter/X posting and analytics."""
    
    def __init__(self) -> None:
        """Initialize Twitter handler."""
        self.logger = AuditLogger(component="twitter_handler")
        
        # Configuration from environment
        self.api_key = os.getenv("TWITTER_API_KEY")
        self.api_secret = os.getenv("TWITTER_API_SECRET")
        self.access_token = os.getenv("TWITTER_ACCESS_TOKEN")
        self.access_token_secret = os.getenv("TWITTER_ACCESS_TOKEN_SECRET")
        self.bearer_token = os.getenv("TWITTER_BEARER_TOKEN")
        
        # Rate limiting: 300 posts per 15 minutes
        self.post_count = 0
        self.rate_limit_window = timedelta(minutes=15)
        self.window_start = datetime.now()
        self.max_posts_per_window = 300
        
        self.client: tweepy.Client | None = None
    
    def authenticate(self) -> bool:
        """Authenticate with Twitter API v2.
        
        Returns:
            True if authentication successful
        """
        if not all([self.api_key, self.api_secret, self.access_token, self.access_token_secret]):
            self.logger.log(
                "ERROR",
                "twitter_missing_credentials",
                {},
            )
            return False
        
        try:
            self.client = tweepy.Client(
                consumer_key=self.api_key,
                consumer_secret=self.api_secret,
                access_token=self.access_token,
                access_token_secret=self.access_token_secret,
                wait_on_rate_limit=True,
            )
            
            # Test authentication
            self.client.get_me()
            
            self.logger.log(
                "INFO",
                "twitter_authenticated",
                {},
            )
            
            return True
            
        except Exception as error:
            self.logger.log(
                "ERROR",
                "twitter_auth_error",
                {"error": str(error)},
            )
            return False
    
    def check_rate_limit(self) -> tuple[bool, int]:
        """Check if within rate limit (300 posts per 15 minutes).
        
        Returns:
            Tuple of (is_within_limit, seconds_until_reset)
        """
        now = datetime.now()
        
        # Reset window if expired
        if now - self.window_start >= self.rate_limit_window:
            self.post_count = 0
            self.window_start = now
        
        if self.post_count >= self.max_posts_per_window:
            seconds_remaining = int(
                (self.window_start + self.rate_limit_window - now).total_seconds()
            )
            return False, seconds_remaining
        
        return True, 0
    
    def post_twitter(
        self,
        text: str,
        media_urls: list[str] | None = None,
        dry_run: bool = False,
    ) -> dict[str, Any]:
        """Create tweet.
        
        Args:
            text: Tweet text (max 280 characters)
            media_urls: Optional list of media URLs to attach
            dry_run: If True, log without posting
            
        Returns:
            dict with tweet_id on success, error details on failure
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
        
        # Truncate text if needed
        if len(text) > 280:
            text = text[:277] + "..."
        
        if dry_run:
            self.logger.log(
                "INFO",
                "twitter_post_dry_run",
                {"text_length": len(text), "media_count": len(media_urls) if media_urls else 0},
                dry_run=True,
            )
            return {
                "success": True,
                "dry_run": True,
                "message": "Tweet would be created (dry-run mode)",
            }
        
        try:
            if not self.client:
                if not self.authenticate():
                    return {"success": False, "error": "Twitter authentication failed"}
            
            # Create tweet
            response = self.client.create_tweet(text=text)
            
            if response.data:
                tweet_id = response.data["id"]
                
                self.post_count += 1
                
                self.logger.log(
                    "INFO",
                    "twitter_post_created",
                    {"tweet_id": tweet_id, "text_length": len(text)},
                )
                
                return {
                    "success": True,
                    "tweet_id": tweet_id,
                    "text": text,
                }
            else:
                return {
                    "success": False,
                    "error": "Twitter API returned no data",
                }
                
        except Exception as error:
            self.logger.log(
                "ERROR",
                "twitter_post_error",
                {"error": str(error)},
            )
            return {"success": False, "error": str(error)}
    
    def get_twitter_analytics(
        self,
        tweet_id: str,
    ) -> dict[str, Any]:
        """Get tweet analytics.
        
        Args:
            tweet_id: Tweet ID
            
        Returns:
            dict with engagement metrics
        """
        try:
            if not self.client:
                if not self.authenticate():
                    return {"success": False, "error": "Twitter authentication failed"}
            
            # Get tweet with public metrics
            response = self.client.get_tweet(
                id=tweet_id,
                tweet_fields=["public_metrics"],
            )
            
            if response.data:
                metrics = response.data.public_metrics
                
                analytics = {
                    "likes": metrics.get("like_count", 0),
                    "retweets": metrics.get("retweet_count", 0),
                    "replies": metrics.get("reply_count", 0),
                    "impressions": metrics.get("impression_count", 0),
                }
                
                self.logger.log(
                    "INFO",
                    "twitter_analytics_retrieved",
                    {"tweet_id": tweet_id, **analytics},
                )
                
                return {"success": True, **analytics}
            else:
                return {
                    "success": False,
                    "error": "Tweet not found",
                }
                
        except Exception as error:
            self.logger.log(
                "ERROR",
                "twitter_analytics_error",
                {"tweet_id": tweet_id, "error": str(error)},
            )
            return {"success": False, "error": str(error)}
