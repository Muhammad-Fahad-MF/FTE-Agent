# Data Model: Platinum Tier - Cloud + Local Executive

**Feature**: Platinum Tier (v6.0.0)
**Branch**: `004-platinum-tier-cloud-executive`
**Date**: 2026-04-02
**Status**: Draft

---

## Overview

This document defines the data entities, relationships, and validation rules for Platinum Tier's two-agent architecture. The data model extends Gold Tier's vault file structure with Cloud/Local specialization, claim-by-move ownership, and security boundary enforcement.

**Key Design Principles**:
1. **File-based entities**: All entities represented as Markdown files in vault folders
2. **YAML frontmatter**: Structured metadata for programmatic access
3. **Atomic operations**: File moves represent state transitions
4. **Single-writer rules**: Prevent sync conflicts (Dashboard.md: Local-only)
5. **Security boundaries**: Secrets never in vault files (OS Credential Manager only)

---

## Core Entities

### 1. VaultFile (Base Entity)

**Description**: Abstract base entity for all vault files with common metadata.

**Fields**:
```yaml
type: string              # Entity type (email, whatsapp, invoice, social_post, etc.)
id: string                # Unique identifier (UUID v4 or timestamp-based)
created_at: datetime      # ISO-8601 timestamp
updated_at: datetime      # ISO-8601 timestamp (last modification)
status: string            # pending|in_progress|awaiting_approval|completed|rejected|cancelled
source: string            # Origin (gmail|whatsapp|odoo|manual)
correlation_id: string    # UUID tracking request across components
dry_run: boolean          # true|false (DEV_MODE flag)
spec_version: string      # Vault file format version (default: "1.0")
```

**Relationships**:
- Parent: None (base entity)
- Children: Email, WhatsAppMessage, Invoice, SocialPost, ApprovalRequest, ClaimFile, UpdateFile, SignalFile

**Validation Rules**:
- `type`: Required, non-empty string
- `id`: Required, unique within vault
- `created_at`: Required, ISO-8601 format
- `updated_at`: Required, must be >= created_at
- `status`: Required, one of allowed values
- `source`: Required, one of allowed sources
- `correlation_id`: Optional, UUID format if provided
- `spec_version`: Required, semver format (e.g., "1.0")

---

### 2. Email (Inbox Item)

**Description**: Incoming email detected by Gmail Watcher (Cloud or Local).

**Fields** (extends VaultFile):
```yaml
type: email
from: string              # Sender email address
to: array[string]         # Recipient email addresses
cc: array[string]         # CC recipients (optional)
bcc: array[string]        # BCC recipients (optional)
subject: string           # Email subject line
body_text: string         # Plain text body
body_html: string         # HTML body (optional)
attachments: array[object]  # Attachment metadata
  - filename: string
  - content_type: string
  - size_bytes: integer
  - path: string          # Local file path (if downloaded)
received_at: datetime     # Email received timestamp
labels: array[string]     # Gmail labels (optional)
message_id: string        # Gmail message ID
thread_id: string         # Gmail thread ID
priority: string          # low|normal|high|urgent (auto-classified)
requires_reply: boolean   # True if reply needed
reply_deadline: datetime  # Reply deadline (optional, calculated from SLA)
```

**Relationships**:
- Parent: VaultFile
- Related: ApprovalRequest (if reply requires approval), DraftEmail (if reply drafted)

**Validation Rules**:
- `from`: Required, valid email format
- `to`: Required, non-empty array of valid email addresses
- `subject`: Required, non-empty string
- `body_text` or `body_html`: At least one required
- `received_at`: Required, ISO-8601 format
- `message_id`: Required, unique Gmail message ID
- `priority`: Auto-classified based on content (urgent keywords, sender importance)

**Example File**: `/vault/Inbox/Email/EMAIL_20260402_081530_abc123.md`

