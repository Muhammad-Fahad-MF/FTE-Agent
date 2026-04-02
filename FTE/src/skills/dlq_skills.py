"""
DLQ (Dead Letter Queue) Manual Review Skills.

Provides skills for manual review and resolution of failed actions:
- list_dlq_items: Query DLQ items by status
- resolve_dlq_item: Mark item as resolved
- discard_dlq_item: Discard item permanently

Usage:
    from src.skills.dlq_skills import list_dlq_items, resolve_dlq_item, discard_dlq_item
    
    # List all failed actions
    failed = list_dlq_items()
    
    # List only pending items
    pending = list_dlq_items(status="pending_review")
    
    # Resolve an item
    resolve_dlq_item("abc-123", resolution="Fixed SMTP credentials", notes="Updated .env file")
    
    # Discard an item
    discard_dlq_item("xyz-789", notes="Action no longer needed")
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from src.utils.dead_letter_queue import DeadLetterQueue
from src.audit_logger import AuditLogger

logger = logging.getLogger(__name__)

# Global DLQ instance
_dlq_instance: Optional[DeadLetterQueue] = None


def get_dlq() -> DeadLetterQueue:
    """Get or create DLQ singleton instance."""
    global _dlq_instance
    if _dlq_instance is None:
        _dlq_instance = DeadLetterQueue()
    return _dlq_instance


def list_dlq_items(
    status: Optional[str] = None,
    action_type: Optional[str] = None,
    limit: int = 100,
) -> list[dict[str, Any]]:
    """
    List DLQ items filtered by status and/or action type.

    Args:
        status: Filter by status (pending_review, resolved, discarded)
        action_type: Filter by original action type
        limit: Maximum results to return (default: 100)

    Returns:
        List of DLQ items with fields:
        - id: UUID of the DLQ item
        - original_action: Name of failed action
        - failure_reason: Reason for failure
        - failure_count: Number of failure attempts
        - last_attempt: Timestamp of last attempt
        - details: Additional failure details
        - original_metadata: Original action metadata
        - status: Current status
        - created_at: Creation timestamp

    Example:
        >>> items = list_dlq_items(status="pending_review")
        >>> len(items)
        5
        >>> items[0]["original_action"]
        'send_email'
    """
    audit_logger = AuditLogger(component="dlq_skills")
    
    try:
        dlq = get_dlq()
        items = dlq.get_failed_actions(
            limit=limit,
            status=status,
            action_type=action_type,
        )
        
        audit_logger.log(
            "INFO",
            "dlq_items_listed",
            {
                "status_filter": status,
                "action_type_filter": action_type,
                "result_count": len(items),
            },
        )
        
        return items
        
    except Exception as e:
        audit_logger.log(
            "ERROR",
            "dlq_list_failed",
            {"error": str(e), "status_filter": status},
        )
        raise


def resolve_dlq_item(
    item_id: str,
    resolution: str,
    notes: Optional[str] = None,
) -> bool:
    """
    Mark a DLQ item as resolved.

    Args:
        item_id: UUID of the DLQ item
        resolution: Description of how it was resolved
        notes: Optional additional notes

    Returns:
        True if item was found and resolved, False otherwise

    Example:
        >>> resolve_dlq_item(
        ...     "abc-123",
        ...     resolution="Fixed SMTP credentials",
        ...     notes="Updated .env file with new password"
        ... )
        True
    """
    audit_logger = AuditLogger(component="dlq_skills")
    
    try:
        dlq = get_dlq()
        
        # Check if item exists
        items = dlq.get_failed_actions(limit=1, action_type=None)
        item_exists = any(item["id"] == item_id for item in items)
        
        if not item_exists:
            audit_logger.log(
                "WARNING",
                "dlq_resolve_not_found",
                {"item_id": item_id},
            )
            return False
        
        # Update database status
        conn = dlq._init_db() or None  # Ensure DB initialized
        import sqlite3
        conn = sqlite3.connect(dlq.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            """
            UPDATE failed_actions
            SET status = 'resolved', updated_at = ?
            WHERE id = ?
        """,
            (datetime.now(), item_id),
        )
        
        updated = cursor.rowcount > 0
        conn.commit()
        conn.close()
        
        if updated:
            # Update .md file with resolution
            _update_dlq_file_resolution(dlq, item_id, resolution, notes)
            
            audit_logger.log(
                "INFO",
                "dlq_item_resolved",
                {
                    "item_id": item_id,
                    "resolution": resolution,
                },
            )
            
            # Update dashboard
            dlq.update_dashboard()
            
            return True
        
        return False
        
    except Exception as e:
        audit_logger.log(
            "ERROR",
            "dlq_resolve_failed",
            {"item_id": item_id, "error": str(e)},
        )
        raise


def _update_dlq_file_resolution(
    dlq: DeadLetterQueue,
    item_id: str,
    resolution: str,
    notes: Optional[str],
) -> None:
    """Update DLQ markdown file with resolution information."""
    file_path = dlq._failed_actions_dir / f"DLQ_{item_id}.md"
    
    if not file_path.exists():
        logger.warning(f"DLQ file not found: {file_path}")
        return
    
    content = file_path.read_text(encoding="utf-8")
    
    # Add resolution section
    resolution_section = f"""
