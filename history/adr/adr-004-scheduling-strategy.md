# ADR-004: Scheduling Strategy

**Date**: 2026-03-19  
**Status**: Proposed  
**Author**: FTE-Agent Team

---

## Context

Silver Tier needs scheduled operations (daily briefing at 8 AM, weekly audit on Sunday 10 PM).

## Options Considered

### Option 1: Hybrid (Windows Task Scheduler + Python) (Recommended)

Use OS scheduler for trigger, Python for execution.

**Pros**:
- Reliable OS-level scheduling
- No always-on process
- Works even if app closed

**Cons**:
- Platform-specific setup
- Two configuration points

### Option 2: APScheduler Library

Use Python scheduling library.

**Pros**:
- Cross-platform
- Single codebase

**Cons**:
- Requires always-on process
- Complex persistence

### Option 3: Cron (Linux) / Task Scheduler (Windows)

Use only OS scheduler.

**Pros**:
- Native
- Reliable

**Cons**:
- Platform-specific scripts
- No Python logic

## Decision

**Option 1: Hybrid**

- Daily briefing: Windows Task Scheduler triggers `generate_briefing.py --type daily`
- Weekly audit: Windows Task Scheduler triggers `generate_briefing.py --type weekly`
- Python handles logic, OS handles timing

## Consequences

- ✅ Reliable scheduling
- ✅ No always-on process
- ⚠️ Platform-specific setup scripts

---

**Review Date**: 2026-07-02
