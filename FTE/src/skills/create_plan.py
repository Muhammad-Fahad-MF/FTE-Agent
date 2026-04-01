"""Create Plan Skill for generating structured Plan.md files from action files.

Usage:
    from src.skills.create_plan import CreatePlanSkill
    
    skill = CreatePlanSkill()
    plan_path = skill.generate_plan(action_file=Path("vault/Needs_Action/FILE_123.md"))
    
    # Update plan status
    skill.update_plan_status(plan_path, "in_progress")
    
    # Mark step as complete
    skill.mark_step_complete(plan_path, step_number=1)
"""

import os
import re
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

import yaml

from .base_skill import BaseSkill

# Cross-platform file locking
if sys.platform == "win32":
    import msvcrt

    def _lock_file_windows(f):
        """Lock file on Windows."""
        try:
            msvcrt.locking(f.fileno(), msvcrt.LK_LOCK, 1)
            return True
        except OSError:
            return False

    def _unlock_file_windows(f):
        """Unlock file on Windows."""
        try:
            f.seek(0)
            msvcrt.locking(f.fileno(), msvcrt.LK_UNLCK, 1)
        except OSError:
            pass
else:
    import fcntl

    def _lock_file_unix(f):
        """Lock file on Unix-like systems."""
        try:
            fcntl.flock(f.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            return True
        except (IOError, OSError):
            return False

    def _unlock_file_unix(f):
        """Unlock file on Unix-like systems."""
        try:
            fcntl.flock(f.fileno(), fcntl.LOCK_UN)
        except OSError:
            pass


class PlanGenerationError(Exception):
    """Raised when plan generation fails."""

    pass


class LockTimeout(Exception):
    """Raised when file lock cannot be acquired within timeout."""

    pass


class CreatePlanSkill(BaseSkill):
    """Skill for generating and managing Plan.md files.

    Features:
    - Generate structured plans from action files
    - YAML frontmatter with status tracking
    - Step extraction and checkbox generation
    - File locking for concurrent update safety
    - Circuit breaker protection
    - Metrics emission
    """

    # Valid plan statuses
    VALID_STATUSES = ["pending", "in_progress", "awaiting_approval", "completed", "cancelled"]

    # Lock timeout in seconds
    LOCK_TIMEOUT = 10

    def __init__(
        self,
        dry_run: bool = False,
        correlation_id: Optional[str] = None,
    ) -> None:
        """Initialize create_plan skill.

        Args:
            dry_run: If True, log without creating files
            correlation_id: Unique ID for tracking
        """
        super().__init__(dry_run=dry_run, correlation_id=correlation_id)
        self.vault_path = Path(os.getenv("VAULT_PATH", "./vault"))

    def generate_plan(self, action_file: Path) -> Path:
        """Generate a Plan.md file from an action file.

        Args:
            action_file: Path to the action file

        Returns:
            Path to the created plan file

        Raises:
            PlanGenerationError: If action file is invalid or generation fails
        """
        start_time = time.perf_counter()

        try:
            # Validate DEV_MODE
            self.validate_dev_mode()

            # Validate action file exists
            if not action_file.exists():
                raise PlanGenerationError(f"Action file not found: {action_file}")

            # Read action file
            content = action_file.read_text(encoding="utf-8")

            # Parse YAML frontmatter
            frontmatter = self._parse_frontmatter(content)
            if not frontmatter:
                raise PlanGenerationError(f"Invalid YAML frontmatter in {action_file}")

            # Extract objective from content
            objective = self._extract_objective(content)

            # Determine if approval is required
            requires_approval = self._requires_approval(frontmatter)

            # Generate plan frontmatter
            plan_frontmatter = self._generate_plan_frontmatter(
                objective=objective,
                source_file=action_file,
                requires_approval=requires_approval,
            )

            # Extract steps from action file
            steps = self._extract_steps(content)

            # Generate plan content
            plan_content = self._generate_plan_content(
                frontmatter=plan_frontmatter,
                steps=steps,
            )

            # Create Plans directory if needed
            plans_path = self.vault_path / "Plans"
            plans_path.mkdir(parents=True, exist_ok=True)

            # Generate plan file name
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            plan_filename = f"Plan_{action_file.stem}_{timestamp}.md"
            plan_file_path = plans_path / plan_filename

            # Write plan file (unless dry-run)
            if not self.dry_run:
                plan_file_path.write_text(plan_content, encoding="utf-8")
            else:
                self.log_action(
                    "INFO",
                    "plan_generation_dry_run",
                    {"would_create": str(plan_file_path), "source": str(action_file)},
                )

            # Log success
            self.log_action(
                "INFO",
                "plan_generated",
                {
                    "plan_file": str(plan_file_path),
                    "source_file": str(action_file),
                    "steps_count": len(steps),
                },
            )

            # Emit metrics
            duration = time.perf_counter() - start_time
            self.emit_metric("create_plan_duration", duration)
            self.emit_metric("create_plan_count", 1.0, tags={"action_type": frontmatter.get("type", "unknown")})

            return plan_file_path

        except Exception as e:
            self.log_action(
                "ERROR",
                "plan_generation_failed",
                {"source_file": str(action_file), "error": str(e)},
            )
            self.emit_metric("create_plan_errors", 1.0)
            raise PlanGenerationError(f"Failed to generate plan: {e}") from e

    def _parse_frontmatter(self, content: str) -> Optional[dict[str, Any]]:
        """Parse YAML frontmatter from content.

        Args:
            content: File content with YAML frontmatter

        Returns:
            Parsed frontmatter dict or None if not found
        """
        if not content.startswith("---"):
            return None

        try:
            # Find end of frontmatter
            end_index = content.find("---", 3)
            if end_index == -1:
                return None

            # Extract and parse YAML
            yaml_content = content[4:end_index].strip()
            return yaml.safe_load(yaml_content)
        except yaml.YAMLError:
            return None

    def _extract_objective(self, content: str) -> str:
        """Extract objective from action file content.

        Args:
            content: Action file content

        Returns:
            Objective string (first non-empty line after frontmatter, max 100 chars)
        """
        # Remove frontmatter
        if content.startswith("---"):
            end_index = content.find("---", 3)
            if end_index != -1:
                content = content[end_index + 3 :]

        # Find first non-empty line
        for line in content.strip().split("\n"):
            line = line.strip()
            if line and not line.startswith("#"):
                # Truncate to 100 chars
                return line[:100]

        return "Process this action"

    def _requires_approval(self, frontmatter: dict[str, Any]) -> bool:
        """Determine if action requires approval.

        Args:
            frontmatter: Action file frontmatter

        Returns:
            True if approval required
        """
        action_type = frontmatter.get("type", "")
        return action_type in ["email", "linkedin", "approval_request"]

    def _generate_plan_frontmatter(
        self,
        objective: str,
        source_file: Path,
        requires_approval: bool,
    ) -> dict[str, Any]:
        """Generate plan YAML frontmatter.

        Args:
            objective: Plan objective
            source_file: Source action file path
            requires_approval: Whether approval is needed

        Returns:
            Frontmatter dict
        """
        return {
            "created": datetime.now().isoformat(),
            "status": "pending",
            "objective": objective,
            "source_file": str(source_file.absolute()),
            "estimated_steps": 5,
            "requires_approval": requires_approval,
        }

    def _extract_steps(self, content: str) -> list[str]:
        """Extract steps from action file content.

        Args:
            content: Action file content

        Returns:
            List of step descriptions (3-10 steps)
        """
        steps = []

        # Look for "Suggested Actions" section
        suggested_section = re.search(r"##\s*Suggested Actions\s*\n(.*?)(?=##|$)", content, re.DOTALL | re.IGNORECASE)
        if suggested_section:
            # Extract checkbox items
            checkboxes = re.findall(r"-\s*\[\s*\]\s*(.+)", suggested_section.group(1))
            steps.extend(checkboxes)

        # If no steps found, generate default steps
        if len(steps) == 0:
            steps = [
                "Review the action file",
                "Determine required actions",
                "Execute the plan",
                "Verify results",
                "Move to Done when complete",
            ]

        # Ensure 3-10 steps
        if len(steps) < 3:
            while len(steps) < 3:
                steps.append(f"Additional step {len(steps) + 1}")
        elif len(steps) > 10:
            steps = steps[:10]

        return steps

    def _generate_plan_content(
        self,
        frontmatter: dict[str, Any],
        steps: list[str],
    ) -> str:
        """Generate complete plan file content.

        Args:
            frontmatter: Plan frontmatter dict
            steps: List of step descriptions

        Returns:
            Complete plan file content
        """
        # Generate YAML frontmatter
        yaml_content = yaml.dump(frontmatter, default_flow_style=False, sort_keys=False)

        # Generate steps section
        steps_content = "\n".join(
            [f"- [ ] **Step {i + 1}:** {step} (pending)  # ~10 min" for i, step in enumerate(steps)]
        )

        content = f"""---
{yaml_content}---

## Steps

{steps_content}

## Notes

[Additional context and observations]
"""
        return content

    def _acquire_lock(self, plan_file: Path) -> Any:
        """Acquire file lock for safe concurrent updates.

        Args:
            plan_file: Path to plan file

        Returns:
            File handle (pass to _release_lock)

        Raises:
            LockTimeout: If lock cannot be acquired within timeout
        """
        start_time = time.time()

        # Ensure file exists
        if not plan_file.exists():
            plan_file.touch()

        # Open file for locking
        lock_file = open(plan_file, "r+", encoding="utf-8")

        while True:
            if sys.platform == "win32":
                if _lock_file_windows(lock_file):
                    return lock_file
            else:
                if _lock_file_unix(lock_file):
                    return lock_file

            if time.time() - start_time > self.LOCK_TIMEOUT:
                lock_file.close()
                raise LockTimeout(f"Could not acquire lock on {plan_file} within {self.LOCK_TIMEOUT}s")
            time.sleep(0.1)

    def _release_lock(self, lock_file: Any) -> None:
        """Release file lock.

        Args:
            lock_file: File handle from _acquire_lock
        """
        try:
            if sys.platform == "win32":
                _unlock_file_windows(lock_file)
            else:
                _unlock_file_unix(lock_file)
            lock_file.close()
        except Exception as e:
            self.log_action("WARNING", "lock_release_error", {"error": str(e)})

    def update_plan_status(self, plan_file: Path, new_status: str) -> None:
        """Update plan status in frontmatter.

        Args:
            plan_file: Path to plan file
            new_status: New status value

        Raises:
            ValueError: If status is invalid
            PlanGenerationError: If file update fails
        """
        if new_status not in self.VALID_STATUSES:
            raise ValueError(f"Invalid status: {new_status}. Valid: {self.VALID_STATUSES}")

        lock = None
        try:
            # Acquire lock
            lock = self._acquire_lock(plan_file)

            # Read current content (file handle already open from lock)
            content = lock.read()
            if not content:
                # File is empty, try reading directly
                lock.close()
                content = plan_file.read_text(encoding="utf-8")
                lock = self._acquire_lock(plan_file)  # Re-acquire lock

            # Parse frontmatter
            frontmatter = self._parse_frontmatter(content)
            if not frontmatter:
                raise PlanGenerationError(f"Invalid frontmatter in {plan_file}")

            # Update status
            old_status = frontmatter.get("status", "unknown")
            frontmatter["status"] = new_status

            # Find end of frontmatter
            end_index = content.find("---", 3)
            if end_index == -1:
                raise PlanGenerationError(f"Invalid frontmatter format in {plan_file}")

            # Generate new frontmatter
            yaml_content = yaml.dump(frontmatter, default_flow_style=False, sort_keys=False)
            new_content = f"---\n{yaml_content}---{content[end_index + 3 :]}"

            # Write back (truncate and write)
            lock.seek(0)
            lock.truncate()
            lock.write(new_content)
            lock.flush()

            # Log
            self.log_action(
                "INFO",
                "plan_status_updated",
                {"plan_file": str(plan_file), "old_status": old_status, "new_status": new_status},
            )

            # Emit metric
            self.emit_metric("plan_status_changes", 1.0, tags={"status": new_status})

        finally:
            if lock:
                self._release_lock(lock)

    def mark_step_complete(self, plan_file: Path, step_number: int) -> None:
        """Mark a step as complete in the plan.

        Args:
            plan_file: Path to plan file
            step_number: Step number to mark (1-indexed)

        Raises:
            PlanGenerationError: If update fails
        """
        lock = None
        try:
            # Acquire lock
            lock = self._acquire_lock(plan_file)

            # Read current content (file handle already open from lock)
            content = lock.read()
            if not content:
                # File is empty, try reading directly
                lock.close()
                content = plan_file.read_text(encoding="utf-8")
                lock = self._acquire_lock(plan_file)  # Re-acquire lock

            # Find and update step checkbox
            pattern = rf"(- \[ \] \*\*Step {step_number}:\*\*.*)\(pending\)"
            replacement = rf"\1[completed]"

            new_content = re.sub(pattern, replacement, content)

            if new_content == content:
                self.log_action(
                    "WARNING",
                    "step_not_found",
                    {"plan_file": str(plan_file), "step_number": step_number},
                )
                return

            # Write back (truncate and write)
            lock.seek(0)
            lock.truncate()
            lock.write(new_content)
            lock.flush()

            # Log
            self.log_action(
                "INFO",
                "step_completed",
                {"plan_file": str(plan_file), "step_number": step_number},
            )

        finally:
            if lock:
                self._release_lock(lock)

    def get_plan_status(self, plan_file: Path) -> str:
        """Get current plan status.

        Args:
            plan_file: Path to plan file

        Returns:
            Current status string
        """
        content = plan_file.read_text(encoding="utf-8")
        frontmatter = self._parse_frontmatter(content)

        if not frontmatter:
            return "unknown"

        return frontmatter.get("status", "unknown")

    def execute(self, action_file: Path) -> Path:
        """Execute the skill (alias for generate_plan).

        Args:
            action_file: Path to action file

        Returns:
            Path to created plan file
        """
        return self.generate_plan(action_file)
