# Silver Tier Specification - FTE-Agent Functional Assistant

**Version:** 2.0.0  
**Created:** 2026-03-19  
**Status:** Draft  
**Tier:** Silver (Functional Assistant)  
**Estimated Effort:** 20-30 hours  
**Branch:** `002-silver-tier-functional-assistant`

---

## 1. Executive Summary

### 1.1 Feature Name
Silver Tier - Functional Assistant

### 1.2 Tier Level
Silver (20-30 hours estimated implementation effort)

### 1.3 Primary Goal
Transform the Bronze tier foundation into a **FUNCTIONAL AI ASSISTANT** that:
- Monitors multiple input sources (Gmail, WhatsApp, FileSystem)
- Creates structured plans for multi-step tasks
- Requires human approval for sensitive actions (Human-in-the-Loop)
- Executes external actions via MCP servers or Python Skills
- Posts to LinkedIn automatically (with approval)
- Runs scheduled tasks (daily briefing, weekly audit)

### 1.4 Success Metrics
- **Functional:** 2+ watchers running continuously, 1+ MCP server operational, approval workflow fully functional
- **Quality:** 80%+ test coverage, 0 quality gate errors (ruff, black, mypy, bandit)
- **Performance:** Watcher intervals met (Gmail: 2min, WhatsApp: 30sec), approval detection <5 seconds
- **Documentation:** All Agent Skills documented with examples, setup guide complete

### 1.5 Out of Scope (Gold/Platinum Tier)
The following are explicitly **NOT** in Silver tier:
- ❌ Odoo accounting integration (Gold)
- ❌ Facebook/Instagram integration (Gold)
- ❌ Twitter/X integration (Gold)
- ❌ CEO Briefing with revenue tracking (Gold)
- ❌ Ralph Wiggum autonomous loop (Gold)
- ❌ Cloud deployment (Platinum)
- ❌ Multi-agent synchronization (Platinum)

---

## 2. Current State (Bronze Tier Foundation)

### 2.1 Completed Components

Silver tier builds upon the following **COMPLETE** Bronze tier components:

| Component | Status | Location | Description |
|-----------|--------|----------|-------------|
| Base Watcher | ✅ Complete | `FTE/src/base_watcher.py` | Abstract base class for all watchers |
| File System Watcher | ✅ Complete | `FTE/src/filesystem_watcher.py` | Monitors filesystem for new files |
| Python Skills | ✅ Complete | `FTE/src/skills.py` | Reusable AI capabilities |
| Audit Logger | ✅ Complete | `FTE/src/audit_logger.py` | JSON logging with correlation IDs |
| Test Suite | ✅ Complete (76 tests) | `FTE/tests/` | Unit, integration, chaos tests |
| Vault Structure | ✅ Complete | `FTE/vault/` | Organized file storage |
| Constitution v4.0.0 | ✅ Complete | `.specify/memory/constitution.md` | Project principles with Silver Tier support |

### 2.2 Existing Vault Structure (Bronze)

```
FTE/vault/
├── Inbox/              # File drop location for manual triggers
├── Needs_Action/       # Items requiring processing (watchers drop here)
├── Done/               # Completed items
├── Logs/               # Audit logs (JSON format)
├── Dashboard.md        # System status (single-writer: orchestrator only)
└── Company_Handbook.md # Rules of engagement, thresholds, configuration
```

### 2.3 Bronze Tier Guarantees (MUST Be Maintained)

All Silver tier implementations **MUST** maintain these Bronze tier guarantees:
- ✅ File dropped in `Inbox/` creates action file
- ✅ Qwen Code CLI reads action file and creates `Plan.md`
- ✅ `DEV_MODE=false` prevents external API calls
- ✅ STOP file (`vault/STOP`) halts orchestrator within 5 seconds
- ✅ All actions logged with `correlation_id`
- ✅ Path traversal attempts blocked
- ✅ `pytest --cov=src` shows 80%+ coverage
- ✅ Quality gates pass (ruff, black, mypy, bandit)
- ✅ Qwen Code CLI authenticated (OAuth, 1,000 free calls/day)

---

## 3. Silver Tier Requirements Matrix

| ID | Requirement | Priority | Dependencies | Acceptance Criteria | Est. Hours |
|----|-------------|----------|--------------|---------------------|------------|
| **S1** | Gmail Watcher | High | Google OAuth2 setup | Detects emails every 2min, creates action files in `Needs_Action/`, tracks processed IDs | 4 |
| **S2** | WhatsApp Watcher | High | Playwright installed | Detects keyword messages every 30sec, creates action files, preserves session | 4 |
| **S3** | Process Manager | High | S1, S2 | Keeps watchers alive, auto-restart on crash within 10sec, health check endpoint | 2 |
| **S4** | Plan.md Generation | High | S1-S3 | Creates structured plans with YAML frontmatter, step checkboxes, status tracking | 3 |
| **S5** | Email MCP Server | High | None | Sends/drafts emails via Gmail API, supports dry-run, requires approval for new contacts | 4 |
| **S6** | HITL Approval Workflow | High | S5 | Approval requests created, file movement detection (<5sec), execution on approval, expiry handling (24hr) | 4 |
| **S7** | LinkedIn Posting | Medium | S4, S6 | Content generation from `Business_Goals.md` + `Done/`, approval required, browser automation via Playwright, rate limiting (1 post/day max) | 4 |
| **S8** | Basic Scheduling | Medium | S4, S7 | Daily briefing (8:00 AM), Weekly audit (Sunday 10:00 PM), Windows Task Scheduler integration, output to `Briefings/` | 3 |
| **S9** | Agent Skills Documentation | Low | All | All 7+ skills documented with purpose, inputs, outputs, error handling, examples | 2 |

**Total Estimated Effort:** 30 hours

---

## 4. Technical Architecture

