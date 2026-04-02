"""Briefing Skills for CEO briefing generation.

Usage:
    from src.skills.briefing_skills import (
        calculate_revenue,
        analyze_expenses,
        count_completed_tasks,
        identify_bottlenecks,
        audit_subscriptions,
        project_cash_flow,
        generate_suggestions,
        generate_ceo_briefing,
    )

    # Calculate revenue for period
    revenue = calculate_revenue(
        period_start=datetime(2026, 3, 24),
        period_end=datetime(2026, 3, 30)
    )

    # Generate complete CEO briefing
    briefing_path = generate_ceo_briefing()
"""

import os
import sys
import time
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from .base_skill import BaseSkill

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from models.ceo_briefing import (
    CEOBriefing,
    RevenueData,
    ExpensesData,
    Bottleneck,
    SubscriptionAudit,
    CashFlowProjection,
    ProactiveSuggestion,
)


# Subscription pattern matching for audit
SUBSCRIPTION_PATTERNS = {
    "netflix.com": "Netflix",
    "spotify.com": "Spotify",
    "adobe.com": "Adobe Creative Cloud",
    "notion.so": "Notion",
    "slack.com": "Slack",
    "microsoft.com": "Microsoft 365",
    "github.com": "GitHub",
    "aws.amazon.com": "Amazon Web Services",
    "azure.microsoft.com": "Microsoft Azure",
    "digitalocean.com": "DigitalOcean",
    "heroku.com": "Heroku",
    "vercel.com": "Vercel",
    "stripe.com": "Stripe",
    "zoom.us": "Zoom",
    "dropbox.com": "Dropbox",
    "box.com": "Box",
    "atlassian.com": "Atlassian",
    "jetbrains.com": "JetBrains",
    "figma.com": "Figma",
    "canva.com": "Canva",
}


