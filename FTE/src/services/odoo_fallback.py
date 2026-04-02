"""
Odoo Fallback Mechanism.

Handles Odoo unavailability with:
- Connection error detection
- Transaction logging to /Vault/Odoo_Fallback/
- Queue for later sync
- User alerting when fallback activated

Usage:
    from src.services.odoo_fallback import OdooFallbackManager
    
    fallback = OdooFallbackManager(vault_path="./vault")
    
    # Log transaction during fallback
    fallback.log_fallback_transaction(
        transaction_type="invoice",
        action="create",
        data={"partner_id": 1, "amount": 100.00},
        error="Connection timeout"
    )
    
    # Check if fallback mode is active
    if fallback.is_fallback_active():
        print("Odoo unavailable - using fallback mode")
    
    # Try to sync queued transactions
    fallback.sync_queued_transactions()
"""

import json
import logging
import threading
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Optional

import requests

from src.audit_logger import AuditLogger
from src.services.alerting import trigger_alert

logger = logging.getLogger(__name__)


class OdooFallbackError(Exception):
    """Base exception for Odoo fallback errors."""

    pass


class OdooFallbackManager:
    """
    Manages Odoo fallback mode when Odoo is unavailable.

    Features:
    - Detects Odoo unavailability
    - Logs transactions to markdown files
    - Queues transactions for later sync
    - Alerts user when fallback activated
    - Automatic retry on Odoo recovery

    Attributes:
        vault_path: Path to vault directory
        odoo_url: Odoo JSON-RPC endpoint URL
        db_name: Odoo database name
        uid: Odoo user ID
        password: Odoo password/API key
    """

    def __init__(
        self,
        vault_path: str,
        odoo_url: Optional[str] = None,
        db_name: Optional[str] = None,
        uid: Optional[int] = None,
        password: Optional[str] = None,
        check_interval: int = 300,
    ):
        """
        Initialize Odoo fallback manager.

        Args:
            vault_path: Path to vault directory
            odoo_url: Odoo JSON-RPC URL (default: http://localhost:8069/jsonrpc)
            db_name: Odoo database name
            uid: Odoo user ID
            password: Odoo password/API key
            check_interval: Seconds between availability checks (default: 300)
        """
        self.vault_path = Path(vault_path).resolve()
        self.odoo_url = odoo_url or "http://localhost:8069/jsonrpc"
        self.db_name = db_name or "odoo"
        self.uid = uid or 2
        self.password = password or "admin"
        self.check_interval = check_interval

        self.logger = AuditLogger(component="odoo_fallback")

        # Fallback state
        self._fallback_active = False
        self._fallback_activated_at: Optional[datetime] = None
        self._lock = threading.Lock()

        # Directories
        self.fallback_dir = self.vault_path / "Odoo_Fallback"
        self.queue_dir = self.vault_path / "Odoo_Queue"
        self.state_file = self.vault_path / "State" / "odoo_fallback_state.json"

        # Ensure directories exist
        self.fallback_dir.mkdir(parents=True, exist_ok=True)
        self.queue_dir.mkdir(parents=True, exist_ok=True)
        self.state_file.parent.mkdir(parents=True, exist_ok=True)

        # Load state
        self._load_state()

        # Alert callbacks
        self._alert_callbacks: list[Callable[[], None]] = []

        self.logger.info(
            "odoo_fallback_initialized",
            {
                "vault_path": str(self.vault_path),
                "odoo_url": self.odoo_url,
            },
        )

    def _load_state(self) -> None:
        """Load fallback state from file."""
        if self.state_file.exists():
            try:
                with open(self.state_file, "r") as f:
                    state = json.load(f)
                    self._fallback_active = state.get("fallback_active", False)
                    if state.get("fallback_activated_at"):
                        self._fallback_activated_at = datetime.fromisoformat(
                            state["fallback_activated_at"]
                        )
            except Exception as e:
                logger.warning(f"Failed to load Odoo fallback state: {e}")

    def _save_state(self) -> None:
        """Save fallback state to file."""
        try:
            state = {
                "fallback_active": self._fallback_active,
                "fallback_activated_at": (
                    self._fallback_activated_at.isoformat()
                    if self._fallback_activated_at
                    else None
                ),
                "last_checked": datetime.now().isoformat(),
            }
            with open(self.state_file, "w") as f:
                json.dump(state, f, indent=2)
        except Exception as e:
            logger.warning(f"Failed to save Odoo fallback state: {e}")

    def is_fallback_active(self) -> bool:
        """
        Check if fallback mode is currently active.

        Returns:
            True if fallback mode is active
        """
        return self._fallback_active

    def check_odoo_availability(self) -> bool:
        """
        Check if Odoo is available.

        Returns:
            True if Odoo is reachable and responsive
        """
        try:
            payload = {
                "jsonrpc": "2.0",
                "method": "call",
                "params": {
                    "service": "common",
                    "method": "version",
                    "args": [],
                },
                "id": 1,
            }

            response = requests.post(self.odoo_url, json=payload, timeout=5)
            response.raise_for_status()

            result = response.json()
            if "result" in result:
                self.logger.info("odoo_availability_check", {"status": "available"})
                return True

        except requests.exceptions.RequestException as e:
            self.logger.info("odoo_availability_check", {"status": "unavailable", "error": str(e)})
            return False
        except Exception as e:
            self.logger.info("odoo_availability_check", {"status": "unavailable", "error": str(e)})
            return False

        return False

    def activate_fallback(self, error: str) -> None:
        """
        Activate fallback mode.

        Args:
            error: Error that triggered fallback activation
        """
        with self._lock:
            if not self._fallback_active:
                self._fallback_active = True
                self._fallback_activated_at = datetime.now()
                self._save_state()

                self.logger.log(
                    "WARNING",
                    "odoo_fallback_activated",
                    {"error": error, "timestamp": self._fallback_activated_at.isoformat()},
                )

                # Trigger alert
                trigger_alert(
                    alert_type="odoo_fallback_activated",
                    message=f"Odoo fallback mode activated: {error}",
                    severity="WARNING",
                    details={"error": error, "timestamp": self._fallback_activated_at.isoformat()},
                )

                # Update dashboard
                self._update_dashboard_fallback_status()

    def deactivate_fallback(self) -> None:
        """Deactivate fallback mode."""
        with self._lock:
            if self._fallback_active:
                self._fallback_active = False
                self._fallback_activated_at = None
                self._save_state()

                self.logger.log(
                    "INFO",
                    "odoo_fallback_deactivated",
                    {"timestamp": datetime.now().isoformat()},
                )

                # Update dashboard
                self._update_dashboard_fallback_status()

    def log_fallback_transaction(
        self,
        transaction_type: str,
        action: str,
        data: dict[str, Any],
        error: str,
        original_metadata: Optional[dict[str, Any]] = None,
    ) -> Path:
        """
        Log a transaction to fallback directory.

        Args:
            transaction_type: Type of transaction (invoice, payment, expense)
            action: Action attempted (create, update, delete)
            data: Transaction data
            error: Error that caused fallback
            original_metadata: Original transaction metadata

        Returns:
            Path to created fallback file
        """
        timestamp = datetime.now()
        date_str = timestamp.strftime("%Y-%m-%d")
        file_id = timestamp.strftime("%Y%m%d_%H%M%S_%f")

        # Create daily fallback log
        fallback_log = self.fallback_dir / f"{date_str}.md"

        # Create queue item
        queue_item = {
            "id": file_id,
            "timestamp": timestamp.isoformat(),
            "transaction_type": transaction_type,
            "action": action,
            "data": data,
            "error": error,
            "original_metadata": original_metadata or {},
            "status": "pending",
            "retry_count": 0,
        }

        # Save to queue
        queue_file = self.queue_dir / f"QUEUE_{file_id}.json"
        with open(queue_file, "w") as f:
            json.dump(queue_item, f, indent=2)

        # Append to daily log
        self._append_to_fallback_log(fallback_log, queue_item)

        # Activate fallback if not already active
        if not self._fallback_active:
            self.activate_fallback(error)

        self.logger.log(
            "INFO",
            "odoo_fallback_transaction_logged",
            {
                "transaction_type": transaction_type,
                "action": action,
                "queue_file": str(queue_file),
            },
        )

        return fallback_log

    def _append_to_fallback_log(
        self,
        log_file: Path,
        transaction: dict[str, Any],
    ) -> None:
        """Append transaction to fallback log file."""
        is_new = not log_file.exists()

        with open(log_file, "a" if log_file.exists() else "w") as f:
            if is_new:
                f.write(f"# Odoo Fallback Log: {log_file.stem}\n\n")
                f.write(f"**Created**: {datetime.now().isoformat()}\n\n")
                f.write("## Transactions\n\n")

            f.write(f"### Transaction: {transaction['id']}\n\n")
            f.write(f"- **Timestamp**: {transaction['timestamp']}\n")
            f.write(f"- **Type**: {transaction['transaction_type']}\n")
            f.write(f"- **Action**: {transaction['action']}\n")
            f.write(f"- **Status**: {transaction['status']}\n")
            f.write(f"- **Error**: {transaction['error']}\n\n")
            f.write("**Data**:\n")
            f.write(f"```json\n{json.dumps(transaction['data'], indent=2)}\n```\n\n")
            f.write("---\n\n")

    def _update_dashboard_fallback_status(self) -> None:
        """Update Dashboard.md with fallback status."""
        dashboard_path = self.vault_path / "Dashboard.md"

        try:
            status_section = f"""
## Odoo Fallback Status

| Metric | Value |
|--------|-------|
| **Status** | {'⚠️ ACTIVE' if self._fallback_active else '✅ Inactive'} |
| **Activated At** | {self._fallback_activated_at.isoformat() if self._fallback_activated_at else 'N/A'} |
| **Queued Transactions** | {len(list(self.queue_dir.glob('*.json')))} |
| **Last Checked** | {datetime.now().isoformat()} |

"""

            if dashboard_path.exists():
                content = dashboard_path.read_text(encoding="utf-8")

                # Remove existing fallback section
                if "## Odoo Fallback Status" in content:
                    start_idx = content.find("## Odoo Fallback Status")
                    end_idx = content.find("\n## ", start_idx + 1)
                    if end_idx == -1:
                        end_idx = len(content)
                    content = content[:start_idx] + content[end_idx:]

                # Insert new section
                insert_marker = "\n## "
                last_section_idx = content.rfind(insert_marker)
                if last_section_idx != -1:
                    line_start = content.rfind("\n", 0, last_section_idx)
                    if line_start == -1:
                        line_start = 0
                    content = content[:line_start] + status_section + content[last_section_idx:]
                else:
                    content += status_section

            else:
                content = f"# FTE Agent Dashboard\n\n{status_section}"

            dashboard_path.write_text(content, encoding="utf-8")
            logger.debug("Dashboard updated with Odoo fallback status")

        except Exception as e:
            logger.error(f"Failed to update dashboard with fallback status: {e}")

    def sync_queued_transactions(self) -> dict[str, Any]:
        """
        Attempt to sync queued transactions to Odoo.

        Returns:
            Dict with sync results:
            - total: Total queued transactions
            - synced: Successfully synced
            - failed: Failed to sync
            - still_queued: Remaining in queue
        """
        results = {
            "total": 0,
            "synced": 0,
            "failed": 0,
            "still_queued": 0,
        }

        # Check if Odoo is available
        if not self.check_odoo_availability():
            self.logger.log("INFO", "odoo_sync_skipped", {"reason": "Odoo unavailable"})
            results["still_queued"] = len(list(self.queue_dir.glob("*.json")))
            return results

        # Odoo is available - deactivate fallback
        if self._fallback_active:
            self.deactivate_fallback()
            self.logger.log("INFO", "odoo_recovered", {"timestamp": datetime.now().isoformat()})

        # Process queue
        queue_files = list(self.queue_dir.glob("*.json"))
        results["total"] = len(queue_files)

        for queue_file in queue_files:
            try:
                with open(queue_file, "r") as f:
                    transaction = json.load(f)

                # Attempt to replay transaction
                success = self._replay_transaction(transaction)

                if success:
                    # Move to done
                    done_file = self.fallback_dir / f"DONE_{queue_file.name}"
                    queue_file.rename(done_file)
                    results["synced"] += 1

                    self.logger.log(
                        "INFO",
                        "odoo_transaction_synced",
                        {"transaction_id": transaction["id"]},
                    )
                else:
                    # Increment retry count
                    transaction["retry_count"] += 1
                    transaction["last_retry"] = datetime.now().isoformat()

                    if transaction["retry_count"] >= 3:
                        # Mark as failed
                        transaction["status"] = "failed"
                        failed_file = self.fallback_dir / f"FAILED_{queue_file.name}"
                        with open(failed_file, "w") as f:
                            json.dump(transaction, f, indent=2)
                        queue_file.unlink()
                        results["failed"] += 1
                    else:
                        # Save back to queue
                        with open(queue_file, "w") as f:
                            json.dump(transaction, f, indent=2)
                        results["still_queued"] += 1

            except Exception as e:
                logger.error(f"Failed to sync transaction {queue_file.name}: {e}")
                results["failed"] += 1

        self.logger.log(
            "INFO",
            "odoo_sync_completed",
            {
                "total": results["total"],
                "synced": results["synced"],
                "failed": results["failed"],
                "still_queued": results["still_queued"],
            },
        )

        return results

    def _replay_transaction(self, transaction: dict[str, Any]) -> bool:
        """
        Replay a queued transaction to Odoo.

        Args:
            transaction: Transaction data

        Returns:
            True if successful
        """
        try:
            # Build Odoo JSON-RPC request
            model_map = {
                "invoice": "account.move",
                "payment": "account.payment",
                "expense": "account.analytic.account",
            }

            model = model_map.get(transaction["transaction_type"])
            if not model:
                logger.warning(f"Unknown transaction type: {transaction['transaction_type']}")
                return False

            payload = {
                "jsonrpc": "2.0",
                "method": "call",
                "params": {
                    "service": "object",
                    "db": self.db_name,
                    "uid": self.uid,
                    "password": self.password,
                    "model": model,
                    "method": transaction["action"],
                    "args": [transaction["data"]],
                },
                "id": transaction["id"],
            }

            response = requests.post(self.odoo_url, json=payload, timeout=30)
            response.raise_for_status()

            result = response.json()
            if "result" in result:
                return True
            else:
                logger.warning(f"Odoo replay failed: {result.get('error', 'Unknown error')}")
                return False

        except Exception as e:
            logger.error(f"Odoo replay exception: {e}")
            return False

    def get_fallback_stats(self) -> dict[str, Any]:
        """
        Get fallback statistics.

        Returns:
            Dict with fallback statistics
        """
        queue_files = list(self.queue_dir.glob("*.json"))
        done_files = list(self.fallback_dir.glob("DONE_*.json"))
        failed_files = list(self.fallback_dir.glob("FAILED_*.json"))

        return {
            "fallback_active": self._fallback_active,
            "activated_at": self._fallback_activated_at.isoformat() if self._fallback_activated_at else None,
            "queued_count": len(queue_files),
            "synced_count": len(done_files),
            "failed_count": len(failed_files),
            "last_checked": datetime.now().isoformat(),
        }


