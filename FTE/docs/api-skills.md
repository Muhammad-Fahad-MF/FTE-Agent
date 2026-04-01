# API Skills Documentation: Silver Tier Functional Assistant

**Version**: 2.0.0  
**Last Updated**: 2026-04-02  
**Owner**: FTE-Agent Team  
**Format**: OpenAPI-style Specification

---

## Overview

This document specifies all Python Skills available in the FTE-Agent Silver Tier. Skills are reusable functions that can be called via:
- Direct Python import
- CLI wrappers
- Qwen Code CLI (via subprocess)

All skills follow the **Python Skills Pattern**:
- Type-annotated signatures
- Comprehensive docstrings
- DEV_MODE validation
- `--dry-run` support
- Audit logging
- Error handling with typed exceptions

---

## Table of Contents

1. [Core Skills](#core-skills)
2. [Watcher Skills](#watcher-skills)
3. [Action Skills](#action-skills)
4. [Utility Skills](#utility-skills)
5. [Health Endpoint API](#health-endpoint-api)

---

## Core Skills

### 1.1 `create_action_file`

**Purpose**: Create action file in `vault/Needs_Action/` directory.

**Signature**:
```python
def create_action_file(
    file_type: str,
    source: str,
    content: str = "",
    dry_run: bool = False
) -> str
```

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `file_type` | str | Yes | Type of action: `file_drop`, `email`, `approval_request` |
| `source` | str | Yes | Source path or identifier |
| `content` | str | No | Optional content for action file (default: "") |
| `dry_run` | bool | No | If True, log without creating file (default: False) |

**Returns**: `str` - Path to created (or would-be created) action file

**Raises**:
- `SystemExit`: If DEV_MODE is not set to "true"
- `PermissionError`: If cannot write to vault directory

**Example**:
```python
from src.skills import create_action_file

# Create email action file
path = create_action_file(
    file_type="email",
    source="gmail:18c5f8a2b3d4e5f6",
    content="Urgent: Q2 Budget Review",
    dry_run=False
)
print(f"Created: {path}")

# Dry run
path = create_action_file(
    file_type="approval",
    source="linkedin_post_20260402",
    content="Excited to announce...",
    dry_run=True
)
# Logs: "Would create: vault/Needs_Action/APPROVAL_linkedin_post_20260402.md"
```

**Output Format**:
```markdown
---
type: email
source: gmail:18c5f8a2b3d4e5f6
created: 2026-04-02T10:30:00
status: pending
---

## Content
Urgent: Q2 Budget Review

## Suggested Actions
- [ ] Process this item
- [ ] Move to Done when complete
```

**Acceptance Criteria**:
- [ ] File created in `vault/Needs_Action/` with correct naming convention
- [ ] YAML frontmatter includes all required fields
- [ ] Dry run mode logs without creating file
- [ ] Audit log entry created

---

### 1.2 `log_audit`

**Purpose**: Write audit log entry in JSON format.

**Signature**:
```python
def log_audit(
    action: str,
    details: dict[str, Any],
    level: str = "INFO",
    dry_run: bool = False
) -> None
```

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `action` | str | Yes | Action type: `file_created`, `action_executed`, `approval_granted`, etc. |
| `details` | dict[str, Any] | Yes | Additional context data |
| `level` | str | No | Log level: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL` (default: "INFO") |
| `dry_run` | bool | No | If True, print to stdout instead of file (default: False) |

**Returns**: `None`

**Raises**:
- `SystemExit`: If DEV_MODE is not set

**Example**:
```python
from src.skills import log_audit

# Log action execution
log_audit(
    action="email_sent",
    details={
        "recipient": "user@example.com",
        "subject": "Q2 Budget Review",
        "duration_ms": 245
    },
    level="INFO"
)

# Dry run
log_audit(
    action="test_event",
    details={"test": True},
    dry_run=True
)
# Output: [DRY-RUN] INFO: test_event - {'test': True}
```

**Log Format**:
```json
{
  "timestamp": "2026-04-02T10:30:00.123456Z",
  "level": "INFO",
  "component": "skills",
  "action": "email_sent",
  "dry_run": false,
  "correlation_id": "abc123",
  "details": {
    "recipient": "user@example.com",
    "subject": "Q2 Budget Review",
    "duration_ms": 245
  }
}
```

**Acceptance Criteria**:
- [ ] Log written in JSON format with required schema
- [ ] Correlation ID auto-generated if not provided
- [ ] Dry run prints to stdout
- [ ] Log rotation triggered at 100MB

---

### 1.3 `validate_path`

**Purpose**: Validate path is within vault directory (path traversal prevention).

**Signature**:
```python
def validate_path(file_path: str, vault_path: str) -> str
```

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `file_path` | str | Yes | Path to validate |
| `vault_path` | str | Yes | Base vault directory |

**Returns**: `str` - Validated absolute path

**Raises**:
- `ValueError`: If path is outside vault directory
- `SystemExit`: If DEV_MODE is not set

**Example**:
```python
from src.skills import validate_path

# Valid path
safe_path = validate_path(
    file_path="Needs_Action/email_123.md",
    vault_path="/home/user/FTE/vault"
)
# Returns: "/home/user/FTE/vault/Needs_Action/email_123.md"

# Invalid path (path traversal attempt)
try:
    validate_path(
        file_path="../../etc/passwd",
        vault_path="/home/user/FTE/vault"
    )
except ValueError as e:
    print(f"Blocked: {e}")
    # Output: Blocked: Path must be within vault: ../../etc/passwd
```

**Acceptance Criteria**:
- [ ] Returns absolute path if within vault
- [ ] Raises ValueError if outside vault
- [ ] Handles symlink attacks
- [ ] Works on Windows and Linux paths

---

### 1.4 `create_alert_file`

**Purpose**: Create alert file for critical errors.

**Signature**:
```python
def create_alert_file(
    file_type: str,
    source: str,
    details: dict[str, Any],
    severity: str = "critical"
) -> Path
```

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `file_type` | str | Yes | Alert type: `disk_full`, `security_incident`, `error_threshold` |
| `source` | str | Yes | Source of the alert |
| `details` | dict[str, Any] | Yes | Error details including message and stack trace |
| `severity` | str | No | Alert severity: `critical`, `high`, `medium` (default: "critical") |

**Returns**: `Path` - Path to created alert file

**Raises**:
- `SystemExit`: If DEV_MODE is not set
- `PermissionError`: If cannot write to vault

**Example**:
```python
from src.skills import create_alert_file

# Create disk full alert
alert_path = create_alert_file(
    file_type="disk_full",
    source="filesystem_watcher",
    details={
        "error": "No space left on device",
        "stack_trace": "Traceback...",
        "disk_usage_percent": 98.5
    },
    severity="critical"
)
print(f"Alert created: {alert_path}")
```

**Acceptance Criteria**:
- [ ] Alert file created in `vault/Needs_Action/`
- [ ] YAML frontmatter includes severity and error type
- [ ] Recommended actions section included
- [ ] Audit log entry created with CRITICAL level

---

## Watcher Skills

### 2.1 Gmail Watcher

**Module**: `src.watchers.gmail_watcher`

**Class**: `GmailWatcher(BaseWatcher)`

**Methods**:

#### `check_for_updates() -> list[dict]`

**Purpose**: Query Gmail API for unread/important messages.

**Returns**: List of message dicts with keys: `message_id`, `from`, `to`, `subject`, `date`, `snippet`

**Example**:
```python
from src.watchers.gmail_watcher import GmailWatcher

watcher = GmailWatcher()
messages = watcher.check_for_updates()
for msg in messages:
    print(f"New email: {msg['subject']} from {msg['from']}")
```

**Acceptance Criteria**:
- [ ] Only unread AND important messages returned
- [ ] Processed messages filtered out
- [ ] OAuth2 credentials used for authentication
- [ ] Circuit breaker wraps API calls

---

#### `create_action_file(message: dict) -> str`

**Purpose**: Create action file for new email.

**Parameters**:
| Name | Type | Description |
|------|------|-------------|
| `message` | dict | Email metadata from check_for_updates() |

**Returns**: `str` - Path to created action file

**File Naming**: `EMAIL_<message_id>.md`

**Acceptance Criteria**:
- [ ] File created in `vault/Needs_Action/`
- [ ] YAML frontmatter per spec format
- [ ] Email headers extracted

---

### 2.2 WhatsApp Watcher

**Module**: `src.watchers.whatsapp_watcher`

**Class**: `WhatsAppWatcher(BaseWatcher)`

**Methods**:

#### `check_for_updates() -> list[dict]`

**Purpose**: Scan WhatsApp Web for new messages with keywords.

**Returns**: List of message dicts with keys: `from`, `contact_name`, `message`, `received`, `keywords_matched`

**Example**:
```python
from src.watchers.whatsapp_watcher import WhatsAppWatcher

watcher = WhatsAppWatcher()
messages = watcher.check_for_updates()
for msg in messages:
    print(f"WhatsApp: {msg['message']} (keywords: {msg['keywords_matched']})")
```

**Acceptance Criteria**:
- [ ] Uses Playwright for browser automation
- [ ] Keyword filtering applied
- [ ] Session preserved across restarts

---

### 2.3 FileSystem Watcher

**Module**: `src.filesystem_watcher`

**Class**: `FileSystemWatcher(BaseWatcher)`

**Methods**:

#### `check_for_updates() -> list[dict]`

**Purpose**: Monitor folder for new files.

**Returns**: List of file dicts with keys: `file_path`, `file_type`, `created`, `size_bytes`

**Acceptance Criteria**:
- [ ] Uses watchdog library for file monitoring
- [ ] Circuit breaker wraps file operations
- [ ] Metrics emitted

---

## Action Skills

### 3.1 `send_email`

**Module**: `src.skills.send_email`

**Signature**:
```python
async def send_email(
    to: str,
    subject: str,
    body: str,
    cc: list[str] = None,
    attachments: list[str] = None,
    dry_run: bool = False
) -> dict[str, Any]
```

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `to` | str | Yes | Recipient email address |
| `subject` | str | Yes | Email subject |
| `body` | str | Yes | Email body (plain text or HTML) |
| `cc` | list[str] | No | CC recipients (default: None) |
| `attachments` | list[str] | No | File paths to attach (default: None) |
| `dry_run` | bool | No | If True, log without sending (default: False) |

**Returns**: `dict[str, Any]` with keys: `success`, `message_id`, `error` (if failed)

**Raises**:
- `ValueError`: If email address invalid
- `GmailAPIError`: If Gmail API call fails

**Example**:
```python
from src.skills.send_email import send_email

# Send email
result = await send_email(
    to="user@example.com",
    subject="Q2 Budget Review",
    body="Please find attached...",
    cc=["manager@example.com"],
    attachments=["/path/to/budget.pdf"],
    dry_run=False
)
if result["success"]:
    print(f"Sent: {result['message_id']}")
else:
    print(f"Failed: {result['error']}")

# Dry run
result = await send_email(
    to="newcontact@example.com",  # New contact requires approval
    subject="Test",
    body="Test body",
    dry_run=True
)
# Logs: "Would send email to newcontact@example.com (requires approval)"
```

**Acceptance Criteria**:
- [ ] Email sent via Gmail API
- [ ] Attachments included
- [ ] Dry run logs without sending
- [ ] Approval required for new contacts
- [ ] Circuit breaker wraps API call
- [ ] Metrics emitted

---

### 3.2 `linkedin_posting`

**Module**: `src.skills.linkedin_posting`

**Signature**:
```python
async def linkedin_posting(
    content: str,
    visibility: str = "public",
    dry_run: bool = False
) -> dict[str, Any]
```

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `content` | str | Yes | Post content (max 3000 characters) |
| `visibility` | str | No | Post visibility: `public`, `connections`, `group` (default: "public") |
| `dry_run` | bool | No | If True, log without posting (default: False) |

**Returns**: `dict[str, Any]` with keys: `success`, `post_id`, `error` (if failed)

**Raises**:
- `LinkedInSessionExpired`: If LinkedIn session invalid
- `LinkedInRateLimitExceeded`: If daily post limit reached

**Example**:
```python
from src.skills.linkedin_posting import linkedin_posting

# Post to LinkedIn
result = await linkedin_posting(
    content="Excited to announce our new product launch! 🚀",
    visibility="public",
    dry_run=False
)
if result["success"]:
    print(f"Posted: {result['post_id']}")
else:
    print(f"Failed: {result['error']}")
```

**Acceptance Criteria**:
- [ ] Post created via Playwright
- [ ] Session recovered from storage
- [ ] 1 post/day limit enforced
- [ ] Dry run logs without posting
- [ ] Session expiry detected

---

### 3.3 `create_plan`

**Module**: `src.skills.create_plan`

**Signature**:
```python
def create_plan(
    objective: str,
    source_file: str,
    estimated_steps: int = 10,
    requires_approval: bool = True,
    dry_run: bool = False
) -> dict[str, Any]
```

**Returns**: `dict[str, Any]` with keys: `success`, `plan_path`, `plan_id`, `error` (if failed)

**Example**:
```python
from src.skills.create_plan import create_plan

result = create_plan(
    objective="Respond to urgent email",
    source_file="vault/Needs_Action/EMAIL_123.md",
    estimated_steps=5,
    requires_approval=True
)
```

---

### 3.4 `request_approval`

**Module**: `src.skills.request_approval`

**Signature**:
```python
def request_approval(
    action_type: str,
    action_details: dict[str, Any],
    risk_level: str = "medium",
    reason: str = "",
    dry_run: bool = False
) -> dict[str, Any]
```

**Returns**: `dict[str, Any]` with keys: `success`, `approval_id`, `expires`, `error` (if failed)

**Example**:
```python
from src.skills.request_approval import request_approval

result = request_approval(
    action_type="send_email",
    action_details={"to": "newcontact@example.com", "subject": "Intro"},
    risk_level="medium",
    reason="New contact requires approval per security policy"
)
```

---

### 3.5 `generate_briefing`

**Module**: `src.skills.generate_briefing`

**Signature**:
```python
def generate_briefing(
    briefing_type: str,
    period: str,
    dry_run: bool = False
) -> dict[str, Any]
```

**Parameters**:
- `briefing_type`: `daily` or `weekly`
- `period`: Date range (e.g., "2026-04-01 to 2026-04-02")

**Returns**: `dict[str, Any]` with keys: `success`, `briefing_path`, `summary`, `error` (if failed)

**Example**:
```python
from src.skills.generate_briefing import generate_briefing

# Daily briefing
result = generate_briefing(
    briefing_type="daily",
    period="2026-04-02"
)

# Weekly briefing
result = generate_briefing(
    briefing_type="weekly",
    period="2026-03-27 to 2026-04-02"
)
```

---

## Utility Skills

### 4.1 Circuit Breaker

**Module**: `src.utils.circuit_breaker`

**Class**: `PersistentCircuitBreaker`

**Usage**:
```python
from src.utils.circuit_breaker import PersistentCircuitBreaker

breaker = PersistentCircuitBreaker(
    name="gmail_api",
    failure_threshold=5,
    recovery_timeout=60
)

@breaker
def call_gmail_api():
    # API call that may fail
    pass

try:
    result = call_gmail_api()
except CircuitBreakerError:
    print("Circuit breaker OPEN - failing fast")
```

---

### 4.2 Metrics Collector

**Module**: `src.metrics.collector`

**Class**: `MetricsCollector`

**Usage**:
```python
from src.metrics.collector import MetricsCollector

collector = MetricsCollector()

# Record histogram
collector.record_histogram("api_call_duration", 0.245)

# Increment counter
collector.increment_counter("api_calls_total")

# Set gauge
collector.set_gauge("memory_usage_bytes", 1024 * 1024 * 150)

# Timer context manager
with collector.timer("operation_duration"):
    # Operation
    pass
```

---

### 4.3 Dead Letter Queue

**Module**: `src.utils.dead_letter_queue`

**Class**: `DeadLetterQueue`

**Usage**:
```python
from src.utils.dead_letter_queue import DeadLetterQueue

dlq = DeadLetterQueue()

# Archive failed action
dlq.archive_action(
    original_action={"type": "send_email", "to": "user@example.com"},
    failure_reason="Gmail API timeout",
    details={"retry_count": 3}
)

# Get failed actions
failed = dlq.get_failed_actions(limit=10)

# Reprocess
dlq.reprocess(action_id="abc123")
```

---

## Health Endpoint API

### Base URL

```
http://localhost:8000
```

---

### GET `/health`

**Purpose**: Return overall system health status.

**Response**: `application/json`

**Schema**:
```json
{
  "status": "healthy",
  "timestamp": "2026-04-02T10:30:00Z",
  "version": "2.0.0",
  "uptime_seconds": 86400,
  "components": {
    "gmail_watcher": {"status": "UP", "last_check": "2026-04-02T10:28:00Z"},
    "whatsapp_watcher": {"status": "UP", "last_check": "2026-04-02T10:29:30Z"},
    "filesystem_watcher": {"status": "UP", "last_check": "2026-04-02T10:29:00Z"},
    "process_manager": {"status": "UP"},
    "database": {"status": "UP"}
  },
  "system": {
    "memory_usage_bytes": 524288000,
    "disk_usage_percent": 45.2,
    "cpu_usage_percent": 12.5
  }
}
```

**Status Codes**:
- `200 OK`: System healthy
- `503 Service Unavailable`: One or more components down

**Example**:
```bash
curl http://localhost:8000/health
```

---

### GET `/metrics`

**Purpose**: Return Prometheus-format metrics.

**Response**: `text/plain; version=0.0.4; charset=utf-8`

**Example**:
```
# HELP watcher_check_duration_seconds Time spent checking for updates
# TYPE watcher_check_duration_seconds histogram
watcher_check_duration_seconds_bucket{watcher="gmail",le="0.1"} 45
watcher_check_duration_seconds_bucket{watcher="gmail",le="0.5"} 98
watcher_check_duration_seconds_bucket{watcher="gmail",le="1.0"} 100
watcher_check_duration_seconds_sum{watcher="gmail"} 12.345
watcher_check_duration_seconds_count{watcher="gmail"} 100

# HELP watcher_restart_count Total number of watcher restarts
# TYPE watcher_restart_count counter
watcher_restart_count{watcher="gmail"} 2
watcher_restart_count{watcher="whatsapp"} 1

# HELP memory_usage_bytes Current memory usage
# TYPE memory_usage_bytes gauge
memory_usage_bytes{component="gmail_watcher"} 157286400
```

**Example**:
```bash
curl http://localhost:8000/metrics
```

---

### GET `/ready`

**Purpose**: Return readiness status (all dependencies healthy).

**Response**: `application/json`

**Schema**:
```json
{
  "status": "ready"
}
```

**Status Codes**:
- `200 OK`: All dependencies healthy
- `503 Service Unavailable`: One or more dependencies unhealthy

**Example**:
```bash
curl http://localhost:8000/ready
```

---

## Error Taxonomy

| Error Code | HTTP Status | Description | Resolution |
|------------|-------------|-------------|------------|
| `DEV_MODE_NOT_SET` | 400 | DEV_MODE environment variable not "true" | Set DEV_MODE=true in .env |
| `PATH_TRAVERSAL_DETECTED` | 400 | Path outside vault detected | Use absolute path within vault |
| `CIRCUIT_BREAKER_OPEN` | 503 | Circuit breaker tripped | Wait for recovery or reset manually |
| `SESSION_EXPIRED` | 401 | OAuth2/session token expired | Re-authenticate |
| `RATE_LIMIT_EXCEEDED` | 429 | API rate limit exceeded | Wait for reset or increase quota |
| `APPROVAL_REQUIRED` | 403 | Action requires approval | Submit approval request |
| `APPROVAL_EXPIRED` | 400 | Approval expired (24 hours) | Request new approval |
| `DATABASE_LOCKED` | 503 | SQLite database locked | Retry with backoff |
| `DISK_FULL` | 507 | No space left on device | Clear disk space |

---

## Rate Limiting

| Skill | Limit | Window | Reset |
|-------|-------|--------|-------|
| Gmail API | 100 calls | 1 hour | Rolling window |
| WhatsApp | 60 checks | 1 hour | Rolling window |
| LinkedIn Posting | 1 post | 24 hours | Midnight UTC |
| Health Endpoint | 60 requests | 1 minute | Rolling window |
| Send Email | 50 emails | 1 hour | Rolling window |

---

## Authentication

### OAuth2 (Gmail)

**Setup**:
1. Create project in Google Cloud Console
2. Enable Gmail API
3. Create OAuth2 credentials
4. Download `credentials.json`
5. Run: `python src/watchers/gmail_watcher.py --reauth`

**Token Storage**: `~/.credentials/gmail-token.json`

---

### Session-Based (WhatsApp, LinkedIn)

**Setup**:
1. Run re-auth command
2. Scan QR code (WhatsApp) or login (LinkedIn)
3. Session saved to `vault/<service>_session/storage.json`

**Session Recovery**: Automatic on restart

---

## Versioning

**Current Version**: 2.0.0 (Silver Tier)

**Versioning Strategy**: Semantic Versioning (SemVer)
- MAJOR: Breaking changes (new tier)
- MINOR: New features (backward compatible)
- PATCH: Bug fixes (backward compatible)

**Deprecation Policy**:
- Deprecated features marked in documentation
- 30-day notice before removal
- Migration guide provided

---

## Support

**Documentation**:
- Runbook: `docs/runbook.md`
- Disaster Recovery: `docs/disaster-recovery.md`
- Deployment Checklist: `docs/deployment-checklist.md`

**Contact**:
- Technical Lead: [TBD]
- Email: [TBD]
- Issue Tracker: [TBD]

---

**Revision History**:
| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2026-03-19 | FTE-Agent Team | Initial Bronze tier skills |
| 2.0.0 | 2026-04-02 | FTE-Agent Team | Silver tier: 7+ skills, health endpoint API |

---

**Next Review Date**: 2026-05-02  
**Document Owner**: FTE-Agent Team  
**Approval Status**: ✅ Production Ready
