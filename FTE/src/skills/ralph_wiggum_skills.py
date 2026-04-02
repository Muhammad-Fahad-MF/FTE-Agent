"""Ralph Wiggum Skills for autonomous multi-step task completion.

Usage:
    from src.skills.ralph_wiggum_skills import (
        save_task_state,
        load_task_state,
        check_completion,
        check_max_iterations,
        move_to_dlq,
    )

    # Save task state
    task = TaskState(objective="Research competitors")
    save_task_state(task, agent="research_agent")

    # Load task state
    task = load_task_state(task_id, agent="research_agent")

    # Check completion
    is_complete = check_completion(task)

    # Check max iterations
    if check_max_iterations(task):
        move_to_dlq(task, error="Max iterations reached")
"""

import os
import sys
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from .base_skill import BaseSkill

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from models.task_state import TaskState, TaskStatus


def save_task_state(
    task: TaskState,
    agent: str = "default",
    dry_run: bool = False,
    correlation_id: Optional[str] = None,
    vault_dir: Optional[Path] = None,
) -> Path:
    """Save task state to file.

    Args:
        task: TaskState instance to save
        agent: Agent name for directory structure
        dry_run: If True, log actions without executing
        correlation_id: Unique ID for tracking
        vault_dir: Base vault directory

    Returns:
        Path to saved file
    """
    skill = RalphWiggumSkill(dry_run=dry_run, correlation_id=correlation_id, vault_dir=vault_dir)
    return skill.save_task_state(task, agent)


def load_task_state(
    task_id: str,
    agent: str = "default",
    dry_run: bool = False,
    correlation_id: Optional[str] = None,
    vault_dir: Optional[Path] = None,
) -> Optional[TaskState]:
    """Load task state from file.

    Args:
        task_id: UUID of task to load
        agent: Agent name for directory structure
        dry_run: If True, log actions without executing
        correlation_id: Unique ID for tracking
        vault_dir: Base vault directory

    Returns:
        TaskState instance or None if not found
    """
    skill = RalphWiggumSkill(dry_run=dry_run, correlation_id=correlation_id, vault_dir=vault_dir)
    return skill.load_task_state(task_id, agent)


def check_completion(
    task: TaskState,
    dry_run: bool = False,
    correlation_id: Optional[str] = None,
    vault_dir: Optional[Path] = None,
) -> bool:
    """Check if task is complete using multiple detection methods.

    Args:
        task: TaskState instance
        dry_run: If True, log actions without executing
        correlation_id: Unique ID for tracking
        vault_dir: Base vault directory

    Returns:
        True if task is complete
    """
    skill = RalphWiggumSkill(dry_run=dry_run, correlation_id=correlation_id, vault_dir=vault_dir)
    return skill.check_completion(task)


def check_max_iterations(
    task: TaskState,
    dry_run: bool = False,
    correlation_id: Optional[str] = None,
    vault_dir: Optional[Path] = None,
) -> bool:
    """Check if task has reached max iterations.

    Args:
        task: TaskState instance
        dry_run: If True, log actions without executing
        correlation_id: Unique ID for tracking
        vault_dir: Base vault directory

    Returns:
        True if max iterations reached
    """
    skill = RalphWiggumSkill(dry_run=dry_run, correlation_id=correlation_id, vault_dir=vault_dir)
    return skill.check_max_iterations(task)


def move_to_dlq(
    task: TaskState,
    error: str,
    dry_run: bool = False,
    correlation_id: Optional[str] = None,
    vault_dir: Optional[Path] = None,
) -> None:
    """Move task to Dead Letter Queue.

    Args:
        task: TaskState instance
        error: Error message describing why moved to DLQ
        dry_run: If True, log actions without executing
        correlation_id: Unique ID for tracking
        vault_dir: Base vault directory
    """
    skill = RalphWiggumSkill(dry_run=dry_run, correlation_id=correlation_id, vault_dir=vault_dir)
    skill.move_to_dlq(task, error)


def alert_user(
    message: str,
    alert_type: str = "info",
    dry_run: bool = False,
    correlation_id: Optional[str] = None,
    vault_dir: Optional[Path] = None,
) -> None:
    """Alert user via Dashboard.md update.

    Args:
        message: Alert message
        alert_type: Type of alert (info, warning, error, critical)
        dry_run: If True, log actions without executing
        correlation_id: Unique ID for tracking
        vault_dir: Base vault directory
    """
    skill = RalphWiggumSkill(dry_run=dry_run, correlation_id=correlation_id, vault_dir=vault_dir)
    skill.alert_user(message, alert_type)


