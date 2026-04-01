"""
Dead Letter Queue (DLQ) Utility.

Features:
- SQLite storage for failed actions
- Archive failed actions as .md files
- Retry tracking with max retry limit
- Manual reprocessing support
- Query methods for failed actions
- Metrics emission

Usage:
    # Create DLQ
    dlq = DeadLetterQueue()

    # Archive failed action
    dlq.archive_action(
        original_action="send_email",
        failure_reason="SMTP connection timeout",
        details={"to": "user@example.com", "subject": "Test"}
    )

    # Get failed actions
    failed = dlq.get_failed_actions(limit=10)

    # Reprocess action
    dlq.reprocess(action_id="abc-123")
"""

import json
import logging
import sqlite3
import threading
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

import json
import logging
import sqlite3
import threading
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)

# Global metrics callback (set by metrics collector)
_metrics_callback: Optional[callable] = None


def set_metrics_callback(callback: callable) -> None:
    """Set metrics callback for DLQ metrics emission."""
    global _metrics_callback
    _metrics_callback = callback


def _emit_metric(name: str, value: float = 1.0, tags: Optional[dict[str, str]] = None) -> None:
    """Emit metric if callback is registered."""
    if _metrics_callback:
        try:
            _metrics_callback(name, value, tags)
        except Exception as e:
            logger.debug(f"Failed to emit DLQ metric: {e}")


class DeadLetterQueueError(Exception):
    """Base exception for DLQ errors."""

    pass