# Global fallback manager instance
_fallback_instance: Optional[OdooFallbackManager] = None


def get_odoo_fallback_manager(
    vault_path: Optional[str] = None,
    odoo_url: Optional[str] = None,
    db_name: Optional[str] = None,
    uid: Optional[int] = None,
    password: Optional[str] = None,
) -> OdooFallbackManager:
    """
    Get or create global Odoo fallback manager instance.

    Args:
        vault_path: Path to vault directory
        odoo_url: Odoo JSON-RPC URL
        db_name: Odoo database name
        uid: Odoo user ID
        password: Odoo password/API key

    Returns:
        OdooFallbackManager instance
    """
    global _fallback_instance
    if _fallback_instance is None:
        vault = vault_path or str(Path(__file__).parent.parent.parent / "vault")
        _fallback_instance = OdooFallbackManager(
            vault_path=vault,
            odoo_url=odoo_url,
            db_name=db_name,
            uid=uid,
            password=password,
        )
    return _fallback_instance


def log_fallback_transaction(
    transaction_type: str,
    action: str,
    data: dict[str, Any],
    error: str,
) -> Path:
    """
    Log a transaction to Odoo fallback.

    Args:
        transaction_type: Type of transaction
        action: Action attempted
        data: Transaction data
        error: Error that caused fallback

    Returns:
        Path to fallback log file
    """
    fallback = get_odoo_fallback_manager()
    return fallback.log_fallback_transaction(transaction_type, action, data, error)


def sync_queued_transactions() -> dict[str, Any]:
    """
    Sync queued transactions to Odoo.

    Returns:
        Sync results dict
    """
    fallback = get_odoo_fallback_manager()
    return fallback.sync_queued_transactions()
