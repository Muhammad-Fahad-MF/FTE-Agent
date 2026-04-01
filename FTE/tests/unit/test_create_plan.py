"""Unit tests for CreatePlanSkill."""

import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.skills.create_plan import CreatePlanSkill, LockTimeout, PlanGenerationError


@pytest.fixture
def mock_metrics_collector():
    """Create a mock metrics collector."""
    mock = MagicMock()
    mock.record_histogram = MagicMock()
    mock.increment_counter = MagicMock()
    mock.set_gauge = MagicMock()
    return mock


@pytest.fixture
def action_file_content():
    """Sample action file content for tests."""
    return """---
type: file_drop
source: Inbox/test.txt
created: 2026-04-01T10:00:00
status: pending
---

## Content
This is test content for the action file.

## Suggested Actions
- [ ] Review this file
- [ ] Process as needed
- [ ] Move to Done when complete
"""


class TestCreatePlanSkill:
    """Unit tests for CreatePlanSkill."""

    @patch('src.skills.base_skill.get_metrics_collector')
    def test_plan_generation_from_action_file(self, mock_get_metrics, monkeypatch, tmp_path, action_file_content):
        """Verify plan.md created with correct format."""
        # Setup
        monkeypatch.setenv("DEV_MODE", "true")
        monkeypatch.setenv("VAULT_PATH", str(tmp_path))
        mock_get_metrics.return_value = MagicMock()

        # Create action file
        needs_action = tmp_path / "Needs_Action"
        needs_action.mkdir(parents=True, exist_ok=True)
        action_file = needs_action / "FILE_test.md"
        action_file.write_text(action_file_content)

        # Create skill and generate plan
        skill = CreatePlanSkill()
        plan_path = skill.generate_plan(action_file)

        # Verify plan file created
        assert plan_path.exists()
        assert plan_path.parent.name == "Plans"
        assert plan_path.suffix == ".md"
        assert "Plan_FILE_test_" in plan_path.name

    @patch('src.skills.base_skill.get_metrics_collector')
    def test_yaml_frontmatter_includes_all_fields(self, mock_get_metrics, monkeypatch, tmp_path, action_file_content):
        """Verify 6 required fields present in frontmatter."""
        # Setup
        monkeypatch.setenv("DEV_MODE", "true")
        monkeypatch.setenv("VAULT_PATH", str(tmp_path))
        mock_get_metrics.return_value = MagicMock()

        # Create action file
        needs_action = tmp_path / "Needs_Action"
        needs_action.mkdir(parents=True, exist_ok=True)
        action_file = needs_action / "FILE_test.md"
        action_file.write_text(action_file_content)

        # Generate plan
        skill = CreatePlanSkill()
        plan_path = skill.generate_plan(action_file)

        # Read and parse frontmatter
        content = plan_path.read_text()
        import yaml
        frontmatter = yaml.safe_load(content.split("---")[1])

        # Verify all required fields
        assert "created" in frontmatter
        assert "status" in frontmatter
        assert "objective" in frontmatter
        assert "source_file" in frontmatter
        assert "estimated_steps" in frontmatter
        assert "requires_approval" in frontmatter

    @patch('src.skills.base_skill.get_metrics_collector')
    def test_step_extraction_from_suggested_actions(self, mock_get_metrics, monkeypatch, tmp_path, action_file_content):
        """Verify steps parsed correctly from Suggested Actions section."""
        # Setup
        monkeypatch.setenv("DEV_MODE", "true")
        monkeypatch.setenv("VAULT_PATH", str(tmp_path))
        mock_get_metrics.return_value = MagicMock()

        # Create action file with specific steps
        needs_action = tmp_path / "Needs_Action"
        needs_action.mkdir(parents=True, exist_ok=True)
        action_file = needs_action / "FILE_test.md"
        action_file.write_text(action_file_content)

        # Generate plan
        skill = CreatePlanSkill()
        plan_path = skill.generate_plan(action_file)

        # Verify steps in content
        content = plan_path.read_text()
        assert "**Step 1:**" in content
        assert "**Step 2:**" in content
        assert "**Step 3:**" in content
        assert "Review this file" in content

    @patch('src.skills.base_skill.get_metrics_collector')
    def test_status_updates_modify_frontmatter(self, mock_get_metrics, monkeypatch, tmp_path, action_file_content):
        """Verify status transitions work correctly."""
        # Setup
        monkeypatch.setenv("DEV_MODE", "true")
        monkeypatch.setenv("VAULT_PATH", str(tmp_path))
        mock_get_metrics.return_value = MagicMock()

        # Create action file
        needs_action = tmp_path / "Needs_Action"
        needs_action.mkdir(parents=True, exist_ok=True)
        action_file = needs_action / "FILE_test.md"
        action_file.write_text(action_file_content)

        # Generate plan
        skill = CreatePlanSkill()
        plan_path = skill.generate_plan(action_file)

        # Update status
        skill.update_plan_status(plan_path, "in_progress")

        # Verify update
        import yaml
        content = plan_path.read_text()
        frontmatter = yaml.safe_load(content.split("---")[1])
        assert frontmatter["status"] == "in_progress"

        # Update to completed
        skill.update_plan_status(plan_path, "completed")
        content = plan_path.read_text()
        frontmatter = yaml.safe_load(content.split("---")[1])
        assert frontmatter["status"] == "completed"

    @patch('src.skills.base_skill.get_metrics_collector')
    def test_invalid_status_raises_error(self, mock_get_metrics, monkeypatch, tmp_path, action_file_content):
        """Verify invalid status raises ValueError."""
        # Setup
        monkeypatch.setenv("DEV_MODE", "true")
        monkeypatch.setenv("VAULT_PATH", str(tmp_path))
        mock_get_metrics.return_value = MagicMock()

        # Create action file
        needs_action = tmp_path / "Needs_Action"
        needs_action.mkdir(parents=True, exist_ok=True)
        action_file = needs_action / "FILE_test.md"
        action_file.write_text(action_file_content)

        # Generate plan
        skill = CreatePlanSkill()
        plan_path = skill.generate_plan(action_file)

        # Try invalid status
        with pytest.raises(ValueError) as exc_info:
            skill.update_plan_status(plan_path, "invalid_status")

        assert "Invalid status" in str(exc_info.value)

    @patch('src.skills.base_skill.get_metrics_collector')
    def test_get_plan_status_returns_current_status(self, mock_get_metrics, monkeypatch, tmp_path, action_file_content):
        """Verify get_plan_status returns correct status."""
        # Setup
        monkeypatch.setenv("DEV_MODE", "true")
        monkeypatch.setenv("VAULT_PATH", str(tmp_path))
        mock_get_metrics.return_value = MagicMock()

        # Create action file
        needs_action = tmp_path / "Needs_Action"
        needs_action.mkdir(parents=True, exist_ok=True)
        action_file = needs_action / "FILE_test.md"
        action_file.write_text(action_file_content)

        # Generate plan
        skill = CreatePlanSkill()
        plan_path = skill.generate_plan(action_file)

        # Verify initial status
        assert skill.get_plan_status(plan_path) == "pending"

        # Update and verify
        skill.update_plan_status(plan_path, "in_progress")
        assert skill.get_plan_status(plan_path) == "in_progress"

    @patch('src.skills.base_skill.get_metrics_collector')
    def test_mark_step_complete_updates_checkbox(self, mock_get_metrics, monkeypatch, tmp_path, action_file_content):
        """Verify mark_step_complete changes checkbox to completed."""
        # Setup
        monkeypatch.setenv("DEV_MODE", "true")
        monkeypatch.setenv("VAULT_PATH", str(tmp_path))
        mock_get_metrics.return_value = MagicMock()

        # Create action file
        needs_action = tmp_path / "Needs_Action"
        needs_action.mkdir(parents=True, exist_ok=True)
        action_file = needs_action / "FILE_test.md"
        action_file.write_text(action_file_content)

        # Generate plan
        skill = CreatePlanSkill()
        plan_path = skill.generate_plan(action_file)

        # Mark step complete
        skill.mark_step_complete(plan_path, 1)

        # Verify checkbox updated
        content = plan_path.read_text()
        assert "[completed]" in content

    @patch('src.skills.base_skill.get_metrics_collector')
    def test_missing_action_file_raises_error(self, mock_get_metrics, monkeypatch, tmp_path):
        """Verify PlanGenerationError raised for missing action file."""
        # Setup
        monkeypatch.setenv("DEV_MODE", "true")
        monkeypatch.setenv("VAULT_PATH", str(tmp_path))
        mock_get_metrics.return_value = MagicMock()

        # Create skill
        skill = CreatePlanSkill()

        # Try to generate plan for non-existent file
        with pytest.raises(PlanGenerationError) as exc_info:
            skill.generate_plan(Path(tmp_path / "nonexistent.md"))

        assert "not found" in str(exc_info.value)

    @patch('src.skills.base_skill.get_metrics_collector')
    def test_dry_run_no_file_creation(self, mock_get_metrics, monkeypatch, tmp_path, action_file_content):
        """Verify dry_run mode doesn't create files."""
        # Setup
        monkeypatch.setenv("DEV_MODE", "true")
        monkeypatch.setenv("VAULT_PATH", str(tmp_path))
        mock_get_metrics.return_value = MagicMock()

        # Create action file
        needs_action = tmp_path / "Needs_Action"
        needs_action.mkdir(parents=True, exist_ok=True)
        action_file = needs_action / "FILE_test.md"
        action_file.write_text(action_file_content)

        # Create skill in dry-run mode
        skill = CreatePlanSkill(dry_run=True)
        plan_path = skill.generate_plan(action_file)

        # Plans directory should not be created (or be empty)
        plans_path = tmp_path / "Plans"
        # In dry-run, file is not created
        assert not plan_path.exists() or list(plans_path.iterdir()) == []

    @patch('src.skills.base_skill.get_metrics_collector')
    def test_metrics_emitted_on_generation(self, mock_get_metrics, monkeypatch, tmp_path, action_file_content):
        """Verify metrics are emitted during plan generation."""
        # Setup
        monkeypatch.setenv("DEV_MODE", "true")
        monkeypatch.setenv("VAULT_PATH", str(tmp_path))
        mock_metrics = MagicMock()
        mock_get_metrics.return_value = mock_metrics

        # Create action file
        needs_action = tmp_path / "Needs_Action"
        needs_action.mkdir(parents=True, exist_ok=True)
        action_file = needs_action / "FILE_test.md"
        action_file.write_text(action_file_content)

        # Generate plan
        skill = CreatePlanSkill()
        skill.generate_plan(action_file)

        # Verify metrics emitted
        assert mock_metrics.record_histogram.called
        assert mock_metrics.increment_counter.called

        # Check specific metrics (verify name and that value is recorded, ignore tags for now)
        assert mock_metrics.record_histogram.call_count >= 1
        histogram_call = mock_metrics.record_histogram.call_args_list[0]
        assert histogram_call[0][0] == "create_plan_duration"
        assert isinstance(histogram_call[0][1], float)
        
        # Check counter metric - verify it was called with create_plan_count and action_type tag
        # (correlation_id is also added automatically)
        increment_calls = mock_metrics.increment_counter.call_args_list
        create_plan_count_calls = [c for c in increment_calls if c[0][0] == "create_plan_count"]
        assert len(create_plan_count_calls) > 0
        # Verify action_type tag is present
        assert create_plan_count_calls[0][1]["tags"]["action_type"] == "file_drop"

    @patch('src.skills.base_skill.get_metrics_collector')
    def test_requires_approval_for_email_type(self, mock_get_metrics, monkeypatch, tmp_path):
        """Verify requires_approval is True for email action type."""
        # Setup
        monkeypatch.setenv("DEV_MODE", "true")
        monkeypatch.setenv("VAULT_PATH", str(tmp_path))
        mock_get_metrics.return_value = MagicMock()

        # Create email action file
        needs_action = tmp_path / "Needs_Action"
        needs_action.mkdir(parents=True, exist_ok=True)
        action_file = needs_action / "EMAIL_test.md"
        action_file.write_text("""---
type: email
from: test@example.com
to: recipient@example.com
subject: Test Email
---

## Content
Test email content
""")

        # Generate plan
        skill = CreatePlanSkill()
        plan_path = skill.generate_plan(action_file)

        # Verify requires_approval is True
        import yaml
        content = plan_path.read_text()
        frontmatter = yaml.safe_load(content.split("---")[1])
        assert frontmatter["requires_approval"] is True
