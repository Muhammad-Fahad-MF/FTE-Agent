# ADR-010: Log Aggregation

**Date**: 2026-03-19  
**Status**: Proposed  
**Author**: FTE-Agent Team  
**Priority**: Critical

---

## Context

JSON logs need aggregation for centralized monitoring and analysis.

## Options Considered

### Option 1: JSON Logs + Optional Shipper (Recommended)

Local JSON logs with optional cloud shipping.

**Pros**:
- Simple
- Flexible
- Cloud-agnostic
- Efficient storage with compression

**Cons**:
- Manual setup for cloud shipping
- No real-time aggregation without shipper

### Option 2: ELK Stack (Elasticsearch, Logstash, Kibana)

Full ELK stack for log management.

**Pros**:
- Real-time search
- Powerful analytics
- Visualization

**Cons**:
- Complex setup
- Resource intensive
- Cost

### Option 3: Cloud-native (CloudWatch, Stackdriver, Azure Monitor)

Use cloud provider's logging service.

**Pros**:
- Managed service
- Integration with cloud

**Cons**:
- Vendor lock-in
- Cost at scale

## Decision

**Option 1: JSON Logs + Optional Shipper**

Implementation in `src/logging/log_aggregator.py`:
- JSON format with required schema
- Log rotation: Daily or 100MB (whichever first)
- Retention: 7 days INFO, 30 days ERROR/CRITICAL
- Compression: gzip for archived logs
- Optional cloud shipping: AWS S3, GCP Cloud Storage, Azure Blob

## Log Schema

```json
{
  "timestamp": "2026-03-19T10:30:00.123456Z",
  "level": "INFO",
  "component": "gmail_watcher",
  "action": "email_checked",
  "dry_run": false,
  "correlation_id": "abc123",
  "details": {
    "new_emails": 5
  }
}
```

## Consequences

- ✅ Simple and flexible
- ✅ Cloud-agnostic
- ✅ Efficient storage
- ⚠️ Manual cloud shipping setup
- ⚠️ No real-time aggregation without shipper

---

**Review Date**: 2026-07-02  
**Next Action**: Implement as specified
