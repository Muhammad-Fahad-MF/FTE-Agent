"""Dashboard Service - Real-time system health monitoring.

This module provides utilities to update and maintain the Dashboard.md file
with real-time system health information.

Usage:
    from src.services.dashboard import DashboardService
    
    dashboard = DashboardService(vault_path="vault/")
    dashboard.update_system_status("running")
    dashboard.add_action("email_sent", "success", 0.5)
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from ..audit_logger import AuditLogger


class DashboardService:
    """Service for updating the FTE-Agent Dashboard.

    Maintains real-time system health information in Dashboard.md
    with single-writer rule compliance.

    Attributes:
        vault_path: Root path of the vault directory.
        dashboard_path: Path to Dashboard.md file.
        logger: Audit logger instance.
    """

    def __init__(
        self,
        vault_path: str,
        dry_run: bool = False,
    ) -> None:
        """Initialize dashboard service.

        Args:
            vault_path: Root path of the vault directory.
            dry_run: If True, log actions without writing files.
        """
        self.vault_path = Path(vault_path).resolve()
        self.dashboard_path = self.vault_path / "Dashboard.md"
        self.dry_run = dry_run
        self.logger = AuditLogger(
            component="DashboardService",
            dry_run=dry_run,
        )

        # State tracking
        self._system_status = "stopped"
        self._orchestrator_start: Optional[datetime] = None
        self._recent_actions: list[dict[str, Any]] = []
        self._max_recent_actions = 10

        # Health indicators
        self._watchers_health: dict[str, dict[str, Any]] = {
            "gmail": {"status": "unknown", "last_check": None, "errors_24h": 0},
            "whatsapp": {"status": "unknown", "last_check": None, "errors_24h": 0},
            "filesystem": {"status": "unknown", "last_check": None, "errors_24h": 0},
        }

        self._mcp_health: dict[str, dict[str, Any]] = {
            "email": {"status": "unknown", "rate_limit": "N/A", "errors_24h": 0},
            "whatsapp": {"status": "unknown", "rate_limit": "N/A", "errors_24h": 0},
            "social": {"status": "unknown", "rate_limit": "N/A", "errors_24h": 0},
            "odoo": {"status": "unknown", "rate_limit": "N/A", "errors_24h": 0},
        }

        self._circuit_breakers: dict[str, dict[str, Any]] = {
            "gmail": {"state": "closed", "failures": 0, "last_failure": None},
            "whatsapp": {"state": "closed", "failures": 0, "last_failure": None},
            "odoo": {"state": "closed", "failures": 0, "last_failure": None},
            "social": {"state": "closed", "failures": 0, "last_failure": None},
        }

        # Alerts
        self._alerts: list[str] = []

        # Metrics
        self._metrics_24h: dict[str, int] = {
            "actions_processed": 0,
            "approvals_requested": 0,
            "approvals_approved": 0,
            "approvals_rejected": 0,
            "errors": 0,
            "warnings": 0,
        }

        self.logger.info(
            "dashboard_service_initialized",
            {"vault_path": str(self.vault_path)},
        )

    def _get_template(self) -> str:
        """Get Dashboard.md template.

        Returns:
            Template string with placeholders.
        """
        return """# FTE-Agent Dashboard

**Last Updated**: {{ last_updated }}
**System Status**: {{ system_status }}
**Uptime**: {{ uptime }}

---

## 🖥️ System Status

| Component | Status | Details |
|-----------|--------|---------|
| **Orchestrator** | {{ orchestrator_status }} | Running since {{ orchestrator_start }} |
| **Gmail Watcher** | {{ gmail_watcher_status }} | Last check: {{ gmail_last_check }} |
| **WhatsApp Watcher** | {{ whatsapp_watcher_status }} | Last check: {{ whatsapp_last_check }} |
| **FileSystem Watcher** | {{ filesystem_watcher_status }} | Last check: {{ filesystem_last_check }} |
| **Approval Handler** | {{ approval_handler_status }} | Pending: {{ pending_approvals }} |
| **Circuit Breakers** | {{ circuit_breaker_status }} | All systems nominal |

---

## 📋 Pending Approvals

**Count**: {{ pending_approvals_count }}

{{ pending_approvals_list }}

