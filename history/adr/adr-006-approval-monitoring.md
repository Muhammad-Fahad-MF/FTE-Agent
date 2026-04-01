# ADR-006: Approval Monitoring

**Date**: 2026-03-19  
**Status**: Proposed  
**Author**: FTE-Agent Team

---

## Context

HITL approval workflow requires detecting when users approve/reject actions.

## Options Considered

### Option 1: File System Polling with Fallback (Recommended)

Poll `vault/Pending_Approval/` for file moves.

**Pros**:
- Simple implementation
- Works with any file manager
- No external dependencies

**Cons**:
- 5-second detection delay
- Polling overhead

### Option 2: File System Events (watchdog)

Use file system notifications.

**Pros**:
- Instant detection
- No polling

**Cons**:
- Platform-specific quirks
- More complex

### Option 3: Database Queue

Use SQLite queue for approvals.

**Pros**:
- Transaction support
- Query support

**Cons**:
- Requires DB interaction for users
- Complex UX

## Decision

**Option 1: File System Polling**

- Poll every 5 seconds
- Detect file moves to `Approved/` or `Rejected/`
- Callbacks for approve/reject events
- 24-hour expiry with auto-reject

## Consequences

- ✅ Simple and reliable
- ✅ User-friendly (file move = approval)
- ⚠️ 5-second detection delay (acceptable)

---

**Review Date**: 2026-07-02