### 4.1 System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                      PERCEPTION LAYER (Watchers)                │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ GmailWatcher │  │ WhatsApp     │  │ FileSystem   │          │
│  │ (2-min)      │  │ Watcher      │  │ Watcher      │          │
│  │              │  │ (30-sec)     │  │ (60-sec)     │          │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘          │
│         │                 │                 │                   │
│         └─────────────────┴─────────────────┘                   │
│                           │                                     │
│                           ▼                                     │
│                  ┌─────────────────┐                           │
│                  │ Needs_Action/   │                           │
│                  │ - EMAIL_*.md    │                           │
│                  │ - WHATSAPP_*.md │                           │
│                  │ - FILE_*.md     │                           │
│                  └────────┬────────┘                           │
└───────────────────────────┼─────────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────────┐
│                      REASONING LAYER                            │
│              (Qwen Code CLI + Python Skills)                    │
├─────────────────────────────────────────────────────────────────┤
│                    ┌─────────────────┐                         │
│                    │  Qwen Code CLI  │                         │
│                    │  (AI Reasoning) │                         │
│                    └────────┬────────┘                         │
│                             │                                   │
│              ┌──────────────┼──────────────┐                   │
│              ▼              ▼              ▼                   │
│     ┌─────────────┐ ┌─────────────┐ ┌─────────────┐            │
│     │ create_plan │ │ request_    │ │ generate_   │            │
│     │ skill       │ │ approval    │ │ briefing    │            │
│     │             │ │ skill       │ │ skill       │            │
│     └──────┬──────┘ └──────┬──────┘ └──────┬──────┘            │
│            │               │                │                    │
│            │      ┌────────▼────────┐      │                    │
│            │      │ Pending_Approval│      │                    │
│            │      │ APPROVAL_*.md   │      │                    │
│            │      └────────┬────────┘      │                    │
│            │               │               │                    │
│            ▼               ▼               ▼                    │
│     ┌─────────────┐ ┌─────────────┐ ┌─────────────┐            │
│     │ Plans/      │ │ Approved/   │ │ Briefings/  │            │
│     │ PLAN_*.md   │ │ Rejected/   │ │ Daily_*.md  │            │
│     └─────────────┘ └─────────────┘ └─────────────┘            │
└───────────────────────────┼─────────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────────┐
│                      ACTION LAYER                               │
│           (MCP Servers / Python Skills)                         │
├─────────────────────────────────────────────────────────────────┤
│         ┌─────────────┐         ┌─────────────┐                │
│         │ Email MCP   │         │ Browser MCP │                │
│         │ Server      │         │ (LinkedIn)  │                │
│         │ (Node/Py)   │         │ (Playwright)│                │
│         └──────┬──────┘         └──────┬──────┘                │
│                │                       │                        │
│         ┌──────▼──────┐         ┌──────▼──────┐                │
│         │ Gmail API   │         │ LinkedIn    │                │
│         │ Send/Draft  │         │ Post        │                │
│         └─────────────┘         └─────────────┘                │
└─────────────────────────────────────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────────┐
│                   SCHEDULING LAYER                              │
│            (Windows Task Scheduler / cron)                      │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐                            │
│  │ Daily        │  │ Weekly       │                            │
│  │ Briefing     │  │ Audit        │                            │
│  │ 8:00 AM      │  │ Sunday 10PM  │                            │
│  └──────────────┘  └──────────────┘                            │
│                                                               │
│  Triggers: windows_scheduled_tasks.ps1                        │
└─────────────────────────────────────────────────────────────────┘
```

### 4.2 Layer Responsibilities

#### Perception Layer (Watchers)
- **Components:** GmailWatcher, WhatsAppWatcher, FileSystemWatcher
- **Responsibilities:** Monitor external sources, detect new items, create action files
- **Interfaces:** All extend `BaseWatcher`, write to `Needs_Action/`
- **Data Flow:** External source → Watcher → `.md` action file

#### Reasoning Layer (Qwen Code CLI + Python Skills)
- **Components:** Qwen Code CLI (OAuth), Python Skills (`create_plan`, `request_approval`, `generate_briefing`)
- **Responsibilities:** Analyze action files, generate plans, create approval requests, produce briefings
- **Interfaces:** Read from `Needs_Action/`, write to `Plans/`, `Pending_Approval/`, `Briefings/`
- **Data Flow:** Action file → Qwen reasoning → Plan/Approval/ Briefing file

#### Action Layer (MCP Servers / Python Skills)
- **Components:** Email MCP Server, Browser MCP (Playwright), Python Skills (`send_email`, `linkedin_post`)
- **Responsibilities:** Execute approved actions, interact with external systems
- **Interfaces:** Read from `Approved/`, write to `Done/`, log to `Logs/`
- **Data Flow:** Approved file → MCP/Skill → External action → Audit log

#### Scheduling Layer
- **Components:** Windows Task Scheduler, Python orchestrator scripts
- **Responsibilities:** Trigger scheduled tasks (daily briefing, weekly audit)
- **Interfaces:** Invoke orchestrator with task type parameter
- **Data Flow:** Scheduler → Orchestrator → Briefing generation → `Briefings/`

---

## 5. Vault Structure (Silver Tier Extended)

### 5.1 Complete Vault Structure

```
FTE/vault/
├── Inbox/                    # [Bronze] Manual file drop location
│   └── *.md                  # User-created action files
├── Needs_Action/             # [Bronze] Watcher output, requires processing
│   ├── EMAIL_*.md           # [Silver] Gmail watcher output
│   ├── WHATSAPP_*.md        # [Silver] WhatsApp watcher output
│   └── FILE_*.md            # [Bronze] FileSystem watcher output
├── Plans/                    # [Silver] NEW - Multi-step task plans
│   └── PLAN_<task>_<timestamp>.md
├── Pending_Approval/         # [Silver] NEW - Awaiting human approval
│   └── APPROVAL_<action>_<timestamp>.md
├── Approved/                 # [Silver] NEW - Ready for execution
│   └── *.md                  # Moved here by human for execution
├── Rejected/                 # [Silver] NEW - Rejected actions
│   └── *.md                  # Moved here by human to cancel
├── Done/                     # [Bronze] Completed items
│   └── *.md                  # Executed actions, completed tasks
├── Briefings/                # [Silver] NEW - Scheduled task output
│   ├── Daily_YYYYMMDD.md    # Daily briefing (8 AM)
│   └── Weekly_YYYYMMDD.md   # Weekly audit (Sunday 10 PM)
├── Logs/                     # [Bronze] Audit logs
│   └── *.json                # Structured JSON logs with correlation_id
├── Templates/                # [Silver] NEW - Reusable templates
│   ├── plan_template.md
│   └── approval_request_template.md
├── Dashboard.md              # [Bronze] System status (single-writer: orchestrator)
└── Company_Handbook.md       # [Bronze] Rules of engagement, thresholds
```

### 5.2 New Folder Specifications

#### Plans/
- **Purpose:** Store structured multi-step task plans generated by Qwen Code CLI
- **File Naming:** `PLAN_<objective-slug>_<YYYYMMDD_HHMMSS>.md`
- **Lifecycle:** Created when action file requires multiple steps → Updated as steps complete → Archived to `Done/` when finished
- **Access Patterns:** Written by `create_plan` skill, read by Qwen Code CLI during execution, read by user for visibility

#### Pending_Approval/
- **Purpose:** Store approval requests for sensitive actions
- **File Naming:** `APPROVAL_<action-type>_<YYYYMMDD_HHMMSS>.md`
- **Lifecycle:** Created by `request_approval` skill → Human reviews → Moved to `Approved/` or `Rejected/` → Expires after 24 hours (flagged in `Dashboard.md`)
- **Access Patterns:** Written by approval skill, read by human for decision, monitored by orchestrator for movement

#### Approved/
- **Purpose:** Hold approved actions ready for execution
- **File Naming:** Same as source file (preserved on move)
- **Lifecycle:** Human moves file here → Orchestrator detects within 5 seconds → Executes action → Moves to `Done/`
- **Access Patterns:** Written by human (move operation), read by orchestrator for execution

#### Rejected/
- **Purpose:** Hold rejected/cancelled actions
- **File Naming:** Same as source file (preserved on move)
- **Lifecycle:** Human moves file here → Orchestrator logs cancellation → File retained for audit
- **Access Patterns:** Written by human (move operation), read by orchestrator for logging

#### Briefings/
- **Purpose:** Store scheduled task outputs (daily briefings, weekly audits)
- **File Naming:** `Daily_YYYYMMDD.md`, `Weekly_YYYYMMDD.md`
- **Lifecycle:** Created by scheduled task → User reads → Retained indefinitely for historical reference
- **Access Patterns:** Written by `generate_briefing` skill, read by user

#### Templates/
- **Purpose:** Store reusable templates for plans and approval requests
- **File Naming:** `<template-name>_template.md`
- **Lifecycle:** Created once → Used repeatedly by skills → Updated as needed
- **Access Patterns:** Read by skills, rarely modified

---

## 6. Component Specifications

### 6.1 S1: Gmail Watcher

**Purpose:** Monitor Gmail for unread/important emails and create action files.

**Implementation:** `FTE/src/watchers/gmail_watcher.py`

**Extends:** `BaseWatcher`

**Interval:** 2 minutes (configurable in `Company_Handbook.md`)

**Authentication:** Google OAuth2

**Technical Requirements:**
- Python 3.13+
- `google-auth` library
- `google-api-python-client` library
- OAuth2 credentials (Client ID, Client Secret, Refresh Token)
- Processed message ID tracking (prevent duplicates)

**Key Methods:**
- `check_for_updates() -> list[dict]`: Query Gmail API for unread/important messages
- `create_action_file(message: dict) -> Path`: Create `.md` file in `Needs_Action/`
- `_extract_headers(payload: dict) -> dict`: Parse email headers
- `_track_processed(message_id: str)`: Record processed ID to prevent duplicates

**Action File Format:**
```markdown
---
type: email
from: sender@example.com
to: me@example.com
subject: Urgent: Project Update
received: 2026-03-19T10:30:00Z
priority: high
status: pending
message_id: <gmail-id>
---