```markdown
---
type: email
id: EMAIL_20260402_081530_abc123
created_at: 2026-04-02T08:15:30Z
updated_at: 2026-04-02T08:15:30Z
status: pending
source: gmail
correlation_id: corr_abc123
spec_version: "1.0"
from: client@example.com
to: ["user@company.com"]
subject: Project Update Request
received_at: 2026-04-02T08:15:30Z
message_id: <msg123@gmail.com>
thread_id: thread_456
priority: high
requires_reply: true
reply_deadline: 2026-04-03T08:15:30Z
---

## Body

Hi,

I need a project update by end of week. Can you provide status on:
1. Current milestones
2. Budget utilization
3. Upcoming deliverables

Thanks,
Client
```

---

### 3. DraftEmail (Reply Draft)

**Description**: Email reply drafted by Cloud Agent (draft-only, requires Local approval to send).

**Fields** (extends VaultFile):
```yaml
type: draft_email
in_reply_to: string       # Original email ID
to: array[string]         # Recipients
cc: array[string]         # CC (optional)
subject: string           # Reply subject (Re: Original)
body_text: string         # Reply body
body_html: string         # HTML reply (optional)
attachments: array[string]  # Attachment file paths
drafted_by: string        # Cloud|Local (agent that drafted)
drafted_at: datetime      # Draft creation timestamp
ready_for_approval: boolean  # True if ready for Local review
```

**Relationships**:
- Parent: VaultFile
- Related: Email (in_reply_to), ApprovalRequest (when submitted for approval)

**State Transitions**:
```
drafting → ready_for_approval → pending_approval → approved → sent
                                ↓
                            rejected → archived
```

**Validation Rules**:
- `in_reply_to`: Required, valid email ID reference
- `to`: Required, non-empty array
- `body_text` or `body_html`: At least one required
- `drafted_by`: Required, Cloud|Local
- `ready_for_approval`: Default false, set true when draft complete

**Example File**: `/vault/Drafts/Email/DRAFT_EMAIL_20260402_082000_xyz789.md`

```markdown
---
type: draft_email
id: DRAFT_EMAIL_20260402_082000_xyz789
created_at: 2026-04-02T08:20:00Z
updated_at: 2026-04-02T08:20:00Z
status: pending
source: gmail
spec_version: "1.0"
in_reply_to: EMAIL_20260402_081530_abc123
to: ["client@example.com"]
subject: "Re: Project Update Request"
body_text: |
  Hi Client,
  
  Thank you for reaching out. I'm currently compiling the project update and will have it ready by end of week.
  
  Current status:
  1. Milestones: On track (80% complete)
  2. Budget: 75% utilized (within projections)
  3. Deliverables: Final review scheduled for Friday
  
  I'll send the detailed report by Friday EOD.
  
  Best regards,
  User
drafted_by: Cloud
drafted_at: 2026-04-02T08:20:00Z
ready_for_approval: true
---

## Approval Required

This draft email is ready for review and approval.

**To Approve**: Move this file to `/Approved/Email/`
**To Reject**: Move this file to `/Rejected/Email/`
```

---

### 4. WhatsAppMessage

**Description**: WhatsApp message detected by WhatsApp Watcher (Cloud or Local).

**Fields** (extends VaultFile):
```yaml
type: whatsapp_message
from: string              # Sender phone number or name
to: string                # Recipient phone number
message_text: string      # Message content
message_type: string      # text|image|video|audio|document|location
media_url: string         # Media file URL (if applicable)
media_path: string        # Local file path (if downloaded)
received_at: datetime     # Message received timestamp
chat_id: string           # WhatsApp chat ID
message_id: string        # WhatsApp message ID
is_group: boolean         # True if group chat
group_name: string        # Group name (if group chat)
priority: string          # low|normal|high|urgent (auto-classified)
requires_reply: boolean   # True if reply needed
keywords: array[string]   # Detected keywords (e.g., "urgent", "asap")
```

**Relationships**:
- Parent: VaultFile
- Related: DraftWhatsApp (if reply drafted)