def calculate_revenue(
    period_start: datetime,
    period_end: datetime,
    dry_run: bool = False,
    correlation_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Calculate revenue for a given period from Odoo invoices.

    Args:
        period_start: Start of period (Monday 12:00 AM)
        period_end: End of period (Sunday 11:59 PM)
        dry_run: If True, log actions without executing
        correlation_id: Unique ID for tracking

    Returns:
        Dict with keys: total, by_source, trend_percentage
    """
    skill = BriefingSkill(dry_run=dry_run, correlation_id=correlation_id)
    return skill.calculate_revenue(period_start, period_end)


def analyze_expenses(
    period_start: datetime,
    period_end: datetime,
    dry_run: bool = False,
    correlation_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Analyze expenses for a given period from Odoo transactions.

    Args:
        period_start: Start of period
        period_end: End of period
        dry_run: If True, log actions without executing
        correlation_id: Unique ID for tracking

    Returns:
        Dict with keys: total, by_category, trend_percentage
    """
    skill = BriefingSkill(dry_run=dry_run, correlation_id=correlation_id)
    return skill.analyze_expenses(period_start, period_end)


def count_completed_tasks(
    period_start: datetime,
    period_end: datetime,
    dry_run: bool = False,
    correlation_id: Optional[str] = None,
    vault_dir: Optional[Path] = None,
) -> Dict[str, Any]:
    """Count completed tasks from /Done/ folder for a given period.

    Args:
        period_start: Start of period
        period_end: End of period
        dry_run: If True, log actions without executing
        correlation_id: Unique ID for tracking
        vault_dir: Base vault directory

    Returns:
        Dict with keys: total, by_type
    """
    skill = BriefingSkill(dry_run=dry_run, correlation_id=correlation_id, vault_dir=vault_dir)
    return skill.count_completed_tasks(period_start, period_end)


def identify_bottlenecks(
    period_start: datetime,
    period_end: datetime,
    dry_run: bool = False,
    correlation_id: Optional[str] = None,
    vault_dir: Optional[Path] = None,
) -> List[Dict[str, str]]:
    """Identify bottlenecks from Plan.md files for a given period.

    Args:
        period_start: Start of period
        period_end: End of period
        dry_run: If True, log actions without executing
        correlation_id: Unique ID for tracking
        vault_dir: Base vault directory

    Returns:
        List of bottleneck dicts: {task, expected, actual, delay}
    """
    skill = BriefingSkill(dry_run=dry_run, correlation_id=correlation_id, vault_dir=vault_dir)
    return skill.identify_bottlenecks(period_start, period_end)


def audit_subscriptions(
    dry_run: bool = False,
    correlation_id: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Audit subscriptions by analyzing transactions.

    Args:
        dry_run: If True, log actions without executing
        correlation_id: Unique ID for tracking

    Returns:
        List of subscription audit dicts: {name, cost, last_used, recommendation}
    """
    skill = BriefingSkill(dry_run=dry_run, correlation_id=correlation_id)
    return skill.audit_subscriptions()


def project_cash_flow(
    dry_run: bool = False,
    correlation_id: Optional[str] = None,
) -> Dict[str, float]:
    """Project cash flow for 30/60/90 days based on historical data.

    Args:
        dry_run: If True, log actions without executing
        correlation_id: Unique ID for tracking

    Returns:
        Dict with keys: 30_day, 60_day, 90_day
    """
    skill = BriefingSkill(dry_run=dry_run, correlation_id=correlation_id)
    return skill.project_cash_flow()


def generate_suggestions(
    briefing_data: Dict[str, Any],
    dry_run: bool = False,
    correlation_id: Optional[str] = None,
    vault_dir: Optional[Path] = None,
) -> List[Dict[str, Any]]:
    """Generate proactive suggestions based on briefing data.

    Args:
        briefing_data: Complete briefing data from other skills
        dry_run: If True, log actions without executing
        correlation_id: Unique ID for tracking
        vault_dir: Base vault directory

    Returns:
        List of suggestion dicts: {suggestion, priority, action_file}
    """
    skill = BriefingSkill(dry_run=dry_run, correlation_id=correlation_id, vault_dir=vault_dir)
    return skill.generate_suggestions(briefing_data)


def generate_ceo_briefing(
    dry_run: bool = False,
    correlation_id: Optional[str] = None,
    vault_dir: Optional[Path] = None,
) -> Path:
    """Generate complete CEO briefing for the previous week.

    Orchestrates all briefing skills in sequence:
    1. Calculate revenue
    2. Analyze expenses
    3. Count completed tasks
    4. Identify bottlenecks
    5. Audit subscriptions
    6. Project cash flow
    7. Generate suggestions
    8. Create and save CEOBriefing

    Args:
        dry_run: If True, log actions without executing
        correlation_id: Unique ID for tracking
        vault_dir: Base vault directory

    Returns:
        Path to generated briefing file
    """
    skill = BriefingSkill(dry_run=dry_run, correlation_id=correlation_id, vault_dir=vault_dir)
    return skill.generate_ceo_briefing()


class BriefingSkill(BaseSkill):
    """Skill for generating CEO briefings and business analytics.

    Attributes:
        vault_dir: Base directory for vault storage
        briefings_dir: Directory for generated briefings
        done_dir: Directory for completed tasks
        plans_dir: Directory for plans
    """

    def __init__(
        self,
        dry_run: bool = False,
        correlation_id: Optional[str] = None,
        vault_dir: Optional[Path] = None,
    ) -> None:
        """Initialize briefing skill.

        Args:
            dry_run: If True, log actions without executing
            correlation_id: Unique ID for tracking
            vault_dir: Base vault directory (default: FTE/vault)
        """
        super().__init__(dry_run=dry_run, correlation_id=correlation_id)

        # Resolve vault directory
        if vault_dir is None:
            vault_dir = Path(__file__).parent.parent.parent / "vault"
        self.vault_dir = Path(vault_dir).resolve()

        self.briefings_dir = self.vault_dir / "Briefings"
        self.done_dir = self.vault_dir / "Done"
        self.plans_dir = self.vault_dir / "Plans"
        self.logs_dir = self.vault_dir / "Logs"

        # Ensure directories exist
        self.briefings_dir.mkdir(parents=True, exist_ok=True)
        self.done_dir.mkdir(parents=True, exist_ok=True)

    def _get_previous_week(self) -> tuple[datetime, datetime]:
        """Get the previous week's Monday and Sunday.

        Returns:
            Tuple of (period_start, period_end)
        """
        today = datetime.now()
        # Find last Monday
        days_since_monday = today.weekday()
        last_monday = today - timedelta(days=days_since_monday, weeks=1)
        last_monday = last_monday.replace(hour=0, minute=0, second=0, microsecond=0)

        # Sunday is 6 days after Monday
        last_sunday = last_monday + timedelta(days=6, hours=23, minutes=59, seconds=59)

        return last_monday, last_sunday

    def _query_odoo_invoices(
        self,
        period_start: datetime,
        period_end: datetime,
    ) -> List[Dict[str, Any]]:
        """Query Odoo for invoices in period.

        Note: This is a stub implementation. In production, this would
        call the Odoo JSON-RPC API.

        Args:
            period_start: Start of period
            period_end: End of period

        Returns:
            List of invoice dicts
        """
        # TODO: Implement Odoo JSON-RPC call
        # Example:
        # invoices = odoo_execute_kw(
        #     'account.move',
        #     'search_read',
        #     [[
        #         ('move_type', '=', 'out_invoice'),
        #         ('date', '>=', period_start.strftime('%Y-%m-%d')),
        #         ('date', '<=', period_end.strftime('%Y-%m-%d')),
        #         ('payment_state', '=', 'paid')
        #     ]],
        #     ['id', 'name', 'partner_id', 'amount_total', 'date']
        # )

        self.logger.log(
            "INFO",
            "query_odoo_invoices",
            {
                "period_start": period_start.isoformat(),
                "period_end": period_end.isoformat(),
                "note": "Stub implementation - returns empty list",
            },
            correlation_id=self.correlation_id,
        )

        return []

    def _query_odoo_expenses(
        self,
        period_start: datetime,
        period_end: datetime,
    ) -> List[Dict[str, Any]]:
        """Query Odoo for expenses in period.

        Note: This is a stub implementation.

        Args:
            period_start: Start of period
            period_end: End of period

        Returns:
            List of expense dicts
        """
        # TODO: Implement Odoo JSON-RPC call for expenses
        self.logger.log(
            "INFO",
            "query_odoo_expenses",
            {
                "period_start": period_start.isoformat(),
                "period_end": period_end.isoformat(),
                "note": "Stub implementation - returns empty list",
            },
            correlation_id=self.correlation_id,
        )

        return []

    def calculate_revenue(
        self,
        period_start: datetime,
        period_end: datetime,
    ) -> Dict[str, Any]:
        """Calculate revenue for a given period.

        Args:
            period_start: Start of period
            period_end: End of period

        Returns:
            Dict with keys: total, by_source, trend_percentage
        """
        start_time = time.time()

        try:
            # Query Odoo for paid invoices
            invoices = self._query_odoo_invoices(period_start, period_end)

            # Calculate total revenue
            total = sum(inv.get("amount_total", 0) for inv in invoices)

            # Group by source (partner)
            by_source: Dict[str, float] = {}
            for inv in invoices:
                partner = inv.get("partner_id", ["Unknown"])[1] if isinstance(inv.get("partner_id"), list) else "Unknown"
                by_source[partner] = by_source.get(partner, 0) + inv.get("amount_total", 0)

            # Calculate trend vs previous period (stub - would need previous period data)
            trend_percentage = 0.0  # TODO: Calculate from previous period

            result = {
                "total": total,
                "by_source": by_source,
                "trend_percentage": trend_percentage,
            }

            elapsed = time.time() - start_time
            self.logger.log(
                "INFO",
                "calculate_revenue",
                {
                    "total": total,
                    "by_source_count": len(by_source),
                    "trend_percentage": trend_percentage,
                    "elapsed_seconds": elapsed,
                },
                correlation_id=self.correlation_id,
            )

            return result

        except Exception as e:
            self.logger.log(
                "ERROR",
                "calculate_revenue_failed",
                {"error": str(e)},
                correlation_id=self.correlation_id,
            )
            # Return zero revenue on error
            return {"total": 0, "by_source": {}, "trend_percentage": 0.0}

    def analyze_expenses(
        self,
        period_start: datetime,
        period_end: datetime,
    ) -> Dict[str, Any]:
        """Analyze expenses for a given period.

        Args:
            period_start: Start of period
            period_end: End of period

        Returns:
            Dict with keys: total, by_category, trend_percentage
        """
        start_time = time.time()

        try:
            # Query Odoo for expenses
            expenses = self._query_odoo_expenses(period_start, period_end)

            # Calculate total expenses
            total = sum(exp.get("amount", 0) for exp in expenses)

            # Group by category
            by_category: Dict[str, float] = {}
            for exp in expenses:
                category = exp.get("category", "uncategorized")
                by_category[category] = by_category.get(category, 0) + exp.get("amount", 0)

            # Calculate trend vs previous period (stub)
            trend_percentage = 0.0  # TODO: Calculate from previous period

            result = {
                "total": total,
                "by_category": by_category,
                "trend_percentage": trend_percentage,
            }

            elapsed = time.time() - start_time
            self.logger.log(
                "INFO",
                "analyze_expenses",
                {
                    "total": total,
                    "by_category_count": len(by_category),
                    "trend_percentage": trend_percentage,
                    "elapsed_seconds": elapsed,
                },
                correlation_id=self.correlation_id,
            )

            return result

        except Exception as e:
            self.logger.log(
                "ERROR",
                "analyze_expenses_failed",
                {"error": str(e)},
                correlation_id=self.correlation_id,
            )
            return {"total": 0, "by_category": {}, "trend_percentage": 0.0}

    def count_completed_tasks(
        self,
        period_start: datetime,
        period_end: datetime,
    ) -> Dict[str, Any]:
        """Count completed tasks from /Done/ folder.

        Args:
            period_start: Start of period
            period_end: End of period

        Returns:
            Dict with keys: total, by_type
        """
        start_time = time.time()

        try:
            if not self.done_dir.exists():
                return {"total": 0, "by_type": {}}

            # Count files by type
            by_type: Dict[str, int] = {}
            total = 0

            for file_path in self.done_dir.glob("*.md"):
                # Check if file was created/moved in period
                file_mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                if period_start <= file_mtime <= period_end:
                    total += 1

                    # Classify by type
                    file_type = self._classify_file_type(file_path)
                    by_type[file_type] = by_type.get(file_type, 0) + 1

            result = {"total": total, "by_type": by_type}

            elapsed = time.time() - start_time
            self.logger.log(
                "INFO",
                "count_completed_tasks",
                {
                    "total": total,
                    "by_type": by_type,
                    "elapsed_seconds": elapsed,
                },
                correlation_id=self.correlation_id,
            )

            return result

        except Exception as e:
            self.logger.log(
                "ERROR",
                "count_completed_tasks_failed",
                {"error": str(e)},
                correlation_id=self.correlation_id,
            )
            return {"total": 0, "by_type": {}}

    def _classify_file_type(self, file_path: Path) -> str:
        """Classify action file by type.

        Args:
            file_path: Path to action file

        Returns:
            Type string: email, invoice, post, approval, other
        """
        try:
            content = file_path.read_text(encoding="utf-8")

            # Parse YAML frontmatter
            if "---" in content:
                parts = content.split("---", 2)
                if len(parts) >= 2:
                    try:
                        frontmatter = yaml.safe_load(parts[1])
                        file_type = frontmatter.get("type", "other")
                        return str(file_type) if file_type else "other"
                    except yaml.YAMLError:
                        pass

            # Fallback: classify by filename
            filename = file_path.name.lower()
            if "email" in filename:
                return "email"
            elif "invoice" in filename:
                return "invoice"
            elif "post" in filename:
                return "post"
            elif "approval" in filename:
                return "approval"
            else:
                return "other"

        except Exception:
            return "other"

    def identify_bottlenecks(
        self,
        period_start: datetime,
        period_end: datetime,
    ) -> List[Dict[str, str]]:
        """Identify bottlenecks from Plan.md files.

        Args:
            period_start: Start of period
            period_end: End of period

        Returns:
            List of bottleneck dicts
        """
        bottlenecks: List[Dict[str, str]] = []

        try:
            if not self.plans_dir.exists():
                return bottlenecks

            # Scan Plan.md files
            for plan_file in self.plans_dir.glob("*.md"):
                try:
                    content = plan_file.read_text(encoding="utf-8")

                    # Parse tasks with expected/actual completion
                    # Look for patterns like:
                    # - Expected: 2 days
                    # - Actual: 5 days
                    lines = content.split("\n")
                    for i, line in enumerate(lines):
                        if "expected" in line.lower() and "day" in line.lower():
                            # Found expected duration
                            expected = line.strip()
                            actual = ""
                            delay = ""

                            # Look for actual duration in next few lines
                            for j in range(i + 1, min(i + 5, len(lines))):
                                if "actual" in lines[j].lower():
                                    actual = lines[j].strip()
                                    # Calculate delay
                                    # This is a simplified parsing - would need more robust logic
                                    delay = "> 2 days"  # Stub
                                    break

                            if actual and delay:
                                bottlenecks.append({
                                    "task": plan_file.name,
                                    "expected": expected,
                                    "actual": actual,
                                    "delay": delay,
                                })

                except Exception as e:
                    self.logger.log(
                        "WARNING",
                        "parse_plan_failed",
                        {"file": str(plan_file), "error": str(e)},
                        correlation_id=self.correlation_id,
                    )

            self.logger.log(
                "INFO",
                "identify_bottlenecks",
                {"bottleneck_count": len(bottlenecks)},
                correlation_id=self.correlation_id,
            )

        except Exception as e:
            self.logger.log(
                "ERROR",
                "identify_bottlenecks_failed",
                {"error": str(e)},
                correlation_id=self.correlation_id,
            )

        return bottlenecks

    def audit_subscriptions(self) -> List[Dict[str, Any]]:
        """Audit subscriptions by analyzing transactions.

        Returns:
            List of subscription audit dicts
        """
        audits: List[Dict[str, Any]] = []

        try:
            # Query Odoo for recurring transactions
            expenses = self._query_odoo_expenses(
                datetime.now() - timedelta(days=90),
                datetime.now(),
            )

            # Match against subscription patterns
            matched_subscriptions: Dict[str, Dict[str, Any]] = {}

            for exp in expenses:
                description = exp.get("description", "").lower()
                for pattern, name in SUBSCRIPTION_PATTERNS.items():
                    if pattern in description:
                        if name not in matched_subscriptions:
                            matched_subscriptions[name] = {
                                "name": name,
                                "cost": 0,
                                "transactions": [],
                                "last_used": None,
                            }
                        matched_subscriptions[name]["cost"] += exp.get("amount", 0)
                        matched_subscriptions[name]["transactions"].append(exp)
                        exp_date = exp.get("date")
                        if exp_date:
                            if (
                                matched_subscriptions[name]["last_used"] is None
                                or exp_date > matched_subscriptions[name]["last_used"]
                            ):
                                matched_subscriptions[name]["last_used"] = exp_date

            # Generate audit entries with recommendations
            for name, data in matched_subscriptions.items():
                last_used = data["last_used"]
                recommendation = "Keep - actively used"

                # Check if unused for > 30 days (stub - would need actual usage data)
                if last_used:
                    days_since_use = (datetime.now() - last_used).days
                    if days_since_use > 30:
                        recommendation = f"Cancel - unused for {days_since_use} days"

                audits.append({
                    "name": name,
                    "cost": data["cost"],
                    "last_used": last_used.isoformat() if last_used else "Unknown",
                    "recommendation": recommendation,
                })

            self.logger.log(
                "INFO",
                "audit_subscriptions",
                {"audit_count": len(audits)},
                correlation_id=self.correlation_id,
            )

        except Exception as e:
            self.logger.log(
                "ERROR",
                "audit_subscriptions_failed",
                {"error": str(e)},
                correlation_id=self.correlation_id,
            )

        return audits

    def project_cash_flow(self) -> Dict[str, float]:
        """Project cash flow for 30/60/90 days.

        Returns:
            Dict with keys: 30_day, 60_day, 90_day
        """
        try:
            # Get historical data (last 90 days)
            period_end = datetime.now()
            period_start = period_end - timedelta(days=90)

            revenue_data = self.calculate_revenue(period_start, period_end)
            expense_data = self.analyze_expenses(period_start, period_end)

            # Calculate monthly averages
            avg_monthly_revenue = revenue_data["total"] / 3
            avg_monthly_expenses = expense_data["total"] / 3
            avg_monthly_profit = avg_monthly_revenue - avg_monthly_expenses

            # Project forward (simplified linear projection)
            # In production, would use more sophisticated forecasting
            current_balance = 0  # TODO: Get from Odoo/bank integration

            result = {
                "30_day": current_balance + (avg_monthly_profit * 1),
                "60_day": current_balance + (avg_monthly_profit * 2),
                "90_day": current_balance + (avg_monthly_profit * 3),
            }

            self.logger.log(
                "INFO",
                "project_cash_flow",
                result,
                correlation_id=self.correlation_id,
            )

            return result

        except Exception as e:
            self.logger.log(
                "ERROR",
                "project_cash_flow_failed",
                {"error": str(e)},
                correlation_id=self.correlation_id,
            )
            return {"30_day": 0, "60_day": 0, "90_day": 0}

    def generate_suggestions(
        self,
        briefing_data: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """Generate proactive suggestions based on briefing data.

        Args:
            briefing_data: Complete briefing data

        Returns:
            List of suggestion dicts
        """
        suggestions: List[Dict[str, Any]] = []

        try:
            # Rule 1: Unused subscriptions > $50/month
            for sub in briefing_data.get("subscription_audit", []):
                if sub.get("cost", 0) > 50 and "cancel" in sub.get("recommendation", "").lower():
                    suggestions.append({
                        "suggestion": f"Cancel unused subscription: {sub['name']} (saves ${sub['cost']:.2f}/month)",
                        "priority": "high",
                        "action_file": f"APPROVAL_cancel_{sub['name'].lower().replace(' ', '_')}.md",
                    })

            # Rule 2: Revenue trend < -10%
            revenue_trend = briefing_data.get("revenue", {}).get("trend_percentage", 0)
            if revenue_trend < -10:
                suggestions.append({
                    "suggestion": "Investigate revenue decline - down {abs(revenue_trend):.1f}% vs previous period",
                    "priority": "high",
                    "action_file": "APPROVAL_revenue_review.md",
                })

            # Rule 3: Expense trend > 20%
            expense_trend = briefing_data.get("expenses", {}).get("trend_percentage", 0)
            if expense_trend > 20:
                suggestions.append({
                    "suggestion": f"Review expense categories for cost reduction - up {expense_trend:.1f}% vs previous period",
                    "priority": "medium",
                    "action_file": "APPROVAL_expense_review.md",
                })

            # Rule 4: Bottlenecks identified
            bottlenecks = briefing_data.get("bottlenecks", [])
            if bottlenecks:
                suggestions.append({
                    "suggestion": f"Address {len(bottlenecks)} bottleneck(s) delaying task completion",
                    "priority": "medium",
                    "action_file": "APPROVAL_bottleneck_review.md",
                })

            self.logger.log(
                "INFO",
                "generate_suggestions",
                {"suggestion_count": len(suggestions)},
                correlation_id=self.correlation_id,
            )

        except Exception as e:
            self.logger.log(
                "ERROR",
                "generate_suggestions_failed",
                {"error": str(e)},
                correlation_id=self.correlation_id,
            )

        return suggestions

    def generate_ceo_briefing(self) -> Path:
        """Generate complete CEO briefing.

        Returns:
            Path to generated briefing file
        """
        start_time = time.time()

        try:
            # Get previous week's date range
            period_start, period_end = self._get_previous_week()

            self.logger.log(
                "INFO",
                "generate_ceo_briefing_started",
                {
                    "period_start": period_start.isoformat(),
                    "period_end": period_end.isoformat(),
                },
                correlation_id=self.correlation_id,
            )

            # Call all briefing skills in sequence
            revenue_data = self.calculate_revenue(period_start, period_end)
            expense_data = self.analyze_expenses(period_start, period_end)
            tasks_data = self.count_completed_tasks(period_start, period_end)
            bottlenecks = self.identify_bottlenecks(period_start, period_end)
            subscriptions = self.audit_subscriptions()
            cash_flow = self.project_cash_flow()

            # Build briefing data dict
            briefing_data = {
                "revenue": revenue_data,
                "expenses": expense_data,
                "tasks_completed": tasks_data["total"],
                "bottlenecks": bottlenecks,
                "subscription_audit": subscriptions,
                "cash_flow_projection": cash_flow,
            }

            # Generate suggestions
            suggestions = self.generate_suggestions(briefing_data)

            # Create CEOBriefing instance
            briefing = CEOBriefing(
                period_start=period_start,
                period_end=period_end,
                revenue=RevenueData(
                    total=revenue_data["total"],
                    by_source=revenue_data["by_source"],
                    trend_percentage=revenue_data["trend_percentage"],
                ),
                expenses=ExpensesData(
                    total=expense_data["total"],
                    by_category=expense_data["by_category"],
                    trend_percentage=expense_data["trend_percentage"],
                ),
                tasks_completed=tasks_data["total"],
                bottlenecks=[
                    Bottleneck(**bn) if isinstance(bn, dict) else bn
                    for bn in bottlenecks
                ],
                subscription_audit=[
                    SubscriptionAudit(**sub) if isinstance(sub, dict) else sub
                    for sub in subscriptions
                ],
                cash_flow_projection=CashFlowProjection(
                    day_30=cash_flow["30_day"],
                    day_60=cash_flow["60_day"],
                    day_90=cash_flow["90_day"],
                ) if cash_flow else None,
                proactive_suggestions=[
                    ProactiveSuggestion(**sug) if isinstance(sug, dict) else sug
                    for sug in suggestions
                ],
            )

            # Save to file
            briefing_path = briefing.save_to_file(output_dir=self.briefings_dir)

            elapsed = time.time() - start_time
            self.logger.log(
                "INFO",
                "generate_ceo_briefing_completed",
                {
                    "briefing_path": str(briefing_path),
                    "elapsed_seconds": elapsed,
                    "target_seconds": 60,
                },
                correlation_id=self.correlation_id,
            )

            # Validate generation time
            if elapsed > 60:
                self.logger.log(
                    "WARNING",
                    "briefing_generation_slow",
                    {
                        "elapsed_seconds": elapsed,
                        "target_seconds": 60,
                    },
                    correlation_id=self.correlation_id,
                )

            return briefing_path

        except Exception as e:
            self.logger.log(
                "ERROR",
                "generate_ceo_briefing_failed",
                {"error": str(e)},
                correlation_id=self.correlation_id,
            )
            raise