## Email Content

[Email snippet or full content]

## Suggested Actions

- [ ] Reply to sender
- [ ] Forward to relevant party
- [ ] Archive after processing
```

**Error Handling:**
- **API Quota Exceeded:** Implement exponential backoff (1s, 2s, 4s; max 3 retries), log warning, skip check
- **Network Failure:** Retry with backoff, after 5 failures create alert file in `Needs_Action/`
- **Session Expiry:** Detect OAuth2 token expiry, notify user via `Dashboard.md` update, halt gracefully
- **Invalid Credentials:** Log error, create alert file in `Needs_Action/`, halt watcher

**Testing:**
- Unit tests with mocked Gmail API (`unittest.mock`)
- Test duplicate prevention (same message ID not processed twice)
- Test action file creation (correct format, metadata extraction)
- Test error handling (API failures, network issues, session expiry)

**Security:**
- OAuth2 credentials stored in `.env` (never committed)
- Minimal scopes: `gmail.readonly`
- Credentials encrypted at rest (optional: use system keychain)

**Setup Script:** `scripts/setup_gmail_oauth.ps1` (document Google Cloud Console steps)

---

### 6.2 S2: WhatsApp Watcher

**Purpose:** Monitor WhatsApp Web for messages with priority keywords.

**Implementation:** `FTE/src/watchers/whatsapp_watcher.py`

**Extends:** `BaseWatcher`

**Interval:** 30 seconds (configurable in `Company_Handbook.md`)

**Authentication:** Manual WhatsApp Web session (browser-based)

**Keywords:** `urgent`, `asap`, `invoice`, `payment`, `help` (configurable)

**Technical Requirements:**
- Python 3.13+
- Playwright for browser automation
- Chromium browser
- Persistent session storage (`vault/whatsapp_session/`)

**Key Methods:**
- `check_for_updates() -> list[dict]`: Scan WhatsApp Web for new messages
- `create_action_file(message: dict) -> Path`: Create `.md` file in `Needs_Action/`
- `_filter_by_keywords(messages: list) -> list`: Filter messages by keywords
- `_preserve_session()`: Save session state for restart recovery

**Action File Format:**
```markdown
---
type: whatsapp
from: +1234567890
contact_name: John Doe
message: Urgent: Need invoice for payment
received: 2026-03-19T10:35:00Z
priority: high
status: pending
keywords_matched: [urgent, payment]
---

## Message Content

[Full message text]

## Suggested Actions

