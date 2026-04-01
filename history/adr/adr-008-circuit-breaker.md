# ADR-008: Circuit Breaker

**Date**: 2026-03-19  
**Status**: Proposed  
**Author**: FTE-Agent Team  
**Priority**: Critical

---

## Context

External API failures must not cascade and bring down the entire system.

## Options Considered

### Option 1: Pybreaker with SQLite Persistence (Recommended)

Use `pybreaker` library with SQLite state persistence.

**Pros**:
- Mature, well-tested library
- SQLite persistence survives restarts
- Configurable threshold and timeout
- Decorator and context manager patterns

**Cons**:
- Additional dependency
- SQLite database management

### Option 2: Custom Implementation

Build our own circuit breaker.

**Pros**:
- Full control
- No external dependency

**Cons**:
- More maintenance
- Reinventing the wheel

### Option 3: Tenacity Retry Only

Use retry library without circuit breaker state.

**Pros**:
- Simple
- Retry logic

**Cons**:
- No circuit breaker state
- No fail-fast

## Decision

**Option 1: Pybreaker with SQLite Persistence**

Implementation in `src/utils/circuit_breaker.py`:
- Failure threshold: 5 consecutive failures
- Recovery timeout: 60 seconds
- State persists to `data/circuit_breakers.db`
- State change logging (WARNING level)
- Decorator and context manager support
- Fallback function support

## Consequences

- ✅ Prevents cascade failures
- ✅ Persists state across restarts
- ✅ Configurable
- ⚠️ Additional dependency
- ⚠️ SQLite database management

---

**Review Date**: 2026-07-02  
**Next Action**: Implement as specified
