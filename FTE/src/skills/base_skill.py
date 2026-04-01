"""Base Skill abstract base class for all agent skills."""

import os
import sys
import uuid
from abc import ABC, abstractmethod
from typing import Any

from ..audit_logger import AuditLogger
from ..metrics.collector import get_metrics_collector


class BaseSkill(ABC):
    """Abstract base class for all agent skills.

    Provides common functionality:
    - DEV_MODE validation
    - --dry-run support
    - correlation_id logging
    - metrics emission

    Attributes:
        dry_run: If True, log actions without executing
        correlation_id: Unique ID for tracking action across logs
        logger: AuditLogger instance
        metrics: MetricsCollector instance
    """

    def __init__(
        self,
        dry_run: bool = False,
        correlation_id: str | None = None,
    ) -> None:
        """Initialize base skill.

        Args:
            dry_run: If True, log actions without executing. Defaults to False.
            correlation_id: Unique ID for tracking. Auto-generated if not provided.
        """
        self.dry_run = dry_run
        self.correlation_id = correlation_id or str(uuid.uuid4())
        self.logger = AuditLogger(component=self.__class__.__name__)
        self.metrics = get_metrics_collector()

    def validate_dev_mode(self) -> bool:
        """Validate DEV_MODE is set to 'true'.

        Returns:
            True if DEV_MODE is valid

        Raises:
            SystemExit: If DEV_MODE is not set to 'true'
        """
        dev_mode = os.getenv("DEV_MODE", "false")
        if dev_mode != "true":
            self.logger.log(
                "ERROR",
                "dev_mode_not_set",
                {"current_value": dev_mode},
                correlation_id=self.correlation_id,
            )
            print(
                f"ERROR: DEV_MODE must be set to 'true' to run. "
                f"Current value: '{dev_mode}'. "
                f"Set DEV_MODE=true in your .env file or environment.",
                file=sys.stderr,
            )
            sys.exit(1)
        return True

    def log_action(
        self,
        level: str,
        action: str,
        details: dict[str, Any],
    ) -> None:
        """Log an action with correlation_id.

        Args:
            level: Log level (INFO, WARNING, ERROR, etc.)
            action: Action name
            details: Additional context
        """
        self.logger.log(
            level,
            action,
            details,
            correlation_id=self.correlation_id,
        )

    def emit_metric(
        self,
        metric_name: str,
        value: float = 1.0,
        tags: dict[str, str] | None = None,
    ) -> None:
        """Emit a metric with optional tags.

        Args:
            metric_name: Name of the metric
            value: Metric value
            tags: Optional tags for filtering
        """
        updated_tags = tags or {}
        updated_tags["correlation_id"] = self.correlation_id

        if metric_name.endswith("_duration"):
            self.metrics.record_histogram(metric_name, value, tags=updated_tags)
        elif metric_name.endswith("_count") or metric_name.endswith("_errors"):
            self.metrics.increment_counter(metric_name, value, tags=updated_tags)
        else:
            self.metrics.set_gauge(metric_name, value, tags=updated_tags)

    @abstractmethod
    def execute(self, *args: Any, **kwargs: Any) -> Any:
        """Execute the skill.

        Args:
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            Result of skill execution

        Raises:
            Exception: Skill-specific exceptions
        """
        pass
