"""TaskState data model for Ralph Wiggum autonomous task completion.

Usage:
    from src.models.task_state import TaskState, TaskStatus
    from datetime import datetime

    # Create task state
    task = TaskState(
        objective="Research competitors and summarize findings",
        max_iterations=10,
    )

    # Update iteration
    task.update_iteration(
        iteration=1,
        state_data={"step": "research", "findings": ["Company A", "Company B"]},
        completed_criteria=["Identified 2 competitors"],
    )

    # Save to file
    task.save_to_file(agent="research_agent", vault_dir=Path("/Vault"))

    # Load from file
    loaded_task = TaskState.load_from_file(task_id=task.task_id, vault_dir=Path("/Vault"))
"""

import os
import sys
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml


class TaskStatus(str, Enum):
    """Task status values.

    Values:
        IN_PROGRESS: Task is currently being worked on
        COMPLETED: Task completed successfully
        FAILED: Task failed due to error
        DLQ: Task moved to Dead Letter Queue after max iterations
    """

    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    DLQ = "dlq"


@dataclass
class TaskState:
    """TaskState data model for Ralph Wiggum autonomous task completion.

    Tracks state of multi-step autonomous tasks across iterations.

    Attributes:
        task_id: Unique UUID for the task
        objective: Task description/objective
        created: ISO-8601 timestamp when task was created
        iteration: Current iteration number (1-10)
        max_iterations: Maximum allowed iterations (default: 10)
        status: Task status (in_progress, completed, failed, dlq)
        state_data: Iteration-specific state data (flexible dict)
        completion_criteria: List of criteria that must be met for completion
        completed_criteria: List of criteria that have been met
        error: Error message if task failed
        completed_at: ISO-8601 timestamp when task completed
    """

    objective: str
    task_id: Optional[str] = None
    created: Optional[datetime] = None
    iteration: int = 0
    max_iterations: int = 10
    status: TaskStatus = TaskStatus.IN_PROGRESS
    state_data: Dict[str, Any] = field(default_factory=dict)
    completion_criteria: List[str] = field(default_factory=list)
    completed_criteria: List[str] = field(default_factory=list)
    error: Optional[str] = None
    completed_at: Optional[datetime] = None

    def __post_init__(self) -> None:
        """Set default values for optional fields."""
        if self.task_id is None:
            self.task_id = str(uuid.uuid4())
        if self.created is None:
            self.created = datetime.now()
        if self.iteration == 0 and self.status == TaskStatus.IN_PROGRESS:
            self.iteration = 1

    def to_dict(self) -> Dict[str, Any]:
        """Convert task state to dictionary.

        Returns:
            Dictionary representation of task state
        """
        return {
            "task_id": self.task_id,
            "objective": self.objective,
            "created": self.created.isoformat() if self.created else None,
            "iteration": self.iteration,
            "max_iterations": self.max_iterations,
            "status": self.status.value if isinstance(self.status, TaskStatus) else self.status,
            "state_data": self.state_data,
            "completion_criteria": self.completion_criteria,
            "completed_criteria": self.completed_criteria,
            "error": self.error,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }

    def to_markdown(self) -> str:
        """Convert task state to markdown format with YAML frontmatter.

        Returns:
            Markdown string with YAML frontmatter
        """
        # Build YAML frontmatter
        frontmatter = {
            "task_id": self.task_id,
            "objective": self.objective,
            "created": self.created.isoformat() if self.created else None,
            "iteration": self.iteration,
            "max_iterations": self.max_iterations,
            "status": self.status.value if isinstance(self.status, TaskStatus) else self.status,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }

        # Build markdown body
        lines = [
            "---",
            yaml.dump(frontmatter, default_flow_style=False, sort_keys=False).strip(),
            "---",
            "",
            "# Ralph Wiggum Task State",
            "",
            "## Objective",
            "",
            self.objective,
            "",
            "## Progress",
            "",
            f"**Iteration**: {self.iteration} / {self.max_iterations}",
            "",
            f"**Status**: {self.status.value}",
            "",
        ]

        # Add completion criteria
        if self.completion_criteria:
            lines.extend([
                "## Completion Criteria",
                "",
            ])
            for criterion in self.completion_criteria:
                is_met = criterion in self.completed_criteria
                checkbox = "[x]" if is_met else "[ ]"
                lines.append(f"- {checkbox} {criterion}")
            lines.append("")

        # Add state data
        if self.state_data:
            lines.extend([
                "## Current State",
                "",
                "```yaml",
                yaml.dump(self.state_data, default_flow_style=False).strip(),
                "```",
                "",
            ])

        # Add error if present
        if self.error:
            lines.extend([
                "## Error",
                "",
                f"```\n{self.error}\n```",
                "",
            ])

        # Add footer
        lines.append(f"*Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")

        return "\n".join(lines)

    def update_iteration(
        self,
        iteration: Optional[int] = None,
        state_data: Optional[Dict[str, Any]] = None,
        completed_criteria: Optional[List[str]] = None,
        error: Optional[str] = None,
    ) -> None:
        """Update task state for current iteration.

        Args:
            iteration: New iteration number (default: current + 1)
            state_data: State data to merge/add
            completed_criteria: New criteria that have been met
            error: Error message if iteration failed
        """
        if iteration is not None:
            self.iteration = iteration
        elif self.status == TaskStatus.IN_PROGRESS:
            self.iteration += 1

        if state_data:
            self.state_data.update(state_data)

        if completed_criteria:
            for criterion in completed_criteria:
                if criterion not in self.completed_criteria:
                    self.completed_criteria.append(criterion)

        if error:
            self.error = error
            self.status = TaskStatus.FAILED

    def mark_completed(self) -> None:
        """Mark task as completed."""
        self.status = TaskStatus.COMPLETED
        self.completed_at = datetime.now()

    def mark_failed(self, error: str) -> None:
        """Mark task as failed.

        Args:
            error: Error message describing failure
        """
        self.status = TaskStatus.FAILED
        self.error = error
        self.completed_at = datetime.now()

    def mark_dlq(self, error: str) -> None:
        """Mark task for Dead Letter Queue.

        Args:
            error: Error message describing why moved to DLQ
        """
        self.status = TaskStatus.DLQ
        self.error = error
        self.completed_at = datetime.now()

    def is_complete(self) -> bool:
        """Check if task is complete.

        Returns:
            True if all completion criteria are met
        """
        if not self.completion_criteria:
            return False

        return all(
            criterion in self.completed_criteria
            for criterion in self.completion_criteria
        )

    def is_max_iterations_reached(self) -> bool:
        """Check if max iterations reached.

        Returns:
            True if iteration >= max_iterations
        """
        return self.iteration >= self.max_iterations

    def can_continue(self) -> bool:
        """Check if task can continue to next iteration.

        Returns:
            True if not complete, not failed, and under max iterations
        """
        return (
            self.status == TaskStatus.IN_PROGRESS
            and not self.is_complete()
            and not self.is_max_iterations_reached()
        )

    def save_to_file(
        self,
        agent: str = "default",
        vault_dir: Optional[Path] = None,
    ) -> Path:
        """Save task state to markdown file.

        Args:
            agent: Agent name for directory structure
            vault_dir: Base vault directory (default: FTE/vault)

        Returns:
            Path to saved file
        """
        if vault_dir is None:
            vault_dir = Path(__file__).parent.parent.parent / "vault"

        vault_dir = Path(vault_dir).resolve()
        in_progress_dir = vault_dir / "In_Progress" / agent
        in_progress_dir.mkdir(parents=True, exist_ok=True)

        filename = f"{self.task_id}.md"
        output_path = in_progress_dir / filename

        # Write markdown content
        markdown_content = self.to_markdown()
        output_path.write_text(markdown_content, encoding="utf-8")

        return output_path

    @classmethod
    def load_from_file(
        cls,
        task_id: str,
        agent: str = "default",
        vault_dir: Optional[Path] = None,
    ) -> Optional["TaskState"]:
        """Load task state from markdown file.

        Args:
            task_id: UUID of task to load
            agent: Agent name for directory structure
            vault_dir: Base vault directory

        Returns:
            TaskState instance or None if not found
        """
        if vault_dir is None:
            vault_dir = Path(__file__).parent.parent.parent / "vault"

        vault_dir = Path(vault_dir).resolve()
        in_progress_dir = vault_dir / "In_Progress" / agent
        file_path = in_progress_dir / f"{task_id}.md"

        if not file_path.exists():
            return None

        try:
            content = file_path.read_text(encoding="utf-8")

            # Parse YAML frontmatter
            if "---" not in content:
                return None

            parts = content.split("---", 3)
            if len(parts) < 2:
                return None

            frontmatter = yaml.safe_load(parts[1])

            # Parse status enum
            status_str = frontmatter.get("status", "in_progress")
            try:
                status = TaskStatus(status_str)
            except ValueError:
                status = TaskStatus.IN_PROGRESS

            # Parse datetime fields
            created = None
            if frontmatter.get("created"):
                try:
                    created = datetime.fromisoformat(frontmatter["created"])
                except ValueError:
                    pass

            completed_at = None
            if frontmatter.get("completed_at"):
                try:
                    completed_at = datetime.fromisoformat(frontmatter["completed_at"])
                except ValueError:
                    pass

            return cls(
                task_id=frontmatter.get("task_id", task_id),
                objective=frontmatter.get("objective", ""),
                created=created,
                iteration=frontmatter.get("iteration", 1),
                max_iterations=frontmatter.get("max_iterations", 10),
                status=status,
                state_data={},  # Will be loaded from body if needed
                completion_criteria=[],
                completed_criteria=[],
                error=None,
                completed_at=completed_at,
            )

        except Exception as e:
            # Log error but don't crash
            print(f"Warning: Failed to load task state {task_id}: {e}")
            return None