## Resolution

**Status**: RESOLVED
**Resolved At**: {datetime.now().isoformat()}
**Resolution**: {resolution}
"""
    
    if notes:
        resolution_section += f"**Notes**: {notes}\n"
    
    # Append resolution section
    content += "\n" + resolution_section
    
    file_path.write_text(content, encoding="utf-8")


def discard_dlq_item(
    item_id: str,
    notes: Optional[str] = None,
) -> bool:
    """
    Discard a DLQ item permanently.

    Args:
        item_id: UUID of the DLQ item
        notes: Optional reason for discarding

    Returns:
        True if item was found and discarded, False otherwise

    Example:
        >>> discard_dlq_item("xyz-789", notes="Action no longer needed")
        True
    """
    audit_logger = AuditLogger(component="dlq_skills")
    
    try:
        dlq = get_dlq()
        
        # Check if item exists
        items = dlq.get_failed_actions(limit=1, action_type=None)
        item_exists = any(item["id"] == item_id for item in items)
        
        if not item_exists:
            audit_logger.log(
                "WARNING",
                "dlq_discard_not_found",
                {"item_id": item_id},
            )
            return False
        
        # Update database status
        import sqlite3
        conn = sqlite3.connect(dlq.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            """
            UPDATE failed_actions
            SET status = 'discarded', updated_at = ?
            WHERE id = ?
        """,
            (datetime.now(), item_id),
        )
        
        updated = cursor.rowcount > 0
        conn.commit()
        conn.close()
        
        if updated:
            # Update .md file with discard notice
            _update_dlq_file_discard(dlq, item_id, notes)
            
            audit_logger.log(
                "INFO",
                "dlq_item_discarded",
                {
                    "item_id": item_id,
                    "notes": notes,
                },
            )
            
            # Update dashboard
            dlq.update_dashboard()
            
            return True
        
        return False
        
    except Exception as e:
        audit_logger.log(
            "ERROR",
            "dlq_discard_failed",
            {"item_id": item_id, "error": str(e)},
        )
        raise


def _update_dlq_file_discard(
    dlq: DeadLetterQueue,
    item_id: str,
    notes: Optional[str],
) -> None:
    """Update DLQ markdown file with discard information."""
    file_path = dlq._failed_actions_dir / f"DLQ_{item_id}.md"
    
    if not file_path.exists():
        logger.warning(f"DLQ file not found: {file_path}")
        return
    
    content = file_path.read_text(encoding="utf-8")
    
    # Add discard section
    discard_section = f"""
## Discarded

**Status**: DISCARDED
**Discarded At**: {datetime.now().isoformat()}
"""
    
    if notes:
        discard_section += f"**Reason**: {notes}\n"
    
    discard_section += """
**Note**: This item has been permanently discarded and will not be reprocessed.
"""
    
    # Append discard section
    content += "\n" + discard_section
    
    file_path.write_text(content, encoding="utf-8")


def get_dlq_summary() -> dict[str, Any]:
    """
    Get summary statistics for DLQ.

    Returns:
        Dictionary with DLQ statistics:
        - total_failed: Total number of failed actions
        - pending_review: Items awaiting manual review
        - resolved: Items that have been resolved
        - discarded: Items that have been discarded
        - by_action_type: Breakdown by action type

    Example:
        >>> summary = get_dlq_summary()
        >>> summary["total_failed"]
        15
        >>> summary["pending_review"]
        5
    """
    audit_logger = AuditLogger(component="dlq_skills")
    
    try:
        dlq = get_dlq()
        stats = dlq.get_dlq_stats()
        
        # Get all items for status breakdown
        all_items = dlq.get_failed_actions(limit=1000)
        
        summary = {
            "total_failed": len(all_items),
            "pending_review": sum(1 for i in all_items if i.get("status") == "pending_review"),
            "resolved": sum(1 for i in all_items if i.get("status") == "resolved"),
            "discarded": sum(1 for i in all_items if i.get("status") == "discarded"),
            "by_action_type": stats.get("by_action_type", {}),
            "last_updated": datetime.now().isoformat(),
        }
        
        audit_logger.log(
            "INFO",
            "dlq_summary_generated",
            {"total_failed": summary["total_failed"]},
        )
        
        return summary
        
    except Exception as e:
        audit_logger.log(
            "ERROR",
            "dlq_summary_failed",
            {"error": str(e)},
        )
        raise


def reprocess_dlq_item(item_id: str) -> bool:
    """
    Mark a DLQ item for reprocessing.

    Args:
        item_id: UUID of the DLQ item

    Returns:
        True if item was marked for reprocessing, False otherwise

    Example:
        >>> reprocess_dlq_item("abc-123")
        True
    """
    audit_logger = AuditLogger(component="dlq_skills")
    
    try:
        dlq = get_dlq()
        
        # Check if item exists and is under retry limit
        result = dlq.reprocess(item_id)
        
        if result:
            audit_logger.log(
                "INFO",
                "dlq_item_reprocess",
                {"item_id": item_id},
            )
            
            # Update dashboard
            dlq.update_dashboard()
        
        return result
        
    except Exception as e:
        audit_logger.log(
            "ERROR",
            "dlq_reprocess_failed",
            {"item_id": item_id, "error": str(e)},
        )
        raise
