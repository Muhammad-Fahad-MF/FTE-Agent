"""Rate Limiting Service - Centralized rate limit tracking for all platforms."""

import os
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

from ..audit_logger import AuditLogger


@dataclass
class RateLimitConfig:
    """Rate limit configuration for a platform."""
    
    max_requests: int
    window_seconds: int
    alert_threshold_percent: float = 80.0


class RateLimiter:
    """Centralized rate limiting service for all external APIs."""
    
    def __init__(self) -> None:
        """Initialize rate limiter with platform-specific configs."""
        self.logger = AuditLogger(component="rate_limiter")
        
        # Rate limit configurations per platform
        self.configs: dict[str, RateLimitConfig] = {
            "linkedin": RateLimitConfig(max_requests=1, window_seconds=86400),  # 1 per 24h
            "twitter": RateLimitConfig(max_requests=300, window_seconds=900),  # 300 per 15min
            "facebook": RateLimitConfig(max_requests=200, window_seconds=3600),  # 200 per hour
            "instagram": RateLimitConfig(max_requests=25, window_seconds=86400),  # 25 per day
            "gmail": RateLimitConfig(max_requests=1000, window_seconds=3600),  # 1000 per hour
            "odoo": RateLimitConfig(max_requests=500, window_seconds=3600),  # 500 per hour
        }
        
        # Tracking state per platform
        self.request_counts: dict[str, int] = {platform: 0 for platform in self.configs}
        self.window_starts: dict[str, datetime] = {
            platform: datetime.now() for platform in self.configs
        }
    
    def check_rate_limit(self, platform: str) -> tuple[bool, int]:
        """Check if request is within rate limit for platform.
        
        Args:
            platform: Platform name (linkedin, twitter, facebook, etc.)
            
        Returns:
            Tuple of (is_within_limit, seconds_until_reset)
        """
        if platform not in self.configs:
            self.logger.log(
                "WARNING",
                "rate_limit_unknown_platform",
                {"platform": platform},
            )
            return True, 0
        
        config = self.configs[platform]
        now = datetime.now()
        
        # Reset window if expired
        window_start = self.window_starts[platform]
        if now - window_start >= timedelta(seconds=config.window_seconds):
            self.request_counts[platform] = 0
            self.window_starts[platform] = now
            window_start = now
        
        # Check if within limit
        current_count = self.request_counts[platform]
        
        if current_count >= config.max_requests:
            seconds_remaining = int(
                (window_start + timedelta(seconds=config.window_seconds) - now).total_seconds()
            )
            
            self.logger.log(
                "WARNING",
                "rate_limit_exceeded",
                {
                    "platform": platform,
                    "current": current_count,
                    "max": config.max_requests,
                    "retry_after": seconds_remaining,
                },
            )
            
            return False, seconds_remaining
        
        # Check alert threshold
        usage_percent = (current_count / config.max_requests) * 100
        if usage_percent >= config.alert_threshold_percent:
            self.logger.log(
                "WARNING",
                "rate_limit_threshold",
                {
                    "platform": platform,
                    "usage_percent": usage_percent,
                    "current": current_count,
                    "max": config.max_requests,
                },
            )
        
        return True, 0
    
    def record_request(self, platform: str) -> None:
        """Record a request for rate limit tracking.
        
        Args:
            platform: Platform name
        """
        if platform not in self.configs:
            return
        
        self.request_counts[platform] += 1
        
        config = self.configs[platform]
        current_count = self.request_counts[platform]
        usage_percent = (current_count / config.max_requests) * 100
        
        self.logger.log(
            "DEBUG",
            "rate_limit_request_recorded",
            {
                "platform": platform,
                "current": current_count,
                "max": config.max_requests,
                "usage_percent": usage_percent,
            },
        )
    
    def get_rate_limit_status(self, platform: str) -> dict[str, Any]:
        """Get current rate limit status for platform.
        
        Args:
            platform: Platform name
            
        Returns:
            Dict with rate limit status information
        """
        if platform not in self.configs:
            return {"error": f"Unknown platform: {platform}"}
        
        config = self.configs[platform]
        now = datetime.now()
        window_start = self.window_starts[platform]
        
        # Calculate reset time
        reset_time = window_start + timedelta(seconds=config.window_seconds)
        seconds_until_reset = max(0, int((reset_time - now).total_seconds()))
        
        current_count = self.request_counts[platform]
        remaining = max(0, config.max_requests - current_count)
        usage_percent = (current_count / config.max_requests) * 100
        
        return {
            "platform": platform,
            "current_requests": current_count,
            "max_requests": config.max_requests,
            "remaining": remaining,
            "usage_percent": round(usage_percent, 2),
            "window_seconds": config.window_seconds,
            "seconds_until_reset": seconds_until_reset,
            "reset_time": reset_time.isoformat(),
            "is_limited": current_count >= config.max_requests,
        }
    
    def get_all_status(self) -> dict[str, dict[str, Any]]:
        """Get rate limit status for all platforms.
        
        Returns:
            Dict with status for all platforms
        """
        return {platform: self.get_rate_limit_status(platform) for platform in self.configs}
    
    def reset_platform(self, platform: str) -> None:
        """Reset rate limit counter for platform.
        
        Args:
            platform: Platform name
        """
        if platform not in self.configs:
            return
        
        self.request_counts[platform] = 0
        self.window_starts[platform] = datetime.now()
        
        self.logger.log(
            "INFO",
            "rate_limit_reset",
            {"platform": platform},
        )
