# ADR-007: Health Check Endpoint

**Date**: 2026-03-19  
**Status**: Proposed  
**Author**: FTE-Agent Team  
**Priority**: Critical

---

## Context

External monitoring systems need to verify system health. Without this, we rely on user reports to detect failures.

## Options Considered

### Option 1: FastAPI HTTP Endpoint (Recommended)

Lightweight HTTP server on port 8000 with `/health`, `/metrics`, `/ready` endpoints.

**Pros**:
- Industry standard
- Integrates with all monitoring tools (Prometheus, Grafana, uptime monitors)
- Minimal overhead
- Rich ecosystem

**Cons**:
- Additional dependency (FastAPI)
- Port management
- Security considerations

### Option 2: File-Based Health

Write heartbeat file every 30 seconds, external monitor checks file age.

**Pros**:
- Simple
- No network

**Cons**:
- External monitor required
- File system overhead
- Not real-time

### Option 3: WebSocket Push

Push health status to monitoring service.

**Pros**:
- Real-time
- Push-based

**Cons**:
- Complex
- Requires monitoring service

## Decision

**Option 1: FastAPI HTTP Endpoint**

Implementation in `src/api/health_endpoint.py`:
- `GET /health` - Overall system status
- `GET /metrics` - Prometheus-format metrics
- `GET /ready` - Readiness check
- Rate limiting (60 requests/minute)
- Optional authentication token

## Production Requirements

- Run on localhost:8000 by default
- Authentication token for /metrics (optional)
- Rate limiting (max 60 requests/minute)
- Timeout (max 5 seconds per request)

## Consequences

- ✅ Standard integration
- ✅ Real-time monitoring
- ✅ Alerting support
- ⚠️ Additional dependency
- ⚠️ Port management

---

**Review Date**: 2026-07-02  
**Next Action**: Implement as specified
