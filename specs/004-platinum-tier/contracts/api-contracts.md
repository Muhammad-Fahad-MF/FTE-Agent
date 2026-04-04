# API Contracts: Platinum Tier - Cloud + Local Executive

**Feature**: Platinum Tier (v6.0.0)
**Branch**: `004-platinum-tier-cloud-executive`
**Date**: 2026-04-02
**Status**: Draft

---

## Overview

This document defines the API contracts for Platinum Tier's external interfaces. The architecture uses file-based communication (vault sync) for Cloud/Local coordination, with HTTP APIs for health monitoring and external integrations.

**API Categories**:
1. **Health Endpoint API** (Cloud VM monitoring)
2. **Vault File Contracts** (Cloud/Local sync)
3. **External API Integrations** (Gmail, WhatsApp, Odoo, Social Media)
4. **Internal Python Skills** (Reusable functions)

---

## 1. Health Endpoint API (Cloud VM)

### Base URL
```
http://<cloud-vm-ip>:8000
```

### Authentication
None (internal monitoring only, firewall-restricted)

### Endpoints

#### GET /health

**Description**: Return health status, uptime, and resource metrics.

**Request**:
```http
GET /health HTTP/1.1
Host: <cloud-vm-ip>:8000
```

**Response** (200 OK):
```json
{
  "status": "healthy|degraded|unhealthy",
  "uptime_seconds": 86400,
  "resources": {
    "cpu_percent": 45.2,
    "memory_percent": 62.5,
    "disk_percent": 71.0
  },
  "watchers": {
    "gmail": "running|stopped|error",
    "whatsapp": "running|stopped|error",
    "filesystem": "running|stopped|error"
  },
  "last_sync": "2026-04-02T08:15:30Z",
  "sync_status": "synced|syncing|failed|conflict"
}
```

**Status Codes**:
- `200 OK`: Health check successful
- `503 Service Unavailable`: Agent unhealthy (disk >90% or crash)

**Performance Budget**:
- Response time: <500ms (p95)
- Availability: 99% over 30-day period

**Error Response**:
```json
{
  "error": "unhealthy",
  "reason": "disk_usage_critical",
  "details": {
    "disk_percent": 92.5,
    "threshold": 90
  }
}
```

---

#### GET /metrics

**Description**: Prometheus-compatible metrics endpoint (optional, advanced monitoring).

**Request**:
```http
GET /metrics HTTP/1.1
Host: <cloud-vm-ip>:8000
Accept: text/plain
```

**Response** (200 OK, Prometheus format):
```plaintext
# HELP fte_uptime_seconds Agent uptime in seconds
# TYPE fte_uptime_seconds counter
fte_uptime_seconds 86400

# HELP fte_cpu_percent CPU usage percentage
# TYPE fte_cpu_percent gauge
fte_cpu_percent 45.2

# HELP fte_memory_percent Memory usage percentage
# TYPE fte_memory_percent gauge
fte_memory_percent 62.5

# HELP fte_disk_percent Disk usage percentage
# TYPE fte_disk_percent gauge
fte_disk_percent 71.0

# HELP fte_watcher_status Watcher status (1=running, 0=stopped)
# TYPE fte_watcher_status gauge
fte_watcher_status{watcher="gmail"} 1
fte_watcher_status{watcher="whatsapp"} 1
fte_watcher_status{watcher="filesystem"} 1

# HELP fte_sync_status Last sync status (1=synced, 0=failed)
# TYPE fte_sync_status gauge
fte_sync_status 1

# HELP fte_draft_queue_size Number of pending drafts
# TYPE fte_draft_queue_size gauge
fte_draft_queue_size 8

# HELP fte_approval_queue_size Number of pending approvals
# TYPE fte_approval_queue_size gauge
fte_approval_queue_size 5
```

---

#### GET /ready

**Description**: Kubernetes-style readiness probe (is agent ready to process tasks?).

**Request**:
```http
GET /ready HTTP/1.1
Host: <cloud-vm-ip>:8000
```

**Response** (200 OK):
```json
{
  "ready": true,
  "checks": {
    "vault_accessible": true,
    "git_configured": true,
    "watchers_healthy": true,
    "odoo_connected": true
  }
}
```

**Error Response** (503 Service Unavailable):
```json
{
  "ready": false,
  "checks": {
    "vault_accessible": true,
    "git_configured": true,
    "watchers_healthy": false,
    "odoo_connected": true
  },
  "failing_check": "watchers_healthy",
  "reason": "Gmail watcher crashed"
}
```

---

## 2. Vault File Contracts

### Folder Structure

