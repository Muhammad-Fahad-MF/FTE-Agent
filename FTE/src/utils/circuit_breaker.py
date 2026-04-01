"""
Circuit Breaker Utility with SQLite Persistence.

Implements the circuit breaker pattern to prevent cascade failures in external API calls.
State persists to SQLite database for crash recovery.

Usage:
    # As a decorator
    @circuit_breaker("gmail_api")
    def call_gmail_api():
        ...

    # As a context manager
    with CircuitBreaker("whatsapp_api"):
        ...

    # With fallback
    @circuit_breaker("external_service", fallback=lambda: default_value)
    def call_external_service():
        ...
"""

import logging
import sqlite3
import threading
from contextlib import contextmanager
from datetime import datetime
from functools import wraps
from pathlib import Path
from typing import Any, Callable, Optional

import pybreaker

logger = logging.getLogger(__name__)

# Thread-local storage for metrics callbacks
_local = threading.Lock()


class CircuitBreakerError(Exception):
    """Base exception for circuit breaker errors."""

    pass


class CircuitBreakerOpenError(CircuitBreakerError):
    """Raised when circuit breaker is open and call is rejected."""

    pass


class StateChangeListener:
    """Listener for pybreaker state changes."""

    def __init__(self, on_state_change_callback):
        self.on_state_change_callback = on_state_change_callback
        self.last_state = "closed"

    def before_call(self, breaker, func, *args, **kwargs):
        """Called before each function call."""
        pass

    def state_change(self, breaker, old_state, new_state):
        """Called when state changes."""
        self.on_state_change_callback(old_state, new_state)

    def success(self, breaker, *args, **kwargs):
        """Called on successful call."""
        pass

    def failure(self, breaker, *args, **kwargs):
        """Called on failure."""
        pass


