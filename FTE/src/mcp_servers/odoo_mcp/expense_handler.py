"""Odoo Expense Handler - Expense categorization and management."""

import re
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from ...audit_logger import AuditLogger
from ...utils.dev_mode import check_dev_mode
from .server import OdooMCPServer


@dataclass
class CategoryRule:
    """Category mapping rule."""
    
    keywords: list[str]
    category_name: str
    account_code: str | None = None


class ExpenseHandler:
    """Handler for Odoo expense operations."""
    
    def __init__(self, server: OdooMCPServer) -> None:
        """Initialize expense handler.
        
        Args:
            server: OdooMCP server instance
        """
        self.server = server
        self.logger = AuditLogger(component="odoo_expense_handler")
        
        # Category mapping rules
        self.category_rules: list[CategoryRule] = [
            CategoryRule(
                keywords=["office", "supplies", "stationery"],
                category_name="office_supplies",
                account_code="6064",
            ),
            CategoryRule(
                keywords=["travel", "flight", "hotel", "taxi", "uber"],
                category_name="travel",
                account_code="6251",
            ),
            CategoryRule(
                keywords=["software", "subscription", "saas", "license"],
                category_name="software",
                account_code="6226",
            ),
            CategoryRule(
                keywords=["utility", "electricity", "water", "internet", "phone"],
                category_name="utilities",
                account_code="6222",
            ),
            CategoryRule(
                keywords=["marketing", "advertising", "promotion", "ads"],
                category_name="marketing",
                account_code="6231",
            ),
            CategoryRule(
                keywords=["meal", "restaurant", "food", "lunch", "dinner"],
                category_name="meals",
                account_code="6256",
            ),
            CategoryRule(
                keywords=["fuel", "gas", "parking", "vehicle"],
                category_name="vehicle",
                account_code="6251",
            ),
        ]
    
    def categorize_expense(
        self,
        amount: float,
        description: str,
        date: str,
        account_id: int | None = None,
        dry_run: bool = False,
    ) -> dict[str, Any]:
        """Categorize and create expense in Odoo.
        
        Args:
            amount: Expense amount
            description: Expense description
            date: Expense date (YYYY-MM-DD)
            account_id: Optional account ID (auto-detected if not provided)
            dry_run: If True, log without creating
            
        Returns:
            dict with expense_id and category on success, error details on failure
        """
        # Validate DEV_MODE
        if not dry_run:
            check_dev_mode()
        
        # Validate required fields
        if not amount or amount <= 0:
            return {"success": False, "error": "amount must be positive"}
        
        if not description:
            return {"success": False, "error": "description is required"}
        
        # Auto-detect category from description
        category = self._map_category(description)
        
        if dry_run:
            self.logger.log(
                "INFO",
                "categorize_expense_dry_run",
                {
                    "amount": amount,
                    "description": description,
                    "category": category["category_name"],
                },
                dry_run=True,
            )
            return {
                "success": True,
                "dry_run": True,
                "category": category["category_name"],
                "message": "Expense would be categorized (dry-run mode)",
            }
        
        try:
            # Create expense using account.analytic.account or account.move
            # For simplicity, we'll create a vendor bill (account.move)
            
            # Get default expense account if not provided
            if not account_id and category.get("account_code"):
                accounts = self.server.search_read(
                    "account.account",
                    domain=[("code", "=", category["account_code"])],
                    fields=["id"],
                    limit=1,
                )
                if accounts:
                    account_id = accounts[0]["id"]
            
            # Create vendor bill
            bill_values = {
                "move_type": "in_invoice",
                "invoice_date": date,
                "state": "draft",
                "invoice_line_ids": [
                    (
                        0,
                        0,
                        {
                            "name": description,
                            "quantity": 1,
                            "price_unit": amount,
                            "account_id": account_id,
                        },
                    )
                ],
            }
            
            expense_id = self.server.create("account.move", bill_values)
            
            if expense_id:
                self.logger.log(
                    "INFO",
                    "expense_categorized",
                    {
                        "expense_id": expense_id,
                        "amount": amount,
                        "category": category["category_name"],
                    },
                )
                
                return {
                    "success": True,
                    "expense_id": expense_id,
                    "category": category["category_name"],
                    "category_keywords": category["keywords"],
                }
            else:
                return {
                    "success": False,
                    "error": "Failed to create expense",
                }
                
        except Exception as error:
            self.logger.log(
                "ERROR",
                "categorize_expense_error",
                {"error": str(error)},
            )
            return {"success": False, "error": str(error)}
    
    def _map_category(self, description: str) -> dict[str, Any]:
        """Map description to expense category using keyword matching.
        
        Args:
            description: Expense description
            
        Returns:
            Dict with category_name and keywords
        """
        description_lower = description.lower()
        
        for rule in self.category_rules:
            for keyword in rule.keywords:
                if re.search(rf"\b{keyword}\b", description_lower):
                    return {
                        "category_name": rule.category_name,
                        "keywords": rule.keywords,
                        "account_code": rule.account_code,
                    }
        
        # Default category if no match
        return {
            "category_name": "miscellaneous",
            "keywords": [],
            "account_code": None,
        }
    
    def get_category_rules(self) -> list[dict[str, Any]]:
        """Get all category mapping rules.
        
        Returns:
            List of category rules
        """
        return [
            {
                "category_name": rule.category_name,
                "keywords": rule.keywords,
                "account_code": rule.account_code,
            }
            for rule in self.category_rules
        ]
    
    def add_category_rule(
        self,
        category_name: str,
        keywords: list[str],
        account_code: str | None = None,
    ) -> None:
        """Add new category mapping rule.
        
        Args:
            category_name: Category name
            keywords: List of keywords to match
            account_code: Optional account code
        """
        self.category_rules.append(
            CategoryRule(
                keywords=keywords,
                category_name=category_name,
                account_code=account_code,
            )
        )
        
        self.logger.log(
            "INFO",
            "category_rule_added",
            {"category_name": category_name, "keywords": keywords},
        )
