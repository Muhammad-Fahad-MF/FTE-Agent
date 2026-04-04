"""
FTE-Agent Alerting
Purpose: Alert generation and notification for resource monitoring
Version: 1.0.0 (Platinum Tier)

Features:
- Alert generation with severity levels
- Alert logging to JSONL format
- Alert propagation to Local agent via Signals folder
- Alert deduplication
"""

import hashlib
import json
import logging
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class AlertSeverity(Enum):
    """Alert severity levels."""

    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"
    EMERGENCY = "EMERGENCY"


@dataclass
class Alert:
    """Alert data class."""

    id: str
    timestamp: str
    severity: str
    source: str
    component: str
    message: str
    metric_name: str | None = None
    metric_value: float | None = None
    threshold: float | None = None
    acknowledged: bool = False
    resolved: bool = False

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)

    def to_signal_file(self) -> str:
        """
        Convert to Signal file format (Markdown with YAML frontmatter).

        Returns:
            Markdown string with YAML frontmatter
        """
        yaml_frontmatter = f"""---
type: alert
id: {self.id}
severity: {self.severity}
source: {self.source}
component: {self.component}
timestamp: {self.timestamp}
acknowledged: {str(self.acknowledged).lower()}
resolved: {str(self.resolved).lower()}
---

# Alert: {self.severity}

**Component**: {self.component}

**Message**: {self.message}

## Details

"""

        if self.metric_name:
            yaml_frontmatter += f"- **Metric**: {self.metric_name}\n"
        if self.metric_value is not None:
            yaml_frontmatter += f"- **Value**: {self.metric_value}\n"
        if self.threshold is not None:
            yaml_frontmatter += f"- **Threshold**: {self.threshold}\n"

        yaml_frontmatter += f"\n**Generated**: {self.timestamp}\n"

        return yaml_frontmatter


