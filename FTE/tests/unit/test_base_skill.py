"""Unit tests for BaseSkill abstract base class."""

import os
import sys
import uuid
from io import StringIO
from unittest.mock import MagicMock, patch

import pytest

from src.skills.base_skill import BaseSkill


class ConcreteSkill(BaseSkill):
    """Concrete implementation of BaseSkill for testing."""

    def execute(self, *args, **kwargs):
        """Execute the skill."""
        return {"status": "executed", "dry_run": self.dry_run}


class TestBaseSkillInitialization:
    """Tests for BaseSkill initialization."""

    def test_correlation_id_auto_generation(self):
        """Test correlation_id is auto-generated if not provided."""
        with patch("src.skills.base_skill.AuditLogger"):
            with patch("src.skills.base_skill.get_metrics_collector"):
                skill = ConcreteSkill()

                assert skill.correlation_id is not None
                # Should be a valid UUID string
                uuid.UUID(skill.correlation_id)  # Should not raise

    def test_correlation_id_from_parameter(self):
        """Test correlation_id can be provided."""
        custom_id = "test-correlation-id-12345"

        with patch("src.skills.base_skill.AuditLogger"):
            with patch("src.skills.base_skill.get_metrics_collector"):
                skill = ConcreteSkill(correlation_id=custom_id)

                assert skill.correlation_id == custom_id

    def test_dry_run_default_false(self):
        """Test dry_run defaults to False."""
        with patch("src.skills.base_skill.AuditLogger"):
            with patch("src.skills.base_skill.get_metrics_collector"):
                skill = ConcreteSkill()

                assert skill.dry_run is False

    def test_dry_run_from_parameter(self):
        """Test dry_run can be set from parameter."""
        with patch("src.skills.base_skill.AuditLogger"):
            with patch("src.skills.base_skill.get_metrics_collector"):
                skill = ConcreteSkill(dry_run=True)

                assert skill.dry_run is True

    def test_logger_initialization(self):
        """Test logger is initialized with correct component name."""
        with patch("src.skills.base_skill.AuditLogger") as mock_logger_class:
            with patch("src.skills.base_skill.get_metrics_collector"):
                mock_logger = MagicMock()
                mock_logger_class.return_value = mock_logger

                skill = ConcreteSkill()

                mock_logger_class.assert_called_once_with(component="ConcreteSkill")
                assert skill.logger == mock_logger

    def test_metrics_initialization(self):
        """Test metrics collector is initialized."""
        with patch("src.skills.base_skill.AuditLogger"):
            with patch("src.skills.base_skill.get_metrics_collector") as mock_get_metrics:
                mock_metrics = MagicMock()
                mock_get_metrics.return_value = mock_metrics

                skill = ConcreteSkill()

                mock_get_metrics.assert_called_once()
                assert skill.metrics == mock_metrics


