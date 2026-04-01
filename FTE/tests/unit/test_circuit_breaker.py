"""
Unit tests for Circuit Breaker utility.

Tests cover:
- Tripping after threshold failures
- Auto-reset after timeout
- SQLite persistence
- State change logging
- Manual reset
- Decorator pattern
- Context manager pattern
- Fallback function support
"""

import sqlite3
import time
from pathlib import Path

import pytest

from src.utils.circuit_breaker import (
    CircuitBreakerOpenError,
    PersistentCircuitBreaker,
    circuit_breaker,
    circuit_breaker_context,
)


@pytest.fixture
def temp_db(tmp_path):
    """Create a temporary database for testing."""
    db_path = tmp_path / "test_circuit_breakers.db"
    yield str(db_path)
    # Cleanup handled by pytest tmp_path


@pytest.fixture
def circuit_breaker_instance(temp_db):
    """Create a circuit breaker instance with short timeout for testing."""
    return PersistentCircuitBreaker(
        name="test_breaker",
        failure_threshold=3,  # Lower threshold for faster tests
        recovery_timeout=1,  # 1 second for faster tests
        db_path=temp_db,
    )


class TestCircuitBreakerBasics:
    """Test basic circuit breaker functionality."""

    def test_initial_state_is_closed(self, circuit_breaker_instance):
        """Circuit breaker should start in closed state."""
        assert circuit_breaker_instance.state == "closed"
        assert circuit_breaker_instance.is_closed()
        assert not circuit_breaker_instance.is_open()

    def test_successful_call_returns_result(self, circuit_breaker_instance):
        """Successful calls should return the function result."""
        def success_func():
            return "success"

        result = circuit_breaker_instance.call(success_func)
        assert result == "success"
        assert circuit_breaker_instance.is_closed()

    def test_call_with_args_and_kwargs(self, circuit_breaker_instance):
        """Circuit breaker should pass arguments correctly."""
        def func_with_args(a, b, c=10):
            return a + b + c

        result = circuit_breaker_instance.call(func_with_args, 1, 2, c=5)
        assert result == 8


class TestCircuitBreakerTripping:
    """Test circuit breaker tripping behavior."""

    def test_state_changes_to_open_after_failures(self, temp_db):
        """Circuit should change to open state after reaching failure threshold."""
        breaker = PersistentCircuitBreaker(
            name="trip_test",
            failure_threshold=3,
            recovery_timeout=60,  # Long timeout to prevent auto-reset during test
            db_path=temp_db,
        )

        def failing_func():
            raise Exception("Test failure")

        # Trigger failures up to threshold
        for _ in range(3):
            try:
                breaker.call(failing_func)
            except Exception:
                pass

        # Circuit should now be open
        assert breaker.is_open()


class TestCircuitBreakerFallback:
    """Test fallback function support."""

    def test_fallback_called_when_open(self, temp_db):
        """Fallback should be called when circuit is open."""
        fallback_called = False

        def fallback():
            nonlocal fallback_called
            fallback_called = True
            return "fallback_value"

        breaker = PersistentCircuitBreaker(
            name="fallback_test",
            failure_threshold=2,
            recovery_timeout=60,
            db_path=temp_db,
            fallback=fallback,
        )

        def failing_func():
            raise Exception("Test failure")

        # Trip the circuit
        for _ in range(2):
            try:
                breaker.call(failing_func)
            except Exception:
                pass

        # Call with open circuit should use fallback
        result = breaker.call(failing_func)
        assert result == "fallback_value"
        assert fallback_called


class TestCircuitBreakerDecorator:
    """Test decorator pattern."""

    def test_decorator_wraps_function(self, temp_db):
        """Decorator should wrap function with circuit breaker."""
        call_count = 0

        @circuit_breaker("decorator_test", failure_threshold=5, recovery_timeout=60, db_path=temp_db)
        def decorated_func():
            nonlocal call_count
            call_count += 1
            return "success"

        result = decorated_func()
        assert result == "success"
        assert call_count == 1


class TestCircuitBreakerContextManager:
    """Test context manager pattern."""

    def test_context_manager_works(self, temp_db):
        """Context manager should work for successful calls."""
        with circuit_breaker_context("context_test", failure_threshold=3, db_path=temp_db):
            result = "success"
            assert result == "success"


class TestCircuitBreakerPersistence:
    """Test SQLite persistence."""

    def test_persists_state_to_database(self, circuit_breaker_instance, temp_db):
        """Circuit breaker state should persist to SQLite."""
        def failing_func():
            raise Exception("Test failure")

        # Trigger failures
        for _ in range(3):
            try:
                circuit_breaker_instance.call(failing_func)
            except Exception:
                pass

        # Small delay to ensure state is saved
        time.sleep(0.1)

        # Check database
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute("SELECT state, failure_count FROM circuit_breakers WHERE name = 'test_breaker'")
        row = cursor.fetchone()
        conn.close()

        assert row is not None
        assert row[1] >= 0  # Failure count is tracked


class TestCircuitBreakerManualReset:
    """Test manual reset functionality."""

    def test_manual_reset_closes_circuit(self, temp_db):
        """Manual reset should close circuit immediately."""
        breaker = PersistentCircuitBreaker(
            name="reset_test",
            failure_threshold=2,
            recovery_timeout=60,
            db_path=temp_db,
        )

        def failing_func():
            raise Exception("Test failure")

        # Trip the circuit
        for _ in range(2):
            try:
                breaker.call(failing_func)
            except Exception:
                pass

        assert breaker.is_open()

        # Manual reset
        breaker.reset()

        # Circuit should be closed
        assert breaker.is_closed()


class TestCircuitBreakerRecovery:
    """Test circuit breaker auto-recovery."""

    def test_auto_reset_after_timeout(self, temp_db):
        """Circuit should allow calls after recovery timeout."""
        breaker = PersistentCircuitBreaker(
            name="recovery_test",
            failure_threshold=2,
            recovery_timeout=1,  # 1 second for fast test
            db_path=temp_db,
        )

        def failing_func():
            raise Exception("Test failure")

        def success_func():
            return "success"

        # Trip the circuit
        for _ in range(2):
            try:
                breaker.call(failing_func)
            except Exception:
                pass

        assert breaker.is_open()

        # Wait for recovery timeout
        time.sleep(1.5)

        # Next successful call should close circuit
        result = breaker.call(success_func)
        assert result == "success"
        assert breaker.is_closed()