**Validation Rules**:
- `from`: Required, valid phone number format
- `to`: Required, valid phone number format
- `message_text` or `media_url`: At least one required
- `received_at`: Required, ISO-8601 format
- `message_id`: Required, unique WhatsApp message ID
- `message_type`: Required, one of allowed types

**Example File**: `/vault/Inbox/WhatsApp/WA_20260402_093000_def456.md`

---

### 5. DraftWhatsApp (Reply Draft)

**Description**: WhatsApp reply drafted by Cloud Agent (draft-only, requires Local approval to send).

**Fields** (extends VaultFile):
```yaml
type: draft_whatsapp
in_reply_to: string       # Original message ID
to: string                # Recipient phone number
message_text: string      # Reply message
message_type: string      # text|image|video|document
media_path: string        # Media file path (if applicable)
drafted_by: string        # Cloud|Local
drafted_at: datetime
ready_for_approval: boolean
```

**Relationships**:
- Parent: VaultFile
- Related: WhatsAppMessage (in_reply_to)

**State Transitions**: Same as DraftEmail

---

### 6. Invoice (Odoo)

**Description**: Odoo invoice (created by Cloud in draft status, posted by Local after approval).

**Fields** (extends VaultFile):
```yaml
type: invoice
invoice_number: string    # Odoo invoice number (assigned on post)
customer_id: string       # Odoo customer ID
customer_name: string     # Customer display name
customer_email: string    # Customer email (for sending)
invoice_date: datetime    # Invoice date
due_date: datetime        # Payment due date
currency: string          # USD|EUR|GBP (default: USD)
status: string            # draft|posted|sent|paid|cancelled
odoo_state: string        # Odoo invoice state (draft|posted|cancel)
line_items: array[object]
  - product_id: string    # Odoo product ID
    product_name: string  # Product display name
    description: string   # Line item description
    quantity: number      # Quantity
    unit_price: number    # Price per unit
    discount: number      # Discount percentage (0-100)
    taxes: array[number]  # Tax percentages (e.g., [10, 5])
    subtotal: number      # Calculated: (qty * price * (1 - discount/100)) + taxes
total_untaxed: number     # Sum of subtotals (pre-tax)
total_tax: number         # Total tax amount
total: number             # Grand total (untaxed + tax)
created_by: string        # Cloud|Local (agent that created)
posted_by: string         # Cloud|Local (agent that posted - Local only)
posted_at: datetime       # Posting timestamp
sent_to_customer: boolean # True if sent to customer
```

**Relationships**:
- Parent: VaultFile
- Related: Email (if invoice request came via email)

**State Transitions**:
```
draft → pending_approval → approved → posted → sent → paid
                            ↓
                        rejected → cancelled
```

**Validation Rules**:
- `customer_id`: Required, valid Odoo customer ID
- `customer_name`: Required, non-empty string
- `invoice_date`: Required, ISO-8601 format
- `due_date`: Required, must be >= invoice_date
- `line_items`: Required, non-empty array (minimum 1 line)
- `total`: Calculated field (must equal sum of line subtotals + tax)
- `odoo_state`: Required, draft|posted|cancel
- `posted_by`: Required if odoo_state = posted (must be Local)

**Example File**: `/vault/Drafts/Invoices/INV_DRAFT_20260402_100000_ghi789.md`

```markdown
---
type: invoice
id: INV_DRAFT_20260402_100000_ghi789
created_at: 2026-04-02T10:00:00Z
updated_at: 2026-04-02T10:00:00Z
status: draft
source: odoo
spec_version: "1.0"
invoice_number: DRAFT-2026-001
customer_id: res_partner_123
customer_name: Acme Corporation
customer_email: billing@acme.com
invoice_date: 2026-04-02
due_date: 2026-05-02
currency: USD
status: draft
odoo_state: draft
line_items:
  - product_id: product_service_001
    product_name: Consulting Services
    description: Business process automation consulting
    quantity: 10
    unit_price: 150
    discount: 0
    taxes: [10]
    subtotal: 1650
total_untaxed: 1650
total_tax: 165
total: 1815
created_by: Cloud
posted_by: null
posted_at: null
sent_to_customer: false
---

## Invoice Details

**Invoice Number**: DRAFT-2026-001 (Draft)
**Customer**: Acme Corporation
**Date**: 2026-04-02
**Due Date**: 2026-05-02

## Line Items

| Description | Qty | Unit Price | Subtotal |
|-------------|-----|------------|----------|
| Consulting Services | 10 | $150.00 | $1,650.00 |

**Total (excl. tax)**: $1,650.00
**Tax (10%)**: $165.00
**Grand Total**: $1,815.00

## Approval Required

**To Approve**: Move to `/Approved/Invoices/` → Local will post and send
**To Reject**: Move to `/Rejected/Invoices/`
```