- [ ] Respond to sender
- [ ] Process payment request
- [ ] Send invoice
```

**Error Handling:**
- **Session Expiry:** Detect WhatsApp Web logout, notify user via `Dashboard.md` ("WhatsApp session expired - please re-authenticate"), halt gracefully
- **Network Failure:** Retry with backoff, after 5 failures create alert file
- **Browser Crash:** Auto-restart Playwright, recover session if possible
- **Rate Limiting:** Respect WhatsApp Web rate limits, implement delays

**Testing:**
- Unit tests with mocked Playwright
- Test keyword filtering (correct messages identified)
- Test session preservation (restart without re-authentication)
- Test error handling (session expiry, network issues)

**Security:**
- Session stored in `vault/whatsapp_session/` (gitignored)
- No credentials in code
- User must manually authenticate first run

---

### 6.3 S3: Process Manager

**Purpose:** Keep all watchers running continuously with auto-recovery.

**Implementation:** `FTE/src/process_manager.py`

**Features:**
- Start/stop all configured watchers
- Health check endpoint (HTTP or file-based)
- Auto-restart on crash (within 10 seconds)
- Memory usage monitoring
- Crash detection and restart limits (prevent infinite loops)

**Technical Requirements:**
- Python 3.13+
- `subprocess` module for watcher management
- `psutil` for process monitoring (optional)

**Key Methods:**
- `start_all_watchers()`: Launch all configured watchers as subprocesses
- `health_check() -> dict`: Return status of all watchers
- `restart_watcher(watcher_name: str)`: Restart a specific watcher
- `monitor_memory() -> dict`: Check memory usage per watcher
- `shutdown()`: Graceful shutdown on SIGINT/SIGTERM

**Error Handling:**
- **Crash Detection:** Monitor watcher PIDs, detect unexpected termination
- **Restart Limits:** Max 3 restarts per hour per watcher (prevent infinite crash loops)
- **Memory Leaks:** Kill watcher if memory exceeds 200MB, log alert, restart
- **Graceful Shutdown:** Handle SIGINT/SIGTERM, stop all watchers cleanly

**Testing:**
- Unit tests with mocked subprocess
- Test crash recovery (simulate crash, verify restart)
- Test restart limits (crash 4 times, verify 4th not restarted)
- Test graceful shutdown (SIGTERM, verify clean exit)

---

### 6.4 S4: Plan.md Generation

**Purpose:** Create structured plans for multi-step tasks automatically.

**Implementation:** `FTE/src/skills/create_plan.py`

**Trigger:** New file in `Needs_Action/` requiring multiple steps

**Template:** YAML frontmatter + step checkboxes

**Status Tracking:** `pending` → `in_progress` → `awaiting_approval` → `completed`

**Plan File Format:**
```markdown
---
created: 2026-03-19T10:40:00Z
status: pending
objective: Process urgent payment request
source_file: Needs_Action/WHATSAPP_12345.md
estimated_steps: 5
requires_approval: true
---

## Objective

Process urgent payment request from John Doe

## Steps

- [ ] **Step 1:** Verify invoice details (pending)
- [ ] **Step 2:** Check payment amount against threshold (pending)
- [ ] **Step 3:** Create approval request if >$100 (pending)
- [ ] **Step 4:** Wait for human approval (awaiting_approval)
- [ ] **Step 5:** Execute payment via MCP (pending)
- [ ] **Step 6:** Move to Done/ and log (pending)

## Notes

[Additional context, decisions, or observations]
```

**Key Methods:**
- `generate_plan(action_file: Path) -> Path`: Create plan from action file
- `update_plan_status(plan_file: Path, new_status: str)`: Update YAML frontmatter
- `mark_step_complete(plan_file: Path, step_number: int)`: Check off completed step
- `get_plan_status(plan_file: Path) -> str`: Return current status

**Error Handling:**
- **Invalid Action File:** Log error, create alert file, skip plan generation
- **Template Missing:** Use default template, log warning
- **Concurrent Updates:** Implement file locking (prevent race conditions)

**Testing:**
- Unit tests with mocked file system
- Test plan generation (correct YAML, steps extracted)
- Test status updates (YAML frontmatter modified correctly)
- Test step completion (checkbox marked)

---

### 6.5 S5: Email MCP Server

**Purpose:** Enable Qwen Code CLI to send emails via Gmail API.

**Implementation Options:**
- **Option A (Recommended for Silver):** Python Skill (`FTE/src/skills/send_email.py`) - simpler, no MCP dependency
- **Option B:** Node.js MCP Server (`FTE/src/mcp_servers/email_mcp/index.js`) - more flexible, follows MCP spec

**Methods:**
- `send_email(to: str, subject: str, body: str, attachments: list[str] | None = None) -> dict`
- `draft_email(to: str, subject: str, body: str) -> dict`
- `search_emails(query: str, limit: int = 10) -> list[dict]`

**Configuration:**
```json
// ~/.config/claude-code/mcp.json (if using MCP)
{
  "mcpServers": {
    "email": {
      "command": "node",
      "args": ["H:/Programming/FTE-Agent/FTE/src/mcp_servers/email_mcp/index.js"],
      "env": {
        "GMAIL_CLIENT_ID": "...",
        "GMAIL_CLIENT_SECRET": "...",
        "GMAIL_REFRESH_TOKEN": "..."
      }
    }
  }
}
```

**Security:**
- OAuth2 credentials in `.env` (never committed)
- `--dry-run` mode supported (log without sending)
- Approval required for:
  - Sends to new contacts (not in address book)
  - Bulk sends (>5 recipients)
  - Sends with attachments >1MB

**Error Handling:**
- **API Quota:** Implement rate limiting, retry with backoff
- **Invalid Recipient:** Validate email format, log error, notify user
- **Attachment Too Large:** Skip attachment, log warning, continue
- **Authentication Failure:** Detect OAuth2 expiry, notify user, halt

**Testing:**
- Unit tests with mocked Gmail API
- Test dry-run mode (no actual send)
- Test approval workflow (new contact triggers approval)
- Test error handling (API failures, invalid emails)

**Environment Variables:**
```bash
GMAIL_CLIENT_ID=your-client-id
GMAIL_CLIENT_SECRET=your-client-secret
GMAIL_REFRESH_TOKEN=your-refresh-token
```

---

### 6.6 S6: HITL Approval Workflow

**Purpose:** Require human approval for sensitive actions before execution.

**Implementation:** `FTE/src/approval_handler.py`

**Sensitive Actions (Require Approval):**
- Payments (any amount to new recipients, >$100 to existing)
- Email sends (new contacts, bulk >5, attachments >1MB)
- Social media posts (replies, DMs, first-time posts)
- External API calls (new endpoints, write operations)

**File Lifecycle:**
```
Pending_Approval/ (created by skill)
    ↓ (human reviews)
