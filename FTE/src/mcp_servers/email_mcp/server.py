"""EmailMCP Server - Gmail API integration with OAuth2 authentication."""

import os
from pathlib import Path
from typing import Any

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from ...audit_logger import AuditLogger
from ...utils.dev_mode import check_dev_mode


class EmailMCPServer:
    """MCP Server for Gmail API operations.
    
    Provides email sending, drafting, and search capabilities via Gmail API.
    """
    
    SCOPES = [
        "https://www.googleapis.com/auth/gmail.send",
        "https://www.googleapis.com/auth/gmail.compose",
        "https://www.googleapis.com/auth/gmail.readonly",
    ]
    
    def __init__(self) -> None:
        """Initialize EmailMCP server."""
        self.logger = AuditLogger(component="email_mcp_server")
        self.service: Any = None
        self.credentials: Credentials | None = None
        
        # Configuration from environment
        self.client_id = os.getenv("GMAIL_CLIENT_ID")
        self.client_secret = os.getenv("GMAIL_CLIENT_SECRET")
        self.redirect_uri = os.getenv("GMAIL_REDIRECT_URI", "http://localhost:8080")
        
        # Token storage path
        vault_path = os.getenv("VAULT_PATH", "./vault")
        self.token_path = Path(vault_path) / ".credentials" / "gmail_token.json"
        self.token_path.parent.mkdir(parents=True, exist_ok=True)
    
    def authenticate(self) -> bool:
        """Authenticate with Gmail API using OAuth2.
        
        Returns:
            True if authentication successful, False otherwise
        """
        try:
            # Load existing credentials
            if self.token_path.exists():
                self.credentials = Credentials.from_authorized_user_file(
                    str(self.token_path), self.SCOPES
                )
            
            # Refresh or obtain new credentials
            if not self.credentials or not self.credentials.valid:
                if self.credentials and self.credentials.expired:
                    self.credentials.refresh(Request())
                    self._save_token()
                else:
                    # Interactive OAuth flow
                    flow = InstalledAppFlow.from_client_config(
                        {
                            "installed": {
                                "client_id": self.client_id,
                                "client_secret": self.client_secret,
                                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                                "token_uri": "https://oauth2.googleapis.com/token",
                                "redirect_uris": [self.redirect_uri],
                            }
                        },
                        self.SCOPES,
                    )
                    self.credentials = flow.run_local_server(port=8080)
                    self._save_token()
            
            # Build Gmail API service
            self.service = build("gmail", "v1", credentials=self.credentials)
            
            self.logger.log(
                "INFO",
                "email_mcp_authenticated",
                {"scopes": self.SCOPES},
            )
            return True
            
        except HttpError as error:
            self.logger.log(
                "ERROR",
                "email_mcp_auth_failed",
                {"error": str(error), "status": error.status_code},
            )
            return False
        except Exception as error:
            self.logger.log(
                "ERROR",
                "email_mcp_auth_error",
                {"error": str(error)},
            )
            return False
    
    def _save_token(self) -> None:
        """Save OAuth2 token to disk."""
        if self.credentials:
            self.token_path.write_text(self.credentials.to_json(), encoding="utf-8")
            self.token_path.chmod(0o600)  # Restrict access
    
    def get_service(self) -> Any | None:
        """Get authenticated Gmail API service.
        
        Returns:
            Gmail API service instance or None if not authenticated
        """
        if not self.service:
            if not self.authenticate():
                return None
        return self.service
    
    def shutdown(self) -> None:
        """Gracefully shutdown the server."""
        self.logger.log("INFO", "email_mcp_shutdown", {})
        self.service = None
        self.credentials = None
