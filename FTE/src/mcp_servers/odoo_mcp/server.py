"""OdooMCP Server - Odoo JSON-RPC API integration."""

import json
import os
from typing import Any

import requests

from ...audit_logger import AuditLogger


class OdooMCPServer:
    """MCP Server for Odoo JSON-RPC API operations.
    
    Provides accounting operations via Odoo's JSON-RPC interface.
    """
    
    def __init__(self) -> None:
        """Initialize OdooMCP server."""
        self.logger = AuditLogger(component="odoo_mcp_server")
        
        # Configuration from environment
        self.host = os.getenv("ODOO_HOST", "localhost")
        self.port = os.getenv("ODOO_PORT", "8069")
        self.db = os.getenv("ODOO_DB", "odoo_db")
        self.username = os.getenv("ODOO_USERNAME", "admin")
        self.password = os.getenv("ODOO_PASSWORD", "admin")
        
        self.endpoint = f"http://{self.host}:{self.port}/jsonrpc"
        self.uid: int | None = None
        
        self.is_running = False
    
    def authenticate(self) -> bool:
        """Authenticate with Odoo via JSON-RPC.
        
        Returns:
            True if authentication successful
        """
        try:
            payload = {
                "jsonrpc": "2.0",
                "method": "call",
                "params": {
                    "service": "common",
                    "method": "authenticate",
                    "args": [self.db, self.username, self.password, {}],
                },
            }
            
            response = requests.post(self.endpoint, json=payload, timeout=30)
            result = response.json()
            
            if "result" in result:
                self.uid = result["result"]
                
                if self.uid:
                    self.is_running = True
                    
                    self.logger.log(
                        "INFO",
                        "odoo_authenticated",
                        {"uid": self.uid, "db": self.db},
                    )
                    return True
                else:
                    self.logger.log(
                        "ERROR",
                        "odoo_auth_failed",
                        {"reason": "Invalid credentials"},
                    )
                    return False
            else:
                self.logger.log(
                    "ERROR",
                    "odoo_auth_error",
                    {"error": result.get("error", "Unknown error")},
                )
                return False
                
        except Exception as error:
            self.logger.log(
                "ERROR",
                "odoo_auth_exception",
                {"error": str(error)},
            )
            return False
    
    def execute_kw(
        self,
        model: str,
        method: str,
        args: list[Any] | None = None,
        kwargs: dict[str, Any] | None = None,
    ) -> Any:
        """Execute Odoo model method via JSON-RPC.
        
        Args:
            model: Odoo model name (e.g., 'account.move')
            method: Method to call (e.g., 'create', 'search_read')
            args: Positional arguments for the method
            kwargs: Keyword arguments for the method
            
        Returns:
            Method result
        """
        if not self.uid:
            if not self.authenticate():
                return None
        
        payload = {
            "jsonrpc": "2.0",
            "method": "call",
            "params": {
                "service": "object",
                "method": "execute_kw",
                "args": [
                    self.db,
                    self.uid,
                    self.password,
                    model,
                    method,
                    args or [],
                    kwargs or {},
                ],
            },
        }
        
        try:
            response = requests.post(self.endpoint, json=payload, timeout=30)
            result = response.json()
            
            if "result" in result:
                return result["result"]
            else:
                self.logger.log(
                    "ERROR",
                    "odoo_execute_error",
                    {
                        "model": model,
                        "method": method,
                        "error": result.get("error", "Unknown error"),
                    },
                )
                return None
                
        except Exception as error:
            self.logger.log(
                "ERROR",
                "odoo_execute_exception",
                {"model": model, "method": method, "error": str(error)},
            )
            return None
    
    def search_read(
        self,
        model: str,
        domain: list[Any] | None = None,
        fields: list[str] | None = None,
        limit: int = 80,
    ) -> list[dict[str, Any]]:
        """Search and read records from Odoo.
        
        Args:
            model: Odoo model name
            domain: Search domain (Odoo filter syntax)
            fields: List of fields to return
            limit: Maximum number of records
            
        Returns:
            List of record dicts
        """
        return self.execute_kw(
            model,
            "search_read",
            args=[domain or [], fields or []],
            kwargs={"limit": limit},
        )
    
    def create(self, model: str, values: dict[str, Any]) -> int | None:
        """Create record in Odoo.
        
        Args:
            model: Odoo model name
            values: Field values for the new record
            
        Returns:
            New record ID or None on failure
        """
        result = self.execute_kw(model, "create", args=[values])
        return result
    
    def shutdown(self) -> None:
        """Gracefully shutdown the server."""
        self.is_running = False
        self.uid = None
        self.logger.log("INFO", "odoo_mcp_shutdown", {})
