"""
Alerting Service for FTE Agent.

Monitors system health and triggers alerts based on conditions:
- Circuit breaker open (immediate alert)
- DLQ size > 10 (threshold alert)
- Watcher restart > 3/hour (pattern alert)
- Approval queue > 20 (backlog alert)

Alert methods:
- File in /Vault/Needs_Action/
- Dashboard.md update
- Optional email notification

Usage:
    from src.services.alerting import AlertingService
    
    alerting = AlertingService(vault_path="./vault")
    
    # Check all alert conditions
    alerts = alerting.check_alert_conditions()
    
    # Trigger manual alert
    alerting.trigger_alert(
        alert_type="custom",
        message="Custom alert message",
        severity="WARNING"
    )
"""

import json
import logging
import smtplib
import threading
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from pathlib import Path
from typing import Any, Callable, Optional

from src.audit_logger import AuditLogger
from src.utils.circuit_breaker import CircuitBreaker, get_circuit_breaker
from src.utils.dead_letter_queue import DeadLetterQueue

logger = logging.getLogger(__name__)


class AlertingService:
    """
    Alerting service for FTE Agent.

    Monitors system health and triggers alerts based on configurable conditions.

    Attributes:
        vault_path: Path to vault directory
        dlq_threshold: DLQ size threshold for alert (default: 10)
        restart_threshold: Watcher restart threshold per hour (default: 3)
        approval_threshold: Approval queue threshold (default: 20)
    """

    def __init__(
        self,
        vault_path: str,
        dlq_threshold: int = 10,
        restart_threshold: int = 3,
        approval_threshold: int = 20,
        email_notifications: bool = False,
        email_config: Optional[dict[str, Any]] = None,
    ):
        """
        Initialize alerting service.

        Args:
            vault_path: Path to vault directory
            dlq_threshold: DLQ size threshold for alert (default: 10)
            restart_threshold: Watcher restart threshold per hour (default: 3)
            approval_threshold: Approval queue threshold (default: 20)
            email_notifications: Enable email notifications (default: False)
            email_config: Email configuration dict with keys:
                - smtp_host: SMTP server hostname
                - smtp_port: SMTP server port
                - username: SMTP username
                - password: SMTP password
                - from_addr: From email address
                - to_addrs: List of recipient email addresses
        """
        self.vault_path = Path(vault_path).resolve()
        self.dlq_threshold = dlq_threshold
        self.restart_threshold = restart_threshold
        self.approval_threshold = approval_threshold
        self.email_notifications = email_notifications
        self.email_config = email_config or {}

        self.logger = AuditLogger(component="alerting")

        # Alert state tracking
        self._alert_cooldowns: dict[str, datetime] = {}
        self._alert_cooldown_seconds = 300  # 5 minutes between duplicate alerts

        # Alert callbacks
        self._alert_callbacks: list[Callable[[str, str, str], None]] = []

        # Paths
        self.needs_action_dir = self.vault_path / "Needs_Action"
        self.dashboard_path = self.vault_path / "Dashboard.md"

        # Ensure directories exist
        self.needs_action_dir.mkdir(parents=True, exist_ok=True)

        self.logger.info(
            "alerting_service_initialized",
            {
                "vault_path": str(self.vault_path),
                "dlq_threshold": self.dlq_threshold,
                "restart_threshold": self.restart_threshold,
                "approval_threshold": self.approval_threshold,
            },
        )

    def register_alert_callback(self, callback: Callable[[str, str, str], None]) -> None:
        """
        Register a callback for alert notifications.

        Args:
            callback: Function(alert_type, message, severity) to receive alerts
        """
        self._alert_callbacks.append(callback)

    def _emit_alert(self, alert_type: str, message: str, severity: str) -> None:
        """Emit alert to registered callbacks."""
        for callback in self._alert_callbacks:
            try:
                callback(alert_type, message, severity)
            except Exception as e:
                logger.debug(f"Alert callback failed: {e}")

    def check_alert_conditions(self) -> list[dict[str, Any]]:
        """
        Check all alert conditions and return triggered alerts.

        Returns:
            List of triggered alerts with fields:
            - type: Alert type (circuit_breaker_open, dlq_size, watcher_restart, approval_queue)
            - severity: Alert severity (CRITICAL, WARNING, INFO)
            - message: Alert message
            - details: Additional alert details

        Example:
            >>> alerting = AlertingService(vault_path="./vault")
            >>> alerts = alerting.check_alert_conditions()
            >>> len(alerts)
            2
            >>> alerts[0]["type"]
            'circuit_breaker_open'
        """
        alerts = []

        # Check circuit breaker status
        cb_alerts = self._check_circuit_breakers()
        alerts.extend(cb_alerts)

        # Check DLQ size
        dlq_alert = self._check_dlq_size()
        if dlq_alert:
            alerts.append(dlq_alert)

        # Check watcher restart rate
        restart_alert = self._check_watcher_restarts()
        if restart_alert:
            alerts.append(restart_alert)

        # Check approval queue backlog
        approval_alert = self._check_approval_queue()
        if approval_alert:
            alerts.append(approval_alert)

        # Trigger alerts
        for alert in alerts:
            self._trigger_alert_internal(
                alert_type=alert["type"],
                message=alert["message"],
                severity=alert["severity"],
                details=alert.get("details", {}),
            )

        if alerts:
            self.logger.log(
                "INFO",
                "alert_conditions_checked",
                {"alerts_triggered": len(alerts)},
            )

        return alerts

    def _check_circuit_breakers(self) -> list[dict[str, Any]]:
        """Check circuit breaker status."""
        alerts = []

        try:
            # Get all circuit breakers
            services = ["gmail", "whatsapp", "odoo", "linkedin", "twitter", "facebook", "instagram"]

            for service in services:
                try:
                    cb = get_circuit_breaker(service)
                    state = cb.get_state()

                    if state == "open":
                        alerts.append(
                            {
                                "type": "circuit_breaker_open",
                                "severity": "CRITICAL",
                                "message": f"Circuit breaker OPEN for {service}",
                                "details": {
                                    "service": service,
                                    "state": state,
                                    "failure_count": cb.failure_count,
                                },
                            }
                        )
                except Exception:
                    # Circuit breaker not initialized for this service
                    pass

        except Exception as e:
            logger.debug(f"Circuit breaker check failed: {e}")

        return alerts

    def _check_dlq_size(self) -> Optional[dict[str, Any]]:
        """Check DLQ size threshold."""
        try:
            dlq = DeadLetterQueue()
            stats = dlq.get_dlq_stats()
            total_failed = stats.get("total_failed", 0)

            if total_failed > self.dlq_threshold:
                return {
                    "type": "dlq_size",
                    "severity": "WARNING",
                    "message": f"DLQ size ({total_failed}) exceeds threshold ({self.dlq_threshold})",
                    "details": {
                        "current_size": total_failed,
                        "threshold": self.dlq_threshold,
                        "active_failures": stats.get("active_failures", 0),
                    },
                }

        except Exception as e:
            logger.debug(f"DLQ size check failed: {e}")

        return None

    def _check_watcher_restarts(self) -> Optional[dict[str, Any]]:
        """Check watcher restart rate."""
        try:
            # Import process manager to check restart counts
            from src.process_manager import ProcessManager

            # This would need access to running process manager instance
            # For now, we'll check a state file if it exists
            restart_state_file = self.vault_path / "State" / "watcher_restarts.json"

            if restart_state_file.exists():
                with open(restart_state_file, "r") as f:
                    restart_data = json.load(f)

                now = datetime.now()
                one_hour_ago = now - timedelta(hours=1)

                for watcher_name, timestamps in restart_data.items():
                    # Count restarts in last hour
                    recent_restarts = [
                        ts for ts in timestamps
                        if datetime.fromisoformat(ts) > one_hour_ago
                    ]

                    if len(recent_restarts) > self.restart_threshold:
                        return {
                            "type": "watcher_restart",
                            "severity": "WARNING",
                            "message": f"Watcher '{watcher_name}' restarted {len(recent_restarts)} times in last hour",
                            "details": {
                                "watcher": watcher_name,
                                "restart_count": len(recent_restarts),
                                "threshold": self.restart_threshold,
                            },
                        }

        except Exception as e:
            logger.debug(f"Watcher restart check failed: {e}")

        return None

    def _check_approval_queue(self) -> Optional[dict[str, Any]]:
        """Check approval queue backlog."""
        try:
            pending_approval_dir = self.vault_path / "Pending_Approval"

            if pending_approval_dir.exists():
                pending_count = len(list(pending_approval_dir.glob("*.md")))

                if pending_count > self.approval_threshold:
                    return {
                        "type": "approval_queue",
                        "severity": "WARNING",
                        "message": f"Approval queue backlog ({pending_count}) exceeds threshold ({self.approval_threshold})",
                        "details": {
                            "pending_count": pending_count,
                            "threshold": self.approval_threshold,
                        },
                    }

        except Exception as e:
            logger.debug(f"Approval queue check failed: {e}")

        return None

    def _trigger_alert_internal(
        self,
        alert_type: str,
        message: str,
        severity: str,
        details: Optional[dict[str, Any]] = None,
    ) -> None:
        """
        Internal alert triggering with cooldown logic.

        Args:
            alert_type: Type of alert
            message: Alert message
            severity: Alert severity (INFO, WARNING, CRITICAL)
            details: Optional additional details
        """
        # Check cooldown
        cooldown_key = f"{alert_type}:{message}"
        if self._is_in_cooldown(cooldown_key):
            logger.debug(f"Alert in cooldown: {alert_type}")
            return

        # Set cooldown
        self._set_cooldown(cooldown_key)

        # Create alert file in Needs_Action
        self._create_alert_file(alert_type, message, severity, details)

        # Update Dashboard
        self._update_dashboard_alert(alert_type, message, severity)

        # Send email if enabled
        if self.email_notifications:
            self._send_email_alert(alert_type, message, severity, details)

        # Emit to callbacks
        self._emit_alert(alert_type, message, severity)

        # Log alert
        self.logger.log(
            "INFO" if severity == "INFO" else "WARNING" if severity == "WARNING" else "ERROR",
            "alert_triggered",
            {
                "type": alert_type,
                "severity": severity,
                "message": message,
            },
        )

    def trigger_alert(
        self,
        alert_type: str,
        message: str,
        severity: str = "WARNING",
        details: Optional[dict[str, Any]] = None,
    ) -> None:
        """
        Trigger a manual alert.

        Args:
            alert_type: Type of alert
            message: Alert message
            severity: Alert severity (INFO, WARNING, CRITICAL)
            details: Optional additional details

        Example:
            >>> alerting.trigger_alert(
            ...     alert_type="custom",
            ...     message="Manual alert message",
            ...     severity="WARNING"
            ... )
        """
        self._trigger_alert_internal(alert_type, message, severity, details)

    def _is_in_cooldown(self, alert_key: str) -> bool:
        """Check if alert is in cooldown period."""
        if alert_key not in self._alert_cooldowns:
            return False

        cooldown_end = self._alert_cooldowns[alert_key]
        return datetime.now() < cooldown_end

    def _set_cooldown(self, alert_key: str) -> None:
        """Set cooldown for alert."""
        self._alert_cooldowns[alert_key] = datetime.now() + timedelta(
            seconds=self._alert_cooldown_seconds
        )

    def _create_alert_file(
        self,
        alert_type: str,
        message: str,
        severity: str,
        details: Optional[dict[str, Any]] = None,
    ) -> Path:
        """Create alert file in Needs_Action directory."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        alert_id = f"ALERT_{alert_type}_{timestamp}"
        file_path = self.needs_action_dir / f"{alert_id}.md"

        content = f"""---
