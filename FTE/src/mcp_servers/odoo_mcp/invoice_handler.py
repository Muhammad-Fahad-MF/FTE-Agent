"""Odoo Invoice Handler - Invoice creation and management."""

from datetime import datetime
from typing import Any

from ...audit_logger import AuditLogger
from ...utils.dev_mode import check_dev_mode
from .server import OdooMCPServer


class InvoiceHandler:
    """Handler for Odoo invoice operations."""
    
    def __init__(self, server: OdooMCPServer) -> None:
        """Initialize invoice handler.
        
        Args:
            server: OdooMCP server instance
        """
        self.server = server
        self.logger = AuditLogger(component="odoo_invoice_handler")
    
    def create_invoice(
        self,
        partner_id: int,
        invoice_date: str,
        due_date: str,
        lines: list[dict[str, Any]],
        invoice_type: str = "out_invoice",
        dry_run: bool = False,
    ) -> dict[str, Any]:
        """Create invoice in Odoo.
        
        Args:
            partner_id: Customer/partner ID
            invoice_date: Invoice date (YYYY-MM-DD)
            due_date: Payment due date (YYYY-MM-DD)
            lines: List of invoice lines: [{description, quantity, price, account_id}]
            invoice_type: Type of invoice (out_invoice, in_invoice, out_refund, in_refund)
            dry_run: If True, log without creating
            
        Returns:
            dict with invoice_id on success, error details on failure
        """
        # Validate DEV_MODE
        if not dry_run:
            check_dev_mode()
        
        # Validate required fields
        if not partner_id:
            return {"success": False, "error": "partner_id is required"}
        
        if not lines or len(lines) == 0:
            return {"success": False, "error": "At least one invoice line is required"}
        
        # Validate invoice lines
        for i, line in enumerate(lines):
            if not line.get("description"):
                return {"success": False, "error": f"Line {i+1}: description is required"}
            if not line.get("quantity"):
                return {"success": False, "error": f"Line {i+1}: quantity is required"}
            if not line.get("price"):
                return {"success": False, "error": f"Line {i+1}: price is required"}
        
        if dry_run:
            self.logger.log(
                "INFO",
                "create_invoice_dry_run",
                {
                    "partner_id": partner_id,
                    "invoice_date": invoice_date,
                    "lines_count": len(lines),
                },
                dry_run=True,
            )
            return {
                "success": True,
                "dry_run": True,
                "message": "Invoice would be created (dry-run mode)",
            }
        
        try:
            # Create invoice header (account.move)
            invoice_values = {
                "move_type": invoice_type,
                "partner_id": partner_id,
                "invoice_date": invoice_date,
                "invoice_date_due": due_date,
                "state": "draft",
            }
            
            invoice_id = self.server.create("account.move", invoice_values)
            
            if not invoice_id:
                return {
                    "success": False,
                    "error": "Failed to create invoice",
                }
            
            # Create invoice lines (account.move.line)
            line_values_list = []
            for line in lines:
                line_values = {
                    "move_id": invoice_id,
                    "name": line["description"],
                    "quantity": line["quantity"],
                    "price_unit": line["price"],
                    "account_id": line.get("account_id"),  # Optional
                }
                line_values_list.append((0, 0, line_values))
            
            # Update invoice with lines
            update_success = self.server.execute_kw(
                "account.move",
                "write",
                args=[[invoice_id], {"invoice_line_ids": line_values_list}],
            )
            
            if update_success:
                self.logger.log(
                    "INFO",
                    "invoice_created",
                    {
                        "invoice_id": invoice_id,
                        "partner_id": partner_id,
                        "lines_count": len(lines),
                    },
                )
                
                return {
                    "success": True,
                    "invoice_id": invoice_id,
                    "partner_id": partner_id,
                }
            else:
                return {
                    "success": False,
                    "error": "Failed to add invoice lines",
                }
                
        except Exception as error:
            self.logger.log(
                "ERROR",
                "create_invoice_error",
                {"error": str(error)},
            )
            return {"success": False, "error": str(error)}
    
    def get_invoice(self, invoice_id: int) -> dict[str, Any] | None:
        """Get invoice details.
        
        Args:
            invoice_id: Invoice ID
            
        Returns:
            Invoice data dict or None
        """
        result = self.server.search_read(
            "account.move",
            domain=[("id", "=", invoice_id)],
            fields=[
                "name",
                "partner_id",
                "invoice_date",
                "invoice_date_due",
                "amount_total",
                "amount_untaxed",
                "amount_tax",
                "state",
            ],
            limit=1,
        )
        
        if result and len(result) > 0:
            return result[0]
        return None
    
    def confirm_invoice(self, invoice_id: int) -> bool:
        """Confirm invoice (post it).
        
        Args:
            invoice_id: Invoice ID
            
        Returns:
            True if successful
        """
        try:
            result = self.server.execute_kw(
                "account.move",
                "action_post",
                args=[[invoice_id]],
            )
            return result is not None
        except Exception:
            return False