---

### 7. SocialPost

**Description**: Social media post (drafted by Cloud, posted by Local after approval).

**Fields** (extends VaultFile):
```yaml
type: social_post
platform: string          # linkedin|facebook|instagram|twitter
post_content: string      # Post text content
media_paths: array[string]  # Image/video file paths
hashtags: array[string]   # Hashtags (optional)
scheduled_at: datetime    # Scheduled post time (optional)
status: string            # draft|pending_approval|approved|posted|failed
posted_by: string         # Cloud|Local (Local only for posting)
posted_at: datetime       # Actual post timestamp
post_url: string          # URL of posted content (after posting)
analytics: object         # Post analytics (after posting)
  - likes: integer
  - comments: integer
  - shares: integer
  - impressions: integer
```

**Relationships**:
- Parent: VaultFile
- Related: ApprovalRequest (when submitted for approval)

**State Transitions**:
```
draft → pending_approval → approved → posted
                            ↓
                        rejected → archived
```

**Validation Rules**:
- `platform`: Required, one of linkedin|facebook|instagram|twitter
- `post_content`: Required, non-empty string (max length per platform)
- `posted_by`: Required if status = posted (must be Local)
- `post_url`: Required if status = posted

**Platform-Specific Limits**:
- LinkedIn: 3,000 characters, 4 images max
- Facebook: 63,206 characters, 10 images max
- Instagram: 2,200 characters, 10 images max
- Twitter: 280 characters, 4 images max

---

### 8. ApprovalRequest

**Description**: Approval request created by Cloud for Local review.

**Fields** (extends VaultFile):
```yaml
type: approval_request
action: string            # send_email|send_whatsapp|post_invoice|post_social
action_details: object    # Action-specific parameters
risk_level: string        # low|medium|high (auto-calculated)
created_at: datetime      # Request creation timestamp
expires_at: datetime      # Expiry timestamp (24 hours from creation)
approved_by: string       # User name (if approved)
approved_at: datetime     # Approval timestamp
rejection_reason: string  # Reason (if rejected)
```

**Relationships**:
- Parent: VaultFile
- Related: DraftEmail, DraftWhatsApp, Invoice, SocialPost (action_details reference)

**State Transitions**:
```
pending → approved → executed → completed
        ↓
    rejected → archived
```

**Validation Rules**:
- `action`: Required, one of allowed actions
- `action_details`: Required, valid object for action type
- `risk_level`: Required, one of low|medium|high
- `expires_at`: Required, must be > created_at (24 hours default)
- `approved_by`: Required if approved
- `approved_at`: Required if approved

**Example File**: `/vault/Pending_Approval/Email/APPROVAL_EMAIL_20260402_082500_jkl012.md`

```markdown
---
type: approval_request
id: APPROVAL_EMAIL_20260402_082500_jkl012
created_at: 2026-04-02T08:25:00Z
updated_at: 2026-04-02T08:25:00Z
status: pending
source: gmail
spec_version: "1.0"
action: send_email
action_details:
  draft_id: DRAFT_EMAIL_20260402_082000_xyz789
  to: ["client@example.com"]
  subject: "Re: Project Update Request"
  body_preview: "Hi Client, Thank you for reaching out..."
risk_level: low
expires_at: 2026-04-03T08:25:00Z
approved_by: null
approved_at: null
rejection_reason: null
---

## Approval Request

**Action**: Send Email Reply
**Risk Level**: Low (known contact, single recipient)

## Details

**To**: client@example.com
**Subject**: Re: Project Update Request
**Preview**: Hi Client, Thank you for reaching out. I'm currently compiling...

## Expiry

This approval request expires in 24 hours (2026-04-03T08:25:00Z).

**To Approve**: Move this file to `/Approved/Email/`
**To Reject**: Move this file to `/Rejected/Email/` with rejection reason
```