class DeadLetterQueue:
    """
    Dead Letter Queue for failed actions.

    Features:
    - SQLite persistence
    - File-based archives in vault/Failed_Actions/
    - Retry tracking
    - Manual reprocessing
    """

    def __init__(
        self,
        db_path: Optional[str] = None,
        vault_dir: Optional[str] = None,
        max_retries: int = 3,
    ):
        """
        Initialize DLQ.

        Args:
            db_path: Path to SQLite database (default: data/failed_actions.db)
            vault_dir: Path to vault directory (default: vault/)
            max_retries: Maximum retry attempts (default: 3)
        """
        self.db_path = db_path or str(Path(__file__).parent.parent / "data" / "failed_actions.db")
        self.vault_dir = vault_dir or str(Path(__file__).parent.parent.parent / "vault")
        self.max_retries = max_retries

        self._lock = threading.Lock()

        # Initialize database
        self._init_db()

        # Ensure Failed_Actions directory exists
        self._failed_actions_dir = Path(self.vault_dir) / "Failed_Actions"
        self._failed_actions_dir.mkdir(parents=True, exist_ok=True)

        # Dashboard path for DLQ status updates
        self.dashboard_path = Path(self.vault_dir) / "Dashboard.md"

        logger.debug(f"DeadLetterQueue initialized (db={self.db_path})")

    def _init_db(self) -> None:
        """Initialize SQLite database schema."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS failed_actions (
                id TEXT PRIMARY KEY,
                original_action TEXT NOT NULL,
                failure_reason TEXT NOT NULL,
                failure_count INTEGER DEFAULT 1,
                last_attempt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                details TEXT,
                original_metadata TEXT,
                status TEXT DEFAULT 'failed',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
        )
        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_failed_actions_status ON failed_actions(status)
        """
        )
        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_failed_actions_created ON failed_actions(created_at)
        """
        )
        conn.commit()
        conn.close()

    def archive_action(
        self,
        original_action: str,
        failure_reason: str,
        details: Optional[dict[str, Any]] = None,
        original_metadata: Optional[dict[str, Any]] = None,
        action_id: Optional[str] = None,
    ) -> str:
        """
        Archive a failed action to DLQ.

        Args:
            original_action: Name/type of the failed action
            failure_reason: Reason for failure
            details: Additional failure details
            original_metadata: Original action metadata
            action_id: Optional action ID (generated if not provided)

        Returns:
            Action ID
        """
        if action_id is None:
            action_id = str(uuid.uuid4())

        timestamp = datetime.now()

        # Insert into database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO failed_actions
            (id, original_action, failure_reason, details, original_metadata, last_attempt)
            VALUES (?, ?, ?, ?, ?, ?)
        """,
            (
                action_id,
                original_action,
                failure_reason,
                json.dumps(details or {}),
                json.dumps(original_metadata or {}),
                timestamp,
            ),
        )
        conn.commit()
        conn.close()

        # Create .md file in vault/Failed_Actions/
        self._create_dlq_file(
            action_id=action_id,
            original_action=original_action,
            failure_reason=failure_reason,
            failure_count=1,
            last_attempt=timestamp,
            details=details,
            original_metadata=original_metadata,
        )

        # Emit metrics
        _emit_metric("dlq_archive_count", tags={"action": original_action})

        # Update dashboard with new DLQ status
        self.update_dashboard()

        logger.info(f"Archived failed action to DLQ: {action_id}")
        return action_id

    def _create_dlq_file(
        self,
        action_id: str,
        original_action: str,
        failure_reason: str,
        failure_count: int,
        last_attempt: datetime,
        details: Optional[dict[str, Any]] = None,
        original_metadata: Optional[dict[str, Any]] = None,
    ) -> None:
        """Create DLQ markdown file."""
        file_path = self._failed_actions_dir / f"DLQ_{action_id}.md"

        content = f"""---
original_action: {original_action}
failure_reason: {failure_reason}
failure_count: {failure_count}
last_attempt: {last_attempt.isoformat()}
details: {json.dumps(details or {})}
---

# Dead Letter Queue Entry: {action_id}

## Original Action

| Field | Value |
|-------|-------|
| **Action ID** | {action_id} |
| **Action Type** | {original_action} |
| **Failure Count** | {failure_count} |
| **Last Attempt** | {last_attempt.isoformat()} |
| **Max Retries** | {self.max_retries} |

## Failure Information

**Reason**: {failure_reason}

**Details**:
```json
{json.dumps(details or {}, indent=2)}
```

## Reprocessing Instructions

**To manually reprocess this action:**

1. Review the failure reason above
2. Fix the underlying issue
3. Move this file from `Failed_Actions/` to `Needs_Action/`
4. Re-run the action

**To archive permanently:**

1. Move to `Done/` with prefix `ARCHIVED_`

---

## Original Action Metadata

```json
{json.dumps(original_metadata or {}, indent=2)}
```

---

**Storage:**
- SQLite: `data/failed_actions.db`
- File: `Failed_Actions/DLQ_{action_id}.md`
"""

        with open(file_path, "w") as f:
            f.write(content)

    def increment_failure_count(self, action_id: str, failure_reason: str) -> bool:
        """
        Increment failure count for existing action.

        Args:
            action_id: Action ID
            failure_reason: New failure reason

        Returns:
            True if action exists and was updated
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Get current failure count
        cursor.execute(
            "SELECT failure_count, original_action FROM failed_actions WHERE id = ?",
            (action_id,),
        )
        row = cursor.fetchone()

        if not row:
            conn.close()
            return False

        current_count = row[0]
        original_action = row[1]
        new_count = current_count + 1

        # Update record
        cursor.execute(
            """
            UPDATE failed_actions
            SET failure_count = ?, failure_reason = ?, last_attempt = ?, updated_at = ?
            WHERE id = ?
        """,
            (new_count, failure_reason, datetime.now(), datetime.now(), action_id),
        )
        conn.commit()
        conn.close()

        # Update .md file
        cursor = sqlite3.connect(self.db_path).cursor()
        cursor.execute("SELECT * FROM failed_actions WHERE id = ?", (action_id,))
        row = cursor.fetchone()
        if row:
            self._update_dlq_file(row)

        logger.warning(f"Action {action_id} failure count incremented to {new_count}")
        return True

    def _update_dlq_file(self, row: tuple) -> None:
        """Update DLQ markdown file."""
        action_id, original_action, failure_reason, failure_count, last_attempt, details, original_metadata = row[:7]

        self._create_dlq_file(
            action_id=action_id,
            original_action=original_action,
            failure_reason=failure_reason,
            failure_count=failure_count,
            last_attempt=datetime.fromisoformat(last_attempt) if isinstance(last_attempt, str) else last_attempt,
            details=json.loads(details) if details else {},
            original_metadata=json.loads(original_metadata) if original_metadata else {},
        )

    def get_failed_actions(
        self,
        limit: int = 100,
        status: Optional[str] = None,
        action_type: Optional[str] = None,
    ) -> list[dict[str, Any]]:
        """
        Query failed actions.

        Args:
            limit: Maximum results to return
            status: Filter by status
            action_type: Filter by action type

        Returns:
            List of failed action records
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        query = "SELECT * FROM failed_actions WHERE 1=1"
        params: list[Any] = []

        if status:
            query += " AND status = ?"
            params.append(status)

        if action_type:
            query += " AND original_action = ?"
            params.append(action_type)

        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)

        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()

        results = []
        for row in rows:
            results.append(
                {
                    "id": row["id"],
                    "original_action": row["original_action"],
                    "failure_reason": row["failure_reason"],
                    "failure_count": row["failure_count"],
                    "last_attempt": row["last_attempt"],
                    "details": json.loads(row["details"]) if row["details"] else {},
                    "original_metadata": json.loads(row["original_metadata"]) if row["original_metadata"] else {},
                    "status": row["status"],
                    "created_at": row["created_at"],
                }
            )

        return results

    def reprocess(self, action_id: str) -> bool:
        """
        Mark action for reprocessing.

        Args:
            action_id: Action ID to reprocess

        Returns:
            True if action was found and marked
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Check if action exists and is under retry limit
        cursor.execute(
            "SELECT failure_count FROM failed_actions WHERE id = ?",
            (action_id,),
        )
        row = cursor.fetchone()

        if not row:
            conn.close()
            logger.warning(f"Action {action_id} not found in DLQ")
            return False

        failure_count = row[0]
        if failure_count >= self.max_retries:
            conn.close()
            logger.error(f"Action {action_id} exceeded max retries ({self.max_retries})")
            return False

        # Update status
        cursor.execute(
            """
            UPDATE failed_actions
            SET status = 'pending_reprocess', updated_at = ?
            WHERE id = ?
        """,
            (datetime.now(), action_id),
        )
        conn.commit()
        conn.close()

        # Emit metrics
        _emit_metric("dlq_reprocess_count", tags={"action_id": action_id})

        logger.info(f"Action {action_id} marked for reprocessing")
        return True

    def delete_action(self, action_id: str) -> bool:
        """
        Delete action from DLQ.

        Args:
            action_id: Action ID to delete

        Returns:
            True if action was found and deleted
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("DELETE FROM failed_actions WHERE id = ?", (action_id,))
        deleted = cursor.rowcount > 0
        conn.commit()
        conn.close()

        # Delete .md file
        file_path = self._failed_actions_dir / f"DLQ_{action_id}.md"
        if file_path.exists():
            file_path.unlink()

        if deleted:
            logger.info(f"Deleted action {action_id} from DLQ")
        return deleted

    def get_retry_count(self, action_id: str) -> Optional[int]:
        """
        Get retry count for action.

        Args:
            action_id: Action ID

        Returns:
            Failure count or None if not found
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT failure_count FROM failed_actions WHERE id = ?", (action_id,))
        row = cursor.fetchone()
        conn.close()

        return row[0] if row else None

    def is_under_retry_limit(self, action_id: str) -> bool:
        """
        Check if action is under retry limit.

        Args:
            action_id: Action ID

        Returns:
            True if under limit
        """
        count = self.get_retry_count(action_id)
        return count is not None and count < self.max_retries

    def update_dashboard(self) -> None:
        """
        Update Dashboard.md with DLQ status.

        Adds a DLQ status section showing:
        - Total failed actions
        - Actions pending reprocess
        - Actions exceeding max retries
        - Recent failures (last 5)
        """
        try:
            # Get DLQ statistics
            all_failed = self.get_failed_actions(limit=1000)
            total_failed = len(all_failed)
            pending_reprocess = sum(1 for a in all_failed if a.get("status") == "pending_reprocess")
            exceeded_retries = sum(1 for a in all_failed if a.get("failure_count", 0) >= self.max_retries)
            active_failures = total_failed - exceeded_retries

            # Get recent failures
            recent = all_failed[:5] if total_failed > 0 else []

            # Build DLQ section
            dlq_section = f"""
