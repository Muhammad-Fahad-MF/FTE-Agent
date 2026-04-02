"""
Audit Logs Query Skills.

Provides skills for querying and exporting audit logs:
- query_logs: Query logs by date, action type, result
- export_to_csv: Export log entries to CSV format
- get_log_statistics: Get log statistics and summaries

Usage:
    from src.skills.audit_skills import query_logs, export_to_csv, get_log_statistics
    
    # Query logs by date
    logs = query_logs(date="2026-04-01")
    
    # Query logs by action type
    emails = query_logs(action="email_sent")
    
    # Query failed actions
    failures = query_logs(result="failure")
    
    # Export to CSV
    export_to_csv(logs, "output.csv")
    
    # Get statistics
    stats = get_log_statistics(days=7)
"""

import csv
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Optional

from src.audit_logger import AuditLogger

logger = logging.getLogger(__name__)


def query_logs(
    date: Optional[str] = None,
    action: Optional[str] = None,
    result: Optional[str] = None,
    component: Optional[str] = None,
    limit: int = 1000,
    vault_path: Optional[str] = None,
) -> list[dict[str, Any]]:
    """
    Query audit logs by filters.

    Args:
        date: Date string (YYYY-MM-DD) or date range (YYYY-MM-DD:YYYY-MM-DD)
        action: Filter by action type (e.g., "email_sent", "approval_requested")
        result: Filter by result (success, failure, pending)
        component: Filter by component (e.g., "gmail_watcher", "approval_skills")
        limit: Maximum results to return (default: 1000)
        vault_path: Path to vault directory (default: ./vault)

    Returns:
        List of log entries matching filters

    Example:
        >>> logs = query_logs(date="2026-04-01", action="email_sent")
        >>> len(logs)
        15
        >>> logs[0]["action"]
        'email_sent'
    """
    audit_logger = AuditLogger(component="audit_skills")
    
    # Resolve vault path
    if vault_path is None:
        vault_path = str(Path(__file__).parent.parent.parent / "vault")
    
    logs_dir = Path(vault_path) / "Logs"
    
    if not logs_dir.exists():
        logger.warning(f"Logs directory not found: {logs_dir}")
        return []
    
    # Determine date range
    date_ranges = _parse_date_range(date)
    
    # Collect matching log entries
    matching_logs = []
    
    for log_date in date_ranges:
        log_file = logs_dir / f"{log_date}.json"
        
        if not log_file.exists():
            continue
        
        try:
            with open(log_file, "r") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    
                    try:
                        log_entry = json.loads(line)
                        
                        # Apply filters
                        if action and log_entry.get("action") != action:
                            continue
                        if result and log_entry.get("result") != result:
                            continue
                        if component and log_entry.get("component") != component:
                            continue
                        
                        matching_logs.append(log_entry)
                        
                        if len(matching_logs) >= limit:
                            break
                            
                    except json.JSONDecodeError:
                        logger.warning(f"Failed to parse log line in {log_file}")
                        continue
                        
        except Exception as e:
            logger.error(f"Failed to read log file {log_file}: {e}")
        
        if len(matching_logs) >= limit:
            break
    
    audit_logger.log(
        "INFO",
        "logs_queried",
        {
            "date_filter": date,
            "action_filter": action,
            "result_filter": result,
            "component_filter": component,
            "result_count": len(matching_logs),
        },
    )
    
    return matching_logs


def _parse_date_range(date: Optional[str]) -> list[str]:
    """
    Parse date string into list of dates.

    Args:
        date: Date string (YYYY-MM-DD) or range (YYYY-MM-DD:YYYY-MM-DD)

    Returns:
        List of date strings (YYYY-MM-DD)
    """
    if not date:
        # Default to today
        return [datetime.now().strftime("%Y-%m-%d")]
    
    if ":" in date:
        # Date range
        start_str, end_str = date.split(":", 1)
        start_date = datetime.strptime(start_str, "%Y-%m-%d")
        end_date = datetime.strptime(end_str, "%Y-%m-%d")
        
        dates = []
        current = start_date
        while current <= end_date:
            dates.append(current.strftime("%Y-%m-%d"))
            current += timedelta(days=1)
        
        return dates
    else:
        # Single date
        return [date]