---

### 9. ClaimFile (Ownership Marker)

**Description**: Claim marker indicating which agent (Cloud or Local) owns a task.

**Fields** (extends VaultFile):
```yaml
type: claim_marker
agent: string             # Cloud|Local (claiming agent)
claimed_at: datetime      # Claim timestamp
task_id: string           # ID of claimed task
original_path: string     # Original file path before claim
status: string            # in_progress|completed|abandoned
expected_completion: datetime  # Expected completion time
completed_at: datetime    # Actual completion timestamp (if completed)
```

**Relationships**:
- Parent: VaultFile
- Related: Any task file (Email, WhatsApp, Invoice, SocialPost)

**Validation Rules**:
- `agent`: Required, Cloud|Local
- `claimed_at`: Required, ISO-8601 format
- `task_id`: Required, valid task ID
- `original_path`: Required, absolute vault path
- `status`: Required, one of in_progress|completed|abandoned
- Stale detection: claimed_at > 5 minutes ago with status = in_progress → reclaimable

**Example File**: `/vault/In_Progress/Cloud/CLAIM_20260402_082000_mno345.md`

```markdown
---
type: claim_marker
id: CLAIM_20260402_082000_mno345
created_at: 2026-04-02T08:20:00Z
updated_at: 2026-04-02T08:20:00Z
status: in_progress
spec_version: "1.0"
agent: Cloud
claimed_at: 2026-04-02T08:20:00Z
task_id: EMAIL_20260402_081530_abc123
original_path: /vault/Needs_Action/Email/EMAIL_20260402_081530_abc123.md
expected_completion: 2026-04-02T08:30:00Z
completed_at: null
---

## Claim Marker

**Claimed By**: Cloud Agent
**Claimed At**: 2026-04-02T08:20:00Z
**Task**: EMAIL_20260402_081530_abc123
**Status**: In Progress
**Expected Completion**: 2026-04-02T08:30:00Z

This file is being processed by Cloud Agent. Local Agent should not modify.
```

---

### 10. UpdateFile (Status Update)

**Description**: Status update written by Cloud to communicate events to Local.

**Fields** (extends VaultFile):
```yaml
type: update
domain: string            # email|whatsapp|invoice|social|system
update_type: string       # detected|drafted|completed|alert
summary: string           # Brief summary
details: object           # Update-specific details
priority: string          # low|normal|high|urgent
read_by_local: boolean    # True if Local has read
read_at: datetime         # Read timestamp
```

**Relationships**:
- Parent: VaultFile
- Related: Any task file (reference in details)

**Validation Rules**:
- `domain`: Required, one of email|whatsapp|invoice|social|system
- `update_type`: Required, one of detected|drafted|completed|alert
- `summary`: Required, non-empty string
- `priority`: Required, one of low|normal|high|urgent
- `read_by_local`: Default false

**Example File**: `/vault/Updates/Email/UPDATE_20260402_082000_pqr678.md`