type: alert
alert_type: {alert_type}
severity: {severity}
created: {datetime.now().isoformat()}
status: pending
---

# Alert: {alert_type}

**Severity**: {severity}
**Created**: {datetime.now().isoformat()}

## Message

{message}

## Details

```json
{json.dumps(details or {}, indent=2)}
```

## Actions

- [ ] Review alert details
- [ ] Take corrective action
- [ ] Move to /Done/ when resolved

---

*Generated by FTE Agent Alerting Service*
"""

        file_path.write_text(content, encoding="utf-8")
        logger.info(f"Alert file created: {file_path}")
        return file_path

    def _update_dashboard_alert(
        self,
        alert_type: str,
        message: str,
        severity: str,
    ) -> None:
        """Update Dashboard.md with alert information."""
        try:
            timestamp = datetime.now().isoformat()
            alert_line = f"- **[{severity}]** {timestamp}: {alert_type} - {message}\n"

            if self.dashboard_path.exists():
                content = self.dashboard_path.read_text(encoding="utf-8")

                # Find or create alerts section
                if "## Alerts" in content:
                    # Insert after ## Alerts header
                    content = content.replace("## Alerts\n", f"## Alerts\n{alert_line}")
                else:
                    # Add alerts section
                    content += f"\n## Alerts\n{alert_line}"

            else:
                # Create new dashboard
                content = f"""# FTE Agent Dashboard