class TestBaseSkillDevModeValidation:
    """Tests for DEV_MODE validation."""

    @pytest.fixture
    def cleanup_env(self):
        """Clean up DEV_MODE environment variable after test."""
        original = os.environ.get("DEV_MODE")
        yield
        if original is None:
            os.environ.pop("DEV_MODE", None)
        else:
            os.environ["DEV_MODE"] = original

    def test_dev_mode_valid_true(self, cleanup_env):
        """Test validate_dev_mode returns True when DEV_MODE='true'."""
        os.environ["DEV_MODE"] = "true"

        with patch("src.skills.base_skill.AuditLogger"):
            with patch("src.skills.base_skill.get_metrics_collector"):
                skill = ConcreteSkill()

                result = skill.validate_dev_mode()

                assert result is True

    def test_dev_mode_invalid_false_raises(self, cleanup_env):
        """Test validate_dev_mode raises SystemExit when DEV_MODE='false'."""
        os.environ["DEV_MODE"] = "false"

        with patch("src.skills.base_skill.AuditLogger"):
            with patch("src.skills.base_skill.get_metrics_collector"):
                skill = ConcreteSkill()

                # Capture stderr
                captured = StringIO()
                old_stderr = sys.stderr
                sys.stderr = captured

                try:
                    with pytest.raises(SystemExit):
                        skill.validate_dev_mode()
                finally:
                    sys.stderr = old_stderr

                # Verify error message
                output = captured.getvalue()
                assert "DEV_MODE must be set to 'true'" in output

    def test_dev_mode_not_set_raises(self, cleanup_env):
        """Test validate_dev_mode raises when DEV_MODE not set."""
        os.environ.pop("DEV_MODE", None)

        with patch("src.skills.base_skill.AuditLogger"):
            with patch("src.skills.base_skill.get_metrics_collector"):
                skill = ConcreteSkill()

                with pytest.raises(SystemExit):
                    skill.validate_dev_mode()

    def test_dev_mode_case_sensitive(self, cleanup_env):
        """Test validate_dev_mode is case-sensitive."""
        os.environ["DEV_MODE"] = "True"  # Capital T

        with patch("src.skills.base_skill.AuditLogger"):
            with patch("src.skills.base_skill.get_metrics_collector"):
                skill = ConcreteSkill()

                with pytest.raises(SystemExit):
                    skill.validate_dev_mode()

    def test_dev_mode_logs_error_before_exit(self, cleanup_env):
        """Test validate_dev_mode logs ERROR before exiting."""
        os.environ["DEV_MODE"] = "false"

        with patch("src.skills.base_skill.AuditLogger") as mock_logger_class:
            with patch("src.skills.base_skill.get_metrics_collector"):
                mock_logger = MagicMock()
                mock_logger_class.return_value = mock_logger

                skill = ConcreteSkill()

                captured = StringIO()
                old_stderr = sys.stderr
                sys.stderr = captured

                try:
                    with pytest.raises(SystemExit):
                        skill.validate_dev_mode()
                finally:
                    sys.stderr = old_stderr

                # Verify error was logged
                mock_logger.log.assert_called_once()
                call_args = mock_logger.log.call_args
                assert call_args[0][0] == "ERROR"
                assert call_args[0][1] == "dev_mode_not_set"


class TestBaseSkillLogging:
    """Tests for logging functionality."""

    @pytest.fixture
    def skill_with_mocks(self):
        """Create skill with mocked logger and metrics."""
        with patch("src.skills.base_skill.AuditLogger") as mock_logger_class:
            with patch("src.skills.base_skill.get_metrics_collector") as mock_get_metrics:
                mock_logger = MagicMock()
                mock_logger_class.return_value = mock_logger
                mock_metrics = MagicMock()
                mock_get_metrics.return_value = mock_metrics

                skill = ConcreteSkill(correlation_id="test-id-123")
                yield skill, mock_logger, mock_metrics

    def test_log_action_calls_logger(self, skill_with_mocks):
        """Test log_action calls logger.log with correct parameters."""
        skill, mock_logger, _ = skill_with_mocks

        skill.log_action("INFO", "test_action", {"key": "value"})

        mock_logger.log.assert_called_once_with(
            "INFO",
            "test_action",
            {"key": "value"},
            correlation_id="test-id-123",
        )

    def test_log_action_with_different_levels(self, skill_with_mocks):
        """Test log_action works with different log levels."""
        skill, mock_logger, _ = skill_with_mocks

        skill.log_action("WARNING", "warning_action", {})
        skill.log_action("ERROR", "error_action", {"error": "test"})

        assert mock_logger.log.call_count == 2
        calls = mock_logger.log.call_args_list
        assert calls[0][0][0] == "WARNING"
        assert calls[1][0][0] == "ERROR"

    def test_log_action_includes_correlation_id(self, skill_with_mocks):
        """Test log_action includes correlation_id in call."""
        skill, mock_logger, _ = skill_with_mocks

        skill.log_action("INFO", "action", {})

        call_kwargs = mock_logger.log.call_args[1]
        assert "correlation_id" in call_kwargs
        assert call_kwargs["correlation_id"] == "test-id-123"


