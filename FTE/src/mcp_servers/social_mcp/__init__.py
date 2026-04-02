"""SocialMCP - Unified social media integration for FTE-Agent."""

from .server import SocialMCPServer
from .linkedin_handler import LinkedInHandler
from .twitter_handler import TwitterHandler
from .facebook_handler import FacebookHandler
from .instagram_handler import InstagramHandler

__all__ = [
    "SocialMCPServer",
    "LinkedInHandler",
    "TwitterHandler",
    "FacebookHandler",
    "InstagramHandler",
]