## Alerts
{alert_line}
"""

            self.dashboard_path.write_text(content, encoding="utf-8")
            logger.debug("Dashboard updated with alert")

        except Exception as e:
            logger.error(f"Failed to update dashboard with alert: {e}")

    def _send_email_alert(
        self,
        alert_type: str,
        message: str,
        severity: str,
        details: Optional[dict[str, Any]] = None,
    ) -> bool:
        """Send email alert notification."""
        if not self.email_notifications or not self.email_config:
            return False

        try:
            smtp_host = self.email_config.get("smtp_host", "smtp.gmail.com")
            smtp_port = self.email_config.get("smtp_port", 587)
            username = self.email_config.get("username")
            password = self.email_config.get("password")
            from_addr = self.email_config.get("from_addr", username)
            to_addrs = self.email_config.get("to_addrs", [])

            if not username or not password or not to_addrs:
                logger.warning("Email configuration incomplete, skipping email alert")
                return False

            # Create email message
            subject = f"[FTE Agent Alert] {severity}: {alert_type}"
            body = f"""
Alert Type: {alert_type}
Severity: {severity}
Time: {datetime.now().isoformat()}

Message:
{message}

Details:
{json.dumps(details or {}, indent=2)}

---
FTE Agent Alerting Service
"""

            msg = MIMEText(body)
            msg["Subject"] = subject
            msg["From"] = from_addr
            msg["To"] = ", ".join(to_addrs)

            # Send email
            with smtplib.SMTP(smtp_host, smtp_port) as server:
                server.starttls()
                server.login(username, password)
                server.send_message(msg)

            logger.info(f"Email alert sent: {alert_type}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email alert: {e}")
            return False


# Global alerting service instance
_alerting_instance: Optional[AlertingService] = None


def get_alerting_service(
    vault_path: Optional[str] = None,
    dlq_threshold: int = 10,
    restart_threshold: int = 3,
    approval_threshold: int = 20,
) -> AlertingService:
    """
    Get or create global alerting service instance.

    Args:
        vault_path: Path to vault directory (default: ./vault)
        dlq_threshold: DLQ size threshold (default: 10)
        restart_threshold: Watcher restart threshold (default: 3)
        approval_threshold: Approval queue threshold (default: 20)

    Returns:
        AlertingService instance
    """
    global _alerting_instance
    if _alerting_instance is None:
        vault = vault_path or str(Path(__file__).parent.parent.parent / "vault")
        _alerting_instance = AlertingService(
            vault_path=vault,
            dlq_threshold=dlq_threshold,
            restart_threshold=restart_threshold,
            approval_threshold=approval_threshold,
        )
    return _alerting_instance


def check_alert_conditions() -> list[dict[str, Any]]:
    """
    Check all alert conditions.

    Returns:
        List of triggered alerts

    Example:
        >>> alerts = check_alert_conditions()
        >>> len(alerts)
        2
    """
    alerting = get_alerting_service()
    return alerting.check_alert_conditions()


def trigger_alert(
    alert_type: str,
    message: str,
    severity: str = "WARNING",
    details: Optional[dict[str, Any]] = None,
) -> None:
    """
    Trigger a manual alert.

    Args:
        alert_type: Type of alert
        message: Alert message
        severity: Alert severity (default: WARNING)
        details: Optional additional details

    Example:
        >>> trigger_alert("custom", "Manual alert", "WARNING")
    """
    alerting = get_alerting_service()
    alerting.trigger_alert(alert_type, message, severity, details)