class RalphWiggumSkill(BaseSkill):
    """Skill for Ralph Wiggum autonomous task completion.

    Implements:
    - State persistence between iterations
    - Completion detection (file movement, promise tags, checklist)
    - Max iterations check
    - DLQ movement

    Attributes:
        vault_dir: Base directory for vault storage
        in_progress_dir: Directory for in-progress task states
        done_dir: Directory for completed tasks
        dlq_dir: Directory for dead letter queue
        dashboard_path: Path to Dashboard.md
    """

    def __init__(
        self,
        dry_run: bool = False,
        correlation_id: Optional[str] = None,
        vault_dir: Optional[Path] = None,
    ) -> None:
        """Initialize Ralph Wiggum skill.

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

        self.in_progress_dir = self.vault_dir / "In_Progress"
        self.done_dir = self.vault_dir / "Done"
        self.dlq_dir = self.vault_dir / "Dead_Letter_Queue"
        self.dashboard_path = self.vault_dir / "Dashboard.md"

        # Ensure directories exist
        self.in_progress_dir.mkdir(parents=True, exist_ok=True)
        self.done_dir.mkdir(parents=True, exist_ok=True)
        self.dlq_dir.mkdir(parents=True, exist_ok=True)

    def save_task_state(
        self,
        task: TaskState,
        agent: str = "default",
    ) -> Path:
        """Save task state to file.

        Args:
            task: TaskState instance to save
            agent: Agent name for directory structure

        Returns:
            Path to saved file
        """
        start_time = time.time()

        try:
            # Create agent directory
            agent_dir = self.in_progress_dir / agent
            agent_dir.mkdir(parents=True, exist_ok=True)

            # Save task state
            task_path = task.save_to_file(agent=agent, vault_dir=self.vault_dir)

            elapsed = time.time() - start_time
            self.logger.log(
                "INFO",
                "save_task_state",
                {
                    "task_id": task.task_id,
                    "agent": agent,
                    "iteration": task.iteration,
                    "status": task.status.value,
                    "elapsed_seconds": elapsed,
                    "path": str(task_path),
                },
                correlation_id=self.correlation_id,
            )

            return task_path

        except Exception as e:
            self.logger.log(
                "ERROR",
                "save_task_state_failed",
                {"task_id": task.task_id, "error": str(e)},
                correlation_id=self.correlation_id,
            )
            raise

    def load_task_state(
        self,
        task_id: str,
        agent: str = "default",
    ) -> Optional[TaskState]:
        """Load task state from file.

        Args:
            task_id: UUID of task to load
            agent: Agent name for directory structure

        Returns:
            TaskState instance or None if not found
        """
        try:
            task = TaskState.load_from_file(
                task_id=task_id,
                agent=agent,
                vault_dir=self.vault_dir,
            )

            if task:
                self.logger.log(
                    "INFO",
                    "load_task_state",
                    {
                        "task_id": task_id,
                        "agent": agent,
                        "iteration": task.iteration,
                        "status": task.status.value,
                    },
                    correlation_id=self.correlation_id,
                )
            else:
                self.logger.log(
                    "WARNING",
                    "task_state_not_found",
                    {"task_id": task_id, "agent": agent},
                    correlation_id=self.correlation_id,
                )

            return task

        except Exception as e:
            self.logger.log(
                "ERROR",
                "load_task_state_failed",
                {"task_id": task_id, "error": str(e)},
                correlation_id=self.correlation_id,
            )
            return None

    def check_completion(self, task: TaskState) -> bool:
        """Check if task is complete using multiple detection methods.

        Detection methods (in priority order):
        1. File movement to /Done/ folder (primary)
        2. Promise tag <promise>TASK_COMPLETE</promise> (fallback)
        3. Plan checklist 100% completion (alternative)
        4. TaskState completion_criteria all met (internal)

        Args:
            task: TaskState instance

        Returns:
            True if task is complete
        """
        try:
            # Method 1: Check TaskState completion criteria
            if task.is_complete():
                self.logger.log(
                    "INFO",
                    "completion_detected_criteria",
                    {"task_id": task.task_id},
                    correlation_id=self.correlation_id,
                )
                return True

            # Method 2: Check /Done/ folder for task file
            if self._check_done_folder(task.task_id):
                self.logger.log(
                    "INFO",
                    "completion_detected_done_folder",
                    {"task_id": task.task_id},
                    correlation_id=self.correlation_id,
                )
                return True

            # Method 3: Check for promise tag in task files
            if self._check_promise_tag(task):
                self.logger.log(
                    "INFO",
                    "completion_detected_promise_tag",
                    {"task_id": task.task_id},
                    correlation_id=self.correlation_id,
                )
                return True

            # Method 4: Check plan checklist completion
            if self._check_plan_checklist(task):
                self.logger.log(
                    "INFO",
                    "completion_detected_plan_checklist",
                    {"task_id": task.task_id},
                    correlation_id=self.correlation_id,
                )
                return True

            self.logger.log(
                "INFO",
                "completion_not_detected",
                {"task_id": task.task_id},
                correlation_id=self.correlation_id,
            )
            return False

        except Exception as e:
            self.logger.log(
                "ERROR",
                "check_completion_failed",
                {"task_id": task.task_id, "error": str(e)},
                correlation_id=self.correlation_id,
            )
            return False

    def _check_done_folder(self, task_id: str) -> bool:
        """Check if task file exists in /Done/ folder.

        Args:
            task_id: UUID of task to check

        Returns:
            True if file found in /Done/
        """
        try:
            # Look for task file in Done folder
            done_file = self.done_dir / f"{task_id}.md"
            if done_file.exists():
                return True

            # Also check for any file containing the task_id
            for file_path in self.done_dir.glob("*.md"):
                try:
                    content = file_path.read_text(encoding="utf-8")
                    if task_id in content:
                        return True
                except Exception:
                    continue

            return False

        except Exception:
            return False

    def _check_promise_tag(self, task: TaskState) -> bool:
        """Check for promise tag in task files.

        Args:
            task: TaskState instance

        Returns:
            True if <promise>TASK_COMPLETE</promise> found
        """
        try:
            # Check task state file for promise tag
            agent_dir = self.in_progress_dir / "default"
            task_file = agent_dir / f"{task.task_id}.md"

            if task_file.exists():
                content = task_file.read_text(encoding="utf-8")
                if "<promise>TASK_COMPLETE</promise>" in content:
                    return True

            return False

        except Exception:
            return False

    def _check_plan_checklist(self, task: TaskState) -> bool:
        """Check if plan checklist is 100% complete.

        Args:
            task: TaskState instance

        Returns:
            True if all checklist items complete
        """
        try:
            # Look for plan files related to task
            plans_dir = self.vault_dir / "Plans"
            if not plans_dir.exists():
                return False

            for plan_file in plans_dir.glob("*.md"):
                try:
                    content = plan_file.read_text(encoding="utf-8")

                    # Count checklist items
                    total_items = content.count("- [ ]") + content.count("- [x]") + content.count("- [X]")
                    completed_items = content.count("- [x]") + content.count("- [X]")

                    if total_items > 0 and completed_items == total_items:
                        # All items complete - check if this plan relates to the task
                        if task.task_id in content or task.objective in content:
                            return True

                except Exception:
                    continue

            return False

        except Exception:
            return False

    def check_max_iterations(self, task: TaskState) -> bool:
        """Check if task has reached max iterations.

        Args:
            task: TaskState instance

        Returns:
            True if iteration >= max_iterations
        """
        try:
            max_reached = task.is_max_iterations_reached()

            if max_reached:
                self.logger.log(
                    "WARNING",
                    "max_iterations_reached",
                    {
                        "task_id": task.task_id,
                        "iteration": task.iteration,
                        "max_iterations": task.max_iterations,
                    },
                    correlation_id=self.correlation_id,
                )
            else:
                self.logger.log(
                    "INFO",
                    "max_iterations_check",
                    {
                        "task_id": task.task_id,
                        "iteration": task.iteration,
                        "max_iterations": task.max_iterations,
                        "remaining": task.max_iterations - task.iteration,
                    },
                    correlation_id=self.correlation_id,
                )

            return max_reached

        except Exception as e:
            self.logger.log(
                "ERROR",
                "check_max_iterations_failed",
                {"task_id": task.task_id, "error": str(e)},
                correlation_id=self.correlation_id,
            )
            return False

    def move_to_dlq(
        self,
        task: TaskState,
        error: str,
    ) -> None:
        """Move task to Dead Letter Queue.

        Args:
            task: TaskState instance
            error: Error message describing why moved to DLQ
        """
        try:
            # Mark task as DLQ
            task.mark_dlq(error)

            # Create DLQ file
            dlq_filename = f"DLQ_{task.task_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
            dlq_path = self.dlq_dir / dlq_filename

            # Build DLQ content
            dlq_content = f"""---
