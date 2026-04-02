"""EmailMCP Handlers - Gmail API operations."""

import base64
import os
from email.mime.audio import MIMEAudio
from email.mime.base import MIMEBase
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import Any

from googleapiclient.errors import HttpError

from ...audit_logger import AuditLogger
from ...utils.dev_mode import check_dev_mode
from .server import EmailMCPServer


class EmailHandlers:
    """Handler functions for EmailMCP operations."""
    
    def __init__(self, server: EmailMCPServer) -> None:
        """Initialize email handlers.
        
        Args:
            server: EmailMCP server instance
        """
        self.server = server
        self.logger = AuditLogger(component="email_handlers")
    
    def send_email(
        self,
        to: str,
        subject: str,
        body: str,
        attachments: list[str] | None = None,
        dry_run: bool = False,
    ) -> dict[str, Any]:
        """Send email via Gmail API.
        
        Args:
            to: Recipient email address
            subject: Email subject
            body: Email body text
            attachments: Optional list of file paths to attach
            dry_run: If True, log without sending
            
        Returns:
            dict with message_id on success, error details on failure
        """
        # Validate DEV_MODE
        if not dry_run:
            check_dev_mode()
        
        try:
            # Create message
            message = self._create_message(to, subject, body, attachments)
            
            if dry_run:
                self.logger.log(
                    "INFO",
                    "send_email_dry_run",
                    {"to": to, "subject": subject, "attachments": attachments},
                    dry_run=True,
                )
                return {
                    "success": True,
                    "dry_run": True,
                    "to": to,
                    "subject": subject,
                    "message": "Email would be sent (dry-run mode)",
                }
            
            # Get service
            service = self.server.get_service()
            if not service:
                return {"success": False, "error": "Failed to authenticate with Gmail API"}
            
            # Send message
            sent_message = (
                service.users()
                .messages()
                .send(userId="me", body=message)
                .execute()
            )
            
            self.logger.log(
                "INFO",
                "email_sent",
                {"to": to, "subject": subject, "message_id": sent_message["id"]},
            )
            
            return {
                "success": True,
                "message_id": sent_message["id"],
                "to": to,
                "subject": subject,
            }
            
        except HttpError as error:
            self.logger.log(
                "ERROR",
                "send_email_failed",
                {"to": to, "subject": subject, "error": str(error), "status": error.status_code},
            )
            return {
                "success": False,
                "error": str(error),
                "status_code": error.status_code,
            }
        except Exception as error:
            self.logger.log(
                "ERROR",
                "send_email_error",
                {"to": to, "subject": subject, "error": str(error)},
            )
            return {"success": False, "error": str(error)}
    
    def draft_email(
        self,
        to: str,
        subject: str,
        body: str,
        attachments: list[str] | None = None,
        dry_run: bool = False,
    ) -> dict[str, Any]:
        """Create draft email in Gmail.
        
        Args:
            to: Recipient email address
            subject: Email subject
            body: Email body text
            attachments: Optional list of file paths to attach
            dry_run: If True, log without creating draft
            
        Returns:
            dict with draft_id on success, error details on failure
        """
        # Validate DEV_MODE
        if not dry_run:
            check_dev_mode()
        
        try:
            # Create message
            message = self._create_message(to, subject, body, attachments)
            
            if dry_run:
                self.logger.log(
                    "INFO",
                    "draft_email_dry_run",
                    {"to": to, "subject": subject, "attachments": attachments},
                    dry_run=True,
                )
                return {
                    "success": True,
                    "dry_run": True,
                    "to": to,
                    "subject": subject,
                    "message": "Draft would be created (dry-run mode)",
                }
            
            # Get service
            service = self.server.get_service()
            if not service:
                return {"success": False, "error": "Failed to authenticate with Gmail API"}
            
            # Create draft
            draft = (
                service.users()
                .drafts()
                .create(userId="me", body={"message": message})
                .execute()
            )
            
            self.logger.log(
                "INFO",
                "draft_created",
                {"to": to, "subject": subject, "draft_id": draft["id"]},
            )
            
            return {
                "success": True,
                "draft_id": draft["id"],
                "to": to,
                "subject": subject,
            }
            
        except HttpError as error:
            self.logger.log(
                "ERROR",
                "draft_email_failed",
                {"to": to, "subject": subject, "error": str(error), "status": error.status_code},
            )
            return {
                "success": False,
                "error": str(error),
                "status_code": error.status_code,
            }
        except Exception as error:
            self.logger.log(
                "ERROR",
                "draft_email_error",
                {"to": to, "subject": subject, "error": str(error)},
            )
            return {"success": False, "error": str(error)}
    
    def search_emails(
        self,
        query: str,
        max_results: int = 10,
        dry_run: bool = False,
    ) -> dict[str, Any]:
        """Search emails in Gmail.
        
        Args:
            query: Gmail search query (supports Gmail search operators)
            max_results: Maximum number of results to return
            dry_run: If True, return mock results
            
        Returns:
            dict with list of messages matching query
        """
        try:
            if dry_run:
                self.logger.log(
                    "INFO",
                    "search_emails_dry_run",
                    {"query": query, "max_results": max_results},
                    dry_run=True,
                )
                return {
                    "success": True,
                    "dry_run": True,
                    "query": query,
                    "messages": [],
                    "message": "Search would execute (dry-run mode)",
                }
            
            # Get service
            service = self.server.get_service()
            if not service:
                return {"success": False, "error": "Failed to authenticate with Gmail API"}
            
            # Search messages
            results = (
                service.users()
                .messages()
                .list(userId="me", q=query, maxResults=max_results)
                .execute()
            )
            
            messages = results.get("messages", [])
            
            # Get message details
            email_list = []
            for msg in messages:
                msg_detail = (
                    service.users()
                    .messages()
                    .get(userId="me", id=msg["id"], format="metadata")
                    .execute()
                )
                
                headers = msg_detail["payload"]["headers"]
                email_list.append({
                    "id": msg_detail["id"],
                    "snippet": msg_detail.get("snippet", ""),
                    "from": self._get_header(headers, "From"),
                    "to": self._get_header(headers, "To"),
                    "subject": self._get_header(headers, "Subject"),
                    "date": self._get_header(headers, "Date"),
                })
            
            self.logger.log(
                "INFO",
                "emails_searched",
                {"query": query, "results_count": len(email_list)},
            )
            
            return {
                "success": True,
                "query": query,
                "messages": email_list,
                "total_results": len(email_list),
            }
            
        except HttpError as error:
            self.logger.log(
                "ERROR",
                "search_emails_failed",
                {"query": query, "error": str(error), "status": error.status_code},
            )
            return {
                "success": False,
                "error": str(error),
                "status_code": error.status_code,
            }
        except Exception as error:
            self.logger.log(
                "ERROR",
                "search_emails_error",
                {"query": query, "error": str(error)},
            )
            return {"success": False, "error": str(error)}
    
    def _create_message(
        self,
        to: str,
        subject: str,
        body: str,
        attachments: list[str] | None = None,
    ) -> dict[str, Any]:
        """Create MIME message for Gmail API.
        
        Args:
            to: Recipient email address
            subject: Email subject
            body: Email body text
            attachments: Optional list of file paths to attach
            
        Returns:
            Base64 encoded message string
        """
        if attachments:
            # Create multipart message for attachments
            message = MIMEMultipart()
            message.attach(MIMEText(body, "plain"))
            
            for file_path in attachments:
                self._attach_file(message, file_path)
        else:
            # Simple text message
            message = MIMEText(body)
        
        message["to"] = to
        message["subject"] = subject
        
        # Encode message
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")
        return {"raw": raw_message}
    
    def _attach_file(self, message: MIMEMultipart, file_path: str) -> None:
        """Attach file to MIME message.
        
        Args:
            message: MIME message to attach to
            file_path: Path to file to attach
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Attachment not found: {file_path}")
        
        content = path.read_bytes()
        
        # Determine MIME type
        if path.suffix.lower() in [".jpg", ".jpeg", ".png", ".gif"]:
            part = MIMEImage(content, path.suffix[1:])
        elif path.suffix.lower() in [".pdf"]:
            part = MIMEApplication(content)
        else:
            part = MIMEBase("application", "octet-stream")
            part.set_content(content)
        
        part.add_header(
            "Content-Disposition",
            f"attachment; filename={path.name}",
        )
        message.attach(part)
    
    def _get_header(self, headers: list[dict[str, Any]], name: str) -> str:
        """Extract header value from headers list.
        
        Args:
            headers: List of header dicts from Gmail API
            name: Header name to find
            
        Returns:
            Header value or empty string
        """
        for header in headers:
            if header["name"] == name:
                return header["value"]
        return ""
