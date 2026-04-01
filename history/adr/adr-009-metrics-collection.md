# ADR-009: Metrics Collection

**Date**: 2026-03-19  
**Status**: Proposed  
**Author**: FTE-Agent Team  
**Priority**: Critical

---

## Context

Production systems require quantitative metrics for monitoring and alerting.

## Options Considered

### Option 1: Prometheus Client + SQLite (Recommended)

Use `prometheus_client` with SQLite persistence.

**Pros**:
- Industry standard
- Powerful querying (PromQL)
- Historical analysis
- Grafana integration

**Cons**:
- Additional infrastructure
- Database management

### Option 2: Custom Metrics System

Build our own metrics collection.

**Pros**:
- Full control
- No external dependency

**Cons**:
- More maintenance
- Limited querying

### Option 3: StatsD

Use StatsD protocol.

**Pros**:
- Simple
- Widely supported

**Cons**:
- No persistence
- Aggregation required

## Decision

**Option 1: Prometheus Client + SQLite**

Implementation in `src/metrics/collector.py`:
- Histogram: `watcher_check_duration_seconds`
- Counter: `watcher_restart_count`
- Gauge: `memory_usage_bytes`
- Timer context manager
- SQLite persistence to `data/metrics.db`
- `/metrics` endpoint with Prometheus format

## Metrics Tracked

- `watcher_check_duration_seconds` (histogram)
- `action_file_creation_latency_seconds` (histogram)
- `approval_detection_latency_seconds` (histogram)
- `api_call_duration_seconds` (histogram)
- `watcher_restart_count` (counter)
- `memory_usage_bytes` (gauge)
- `error_count` (counter)

## Consequences

- ✅ Industry standard
- ✅ Powerful querying
- ✅ Historical analysis
- ⚠️ Additional infrastructure
- ⚠️ Database management

---

**Review Date**: 2026-07-02  
**Next Action**: Implement as specified
