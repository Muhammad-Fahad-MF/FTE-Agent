"""Retry Handler with exponential backoff.

This module implements retry logic with exponential backoff (1s, 2s, 4s),
maximum 3 retries, typed exception handling, and retry attempt logging.

Usage:
    from src.utils.retry_handler import retry_with_backoff
    
    @retry_with_backoff(max_retries=3)
    def flaky_api_call():
        ...
    
    # Or use directly
    result = retry_with_backoff(my_function, max_retries=3, retryable_exceptions=[ConnectionError])
"""

import logging
import time
from datetime import datetime
from functools import wraps
from pathlib import Path
from typing import Any, Callable, Optional, Type

from ..audit_logger import AuditLogger

logger = logging.getLogger(__name__)


# Default retryable exceptions
DEFAULT_RETRYABLE_EXCEPTIONS = (ConnectionError, TimeoutError, OSError)


class RetryExhaustedError(Exception):
    """Raised when all retry attempts have been exhausted."""

    pass


class RateLimitError(Exception):
    """Raised when rate limit is exceeded."""

    pass


def calculate_delay(attempt: int, base_delay: float = 1.0) -> float:
    """
    Calculate exponential backoff delay.

    Args:
        attempt: Current attempt number (0-indexed).
        base_delay: Base delay in seconds (default: 1.0).

    Returns:
        Delay in seconds: base_delay * 2^attempt (1s, 2s, 4s, 8s, ...)

    Example:
        >>> calculate_delay(0)
        1.0
        >>> calculate_delay(1)
        2.0
        >>> calculate_delay(2)
        4.0
    """
    return base_delay * (2 ** attempt)


def is_retryable_exception(
    exc: Exception,
    retryable_exceptions: tuple[Type[Exception], ...] = DEFAULT_RETRYABLE_EXCEPTIONS,
) -> bool:
    """
    Check if exception is retryable.

    Args:
        exc: Exception to check.
        retryable_exceptions: Tuple of exception types to retry.

    Returns:
        True if exception should trigger retry.

    Example:
        >>> is_retryable_exception(ConnectionError("timeout"))
        True
        >>> is_retryable_exception(ValueError("invalid"))
        False
    """
    return isinstance(exc, retryable_exceptions)


def retry_with_backoff(
    func: Optional[Callable] = None,
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    retryable_exceptions: Optional[tuple[Type[Exception], ...]] = None,
    logger: Optional[AuditLogger] = None,
    on_retry: Optional[Callable[[int, Exception, float], None]] = None,
) -> Callable:
    """
    Retry function with exponential backoff.

    Args:
        func: Function to wrap (for decorator usage).
        max_retries: Maximum number of retry attempts (default: 3).
        base_delay: Base delay in seconds (default: 1.0).
        max_delay: Maximum delay in seconds (default: 60.0).
        retryable_exceptions: Tuple of exception types to retry.
                              Defaults to (ConnectionError, TimeoutError, OSError).
        logger: AuditLogger for logging retry attempts.
        on_retry: Optional callback called on each retry:
                  callback(attempt, exception, delay).

    Returns:
        Wrapped function with retry logic.

    Raises:
        RetryExhaustedError: When all retry attempts are exhausted.

    Example:
        @retry_with_backoff(max_retries=3)
        def flaky_api_call():
            ...
        
        # Or with custom exceptions
        @retry_with_backoff(
            max_retries=5,
            retryable_exceptions=(ConnectionError, RateLimitError)
        )
        def api_call():
            ...
    """
    if retryable_exceptions is None:
        retryable_exceptions = DEFAULT_RETRYABLE_EXCEPTIONS

    def decorator(fn: Callable) -> Callable:
        @wraps(fn)
        def wrapper(*args, **kwargs) -> Any:
            last_exception = None
            component = fn.__name__
            
            # Create logger if not provided
            nonlocal logger
            if logger is None:
                logger = AuditLogger(component=component)

            for attempt in range(max_retries + 1):  # +1 for initial attempt
                try:
                    # Attempt the function call
                    result = fn(*args, **kwargs)
                    
                    # Log success if not first attempt
                    if attempt > 0:
                        logger.log(
                            "INFO",
                            "retry_success",
                            {
                                "function": fn.__name__,
                                "attempt": attempt + 1,
                                "max_retries": max_retries,
                            },
                        )
                    
                    return result

                except Exception as exc:
                    last_exception = exc

                    # Check if exception is retryable
                    if not is_retryable_exception(exc, retryable_exceptions):
                        # Not retryable, re-raise immediately
                        logger.log(
                            "ERROR",
                            "non_retryable_error",
                            {
                                "function": fn.__name__,
                                "error": str(exc),
                                "error_type": type(exc).__name__,
                            },
                        )
                        raise

                    # Check if we have retries left
                    if attempt >= max_retries:
                        # No more retries
                        logger.log(
                            "ERROR",
                            "retry_exhausted",
                            {
                                "function": fn.__name__,
                                "error": str(exc),
                                "error_type": type(exc).__name__,
                                "max_retries": max_retries,
                            },
                        )
                        raise RetryExhaustedError(
                            f"All {max_retries} retry attempts exhausted. "
                            f"Last error: {exc}"
                        ) from exc

                    # Calculate delay with cap
                    delay = min(calculate_delay(attempt, base_delay), max_delay)

                    # Log retry attempt
                    logger.log(
                        "WARNING",
                        "retry_attempt",
                        {
                            "function": fn.__name__,
                            "attempt": attempt + 1,
                            "max_retries": max_retries,
                            "delay": delay,
                            "error": str(exc),
                            "error_type": type(exc).__name__,
                        },
                    )

                    # Call retry callback if provided
                    if on_retry:
                        on_retry(attempt + 1, exc, delay)

                    # Wait before retry
                    time.sleep(delay)

            # Should never reach here, but just in case
            raise RetryExhaustedError(
                f"All retry attempts exhausted for {fn.__name__}"
            ) from last_exception

        return wrapper

    # Handle both @retry_with_backoff and @retry_with_backoff() syntax
    if func is not None and callable(func):
        return decorator(func)

    return decorator