class TestBaseSkillMetrics:
    """Tests for metrics emission functionality."""

    @pytest.fixture
    def skill_with_mocks(self):
        """Create skill with mocked logger and metrics."""
        with patch("src.skills.base_skill.AuditLogger") as mock_logger_class:
            with patch("src.skills.base_skill.get_metrics_collector") as mock_get_metrics:
                mock_logger = MagicMock()
                mock_logger_class.return_value = mock_logger
                mock_metrics = MagicMock()
                mock_get_metrics.return_value = mock_metrics

                skill = ConcreteSkill(correlation_id="test-metrics-id")
                yield skill, mock_logger, mock_metrics

    def test_emit_metric_histogram(self, skill_with_mocks):
        """Test emit_metric records histogram for duration metrics."""
        skill, _, mock_metrics = skill_with_mocks

        skill.emit_metric("test_duration", 1.5)

        mock_metrics.record_histogram.assert_called_once_with(
            "test_duration",
            1.5,
            tags={"correlation_id": "test-metrics-id"},
        )

    def test_emit_metric_counter(self, skill_with_mocks):
        """Test emit_metric increments counter for count metrics."""
        skill, _, mock_metrics = skill_with_mocks

        skill.emit_metric("test_count", 5.0)

        mock_metrics.increment_counter.assert_called_once_with(
            "test_count",
            5.0,
            tags={"correlation_id": "test-metrics-id"},
        )

    def test_emit_metric_errors(self, skill_with_mocks):
        """Test emit_metric increments counter for error metrics."""
        skill, _, mock_metrics = skill_with_mocks

        skill.emit_metric("test_errors", 1.0)

        mock_metrics.increment_counter.assert_called_once_with(
            "test_errors",
            1.0,
            tags={"correlation_id": "test-metrics-id"},
        )

    def test_emit_metric_gauge(self, skill_with_mocks):
        """Test emit_metric sets gauge for other metrics."""
        skill, _, mock_metrics = skill_with_mocks

        skill.emit_metric("test_gauge", 42.0)

        mock_metrics.set_gauge.assert_called_once_with(
            "test_gauge",
            42.0,
            tags={"correlation_id": "test-metrics-id"},
        )

    def test_emit_metric_with_custom_tags(self, skill_with_mocks):
        """Test emit_metric includes custom tags."""
        skill, _, mock_metrics = skill_with_mocks

        skill.emit_metric(
            "test_metric",
            1.0,
            tags={"custom_tag": "value", "another": "tag"},
        )

        # Verify tags include both custom tags and correlation_id
        call_kwargs = mock_metrics.set_gauge.call_args[1]
        actual_tags = call_kwargs.get("tags", {})
        assert actual_tags["correlation_id"] == "test-metrics-id"
        assert actual_tags["custom_tag"] == "value"
        assert actual_tags["another"] == "tag"

    def test_emit_metric_default_value(self, skill_with_mocks):
        """Test emit_metric uses default value of 1.0."""
        skill, _, mock_metrics = skill_with_mocks

        skill.emit_metric("test_count")

        mock_metrics.increment_counter.assert_called_once_with(
            "test_count",
            1.0,
            tags={"correlation_id": "test-metrics-id"},
        )

    def test_emit_metric_default_tags(self, skill_with_mocks):
        """Test emit_metric works without tags."""
        skill, _, mock_metrics = skill_with_mocks

        skill.emit_metric("test_metric", 1.0)

        # Verify only correlation_id is in tags
        call_kwargs = mock_metrics.set_gauge.call_args[1]
        actual_tags = call_kwargs.get("tags", {})
        assert actual_tags == {"correlation_id": "test-metrics-id"}


