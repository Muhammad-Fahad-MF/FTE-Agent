"""EmailMCP - Gmail API integration for FTE-Agent."""

from .server import EmailMCPServer
from .handlers import EmailHandlers

__all__ = ["EmailMCPServer", "EmailHandlers"]