class PersistentCircuitBreaker:
    """
    Circuit breaker with SQLite persistence for crash recovery.

    Attributes:
        name: Unique identifier for this circuit breaker
        failure_threshold: Number of consecutive failures before opening
        recovery_timeout: Seconds to wait before attempting recovery
        db_path: Path to SQLite database for persistence
    """

    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        db_path: Optional[str] = None,
        fallback: Optional[Callable] = None,
    ):
        """
        Initialize circuit breaker.

        Args:
            name: Unique identifier for this circuit breaker
            failure_threshold: Number of consecutive failures before opening (default: 5)
            recovery_timeout: Seconds to wait before attempting recovery (default: 60)
            db_path: Path to SQLite database (default: data/circuit_breakers.db)
            fallback: Optional fallback function to call when circuit is open
        """
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.fallback = fallback
        self.db_path = db_path or str(Path(__file__).parent.parent / "data" / "circuit_breakers.db")

        self._lock = threading.Lock()
        self._metrics_callbacks: list[Callable] = []

        # Initialize database
        self._init_db()

        # Load persisted state
        persisted_state = self._load_state()
        initial_failures = persisted_state.get("failure_count", 0) if persisted_state else 0

        # Create pybreaker instance
        self._breaker = pybreaker.CircuitBreaker(
            fail_max=failure_threshold,
            reset_timeout=recovery_timeout,
            name=name,
        )

        # Restore failure count if persisted
        if initial_failures > 0:
            # pybreaker doesn't support setting failure count directly
            # We track it in our own state
            self._persisted_failure_count = initial_failures
        else:
            self._persisted_failure_count = 0

        # Register state change listener
        self._listener = StateChangeListener(self._on_state_change)
        self._breaker.add_listener(self._listener)

        logger.debug(f"CircuitBreaker '{name}' initialized (threshold={failure_threshold}, timeout={recovery_timeout}s)")

    def _init_db(self) -> None:
        """Initialize SQLite database schema."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS circuit_breakers (
                    name TEXT PRIMARY KEY,
                    state TEXT NOT NULL,
                    failure_count INTEGER DEFAULT 0,
                    last_failure_time TIMESTAMP,
                    last_state_change TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
            )
            conn.commit()
            conn.close()
        except sqlite3.Error as e:
            logger.error(f"Failed to initialize circuit breaker database: {e}")
            raise CircuitBreakerError(f"Database initialization failed: {e}")

    def _load_state(self) -> Optional[dict[str, Any]]:
        """Load circuit breaker state from database."""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM circuit_breakers WHERE name = ?",
                (self.name,),
            )
            row = cursor.fetchone()
            conn.close()

            if row:
                return dict(row)
            return None
        except sqlite3.Error as e:
            logger.warning(f"Failed to load circuit breaker state: {e}")
            return None

    def _save_state(
        self,
        state: str,
        failure_count: int,
        last_failure_time: Optional[datetime] = None,
    ) -> None:
        """Save circuit breaker state to database."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT OR REPLACE INTO circuit_breakers
                (name, state, failure_count, last_failure_time, last_state_change, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """,
                (
                    self.name,
                    state,
                    failure_count,
                    last_failure_time or datetime.now(),
                    datetime.now(),
                    datetime.now(),
                ),
            )
            conn.commit()
            conn.close()
        except sqlite3.Error as e:
            logger.error(f"Failed to save circuit breaker state: {e}")

    def _on_state_change(self, old_state: str, new_state: str) -> None:
        """
        Handle circuit breaker state changes.

        States: CLOSED (normal) → OPEN (tripped) → HALF_OPEN (testing) → CLOSED (recovered)
        """
        logger.warning(
            f"CircuitBreaker '{self.name}' state change: {old_state} → {new_state}",
            extra={
                "circuit_breaker": self.name,
                "old_state": old_state,
                "new_state": new_state,
            },
        )

        # Persist state change
        self._save_state(new_state, self._persisted_failure_count)

        # Emit metrics
        self._emit_metrics("circuit_breaker_state_change_count", tags={"name": self.name, "state": new_state})

    def _emit_metrics(self, metric_name: str, value: float = 1.0, tags: Optional[dict[str, str]] = None) -> None:
        """Emit metrics (callback-based for decoupling)."""
        for callback in self._metrics_callbacks:
            try:
                callback(metric_name, value, tags)
            except Exception as e:
                logger.debug(f"Metrics callback failed: {e}")

    def register_metrics_callback(self, callback: Callable) -> None:
        """
        Register a callback for metrics emission.

        Args:
            callback: Function(metric_name, value, tags) to receive metrics
        """
        self._metrics_callbacks.append(callback)

    @property
    def state(self) -> str:
        """Get current circuit breaker state (CLOSED, OPEN, HALF_OPEN)."""
        return self._breaker.current_state

    @property
    def failure_count(self) -> int:
        """Get current failure count."""
        return self._persisted_failure_count

    def call(self, func: Callable, *args: Any, **kwargs: Any) -> Any:
        """
        Execute function with circuit breaker protection.

        Args:
            func: Function to execute
            *args: Positional arguments for func
            **kwargs: Keyword arguments for func

        Returns:
            Result of func execution or fallback

        Raises:
            CircuitBreakerOpenError: If circuit is open and no fallback provided
            Exception: Any exception from func (may trip breaker)
        """
        try:

            def wrapped_func() -> Any:
                result = func(*args, **kwargs)
                # Reset failure count on success
                with self._lock:
                    self._persisted_failure_count = 0
                    self._save_state(self.state, 0)
                return result

            return self._breaker.call(wrapped_func)

        except pybreaker.CircuitBreakerError:
            logger.warning(
                f"CircuitBreaker '{self.name}' is OPEN - rejecting call",
                extra={"circuit_breaker": self.name},
            )
            self._emit_metrics("circuit_breaker_rejection_count", tags={"name": self.name})

            if self.fallback:
                logger.info(f"Using fallback for circuit breaker '{self.name}'")
                return self.fallback()

            raise CircuitBreakerOpenError(f"Circuit breaker '{self.name}' is open")

        except Exception as e:
            # Increment failure count
            with self._lock:
                self._persisted_failure_count += 1
                self._save_state(self.state, self._persisted_failure_count, datetime.now())

            logger.warning(
                f"CircuitBreaker '{self.name}' caught exception: {type(e).__name__}: {e}",
                extra={"circuit_breaker": self.name, "error": str(e)},
            )
            raise

    def __call__(self, func: Callable) -> Callable:
        """
        Decorator usage: @circuit_breaker("name").

        Args:
            func: Function to decorate

        Returns:
            Wrapped function with circuit breaker protection
        """

        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            return self.call(func, *args, **kwargs)

        return wrapper

    def reset(self) -> None:
        """
        Manually reset circuit breaker to CLOSED state.

        Use this to manually recover after fixing underlying issues.
        """
        logger.info(f"Manually resetting circuit breaker '{self.name}'")
        self._breaker.close()
        with self._lock:
            self._persisted_failure_count = 0
        self._save_state("closed", 0)
        self._emit_metrics("circuit_breaker_manual_reset_count", tags={"name": self.name})

    def is_closed(self) -> bool:
        """Check if circuit breaker is closed (normal operation)."""
        return self.state == "closed"

    def is_open(self) -> bool:
        """Check if circuit breaker is open (rejecting calls)."""
        return self.state == "open"

    def is_half_open(self) -> bool:
        """Check if circuit breaker is half-open (testing recovery)."""
        return self.state == "half_open"


@contextmanager
def circuit_breaker_context(name: str, **kwargs: Any):
    """
    Context manager for circuit breaker protection.

    Usage:
        with circuit_breaker_context("gmail_api"):
            call_gmail_api()

    Args:
        name: Circuit breaker name
        **kwargs: Arguments for PersistentCircuitBreaker
    """
    breaker = PersistentCircuitBreaker(name, **kwargs)
    try:
        yield breaker
    except CircuitBreakerOpenError:
        raise
    except Exception as e:
        logger.warning(f"Circuit breaker '{name}' caught exception: {e}")
        raise


# Global registry for easy access to circuit breakers
_circuit_breakers: dict[str, PersistentCircuitBreaker] = {}
_registry_lock = threading.Lock()


def get_circuit_breaker(
    name: str,
    failure_threshold: int = 5,
    recovery_timeout: int = 60,
    fallback: Optional[Callable] = None,
    db_path: Optional[str] = None,
) -> PersistentCircuitBreaker:
    """
    Get or create a circuit breaker from the global registry.

    Args:
        name: Unique circuit breaker name
        failure_threshold: Failures before opening (default: 5)
        recovery_timeout: Seconds before recovery attempt (default: 60)
        fallback: Optional fallback function
        db_path: Optional database path (default: data/circuit_breakers.db)

    Returns:
        PersistentCircuitBreaker instance
    """
    with _registry_lock:
        if name not in _circuit_breakers:
            _circuit_breakers[name] = PersistentCircuitBreaker(
                name=name,
                failure_threshold=failure_threshold,
                recovery_timeout=recovery_timeout,
                fallback=fallback,
                db_path=db_path,
            )
        return _circuit_breakers[name]


def circuit_breaker(
    name: str,
    failure_threshold: int = 5,
    recovery_timeout: int = 60,
    fallback: Optional[Callable] = None,
    db_path: Optional[str] = None,
) -> Callable:
    """
    Decorator for circuit breaker protection.

    Usage:
        @circuit_breaker("gmail_api", failure_threshold=3)
        def call_gmail():
            ...

    Args:
        name: Circuit breaker name
        failure_threshold: Failures before opening (default: 5)
        recovery_timeout: Seconds before recovery attempt (default: 60)
        fallback: Optional fallback function
        db_path: Optional database path (default: data/circuit_breakers.db)

    Returns:
        Decorated function with circuit breaker protection
    """
    breaker = PersistentCircuitBreaker(
        name=name,
        failure_threshold=failure_threshold,
        recovery_timeout=recovery_timeout,
        fallback=fallback,
        db_path=db_path,
    )

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            return breaker.call(func, *args, **kwargs)

        return wrapper

    return decorator
