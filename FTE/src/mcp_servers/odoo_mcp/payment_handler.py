"""Odoo Payment Handler - Payment recording and reconciliation."""

from datetime import datetime
from typing import Any

from ...audit_logger import AuditLogger
from ...utils.dev_mode import check_dev_mode
from .server import OdooMCPServer


class PaymentHandler:
    """Handler for Odoo payment operations."""
    
    def __init__(self, server: OdooMCPServer) -> None:
        """Initialize payment handler.
        
        Args:
            server: OdooMCP server instance
        """
        self.server = server
        self.logger = AuditLogger(component="odoo_payment_handler")
    
    def record_payment(
        self,
        invoice_id: int,
        amount: float,
        payment_date: str,
        payment_method: str = "bank",
        partner_id: int | None = None,
        dry_run: bool = False,
    ) -> dict[str, Any]:
        """Record payment in Odoo.
        
        Args:
            invoice_id: Invoice ID to pay
            amount: Payment amount
            payment_date: Payment date (YYYY-MM-DD)
            payment_method: Payment method (bank, cash, check, credit_card)
            partner_id: Partner ID (optional, inferred from invoice if not provided)
            dry_run: If True, log without creating
            
        Returns:
            dict with payment_id on success, error details on failure
        """
        # Validate DEV_MODE
        if not dry_run:
            check_dev_mode()
        
        # Validate required fields
        if not invoice_id:
            return {"success": False, "error": "invoice_id is required"}
        
        if not amount or amount <= 0:
            return {"success": False, "error": "amount must be positive"}
        
        # Validate payment method
        valid_methods = ["bank", "cash", "check", "credit_card"]
        if payment_method not in valid_methods:
            return {
                "success": False,
                "error": f"Invalid payment method. Must be one of: {valid_methods}",
            }
        
        if dry_run:
            self.logger.log(
                "INFO",
                "record_payment_dry_run",
                {
                    "invoice_id": invoice_id,
                    "amount": amount,
                    "payment_date": payment_date,
                    "payment_method": payment_method,
                },
                dry_run=True,
            )
            return {
                "success": True,
                "dry_run": True,
                "message": "Payment would be recorded (dry-run mode)",
            }
        
        try:
            # Get invoice details to find partner
            if not partner_id:
                invoice = self.server.search_read(
                    "account.move",
                    domain=[("id", "=", invoice_id)],
                    fields=["partner_id"],
                    limit=1,
                )
                if invoice and len(invoice) > 0:
                    partner_id = invoice[0].get("partner_id", [None])[0]
            
            if not partner_id:
                return {
                    "success": False,
                    "error": "Could not determine partner from invoice",
                }
            
            # Get payment journal based on method
            journal_code_map = {
                "bank": "BNK1",
                "cash": "CSH1",
                "check": "BNK1",
                "credit_card": "BNK1",
            }
            journal_code = journal_code_map.get(payment_method, "BNK1")
            
            journals = self.server.search_read(
                "account.journal",
                domain=[("code", "=", journal_code), ("type", "=", "bank")],
                fields=["id"],
                limit=1,
            )
            
            journal_id = journals[0]["id"] if journals else None
            
            if not journal_id:
                # Fallback to any bank journal
                journals = self.server.search_read(
                    "account.journal",
                    domain=[("type", "=", "bank")],
                    fields=["id"],
                    limit=1,
                )
                journal_id = journals[0]["id"] if journals else None
            
            if not journal_id:
                return {
                    "success": False,
                    "error": "No bank journal found",
                }
            
            # Create payment using account.payment.register wizard
            # This is the modern Odoo way to record payments
            payment_register_id = self.server.execute_kw(
                "account.payment.register",
                "create",
                args=[
                    {
                        "journal_id": journal_id,
                        "payment_date": payment_date,
                        "amount": amount,
                    }
                ],
            )
            
            if not payment_register_id:
                return {
                    "success": False,
                    "error": "Failed to create payment register",
                }
            
            # Create payments from register
            payment_result = self.server.execute_kw(
                "account.payment.register",
                "create_payments",
                args=[[payment_register_id]],
                kwargs={"active_ids": [invoice_id]},
            )
            
            if payment_result:
                payment_id = payment_result.get("res_id")
                
                self.logger.log(
                    "INFO",
                    "payment_recorded",
                    {
                        "payment_id": payment_id,
                        "invoice_id": invoice_id,
                        "amount": amount,
                        "payment_method": payment_method,
                    },
                )
                
                return {
                    "success": True,
                    "payment_id": payment_id,
                    "invoice_id": invoice_id,
                    "amount": amount,
                }
            else:
                return {
                    "success": False,
                    "error": "Failed to create payment",
                }
                
        except Exception as error:
            self.logger.log(
                "ERROR",
                "record_payment_error",
                {"error": str(error)},
            )
            return {"success": False, "error": str(error)}
    
    def get_payment(self, payment_id: int) -> dict[str, Any] | None:
        """Get payment details.
        
        Args:
            payment_id: Payment ID
            
        Returns:
            Payment data dict or None
        """
        result = self.server.search_read(
            "account.payment",
            domain=[("id", "=", payment_id)],
            fields=[
                "name",
                "partner_id",
                "payment_date",
                "amount",
                "payment_type",
                "state",
            ],
            limit=1,
        )
        
        if result and len(result) > 0:
            return result[0]
        return None