```markdown
---
type: update
id: UPDATE_20260402_082000_pqr678
created_at: 2026-04-02T08:20:00Z
updated_at: 2026-04-02T08:20:00Z
status: completed
spec_version: "1.0"
domain: email
update_type: drafted
summary: Cloud drafted reply to urgent client email
details:
  task_id: EMAIL_20260402_081530_abc123
  draft_id: DRAFT_EMAIL_20260402_082000_xyz789
  from: client@example.com
  subject: Project Update Request
  priority: high
priority: high
read_by_local: false
read_at: null
---

## Update: Email Draft Created

**Domain**: Email
**Type**: Draft Created
**Priority**: High

## Summary

Cloud Agent detected an urgent email from client@example.com and drafted a reply.

## Details

**Original Email**: EMAIL_20260402_081530_abc123
**Draft Reply**: DRAFT_EMAIL_20260402_082000_xyz789
**From**: client@example.com
**Subject**: Project Update Request
**Received**: 2026-04-02T08:15:30Z
**Drafted**: 2026-04-02T08:20:00Z

## Action Required

Review the draft reply in `/Drafts/Email/` and approve/reject.
```

---

### 11. SignalFile (Urgent Alert)

**Description**: Urgent alert/notification for immediate Local attention.

**Fields** (extends VaultFile):
```yaml
type: signal
domain: string            # security|system|business|urgent
signal_type: string       # breach|crash|threshold_breach|critical_event
title: string             # Alert title
message: string           # Alert message
severity: string          # critical|high|medium|low
acknowledged_by: string   # Local user name (if acknowledged)
acknowledged_at: datetime # Acknowledgment timestamp
```

**Relationships**:
- Parent: VaultFile
- Related: Any task file or system event

**Validation Rules**:
- `domain`: Required, one of security|system|business|urgent
- `signal_type`: Required, one of breach|crash|threshold_breach|critical_event
- `title`: Required, non-empty string
- `message`: Required, non-empty string
- `severity`: Required, one of critical|high|medium|low

**Example File**: `/vault/Signals/Security/SIGNAL_20260402_120000_stu901.md`

```markdown
---
type: signal
id: SIGNAL_20260402_120000_stu901
created_at: 2026-04-02T12:00:00Z
updated_at: 2026-04-02T12:00:00Z
status: new
spec_version: "1.0"
domain: security
signal_type: breach
title: Security Boundary Breach Attempt Detected
message: Attempted to sync .env file to Cloud - BLOCKED
severity: critical
acknowledged_by: null
acknowledged_at: null
---

## 🚨 SECURITY ALERT

**Type**: Security Boundary Breach Attempt
**Severity**: CRITICAL
**Time**: 2026-04-02T12:00:00Z

## Details

Cloud Agent detected an attempt to sync a secret file to the vault:

**File Path**: `.env`
**Action**: Blocked and quarantined
**Source**: Pre-sync validation

## Immediate Actions Required

1. Review Local vault for unauthorized files
2. Verify .gitignore configuration
3. Check for credential exposure
4. Rotate compromised credentials (if any)

## Investigation

See audit log: `/vault/Logs/security_2026-04-02.json`
```

---

### 12. Dashboard (Single-Writer Status)

**Description**: Central status dashboard (Local single-writer, Cloud reads only).

**Fields**:
```yaml
type: dashboard
last_updated: datetime    # Last update timestamp
updated_by: string        # Local (always)
system_status: string     # healthy|degraded|unhealthy
cloud_status: string      # online|offline|degraded
local_status: string      # online|offline
last_sync: datetime       # Last vault sync time
sync_status: string       # synced|syncing|failed|conflict
metrics: object
  - pending_count: integer    # Items in Needs_Action/
  - in_progress_count: integer # Items in In_Progress/
  - pending_approval_count: integer # Items in Pending_Approval/
  - draft_count: integer      # Items in Drafts/
  - completed_today: integer  # Items completed today
  - alerts_count: integer     # Unacknowledged alerts
watchers: object
  - gmail: string         # running|stopped|error
  - whatsapp: string      # running|stopped|error
  - filesystem: string    # running|stopped|error
cloud_health: object      # From Cloud health endpoint
  - uptime_seconds: integer
  - cpu_percent: number
  - memory_percent: number
  - disk_percent: number
recent_activity: array[object]  # Last 10 actions
  - timestamp: datetime
    action: string
    agent: string
    status: string
```

**Relationships**:
- Parent: None (standalone)
- Related: All vault entities (aggregated status)