```
vault/
├── Inbox/<domain>/              # Incoming items (email, WhatsApp, files)
├── Needs_Action/<domain>/       # Items requiring processing
├── In_Progress/<agent>/         # Claimed items (Cloud or Local ownership)
│   ├── Cloud/
│   └── Local/
├── Drafts/<domain>/             # Cloud-prepared drafts
│   ├── Email/
│   ├── Social/
│   └── Invoices/
├── Pending_Approval/<domain>/   # Drafts awaiting Local approval
├── Updates/<domain>/            # Cloud status updates for Local dashboard
├── Signals/<domain>/            # Urgent alerts (security breaches, critical events)
├── Completed/<domain>/          # Executed actions with audit trail
├── Dashboard.md                 # Single-writer (Local only) status dashboard
└── Logs/                        # Audit logs (JSON, rotated daily)
```

### Sync Exclusion Patterns (.gitignore)

```gitignore
# Secrets (NEVER sync)
.env
tokens/
sessions/
banking/
credentials/
*.key
*.pem
.os_credential_cache/

# Python artifacts
__pycache__/
*.pyc
*.pyo
.pytest_cache/

# Logs (rotate locally, don't sync)
Logs/*.log
Logs/*.json

# OS files
.DS_Store
Thumbs.db

# IDE files
.idea/
.vscode/
*.swp
*.swo
```

### Claim File Contract

**Path**: `/vault/In_Progress/<agent>/CLAIM_<timestamp>_<id>.md`

**Frontmatter**:
```yaml
---
type: claim_marker
id: CLAIM_<timestamp>_<id>
created_at: <ISO-8601>
updated_at: <ISO-8601>
status: in_progress|completed|abandoned
agent: Cloud|Local
claimed_at: <ISO-8601>
task_id: <original_task_id>
original_path: <absolute_vault_path>
expected_completion: <ISO-8601>
completed_at: <ISO-8601|null>
---
```

**Validation Rules**:
- `agent`: Must be "Cloud" or "Local"
- `claimed_at`: Must be within last 5 minutes (or marked stale)
- `original_path`: Must be valid vault path
- `status`: Must reflect actual processing state

### Update File Contract

**Path**: `/vault/Updates/<domain>/UPDATE_<timestamp>_<id>.md`

**Frontmatter**:
```yaml
---
type: update
id: UPDATE_<timestamp>_<id>
created_at: <ISO-8601>
updated_at: <ISO-8601>
status: new|read|archived
domain: email|whatsapp|invoice|social|system
update_type: detected|drafted|completed|alert
summary: <brief_summary>
details:
  <update_specific_fields>
priority: low|normal|high|urgent
read_by_local: false|true
read_at: <ISO-8601|null>
---
```

**Body**: Markdown-formatted update details

### Signal File Contract

**Path**: `/vault/Signals/<domain>/SIGNAL_<timestamp>_<id>.md`

**Frontmatter**:
```yaml
---
type: signal
id: SIGNAL_<timestamp>_<id>
created_at: <ISO-8601>
updated_at: <ISO-8601>
status: new|acknowledged|resolved
domain: security|system|business|urgent
signal_type: breach|crash|threshold_breach|critical_event
title: <alert_title>
message: <alert_message>
severity: critical|high|medium|low
acknowledged_by: <user_name|null>
acknowledged_at: <ISO-8601|null>
---
```

**Body**: Markdown-formatted alert with action items

### Dashboard.md Contract

**Path**: `/vault/Dashboard.md`

**Frontmatter**:
```yaml
---
type: dashboard
last_updated: <ISO-8601>
updated_by: Local  # ALWAYS "Local" (single-writer rule)
system_status: healthy|degraded|unhealthy
cloud_status: online|offline|degraded
local_status: online|offline
last_sync: <ISO-8601>
sync_status: synced|syncing|failed|conflict
metrics:
  pending_count: <integer>
  in_progress_count: <integer>
  pending_approval_count: <integer>
  draft_count: <integer>
  completed_today: <integer>
  alerts_count: <integer>
watchers:
  gmail: running|stopped|error
  whatsapp: running|stopped|error
  filesystem: running|stopped|error
cloud_health:
  uptime_seconds: <integer>
  cpu_percent: <number>
  memory_percent: <number>
  disk_percent: <number>
recent_activity:
  - timestamp: <ISO-8601>
    action: <action_type>
    agent: Cloud|Local
    status: success|failure
    details: <optional_details>
---
```

**Body**: Markdown-formatted dashboard (human-readable)

**Single-Writer Rule**:
- ONLY Local Agent may write to Dashboard.md
- Cloud Agent writes updates to `/Updates/<domain>/`
- Local merges updates into Dashboard.md during sync

