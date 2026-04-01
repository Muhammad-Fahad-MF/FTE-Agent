"""Unit and integration tests for generate_briefing skill."""

import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.skills.generate_briefing import BriefingGenerationError, GenerateBriefingSkill


class TestGenerateBriefingSkill:
    """Tests for GenerateBriefingSkill."""

    @pytest.fixture
    def temp_vault(self):
        """Create temporary vault directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            vault = Path(tmpdir) / "vault"
            vault.mkdir(parents=True)
            (vault / "Needs_Action").mkdir()
            (vault / "Plans").mkdir()
            (vault / "Done").mkdir()
            (vault / "Briefings").mkdir()
            (vault / "Pending_Approval").mkdir()
            (vault / "Approved").mkdir()
            (vault / "Rejected").mkdir()
            yield vault

    @pytest.fixture
    def skill(self, temp_vault):
        """Create GenerateBriefingSkill instance with mocked dependencies."""
        with patch("src.skills.base_skill.AuditLogger") as MockLogger:
            with patch("src.skills.base_skill.get_metrics_collector") as mock_get_metrics:
                mock_logger = MagicMock()
                MockLogger.return_value = mock_logger
                mock_metrics = MagicMock()
                mock_get_metrics.return_value = mock_metrics

                skill = GenerateBriefingSkill(vault_dir=temp_vault)
                yield skill

    def test_generate_daily_briefing_creates_file(self, skill, temp_vault):
        """Test daily briefing file creation."""
        date = datetime.now()
        briefing_path = skill.generate_daily_briefing(date)

        assert briefing_path.exists()
        assert "Briefings" in str(briefing_path.parent)
        assert briefing_path.name.startswith("Daily_")

    def test_generate_daily_briefing_content(self, skill, temp_vault):
        """Test daily briefing content format."""
        # Create some test files
        (temp_vault / "Needs_Action" / "FILE_001.md").write_text("---\ntype: test\n---\n")
        (temp_vault / "Done" / "FILE_002.md").write_text("---\ntype: test\n---\n")

        date = datetime.now()
        briefing_path = skill.generate_daily_briefing(date)

        content = briefing_path.read_text(encoding="utf-8")

        # Check required sections
        assert "Daily Briefing" in content
        assert "Summary" in content
        assert "Needs Action" in content
        assert "Today's Activity" in content
        assert date.strftime("%Y-%m-%d") in content

    def test_generate_daily_briefing_yaml_frontmatter(self, skill, temp_vault):
        """Test daily briefing YAML frontmatter."""
        date = datetime.now()
        briefing_path = skill.generate_daily_briefing(date)

        content = briefing_path.read_text(encoding="utf-8")

        # Check frontmatter
        assert content.startswith("---")
        assert "type: daily_briefing" in content
        assert f"date: {date.strftime('%Y-%m-%d')}" in content

    def test_generate_weekly_audit_creates_file(self, skill, temp_vault):
        """Test weekly audit file creation."""
        date = datetime.now()
        audit_path = skill.generate_weekly_audit(date)

        assert audit_path.exists()
        assert "Briefings" in str(audit_path.parent)
        assert audit_path.name.startswith("Weekly_Audit_")

    def test_generate_weekly_audit_content(self, skill, temp_vault):
        """Test weekly audit content format."""
        # Create some test files
        for i in range(5):
            (temp_vault / "Needs_Action" / f"FILE_{i:03d}.md").write_text(
                "---\ntype: test\n---\n"
            )
        for i in range(3):
            (temp_vault / "Done" / f"FILE_{i:03d}.md").write_text("---\ntype: test\n---\n")

        date = datetime.now()
        audit_path = skill.generate_weekly_audit(date)

        content = audit_path.read_text(encoding="utf-8")

        # Check required sections
        assert "Weekly Audit" in content
        assert "Key Metrics" in content
        assert "Approval Workflow" in content
        assert "Bottlenecks" in content
        assert "Recommendations" in content

    def test_generate_weekly_audit_yaml_frontmatter(self, skill, temp_vault):
        """Test weekly audit YAML frontmatter."""
        date = datetime.now()
        audit_path = skill.generate_weekly_audit(date)

        content = audit_path.read_text(encoding="utf-8")

        # Check frontmatter
        assert content.startswith("---")
        assert "type: weekly_audit" in content
        assert "week_start:" in content
        assert "week_end:" in content

    def test_generate_daily_briefing_dry_run(self, temp_vault):
        """Test dry run mode doesn't create file."""
        with patch("src.skills.base_skill.AuditLogger") as MockLogger:
            with patch("src.skills.base_skill.get_metrics_collector") as mock_get_metrics:
                mock_logger = MagicMock()
                MockLogger.return_value = mock_logger
                mock_metrics = MagicMock()
                mock_get_metrics.return_value = mock_metrics

                skill = GenerateBriefingSkill(vault_dir=temp_vault, dry_run=True)

                date = datetime.now()
                briefing_path = skill.generate_daily_briefing(date)

                # In dry run, file should not be created
                assert not briefing_path.exists()

    def test_generate_weekly_audit_dry_run(self, temp_vault):
        """Test dry run mode doesn't create file."""
        with patch("src.skills.base_skill.AuditLogger") as MockLogger:
            with patch("src.skills.base_skill.get_metrics_collector") as mock_get_metrics:
                mock_logger = MagicMock()
                MockLogger.return_value = mock_logger
                mock_metrics = MagicMock()
                mock_get_metrics.return_value = mock_metrics

                skill = GenerateBriefingSkill(vault_dir=temp_vault, dry_run=True)

                date = datetime.now()
                audit_path = skill.generate_weekly_audit(date)

                # In dry run, file should not be created
                assert not audit_path.exists()

    def test_execute_daily_briefing(self, skill):
        """Test execute method with daily briefing."""
        date = datetime.now()
        briefing_path = skill.execute(briefing_type="daily", date=date)

        assert briefing_path.exists()
        assert "Daily_" in briefing_path.name

    def test_execute_weekly_audit(self, skill):
        """Test execute method with weekly audit."""
        date = datetime.now()
        audit_path = skill.execute(briefing_type="weekly", date=date)

        assert audit_path.exists()
        assert "Weekly_Audit_" in audit_path.name

    def test_execute_invalid_type(self, skill):
        """Test execute method with invalid type."""
        with pytest.raises(ValueError, match="Invalid briefing_type"):
            skill.execute(briefing_type="invalid")

    def test_count_files_in_folder(self, skill, temp_vault):
        """Test file counting in folder."""
        # Create test files
        for i in range(5):
            (temp_vault / "Needs_Action" / f"FILE_{i:03d}.md").write_text("test")

        count = skill._count_files_in_folder(temp_vault / "Needs_Action")
        assert count == 5

    def test_count_files_in_nonexistent_folder(self, skill):
        """Test file counting in nonexistent folder."""
        count = skill._count_files_in_folder(Path("/nonexistent/folder"))
        assert count == 0

    def test_get_files_by_age(self, skill, temp_vault):
        """Test getting files by age."""
        # Create a recent file
        recent_file = temp_vault / "Needs_Action" / "RECENT.md"
        recent_file.write_text("test")

        files = skill._get_files_by_age(temp_vault / "Needs_Action", hours=1)
        assert len(files) >= 1
        assert any(f.name == "RECENT.md" for f in files)


