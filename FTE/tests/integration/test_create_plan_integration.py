"""Integration tests for CreatePlanSkill.

Tests end-to-end functionality including file system interactions,
plan generation, and status tracking across multiple operations.
"""

import os
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture
def action_file_content():
    """Sample action file content for integration tests."""
    return """---
type: file_drop
source: Inbox/test_document.txt
created: 2026-04-01T10:00:00
status: pending
---

## Content
This is a test document for integration testing.

## Suggested Actions
- [ ] Review the document
- [ ] Extract key information
- [ ] Create action items
- [ ] Move to Done when complete
"""


class TestCreatePlanIntegration:
    """Integration tests for CreatePlanSkill."""

    @patch('src.skills.base_skill.get_metrics_collector')
    def test_action_file_triggers_plan_generation(self, mock_get_metrics, monkeypatch, tmp_path, action_file_content):
        """Verify dropping file in Needs_Action/ triggers Plan.md creation.
        
        End-to-end test simulating real workflow:
        1. Action file created in Needs_Action/
        2. CreatePlanSkill.generate_plan() called
        3. Plan.md created in Plans/ directory
        4. Plan contains correct frontmatter and steps
        """
        # Setup
        monkeypatch.setenv("DEV_MODE", "true")
        monkeypatch.setenv("VAULT_PATH", str(tmp_path))
        mock_get_metrics.return_value = MagicMock()

        from src.skills.create_plan import CreatePlanSkill

        # Create Needs_Action directory and action file
        needs_action = tmp_path / "Needs_Action"
        needs_action.mkdir(parents=True, exist_ok=True)
        action_file = needs_action / "FILE_integration_test.md"
        action_file.write_text(action_file_content)

        # Create skill and generate plan
        skill = CreatePlanSkill()
        plan_path = skill.generate_plan(action_file)

        # Verify plan was created in Plans/ directory
        assert plan_path.exists(), "Plan file should be created"
        assert plan_path.parent.name == "Plans", "Plan should be in Plans/ directory"
        assert plan_path.suffix == ".md", "Plan should be markdown file"
        assert "Plan_FILE_integration_test_" in plan_path.name, "Plan name should include source file stem"

        # Verify plan content
        content = plan_path.read_text()
        
        # Check YAML frontmatter present
        assert content.startswith("---"), "Plan should start with YAML frontmatter"
        
        # Check required frontmatter fields
        import yaml
        frontmatter = yaml.safe_load(content.split("---")[1])
        assert frontmatter["status"] == "pending", "Initial status should be pending"
        assert "objective" in frontmatter, "Should have objective field"
        assert frontmatter["source_file"] == str(action_file.absolute()), "Should reference source file"
        assert frontmatter["requires_approval"] is False, "File drop should not require approval"
        
        # Check steps section
        assert "## Steps" in content, "Should have Steps section"
        assert "**Step 1:**" in content, "Should have numbered steps"
        assert "Review the document" in content, "Should include extracted steps"
        
        # Check notes section
        assert "## Notes" in content, "Should have Notes section"

    @patch('src.skills.base_skill.get_metrics_collector')
    def test_plan_status_tracking_across_updates(self, mock_get_metrics, monkeypatch, tmp_path, action_file_content):
        """Verify status transitions work correctly across multiple updates.
        
        End-to-end test for status lifecycle:
        1. Plan created with 'pending' status
        2. Update to 'in_progress'
        3. Mark step as complete
        4. Update to 'completed'
        5. Verify all transitions persisted correctly
        """
        # Setup
        monkeypatch.setenv("DEV_MODE", "true")
        monkeypatch.setenv("VAULT_PATH", str(tmp_path))
        mock_metrics = MagicMock()
        mock_get_metrics.return_value = mock_metrics

        from src.skills.create_plan import CreatePlanSkill

        # Create Needs_Action directory and action file
        needs_action = tmp_path / "Needs_Action"
        needs_action.mkdir(parents=True, exist_ok=True)
        action_file = needs_action / "FILE_status_test.md"
        action_file.write_text(action_file_content)

        # Create skill and generate plan
        skill = CreatePlanSkill()
        plan_path = skill.generate_plan(action_file)

        # Verify initial status
        initial_status = skill.get_plan_status(plan_path)
        assert initial_status == "pending", f"Initial status should be pending, got {initial_status}"

        # Update to in_progress
        skill.update_plan_status(plan_path, "in_progress")
        status = skill.get_plan_status(plan_path)
        assert status == "in_progress", f"Status should be in_progress, got {status}"

        # Mark first step as complete
        skill.mark_step_complete(plan_path, 1)
        
        # Verify step was marked in file
        content = plan_path.read_text()
        # First step should be marked completed
        lines = content.split("\n")
        step_lines = [l for l in lines if "**Step 1:**" in l]
        assert len(step_lines) > 0, "Step 1 should exist"
        # Check that step is marked (either [completed] or not (pending))
        assert "[completed]" in str(step_lines), "Step 1 should be marked as completed"

        # Update to awaiting_approval
        skill.update_plan_status(plan_path, "awaiting_approval")
        status = skill.get_plan_status(plan_path)
        assert status == "awaiting_approval", f"Status should be awaiting_approval, got {status}"

        # Update to completed
        skill.update_plan_status(plan_path, "completed")
        status = skill.get_plan_status(plan_path)
        assert status == "completed", f"Status should be completed, got {status}"

        # Verify final content
        content = plan_path.read_text()
        import yaml
        frontmatter = yaml.safe_load(content.split("---")[1])
        assert frontmatter["status"] == "completed", "Final status should be completed"

        # Verify plan generation metrics were emitted
        assert mock_metrics.record_histogram.called, "Should record duration metric"
        assert mock_metrics.increment_counter.called, "Should increment counter metric"

    @patch('src.skills.base_skill.get_metrics_collector')
    def test_email_action_requires_approval(self, mock_get_metrics, monkeypatch, tmp_path):
        """Verify email type actions have requires_approval=True.
        
        Integration test for approval requirement logic:
        1. Create email action file
        2. Generate plan
        3. Verify requires_approval is True
        """
        # Setup
        monkeypatch.setenv("DEV_MODE", "true")
        monkeypatch.setenv("VAULT_PATH", str(tmp_path))
        mock_get_metrics.return_value = MagicMock()

        from src.skills.create_plan import CreatePlanSkill

        # Create email action file
        needs_action = tmp_path / "Needs_Action"
        needs_action.mkdir(parents=True, exist_ok=True)
        email_action = needs_action / "EMAIL_test.md"
        email_action.write_text("""---
type: email
from: sender@example.com
to: recipient@example.com
subject: Important Message
---

## Content
This is an email that requires approval.
""")

        # Generate plan
        skill = CreatePlanSkill()
        plan_path = skill.generate_plan(email_action)

        # Verify requires_approval is True
        content = plan_path.read_text()
        import yaml
        frontmatter = yaml.safe_load(content.split("---")[1])
        assert frontmatter["requires_approval"] is True, "Email should require approval"

    @patch('src.skills.base_skill.get_metrics_collector')
    def test_plan_generation_performance(self, mock_get_metrics, monkeypatch, tmp_path, action_file_content):
        """Verify plan generation completes within performance budget (<2 seconds p95)."""
        # Setup
        monkeypatch.setenv("DEV_MODE", "true")
        monkeypatch.setenv("VAULT_PATH", str(tmp_path))
        mock_metrics = MagicMock()
        mock_get_metrics.return_value = mock_metrics

        from src.skills.create_plan import CreatePlanSkill

        # Create action file
        needs_action = tmp_path / "Needs_Action"
        needs_action.mkdir(parents=True, exist_ok=True)
        action_file = needs_action / "FILE_perf_test.md"
        action_file.write_text(action_file_content)

        # Measure generation time
        skill = CreatePlanSkill()
        start = time.time()
        plan_path = skill.generate_plan(action_file)
        duration = time.time() - start

        # Verify performance budget (p95 < 2 seconds)
        assert duration < 2.0, f"Plan generation took {duration}s, should be <2s"

        # Verify metric was recorded
        histogram_calls = [
            c for c in mock_metrics.record_histogram.call_args_list
            if c[0][0] == "create_plan_duration"
        ]
        assert len(histogram_calls) > 0, "Should record duration metric"
        assert histogram_calls[0][0][1] < 2.0, "Recorded duration should be <2s"