**Link**: [`/Vault/Pending_Approval/`](Pending_Approval/)

---

## 📊 Recent Actions (Last 10)

| Timestamp | Type | Action | Result | Duration |
|-----------|------|--------|--------|----------|
{{ recent_actions }}

---

## 🏥 Health Indicators

### Watchers

| Watcher | Status | Interval | Last Check | Errors (24h) |
|---------|--------|----------|------------|--------------|
| Gmail | {{ gmail_health }} | 2 min | {{ gmail_last_check }} | {{ gmail_errors }} |
| WhatsApp | {{ whatsapp_health }} | 30 sec | {{ whatsapp_last_check }} | {{ whatsapp_errors }} |
| FileSystem | {{ filesystem_health }} | 60 sec | {{ filesystem_last_check }} | {{ filesystem_errors }} |

### MCP Servers

| MCP Server | Status | Rate Limit | Errors (24h) |
|------------|--------|------------|--------------|
| EmailMCP | {{ email_mcp_status }} | {{ email_rate_limit }} | {{ email_mcp_errors }} |
| WhatsAppMCP | {{ whatsapp_mcp_status }} | N/A | {{ whatsapp_mcp_errors }} |
| SocialMCP | {{ social_mcp_status }} | {{ social_rate_limit }} | {{ social_mcp_errors }} |
| OdooMCP | {{ odoo_mcp_status }} | {{ odoo_rate_limit }} | {{ odoo_mcp_errors }} |

### Storage

| Path | Size | Files | Status |
|------|------|-------|--------|
| `/Vault/Needs_Action/` | {{ needs_action_size }} | {{ needs_action_count }} | {{ needs_action_status }} |
| `/Vault/Pending_Approval/` | {{ pending_approval_size }} | {{ pending_approval_count }} | {{ pending_approval_status }} |
| `/Vault/Approved/` | {{ approved_size }} | {{ approved_count }} | {{ approved_status }} |
| `/Vault/Logs/` | {{ logs_size }} | {{ logs_count }} | {{ logs_status }} |

### Circuit Breakers

| Service | State | Failures | Last Failure |
|---------|-------|----------|--------------|
| Gmail API | {{ gmail_cb_state }} | {{ gmail_cb_failures }} | {{ gmail_cb_last_failure }} |
| WhatsApp | {{ whatsapp_cb_state }} | {{ whatsapp_cb_failures }} | {{ whatsapp_cb_last_failure }} |
| Odoo API | {{ odoo_cb_state }} | {{ odoo_cb_failures }} | {{ odoo_cb_last_failure }} |
| Social Media | {{ social_cb_state }} | {{ social_cb_failures }} | {{ social_cb_last_failure }} |

---

## ⚠️ Alerts

{{ alerts_section }}

---

## 📈 Metrics (Last 24 Hours)

| Metric | Value |
|--------|-------|
| Actions Processed | {{ actions_processed_24h }} |
| Approvals Requested | {{ approvals_requested_24h }} |
| Approvals Approved | {{ approvals_approved_24h }} |
| Approvals Rejected | {{ approvals_rejected_24h }} |
| Errors | {{ errors_24h }} |
| Warnings | {{ warnings_24h }} |

---

## 🛑 Controls

- **Stop All**: Create `/Vault/STOP` file to halt all operations
- **Restart**: Delete `/Vault/STOP` file and restart services
- **Dry Run Mode**: {{ dry_run_status }}

---

## 📝 Notes

{{ notes_section }}

---