Approved/ (human moves here) → Orchestrator executes → Done/
    ↓ (human rejects)
Rejected/ (human moves here) → Orchestrator logs cancellation
    ↓ (24 hours pass)
EXPIRED (flagged in Dashboard.md, requires re-approval)
```

**Approval File Format:**
```markdown
---
type: approval_request
action: send_email
action_details:
  to: new-contact@example.com
  subject: Project Update
  body: |
    Hi Team,
    ...
created: 2026-03-19T10:45:00Z
expires: 2026-03-20T10:45:00Z
status: pending
risk_level: medium
reason: New contact (not in address book)
---

## Approval Request

**Action:** Send Email  
**To:** new-contact@example.com  
**Subject:** Project Update  
**Risk Level:** Medium  
**Reason:** New contact (not in address book)

## Instructions

1. **To Approve:** Move this file to `Approved/` folder
2. **To Reject:** Move this file to `Rejected/` folder
3. **Expiry:** This request expires in 24 hours (2026-03-20T10:45:00Z)

## Details

[Full action details for review]
```

**Key Methods:**
- `create_approval_request(action: dict, reason: str) -> Path`: Create approval file
- `check_expiry() -> list[Path]`: Find expired approvals
- `flag_expired(expired_files: list[Path])`: Update `Dashboard.md` with expired alerts
- `monitor_approved_folder() -> list[Path]`: Detect files moved to `Approved/`

**Expiry Handling:**
- Expiry timestamp: 24 hours from creation (configurable in `Company_Handbook.md`)
- Expired approvals flagged in `Dashboard.md` with alert
- Expired approvals require re-approval (cannot be executed)

**Error Handling:**
- **File Move Detection Failure:** Retry every 5 seconds, log error after 3 failures
- **Expired Approval Execution Attempt:** Block execution, log error, notify user
- **Concurrent Moves:** Implement file locking (prevent race conditions)

**Testing:**
- Unit tests with mocked file system
- Test approval file creation (correct format, expiry set)
- Test expiry detection (expired files identified)
- Test file move detection (Approved/ movement triggers execution)
- Test rejection handling (Rejected/ movement logs cancellation)

---

### 6.7 S7: LinkedIn Posting

**Purpose:** Generate and post business content to LinkedIn automatically.

**Implementation:** `FTE/src/skills/linkedin_posting.py`

**Content Generation Sources:**
- `Business_Goals.md` (company objectives, target audience)
- `Done/` folder (recent achievements, completed tasks)
- Industry trends (optional web search via Qwen)

**Approval:** Required before posting (via HITL workflow)

**Execution:** Playwright browser automation (fallback if LinkedIn API unavailable)

**Rate Limiting:** Max 1 post/day (configurable in `Company_Handbook.md`)

**Technical Requirements:**
- Python 3.13+
- Playwright for browser automation
- Content generation logic (Qwen Code CLI skill)

**Key Methods:**
- `generate_content() -> str`: Create LinkedIn post from goals + achievements
- `create_approval_request(content: str) -> Path`: Create approval file
- `post_to_linkedin(content: str) -> dict`: Execute post via Playwright
- `check_rate_limit() -> bool`: Verify <1 post today

**Post File Format (in Pending_Approval/):**
```markdown
---
type: approval_request
action: linkedin_post
content: |
  🚀 Exciting news! We've completed...
created: 2026-03-19T11:00:00Z
expires: 2026-03-20T11:00:00Z
status: pending
scheduled_time: 2026-03-19T12:00:00Z
---

## LinkedIn Post Approval

**Content:**
[Post text preview]

**Scheduled Time:** 2026-03-19T12:00:00Z  
**Rate Limit Check:** ✅ (0 posts today)

## Instructions

1. **To Approve:** Move to `Approved/`
2. **To Reject:** Move to `Rejected/`
3. **Expiry:** 24 hours

## Full Content

[Complete post text for review]
```

**Error Handling:**
- **Session Expiry:** Detect LinkedIn logout, notify user, halt
- **Rate Limit Exceeded:** Skip post, log warning, notify user
- **Browser Crash:** Retry Playwright launch, max 3 attempts
- **Post Failure:** Log error with full response, notify user, move to `Rejected/`

**Testing:**
- Unit tests with mocked Playwright
- Test content generation (goals + achievements combined)
- Test rate limiting (2nd post blocked)
- Test approval workflow (approval required)
- Test error handling (session expiry, browser crash)

---

### 6.8 S8: Basic Scheduling

**Purpose:** Run automated tasks on a schedule (daily briefing, weekly audit).

**Implementation:**
- `FTE/src/scheduler/daily_briefing.py`
- `FTE/src/scheduler/weekly_audit.py`
- `FTE/src/scripts/windows_scheduled_tasks.ps1` (setup script)

**Trigger:** Windows Task Scheduler (or cron on Linux/Mac)

**Tasks:**

#### Daily Briefing (8:00 AM)
- **Purpose:** Summarize business tasks, priorities, and status
- **Input:** `Needs_Action/`, `Plans/`, `Done/` folders
- **Output:** `Briefings/Daily_YYYYMMDD.md`
- **Content:**
  - Pending items count
  - In-progress plans summary
  - Completed items (yesterday)
  - Today's priorities

#### Weekly Audit (Sunday 10:00 PM)
- **Purpose:** Business review, metrics, bottlenecks
- **Input:** All vault folders, `Logs/`, `Dashboard.md`
- **Output:** `Briefings/Weekly_YYYYMMDD.md`
- **Content:**
  - Week summary (tasks completed, pending, rejected)
  - Watcher uptime metrics
  - Approval workflow stats
  - Bottlenecks identified
  - Recommendations for next week

**Windows Task Scheduler Setup:**
```powershell
# scripts/windows_scheduled_tasks.ps1

