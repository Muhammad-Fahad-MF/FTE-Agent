# ADR-001: Watcher Process Management

**Date**: 2026-03-19  
**Status**: Proposed  
**Author**: FTE-Agent Team  
**Branch**: `002-silver-tier-functional-assistant`

---

## Context

The FTE-Agent needs to run multiple watchers (Gmail, WhatsApp, FileSystem) continuously. We need a strategy to manage these processes, detect failures, and ensure high availability.

## Problem

How do we manage watcher processes to ensure:
- Continuous operation (24/7 monitoring)
- Automatic recovery from crashes
- Resource monitoring (memory, CPU)
- Graceful shutdown on demand

## Options Considered

### Option 1: Subprocess with Health Monitoring (Recommended)

Launch each watcher as a separate subprocess and monitor health via PID checks.

**Pros**:
- Process isolation (crash in one doesn't affect others)
- Easy to monitor via PID
- Can restart individual watchers
- Memory monitoring per process

**Cons**:
- Inter-process communication complexity
- Resource overhead for multiple processes

### Option 2: Threading

Run each watcher in a separate thread within the same process.

**Pros**:
- Shared memory space
- Easy communication between watchers
- Lower resource overhead

**Cons**:
- Single point of failure (one crash kills all)
- Harder to isolate resource usage
- GIL limitations in Python

### Option 3: AsyncIO Tasks

Run each watcher as an async task.

**Pros**:
- Lightweight
- Easy to coordinate
- Single process

**Cons**:
- Blocking operation in one watcher affects all
- Complex error handling
- No process isolation

## Decision

**Option 1: Subprocess with Health Monitoring**

We chose subprocess-based process management with the following features:
- `ProcessManager` class in `src/process_manager.py`
- Health checks every 10 seconds via `process.poll()`
- Auto-restart within 10 seconds of crash detection
- Restart limits (max 3/hour per watcher)
- Memory monitoring via `psutil` (kill if >200MB)
- Graceful shutdown via SIGTERM → SIGKILL

## Implementation

```python
# src/process_manager.py
class ProcessManager:
    def __init__(self):
        self.watchers = {}
        self._restart_counts = defaultdict(int)
    
    def start_all_watchers(self):
        """Launch gmail_watcher.py, whatsapp_watcher.py, filesystem_watcher.py"""
        pass
    
    def _check_watcher_health(self, name: str) -> bool:
        """Check if watcher is running via process.poll()"""
        pass
    
    def _restart_watcher(self, name: str):
        """Restart crashed watcher with rate limiting"""
        pass
```

## Consequences

### Positive
- High availability (auto-recovery)
- Process isolation
- Resource monitoring
- Graceful degradation

### Negative
- More complex architecture
- IPC required for coordination
- Higher memory footprint

## Compliance

- **Constitution IV**: Testable via `test_process_manager.py`
- **Constitution VIII**: Typed exceptions (`ProcessManagerError`)
- **Constitution V**: Metrics emitted (`process_manager_watcher_restarts`)

---

**Review Date**: 2026-07-02  
**Next Action**: Implement as specified
