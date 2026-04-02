# FTE-Agent API Reference

**Version**: 3.0.0 (Gold Tier)  
**Last Updated**: 2026-04-02  
**Branch**: `003-gold-tier-autonomous-employee`

---

## Table of Contents

1. [Email MCP Server](#email-mcp-server)
2. [WhatsApp MCP Server](#whatsapp-mcp-server)
3. [Social MCP Server](#social-mcp-server)
4. [Odoo MCP Server](#odoo-mcp-server)
5. [Audit Skills](#audit-skills)
6. [DLQ Skills](#dlq-skills)
7. [Briefing Skills](#briefing-skills)
8. [Ralph Wiggum Skills](#ralph-wiggum-skills)
9. [Health Endpoint](#health-endpoint)

---

## Email MCP Server

**Module**: `src/mcp_servers/email_mcp/handlers.py`

### send_email

**Signature**:
```python
def send_email(
    to: str,
    subject: str,
    body: str,
    attachments: list[str] | None = None,
    dry_run: bool = False
) -> dict[str, Any]:
```

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| to | str | Yes | Recipient email address |
| subject | str | Yes | Email subject |
| body | str | Yes | Email body text |
| attachments | list[str] | No | List of file paths to attach |
| dry_run | bool | No | Log without sending (default: False) |

**Returns**:
```python
{
    "success": bool,
    "message_id": str,
    "status": "sent" | "failed" | "dry_run",
    "error": str | None
}
```

**Errors**:
- `ValueError`: Invalid recipient or empty subject
- `ConnectionError`: SMTP connection failed
- `PermissionError`: DEV_MODE not enabled

**Example**:
```python
from src.skills.email_skills import send_email

result = send_email(
    to="user@example.com",
    subject="Invoice #1234",
    body="Please find attached invoice...",
    attachments=["/path/to/invoice.pdf"]
)

assert result["status"] == "sent"
```

---

### draft_email

**Signature**:
```python
def draft_email(
    to: str,
    subject: str,
    body: str,
    attachments: list[str] | None = None
) -> dict[str, Any]:
```

**Parameters**: Same as `send_email` (without `dry_run`)

**Returns**:
```python
{
    "success": bool,
    "draft_id": str,
    "status": "draft_created" | "failed"
}
```

**Example**:
```python
from src.skills.email_skills import draft_email

result = draft_email(
    to="user@example.com",
    subject="Draft: Invoice #1234",
    body="Draft email..."
)

print(f"Draft ID: {result['draft_id']}")
```

---

### search_emails

**Signature**:
```python
def search_emails(
    query: str,
    max_results: int = 10
) -> list[dict[str, Any]]:
```

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| query | str | Yes | Gmail search query |
| max_results | int | No | Maximum results (default: 10) |

**Returns**:
```python
[
    {
        "id": str,
        "snippet": str,
        "from": str,
        "subject": str,
        "date": str
    }
]
```

**Gmail Search Operators**:
- `from:user@example.com` - From specific sender
- `to:user@example.com` - To specific recipient
- `subject:invoice` - Subject contains word
- `has:attachment` - Has attachments
- `is:unread` - Unread messages
- `is:important` - Important messages

**Example**:
```python
from src.skills.email_skills import search_emails

messages = search_emails("is:unread is:important", max_results=5)

for msg in messages:
    print(f"From: {msg['from']}, Subject: {msg['subject']}")
```

---

## WhatsApp MCP Server

**Module**: `src/mcp_servers/whatsapp_mcp/handlers.py`

### send_whatsapp

**Signature**:
```python
def send_whatsapp(
    contact: str,
    message: str
) -> dict[str, Any]:
```

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| contact | str | Yes | Contact name or phone number |
| message | str | Yes | Message text |

**Returns**:
```python
{
    "success": bool,
    "status": "sent" | "failed" | "session_expired",
    "timestamp": str
}
```

**Errors**:
- `SessionExpiredError`: WhatsApp session expired
- `ContactNotFoundError`: Contact not found
- `PermissionError`: DEV_MODE not enabled

**Example**:
```python
from src.skills.whatsapp_skills import send_whatsapp

result = send_whatsapp(
    contact="+1234567890",
    message="Meeting at 3 PM today"
)

assert result["status"] == "sent"
```

---

## Social MCP Server

**Module**: `src/mcp_servers/social_mcp/`

### post_linkedin

**Signature**:
```python
def post_linkedin(
    text: str,
    image_url: str | None = None
) -> dict[str, Any]:
```

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| text | str | Yes | Post text (max 3000 chars) |
| image_url | str | No | Optional image URL |

**Returns**:
```python
{
    "success": bool,
    "post_id": str,
    "status": "posted" | "failed" | "rate_limited",
    "url": str
}
```

**Rate Limits**:
- 1 post per 24 hours
- Reset at midnight UTC

**Example**:
```python
from src.skills.social_skills import post_linkedin

result = post_linkedin(
    text="Excited to announce our new product launch!",
    image_url="https://example.com/product.jpg"
)

print(f"Post URL: {result['url']}")
```

---

### post_twitter

**Signature**:
```python
def post_twitter(
    text: str,
    media_urls: list[str] | None = None
) -> dict[str, Any]:
```

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| text | str | Yes | Tweet text (max 280 chars) |
| media_urls | list[str] | No | List of media URLs (max 4) |

**Returns**:
```python
{
    "success": bool,
    "tweet_id": str,
    "status": "posted" | "failed" | "rate_limited",
    "url": str
}
```

**Rate Limits**:
- 300 posts per 15-minute window
- Reset every 15 minutes

**Example**:
```python
from src.skills.social_skills import post_twitter

result = post_twitter(
    text="Hello Twitter! #FTEAgent",
    media_urls=["https://example.com/image.jpg"]
)

print(f"Tweet URL: {result['url']}")
```

---

### post_facebook

**Signature**:
```python
def post_facebook(
    page_id: str,
    content: str,
    image_url: str | None = None
) -> dict[str, Any]:
```

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| page_id | str | Yes | Facebook page ID |
| content | str | Yes | Post content |
| image_url | str | No | Optional image URL |

**Returns**:
```python
{
    "success": bool,
    "post_id": str,
    "status": "posted" | "failed" | "rate_limited",
    "url": str
}
```

**Rate Limits**:
- 200 calls per hour
- Reset every hour

**Example**:
```python
from src.skills.social_skills import post_facebook

result = post_facebook(
    page_id="123456789",
    content="Check out our latest update!",
    image_url="https://example.com/update.jpg"
)

print(f"Post URL: {result['url']}")
```

---

### post_instagram

**Signature**:
```python
def post_instagram(
    image_path: str,
    caption: str
) -> dict[str, Any]:
```

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| image_path | str | Yes | Path to image file |
| caption | str | Yes | Post caption (max 2200 chars) |

**Returns**:
```python
{
    "success": bool,
    "media_id": str,
    "status": "posted" | "failed" | "rate_limited",
    "permalink": str
}
```

**Rate Limits**:
- 25 posts per day
- Reset at midnight UTC

**Requirements**:
- Instagram Business account required
- Image must be square (1:1 aspect ratio recommended)

**Example**:
```python
from src.skills.social_skills import post_instagram

result = post_instagram(
    image_path="images/product.jpg",
    caption="New product launch! #innovation"
)

print(f"Permalink: {result['permalink']}")
```

---

### get_analytics (All Platforms)

**Signature**:
```python
def get_linkedin_analytics(post_id: str) -> dict[str, Any]:
def get_twitter_analytics(tweet_id: str) -> dict[str, Any]:
def get_facebook_insights(page_id: str, post_id: str) -> dict[str, Any]:
def get_instagram_insights(media_id: str) -> dict[str, Any]:
```

**Returns** (LinkedIn):
```python
{
    "likes": int,
    "comments": int,
    "shares": int,
    "impressions": int,
    "clicks": int
}
```

**Returns** (Twitter):
```python
{
    "likes": int,
    "retweets": int,
    "replies": int,
    "impressions": int
}
```

**Returns** (Facebook):
```python
{
    "reach": int,
    "engagement": int,
    "likes": int,
    "comments": int,
    "shares": int
}
```

**Returns** (Instagram):
```python
{
    "likes": int,
    "comments": int,
    "saves": int,
    "reach": int,
    "impressions": int
}
```

---

## Odoo MCP Server

**Module**: `src/mcp_servers/odoo_mcp/handlers.py`

### create_invoice

**Signature**:
```python
def create_invoice(
    partner_id: int,
    amount: float,
    description: str,
    invoice_date: str | None = None
) -> dict[str, Any]:
```

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| partner_id | int | Yes | Odoo partner ID (customer) |
| amount | float | Yes | Invoice amount (positive) |
| description | str | Yes | Invoice description |
| invoice_date | str | No | Date (YYYY-MM-DD), default today |

**Returns**:
```python
{
    "success": bool,
    "invoice_id": int,
    "number": str,
    "status": "created" | "failed",
    "amount": float
}
```

**Errors**:
- `ValueError`: Invalid amount or missing partner
- `ConnectionError`: Odoo connection failed
- `PermissionError`: DEV_MODE not enabled

**Example**:
```python
from src.skills.odoo_skills import create_invoice

result = create_invoice(
    partner_id=1,
    amount=1000.00,
    description="Consulting services - March 2026"
)

print(f"Invoice Number: {result['number']}")
```

---

### record_payment

**Signature**:
```python
def record_payment(
    invoice_id: int,
    amount: float,
    payment_date: str | None = None
) -> dict[str, Any]:
```

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| invoice_id | int | Yes | Odoo invoice ID |
| amount | float | Yes | Payment amount |
| payment_date | str | No | Date (YYYY-MM-DD), default today |

**Returns**:
```python
{
    "success": bool,
    "payment_id": int,
    "status": "recorded" | "failed",
    "remaining_balance": float
}
```

**Example**:
```python
from src.skills.odoo_skills import record_payment

result = record_payment(
    invoice_id=123,
    amount=1000.00
)

print(f"Remaining Balance: ${result['remaining_balance']}")
```

---

### categorize_expense

**Signature**:
```python
def categorize_expense(
    amount: float,
    description: str,
    category: str
) -> dict[str, Any]:
```

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| amount | float | Yes | Expense amount |
| description | str | Yes | Expense description |
| category | str | Yes | Category (e.g., "Software", "Travel") |

**Returns**:
```python
{
    "success": bool,
    "expense_id": int,
    "status": "categorized" | "failed",
    "category": str
}
```

**Example**:
```python
from src.skills.odoo_skills import categorize_expense

result = categorize_expense(
    amount=50.00,
    description="AWS monthly bill",
    category="Software"
)

print(f"Expense ID: {result['expense_id']}")
```

---

## Audit Skills

**Module**: `src/skills/audit_skills.py`

### query_logs

**Signature**:
```python
def query_logs(
    date: str | None = None,
    action: str | None = None,
    result: str | None = None,
    component: str | None = None,
    limit: int = 1000
) -> list[dict[str, Any]]:
```

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| date | str | No | Date (YYYY-MM-DD) or range (start:end) |
| action | str | No | Filter by action type |
| result | str | No | Filter by result (success, failure, pending) |
| component | str | No | Filter by component |
| limit | int | No | Maximum results (default: 1000) |

**Returns**:
```python
[
    {
        "timestamp": str,
        "level": str,
        "component": str,
        "action": str,
        "result": str,
        "error": str | None,
        "details": dict
    }
]
```

**Example**:
```python
from src.skills.audit_skills import query_logs

# Query today's logs
logs = query_logs(date="2026-04-02")

# Query failed email sends
failures = query_logs(
    action="email_sent",
    result="failure"
)

# Query date range
range_logs = query_logs(date="2026-04-01:2026-04-02")
```

---

### export_to_csv

**Signature**:
```python
def export_to_csv(
    log_entries: list[dict],
    output_path: str,
    fields: list[str] | None = None
) -> Path:
```

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| log_entries | list[dict] | Yes | Log entries to export |
| output_path | str | Yes | Output file path |
| fields | list[str] | No | Fields to include (default: all) |

**Returns**: `Path` to created CSV file

**Example**:
```python
from src.skills.audit_skills import query_logs, export_to_csv

logs = query_logs(date="2026-04-01")
csv_path = export_to_csv(
    logs,
    "logs_april_1.csv",
    fields=["timestamp", "action", "result", "error"]
)

print(f"CSV exported to: {csv_path}")
```

---

### get_log_statistics

**Signature**:
```python
def get_log_statistics(
    days: int = 7
) -> dict[str, Any]:
```

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| days | int | No | Days to analyze (default: 7) |

**Returns**:
```python
{
    "total_entries": int,
    "by_result": dict,
    "by_action": dict,
    "by_component": dict,
    "by_date": dict,
    "error_rate": float,
    "peak_hour": str,
    "period": {"start": str, "end": str},
    "recent_errors": list
}
```

**Example**:
```python
from src.skills.audit_skills import get_log_statistics

stats = get_log_statistics(days=7)

print(f"Total Entries: {stats['total_entries']}")
print(f"Error Rate: {stats['error_rate']}%")
print(f"Peak Hour: {stats['peak_hour']}")
```

---

## DLQ Skills

**Module**: `src/skills/dlq_skills.py`

### list_dlq_items

**Signature**:
```python
def list_dlq_items(
    status: str | None = None,
    action_type: str | None = None,
    limit: int = 100
) -> list[dict[str, Any]]:
```

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| status | str | No | Filter by status (pending_review, resolved, discarded) |
| action_type | str | No | Filter by action type |
| limit | int | No | Maximum results (default: 100) |

**Returns**:
```python
[
    {
        "id": str,
        "original_action": str,
        "failure_reason": str,
        "failure_count": int,
        "last_attempt": str,
        "status": str,
        "details": dict
    }
]
```

**Example**:
```python
from src.skills.dlq_skills import list_dlq_items

# List pending items
pending = list_dlq_items(status="pending_review")

# List email failures
email_failures = list_dlq_items(action_type="send_email")
```

---

### resolve_dlq_item

**Signature**:
```python
def resolve_dlq_item(
    item_id: str,
    resolution: str,
    notes: str | None = None
) -> bool:
```

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| item_id | str | Yes | DLQ item UUID |
| resolution | str | Yes | Resolution description |
| notes | str | No | Additional notes |

**Returns**: `True` if resolved, `False` if not found

**Example**:
```python
from src.skills.dlq_skills import resolve_dlq_item

success = resolve_dlq_item(
    item_id="abc-123",
    resolution="Fixed SMTP credentials",
    notes="Updated .env file with new password"
)

assert success is True
```

---

### discard_dlq_item

**Signature**:
```python
def discard_dlq_item(
    item_id: str,
    notes: str | None = None
) -> bool:
```

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| item_id | str | Yes | DLQ item UUID |
| notes | str | No | Reason for discarding |

**Returns**: `True` if discarded, `False` if not found

**Example**:
```python
from src.skills.dlq_skills import discard_dlq_item

success = discard_dlq_item(
    item_id="xyz-789",
    notes="Action no longer needed"
)

assert success is True
```

---

## Briefing Skills

**Module**: `src/skills/briefing_skills.py`

### generate_ceo_briefing

**Signature**:
```python
def generate_ceo_briefing() -> dict[str, Any]:
```

**Returns**:
```python
{
    "success": bool,
    "briefing_path": str,
    "generation_time_sec": float,
    "period": {"start": str, "end": str}
}
```

**Output File**: `/Vault/Briefings/YYYY-MM-DD_Monday_Briefing.md`

**Example**:
```python
from src.skills.briefing_skills import generate_ceo_briefing

result = generate_ceo_briefing()

print(f"Briefing generated: {result['briefing_path']}")
print(f"Generation time: {result['generation_time_sec']}s")
```

---

### calculate_revenue

**Signature**:
```python
def calculate_revenue(
    period_start: str,
    period_end: str
) -> dict[str, Any]:
```

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| period_start | str | Yes | Start date (YYYY-MM-DD) |
| period_end | str | Yes | End date (YYYY-MM-DD) |

**Returns**:
```python
{
    "total": float,
    "by_source": dict,
    "trend_percentage": float
}
```

**Example**:
```python
from src.skills.briefing_skills import calculate_revenue

revenue = calculate_revenue(
    period_start="2026-03-25",
    period_end="2026-03-31"
)

print(f"Total Revenue: ${revenue['total']}")
print(f"Trend: {revenue['trend_percentage']}%")
```

---

## Ralph Wiggum Skills

**Module**: `src/skills/ralph_wiggum_skills.py`

### save_task_state

**Signature**:
```python
def save_task_state(task_state: TaskState) -> Path:
```

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| task_state | TaskState | Yes | TaskState object |

**Returns**: `Path` to state file

**State File Location**: `/Vault/In_Progress/<agent>/<task-id>.md`

**Example**:
```python
from src.models.task_state import TaskState
from src.skills.ralph_wiggum_skills import save_task_state

task_state = TaskState(
    task_id="task-123",
    objective="Process all emails",
    iteration=1,
    max_iterations=10
)

state_file = save_task_state(task_state)
print(f"State saved to: {state_file}")
```

---

### check_completion

**Signature**:
```python
def check_completion(task_id: str) -> bool:
```

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| task_id | str | Yes | Task UUID |

**Returns**: `True` if complete, `False` otherwise

**Completion Detection Methods**:
1. Primary: File moved to `/Done/`
2. Fallback: `<promise>TASK_COMPLETE</promise>` tag
3. Alternative: Plan checklist 100% complete

**Example**:
```python
from src.skills.ralph_wiggum_skills import check_completion

if check_completion("task-123"):
    print("Task complete!")
else:
    print("Task still in progress")
```

---

## Health Endpoint

**Module**: `src/api/health_endpoint.py`

### GET /health

**Endpoint**: `http://localhost:8000/health`

**Method**: GET

**Response**:
```json
{
    "status": "healthy" | "degraded" | "unhealthy",
    "timestamp": "2026-04-02T10:30:00",
    "components": {
        "watcher_gmail": {
            "status": "healthy",
            "last_check": "2026-04-02T10:30:00",
            "error_count": 0,
            "fallback_active": false
        }
    },
    "system": {
        "cpu_percent": 45.2,
        "memory_percent": 62.1,
        "disk_percent": 55.0
    }
}
```

**Example**:
```bash
curl http://localhost:8000/health
```

---

### GET /metrics

**Endpoint**: `http://localhost:8000/metrics`

**Method**: GET

**Authentication**: Optional (Bearer token via `Authorization` header)

**Response Format**: Prometheus exposition format

```
# HELP fte_component_health Component health status
# TYPE fte_component_health gauge
fte_component_health{component="watcher_gmail"} 1.0
fte_component_health{component="watcher_whatsapp"} 1.0

# HELP fte_system_cpu_percent CPU usage percentage
# TYPE fte_system_cpu_percent gauge
fte_system_cpu_percent 45.2
```

**Example**:
```bash
curl http://localhost:8000/metrics

# With authentication
curl -H "Authorization: Bearer <token>" http://localhost:8000/metrics
```

---

### GET /ready

**Endpoint**: `http://localhost:8000/ready`

**Method**: GET

**Response Codes**:
- `200`: Service ready
- `503`: Service not ready (critical dependency unhealthy)

**Example**:
```bash
curl http://localhost:8000/ready
```

---

### GET /live

**Endpoint**: `http://localhost:8000/live`

**Method**: GET

**Response**:
```json
{
    "status": "alive",
    "timestamp": "2026-04-02T10:30:00"
}
```

**Example**:
```bash
curl http://localhost:8000/live
```

---

### POST /health/reset

**Endpoint**: `http://localhost:8000/health/reset`

**Method**: POST

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| component | str | No | Specific component to reset |

**Example**:
```bash
# Reset all components
curl -X POST http://localhost:8000/health/reset

# Reset specific component
curl -X POST "http://localhost:8000/health/reset?component=watcher_gmail"
```

---

## Error Codes

### Common Error Codes

| Code | Meaning | Resolution |
|------|---------|------------|
| `DEV_MODE_DISABLED` | DEV_MODE not enabled | Set `DEV_MODE=true` in .env |
| `CIRCUIT_BREAKER_OPEN` | Circuit breaker tripped | Wait for reset or manually reset |
| `RATE_LIMIT_EXCEEDED` | API rate limit exceeded | Wait for reset window |
| `SESSION_EXPIRED` | Authentication session expired | Re-authenticate |
| `DLQ_QUARANTINED` | Action quarantined in DLQ | Review and resolve DLQ item |

---

## Rate Limits

| Platform | Limit | Reset Window |
|----------|-------|--------------|
| Gmail API | 250 units/15 sec | 15 seconds |
| WhatsApp Web | No hard limit | N/A |
| LinkedIn | 1 post/day | 24 hours |
| Twitter | 300 posts/15 min | 15 minutes |
| Facebook | 200 calls/hour | 1 hour |
| Instagram | 25 posts/day | 24 hours |
| Odoo | No hard limit | N/A |

---

*Generated by FTE-Agent Development Team*  
*Last Updated: 2026-04-02*