---

## 3. External API Integrations

### Gmail API (Gold Tier, Extended for Platinum)

**Base URL**: `https://www.googleapis.com/gmail/v1`

**Authentication**: OAuth 2.0 (Local only, credentials never sync to Cloud)

**Cloud Permissions** (Draft-Only):
```python
scopes = [
    "https://www.googleapis.com/auth/gmail.readonly",  # Read emails
    "https://www.googleapis.com/auth/gmail.compose"     # Create drafts (NOT send)
]
```

**Local Permissions** (Full Execution):
```python
scopes = [
    "https://www.googleapis.com/auth/gmail.readonly",  # Read emails
    "https://www.googleapis.com/auth/gmail.compose",   # Create drafts
    "https://www.googleapis.com/auth/gmail.send"       # Send emails (Local only)
]
```

**Key Endpoints**:
```python
# List unread emails (Cloud/Local)
GET /users/me/messages?q=is:unread

# Get email details (Cloud/Local)
GET /users/me/messages/{messageId}

# Create draft (Cloud/Local)
POST /users/me/drafts
Body: {
  "message": {
    "raw": "<base64-encoded RFC2822 email>"
  }
}

# Send email (Local ONLY)
POST /users/me/messages/send
Body: {
  "raw": "<base64-encoded RFC2822 email>"
}
```

**Rate Limits**:
- Read: 250 requests/second (per user)
- Draft/Create: 50 requests/second
- Send: 50 requests/second

**Error Handling**:
- `401 Unauthorized`: Token expired → refresh token
- `403 Forbidden`: Insufficient permissions → check scopes
- `429 Too Many Requests`: Rate limit exceeded → exponential backoff

---

### WhatsApp Web API (Playwright Automation)

**Base URL**: `https://web.whatsapp.com`

**Authentication**: Session-based (QR code scan, session stored locally)

**Cloud Mode** (Draft-Only):
- Monitor incoming messages (read-only)
- Create draft replies in vault
- NO session sync to Cloud (security boundary)

**Local Mode** (Full Execution):
- Send messages via Playwright automation
- Session stored in Local vault (excluded from sync)

**Session File Pattern**:
```
vault/whatsapp_session/
├── session.json         # NEVER sync to Cloud (.gitignore)
└── qr_code.png          # Temporary (deleted after scan)
```

**Playwright Workflow**:
```python
from playwright.sync_api import sync_playwright

def send_whatsapp_message(phone: str, message: str):
    """Send WhatsApp message via Playwright (Local only)."""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto("https://web.whatsapp.com")
        
        # Wait for QR scan (session restored if exists)
        page.wait_for_selector('div[data-testid="default-user"]')
        
        # Search contact and send message
        page.fill('div[contenteditable="true"][data-tab="3"]', phone)
        page.keyboard.press("Enter")
        page.wait_for_timeout(1000)
        page.fill('div[contenteditable="true"][data-tab="10"]', message)
        page.keyboard.press("Enter")
        
        browser.close()
```

**Session Expiry Handling**:
- Detect QR code requirement → notify user
- Save QR code image to vault
- User scans QR → session restored
- Session persisted to Local vault (encrypted)

---

### Odoo JSON-RPC API (Gold Tier, Extended for Platinum)

**Base URL**: `http://<cloud-vm>:8069/jsonrpc`

**Authentication**: JSON-RPC with UID/password (Cloud: draft-only, Local: full)

**Cloud Mode** (Draft-Only):
```python
# Create draft invoice (Cloud)
def odoo_create_draft_invoice(invoice_data: dict) -> int:
    """Create draft invoice in Odoo (Cloud, draft-only)."""
    payload = {
        "jsonrpc": "2.0",
        "method": "call",
        "params": {
            "service": "object",
            "db": "odoo_db",
            "uid": 2,  # Draft-only user (no post permissions)
            "password": "<draft-only-password>",
            "model": "account.move",
            "method": "create",
            "args": [[invoice_data]],
            "kwargs": {}
        }
    }
    response = requests.post(url, json=payload)
    return response.json().get("result")  # Invoice ID (draft status)
```

**Local Mode** (Full Execution):
```python
# Post invoice (Local only)
def odoo_post_invoice(invoice_id: int) -> bool:
    """Post draft invoice and send to customer (Local only)."""
    payload = {
        "jsonrpc": "2.0",
        "method": "call",
        "params": {
            "service": "object",
            "db": "odoo_db",
            "uid": 2,  # Admin user (full permissions)
            "password": "<admin-password>",
            "model": "account.move",
            "method": "action_post",
            "args": [[invoice_id]],
            "kwargs": {}
        }
    }
    response = requests.post(url, json=payload)
    return response.json().get("result")
```