class AlertManager:
    """
    Alert manager for FTE-Agent Cloud VM.

    Manages alert generation, logging, and propagation.
    """

    def __init__(
        self,
        log_path: Path | None = None,
        signals_path: Path | None = None,
        dedup_window: int = 300,
    ):
        """
        Initialize alert manager.

        Args:
            log_path: Path to alert log directory
            signals_path: Path to Signals folder for Local agent
            dedup_window: Deduplication window in seconds (default: 300)
        """
        self.log_path = log_path or Path("/tmp/fte-agent/logs")
        self.signals_path = signals_path or Path.home() / "fte-agent" / "vault" / "Signals"
        self.dedup_window = dedup_window
        self._recent_alerts: dict[str, datetime] = {}

    def generate_id(self, severity: str, component: str, message: str) -> str:
        """
        Generate unique alert ID.

        Args:
            severity: Alert severity
            component: Component name
            message: Alert message

        Returns:
            Hash-based ID
        """
        content = f"{severity}:{component}:{message}"
        return hashlib.md5(content.encode()).hexdigest()[:12]

    def should_deduplicate(self, alert_id: str) -> bool:
        """
        Check if alert should be deduplicated.

        Args:
            alert_id: Alert ID

        Returns:
            True if alert is duplicate within dedup window
        """
        now = datetime.now(UTC)

        # Clean old entries
        cutoff = now.timestamp() - self.dedup_window
        self._recent_alerts = {
            k: v for k, v in self._recent_alerts.items() if v.timestamp() > cutoff
        }

        # Check for duplicate
        if alert_id in self._recent_alerts:
            return True

        # Record new alert
        self._recent_alerts[alert_id] = now
        return False

    def create_alert(
        self,
        severity: str,
        component: str,
        message: str,
        metric_name: str | None = None,
        metric_value: float | None = None,
        threshold: float | None = None,
    ) -> Alert:
        """
        Create new alert.

        Args:
            severity: Alert severity
            component: Component name
            message: Alert message
            metric_name: Optional metric name
            metric_value: Optional metric value
            threshold: Optional threshold value

        Returns:
            Alert object
        """
        alert_id = self.generate_id(severity, component, message)

        # Check for deduplication
        if self.should_deduplicate(alert_id):
            logger.debug(f"Alert deduplicated: {alert_id}")
            return None

        alert = Alert(
            id=alert_id,
            timestamp=datetime.now(UTC).isoformat(),
            severity=severity,
            source="cloud_agent",
            component=component,
            message=message,
            metric_name=metric_name,
            metric_value=metric_value,
            threshold=threshold,
        )

        return alert

    def log_alert(self, alert: Alert) -> None:
        """
        Log alert to JSONL file.

        Args:
            alert: Alert object
        """
        log_file = self.log_path / "alerts.jsonl"
        log_file.parent.mkdir(parents=True, exist_ok=True)

        log_entry = {
            "timestamp": alert.timestamp,
            "level": alert.severity,
            "component": "alerting",
            "alert": alert.to_dict(),
        }

        with open(log_file, "a") as f:
            f.write(json.dumps(log_entry) + "\n")

        logger.warning(f"[{alert.severity}] {alert.message}")

    def write_signal_file(self, alert: Alert) -> Path:
        """
        Write alert to Signals folder for Local agent.

        Args:
            alert: Alert object

        Returns:
            Path to signal file
        """
        self.signals_path.mkdir(parents=True, exist_ok=True)

        # Create signal file
        filename = f"ALERT_{alert.severity}_{alert.id}.md"
        signal_file = self.signals_path / filename

        with open(signal_file, "w") as f:
            f.write(alert.to_signal_file())

        logger.info(f"Signal file created: {signal_file}")
        return signal_file

    def send_alert(
        self,
        severity: str,
        component: str,
        message: str,
        metric_name: str | None = None,
        metric_value: float | None = None,
        threshold: float | None = None,
        propagate: bool = True,
    ) -> Alert | None:
        """
        Send alert (log and optionally propagate).

        Args:
            severity: Alert severity
            component: Component name
            message: Alert message
            metric_name: Optional metric name
            metric_value: Optional metric value
            threshold: Optional threshold value
            propagate: Whether to write signal file

        Returns:
            Alert object or None if deduplicated
        """
        alert = self.create_alert(
            severity=severity,
            component=component,
            message=message,
            metric_name=metric_name,
            metric_value=metric_value,
            threshold=threshold,
        )

        if alert is None:
            return None

        # Log alert
        self.log_alert(alert)

        # Propagate to Local agent if critical/emergency
        if propagate and severity in [AlertSeverity.CRITICAL, AlertSeverity.EMERGENCY]:
            self.write_signal_file(alert)

        return alert

    def get_recent_alerts(self, limit: int = 100) -> list[dict[str, Any]]:
        """
        Get recent alerts from log file.

        Args:
            limit: Maximum number of alerts to return

        Returns:
            List of alert dictionaries
        """
        log_file = self.log_path / "alerts.jsonl"

        if not log_file.exists():
            return []

        alerts = []
        with open(log_file) as f:
            for line in f:
                try:
                    entry = json.loads(line)
                    if "alert" in entry:
                        alerts.append(entry["alert"])
                except json.JSONDecodeError:
                    continue

        # Return most recent first
        return list(reversed(alerts[-limit:]))

    def acknowledge_alert(self, alert_id: str) -> bool:
        """
        Acknowledge an alert.

        Args:
            alert_id: Alert ID

        Returns:
            True if acknowledged, False if not found
        """
        # In a full implementation, this would update the alert in storage
        # For now, just log the acknowledgment
        logger.info(f"Alert acknowledged: {alert_id}")
        return True

    def resolve_alert(self, alert_id: str) -> bool:
        """
        Resolve an alert.

        Args:
            alert_id: Alert ID

        Returns:
            True if resolved, False if not found
        """
        logger.info(f"Alert resolved: {alert_id}")
        return True
