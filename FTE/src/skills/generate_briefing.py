"""Generate Briefing Skill for creating daily and weekly summaries.

Usage:
    from src.skills.generate_briefing import GenerateBriefingSkill

    skill = GenerateBriefingSkill()
    
    # Generate daily briefing
    briefing_path = skill.generate_daily_briefing(date=datetime.now())
    
    # Generate weekly audit
    audit_path = skill.generate_weekly_audit(date=datetime.now())
"""

import os
import sys
import time
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Optional

import yaml

from .base_skill import BaseSkill


class BriefingGenerationError(Exception):
    """Raised when briefing generation fails."""

    pass


class GenerateBriefingSkill(BaseSkill):
    """Skill for generating daily briefings and weekly audits.

    Generates summaries from vault data:
    - Daily briefing: Summary of Needs_Action/, Plans/, Done/ folders
    - Weekly audit: Metrics, watcher uptime, approval stats, recommendations

    Attributes:
        vault_dir: Base directory for vault storage
        briefings_dir: Directory for generated briefings
    """

    def __init__(
        self,
        dry_run: bool = False,
        correlation_id: Optional[str] = None,
        vault_dir: Optional[Path] = None,
    ) -> None:
        """Initialize generate briefing skill.

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
        self.needs_action_dir = self.vault_dir / "Needs_Action"
        self.plans_dir = self.vault_dir / "Plans"
        self.done_dir = self.vault_dir / "Done"
        self.pending_approval_dir = self.vault_dir / "Pending_Approval"
        self.approved_dir = self.vault_dir / "Approved"
        self.rejected_dir = self.vault_dir / "Rejected"
        self.dashboard_path = self.vault_dir / "Dashboard.md"

        # Ensure directories exist
        self.briefings_dir.mkdir(parents=True, exist_ok=True)

    def _count_files_in_folder(self, folder: Path, pattern: str = "*.md") -> int:
        """Count files in a folder matching pattern.

        Args:
            folder: Directory to scan
            pattern: Glob pattern for files

        Returns:
            Count of matching files
        """
        try:
            if not folder.exists():
                return 0
            return len(list(folder.glob(pattern)))
        except Exception as e:
            self.logger.log(
                "WARNING",
                "folder_count_failed",
                {"folder": str(folder), "error": str(e)},
                correlation_id=self.correlation_id,
            )
            return 0

    def _get_files_by_age(
        self, folder: Path, hours: int = 24, pattern: str = "*.md"
    ) -> list[Path]:
        """Get files modified within specified hours.

        Args:
            folder: Directory to scan
            hours: Hours threshold
            pattern: Glob pattern for files

        Returns:
            List of files modified within threshold
        """
        try:
            if not folder.exists():
                return []

            cutoff = datetime.now() - timedelta(hours=hours)
            files = []

            for f in folder.glob(pattern):
                try:
                    mtime = datetime.fromtimestamp(f.stat().st_mtime)
                    if mtime >= cutoff:
                        files.append(f)
                except Exception:
                    continue

            return files

        except Exception as e:
            self.logger.log(
                "WARNING",
                "get_files_by_age_failed",
                {"folder": str(folder), "error": str(e)},
                correlation_id=self.correlation_id,
            )
            return []

    def _generate_daily_briefing_content(
        self, date: datetime
    ) -> tuple[str, dict[str, Any]]:
        """Generate daily briefing content.

        Args:
            date: Date for briefing

        Returns:
            Tuple of (content, metrics_dict)
        """
        date_str = date.strftime("%Y-%m-%d")

        # Collect metrics
        metrics = {
            "date": date_str,
            "needs_action_count": self._count_files_in_folder(self.needs_action_dir),
            "plans_count": self._count_files_in_folder(self.plans_dir),
            "done_count": self._count_files_in_folder(self.done_dir),
            "pending_approval_count": self._count_files_in_folder(self.pending_approval_dir),
            "new_items_today": len(
                self._get_files_by_age(self.needs_action_dir, hours=24)
            ),
            "completed_today": len(self._get_files_by_age(self.done_dir, hours=24)),
        }

        # Generate content
        content = f"""---
type: daily_briefing
date: {date_str}
generated: {datetime.now().isoformat()}
---

# Daily Briefing - {date_str}

**Generated:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

---

## Summary

| Metric | Count |
|--------|-------|
| Needs Action | {metrics['needs_action_count']} |
| In Progress (Plans) | {metrics['plans_count']} |
| Completed (Done) | {metrics['done_count']} |
| Pending Approval | {metrics['pending_approval_count']} |

## Today's Activity

- **New Items:** {metrics['new_items_today']}
- **Completed:** {metrics['completed_today']}

---

## Needs Action