**Validation Rules**:
- `last_updated`: Required, ISO-8601 format
- `updated_by`: Required, must be "Local" (single-writer rule)
- `system_status`: Required, one of healthy|degraded|unhealthy
- `sync_status`: Required, one of synced|syncing|failed|conflict
- `recent_activity`: Array of last 10 actions (newest first)

**Example File**: `/vault/Dashboard.md`

```markdown
---
type: dashboard
last_updated: 2026-04-02T12:30:00Z
updated_by: Local
system_status: healthy
cloud_status: online
local_status: online
last_sync: 2026-04-02T12:29:45Z
sync_status: synced
metrics:
  pending_count: 3
  in_progress_count: 2
  pending_approval_count: 5
  draft_count: 8
  completed_today: 12
  alerts_count: 0
watchers:
  gmail: running
  whatsapp: running
  filesystem: running
cloud_health:
  uptime_seconds: 86400
  cpu_percent: 45
  memory_percent: 62
  disk_percent: 71
recent_activity:
  - timestamp: 2026-04-02T12:29:45Z
    action: vault_sync
    agent: Cloud
    status: success
  - timestamp: 2026-04-02T12:25:00Z
    action: draft_created
    agent: Cloud
    status: success
    details: DRAFT_EMAIL_20260402_122500
  - timestamp: 2026-04-02T12:20:00Z
    action: email_detected
    agent: Cloud
    status: success
    details: EMAIL_20260402_122000
  # ... last 10 actions
---

# FTE-Agent Dashboard

**Last Updated**: 2026-04-02T12:30:00Z
**System Status**: 🟢 Healthy

## Agent Status

| Agent | Status | Details |
|-------|--------|---------|
| Cloud | 🟢 Online | Uptime: 24h, CPU: 45%, Memory: 62% |
| Local | 🟢 Online | User workstation |

## Vault Sync

**Last Sync**: 2026-04-02T12:29:45Z (15 seconds ago)
**Sync Status**: ✅ Synced
**Pending Changes**: 0

## Queue Summary

| Queue | Count | Trend |
|-------|-------|-------|
| Needs Action | 3 | ↓ -2 |
| In Progress | 2 | → 0 |
| Pending Approval | 5 | ↑ +3 |
| Drafts | 8 | ↑ +2 |
| Completed Today | 12 | ↑ +12 |

## Watchers

| Watcher | Status | Last Check |
|---------|--------|------------|
| Gmail | 🟢 Running | 2026-04-02T12:28:00Z |
| WhatsApp | 🟢 Running | 2026-04-02T12:29:00Z |
| FileSystem | 🟢 Running | 2026-04-02T12:27:00Z |

## Alerts

No active alerts.

## Recent Activity

1. 12:29:45 - Vault sync completed (Cloud)
2. 12:25:00 - Draft email created (Cloud)
3. 12:20:00 - Email detected (Cloud)
4. ...

---

*Dashboard is single-writer (Local only). Cloud writes updates to `/Updates/`.*
```

---

## Entity Relationship Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                         VAULT FILE ENTITIES                         │
└─────────────────────────────────────────────────────────────────────┘

                    ┌─────────────────┐
                    │   VaultFile     │
                    │   (Base Entity) │
                    └────────┬────────┘
                             │
         ┌───────────────────┼───────────────────┐
         │                   │                   │
         ▼                   ▼                   ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│     Email       │ │  WhatsAppMsg    │ │    Invoice      │
│  (Inbox Item)   │ │  (Inbox Item)   │ │   (Odoo)        │
└────────┬────────┘ └────────┬────────┘ └────────┬────────┘
         │                   │                   │
         │                   │                   │
         ▼                   ▼                   ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│   DraftEmail    │ │ DraftWhatsApp   │ │  ApprovalReq    │
│   (Reply)       │ │   (Reply)       │ │                 │
└────────┬────────┘ └────────┬────────┘ └────────┬────────┘
         │                   │                   │
         └───────────────────┼───────────────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │   ClaimFile     │
                    │ (Ownership)     │
                    └─────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                    CROSS-AGENT COMMUNICATION                        │
