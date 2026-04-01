"""
Graceful Degradation Utilities.

Provides fallback mechanisms and error handling to ensure partial failures
don't halt the entire system.

Features:
- In-memory fallback for SQLite failures
- Memory queue for file write failures
- Error dict returns instead of exceptions (for skills)
- Component health tracking
- DEV_MODE validation
- Circuit breaker isolation

Usage:
    from src.utils.graceful_degradation import GracefulDegradationManager

    manager = GracefulDegradationManager()
    
    # Use SQLite with fallback
    result = manager.execute_with_fallback(
        primary_fn=sqlite_operation,
        fallback_fn=memory_operation,
        default_value={}
    )
    
    # Check component health
    health = manager.get_component_health()
"""

import logging
import sqlite3
import threading
import time
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Optional

logger = logging.getLogger(__name__)


class ComponentStatus(Enum):
    """Component health status."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class ComponentHealth:
    """Health status for a component."""
    name: str
    status: ComponentStatus = ComponentStatus.UNKNOWN
    last_check: Optional[datetime] = None
    error_count: int = 0
    last_error: Optional[str] = None
    fallback_active: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)


class GracefulDegradationError(Exception):
    """Base exception for graceful degradation errors."""
    pass


class FallbackNotAvailableError(GracefulDegradationError):
    """Raised when fallback mechanism is not available."""
    pass


class GracefulDegradationManager:
    """
    Manages graceful degradation across all components.
    
    Features:
    - Component health tracking
    - In-memory fallback for database failures
    - Memory queue for file write failures
    - Error dict returns for skills
    - DEV_MODE validation
    """
    
    def __init__(self) -> None:
        """Initialize degradation manager."""
        self._lock = threading.Lock()
        self._components: dict[str, ComponentHealth] = {}
        
        # In-memory storage for SQLite fallback
        self._memory_store: dict[str, Any] = {}
        self._memory_store_enabled = False
        
        # Memory queue for file writes
        self._file_write_queue: deque = deque(maxlen=1000)
        self._file_queue_enabled = False
        
        # Error tracking
        self._error_counts: dict[str, int] = {}
        self._error_window_start = time.time()
        self._error_window_seconds = 3600  # 1 hour
        
        # DEV_MODE flag
        self._dev_mode = False
        
        # Initialize default components
        self._init_default_components()
    
    def _init_default_components(self) -> None:
        """Initialize default component health tracking."""
        default_components = [
            "sqlite_database",
            "file_system",
            "metrics_collector",
            "external_api",
            "watcher_gmail",
            "watcher_whatsapp",
            "watcher_filesystem",
            "approval_handler",
            "dlq",
            "health_endpoint",
        ]
        
        for name in default_components:
            self._components[name] = ComponentHealth(name=name)
    
    def set_dev_mode(self, enabled: bool) -> None:
        """
        Enable or disable DEV_MODE.
        
        When enabled, external actions are prevented but operations
        return success with dry_run=True.
        
        Args:
            enabled: True to enable DEV_MODE
        """
        self._dev_mode = enabled
        logger.info(f"DEV_MODE {'enabled' if enabled else 'disabled'}")
    
    def is_dev_mode(self) -> bool:
        """Check if DEV_MODE is enabled."""
        return self._dev_mode
    
    def get_component_health(self, component_name: Optional[str] = None) -> dict[str, Any]:
        """
        Get health status for component(s).
        
        Args:
            component_name: Optional specific component name
            
        Returns:
            Dict with health status
        """
        with self._lock:
            if component_name:
                if component_name not in self._components:
                    return {"status": "unknown", "error": f"Component {component_name} not found"}
                health = self._components[component_name]
                return self._health_to_dict(health)
            
            # Return all components
            return {
                name: self._health_to_dict(health)
                for name, health in self._components.items()
            }
    
    def _health_to_dict(self, health: ComponentHealth) -> dict[str, Any]:
        """Convert ComponentHealth to dict."""
        return {
            "status": health.status.value,
            "last_check": health.last_check.isoformat() if health.last_check else None,
            "error_count": health.error_count,
            "last_error": health.last_error,
            "fallback_active": health.fallback_active,
            "metadata": health.metadata,
        }
    
    def set_component_status(
        self,
        component_name: str,
        status: ComponentStatus,
        error: Optional[str] = None,
        fallback_active: bool = False,
        metadata: Optional[dict[str, Any]] = None,
    ) -> None:
        """
        Set component health status.
        
        Args:
            component_name: Name of component
            status: Health status
            error: Optional error message
            fallback_active: Whether fallback is active
            metadata: Optional additional metadata
        """
        with self._lock:
            if component_name not in self._components:
                self._components[component_name] = ComponentHealth(name=component_name)
            
            health = self._components[component_name]
            health.status = status
            health.last_check = datetime.now()
            
            if error:
                health.last_error = error
                health.error_count += 1
            
            health.fallback_active = fallback_active
            
            if metadata:
                health.metadata.update(metadata)
            
            logger.debug(f"Component {component_name} status: {status.value}")
    
    def record_error(self, component_name: str, error: str) -> None:
        """
        Record an error for a component.
        
        Args:
            component_name: Component name
            error: Error message
        """
        with self._lock:
            key = f"{component_name}:{self._error_window_start}"
            self._error_counts[key] = self._error_counts.get(key, 0) + 1
            
            # Update component status
            if component_name in self._components:
                self._components[component_name].last_error = error
                self._components[component_name].error_count += 1
    
    def get_error_rate(self, component_name: Optional[str] = None) -> int:
        """
        Get error count in current window.
        
        Args:
            component_name: Optional specific component
            
        Returns:
            Error count in current window
        """
        current_time = time.time()
        
        # Reset window if expired
        if current_time - self._error_window_start > self._error_window_seconds:
            self._error_counts.clear()
            self._error_window_start = current_time
        
        with self._lock:
            if component_name:
                key = f"{component_name}:{self._error_window_start}"
                return self._error_counts.get(key, 0)
            
            return sum(self._error_counts.values())
    
    # SQLite Fallback
    
    def enable_memory_fallback(self) -> None:
        """Enable in-memory fallback for SQLite failures."""
        self._memory_store_enabled = True
        logger.info("Memory fallback enabled for SQLite failures")
    
    def disable_memory_fallback(self) -> None:
        """Disable in-memory fallback."""
        self._memory_store_enabled = False
        self._memory_store.clear()
        logger.info("Memory fallback disabled")
    
    def execute_with_fallback(
        self,
        primary_fn: Callable[[], Any],
        fallback_fn: Optional[Callable[[], Any]] = None,
        default_value: Any = None,
        component_name: str = "sqlite_database",
    ) -> Any:
        """
        Execute primary function with fallback on failure.
        
        Args:
            primary_fn: Primary function to execute
            fallback_fn: Optional fallback function
            default_value: Default value if both fail
            component_name: Component name for health tracking
            
        Returns:
            Result from primary, fallback, or default value
        """
        try:
            result = primary_fn()
            # Success - update health
            self.set_component_status(component_name, ComponentStatus.HEALTHY)
            return result
            
        except sqlite3.OperationalError as e:
            # SQLite failure
            self.record_error(component_name, str(e))
            logger.warning(f"SQLite failure, attempting fallback: {e}")
            
            # Try fallback
            if self._memory_store_enabled and fallback_fn:
                try:
                    result = fallback_fn()
                    self.set_component_status(
                        component_name,
                        ComponentStatus.DEGRADED,
                        fallback_active=True,
                    )
                    return result
                except Exception as fallback_error:
                    logger.error(f"Fallback also failed: {fallback_error}")
            
            # Set unhealthy if no fallback
            self.set_component_status(
                component_name,
                ComponentStatus.UNHEALTHY,
                error=str(e),
                fallback_active=False,
            )
            
            return default_value
            
        except Exception as e:
            # Other errors
            self.record_error(component_name, str(e))
            self.set_component_status(component_name, ComponentStatus.UNHEALTHY, error=str(e))
            return default_value
    
    def memory_store_set(self, key: str, value: Any) -> bool:
        """
        Set value in memory store (SQLite fallback).
        
        Args:
            key: Storage key
            value: Value to store
            
        Returns:
            True if successful
        """
        if not self._memory_store_enabled:
            return False
        
        self._memory_store[key] = value
        return True
    
    def memory_store_get(self, key: str, default: Any = None) -> Any:
        """
        Get value from memory store.
        
        Args:
            key: Storage key
            default: Default value if not found
            
        Returns:
            Stored value or default
        """
        return self._memory_store.get(key, default)
    
    # File Write Queue
    
    def enable_file_queue(self) -> None:
        """Enable memory queue for file write failures."""
        self._file_queue_enabled = True
        logger.info("File write queue enabled")
    
    def disable_file_queue(self) -> None:
        """Disable file write queue."""
        self._file_queue_enabled = False
        self._file_write_queue.clear()
        logger.info("File write queue disabled")
    
    def write_file_with_queue(
        self,
        file_path: Path,
        content: str,
        mode: str = "w",
    ) -> bool:
        """
        Write file with queue fallback on failure.
        
        Args:
            file_path: Target file path
            content: Content to write
            mode: File mode (default: "w")
            
        Returns:
            True if written to file, False if queued
        """
        try:
            file_path.write_text(content, encoding="utf-8")
            self.set_component_status("file_system", ComponentStatus.HEALTHY)
            return True
            
        except (IOError, OSError, PermissionError) as e:
            self.record_error("file_system", str(e))
            logger.warning(f"File write failed, queuing: {e}")
            
            if self._file_queue_enabled:
                self._file_write_queue.append({
                    "path": str(file_path),
                    "content": content,
                    "mode": mode,
                    "timestamp": datetime.now().isoformat(),
                })
                self.set_component_status(
                    "file_system",
                    ComponentStatus.DEGRADED,
                    fallback_active=True,
                )
                return False
            
            self.set_component_status("file_system", ComponentStatus.UNHEALTHY, error=str(e))
            return False
    
    def flush_file_queue(self) -> tuple[int, int]:
        """
        Flush queued file writes.
        
        Returns:
            Tuple of (success_count, failure_count)
        """
        success = 0
        failure = 0
        
        while self._file_write_queue:
            item = self._file_write_queue.popleft()
            try:
                path = Path(item["path"])
                path.write_text(item["content"], encoding="utf-8")
                success += 1
            except Exception as e:
                logger.error(f"Failed to flush queued file {item['path']}: {e}")
                failure += 1
                # Re-queue failed items
                self._file_write_queue.append(item)
        
        if failure == 0:
            self.set_component_status("file_system", ComponentStatus.HEALTHY)
        
        return success, failure
    
    def get_queue_size(self) -> int:
        """Get current file queue size."""
        return len(self._file_write_queue)
    
    # Skill Error Dict Helper
    
    def create_error_dict(
        self,
        error: Exception,
        action: str,
        details: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """
        Create standardized error dict for skill returns.
        
        Args:
            error: Exception that occurred
            action: Action name
            details: Optional additional details
            
        Returns:
            Error dict with status, error, action, details
        """
        return {
            "status": "error",
            "error": str(error),
            "error_type": type(error).__name__,
            "action": action,
            "details": details or {},
            "timestamp": datetime.now().isoformat(),
            "dev_mode": self._dev_mode,
        }
    
    def create_success_dict(
        self,
        action: str,
        result: Any = None,
        details: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """
        Create standardized success dict for skill returns.
        
        Args:
            action: Action name
            result: Optional result data
            details: Optional additional details
            
        Returns:
            Success dict with status, action, result, details
        """
        return {
            "status": "success",
            "action": action,
            "result": result,
            "details": details or {},
            "timestamp": datetime.now().isoformat(),
            "dev_mode": self._dev_mode,
        }
    
    # Overall System Health
    
    def get_overall_status(self) -> str:
        """
        Get overall system health status.
        
        Returns:
            "healthy", "degraded", or "unhealthy"
        """
        with self._lock:
            statuses = [h.status for h in self._components.values()]
            
            if all(s == ComponentStatus.HEALTHY for s in statuses):
                return "healthy"
            
            if any(s == ComponentStatus.UNHEALTHY for s in statuses):
                return "unhealthy"
            
            if any(s in [ComponentStatus.DEGRADED, ComponentStatus.UNKNOWN] for s in statuses):
                return "degraded"
            
            return "unknown"


# Global instance
_degradation_manager: Optional[GracefulDegradationManager] = None


def get_degradation_manager() -> GracefulDegradationManager:
    """Get or create global degradation manager instance."""
    global _degradation_manager
    if _degradation_manager is None:
        _degradation_manager = GracefulDegradationManager()
    return _degradation_manager
