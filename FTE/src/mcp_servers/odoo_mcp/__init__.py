"""OdooMCP - Odoo JSON-RPC integration for FTE-Agent."""

from .server import OdooMCPServer
from .invoice_handler import InvoiceHandler
from .payment_handler import PaymentHandler
from .expense_handler import ExpenseHandler

__all__ = [
    "OdooMCPServer",
    "InvoiceHandler",
    "PaymentHandler",
    "ExpenseHandler",
]
