# FTE-Agent Quickstart Guide

**Version**: 3.0.0 (Gold Tier)  
**Last Updated**: 2026-04-02  
**Branch**: `003-gold-tier-autonomous-employee`

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Installation](#installation)
3. [Configuration](#configuration)
4. [First Run](#first-run)
5. [Health Check Verification](#health-check-verification)
6. [API Reference](#api-reference)

---

## Prerequisites

### Required Software

| Software | Version | Purpose | Installation Link |
|----------|---------|---------|-------------------|
| **Python** | 3.13+ | Core runtime | https://www.python.org/downloads/ |
| **Node.js** | 24+ LTS | MCP servers | https://nodejs.org/ |
| **Git** | Latest | Version control | https://git-scm.com/ |
| **Playwright** | Latest | Browser automation | `pip install playwright` |
| **Odoo** | v19+ (optional) | Accounting system | https://www.odoo.com/documentation/19.0/ |

### Hardware Requirements

- **Minimum**: 8GB RAM, 4-core CPU, 20GB free disk space
- **Recommended**: 16GB RAM, 8-core CPU, SSD storage
- **For always-on operation**: Consider cloud VM (Oracle Cloud Free Tier, AWS EC2)

### Developer Accounts (Optional)

| Service | Purpose | Setup Time |
|---------|---------|------------|
| Gmail API | Email integration | 15 min |
| WhatsApp Web | Messaging integration | 5 min |
| LinkedIn Developer | Social posting | 30 min |
| Twitter Developer | Social posting | 30 min |
| Facebook Developer | Social posting | 30 min |
| Instagram Business | Social posting | 15 min |

---

## Installation

### Step 1: Clone Repository

```bash
cd H:\Programming
git clone <repository-url> FTE-Agent
cd FTE-Agent
```

### Step 2: Create Virtual Environment

```bash
# Windows PowerShell
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Linux/Mac
python3 -m venv .venv
source .venv/bin/activate
```

### Step 3: Install Dependencies

```bash
# Install Python dependencies
pip install -r FTE/requirements.txt

# Install Playwright browsers
playwright install chromium

# Verify installation
pytest --version
```

### Step 4: Setup Vault Directory

```bash
cd FTE

# Create vault structure
mkdir -p vault/Inbox
mkdir -p vault/Needs_Action
mkdir -p vault/Pending_Approval
mkdir -p vault/Approved
mkdir -p vault/Done
mkdir -p vault/Logs
mkdir -p vault/Briefings
mkdir -p vault/Drafts
mkdir -p vault/Odoo_Fallback
mkdir -p vault/Dead_Letter_Queue
mkdir -p vault/State
```

---

## Configuration

### Step 1: Environment Variables

Create `.env` file in `FTE/` directory:

```bash
# FTE/.env

# DEV_MODE: Enable external actions (REQUIRED for production)
DEV_MODE=true

# DRY_RUN: Log actions without executing (default: false)
DRY_RUN=false

# Gmail API (optional)
GMAIL_CLIENT_ID=your_client_id
GMAIL_CLIENT_SECRET=your_client_secret
GMAIL_REDIRECT_URI=http://localhost:8080/callback
GMAIL_SCOPES=https://www.googleapis.com/auth/gmail.send,https://www.googleapis.com/auth/gmail.readonly

# Odoo (optional)
ODOO_URL=http://localhost:8069/jsonrpc
ODOO_DB=odoo
ODOO_UID=2
ODOO_PASSWORD=admin

# Social Media APIs (optional)
LINKEDIN_CLIENT_ID=your_linkedin_client_id
LINKEDIN_CLIENT_SECRET=your_linkedin_client_secret
TWITTER_API_KEY=your_twitter_api_key
TWITTER_API_SECRET=your_twitter_api_secret
FACEBOOK_APP_ID=your_facebook_app_id
FACEBOOK_APP_SECRET=your_facebook_app_secret
INSTAGRAM_BUSINESS_ACCOUNT_ID=your_instagram_business_account_id

# Health Endpoint (optional)
METRICS_AUTH_TOKEN=your_secure_token_here
```

### Step 2: Company Handbook

Create `vault/Company_Handbook.md`:

```markdown
# Company Handbook

## Rules of Engagement

1. **Email Communication**: Always be polite and professional
2. **Social Media**: Post only during business hours (9 AM - 6 PM)
3. **Payments**: Flag any payment over $500 for manual approval
4. **Invoices**: Send within 24 hours of service completion

## Subscription Patterns

Flag for review if:
- No login in 30 days
- Cost increased > 20%
- Duplicate functionality with another tool

## Business Goals

### Q1 2026 Objectives

**Revenue Target**: $10,000/month
**Current MTD**: $4,500

### Key Metrics

| Metric | Target | Alert Threshold |
|--------|--------|-----------------|
| Client response time | < 24 hours | > 48 hours |
| Invoice payment rate | > 90% | < 80% |
| Software costs | < $500/month | > $600/month |
```

### Step 3: Gmail OAuth Setup (Optional)

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create new project or select existing
3. Enable Gmail API
4. Create OAuth 2.0 credentials
5. Download `credentials.json`
6. Place in `FTE/credentials/gmail_credentials.json`
7. Run authentication flow:

```bash
cd FTE
python scripts/auth/gmail_auth.py
```

### Step 4: WhatsApp Session Setup (Optional)

```bash
cd FTE

# Initialize WhatsApp session
python scripts/auth/whatsapp_auth.py

# Scan QR code with WhatsApp mobile app
# Session saved to vault/State/whatsapp_session/
```

---

## First Run

### Start Watchers

```bash
cd FTE

# Start all watchers
python src/watchers/gmail_watcher.py &
python src/watchers/whatsapp_watcher.py &
python src/filesystem_watcher.py &

# Or use the start script (Windows)
.\scripts\start-watchers.bat
```

### Start Health Endpoint

```bash
cd FTE

# Start FastAPI health endpoint
python src/api/health_endpoint.py

# Health endpoint available at http://localhost:8000/health
```

### Start Process Manager

```bash
cd FTE

# Start process manager (monitors watchers)
python src/process_manager.py
```

### Verify Watchers Running

Check `vault/Dashboard.md`:

```markdown
# FTE Agent Dashboard

## System Status: RUNNING

| Component | Status | Last Check |
|-----------|--------|------------|
| Gmail Watcher | ✅ Running | 2026-04-02T10:30:00 |
| WhatsApp Watcher | ✅ Running | 2026-04-02T10:30:00 |
| FileSystem Watcher | ✅ Running | 2026-04-02T10:30:00 |
```

---

## Health Check Verification

### Manual Health Check

```bash
# Check health endpoint
curl http://localhost:8000/health

# Expected response:
{
    "status": "healthy",
    "timestamp": "2026-04-02T10:30:00",
    "components": {
        "watcher_gmail": {"status": "healthy"},
        "watcher_whatsapp": {"status": "healthy"},
        "watcher_filesystem": {"status": "healthy"}
    },
    "system": {
        "cpu_percent": 45.2,
        "memory_percent": 62.1,
        "disk_percent": 55.0
    }
}
```

### Test Email Flow

1. Drop test email action in `vault/Inbox/`:

```markdown
---
type: email
to: test@example.com
subject: Test Email
body: This is a test email from FTE-Agent
---
```

2. Move to `vault/Needs_Action/`
3. Check logs in `vault/Logs/YYYY-MM-DD.json`
4. Verify email sent (or logged if DRY_RUN=true)

### Test Approval Workflow

1. Create approval request:

```python
from src.skills.request_approval import request_approval

request_approval(
    action="payment",
    action_details={"amount": 100.00, "recipient": "Test Vendor"},
    risk_level="high"
)
```

2. Check `vault/Pending_Approval/` for approval file
3. Move to `vault/Approved/` to approve
4. Move to `vault/Rejected/` to reject

### Test CEO Briefing Generation

```bash
cd FTE

# Generate briefing manually
python -c "from src.skills.briefing_skills import generate_ceo_briefing; generate_ceo_briefing()"

# Check vault/Briefings/ for generated briefing
```

### Schedule CEO Briefing (Windows)

```bash
# Schedule for every Monday at 8 AM
.\scripts\schedule-ceo-briefing.bat

# List scheduled tasks
schtasks /Query /TN "FTE-CEO-Briefing"

# Disable task
.\scripts\disable-ceo-briefing.bat

# Remove task
.\scripts\remove-ceo-briefing.bat
```

---

## API Reference

### Email MCP Server

**Endpoint**: `src/mcp_servers/email_mcp/handlers.py`

#### send_email

```python
def send_email(
    to: str,
    subject: str,
    body: str,
    attachments: list[str] | None = None,
    dry_run: bool = False
) -> dict[str, Any]:
    """
    Send email via Gmail API.

    Args:
        to: Recipient email address
        subject: Email subject
        body: Email body text
        attachments: List of file paths to attach
        dry_run: Log without sending

    Returns:
        dict with message_id, status

    Example:
        >>> result = send_email("user@example.com", "Test", "Body")
        >>> result["status"]
        'sent'
    """
```

#### draft_email

```python
def draft_email(
    to: str,
    subject: str,
    body: str,
    attachments: list[str] | None = None
) -> dict[str, Any]:
    """
    Create Gmail draft.

    Args:
        to: Recipient email address
        subject: Email subject
        body: Email body text
        attachments: List of file paths to attach

    Returns:
        dict with draft_id

    Example:
        >>> result = draft_email("user@example.com", "Test", "Body")
        >>> result["draft_id"]
        'r1234567890'
    """
```

#### search_emails

```python
def search_emails(
    query: str,
    max_results: int = 10
) -> list[dict[str, Any]]:
    """
    Search Gmail messages.

    Args:
        query: Gmail search query (e.g., "from:user@example.com")
        max_results: Maximum results to return

    Returns:
        List of messages with id, snippet, from, subject, date

    Example:
        >>> messages = search_emails("is:unread", max_results=5)
        >>> len(messages)
        5
    """
```

---

### WhatsApp MCP Server

**Endpoint**: `src/mcp_servers/whatsapp_mcp/handlers.py`

#### send_whatsapp

```python
def send_whatsapp(
    contact: str,
    message: str
) -> dict[str, Any]:
    """
    Send WhatsApp message.

    Args:
        contact: Contact name or phone number
        message: Message text

    Returns:
        dict with status, timestamp

    Example:
        >>> result = send_whatsapp("+1234567890", "Hello!")
        >>> result["status"]
        'sent'
    """
```

---

### Social MCP Server

**Endpoint**: `src/mcp_servers/social_mcp/`

#### post_linkedin

```python
def post_linkedin(
    text: str,
    image_url: str | None = None
) -> dict[str, Any]:
    """
    Create LinkedIn post.

    Args:
        text: Post text (max 3000 characters)
        image_url: Optional image URL

    Returns:
        dict with post_id, status

    Example:
        >>> result = post_linkedin("Excited to announce...")
        >>> result["post_id"]
        'urn:li:share:1234567890'
    """
```

#### post_twitter

```python
def post_twitter(
    text: str,
    media_urls: list[str] | None = None
) -> dict[str, Any]:
    """
    Create tweet.

    Args:
        text: Tweet text (max 280 characters)
        media_urls: Optional list of media URLs

    Returns:
        dict with tweet_id, status

    Example:
        >>> result = post_twitter("Hello Twitter!")
        >>> result["tweet_id"]
        '1234567890'
    """
```

#### post_facebook

```python
def post_facebook(
    page_id: str,
    content: str,
    image_url: str | None = None
) -> dict[str, Any]:
    """
    Create Facebook page post.

    Args:
        page_id: Facebook page ID
        content: Post content
        image_url: Optional image URL

    Returns:
        dict with post_id, status

    Example:
        >>> result = post_facebook("123456789", "Hello Facebook!")
        >>> result["post_id"]
        '123456789_987654321'
    """
```

#### post_instagram

```python
def post_instagram(
    image_path: str,
    caption: str
) -> dict[str, Any]:
    """
    Create Instagram media post.

    Args:
        image_path: Path to image file
        caption: Post caption

    Returns:
        dict with media_id, status

    Example:
        >>> result = post_instagram("image.jpg", "Beautiful day!")
        >>> result["media_id"]
        '1234567890'
    """
```

---

### Odoo MCP Server

**Endpoint**: `src/mcp_servers/odoo_mcp/handlers.py`

#### create_invoice

```python
def create_invoice(
    partner_id: int,
    amount: float,
    description: str,
    invoice_date: str | None = None
) -> dict[str, Any]:
    """
    Create invoice in Odoo.

    Args:
        partner_id: Odoo partner ID (customer)
        amount: Invoice amount
        description: Invoice description
        invoice_date: Optional invoice date (YYYY-MM-DD)

    Returns:
        dict with invoice_id, number, status

    Example:
        >>> result = create_invoice(1, 1000.00, "Consulting services")
        >>> result["invoice_id"]
        123
        >>> result["number"]
        'INV/2026/0001'
    """
```

#### record_payment

```python
def record_payment(
    invoice_id: int,
    amount: float,
    payment_date: str | None = None
) -> dict[str, Any]:
    """
    Record payment against invoice.

    Args:
        invoice_id: Odoo invoice ID
        amount: Payment amount
        payment_date: Optional payment date (YYYY-MM-DD)

    Returns:
        dict with payment_id, status, remaining_balance

    Example:
        >>> result = record_payment(123, 1000.00)
        >>> result["payment_id"]
        456
        >>> result["remaining_balance"]
        0.0
    """
```

#### categorize_expense

```python
def categorize_expense(
    amount: float,
    description: str,
    category: str
) -> dict[str, Any]:
    """
    Categorize expense in Odoo.

    Args:
        amount: Expense amount
        description: Expense description
        category: Expense category (e.g., "Software", "Travel")

    Returns:
        dict with expense_id, status

    Example:
        >>> result = categorize_expense(50.00, "AWS bill", "Software")
        >>> result["expense_id"]
        789
    """
```

---

### Audit Skills

**Endpoint**: `src/skills/audit_skills.py`

#### query_logs

```python
def query_logs(
    date: str | None = None,
    action: str | None = None,
    result: str | None = None,
    component: str | None = None,
    limit: int = 1000
) -> list[dict[str, Any]]:
    """
    Query audit logs.

    Args:
        date: Date (YYYY-MM-DD) or range (YYYY-MM-DD:YYYY-MM-DD)
        action: Filter by action type
        result: Filter by result (success, failure, pending)
        component: Filter by component
        limit: Maximum results

    Returns:
        List of log entries

    Example:
        >>> logs = query_logs(date="2026-04-01", action="email_sent")
        >>> len(logs)
        15
    """
```

#### export_to_csv

```python
def export_to_csv(
    log_entries: list[dict],
    output_path: str,
    fields: list[str] | None = None
) -> Path:
    """
    Export logs to CSV.

    Args:
        log_entries: List of log entries
        output_path: Output file path
        fields: Fields to include

    Returns:
        Path to created CSV file

    Example:
        >>> csv_path = export_to_csv(logs, "logs.csv")
        >>> csv_path.exists()
        True
    """
```

---

### DLQ Skills

**Endpoint**: `src/skills/dlq_skills.py`

#### list_dlq_items

```python
def list_dlq_items(
    status: str | None = None,
    action_type: str | None = None,
    limit: int = 100
) -> list[dict[str, Any]]:
    """
    List DLQ items.

    Args:
        status: Filter by status (pending_review, resolved, discarded)
        action_type: Filter by action type
        limit: Maximum results

    Returns:
        List of DLQ items

    Example:
        >>> items = list_dlq_items(status="pending_review")
        >>> len(items)
        5
    """
```

#### resolve_dlq_item

```python
def resolve_dlq_item(
    item_id: str,
    resolution: str,
    notes: str | None = None
) -> bool:
    """
    Resolve DLQ item.

    Args:
        item_id: DLQ item UUID
        resolution: Resolution description
        notes: Optional additional notes

    Returns:
        True if resolved

    Example:
        >>> resolve_dlq_item("abc-123", "Fixed credentials")
        True
    """
```

---

## Troubleshooting

### Common Issues

#### Watcher Not Starting

**Symptom**: Watcher process exits immediately

**Solution**:
1. Check Python version: `python --version` (must be 3.13+)
2. Check dependencies: `pip install -r FTE/requirements.txt`
3. Check vault path permissions
4. Review logs in `vault/Logs/`

#### Gmail API Authentication Failed

**Symptom**: `google.auth.exceptions.RefreshError`

**Solution**:
1. Verify `credentials.json` is valid
2. Re-run authentication: `python scripts/auth/gmail_auth.py`
3. Check Gmail API is enabled in Google Cloud Console
4. Verify scopes in `.env`

#### Odoo Connection Timeout

**Symptom**: `requests.exceptions.ConnectionError`

**Solution**:
1. Verify Odoo is running: `curl http://localhost:8069`
2. Check Odoo URL in `.env`
3. Verify database name, user ID, password
4. Enable Odoo fallback mode

#### Circuit Breaker Open

**Symptom**: `CircuitBreakerOpenError`

**Solution**:
1. Check underlying service health
2. Wait for reset timeout (300 seconds)
3. Manually reset: `curl http://localhost:8000/health/reset?component=<name>`
4. Review error logs

### Getting Help

- **Documentation**: `FTE/docs/`
- **Logs**: `vault/Logs/YYYY-MM-DD.json`
- **Dashboard**: `vault/Dashboard.md`
- **Health Endpoint**: `http://localhost:8000/health`

---

## Next Steps

1. **Configure Integrations**: Set up Gmail, WhatsApp, social media APIs
2. **Test Workflows**: Run through test scenarios in Section 5
3. **Schedule CEO Briefing**: Set up Monday 8 AM task
4. **Monitor Dashboard**: Check `vault/Dashboard.md` daily
5. **Review Logs**: Audit `vault/Logs/` weekly

---

*Generated by FTE-Agent Development Team*  
*Last Updated: 2026-04-02*