"""

        # List items in Needs_Action
        needs_action_files = list(self.needs_action_dir.glob("*.md"))[:10]
        if needs_action_files:
            for f in needs_action_files:
                content += f"- `{f.name}`\n"
        else:
            content += "*No items*\n"

        content += """
---

## Recent Plans

"""

        # List recent plans
        plan_files = list(self.plans_dir.glob("*.md"))[:5]
        if plan_files:
            for f in plan_files:
                content += f"- `{f.name}`\n"
        else:
            content += "*No plans*\n"

        content += """
---

## Notes

[Add any additional notes or observations here]

"""

        return content, metrics

    def _generate_weekly_audit_content(
        self, date: datetime
    ) -> tuple[str, dict[str, Any]]:
        """Generate weekly audit content.

        Args:
            date: Date for audit (typically Sunday)

        Returns:
            Tuple of (content, metrics_dict)
        """
        # Calculate week start (Monday)
        week_start = date - timedelta(days=date.weekday())
        week_end = week_start + timedelta(days=6)

        week_start_str = week_start.strftime("%Y-%m-%d")
        week_end_str = week_end.strftime("%Y-%m-%d")

        # Collect metrics
        metrics = {
            "week_start": week_start_str,
            "week_end": week_end_str,
            "total_needs_action": self._count_files_in_folder(self.needs_action_dir),
            "total_plans": self._count_files_in_folder(self.plans_dir),
            "total_done": self._count_files_in_folder(self.done_dir),
            "weekly_new_items": len(
                self._get_files_by_age(self.needs_action_dir, hours=24 * 7)
            ),
            "weekly_completed": len(self._get_files_by_age(self.done_dir, hours=24 * 7)),
            "pending_approvals": self._count_files_in_folder(self.pending_approval_dir),
            "approved_this_week": len(self._get_files_by_age(self.approved_dir, hours=24 * 7)),
            "rejected_this_week": len(self._get_files_by_age(self.rejected_dir, hours=24 * 7)),
        }

        # Calculate completion rate
        if metrics["weekly_new_items"] > 0:
            completion_rate = (
                metrics["weekly_completed"] / metrics["weekly_new_items"] * 100
            )
        else:
            completion_rate = 0

        metrics["completion_rate"] = round(completion_rate, 1)

        # Generate content
        content = f"""---
type: weekly_audit
week_start: {week_start_str}
week_end: {week_end_str}
generated: {datetime.now().isoformat()}
---

# Weekly Audit - {week_start_str} to {week_end_str}

**Generated:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

---

## Key Metrics

| Metric | Value |
|--------|-------|
| Total Needs Action | {metrics['total_needs_action']} |
| Total Plans | {metrics['total_plans']} |
| Total Done | {metrics['total_done']} |
| New Items This Week | {metrics['weekly_new_items']} |
| Completed This Week | {metrics['weekly_completed']} |
| **Completion Rate** | **{metrics['completion_rate']}%** |

---

## Approval Workflow

| Status | Count |
|--------|-------|
| Pending Approval | {metrics['pending_approvals']} |
| Approved This Week | {metrics['approved_this_week']} |
| Rejected This Week | {metrics['rejected_this_week']} |

---

## Watcher Uptime

*Watcher uptime metrics would be collected from the metrics database*

- Gmail Watcher: [Status]
- WhatsApp Watcher: [Status]
- FileSystem Watcher: [Status]

---

## Bottlenecks

*Identify areas where items are getting stuck:*

"""

        # Analyze bottlenecks
        if metrics["pending_approvals"] > 5:
            content += "- ⚠️ High pending approvals - consider reviewing approval process\n"

        if metrics["total_needs_action"] > 20:
            content += "- ⚠️ Large backlog in Needs_Action - prioritize processing\n"

        if metrics["completion_rate"] < 50:
            content += "- ⚠️ Low completion rate - review workflow efficiency\n"

        if not any(
            [
                metrics["pending_approvals"] > 5,
                metrics["total_needs_action"] > 20,
                metrics["completion_rate"] < 50,
            ]
        ):
            content += "*No significant bottlenecks identified*\n"

        content += """
---

## Recommendations

"""

        # Generate recommendations
        recommendations = []

        if metrics["pending_approvals"] > 0:
            recommendations.append(
                f"1. **Process {metrics['pending_approvals']} pending approval(s)** - Review and approve/reject items in Pending_Approval/"
            )

        if metrics["weekly_completed"] > 0:
            recommendations.append(
                f"2. **Celebrate {metrics['weekly_completed']} completions** - Great progress this week!"
            )

        if metrics["completion_rate"] < 80 and metrics["weekly_new_items"] > 0:
            recommendations.append(
                "3. **Improve completion rate** - Focus on reducing backlog and increasing throughput"
            )

        if not recommendations:
            recommendations.append("*No specific recommendations - system running smoothly*")

        for rec in recommendations:
            content += f"{rec}\n"

        content += """