class TestBaseSkillExecute:
    """Tests for skill execution."""

    @pytest.fixture
    def skill_with_mocks(self):
        """Create skill with mocked dependencies."""
        with patch("src.skills.base_skill.AuditLogger") as mock_logger_class:
            with patch("src.skills.base_skill.get_metrics_collector") as mock_get_metrics:
                mock_logger = MagicMock()
                mock_logger_class.return_value = mock_logger
                mock_metrics = MagicMock()
                mock_get_metrics.return_value = mock_metrics

                skill = ConcreteSkill()
                yield skill, mock_logger, mock_metrics

    def test_execute_returns_dict(self, skill_with_mocks):
        """Test execute returns dict with status."""
        skill, _, _ = skill_with_mocks

        result = skill.execute()

        assert isinstance(result, dict)
        assert result["status"] == "executed"

    def test_execute_dry_run_false(self, skill_with_mocks):
        """Test execute returns dry_run=False when not in dry run mode."""
        skill, _, _ = skill_with_mocks

        result = skill.execute()

        assert result["dry_run"] is False

    def test_execute_dry_run_true(self, skill_with_mocks):
        """Test execute returns dry_run=True when in dry run mode."""
        skill, _, _ = skill_with_mocks
        skill.dry_run = True

        result = skill.execute()

        assert result["dry_run"] is True


class TestBaseSkillAbstract:
    """Tests for abstract behavior of BaseSkill."""

    def test_cannot_instantiate_base_skill_directly(self):
        """Test BaseSkill cannot be instantiated directly."""
        with pytest.raises(TypeError, match="abstract method"):
            with patch("src.skills.base_skill.AuditLogger"):
                with patch("src.skills.base_skill.get_metrics_collector"):
                    BaseSkill()

    def test_must_implement_execute_method(self):
        """Test subclasses must implement execute method."""

        class IncompleteSkill(BaseSkill):
            pass

        with pytest.raises(TypeError, match="abstract method"):
            with patch("src.skills.base_skill.AuditLogger"):
                with patch("src.skills.base_skill.get_metrics_collector"):
                    IncompleteSkill()


class TestBaseSkillEdgeCases:
    """Edge case tests for BaseSkill."""

    def test_correlation_id_uuid_format(self):
        """Test auto-generated correlation_id is valid UUID format."""
        with patch("src.skills.base_skill.AuditLogger"):
            with patch("src.skills.base_skill.get_metrics_collector"):
                skill = ConcreteSkill()

                # Should not raise ValueError
                parsed = uuid.UUID(skill.correlation_id)
                assert parsed.version == 4  # UUID4

    def test_multiple_instances_have_unique_correlation_ids(self):
        """Test multiple instances get unique correlation IDs."""
        with patch("src.skills.base_skill.AuditLogger"):
            with patch("src.skills.base_skill.get_metrics_collector"):
                skill1 = ConcreteSkill()
                skill2 = ConcreteSkill()

                assert skill1.correlation_id != skill2.correlation_id

    def test_log_action_with_empty_details(self, caplog):
        """Test log_action works with empty details dict."""
        with patch("src.skills.base_skill.AuditLogger") as mock_logger_class:
            with patch("src.skills.base_skill.get_metrics_collector"):
                mock_logger = MagicMock()
                mock_logger_class.return_value = mock_logger

                skill = ConcreteSkill()

                skill.log_action("INFO", "action", {})

                mock_logger.log.assert_called_once()
                call_args = mock_logger.log.call_args
                assert call_args[0][2] == {}

    def test_emit_metric_with_none_tags_uses_empty_dict(self):
        """Test emit_metric handles None tags gracefully."""
        with patch("src.skills.base_skill.AuditLogger"):
            with patch("src.skills.base_skill.get_metrics_collector") as mock_get_metrics:
                mock_metrics = MagicMock()
                mock_get_metrics.return_value = mock_metrics

                skill = ConcreteSkill(correlation_id="test-id")

                skill.emit_metric("test_metric", 1.0, tags=None)

                # Should not raise, should use empty dict plus correlation_id
                call_kwargs = mock_metrics.set_gauge.call_args[1]
                actual_tags = call_kwargs.get("tags", {})
                assert actual_tags == {"correlation_id": "test-id"}