def retry_with_backoff_sync(
    fn: Callable,
    *args,
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    retryable_exceptions: Optional[tuple[Type[Exception], ...]] = None,
    logger: Optional[AuditLogger] = None,
    **kwargs,
) -> Any:
    """
    Execute function with retry and exponential backoff (synchronous).

    This is a convenience function for direct usage rather than as a decorator.

    Args:
        fn: Function to execute.
        *args: Positional arguments for fn.
        max_retries: Maximum number of retry attempts (default: 3).
        base_delay: Base delay in seconds (default: 1.0).
        max_delay: Maximum delay in seconds (default: 60.0).
        retryable_exceptions: Tuple of exception types to retry.
        logger: AuditLogger for logging retry attempts.
        **kwargs: Keyword arguments for fn.

    Returns:
        Result of fn execution.

    Raises:
        RetryExhaustedError: When all retry attempts are exhausted.

    Example:
        result = retry_with_backoff_sync(
            my_api_call,
            "arg1",
            key="value",
            max_retries=5
        )
    """
    decorated = retry_with_backoff(
        max_retries=max_retries,
        base_delay=base_delay,
        max_delay=max_delay,
        retryable_exceptions=retryable_exceptions,
        logger=logger,
    )
    return decorated(fn)(*args, **kwargs)


class RetryHandler:
    """
    Configurable retry handler with state tracking.

    Provides a class-based approach for more complex retry scenarios
    with state tracking and metrics.

    Attributes:
        max_retries: Maximum retry attempts.
        base_delay: Base delay in seconds.
        max_delay: Maximum delay in seconds.
        retryable_exceptions: Exception types to retry.
        logger: Audit logger instance.
    """

    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        retryable_exceptions: Optional[tuple[Type[Exception], ...]] = None,
        logger: Optional[AuditLogger] = None,
    ) -> None:
        """
        Initialize retry handler.

        Args:
            max_retries: Maximum retry attempts (default: 3).
            base_delay: Base delay in seconds (default: 1.0).
            max_delay: Maximum delay in seconds (default: 60.0).
            retryable_exceptions: Exception types to retry.
            logger: Audit logger instance.
        """
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.retryable_exceptions = retryable_exceptions or DEFAULT_RETRYABLE_EXCEPTIONS
        self.logger = logger or AuditLogger(component="RetryHandler")
        
        # State tracking
        self._retry_count = 0
        self._success_count = 0
        self._failure_count = 0

    def execute(
        self,
        fn: Callable,
        *args,
        on_retry: Optional[Callable[[int, Exception, float], None]] = None,
        **kwargs,
    ) -> Any:
        """
        Execute function with retry logic.

        Args:
            fn: Function to execute.
            *args: Positional arguments for fn.
            on_retry: Optional callback on retry.
            **kwargs: Keyword arguments for fn.

        Returns:
            Result of fn execution.

        Raises:
            RetryExhaustedError: When all retry attempts are exhausted.
        """
        self._retry_count += 1

        try:
            result = retry_with_backoff_sync(
                fn,
                *args,
                max_retries=self.max_retries,
                base_delay=self.base_delay,
                max_delay=self.max_delay,
                retryable_exceptions=self.retryable_exceptions,
                logger=self.logger,
                on_retry=on_retry,
                **kwargs,
            )
            self._success_count += 1
            return result

        except RetryExhaustedError:
            self._failure_count += 1
            raise

    def get_stats(self) -> dict[str, int]:
        """
        Get retry statistics.

        Returns:
            Dictionary with retry counts.
        """
        return {
            "total_attempts": self._retry_count,
            "successes": self._success_count,
            "failures": self._failure_count,
        }

    def reset_stats(self) -> None:
        """Reset statistics."""
        self._retry_count = 0
        self._success_count = 0
        self._failure_count = 0