# Daily Briefing (8:00 AM)
$action = New-ScheduledTaskAction -Execute "python" `
  -Argument "H:\Programming\FTE-Agent\FTE\src\orchestrator.py --task daily_briefing"
$trigger = New-ScheduledTaskTrigger -Daily -At 8am
Register-ScheduledTask -TaskName "FTE_Daily_Briefing" -Action $action -Trigger $trigger

# Weekly Audit (Sunday 10:00 PM)
$trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Sunday -At 10pm
Register-ScheduledTask -TaskName "FTE_Weekly_Audit" -Action $action -Trigger $trigger
```

**Error Handling:**
- **Task Failure:** Log error, create alert file in `Needs_Action/`, notify user
- **Missed Schedule:** Detect missed runs, execute on next start (with warning)
- **Concurrent Execution:** Prevent overlapping runs (file locking)

**Testing:**
- Unit tests with mocked scheduler
- Test briefing generation (correct content, format)
- Test audit generation (metrics calculated correctly)
- Test error handling (task failure, missed schedule)

---

### 6.9 S9: Agent Skills Documentation

**Purpose:** Document all AI capabilities as reusable Agent Skills.

**Implementation:** `FTE/src/skills/skills_index.md` (master index) + individual skill docs

**Documented Skills:**

| Skill | Purpose | Input | Output | Location |
|-------|---------|-------|--------|----------|
| `triage_email` | Process incoming emails | Action file | Prioritized list, suggested actions | `skills/triage_email.py` |
| `create_plan` | Generate Plan.md from action files | Action file path | Plan file path | `skills/create_plan.py` |
| `request_approval` | Create approval request files | Action details | Approval file path | `skills/request_approval.py` |
| `execute_approved_action` | Run approved MCP actions | Approved file path | Execution result | `skills/execute_approved_action.py` |
| `generate_briefing` | Create daily/weekly briefings | Task type, date | Briefing file path | `skills/generate_briefing.py` |
| `send_email` | Send emails via Gmail API | to, subject, body, attachments | Send result | `skills/send_email.py` |
| `linkedin_post` | Generate and post LinkedIn content | Goals, achievements | Post result | `skills/linkedin_posting.py` |

**Documentation Format (per skill):**
```markdown
# Skill: <skill-name>

**Purpose:** [One-line description]

**Location:** `src/skills/<skill>.py`

**Inputs:**
- `param1` (type): Description
- `param2` (type): Description

**Outputs:**
- `return` (type): Description

**Error Handling:**
- Error type 1: Behavior
- Error type 2: Behavior

**Example Usage:**
```python
from skills import skill_name
result = skill_name(param1=value1, param2=value2)
```

**Tests:** `tests/unit/test_<skill>.py`
```

**Testing:**
- Verify all 7+ skills documented
- Verify examples are accurate and executable
- Verify error handling documented

---

## 7. Security Requirements

### 7.1 Credential Management

**Requirements:**
- ✅ All credentials stored in `.env` (never committed to Git)
- ✅ `.env` added to `.gitignore`
- ✅ `.env.example` provided with placeholder values
- ✅ Credentials encrypted at rest where possible (optional: use system keychain)
- ✅ Minimal OAuth2 scopes used (`gmail.readonly`, not `gmail.modify`)
- ✅ Credentials rotated monthly (documented process)

**Environment Variables:**
```bash
# .env.example (commit this)
GMAIL_CLIENT_ID=your-client-id-here
GMAIL_CLIENT_SECRET=your-client-secret-here
GMAIL_REFRESH_TOKEN=your-refresh-token-here
DEV_MODE=true
```

### 7.2 Approval Workflow Security

**Requirements:**
- ✅ Sensitive actions always require approval (configurable thresholds in `Company_Handbook.md`)
- ✅ Approval files have expiry (24 hours from creation)
- ✅ Rejected actions logged with reason
- ✅ Approval audit trail maintained (all moves logged to `Logs/`)
- ✅ Expired approvals flagged in `Dashboard.md`
- ✅ Execution blocked for expired approvals

### 7.3 File System Security

**Requirements:**
- ✅ Path traversal prevention (validate all paths start with `vault_path`)
- ✅ `DEV_MODE` validation (check before all external actions)
- ✅ File access logged to audit log (JSON format with correlation_id)
- ✅ File size limits enforced (skip files >10MB, log warning)

### 7.4 STOP File Mechanism

**Requirements:**
- ✅ Creating `vault/STOP` immediately halts all orchestrator operations (within 5 seconds)
- ✅ STOP file checked every loop iteration (watchers, orchestrator, skills)
- ✅ STOP file removed to resume operations
- ✅ STOP file creation logged to audit log

### 7.5 Session Expiry Handling

**Requirements:**
- ✅ WhatsApp Web session expiry detected automatically
- ✅ LinkedIn session expiry detected automatically
- ✅ OAuth2 token expiry detected and handled (refresh or notify user)
- ✅ User notified via `Dashboard.md` update when session expires
- ✅ Watcher halts gracefully on session expiry (no retry loops)

---

## 8. API Credentials & Setup

### 8.1 Gmail API

**Required Credentials:**
- Client ID
- Client Secret
- Refresh Token

**OAuth2 Setup Steps:**
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create new project or select existing
3. Enable Gmail API
4. Create OAuth2 credentials (Desktop app)
5. Download `credentials.json`
6. Run `scripts/setup_gmail_oauth.ps1` to obtain refresh token
7. Copy credentials to `.env`

**Scopes:**
- `gmail.readonly` (for Gmail Watcher)
- `gmail.send` (for Email MCP/Skill)

**Environment Variables:**
```bash
GMAIL_CLIENT_ID=your-client-id
GMAIL_CLIENT_SECRET=your-client-secret
GMAIL_REFRESH_TOKEN=your-refresh-token
```

**Setup Script:** `scripts/setup_gmail_oauth.ps1` (document full OAuth2 flow)

### 8.2 WhatsApp Web

**Required:** Manual authentication via browser (no API credentials)

**Session Storage:** `vault/whatsapp_session/` (gitignored)

**Setup Steps:**
1. Run WhatsApp Watcher for first time
2. Scan QR code with WhatsApp mobile app
3. Session saved to `vault/whatsapp_session/`
4. Subsequent runs use saved session