└─────────────────────────────────────────────────────────────────────┘

         Cloud Agent                          Local Agent
              │                                    │
              │  ┌──────────────────┐              │
              │  │   UpdateFile     │◄─────────────┤
              ├──│  (Status Update) │  Read        │
              │  └──────────────────┘              │
              │                                    │
              │  ┌──────────────────┐              │
              │  │   SignalFile     │◄─────────────┤
              ├──│   (Urgent Alert) │  Acknowledge │
              │  └──────────────────┘              │
              │                                    │
              │  ┌──────────────────┐              │
              │  │   Dashboard.md   │──────────────┤
              └─►│ (Single-Writer)  │  Write Only  │
                 └──────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                      STATE TRANSITIONS                              │
└─────────────────────────────────────────────────────────────────────┘

Draft Lifecycle:
  drafting → ready_for_approval → pending_approval → approved → executed → completed
                                  ↓
                              rejected → archived

Claim Lifecycle:
  unclaimed → claimed (in_progress) → completed
                         │
                         └──> abandoned (stale >5min) → reclaimable

Approval Lifecycle:
  pending → approved → executed → completed
          ↓
      rejected → archived
```

---

## Validation Rules Summary

### Required Fields (All Entities)

| Field | Type | Validation |
|-------|------|------------|
| type | string | Required, non-empty |
| id | string | Required, unique |
| created_at | datetime | Required, ISO-8601 |
| updated_at | datetime | Required, >= created_at |
| status | string | Required, one of allowed values |
| source | string | Required, one of allowed sources |
| spec_version | string | Required, semver format |

### Security Validation

- **Secret Detection**: All files scanned for secret patterns before sync
- **Path Validation**: All paths must start with vault_path (prevent traversal)
- **Single-Writer**: Dashboard.md updated_by must be "Local"
- **Claim Validation**: Claim files >5 minutes old are stale (reclaimable)

### Sync Validation

- **Exclusion Patterns**: `.env`, `tokens/`, `sessions/`, `banking/`, `credentials/`, `*.key`, `*.pem`
- **Conflict Resolution**: Last-write-wins (except Dashboard.md: local-wins)
- **File Size Limit**: Skip files >10MB (log warning)

---

## File Naming Conventions

| Entity Type | Pattern | Example |
|-------------|---------|---------|
| Email | `EMAIL_<timestamp>_<id>.md` | `EMAIL_20260402_081530_abc123.md` |
| Draft Email | `DRAFT_EMAIL_<timestamp>_<id>.md` | `DRAFT_EMAIL_20260402_082000_xyz789.md` |
| WhatsApp | `WA_<timestamp>_<id>.md` | `WA_20260402_093000_def456.md` |
| Invoice | `INV_DRAFT_<timestamp>_<id>.md` | `INV_DRAFT_20260402_100000_ghi789.md` |
| Approval | `APPROVAL_<domain>_<timestamp>_<id>.md` | `APPROVAL_EMAIL_20260402_082500_jkl012.md` |
| Claim | `CLAIM_<timestamp>_<id>.md` | `CLAIM_20260402_082000_mno345.md` |
| Update | `UPDATE_<domain>_<timestamp>_<id>.md` | `UPDATE_20260402_082000_pqr678.md` |
| Signal | `SIGNAL_<domain>_<timestamp>_<id>.md` | `SIGNAL_20260402_120000_stu901.md` |

**Timestamp Format**: `YYYYMMDD_HHMMSS` (sortable)
**ID Format**: `<random_string>` (6+ characters, alphanumeric)

---

## Next Steps

1. ✅ Data model complete (12 entities defined)
2. → Generate API contracts (OpenAPI spec for health endpoint)
3. → Generate quickstart guide (Cloud/Local setup)
4. → Update agent context with new technologies

---

**Status**: Phase 1 Data Model COMPLETE
**Date**: 2026-04-02
**Next**: API Contracts & Quickstart