**Key Methods**:
```python
# Create invoice (draft)
account.move.create([values]) → int (invoice ID)

# Post invoice (Local only)
account.move.action_post([invoice_id]) → bool

# Send invoice to customer (Local only)
account.move.action_invoice_send([invoice_id]) → bool

# Get invoice details
account.move.read([invoice_id], fields) → list[dict]
```

**Error Handling**:
- `TimeoutException`: Retry with exponential backoff (1s, 2s, 4s; max 3 retries)
- `ConnectionError`: Circuit breaker (trip after 5 failures, reset after 300s)
- `OdooException`: Log full error, create draft in vault (fallback)

**Rate Limits**:
- JSON-RPC: No hard limit (Odoo server-dependent)
- Recommended: <10 requests/second (avoid server overload)

---

### Social Media APIs

#### Facebook Graph API v18+

**Base URL**: `https://graph.facebook.com/v18.0`

**Authentication**: OAuth 2.0 (Page Access Token, Local only)

**Endpoints**:
```python
# Create post (Local only)
POST /{page-id}/feed
Body: {
  "message": "<post_content>",
  "access_token": "<page-access-token>"
}
Response: {"id": "<post-id>"}

# Upload photo (Local only)
POST /{page-id}/photos
Body: {
  "url": "<photo-url>",
  "message": "<caption>",
  "access_token": "<page-access-token>"
}

# Get analytics (Local only)
GET /{post-id}/insights?metric=post_impressions,post_likes
Response: {"data": [{"name": "post_impressions", "values": [...]}]}
```

**Rate Limits**:
- 200 calls/hour (per Page)
- 4,000 calls/day (per App)

---

#### Twitter API v2

**Base URL**: `https://api.twitter.com/2`

**Authentication**: OAuth 2.0 Bearer Token (Local only)

**Endpoints**:
```python
# Create tweet (Local only)
POST /tweets
Body: {
  "text": "<tweet-content>"
}
Headers: {
  "Authorization": "Bearer <access-token>"
}
Response: {"data": {"id": "<tweet-id>", "text": "..."}}

# Get analytics (Local only)
GET /tweets/{tweet-id}?tweet.fields=public_metrics
Response: {"data": {"public_metrics": {"like_count": 10, "retweet_count": 5}}}
```

**Rate Limits**:
- 300 calls/15 minutes (per user)

---

#### LinkedIn API

**Base URL**: `https://api.linkedin.com/v2`

**Authentication**: OAuth 2.0 (Local only)

**Endpoints**:
```python
# Create post (Local only)
POST /ugcPosts
Body: {
  "author": "urn:li:person:{person-id}",
  "lifecycleState": "PUBLISHED",
  "specificContent": {
    "com.linkedin.ugc.ShareContent": {
      "shareCommentary": {
        "text": "<post-content>"
      }
    }
  },
  "visibility": {
    "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
  }
}

# Get analytics (Local only)
GET /posts/{post-id}?projection=(elements*(actions))
```

**Rate Limits**:
- 500 calls/day (per user)

---

## 4. Internal Python Skills

### Vault Sync Skill

```python
def sync_vault(mode: Literal["pull", "push", "full"]) -> dict[str, Any]:
    """
    Sync vault between Cloud and Local via Git remote.
    
    Args:
        mode: "pull" (fetch from remote), "push" (commit and push),
              "full" (pull + push)
    
    Returns:
        Dict with sync status, duration, conflicts
    
    Raises:
        GitError: If sync fails
        SecretDetectedError: If secret file detected in sync path
    """
    check_dev_mode()
    logger = AuditLogger(component="sync_vault")
    # ... implementation
```

**Usage**:
```python
# Cloud: Pull changes from remote
result = sync_vault(mode="pull")

# Local: Push approved actions
result = sync_vault(mode="push")

# Full sync (both directions)
result = sync_vault(mode="full")
```

---

### Security Boundary Skill

```python
def validate_sync_file(file_path: Path) -> bool:
    """
    Validate file before syncing to Cloud.
    
    Args:
        file_path: Path to file being synced
    
    Returns:
        True if safe to sync, False if blocked
    
    Raises:
        SecretDetectedError: If secret pattern detected
    """
    SECRET_PATTERNS = [
        r"\.env$",
        r"tokens/",
        r"sessions/",
        r"banking/",
        r"credentials/",
        r".*\.key$",
        r".*\.pem$",
    ]
    # ... implementation
```

**Usage**:
```python
# Pre-sync validation
if validate_sync_file(file_path):
    sync_file(file_path)
else:
    logger.error(f"Blocked secret file: {file_path}")
```