task_id: {task.task_id}
objective: {task.objective}
created: {task.created.isoformat() if task.created else None}
moved_to_dlq: {datetime.now().isoformat()}
iteration: {task.iteration}
max_iterations: {task.max_iterations}
error: {error}
status: dlq
---

# Dead Letter Queue Item

## Task Details
- **Task ID**: {task.task_id}
- **Objective**: {task.objective}
- **Created**: {task.created.strftime('%Y-%m-%d %H:%M:%S') if task.created else 'Unknown'}
- **Moved to DLQ**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- **Iteration**: {task.iteration} / {task.max_iterations}

## Error
```
{error}
```

## State Data
```yaml
{task.state_data}
```

## Completion Status
- **Completion Criteria**: {len(task.completion_criteria)}
- **Completed Criteria**: {len(task.completed_criteria)}
- **Progress**: {len(task.completed_criteria)}/{len(task.completion_criteria)} criteria met

---

*This task requires manual review. Resolve by moving to /Done/ or /Rejected/.*
"""

            dlq_path.write_text(dlq_content, encoding="utf-8")

            # Remove from In_Progress
            agent_dir = self.in_progress_dir / "default"
            task_file = agent_dir / f"{task.task_id}.md"
            if task_file.exists():
                task_file.unlink()

            self.logger.log(
                "WARNING",
                "task_moved_to_dlq",
                {
                    "task_id": task.task_id,
                    "error": error,
                    "dlq_path": str(dlq_path),
                },
                correlation_id=self.correlation_id,
            )

            # Alert user
            self.alert_user(
                f"Task moved to DLQ: {task.objective[:50]}... (Iteration {task.iteration}/{task.max_iterations})",
                alert_type="warning",
            )

        except Exception as e:
            self.logger.log(
                "ERROR",
                "move_to_dlq_failed",
                {"task_id": task.task_id, "error": str(e)},
                correlation_id=self.correlation_id,
            )
            raise

    def alert_user(
        self,
        message: str,
        alert_type: str = "info",
    ) -> None:
        """Alert user via Dashboard.md update.

        Args:
            message: Alert message
            alert_type: Type of alert (info, warning, error, critical)
        """
        try:
            # Create alert file in Needs_Action
            needs_action_dir = self.vault_dir / "Needs_Action"
            needs_action_dir.mkdir(parents=True, exist_ok=True)

            alert_filename = f"ALERT_{alert_type.upper()}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
            alert_path = needs_action_dir / alert_filename

            alert_content = f"""---