**No API credentials needed.**

### 8.3 LinkedIn (Browser Automation)

**Required:** LinkedIn account credentials

**Session Storage:** `vault/linkedin_session/` (gitignored)

**Setup Steps:**
1. Run LinkedIn posting skill for first time
2. Manually authenticate via browser
3. Session saved to `vault/linkedin_session/`
4. Subsequent runs use saved session

**Manual first-time authentication required.**

---

## 9. Testing Strategy

### 9.1 Unit Tests (80%+ Coverage Required)

**Test Files:**
- `tests/unit/test_gmail_watcher.py`
- `tests/unit/test_whatsapp_watcher.py`
- `tests/unit/test_process_manager.py`
- `tests/unit/test_create_plan.py`
- `tests/unit/test_approval_handler.py`
- `tests/unit/test_linkedin_posting.py`
- `tests/unit/test_scheduler.py`
- `tests/unit/test_send_email.py`

**Coverage Requirement:** 80%+ (measured via `pytest --cov=src`)

**Mocking Strategy:**
- Mock all external APIs (Gmail, WhatsApp, LinkedIn)
- Mock file system operations (use `tmp_path` fixture)
- Mock Qwen Code CLI subprocess calls
- Mock Playwright browser

### 9.2 Integration Tests

**Test Scenarios:**
- **watcher→plan→approval→execution flow:**
  1. Gmail Watcher creates action file
  2. Qwen generates Plan.md
  3. Approval request created
  4. Human moves to Approved/
  5. Orchestrator executes action
  6. Action logged, file moved to Done/
- **scheduled task→briefing generation:**
  1. Windows Task Scheduler triggers orchestrator
  2. Daily briefing generated
  3. Briefing saved to `Briefings/`
  4. Dashboard.md updated
- **MCP server→external action:**
  1. Email MCP receives send request
  2. Gmail API called
  3. Email sent (or dry-run logged)
  4. Audit log updated

### 9.3 Chaos Tests

**Test Scenarios:**
- **Watcher crash recovery:**
  1. Start Gmail Watcher
  2. Kill process mid-operation
  3. Verify Process Manager restarts within 10 seconds
  4. Verify no messages lost
- **API failure with retry:**
  1. Mock Gmail API to fail (503 error)
  2. Verify exponential backoff (1s, 2s, 4s)
  3. Verify max 3 retries
  4. Verify alert created after 5 failures
- **Network interruption:**
  1. Simulate network disconnection
  2. Verify watchers handle gracefully (no crash)
  3. Verify reconnection recovery
- **Session expiry handling:**
  1. Mock WhatsApp Web session expiry
  2. Verify detection
  3. Verify user notification
  4. Verify graceful halt
- **Disk full scenario:**
  1. Mock disk full error (95% capacity)
  2. Verify graceful degradation (skip writes, log alerts)
  3. Verify no data corruption

---

## 10. Quality Gates

**All quality gates MUST pass before merging to main branch:**

| Gate | Command | Requirement |
|------|---------|-------------|
| Linting | `ruff check src/ tests/` | 0 errors |
| Formatting | `black --check src/ tests/` | 0 errors (line length: 100) |
| Type Checking | `mypy --strict src/` | 0 errors (all functions typed, no `Any`) |
| Security Scan | `bandit -r src/` | 0 high-severity issues |
| Test Coverage | `pytest --cov=src --cov-report=term-missing` | 80%+ coverage |
| Import Order | `isort --check-only src/ tests/` | 0 errors |

**Configuration Files:**
- `.ruff.toml` (linting rules)
- `pyproject.toml` (black, mypy, pytest config)
- `.isort.cfg` (import order)

**CI/CD Integration:** Quality gates run automatically on every PR (GitHub Actions or similar)

---

## 11. Safety Validation Checklist

### 11.1 Bronze Tier (REQUIRED - Must Be Maintained)

- [ ] File dropped in `Inbox/` creates action file
- [ ] Qwen Code CLI reads action file and creates `Plan.md`
- [ ] `DEV_MODE=false` prevents external API calls
- [ ] STOP file (`vault/STOP`) halts orchestrator within 5 seconds
- [ ] All actions logged with `correlation_id`
- [ ] Path traversal attempts blocked (validation in all file operations)
- [ ] `pytest --cov=src` shows 80%+ coverage
- [ ] Quality gates pass (ruff, black, mypy, bandit, isort)
- [ ] Qwen Code CLI authenticated (OAuth, 1,000 free calls/day)

### 11.2 Silver Tier (REQUIRED for Silver Completion)

- [ ] Gmail watcher detects new emails (2-min interval)
- [ ] WhatsApp watcher detects keyword messages (30-sec interval)
- [ ] Process manager keeps watchers alive (auto-restart within 10sec)
- [ ] Plan.md files created with YAML frontmatter
- [ ] Approval requests created for sensitive actions
- [ ] Moving to `Approved/` triggers execution (within 5sec)
- [ ] Moving to `Rejected/` logs cancellation
- [ ] Expired approvals flagged in `Dashboard.md`
- [ ] Daily briefing runs at 8:00 AM
- [ ] Email MCP/Skill sends test email (dry-run mode verified)
- [ ] LinkedIn posting with approval workflow functional
- [ ] Watcher failures logged and recovered (crash recovery tested)
- [ ] API rate limit handling tested (backoff implemented)
- [ ] Session expiry detected and notified (WhatsApp, LinkedIn)
- [ ] Scheduled tasks registered and executable (Windows Task Scheduler)
- [ ] Integration test: end-to-end flow (watcher→plan→approval→execution)
- [ ] Chaos tests pass (crash, API failure, disk full, network interruption)

---

## 12. Out of Scope (Gold/Platinum Tier)

The following are explicitly **NOT** in Silver tier:

### Gold Tier (Future)
- ❌ Odoo accounting integration (JSON-RPC, invoice management)
- ❌ Facebook/Instagram integration (posting, analytics)
- ❌ Twitter/X integration (posting, monitoring)
- ❌ CEO Briefing with revenue tracking (bank integration, financial metrics)
- ❌ Ralph Wiggum autonomous loop (multi-step autonomous execution)