**Dashboard Version**: 1.0.0 (Gold Tier)
**Generated By**: FTE-Agent Orchestrator
"""

    def _calculate_uptime(self) -> str:
        """Calculate system uptime.

        Returns:
            Human-readable uptime string.
        """
        if not self._orchestrator_start:
            return "N/A"

        delta = datetime.now() - self._orchestrator_start
        days = delta.days
        hours, remainder = divmod(int(delta.seconds), 3600)
        minutes, seconds = divmod(remainder, 60)

        if days > 0:
            return f"{days}d {hours}h {minutes}m"
        elif hours > 0:
            return f"{hours}h {minutes}m {seconds}s"
        elif minutes > 0:
            return f"{minutes}m {seconds}s"
        else:
            return f"{seconds}s"

    def _format_recent_actions(self) -> str:
        """Format recent actions as markdown table rows.

        Returns:
            Markdown table rows string.
        """
        if not self._recent_actions:
            return "| - | - | - | - | - |"

        rows = []
        for action in self._recent_actions:
            timestamp = action.get("timestamp", "-")
            action_type = action.get("type", "-")
            action_name = action.get("action", "-")
            result = action.get("result", "-")
            duration = f"{action.get('duration', 0):.2f}s"

            rows.append(
                f"| {timestamp} | {action_type} | {action_name} | {result} | {duration} |"
            )

        return "\n".join(rows)

    def _format_alerts(self) -> str:
        """Format alerts as markdown list.

        Returns:
            Markdown alerts string.
        """
        if not self._alerts:
            return "No active alerts. All systems operational."

        alert_lines = []
        for alert in self._alerts:
            alert_lines.append(f"- ⚠️ {alert}")

        return "\n".join(alert_lines)

    def _get_storage_stats(self, folder: str) -> tuple[str, int, str]:
        """Get storage statistics for a folder.

        Args:
            folder: Folder name.

        Returns:
            Tuple of (size, file_count, status).
        """
        folder_path = self.vault_path / folder

        if not folder_path.exists():
            return "0 KB", 0, "⚠️ Not found"

        try:
            files = list(folder_path.glob("*"))
            file_count = len([f for f in files if f.is_file()])

            # Calculate total size
            total_size = sum(f.stat().st_size for f in files if f.is_file())

            # Format size
            if total_size < 1024:
                size_str = f"{total_size} B"
            elif total_size < 1024 * 1024:
                size_str = f"{total_size / 1024:.1f} KB"
            else:
                size_str = f"{total_size / (1024 * 1024):.1f} MB"

            # Determine status
            if file_count == 0:
                status = "✅ Empty"
            elif file_count < 100:
                status = "✅ Normal"
            elif file_count < 1000:
                status = "⚠️ Growing"
            else:
                status = "🔴 Large"

            return size_str, file_count, status

        except Exception:
            return "Error", 0, "⚠️ Error"

    def update_dashboard(self) -> None:
        """Update Dashboard.md with current state."""
        now = datetime.now()
        last_updated = now.isoformat()
        uptime = self._calculate_uptime()

        # Get storage stats
        needs_action_size, needs_action_count, needs_action_status = self._get_storage_stats(
            "Needs_Action"
        )
        pending_approval_size, pending_approval_count, pending_approval_status = (
            self._get_storage_stats("Pending_Approval")
        )
        approved_size, approved_count, approved_status = self._get_storage_stats("Approved")
        logs_size, logs_count, logs_status = self._get_storage_stats("Logs")

        # Build dashboard content
        content = (
            self._get_template()
            .replace("{{ last_updated }}", last_updated)
            .replace("{{ system_status }}", self._system_status.upper())
            .replace("{{ uptime }}", uptime)
            .replace("{{ orchestrator_status }}", "✅ Running" if self._system_status == "running" else "⏹️ Stopped")
            .replace("{{ orchestrator_start }}", self._orchestrator_start.isoformat() if self._orchestrator_start else "N/A")
            .replace("{{ gmail_watcher_status }}", self._watchers_health["gmail"]["status"])
            .replace("{{ gmail_last_check }}", str(self._watchers_health["gmail"].get("last_check", "N/A")))
            .replace("{{ whatsapp_watcher_status }}", self._watchers_health["whatsapp"]["status"])
            .replace("{{ whatsapp_last_check }}", str(self._watchers_health["whatsapp"].get("last_check", "N/A")))
            .replace("{{ filesystem_watcher_status }}", self._watchers_health["filesystem"]["status"])
            .replace("{{ filesystem_last_check }}", str(self._watchers_health["filesystem"].get("last_check", "N/A")))
            .replace("{{ pending_approvals }}", str(pending_approval_count))
            .replace("{{ pending_approvals_count }}", str(pending_approval_count))
            .replace("{{ pending_approvals_list }}", "No pending approvals." if pending_approval_count == 0 else f"See `/Vault/Pending_Approval/` ({pending_approval_count} files)")
            .replace("{{ recent_actions }}", self._format_recent_actions())
            .replace("{{ gmail_health }}", self._watchers_health["gmail"]["status"])
            .replace("{{ gmail_errors }}", str(self._watchers_health["gmail"]["errors_24h"]))
            .replace("{{ whatsapp_health }}", self._watchers_health["whatsapp"]["status"])
            .replace("{{ whatsapp_errors }}", str(self._watchers_health["whatsapp"]["errors_24h"]))
            .replace("{{ filesystem_health }}", self._watchers_health["filesystem"]["status"])
            .replace("{{ filesystem_errors }}", str(self._watchers_health["filesystem"]["errors_24h"]))
            .replace("{{ email_mcp_status }}", self._mcp_health["email"]["status"])
            .replace("{{ email_rate_limit }}", self._mcp_health["email"]["rate_limit"])
            .replace("{{ email_mcp_errors }}", str(self._mcp_health["email"]["errors_24h"]))
            .replace("{{ whatsapp_mcp_status }}", self._mcp_health["whatsapp"]["status"])
            .replace("{{ whatsapp_mcp_errors }}", str(self._mcp_health["whatsapp"]["errors_24h"]))
            .replace("{{ social_mcp_status }}", self._mcp_health["social"]["status"])
            .replace("{{ social_rate_limit }}", self._mcp_health["social"]["rate_limit"])
            .replace("{{ social_mcp_errors }}", str(self._mcp_health["social"]["errors_24h"]))
            .replace("{{ odoo_mcp_status }}", self._mcp_health["odoo"]["status"])
            .replace("{{ odoo_rate_limit }}", self._mcp_health["odoo"]["rate_limit"])
            .replace("{{ odoo_mcp_errors }}", str(self._mcp_health["odoo"]["errors_24h"]))
            .replace("{{ needs_action_size }}", needs_action_size)
            .replace("{{ needs_action_count }}", str(needs_action_count))
            .replace("{{ needs_action_status }}", needs_action_status)
            .replace("{{ pending_approval_size }}", pending_approval_size)
            .replace("{{ pending_approval_count }}", str(pending_approval_count))
            .replace("{{ pending_approval_status }}", pending_approval_status)
            .replace("{{ approved_size }}", approved_size)
            .replace("{{ approved_count }}", str(approved_count))
            .replace("{{ approved_status }}", approved_status)
            .replace("{{ logs_size }}", logs_size)
            .replace("{{ logs_count }}", str(logs_count))
            .replace("{{ logs_status }}", logs_status)
            .replace("{{ gmail_cb_state }}", self._circuit_breakers["gmail"]["state"])
            .replace("{{ gmail_cb_failures }}", str(self._circuit_breakers["gmail"]["failures"]))
            .replace("{{ gmail_cb_last_failure }}", str(self._circuit_breakers["gmail"].get("last_failure", "N/A")))
            .replace("{{ whatsapp_cb_state }}", self._circuit_breakers["whatsapp"]["state"])
            .replace("{{ whatsapp_cb_failures }}", str(self._circuit_breakers["whatsapp"]["failures"]))
            .replace("{{ whatsapp_cb_last_failure }}", str(self._circuit_breakers["whatsapp"].get("last_failure", "N/A")))
            .replace("{{ odoo_cb_state }}", self._circuit_breakers["odoo"]["state"])
            .replace("{{ odoo_cb_failures }}", str(self._circuit_breakers["odoo"]["failures"]))
            .replace("{{ odoo_cb_last_failure }}", str(self._circuit_breakers["odoo"].get("last_failure", "N/A")))
            .replace("{{ social_cb_state }}", self._circuit_breakers["social"]["state"])
            .replace("{{ social_cb_failures }}", str(self._circuit_breakers["social"]["failures"]))
            .replace("{{ social_cb_last_failure }}", str(self._circuit_breakers["social"].get("last_failure", "N/A")))
            .replace("{{ alerts_section }}", self._format_alerts())
            .replace("{{ actions_processed_24h }}", str(self._metrics_24h["actions_processed"]))
            .replace("{{ approvals_requested_24h }}", str(self._metrics_24h["approvals_requested"]))
            .replace("{{ approvals_approved_24h }}", str(self._metrics_24h["approvals_approved"]))
            .replace("{{ approvals_rejected_24h }}", str(self._metrics_24h["approvals_rejected"]))
            .replace("{{ errors_24h }}", str(self._metrics_24h["errors"]))
            .replace("{{ warnings_24h }}", str(self._metrics_24h["warnings"]))
            .replace("{{ dry_run_status }}", "🟡 Enabled" if self.dry_run else "🟢 Disabled")
            .replace("{{ notes_section }}", "System operating normally.")
        )

        if self.dry_run:
            self.logger.info(
                "dashboard_update_dry_run",
                {"dashboard_path": str(self.dashboard_path)},
            )
            return

        # Write dashboard
        try:
            self.dashboard_path.write_text(content, encoding="utf-8")
            self.logger.info(
                "dashboard_updated",
                {"dashboard_path": str(self.dashboard_path)},
            )
        except Exception as e:
            self.logger.error(
                "dashboard_update_failed",
                {"error": str(e)},
            )

    def set_system_status(self, status: str) -> None:
        """Set system status.

        Args:
            status: One of 'running', 'stopped', 'degraded'.
        """
        self._system_status = status
        if status == "running" and not self._orchestrator_start:
            self._orchestrator_start = datetime.now()
        self.update_dashboard()

    def add_action(
        self,
        action_type: str,
        action_name: str,
        result: str,
        duration: float,
    ) -> None:
        """Add action to recent actions list.

        Args:
            action_type: Type of action.
            action_name: Action name.
            result: Result (success/failure/pending).
            duration: Duration in seconds.
        """
        action = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "type": action_type,
            "action": action_name,
            "result": result,
            "duration": duration,
        }

        self._recent_actions.insert(0, action)

        # Trim to max size
        self._recent_actions = self._recent_actions[: self._max_recent_actions]

        # Update metrics
        self._metrics_24h["actions_processed"] += 1
        if result == "failure":
            self._metrics_24h["errors"] += 1
        elif result == "warning":
            self._metrics_24h["warnings"] += 1

        self.update_dashboard()

    def add_alert(self, alert: str) -> None:
        """Add alert to dashboard.

        Args:
            alert: Alert message.
        """
        self._alerts.append(alert)
        self.update_dashboard()

    def clear_alerts(self) -> None:
        """Clear all alerts."""
        self._alerts = []
        self.update_dashboard()

    def update_watcher_health(
        self,
        watcher: str,
        status: str,
        last_check: Optional[datetime] = None,
        errors_24h: int = 0,
    ) -> None:
        """Update watcher health status.

        Args:
            watcher: Watcher name (gmail, whatsapp, filesystem).
            status: Status string.
            last_check: Last check timestamp.
            errors_24h: Error count in last 24 hours.
        """
        if watcher in self._watchers_health:
            self._watchers_health[watcher]["status"] = status
            self._watchers_health[watcher]["last_check"] = (
                last_check.isoformat() if last_check else "N/A"
            )
            self._watchers_health[watcher]["errors_24h"] = errors_24h
            self.update_dashboard()

    def update_circuit_breaker(
        self,
        service: str,
        state: str,
        failures: int = 0,
        last_failure: Optional[datetime] = None,
    ) -> None:
        """Update circuit breaker status.

        Args:
            service: Service name.
            state: State (closed, open, half_open).
            failures: Failure count.
            last_failure: Last failure timestamp.
        """
        if service in self._circuit_breakers:
            self._circuit_breakers[service]["state"] = state
            self._circuit_breakers[service]["failures"] = failures
            self._circuit_breakers[service]["last_failure"] = (
                last_failure.isoformat() if last_failure else "N/A"
            )
            self.update_dashboard()


# Global instance
_dashboard_service: Optional[DashboardService] = None


def get_dashboard_service(
    vault_path: str,
    dry_run: bool = False,
) -> DashboardService:
    """Get or create global dashboard service.

    Args:
        vault_path: Root vault path.
        dry_run: Dry run mode.

    Returns:
        DashboardService instance.
    """
    global _dashboard_service
    if _dashboard_service is None:
        _dashboard_service = DashboardService(vault_path=vault_path, dry_run=dry_run)
    return _dashboard_service