def export_to_csv(
    log_entries: list[dict[str, Any]],
    output_path: str,
    fields: Optional[list[str]] = None,
) -> Path:
    """
    Export log entries to CSV format.

    Args:
        log_entries: List of log entries to export
        output_path: Path to output CSV file
        fields: Optional list of fields to include (default: all fields)

    Returns:
        Path to created CSV file

    Example:
        >>> logs = query_logs(date="2026-04-01")
        >>> csv_path = export_to_csv(logs, "logs.csv")
        >>> csv_path.exists()
        True
    """
    audit_logger = AuditLogger(component="audit_skills")
    
    if not log_entries:
        logger.warning("No log entries to export")
        return None
    
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Determine fields
    if fields is None:
        # Use all fields from first entry
        fields = list(log_entries[0].keys())
    
    # Write CSV
    with open(output_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(log_entries)
    
    audit_logger.log(
        "INFO",
        "logs_exported",
        {
            "output_path": str(output_file),
            "entry_count": len(log_entries),
            "fields": fields,
        },
    )
    
    logger.info(f"Exported {len(log_entries)} log entries to {output_file}")
    return output_file


def get_log_statistics(
    days: int = 7,
    vault_path: Optional[str] = None,
) -> dict[str, Any]:
    """
    Get log statistics for the specified period.

    Args:
        days: Number of days to analyze (default: 7)
        vault_path: Path to vault directory

    Returns:
        Dictionary with statistics:
        - total_entries: Total log entries
        - by_result: Count by result (success, failure, pending)
        - by_action: Count by action type
        - by_component: Count by component
        - by_date: Count by date
        - error_rate: Percentage of failures
        - peak_hour: Hour with most activity

    Example:
        >>> stats = get_log_statistics(days=7)
        >>> stats["total_entries"]
        1500
        >>> stats["error_rate"]
        2.5
    """
    audit_logger = AuditLogger(component="audit_skills")
    
    # Resolve vault path
    if vault_path is None:
        vault_path = str(Path(__file__).parent.parent.parent / "vault")
    
    logs_dir = Path(vault_path) / "Logs"
    
    if not logs_dir.exists():
        logger.warning(f"Logs directory not found: {logs_dir}")
        return {
            "total_entries": 0,
            "by_result": {},
            "by_action": {},
            "by_component": {},
            "by_date": {},
            "error_rate": 0.0,
            "peak_hour": None,
        }
    
    # Calculate date range
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    # Collect statistics
    stats = {
        "total_entries": 0,
        "by_result": {},
        "by_action": {},
        "by_component": {},
        "by_date": {},
        "by_hour": {},
        "errors": [],
    }
    
    current_date = start_date
    while current_date <= end_date:
        log_file = logs_dir / f"{current_date.strftime('%Y-%m-%d')}.json"
        
        if log_file.exists():
            try:
                with open(log_file, "r") as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        
                        try:
                            log_entry = json.loads(line)
                            stats["total_entries"] += 1
                            
                            # By result
                            result = log_entry.get("result", "unknown")
                            stats["by_result"][result] = stats["by_result"].get(result, 0) + 1
                            
                            # By action
                            action = log_entry.get("action", "unknown")
                            stats["by_action"][action] = stats["by_action"].get(action, 0) + 1
                            
                            # By component
                            component = log_entry.get("component", "unknown")
                            stats["by_component"][component] = stats["by_component"].get(component, 0) + 1
                            
                            # By date
                            date_str = current_date.strftime("%Y-%m-%d")
                            stats["by_date"][date_str] = stats["by_date"].get(date_str, 0) + 1
                            
                            # By hour
                            timestamp = log_entry.get("timestamp", "")
                            if timestamp:
                                try:
                                    dt = datetime.fromisoformat(timestamp)
                                    hour = dt.strftime("%H:00")
                                    stats["by_hour"][hour] = stats["by_hour"].get(hour, 0) + 1
                                except Exception:
                                    pass
                            
                            # Track errors
                            if result == "failure":
                                stats["errors"].append({
                                    "timestamp": log_entry.get("timestamp"),
                                    "action": log_entry.get("action"),
                                    "component": log_entry.get("component"),
                                    "error": log_entry.get("error"),
                                })
                                
                        except json.JSONDecodeError:
                            continue
                            
            except Exception as e:
                logger.error(f"Failed to read log file {log_file}: {e}")
        
        current_date += timedelta(days=1)
    
    # Calculate error rate
    total = stats["total_entries"]
    failures = stats["by_result"].get("failure", 0)
    error_rate = (failures / total * 100) if total > 0 else 0.0
    
    # Find peak hour
    peak_hour = None
    peak_count = 0
    for hour, count in stats["by_hour"].items():
        if count > peak_count:
            peak_count = count
            peak_hour = hour
    
    # Build result
    result = {
        "total_entries": total,
        "by_result": stats["by_result"],
        "by_action": stats["by_action"],
        "by_component": stats["by_component"],
        "by_date": stats["by_date"],
        "error_rate": round(error_rate, 2),
        "peak_hour": peak_hour,
        "peak_hour_count": peak_count,
        "period": {
            "start": start_date.strftime("%Y-%m-%d"),
            "end": end_date.strftime("%Y-%m-%d"),
        },
        "recent_errors": stats["errors"][-10:],  # Last 10 errors
    }
    
    audit_logger.log(
        "INFO",
        "log_statistics_generated",
        {
            "days": days,
            "total_entries": total,
            "error_rate": error_rate,
        },
    )
    
    return result


def get_recent_errors(
    limit: int = 50,
    vault_path: Optional[str] = None,
) -> list[dict[str, Any]]:
    """
    Get recent error log entries.

    Args:
        limit: Maximum errors to return (default: 50)
        vault_path: Path to vault directory

    Returns:
        List of error log entries

    Example:
        >>> errors = get_recent_errors(limit=10)
        >>> len(errors)
        10
    """
    # Query for failure results
    errors = query_logs(result="failure", limit=limit, vault_path=vault_path)
    
    # Sort by timestamp (most recent first)
    errors.sort(
        key=lambda x: x.get("timestamp", ""),
        reverse=True,
    )
    
    return errors


def search_logs(
    query: str,
    field: str = "details",
    limit: int = 100,
    vault_path: Optional[str] = None,
) -> list[dict[str, Any]]:
    """
    Search logs by text query in a specific field.

    Args:
        query: Search query string
        field: Field to search in (default: details)
        limit: Maximum results to return (default: 100)
        vault_path: Path to vault directory

    Returns:
        List of matching log entries

    Example:
        >>> results = search_logs("timeout", field="error")
        >>> len(results)
        5
    """
    audit_logger = AuditLogger(component="audit_skills")
    
    # Resolve vault path
    if vault_path is None:
        vault_path = str(Path(__file__).parent.parent.parent / "vault")
    
    logs_dir = Path(vault_path) / "Logs"
    
    if not logs_dir.exists():
        return []
    
    # Get all log files (last 30 days)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    
    matching_logs = []
    current_date = start_date
    
    while current_date <= end_date:
        if len(matching_logs) >= limit:
            break
        
        log_file = logs_dir / f"{current_date.strftime('%Y-%m-%d')}.json"
        
        if log_file.exists():
            try:
                with open(log_file, "r") as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        
                        try:
                            log_entry = json.loads(line)
                            
                            # Search in specified field
                            field_value = log_entry.get(field, "")
                            
                            # Handle nested fields (e.g., details.error)
                            if "." in field:
                                parts = field.split(".")
                                value = log_entry
                                for part in parts:
                                    if isinstance(value, dict):
                                        value = value.get(part, "")
                                    else:
                                        value = ""
                                        break
                                field_value = value
                            
                            if isinstance(field_value, str) and query.lower() in field_value.lower():
                                matching_logs.append(log_entry)
                                
                                if len(matching_logs) >= limit:
                                    break
                                    
                        except json.JSONDecodeError:
                            continue
                            
            except Exception as e:
                logger.error(f"Failed to read log file {log_file}: {e}")
        
        current_date += timedelta(days=1)
    
    audit_logger.log(
        "INFO",
        "logs_searched",
        {
            "query": query,
            "field": field,
            "result_count": len(matching_logs),
        },
    )
    
    return matching_logs