class TestGenerateBriefingIntegration:
    """Integration tests for generate_briefing skill."""

    @pytest.fixture
    def temp_vault(self):
        """Create temporary vault directory with test data."""
        with tempfile.TemporaryDirectory() as tmpdir:
            vault = Path(tmpdir) / "vault"
            vault.mkdir(parents=True)
            (vault / "Needs_Action").mkdir()
            (vault / "Plans").mkdir()
            (vault / "Done").mkdir()
            (vault / "Briefings").mkdir()
            (vault / "Pending_Approval").mkdir()
            (vault / "Approved").mkdir()
            (vault / "Rejected").mkdir()

            # Create test data
            for i in range(10):
                (vault / "Needs_Action" / f"FILE_{i:03d}.md").write_text(
                    f"---\ntype: test\nid: {i}\n---\nContent {i}"
                )

            for i in range(5):
                (vault / "Done" / f"FILE_{i:03d}.md").write_text(
                    f"---\ntype: test\nid: {i}\n---\nCompleted {i}"
                )

            yield vault

    def test_daily_briefing_format(self, temp_vault):
        """Test daily briefing format with real data."""
        with patch("src.skills.base_skill.AuditLogger") as MockLogger:
            with patch("src.skills.base_skill.get_metrics_collector") as mock_get_metrics:
                mock_logger = MagicMock()
                MockLogger.return_value = mock_logger
                mock_metrics = MagicMock()
                mock_get_metrics.return_value = mock_metrics

                skill = GenerateBriefingSkill(vault_dir=temp_vault)

                date = datetime.now()
                briefing_path = skill.generate_daily_briefing(date)

                content = briefing_path.read_text(encoding="utf-8")

                # Verify format
                assert "---" in content
                assert "type: daily_briefing" in content
                assert "| Metric | Count |" in content
                assert "Needs Action" in content
                assert "10" in content  # Should show 10 needs action items

    def test_weekly_audit_metrics(self, temp_vault):
        """Test weekly audit includes correct metrics."""
        with patch("src.skills.base_skill.AuditLogger") as MockLogger:
            with patch("src.skills.base_skill.get_metrics_collector") as mock_get_metrics:
                mock_logger = MagicMock()
                MockLogger.return_value = mock_logger
                mock_metrics = MagicMock()
                mock_get_metrics.return_value = mock_metrics

                skill = GenerateBriefingSkill(vault_dir=temp_vault)

                date = datetime.now()
                audit_path = skill.generate_weekly_audit(date)

                content = audit_path.read_text(encoding="utf-8")

                # Verify metrics table
                assert "| Metric | Value |" in content
                assert "Total Needs Action" in content
                assert "Total Done" in content
                assert "Completion Rate" in content

    def test_briefing_content_generation(self, temp_vault):
        """Test briefing content is generated from vault data."""
        with patch("src.skills.base_skill.AuditLogger") as MockLogger:
            with patch("src.skills.base_skill.get_metrics_collector") as mock_get_metrics:
                mock_logger = MagicMock()
                MockLogger.return_value = mock_logger
                mock_metrics = MagicMock()
                mock_get_metrics.return_value = mock_metrics

                skill = GenerateBriefingSkill(vault_dir=temp_vault)

                date = datetime.now()
                briefing_path = skill.generate_daily_briefing(date)

                content = briefing_path.read_text(encoding="utf-8")

                # Should list some files from Needs_Action
                assert "FILE_" in content