## Dead Letter Queue Status

| Metric | Value |
|--------|-------|
| **Total Failed Actions** | {total_failed} |
| **Active Failures** | {active_failures} |
| **Pending Reprocess** | {pending_reprocess} |
| **Exceeded Max Retries** | {exceeded_retries} |
| **Last Updated** | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} |

"""

            if recent:
                dlq_section += "### Recent Failures\n\n"
                for i, action in enumerate(recent, 1):
                    dlq_section += f"""
**{i}. {action['original_action']}** (ID: `{action['id']}`)
- **Failure Count**: {action['failure_count']}/{self.max_retries}
- **Reason**: {action['failure_reason']}
- **Status**: {action['status']}
- **Last Attempt**: {action['last_attempt']}

"""
            else:
                dlq_section += "**✅ No failed actions in DLQ**\n\n"

            # Read existing dashboard
            if self.dashboard_path.exists():
                content = self.dashboard_path.read_text(encoding="utf-8")

                # Remove existing DLQ section if present
                start_marker = "## Dead Letter Queue Status"
                if start_marker in content:
                    # Find start and end of section
                    start_idx = content.find(start_marker)
                    # Find next ## section or end of file
                    end_idx = content.find("\n## ", start_idx + 1)
                    if end_idx == -1:
                        end_idx = len(content)
                    content = content[:start_idx] + content[end_idx:]

                # Insert DLQ section before last ## section or at end
                insert_marker = "\n## "
                last_section_idx = content.rfind(insert_marker)
                if last_section_idx != -1:
                    # Find the start of the last section
                    line_start = content.rfind("\n", 0, last_section_idx)
                    if line_start == -1:
                        line_start = 0
                    content = content[:line_start] + dlq_section + content[last_section_idx:]
                else:
                    content += dlq_section

            else:
                # Create new dashboard
                content = f"""# FTE Agent Dashboard

{dlq_section}
"""

            # Write updated dashboard
            self.dashboard_path.write_text(content, encoding="utf-8")
            logger.debug("Dashboard updated with DLQ status")

        except Exception as e:
            logger.warning(f"Failed to update dashboard with DLQ status: {e}")

    def get_dlq_stats(self) -> dict[str, Any]:
        """
        Get DLQ statistics.

        Returns:
            Dict with DLQ statistics
        """
        all_failed = self.get_failed_actions(limit=1000)
        return {
            "total_failed": len(all_failed),
            "pending_reprocess": sum(1 for a in all_failed if a.get("status") == "pending_reprocess"),
            "exceeded_retries": sum(1 for a in all_failed if a.get("failure_count", 0) >= self.max_retries),
            "active_failures": sum(1 for a in all_failed if a.get("failure_count", 0) < self.max_retries),
            "by_action_type": self._count_by_action_type(all_failed),
        }

    def _count_by_action_type(self, actions: list[dict[str, Any]]) -> dict[str, int]:
        """Count failures by action type."""
        counts: dict[str, int] = {}
        for action in actions:
            action_type = action.get("original_action", "unknown")
            counts[action_type] = counts.get(action_type, 0) + 1
        return counts