---

### Claim-by-Move Skill

```python
def claim_task(task_id: str, agent: Literal["Cloud", "Local"]) -> ClaimFile:
    """
    Claim task by moving to agent-specific folder.
    
    Args:
        task_id: ID of task to claim
        agent: Claiming agent (Cloud or Local)
    
    Returns:
        ClaimFile with claim metadata
    
    Raises:
        TaskAlreadyClaimedError: If another agent already claimed
    """
    # ... implementation
```

**Usage**:
```python
# Cloud claims email for drafting
claim = claim_task(task_id="EMAIL_123", agent="Cloud")

# Local checks if task is claimed
if is_claimed(task_id) and get_claim_agent(task_id) != "Local":
    # Skip, Cloud is working on it
    pass
```

---

### Health Check Skill

```python
def get_health_status() -> dict[str, Any]:
    """
    Get Cloud VM health status.
    
    Returns:
        Dict with status, uptime, resources, watchers
    
    Raises:
        HealthEndpointError: If health endpoint unreachable
    """
    # ... implementation
```

**Usage**:
```python
# Check Cloud health
health = get_health_status()
if health["status"] == "unhealthy":
    alert_user("Cloud VM unhealthy", severity="high")
```

---

## Error Taxonomy

### HTTP Status Codes (Health Endpoint)

| Code | Meaning | Usage |
|------|---------|-------|
| 200 | OK | Health check successful |
| 400 | Bad Request | Invalid request format |
| 401 | Unauthorized | Authentication required (if enabled) |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Endpoint not found |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Unexpected error |
| 503 | Service Unavailable | Agent unhealthy (disk >90%, crash) |

### Python Exceptions

```python
class FTEAgentError(Exception):
    """Base exception for FTE-Agent."""

class SecretDetectedError(FTEAgentError):
    """Raised when secret file detected in sync path."""

class TaskAlreadyClaimedError(FTEAgentError):
    """Raised when attempting to claim already-claimed task."""

class StaleClaimError(FTEAgentError):
    """Raised when claim is stale (>5 minutes) and reclaimable."""

class HealthEndpointError(FTEAgentError):
    """Raised when health endpoint unreachable."""

class OdooRPCError(FTEAgentError):
    """Raised when Odoo JSON-RPC call fails."""

class SessionExpiredError(FTEAgentError):
    """Raised when WhatsApp/LinkedIn session expired."""

class ApprovalExpiredError(FTEAgentError):
    """Raised when approval request expired (>24 hours)."""

class SyncConflictError(FTEAgentError):
    """Raised when sync conflict detected (unresolvable)."""

class VaultPathError(FTEAgentError):
    """Raised when invalid vault path detected (traversal attempt)."""
```

---

## Versioning Strategy

### API Versioning

- **Health Endpoint**: No versioning (internal only, stable contract)
- **Vault Files**: `spec_version` in frontmatter (e.g., "1.0")
- **External APIs**: Use latest stable version (Gmail v1, Facebook v18, Twitter v2)

### Backward Compatibility

- Vault files: Support previous 2 spec versions
- Migration scripts: `scripts/migrations/migrate_v1_to_v2.py`
- Deprecation policy: 90-day notice before breaking changes

---

## Idempotency & Retries

### Idempotency

- **Claim-by-Move**: Atomic file operations (idempotent)
- **Draft Creation**: Check for existing draft (prevent duplicates)
- **Approval Execution**: Track executed approvals by hash (prevent double-execution)

### Retry Strategy

```python
# External API calls (Odoo, Social Media)
@retry(
    wait=wait_exponential(multiplier=1, min=1, max=4),  # 1s, 2s, 4s
    stop=stop_after_attempt(3),
    retry=retry_if_exception_type((TimeoutException, ConnectionError))
)
def external_api_call():
    # ... implementation
```

### Circuit Breaker

```python
# Circuit breaker for external APIs
circuit_breaker = CircuitBreaker(
    failure_threshold=5,      # Trip after 5 failures
    recovery_timeout=300,     # Reset after 300 seconds
    expected_exceptions=(OdooRPCError, requests.RequestException)
)

@circuit_breaker
def odoo_rpc_call():
    # ... implementation
```

---

## Next Steps

1. ✅ API contracts complete (Health, Vault, External, Skills)
2. → Generate quickstart guide (Cloud/Local setup)
3. → Update agent context with new technologies
4. → Fill plan.md Technical Context and Constitution Check

---

**Status**: Phase 1 Contracts COMPLETE
**Date**: 2026-04-02
**Next**: Quickstart Guide