---

## Notes

[Add any additional observations or action items here]

"""

        return content, metrics

    def generate_daily_briefing(
        self, date: Optional[datetime] = None
    ) -> Path:
        """Generate daily briefing.

        Args:
            date: Date for briefing (default: today)

        Returns:
            Path to generated briefing file

        Raises:
            BriefingGenerationError: If generation fails
        """
        start_time = time.time()

        if date is None:
            date = datetime.now()

        date_str = date.strftime("%Y-%m-%d")
        filename = f"Daily_{date_str}.md"
        briefing_path = self.briefings_dir / filename

        try:
            # Generate content
            content, metrics = self._generate_daily_briefing_content(date)

            if self.dry_run:
                self.logger.log(
                    "INFO",
                    "dry_run_daily_briefing",
                    {"filename": filename, "metrics": metrics},
                    correlation_id=self.correlation_id,
                )
                self.emit_metric(
                    "briefing_generation_duration", time.time() - start_time
                )
                self.emit_metric(
                    "briefing_generated_count", 1.0, {"type": "daily", "dry_run": "true"}
                )
                return briefing_path

            # Write file
            briefing_path.write_text(content, encoding="utf-8")

            self.logger.log(
                "INFO",
                "daily_briefing_generated",
                {
                    "file": str(briefing_path),
                    "date": date_str,
                    "metrics": metrics,
                },
                correlation_id=self.correlation_id,
            )

            # Emit metrics
            duration = time.time() - start_time
            self.emit_metric("briefing_generation_duration", duration)
            self.emit_metric(
                "briefing_generated_count", 1.0, {"type": "daily", "dry_run": "false"}
            )

            return briefing_path

        except Exception as e:
            self.logger.log(
                "ERROR",
                "daily_briefing_generation_failed",
                {"error": str(e)},
                correlation_id=self.correlation_id,
            )
            self.emit_metric("briefing_generation_errors", 1.0)
            raise BriefingGenerationError(f"Failed to generate daily briefing: {e}") from e

    def generate_weekly_audit(
        self, date: Optional[datetime] = None
    ) -> Path:
        """Generate weekly audit.

        Args:
            date: Date for audit (default: today, should be Sunday)

        Returns:
            Path to generated audit file

        Raises:
            BriefingGenerationError: If generation fails
        """
        start_time = time.time()

        if date is None:
            date = datetime.now()

        week_start = date - timedelta(days=date.weekday())
        week_start_str = week_start.strftime("%Y-%m-%d")
        filename = f"Weekly_Audit_{week_start_str}.md"
        audit_path = self.briefings_dir / filename

        try:
            # Generate content
            content, metrics = self._generate_weekly_audit_content(date)

            if self.dry_run:
                self.logger.log(
                    "INFO",
                    "dry_run_weekly_audit",
                    {"filename": filename, "metrics": metrics},
                    correlation_id=self.correlation_id,
                )
                self.emit_metric(
                    "briefing_generation_duration", time.time() - start_time
                )
                self.emit_metric(
                    "briefing_generated_count", 1.0, {"type": "weekly", "dry_run": "true"}
                )
                return audit_path

            # Write file
            audit_path.write_text(content, encoding="utf-8")

            self.logger.log(
                "INFO",
                "weekly_audit_generated",
                {
                    "file": str(audit_path),
                    "week_start": week_start_str,
                    "metrics": metrics,
                },
                correlation_id=self.correlation_id,
            )

            # Emit metrics
            duration = time.time() - start_time
            self.emit_metric("briefing_generation_duration", duration)
            self.emit_metric(
                "briefing_generated_count", 1.0, {"type": "weekly", "dry_run": "false"}
            )

            return audit_path

        except Exception as e:
            self.logger.log(
                "ERROR",
                "weekly_audit_generation_failed",
                {"error": str(e)},
                correlation_id=self.correlation_id,
            )
            self.emit_metric("briefing_generation_errors", 1.0)
            raise BriefingGenerationError(f"Failed to generate weekly audit: {e}") from e

    def execute(
        self, briefing_type: str = "daily", date: Optional[datetime] = None
    ) -> Path:
        """Execute the briefing generation skill.

        Args:
            briefing_type: 'daily' or 'weekly'
            date: Date for briefing/audit

        Returns:
            Path to generated file

        Raises:
            ValueError: If briefing_type is invalid
        """
        if briefing_type == "daily":
            return self.generate_daily_briefing(date)
        elif briefing_type == "weekly":
            return self.generate_weekly_audit(date)
        else:
            raise ValueError(
                f"Invalid briefing_type: {briefing_type}. Must be 'daily' or 'weekly'"
            )
