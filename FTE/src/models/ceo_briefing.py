"""CEOBriefing data model for weekly business intelligence reports.

Usage:
    from src.models.ceo_briefing import CEOBriefing
    from datetime import datetime

    # Create briefing instance
    briefing = CEOBriefing(
        period_start=datetime(2026, 3, 24),
        period_end=datetime(2026, 3, 30),
        revenue={"total": 5000, "by_source": {"Client A": 3000, "Client B": 2000}, "trend_percentage": 15.5},
        expenses={"total": 1500, "by_category": {"software": 500, "marketing": 1000}, "trend_percentage": -5.0},
        tasks_completed=12,
        bottlenecks=[{"task": "Client B proposal", "expected": "2 days", "actual": "5 days", "delay": "3 days"}],
        subscription_audit=[{"name": "Notion", "cost": 15, "last_used": "2026-02-15", "recommendation": "Cancel - unused for 45 days"}],
        cash_flow_projection={"30_day": 15000, "60_day": 28000, "90_day": 42000},
        proactive_suggestions=[{"suggestion": "Cancel unused subscription: Notion", "priority": "medium", "action_file": "APPROVAL_cancel_notion.md"}]
    )

    # Generate markdown output
    md_content = briefing.to_markdown()

    # Save to file
    briefing_path = briefing.save_to_file(output_dir=Path("/Vault/Briefings"))
"""

import os
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class RevenueData:
    """Revenue data for CEO briefing.

    Attributes:
        total: Total revenue for the period
        by_source: Revenue breakdown by source/client
        trend_percentage: Percentage change vs previous period
    """

    total: float
    by_source: Dict[str, float] = field(default_factory=dict)
    trend_percentage: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "total": self.total,
            "by_source": self.by_source,
            "trend_percentage": self.trend_percentage,
        }


@dataclass
class ExpensesData:
    """Expenses data for CEO briefing.

    Attributes:
        total: Total expenses for the period
        by_category: Expenses breakdown by category
        trend_percentage: Percentage change vs previous period
    """

    total: float
    by_category: Dict[str, float] = field(default_factory=dict)
    trend_percentage: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "total": self.total,
            "by_category": self.by_category,
            "trend_percentage": self.trend_percentage,
        }


@dataclass
class Bottleneck:
    """Bottleneck identified in task completion.

    Attributes:
        task: Task name or description
        expected: Expected completion time
        actual: Actual completion time
        delay: Delay duration (e.g., "3 days")
    """

    task: str
    expected: str
    actual: str
    delay: str

    def to_dict(self) -> Dict[str, str]:
        """Convert to dictionary."""
        return {
            "task": self.task,
            "expected": self.expected,
            "actual": self.actual,
            "delay": self.delay,
        }


@dataclass
class SubscriptionAudit:
    """Subscription audit entry.

    Attributes:
        name: Subscription name (e.g., "Netflix", "Notion")
        cost: Monthly cost in USD
        last_used: Last usage date (ISO-8601 or human-readable)
        recommendation: Action recommendation
    """

    name: str
    cost: float
    last_used: str
    recommendation: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "cost": self.cost,
            "last_used": self.last_used,
            "recommendation": self.recommendation,
        }


@dataclass
class CashFlowProjection:
    """Cash flow projection data.

    Attributes:
        day_30: Projected cash flow in 30 days
        day_60: Projected cash flow in 60 days
        day_90: Projected cash flow in 90 days
    """

    day_30: float
    day_60: float
    day_90: float

    def to_dict(self) -> Dict[str, float]:
        """Convert to dictionary."""
        return {
            "30_day": self.day_30,
            "60_day": self.day_60,
            "90_day": self.day_90,
        }


@dataclass
class ProactiveSuggestion:
    """Proactive suggestion for business improvement.

    Attributes:
        suggestion: Suggestion description
        priority: Priority level (low, medium, high)
        action_file: Associated action file name (if any)
    """

    suggestion: str
    priority: str = "medium"
    action_file: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "suggestion": self.suggestion,
            "priority": self.priority,
            "action_file": self.action_file or "N/A",
        }