### Platinum Tier (Future)
- ❌ Cloud deployment (always-on VM, containerization)
- ❌ Multi-agent synchronization (A2A communication, distributed vault)
- ❌ Work-Zone Specialization (Cloud vs Local agent separation)

---

## 13. Risks & Mitigations

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| **Gmail API quota limits** | Medium | Low | Implement rate limiting (max 100 calls/hour), cache responses, use batch API where possible |
| **WhatsApp session expiry** | Medium | Medium | Auto-detection of session expiry, user notification via `Dashboard.md`, easy re-authentication flow |
| **LinkedIn API access denied** | High | Medium | Fallback to browser automation (Playwright), document manual setup steps |
| **MCP server complexity** | Medium | Medium | Start simple (Python Skills pattern), iterate based on learnings, use reference implementations |
| **Windows Task Scheduler permissions** | Low | Low | Document manual setup steps, provide PowerShell script with admin elevation, test on clean Windows install |
| **OAuth2 credential leakage** | High | Low | Strict `.gitignore` validation, pre-commit hooks to scan for secrets, use system keychain where possible |
| **Watcher silent failures** | High | Medium | Process Manager health checks, alert file creation on watcher crash, `Dashboard.md` status updates |
| **Approval workflow bypass** | High | Low | Orchestrator validates approval file age (>60sec in `Pending_Approval/`), log all executions, audit trail |

---

## 14. Success Metrics

### 14.1 Functional Metrics

| Metric | Target | Measurement Method |
|--------|--------|-------------------|
| Watcher uptime | >99% | Process Manager logs (uptime / total time) |
| Action file creation latency | <5 seconds | Audit log timestamps (detection → file creation) |
| Approval workflow completion | <24 hours | Approval file lifecycle (creation → approval/expiration) |
| Scheduled task reliability | 100% | Task execution logs (scheduled vs actual run) |
| Test coverage | >80% | `pytest --cov=src` report |
| Approval detection time | <5 seconds | File move detection latency (move → orchestrator action) |
| Watcher restart time | <10 seconds | Crash → restart latency (Process Manager logs) |

### 14.2 Quality Metrics

| Metric | Target | Measurement Method |
|--------|--------|-------------------|
| Critical security vulnerabilities | 0 | `bandit -r src/` scan |
| Type errors | 0 | `mypy --strict src/` check |
| Linting errors | 0 | `ruff check src/` check |
| Formatting errors | 0 | `black --check src/` check |
| Import order errors | 0 | `isort --check-only src/` check |
| Test failures | 0 | `pytest` run |

### 14.3 Performance Metrics

| Metric | Target | Measurement Method |
|--------|--------|-------------------|
| Gmail watcher interval | 2 minutes | Actual check interval (logs) |
| WhatsApp watcher interval | 30 seconds | Actual check interval (logs) |
| FileSystem watcher interval | 60 seconds | Actual check interval (logs) |
| Memory usage per watcher | <200MB | Process Manager monitoring |
| MCP server call timeout | <5 seconds | Execution logs (start → completion) |
| Log file size | <100MB per file | Log rotation (7 days or 100MB) |

### 14.4 Documentation Metrics

| Metric | Target | Measurement Method |
|--------|--------|-------------------|
| Skills documented | 100% (7/7) | `skills/skills_index.md` review |
| Setup guide complete | Yes | `README.md` review |
| API credentials documented | Yes | Section 8 review |
| Error handling documented | Yes | Each component spec review |

---

## 15. References

### 15.1 Project Documents
- [Personal AI Employee Hackathon Spec](../../Personal_AI_Employee_Hackathon.md) - Silver Tier requirements source
- [Constitution v4.0.0](../../.specify/memory/constitution.md) - Project principles, Silver Tier architecture
- [Bronze Tier Spec](../001-file-system-watcher/spec.md) - Foundation components

### 15.2 External Documentation
- [Gmail API Documentation](https://developers.google.com/gmail/api)
- [Google OAuth2 Setup](https://developers.google.com/identity/protocols/oauth2)
- [Playwright Documentation](https://playwright.dev/python/)
- [MCP Specification](https://modelcontextprotocol.io/)
- [Qwen Code CLI Documentation](https://docs.anthropic.com/claude-code/)
- [Windows Task Scheduler](https://docs.microsoft.com/en-us/windows/win32/taskschd/task-scheduler-start-page)
- [pytest Documentation](https://docs.pytest.org/)
- [ruff Documentation](https://docs.astral.sh/ruff/)
- [mypy Documentation](https://mypy.readthedocs.io/)
- [bandit Documentation](https://bandit.readthedocs.io/)

---

## 16. Approval

**Spec Author:** FTE-Agent Team  
**Review Date:** TBD  
**Approval Status:** Draft  
**Version:** 2.0.0 (Enhanced with comprehensive requirements)

---

## Appendix A: File Naming Conventions

| File Type | Pattern | Example |
|-----------|---------|---------|
| Email Action | `EMAIL_<gmail-id>.md` | `EMAIL_18a3b2c1d4e5f6g7.md` |
| WhatsApp Action | `WHATSAPP_<phone-number>_<timestamp>.md` | `WHATSAPP_1234567890_20260319103000.md` |
| File Drop Action | `FILE_<filename>_<timestamp>.md` | `FILE_invoice.pdf_20260319103000.md` |
| Plan | `PLAN_<objective-slug>_<timestamp>.md` | `PLAN_process-payment_20260319104000.md` |
| Approval Request | `APPROVAL_<action-type>_<timestamp>.md` | `APPROVAL_send-email_20260319104500.md` |
| Daily Briefing | `Daily_YYYYMMDD.md` | `Daily_20260319.md` |
| Weekly Audit | `Weekly_YYYYMMDD.md` | `Weekly_20260319.md` |

---

## Appendix B: Status Enums

| Context | Valid Values |
|---------|--------------|
| Plan Status | `pending`, `in_progress`, `awaiting_approval`, `completed`, `cancelled` |
| Approval Status | `pending`, `approved`, `rejected`, `expired` |
| Action File Status | `pending`, `processing`, `completed`, `failed` |
| Watcher Status | `running`, `stopped`, `crashed`, `restarting` |

---

*This specification follows Spec-Driven Development methodology. All implementation must reference this document. Changes require spec update and re-approval.*