type: alert
alert_type: {alert_type}
created: {datetime.now().isoformat()}
priority: {alert_type}
status: pending
---

# {alert_type.upper()} Alert

{message}

---

*Generated by Ralph Wiggum Skill at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""

            alert_path.write_text(alert_content, encoding="utf-8")

            # Update Dashboard.md
            self._update_dashboard_alert(message, alert_type)

            self.logger.log(
                "INFO",
                "alert_user",
                {
                    "alert_type": alert_type,
                    "message": message[:100],
                    "alert_path": str(alert_path),
                },
                correlation_id=self.correlation_id,
            )

        except Exception as e:
            self.logger.log(
                "ERROR",
                "alert_user_failed",
                {"error": str(e)},
                correlation_id=self.correlation_id,
            )

    def _update_dashboard_alert(
        self,
        message: str,
        alert_type: str,
    ) -> None:
        """Update Dashboard.md with alert.

        Args:
            message: Alert message
            alert_type: Type of alert
        """
        try:
            if not self.dashboard_path.exists():
                # Create basic dashboard
                dashboard_content = """# FTE-Agent Dashboard

## System Status
- **Status**: Running
- **Last Updated**: {timestamp}

## Recent Alerts
{alerts}

## Health Indicators
- **Watchers**: Running
- **MCP Servers**: Connected
- **Storage**: OK
- **Circuit Breakers**: Closed

---

*Last updated: {timestamp}*
"""
                self.dashboard_path.write_text(
                    dashboard_content.format(
                        timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        alerts=f"- [{alert_type.upper()}] {message}",
                    ),
                    encoding="utf-8",
                )
            else:
                # Append to existing dashboard
                content = self.dashboard_path.read_text(encoding="utf-8")
                if "## Recent Alerts" in content:
                    # Insert alert after Recent Alerts header
                    parts = content.split("## Recent Alerts", 1)
                    new_alert = f"\n- [{alert_type.upper()}] {message}"
                    content = parts[0] + "## Recent Alerts" + new_alert + parts[1]
                else:
                    # Add Recent Alerts section
                    content += f"\n\n## Recent Alerts\n- [{alert_type.upper()}] {message}\n"

                self.dashboard_path.write_text(content, encoding="utf-8")

        except Exception as e:
            self.logger.log(
                "ERROR",
                "update_dashboard_failed",
                {"error": str(e)},
                correlation_id=self.correlation_id,
            )