@dataclass
class CEOBriefing:
    """CEO Briefing data model for weekly business intelligence.

    Generated every Monday at 8 AM with comprehensive business analytics.

    Attributes:
        generated: ISO-8601 timestamp when briefing was generated
        period_start: Start of reporting period (Monday 12:00 AM)
        period_end: End of reporting period (Sunday 11:59 PM)
        revenue: Revenue data (total, by_source, trend)
        expenses: Expenses data (total, by_category, trend)
        tasks_completed: Number of tasks completed in period
        bottlenecks: List of identified bottlenecks
        subscription_audit: List of subscription audit entries
        cash_flow_projection: 30/60/90 day cash flow projections
        proactive_suggestions: List of proactive suggestions
    """

    period_start: datetime
    period_end: datetime
    revenue: RevenueData
    expenses: ExpensesData
    tasks_completed: int = 0
    bottlenecks: List[Bottleneck] = field(default_factory=list)
    subscription_audit: List[SubscriptionAudit] = field(default_factory=list)
    cash_flow_projection: Optional[CashFlowProjection] = None
    proactive_suggestions: List[ProactiveSuggestion] = field(default_factory=list)
    generated: Optional[datetime] = None

    def __post_init__(self) -> None:
        """Set generated timestamp if not provided."""
        if self.generated is None:
            self.generated = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """Convert briefing to dictionary.

        Returns:
            Dictionary representation of briefing data
        """
        return {
            "generated": self.generated.isoformat() if self.generated else None,
            "period_start": self.period_start.isoformat()
            if self.period_start
            else None,
            "period_end": self.period_end.isoformat() if self.period_end else None,
            "revenue": self.revenue.to_dict() if self.revenue else {},
            "expenses": self.expenses.to_dict() if self.expenses else {},
            "tasks_completed": self.tasks_completed,
            "bottlenecks": [b.to_dict() for b in self.bottlenecks],
            "subscription_audit": [s.to_dict() for s in self.subscription_audit],
            "cash_flow_projection": self.cash_flow_projection.to_dict()
            if self.cash_flow_projection
            else {"30_day": 0, "60_day": 0, "90_day": 0},
            "proactive_suggestions": [s.to_dict() for s in self.proactive_suggestions],
        }

    def to_markdown(self) -> str:
        """Convert briefing to markdown format with YAML frontmatter.

        Returns:
            Markdown string with YAML frontmatter
        """
        import yaml

        # Build YAML frontmatter
        frontmatter = {
            "generated": self.generated.isoformat() if self.generated else None,
            "period_start": self.period_start.strftime("%Y-%m-%d")
            if self.period_start
            else None,
            "period_end": self.period_end.strftime("%Y-%m-%d")
            if self.period_end
            else None,
        }

        # Build markdown body
        lines = [
            "---",
            yaml.dump(frontmatter, default_flow_style=False, sort_keys=False).strip(),
            "---",
            "",
            "# Monday Morning CEO Briefing",
            "",
            "## Executive Summary",
            "",
        ]

        # Add executive summary
        revenue_trend = (
            f"+{self.revenue.trend_percentage}%"
            if self.revenue.trend_percentage >= 0
            else f"{self.revenue.trend_percentage}%"
        )
        expense_trend = (
            f"+{self.expenses.trend_percentage}%"
            if self.expenses.trend_percentage >= 0
            else f"{self.expenses.trend_percentage}%"
        )

        summary = f"Week of {self.period_start.strftime('%Y-%m-%d')} to {self.period_end.strftime('%Y-%m-%d')}. "
        summary += f"Revenue: ${self.revenue.total:,.2f} ({revenue_trend} trend). "
        summary += f"Expenses: ${self.expenses.total:,.2f} ({expense_trend} trend). "
        summary += f"Tasks completed: {self.tasks_completed}."

        lines.extend(
            [
                summary,
                "",
                "## Revenue",
                "",
                f"- **This Week**: ${self.revenue.total:,.2f}",
                f"- **Trend**: {revenue_trend} vs previous period",
                "",
                "### Revenue by Source",
                "",
            ]
        )

        # Add revenue by source
        if self.revenue.by_source:
            for source, amount in self.revenue.by_source.items():
                lines.append(f"- {source}: ${amount:,.2f}")
        else:
            lines.append("- No revenue recorded")

        lines.extend(
            [
                "",
                "## Expenses",
                "",
                f"- **This Week**: ${self.expenses.total:,.2f}",
                f"- **Trend**: {expense_trend} vs previous period",
                "",
                "### Expenses by Category",
                "",
            ]
        )

        # Add expenses by category
        if self.expenses.by_category:
            for category, amount in self.expenses.by_category.items():
                lines.append(f"- {category.capitalize()}: ${amount:,.2f}")
        else:
            lines.append("- No expenses recorded")

        # Add completed tasks
        lines.extend(
            [
                "",
                "## Completed Tasks",
                "",
                f"- **Total**: {self.tasks_completed} tasks",
                "",
            ]
        )

        # Add bottlenecks
        lines.extend(["## Bottlenecks", ""])
        if self.bottlenecks:
            lines.append(
                "| Task | Expected | Actual | Delay |",
                "|------|----------|--------|-------|",
            )
            for bottleneck in self.bottlenecks:
                lines.append(
                    f"| {bottleneck.task} | {bottleneck.expected} | {bottleneck.actual} | {bottleneck.delay} |"
                )
        else:
            lines.append("No bottlenecks identified.")

        # Add subscription audit
        lines.extend(["", "## Subscription Audit", ""])
        if self.subscription_audit:
            lines.append(
                "| Subscription | Cost | Last Used | Recommendation |",
                "|--------------|------|-----------|----------------|",
            )
            for sub in self.subscription_audit:
                lines.append(
                    f"| {sub.name} | ${sub.cost:.2f} | {sub.last_used} | {sub.recommendation} |"
                )
        else:
            lines.append("No subscriptions requiring audit.")

        # Add cash flow projection
        lines.extend(["", "## Cash Flow Projection", ""])
        if self.cash_flow_projection:
            lines.append(
                f"- **30 Days**: ${self.cash_flow_projection.day_30:,.2f}",
                f"- **60 Days**: ${self.cash_flow_projection.day_60:,.2f}",
                f"- **90 Days**: ${self.cash_flow_projection.day_90:,.2f}",
            )
        else:
            lines.append("No cash flow projection available.")

        # Add proactive suggestions
        lines.extend(["", "## Proactive Suggestions", ""])
        if self.proactive_suggestions:
            for i, suggestion in enumerate(self.proactive_suggestions, 1):
                priority_badge = f"[{suggestion.priority.upper()}]"
                lines.append(
                    f"### {i}. {priority_badge} {suggestion.suggestion}",
                )
                if suggestion.action_file:
                    lines.append(f"   - Action File: `{suggestion.action_file}`")
                lines.append("")
        else:
            lines.append("No proactive suggestions at this time.")

        # Add footer
        lines.extend(
            [
                "---",
                "",
                f"*Generated by AI Employee v0.1 on {self.generated.strftime('%Y-%m-%d %H:%M:%S')}*",
            ]
        )

        return "\n".join(lines)

    def save_to_file(
        self, output_dir: Optional[Path] = None, filename: Optional[str] = None
    ) -> Path:
        """Save briefing to markdown file.

        Args:
            output_dir: Output directory (default: /Vault/Briefings)
            filename: Custom filename (default: YYYY-MM-DD_Monday_Briefing.md)

        Returns:
            Path to saved file
        """
        if output_dir is None:
            output_dir = Path(__file__).parent.parent.parent / "vault" / "Briefings"

        output_dir = Path(output_dir).resolve()
        output_dir.mkdir(parents=True, exist_ok=True)

        if filename is None:
            # Default filename: YYYY-MM-DD_Monday_Briefing.md
            filename = f"{self.generated.strftime('%Y-%m-%d')}_Monday_Briefing.md"

        output_path = output_dir / filename

        # Write markdown content
        markdown_content = self.to_markdown()
        output_path.write_text(markdown_content, encoding="utf-8")

        return output_path
