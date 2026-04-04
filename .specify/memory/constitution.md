<!--
SYNC IMPACT REPORT
==================
Version change: 4.0.0 → 5.0.0 (Major: Gold Tier support - Odoo, social media, Ralph Wiggum, multi-MCP)
Modified principles:
  - I. Security-First Automation (added Gold Tier Extension: revenue tracking, encryption, max iterations)
  - VIII. Production-Grade Error Handling (added Gold Tier Extension: Odoo RPC, social media rate limits, MCP isolation)
  - IX. Testing Pyramid & Coverage (updated to risk-based 50-60% overall target)
  - XII. Performance Budgets (added Gold Tier Extension: Odoo <5s, Briefing <60s, Ralph <30s)
  - XIII. AI Reasoning Engine & Python Skills Pattern (expanded with Gold tier, Ralph Wiggum pattern)
Added sections:
  - Gold Tier Architecture (Perception→Reasoning→Action→CEO Briefing, Ralph Wiggum, Multi-MCP)
  - Gold Tier Dependencies (Odoo v19+, Facebook Graph v18+, Twitter API v2, MCP coordination)
  - Gold Tier Directory Structure (ralph_wiggum/, mcp_coordinator/, ceo_briefing/, cross_domain/)
  - Gold Tier Safety Validation Checklist (all G1-G12 items with acceptance criteria)
Removed sections: None
Templates requiring updates:
  - ⚠️ .specify/templates/plan-template.md (Add Gold tier Constitution Check for Ralph Wiggum, CEO Briefing)
  - ⚠️ .specify/templates/spec-template.md (Add Gold tier dependencies, Odoo/Social Media setup)
  - ⚠️ .specify/templates/tasks-template.md (Add Gold tier task categories: Odoo, social, Ralph Wiggum)
  - ⚠️ .specify/templates/commands/*.md (May need Gold tier workflow examples)
Follow-up TODOs:
  - TODO(ODOO_SETUP): Install Odoo Community v19+ locally or Docker (2 hours)
  - TODO(FACEBOOK_DEV): Create Facebook Developer Account (1 hour)
  - TODO(TWITTER_DEV): Create Twitter Developer Account (1 hour)
  - TODO(RALPH_VALIDATE): Test Ralph Wiggum autonomous task completion
  - TODO(MCP_COORDINATE): Test 5+ MCPs running concurrently
-->

# FTE-Agent Constitution

## Core Principles

### I. Security-First Automation (CRITICAL)

DEV_MODE=true MUST be set before ANY code runs—this is the kill switch for all external actions. The --dry-run flag MUST be implemented and functional in ALL action scripts including watchers, orchestrator, and skills. Audit logging MUST capture EVERY action attempt (success, failure, dry-run) to /vault/Logs/ in JSON format. Human-in-the-Loop (HITL) approval is REQUIRED for ALL sensitive actions including payments, external API calls, and file moves outside the vault. The STOP file mechanism MUST be implemented: creating vault/STOP immediately halts all orchestrator operations.

**Rationale**: Autonomous systems handling business affairs require non-bypassable safety mechanisms. These five security controls (DEV_MODE, --dry-run, audit logging, HITL, STOP file) form the minimum viable safety foundation.

**Silver Tier Extension**: Approval request files MUST include expiry timestamp (24 hours from creation). Expired approvals MUST be flagged in Dashboard.md and require re-approval before execution. Sensitive action thresholds (e.g., payment amount, email recipient count) MUST be configurable in Company_Handbook.md. All watcher processes MUST be monitored and auto-restarted on crash to prevent silent failures.

**Gold Tier Extension**: CEO Briefing MUST include revenue tracking with data sourced from Odoo (self-hosted, local) or bank APIs. All financial data MUST be encrypted at rest. Ralph Wiggum loop MUST implement max iterations (default: 10) with state persistence. Multi-MCP coordination MUST prevent double-execution via distributed locking. Cross-domain data (personal vs business) MUST be tagged and separable in all reports.

### II. Local-First Privacy Architecture

All data MUST be stored locally in an Obsidian vault using Markdown files. Secrets MUST NEVER be stored in the vault—use .env file (gitignored) or system credential managers (macOS Keychain, Windows Credential Manager, 1Password CLI). The .env file MUST be excluded from version control with .gitignore validation. Vault sync (for Cloud deployment) MUST exclude: .env, tokens, sessions, and banking credentials. Python 3.13+ is REQUIRED for type safety and modern async features.

**Rationale**: Privacy and data ownership are fundamental. Local-first architecture ensures user control while enabling cloud deployment with proper secret isolation.

### III. Spec-Driven Development (MANDATORY PROCESS)

Every feature MUST follow: Spec → Plan → Tasks → Implementation → Tests. No code MAY be written without prior spec approval. All AI functionality MUST be implemented as Python Skills (loadable by Qwen Code CLI via subprocess or direct import). The Ralph Wiggum loop pattern MUST be used for autonomous multi-step task completion (use scripts/ralph-loop.bat with Qwen Code CLI). The single-writer rule applies: ONLY the orchestrator MAY write to Dashboard.md.

**Rationale**: Spec-driven development prevents scope creep and ensures alignment. Python Skills enable consistent, testable AI capabilities without MCP dependency. Single-writer rule prevents race conditions and state corruption.

### IV. Testable Acceptance Criteria

Every principle MUST be verifiable via test or inspection. Security features MUST be tested before functionality (dry-run validation, STOP file test). Integration tests are REQUIRED for: watcher→action file creation, orchestrator→Qwen invocation, approval→execution flow. The test sequence MUST be: dry-run → DEV_MODE=true → (optionally) real mode.

**Rationale**: Untestable principles are unenforceable. Security-first testing ensures safety mechanisms work before functional testing begins.

### V. Observability & Debuggability

Structured JSON logging with log rotation (keep last 7 days) is MANDATORY. All watchers MUST extend BaseWatcher for consistent logging and error handling. Dashboard.md MUST show: system status, pending count, and recent activity (last 10 actions). Error paths MUST be logged with full stack traces to /vault/Logs/. File size limits MUST be enforced: skip files >10MB and log a warning instead of processing.

**Rationale**: Observability enables rapid debugging and audit trail review. Consistent logging patterns across all watchers simplify maintenance and incident response.

### VI. Incremental Complexity (YAGNI)

Start with Bronze tier: one watcher, basic orchestrator, HITL approval. Silver/Gold features MAY only be implemented after Bronze is fully tested and documented. No refactoring of unrelated code is permitted during feature implementation. The smallest viable diff is REQUIRED for every change. Code references are REQUIRED for all modified/inspected files.

**Rationale**: You Ain't Gonna Need It (YAGNI) prevents over-engineering. Bronze-first approach ensures working foundation before complexity.

### VII. Path Validation & Sandboxing

All file operations MUST validate the path starts with vault_path (prevent directory traversal). Each skill MUST validate DEV_MODE before execution. Idempotency is REQUIRED: track executed approval files by hash and skip duplicates. Approval validation MUST ensure execution only occurs if the file was in Pending_Approval/ for >60 seconds (human review time).

**Rationale**: Path validation prevents unauthorized file access. Idempotency and review time prevent accidental or malicious double-execution.

### VIII. Production-Grade Error Handling

Typed exceptions with specific error types MUST be used—bare `except Exception:` or `except:` without specific error types are PROHIBITED. External API calls MUST implement: timeout (30 seconds default), retry with exponential backoff (1s, 2s, 4s; maximum 3 retries), and circuit breaker (fail fast after 5 consecutive failures). File operations MUST explicitly handle: PermissionError (log and skip, continue processing), FileNotFoundError (log warning, add to retry queue), and DiskFullError (immediate halt with alert). Every exception MUST be logged with full stack trace AND either recovered gracefully with fallback behavior OR escalated to user via approval file.

**Rationale**: Production systems must handle failures predictably. Specific exception types enable targeted recovery strategies. Retry with backoff handles transient failures. Circuit breakers prevent cascade failures.

**Silver Tier Extension**: External API calls (Gmail API, WhatsApp Web, LinkedIn) MUST implement: (1) timeout of 30 seconds, (2) retry with exponential backoff (1s, 2s, 4s; maximum 3 retries), (3) circuit breaker pattern (fail fast after 5 consecutive failures), (4) rate limit detection and compliance (e.g., Gmail API quota). Session-based integrations (WhatsApp Web, LinkedIn) MUST detect session expiry and notify user for re-authentication. All API errors MUST be logged with full HTTP response details (status code, headers, body truncated to 1KB).

**Gold Tier Extension**: Odoo JSON-RPC calls MUST implement timeout (30 seconds), retry with exponential backoff (1s, 2s, 4s; max 3 retries), and circuit breaker (trip after 5 failures, reset after 300 seconds). Social media API calls (Facebook Graph, Twitter API v2) MUST implement platform-specific rate limit handling (Facebook: 200 calls/hour, Twitter: 300 calls/15min). Fallback mechanisms REQUIRED: when Odoo unavailable, queue invoices in memory; when social media API fails, save draft posts to `/Drafts/`. All MCP server failures MUST be isolated (one MCP failure doesn't affect others).

### IX. Testing Pyramid & Coverage (Risk-Based)

**Gold Tier Approach**: Focus testing on complex business logic and critical file flows. Simple utilities, getters/setters, and static templates DO NOT require tests.

**Coverage Targets**:
- Critical Business Logic (Ralph Wiggum, CEO Briefing, revenue calculations): 90%+
- File System Flows (watcher→plan→approval→execution): 80%+
- External API Integration (Odoo, Social Media, Banking): 70%+
- Utilities and Helpers: 0-30% (only if complex or frequently changed)
- **Overall Target: 50-60%** (measured via pytest-cov)

**Mandatory Tests** (ALL Gold Tier features):
1. Ralph Wiggum loop state persistence across restarts
2. CEO Briefing revenue calculation accuracy (with mocked Odoo data)
3. Multi-MCP coordination (no double-execution)
4. Approval workflow with 24-hour expiry
5. Circuit breaker trip and recovery
6. Session expiry detection (WhatsApp, LinkedIn, Odoo)
7. Fallback mechanism (API unavailable → draft/in-memory queue)

**Integration Tests** (Critical Flows Only):
1. Gmail watcher → Plan generation → Approval → Email send
2. Odoo invoice creation → CEO Briefing revenue tracking
3. Social media post → Approval → Post execution → Analytics
4. Ralph Wiggum loop: 5-step autonomous task completion

**Chaos Tests** (Failure Scenarios):
1. Kill watcher mid-operation → verify auto-restart within 10s
2. Odoo API failure → verify fallback to draft invoices
3. MCP coordinator crash → verify MCPs pause and recover
4. Disk 95% full → verify graceful degradation with alert

**Tests MAY Be Skipped For**:
- Simple getters/setters (one-line return statements)
- Static templates (no dynamic content)
- Logging/formatting functions (unless compliance required)
- Utility functions with trivial logic (filename sanitization, etc.)

**Rationale**: Risk-based testing focuses effort where it matters. Critical flows (revenue, multi-MCP, Ralph Wiggum) require thorough testing. Trivial utilities don't. This approach saves 60-70% on token/context usage while maintaining quality.

### X. Code Quality Gates (BLOCKING MERGE)

The following quality gates MUST pass with zero errors before any pull request can merge: Linting via `ruff check` with 0 errors. Formatting via `black` enforced (line length 100 characters). Type checking via `mypy --strict` with 0 errors—all function signatures MUST have type hints (parameters and return type), `Any` type is PROHIBITED without explicit justification comment. Security scan via `bandit` with 0 high-severity issues. Import order via `isort` enforced.

**Rationale**: Automated quality gates catch defects early. Consistent formatting improves readability. Strict type checking prevents runtime errors. Security scanning identifies vulnerabilities before deployment.

### XI. Logging Schema & Alerting

Every log entry MUST include the following fields in JSON format: `timestamp` (ISO-8601), `level` (DEBUG|INFO|WARNING|ERROR|CRITICAL), `component` (watcher|orchestrator|skill|logger), `action` (file_created|approval_requested|action_executed), `dry_run` (true|false), `correlation_id` (UUID tracking request across components), `details` (object with contextual data). Alerting thresholds: >5 errors in 1 minute triggers immediate user notification (create file in Needs_Action/), >10 warnings in 10 minutes triggers Dashboard.md update. Log retention: INFO level retained for 7 days then rotated; ERROR/CRITICAL retained for 30 days.

**Rationale**: Structured logging enables automated analysis and correlation. Alerting thresholds prevent alert fatigue while ensuring critical issues are noticed. Retention policies balance debuggability with disk space.

### XII. Performance Budgets

Watcher check interval MUST NOT exceed 60 seconds (configurable per deployment). Action file creation MUST complete in <2 seconds for files <10MB. Orchestrator loop MUST process approval in <5 seconds from file detection to execution start. Memory usage MUST NOT exceed 500MB during normal operation (measured via process monitoring). Log file size MUST NOT exceed 100MB per file (enforced by rotation at 7 days or 100MB, whichever comes first).

**Rationale**: Performance budgets prevent gradual degradation. Explicit budgets enable performance testing and capacity planning. Memory limits ensure stability on resource-constrained systems.

**Silver Tier Extension**: Watcher intervals MUST NOT exceed: Gmail (2 minutes), WhatsApp (30 seconds), FileSystem (60 seconds). Process manager MUST restart crashed watchers within 10 seconds. MCP server calls MUST complete within 5 seconds (excluding external API latency). Approval workflow MUST detect file moves within 5 seconds. Scheduled tasks MUST start within 60 seconds of scheduled time. Memory usage per watcher MUST NOT exceed 200MB.

**Gold Tier Extension**: Odoo JSON-RPC calls MUST complete within 5 seconds (excluding external API latency). CEO Briefing generation MUST complete within 60 seconds. Ralph Wiggum iteration MUST complete within 30 seconds per loop. Multi-MCP coordination overhead MUST NOT exceed 100ms. Analytics dashboard refresh MUST complete within 5 seconds. Cross-domain queries MUST complete within 2 seconds.

### XIII. AI Reasoning Engine & Python Skills Pattern

**AI Reasoning Engine**: Qwen Code CLI (free tier: 1,000 OAuth calls/day) MUST be used for all AI-assisted development. MCP servers are NOT supported—Python Skills pattern MUST be used instead.

**Python Skills Pattern** (MANDATORY):
- All AI functionality MUST be implemented as Python functions in `src/skills.py` or `src/skills/*.py`
- Skills MUST be callable via: (1) direct Python import, (2) Qwen Code CLI subprocess, (3) CLI wrapper scripts
- Skills MUST validate DEV_MODE via `check_dev_mode()` before execution
- Skills MUST implement audit logging for all actions via `AuditLogger`
- Skills MUST handle errors with typed exceptions and graceful degradation
- Skills MUST support `--dry-run` mode where applicable
- Skills MUST be unit-testable with mocked external dependencies

**Tier Progression**:

| Tier | Python Skills Scope | External Dependencies | MCP Servers |
|------|---------------------|----------------------|-------------|
| **Bronze** | File operations only (read, write, move, create action files) | `watchdog`, `pathlib` | None |
| **Silver** | Email sending (`smtplib`), Web automation (`playwright`), HTTP APIs (`requests`), Plan generation, Approval workflow | `playwright`, `google-auth`, `requests` | Optional (Email, Browser) |
| **Gold** | Odoo accounting, Social media APIs, Bank integrations, CEO Briefing, Ralph Wiggum loop | Odoo v19+, Facebook Graph API, Twitter API v2, banking APIs | Required (5+: Odoo, Social, Browser, Calendar, Email) |

**Ralph Wiggum Pattern Documentation** (Gold Tier MANDATORY):

```python
# Ralph Wiggum Stop Hook Pattern (Gold Tier MANDATORY)

def ralph_wiggum_stop_hook(output: str, task_file: Path) -> bool:
    """
    Intercept Claude exit and re-inject prompt if task incomplete.
    
    Returns:
        True: Allow exit (task complete)
        False: Block exit, re-inject prompt (task incomplete)
    """
    if not is_task_complete(task_file):
        block_exit()
        reinject_prompt(output)
        return False
    return True

# State file pattern:
# /In_Progress/<agent>/<task-id>.md
# - Created when task starts
# - Updated with progress every iteration
# - Moved to /Done/ when complete
# - Max iterations: 10 (configurable in Company_Handbook.md)
```

**Example Skill Structure**:
```python
def send_email(
    to: str,
    subject: str,
    body: str,
    attachments: list[str] | None = None,
    dry_run: bool = False
) -> dict[str, Any]:
    """Send email via SMTP.

    Args:
        to: Recipient email address
        subject: Email subject line
        body: Email body text
        attachments: Optional list of file paths to attach
        dry_run: If True, log without sending

    Returns:
        Dict with status, message_id, timestamp

    Raises:
        ValueError: If email address invalid
        SMTPException: If sending fails
    """
    check_dev_mode()
    logger = AuditLogger(component="send_email_skill")
    # ... implementation
```

**MCP Servers** (OPTIONAL - Silver Tier):
- MCP servers MAY be used for complex external integrations (email, browser automation)
- MCP servers MUST be implemented in `src/mcp_servers/`
- MCP servers MUST be configured in `~/.config/claude-code/mcp.json` or project-local config
- MCP servers MUST validate DEV_MODE and support dry-run mode
- Python Skills pattern is PREFERRED over MCP for simplicity and testability

## Silver Tier Architecture

### Perception → Reasoning → Action Pattern

Silver tier implements the following architectural pattern:

```
┌─────────────────────────────────────────────────────────┐
│ PERCEPTION LAYER (Watchers)                             │
│ - GmailWatcher (Gmail API, 2-min interval)              │
│ - WhatsAppWatcher (Playwright, 30-sec interval)         │
│ - FileSystemWatcher (watchdog, 60-sec interval)         │
│ ALL extend BaseWatcher, create files in Needs_Action/   │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│ REASONING LAYER (Qwen Code CLI + Python Skills)         │
│ - create_plan skill: Generates Plan.md with steps       │
│ - request_approval skill: Creates approval requests     │
│ - triage_email skill: Categorizes and prioritizes       │
│ ALL validate DEV_MODE, log with correlation_id          │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│ ACTION LAYER (MCP Servers or Python Skills)             │
│ - Email MCP / send_email skill: Send emails             │
│ - Browser MCP / playwright skill: Web automation        │
│ - Approval Handler: Monitors Approved/ for execution    │
│ ALL require HITL approval for sensitive actions         │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│ SCHEDULING LAYER (Windows Task Scheduler / cron)        │
│ - Daily Briefing (8:00 AM): Summarize tasks             │
│ - Weekly Audit (Sunday 10:00 PM): Business review       │
│ ALL output to /Briefings/, failures logged              │
└─────────────────────────────────────────────────────────┘
```

### Human-in-the-Loop (HITL) Approval Workflow

**Sensitive Actions Requiring Approval**:
- Email sends to new contacts (not in address book)
- Email sends to >5 recipients (bulk)
- Email sends with attachments >1MB
- Payments to new recipients
- Payments >$100 (configurable threshold)
- Social media posts (LinkedIn, Twitter, Facebook)
- Any external API call with side effects

**Approval File Lifecycle**:
1. Claude/Python Skill creates `APPROVAL_<action>_<timestamp>.md` in `Pending_Approval/`
2. File includes YAML frontmatter: action type, parameters, created/expiry timestamps
3. Human reviews file, moves to `Approved/` or `Rejected/`
4. Approval Handler detects move:
   - `Approved/` → Execute action via MCP/Skill, log to audit, move to `Done/`
   - `Rejected/` → Log cancellation, move to `Rejected/` archive
5. Files in `Pending_Approval/` >24 hours flagged as expired in Dashboard.md

**Approval File Template** (in `vault/Templates/approval_request_template.md`):
```markdown
---
type: approval_request
action: send_email|payment|social_post
action_details: {to, subject, body, ...}
created: ISO timestamp
expires: ISO timestamp (24 hours later)
status: pending|approved|rejected|expired
risk_level: low|medium|high
---

## Action Details
<Clear description of intended action>

## Risk Assessment
<Why this requires approval>

## To Approve
Move this file to /Approved folder.

## To Reject
Move this file to /Rejected folder.
```

### Plan.md Generation

**Trigger**: New file detected in `Needs_Action/`

**Plan Structure** (in `vault/Templates/plan_template.md`):
```markdown
---
created: ISO timestamp
status: pending|in_progress|awaiting_approval|completed|cancelled
objective: <task description>
source_file: <path to triggering file>
estimated_steps: <number>
completed_steps: <number>
---

## Steps
- [ ] Step 1: <description>
- [ ] Step 2: <description> (REQUIRES APPROVAL)
- [ ] Step 3: <description>

## Approval Required
<Link to approval file in Pending_Approval/>

## Completion Criteria
<What constitutes "done">
```

**Acceptance Criteria**:
- Plan created within 60 seconds of action file detection
- Plan status updated as steps complete
- Approval steps link to approval file
- Final status written to Dashboard.md

## Gold Tier Architecture

### Perception → Reasoning → Action → CEO Briefing Pattern

Gold tier extends Silver tier with autonomous multi-step task completion, Odoo accounting integration, social media APIs, and CEO Briefing with revenue tracking:

```
┌─────────────────────────────────────────────────────────────┐
│ GOLD TIER: AUTONOMOUS EMPLOYEE                              │
├─────────────────────────────────────────────────────────────┤
│ PERCEPTION LAYER (Extended)                                 │
│ - Gmail, WhatsApp, FileSystem (Silver)                      │
│ - Odoo Webhooks (NEW)                                       │
│ - Bank Transaction Feeds (NEW)                              │
│ - Social Media Mentions (NEW)                               │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│ REASONING LAYER (Extended)                                  │
│ - Qwen Code CLI + Ralph Wiggum Loop (NEW)                   │
│ - Multi-step autonomous task completion                     │
│ - State file management (/In_Progress/<agent>/)             │
│ - Task completion detection (/Done/)                        │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│ ACTION LAYER (Extended)                                     │
│ - Python Skills (Silver)                                    │
│ - MCP Servers (5+ coordinated):                             │
│   * Odoo MCP (invoices, payments, accounting)               │
│   * Social MCP (Facebook, Instagram, Twitter)               │
│   * Browser MCP (Playwright automation)                     │
│   * Calendar MCP (scheduling, meetings)                     │
│   * Email MCP (Gmail API)                                   │
│ - MCP Coordinator (NEW - prevents double-execution)         │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│ CEO BRIEFING ENGINE (NEW)                                   │
│ - Revenue tracking from Odoo/bank data                      │
│ - Expense categorization and analysis                       │
│ - Bottleneck identification                                 │
│ - Proactive suggestions generation                          │
│ - Output: vault/Briefings/CEO_Briefing_YYYYMMDD.md          │
└─────────────────────────────────────────────────────────────┘
```

**Ralph Wiggum Loop Pattern**:
- State file creation: `/In_Progress/<agent>/<task-id>.md`
- Stop hook intercepts Claude/Qwen exit
- Re-inject prompt if task file not in `/Done/`
- Max iterations: 10 (configurable in Company_Handbook.md)
- State persistence across restarts

**Multi-MCP Coordination**:
- Single coordinator process prevents double-execution
- MCP servers isolated (failure doesn't cascade)
- Shared audit logging across all MCPs
- Health monitoring per MCP server

## Technology Stack

### Core Runtime
- **Python**: 3.13+ with uv for environment management
- **Obsidian**: v1.10.6+ for vault/GUI
- **AI Reasoning Engine**: Qwen Code CLI (free OAuth tier - 1,000 calls/day)

### Bronze Tier Dependencies
- **File Monitoring**: `watchdog>=4.0.0` for file system monitoring
- **Environment**: `python-dotenv>=1.0.0` for .env file loading
- **Testing**: `pytest>=8.0.0`, `pytest-cov>=5.0.0`, `pytest-mock>=3.12.0`

### Silver Tier Dependencies (NEW)
- **Email Sending**: `smtplib` (stdlib), `imaplib` (stdlib) for Gmail integration
- **Gmail API**: `google-auth-oauthlib`, `google-api-python-client` for Gmail watcher
- **Web Automation**: `playwright>=1.40.0` for WhatsApp/LinkedIn browser automation
- **HTTP APIs**: `requests>=2.31.0`, `httpx` for REST API integrations
- **Process Management**: `psutil>=5.9.0` for watcher process monitoring
- **MCP Servers** (OPTIONAL): Node.js v24+ for MCP server implementations

### Gold Tier Dependencies (MANDATORY for G1-G12)
- **Accounting Integration**: 
  - Odoo Community Edition v19+ (self-hosted, local or Docker)
  - JSON-RPC client: `requests>=2.31.0` with custom Odoo RPC wrapper
  - Database: PostgreSQL 14+ (Odoo backend)
  - Setup time: 2 hours (install + configure)
  
- **Social Media APIs**:
  - Facebook Graph API v18.0+ (requires Facebook Developer Account, 1h setup)
  - Instagram Graph API v18.0+ (requires Facebook Business integration)
  - Twitter API v2 (requires Twitter Developer Account, 1h setup; free tier: 1,500 posts/month)
  - LinkedIn API (browser automation via Playwright, no API key required)
  
- **Banking Integration** (for CEO Briefing revenue tracking):
  - Bank API clients (platform-specific) OR
  - CSV import pattern (manual download, automated parsing)
  - Plaid API (optional, for US banks)
  
- **Multi-MCP Coordination**:
  - Node.js v24+ (for MCP server implementations)
  - `@modelcontextprotocol/sdk` for MCP server development
  - Redis (optional, for distributed locking across MCPs)
  
- **Analytics & Visualization**:
  - `prometheus-client>=0.19.0` for metrics exposition
  - `matplotlib>=3.8.0` or `plotly>=5.18.0` for chart generation (Markdown-compatible)
  - SQLite (for metrics persistence, already in Silver)

### Quality Tools (ALL TIERS - BLOCKING MERGE)
- **Linting**: `ruff>=0.1.0` with 0 errors required
- **Formatting**: `black>=24.0.0` with line length 100 characters
- **Type Checking**: `mypy>=1.8.0` with `--strict` flag, 0 errors required
- **Security**: `bandit>=1.7.0` with 0 high-severity issues required
- **Import Order**: `isort>=5.13.0` enforced

## Directory Structure (Non-Negotiable)

```
vault/
  ├── Inbox/              # Drop zone for incoming files
  ├── Needs_Action/       # Action files created by watchers
  ├── Plans/              # [SILVER] Multi-step task plans with checkboxes
  ├── Pending_Approval/   # Waiting for human review (>60 seconds before execution)
  ├── Approved/           # Human-approved actions ready to execute
  ├── Rejected/           # Declined actions (logged, not executed)
  ├── Briefings/          # [SILVER] Daily/Weekly briefings
  │   ├── Daily_*.md        # [SILVER] Daily briefings
  │   ├── Weekly_*.md       # [SILVER] Weekly audits
  │   └── CEO_Briefing_*.md # [GOLD] CEO briefings with revenue
  ├── Templates/          # [SILVER] Plan and approval request templates
  ├── Done/               # Completed tasks
  ├── Logs/               # Audit logs (JSON)
  ├── In_Progress/        # [GOLD] Ralph Wiggum state files
  │   └── <agent>/          # [GOLD] Per-agent state directories
  ├── Drafts/             # [GOLD] Draft posts, invoices
  ├── Analytics/          # [GOLD] Charts, metrics reports
  ├── Dashboard.md        # System status overview
  └── Company_Handbook.md # Rules of engagement

src/
  ├── base_watcher.py       # Abstract base class (ALL watchers MUST extend this)
  ├── filesystem_watcher.py # Bronze: File monitoring
  ├── watchers/             # [SILVER] Additional watchers
  │   ├── gmail_watcher.py    # Gmail API integration
  │   └── whatsapp_watcher.py # Playwright-based WhatsApp Web monitoring
  ├── orchestrator.py       # Main orchestration logic
  ├── approval_handler.py   # [SILVER] HITL approval workflow
  ├── audit_logger.py       # Structured logging
  ├── skills.py             # Python Skills (Bronze: file ops)
  ├── skills/               # [SILVER] Extended skills
  │   ├── create_plan.py      # Plan.md generation
  │   ├── request_approval.py # Approval request creation
  │   ├── send_email.py       # Email sending (smtplib)
  │   └── linkedin_posting.py # LinkedIn automation (Playwright)
  ├── ralph_wiggum/         # [GOLD] Ralph Wiggum loop implementation
  │   ├── stop_hook.py        # Stop hook interceptor
  │   ├── state_manager.py    # State file management (/In_Progress/)
  │   └── iteration_tracker.py # Max iterations, retry logic
  ├── mcp_coordinator/      # [GOLD] Multi-MCP coordination
  │   ├── coordinator.py      # Prevents double-execution
  │   ├── health_monitor.py   # MCP health checks
  │   └── distributed_lock.py # Locking for concurrent MCPs
  ├── ceo_briefing/         # [GOLD] CEO Briefing engine
  │   ├── revenue_tracker.py  # Revenue calculation from Odoo/bank
  │   ├── expense_analyzer.py # Expense categorization
  │   ├── bottleneck_detector.py # Identify delays
  │   └── suggestion_generator.py # Proactive recommendations
  ├── cross_domain/         # [GOLD] Personal + Business unification
  │   ├── domain_tagger.py    # Tag actions as personal/business
  │   └── unified_dashboard.py # Combined view generation
  ├── mcp_servers/          # [SILVER] OPTIONAL - MCP servers for external actions
  │   ├── odoo_mcp/           # [GOLD] Odoo JSON-RPC wrapper
  │   ├── social_mcp/         # [GOLD] Facebook, Instagram, Twitter
  │   ├── browser_mcp/        # [SILVER] Playwright automation
  │   ├── calendar_mcp/       # [GOLD] Calendar integration
  │   └── email_mcp/          # [SILVER] Gmail API
  └── scheduler/            # [SILVER] Scheduled task implementations
      ├── daily_briefing.py   # 8:00 AM daily summary
      └── weekly_audit.py     # Sunday 10:00 PM weekly review

scripts/
  ├── ralph-loop.bat        # Autonomous multi-step task loop for Qwen Code CLI
  ├── setup-vault.ps1       # Vault initialization script
  ├── start_watchers.ps1    # [SILVER] Start all watchers via process manager
  └── register_scheduled_tasks.ps1  # [SILVER] Windows Task Scheduler setup

data/
  ├── odoo.db               # [GOLD] Odoo SQLite/PostgreSQL
  ├── revenue.db            # [GOLD] Revenue tracking cache
  └── analytics.db          # [GOLD] Analytics data store

tests/
  ├── unit/                 # Unit tests (50-60% coverage required)
  ├── integration/          # Integration tests (watcher→plan→approval→execution)
  ├── contract/             # Contract tests (BaseWatcher, Python Skills interfaces)
  └── chaos/                # Chaos/failure scenario tests (API failures, crashes)
```

## Safety Validation Checklist

### Bronze Tier (REQUIRED - All Must Pass)
- [ ] File dropped in Inbox/ creates action file in Needs_Action/ (with and without --dry-run)
- [ ] Qwen Code CLI reads action file and creates Plan.md
- [ ] DEV_MODE=false prevents ANY external API calls
- [ ] STOP file halts orchestrator within 5 seconds
- [ ] All actions logged to /Logs/ with correlation_id
- [ ] Path traversal attempts blocked and logged
- [ ] pytest --cov=src shows 50-60%+ coverage (risk-based)
- [ ] ruff check src/ passes with 0 errors
- [ ] mypy --strict src/ passes with 0 errors
- [ ] bandit -r src/ shows 0 high-severity issues
- [ ] Qwen Code CLI installed and authenticated (`qwen --version`, `/auth` completed)

### Silver Tier (REQUIRED for Silver Completion - All Must Pass)
- [ ] Gmail watcher detects new emails and creates action files (2-minute interval)
- [ ] WhatsApp watcher detects keyword messages and creates action files (30-second interval)
- [ ] Process manager keeps all watchers alive (auto-restart on crash)
- [ ] Plan.md files created with YAML frontmatter and step checkboxes
- [ ] Approval request files created for sensitive actions (payments, emails to new contacts)
- [ ] Moving file to Approved/ triggers MCP action execution
- [ ] Moving file to Rejected/ logs cancellation (no execution)
- [ ] Expired approvals (>24 hours) flagged in Dashboard.md
- [ ] Daily briefing scheduled task runs at 8:00 AM, creates file in /Briefings/
- [ ] Email MCP server (or Python skill) sends test email successfully
- [ ] LinkedIn posting creates approval request, waits for approval, then posts
- [ ] All watcher failures logged with stack traces and recovered gracefully
- [ ] API rate limit handling tested (exponential backoff verified)
- [ ] Session expiry (WhatsApp, LinkedIn) detected and user notified
- [ ] Windows Task Scheduler tasks registered and executable
- [ ] Integration test: watcher→plan→approval→MCP execution completes
- [ ] Chaos test: Kill watcher mid-operation, verify recovery within 60 seconds
- [ ] Chaos test: Simulate API failure, verify retry with backoff
- [ ] Chaos test: Fill disk to 95%, verify graceful degradation and alert

### Gold Tier (REQUIRED for Gold Completion - All Must Pass)

**Odoo Accounting (G1):**
- [ ] Odoo Community v19+ installed and running locally (or Docker container)
- [ ] JSON-RPC connection established (test: create invoice via API)
- [ ] Invoice creation via MCP/Skill works (dry-run verified)
- [ ] Payment tracking updates invoice status
- [ ] Financial reports generated (P&L, balance sheet)
- [ ] Bank transaction import and categorization functional

**Social Media Integration (G2-G4):**
- [ ] Facebook post creation with approval workflow
- [ ] Instagram post creation (images, carousels) with approval
- [ ] Twitter/X tweet creation with approval workflow
- [ ] Analytics retrieval for all platforms (reach, engagement)
- [ ] Weekly summary reports generated automatically

**CEO Briefing (G5):**
- [ ] Weekly audit runs Sunday 10 PM automatically
- [ ] Revenue data pulled from Odoo/bank integration
- [ ] Expense analysis with subscription audit
- [ ] Bottleneck identification (tasks taking too long)
- [ ] Proactive suggestions generated (cost optimization)
- [ ] Briefing format matches template (Executive Summary, Revenue, Tasks, Bottlenecks, Suggestions)

**Ralph Wiggum Loop (G6):**
- [ ] Stop hook intercepts Claude/Qwen exit correctly
- [ ] State files created in `/In_Progress/<agent>/`
- [ ] Task completion detection (file moved to `/Done/`)
- [ ] Max iterations enforced (default: 10)
- [ ] State persists across application restarts
- [ ] Loop recovery after crash (state file not lost)

**Multi-MCP Coordination (G7):**
- [ ] 5+ MCP servers configured and operational (Odoo, Social, Browser, Calendar, Email)
- [ ] MCP Coordinator prevents double-execution
- [ ] MCP servers isolated (one failure doesn't affect others)
- [ ] Centralized audit logging across all MCPs
- [ ] Health monitoring per MCP server (status page)

**Error Recovery (G8):**
- [ ] All external calls have retry logic with exponential backoff
- [ ] Circuit breakers prevent cascade failures (trip after 5 failures)
- [ ] Fallback mechanisms in place (in-memory queue, draft files)
- [ ] Alert escalation working (4 levels: log → dashboard → alert file → notify)
- [ ] Chaos test: Kill one MCP, verify others continue operating

**Audit Logging (G9):**
- [ ] Enhanced log schema implemented (timestamp, level, component, action, correlation_id, user, details, duration_ms, result)
- [ ] Log search utility functional (query by date, component, action, correlation_id)
- [ ] Log reporting (daily/weekly summaries) generated
- [ ] 90-day log retention enforced

**Cross-Domain (G10):**
- [ ] Domain tagging on all action files (personal vs business)
- [ ] Unified Dashboard.md with domain sections
- [ ] Cross-domain workflows supported (personal email → business lead)
- [ ] Domain filtering in reports

**Analytics Dashboard (G11):**
- [ ] Real-time metrics dashboard (watcher uptime, action completion rate, approval stats, error rates)
- [ ] Visual charts in Dashboard.md (Markdown-compatible)
- [ ] Export functionality (PDF reports, CSV data)

**Documentation (G12):**
- [ ] Gold Tier Architecture document complete (`docs/gold-tier-architecture.md`)
- [ ] Deployment guide complete (`docs/gold-deployment.md`)
- [ ] API Reference complete (`docs/gold-api-reference.md`)
- [ ] Lessons Learned captured (`docs/gold-lessons-learned.md`)

**Integration Tests:**
- [ ] End-to-end: Odoo invoice → CEO Briefing revenue tracking
- [ ] End-to-end: Social media post → Analytics summary
- [ ] End-to-end: Ralph Wiggum loop completes 5-step task autonomously
- [ ] Multi-MCP: 3 MCPs operate concurrently without interference

**Chaos Tests:**
- [ ] Odoo API failure: Verify fallback to draft invoices
- [ ] Social media API rate limit: Verify queuing and retry
- [ ] MCP crash: Verify coordinator detects and continues with remaining MCPs
- [ ] Ralph Wiggum max iterations: Verify graceful halt with state preserved

## Emergency Procedures

- **Unintended action detected**: Create vault/STOP file immediately
- **Credential compromise suspected**: Rotate credentials, review /Logs/
- **Watcher runaway**: Kill process, check for error loops in logs
- **Performance degradation**: Check memory usage, review log rotation, verify no file handle leaks
- **Qwen API rate limit hit**: Batch requests, implement caching, or wait for daily reset (midnight UTC)
- **Session expiry detected**: Notify user for re-authentication, pause affected watcher
- **Odoo unavailable**: Queue invoices in `/Drafts/`, retry after 5 minutes, alert user after 3 failures
- **Social media API rate limited**: Save post as draft, schedule retry after rate limit reset (Facebook: 1 hour, Twitter: 15 minutes)
- **Ralph Wiggum infinite loop detected**: Max iterations reached, preserve state, create alert file in `Needs_Action/`
- **MCP Coordinator failure**: All MCPs pause, coordinator restarts within 10 seconds, queued requests processed
- **CEO Briefing generation fails**: Create alert file, retry next scheduled run, notify user of missing data

## Development Workflow & Quality Gates

All pull requests MUST verify constitution compliance (security features present, tests passing, quality gates passing). Complexity MUST be justified with rationale and rejected alternatives. Version bump rules MUST follow semantic versioning:

- **MAJOR**: Security principle changes, breaking API changes, quality gate additions, AI engine changes, tier progression
- **MINOR**: New watcher/skill added, new tier functionality, performance budget changes, new MCP servers
- **PATCH**: Bug fixes, clarifications, non-breaking improvements

Constitution amendments require: documentation, approval rationale, and migration plan if breaking.

## Governance

This constitution supersedes all other development practices. Amendments require:

1. Documentation of the proposed change
2. Approval rationale explaining why the change is needed
3. Migration plan if the change is breaking

All PRs and reviews MUST verify compliance with this constitution. Use `.specify/memory/constitution.md` as the single source of truth for runtime development guidance.

**Gold Tier amendments require**:
1. Odoo Community v19+ setup and testing (2 hours)
2. Facebook Developer Account setup (1 hour)
3. Twitter Developer Account setup (1 hour)
4. Ralph Wiggum pattern validation (autonomous task completion test)
5. Multi-MCP coordination test (5+ MCPs running concurrently)

**Version**: 6.0.0 | **Ratified**: 2026-04-02 | **Last Amended**: 2026-04-02 (Platinum Tier preparation)

---

## Platinum Tier Architecture

### XIV. Platinum Tier: Cloud + Local Executive (Production-Ready)

**Architecture Overview**:
Platinum Tier extends Gold Tier with a two-agent architecture: Cloud Agent (24/7 always-on) and Local Agent (user workstation). This enables continuous operation while maintaining strict security boundaries for sensitive operations.

```
┌─────────────────────────────────────────────────────────────────┐
│ CLOUD AGENT (24/7 VM: Oracle/AWS/Google Cloud)                  │
├─────────────────────────────────────────────────────────────────┤
│ Responsibilities (DRAFT-ONLY):                                  │
│ - Email triage + draft replies (requires Local approval)        │
│ - Social post drafts/scheduling (requires Local approval)       │
│ - Odoo draft invoices (requires Local approval to post)         │
│ - Monitoring + alerting (health checks, metrics)                │
│                                                                 │
│ Writes to: /Updates/<domain>/, /Signals/<domain>/               │
│ NEVER stores: WhatsApp sessions, banking creds, payment tokens  │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼  Vault Sync (Git/Syncthing)
                     │  Excludes: .env, tokens, sessions, creds
┌────────────────────┴────────────────────────────────────────────┐
│ LOCAL AGENT (User Workstation)                                  │
├─────────────────────────────────────────────────────────────────┤
│ Responsibilities (EXECUTION AUTHORITY):                         │
│ - Final approvals (move files to Approved/)                     │
│ - WhatsApp session (browser automation)                         │
│ - Payments/banking (final execution)                            │
│ - Send/post actions (Email MCP, Social MCP)                     │
│ - Merge Cloud updates into Dashboard.md (single-writer rule)    │
│                                                                 │
│ Stores secrets in: OS Credential Manager (never in vault)       │
└─────────────────────────────────────────────────────────────────┘
```

**P1: Cloud 24/7 Deployment Requirements**:
- Cloud Agent MUST run on cloud VM (Oracle Cloud Free Tier, AWS EC2, or Google Cloud)
- MUST achieve 99% uptime SLA (measured via health endpoint)
- MUST implement auto-restart on crash (systemd or PM2)
- MUST expose health endpoint at `http://<vm-ip>:8000/health`
- MUST implement resource monitoring (CPU <80%, Memory <80%, Disk <90%)
- MUST alert Local Agent on threshold breaches via `/Alerts/` files

**P2: Work-Zone Specialization**:
- **Cloud owns** (draft-only, requires Local approval):
  - Email triage: Categorize, draft replies, flag urgent
  - Social media: Draft posts, schedule (no auto-post)
  - Odoo accounting: Draft invoices, categorize expenses
  - Monitoring: Health checks, metrics collection
- **Local owns** (execution authority):
  - Approvals: Move files from `Pending_Approval/` to `Approved/`
  - WhatsApp: Session management, message sending
  - Payments: Bank API calls, payment execution
  - Send/Post: Email send, social media posting
  - Dashboard: Single-writer rule (Local merges Cloud updates)

**P3: Delegation via Synced Vault**:
- **Folder Structure**:
  - `/Needs_Action/<domain>/` - Domain-specific action files (Cloud + Local)
  - `/Plans/<domain>/` - Domain-specific plans
  - `/Pending_Approval/<domain>/` - Domain-specific approvals
  - `/In_Progress/<agent>/` - Per-agent claim files (Cloud/Local)
  - `/Updates/<domain>/` - Cloud writes status updates here
  - `/Signals/<domain>/` - Cloud writes alerts/notifications here
- **Claim-by-Move Rule**:
  - First agent to move file from `/Needs_Action/` to `/In_Progress/<agent>/` owns it
  - Other agents MUST ignore claimed files (check every 60 seconds)
  - Prevents double-work across Cloud/Local agents
- **Single-Writer Rule**:
  - ONLY Local Agent MAY write to `Dashboard.md`
  - Cloud Agent writes to `/Updates/` and `/Signals/`
  - Local Agent merges updates into Dashboard.md every 5 minutes
- **Vault Sync Mechanism**:
  - MUST use Git (recommended) or Syncthing
  - Sync frequency: Every 60 seconds (configurable)
  - Conflict resolution: Last-write-wins for action files, Local-wins for Dashboard.md

**P4: Security Boundaries (CRITICAL)**:
- **Vault Sync Exclusions** (via .gitignore):
  - `.env` - Environment variables with secrets
  - `*.session` - WhatsApp/browser session files
  - `tokens/` - API tokens and OAuth credentials
  - `banking/` - Banking credentials and payment tokens
  - `credentials/` - Any credential files
- **Cloud Agent NEVER has access to**:
  - WhatsApp Web session (browser cookies, local storage)
  - Banking API credentials (username, password, API keys)
  - Payment tokens (Stripe, PayPal, bank transfer credentials)
  - Email SMTP credentials (for sending, not reading)
  - Social media posting credentials (Facebook, Twitter, LinkedIn)
- **Local Agent MUST**:
  - Store all secrets in OS Credential Manager (Windows Credential Manager, macOS Keychain, 1Password CLI)
  - Never sync secrets to cloud via Git/Syncthing
  - Validate all Cloud-sourced actions before execution
  - Maintain separate .env file (not synced)

**P5: Cloud Odoo Deployment**:
- Odoo Community v19+ MUST be deployed on separate cloud VM (or same VM with Docker isolation)
- MUST configure HTTPS with valid SSL/TLS certificate (Let's Encrypt recommended)
- MUST implement automated daily backups (encrypted, stored off-site)
- MUST expose health endpoint at `https://<odoo-domain>/web/health`
- **Cloud Agent**: Draft-only accounting actions (create_invoice, categorize_expense)
- **Local Agent**: Approval + posting of invoices/payments (record_payment, validate_invoice)
- Backup retention: 30 days minimum, encrypted with AES-256

**P6: A2A Upgrade (Phase 2 - Optional)**:
- MAY replace file-based handoffs with direct Agent-to-Agent messages
- MUST use HTTP REST API or WebSocket for real-time communication
- MUST keep vault as audit record (read-only for A2A messages)
- MUST maintain backward compatibility with file-based workflow
- A2A message schema:
  ```json
  {
    "type": "approval_request|status_update|alert",
    "source": "cloud_agent|local_agent",
    "correlation_id": "uuid",
    "payload": { ... },
    "timestamp": "ISO-8601"
  }
  ```

**P7: Platinum Demo (Minimum Passing Gate)**:
The following end-to-end workflow MUST complete successfully:
1. Email arrives while Local is offline (Cloud detects, Local disconnected)
2. Cloud drafts reply (draft-only, no send)
3. Cloud writes approval file to `/Pending_Approval/email/`
4. Local returns (user reconnects, vault sync completes)
5. User approves (moves file to `/Approved/`)
6. Local executes send via Email MCP/Skill
7. Local logs action to audit logger
8. Local moves task to `/Done/`

**Acceptance Criteria**:
- [ ] All 8 steps complete successfully
- [ ] Audit log contains full trail (Cloud detect → Local execute)
- [ ] No secrets synced to Cloud (verified via .gitignore check)
- [ ] Cloud never accessed WhatsApp session or banking credentials
- [ ] Vault sync completed without conflicts

### Platinum Tier Directory Structure

```
vault/
  ├── Needs_Action/
  │   ├── email/              # Platinum: Email-specific action files
  │   ├── whatsapp/           # Platinum: WhatsApp-specific
  │   ├── social/             # Platinum: Social media-specific
  │   └── accounting/         # Platinum: Odoo-specific
  ├── Plans/
  │   ├── email/
  │   ├── whatsapp/
  │   ├── social/
  │   └── accounting/
  ├── Pending_Approval/
  │   ├── email/
  │   ├── whatsapp/
  │   ├── social/
  │   └── accounting/
  ├── In_Progress/
  │   ├── cloud/              # Platinum: Cloud agent claim files
  │   └── local/              # Platinum: Local agent claim files
  ├── Updates/                # Platinum: Cloud writes status updates here
  │   ├── email/
  │   ├── social/
  │   └── accounting/
  ├── Signals/                # Platinum: Cloud writes alerts here
  │   ├── critical/           # Immediate attention required
  │   └── info/               # Informational updates
  ├── Drafts/
  │   ├── emails/             # Platinum: Draft email replies (Cloud)
  │   ├── social_posts/       # Platinum: Draft posts (Cloud)
  │   └── invoices/           # Platinum: Draft invoices (Cloud)
  ├── Done/
  ├── Logs/
  ├── Briefings/
  ├── Templates/
  ├── Dashboard.md            # Local-only (single-writer rule)
  └── Company_Handbook.md     # Synced (read-only for Cloud)

cloud/                        # Platinum: Cloud-specific configuration
  ├── .env.cloud              # Cloud environment (NO secrets)
  ├── config.yaml             # Cloud agent config
  └── sync_exclusions.txt     # Files excluded from sync

local/                        # Platinum: Local-specific configuration
  ├── .env.local              # Local environment (WITH secrets)
  ├── config.yaml             # Local agent config
  └── credentials/            # OS credential manager references

scripts/
  ├── platinum/
  │   ├── setup-cloud-vm.sh     # Platinum: Cloud VM setup script
  │   ├── configure-git-sync.sh # Platinum: Git sync configuration
  │   ├── configure-syncthing.sh # Platinum: Syncthing configuration
  │   ├── deploy-odoo-cloud.sh  # Platinum: Cloud Odoo deployment
  │   └── test-platinum-demo.sh # Platinum: Demo validation script
  └── ...

src/
  ├── cloud_agent/            # Platinum: Cloud-specific agent
  │   ├── draft_email_reply.py  # Draft-only email replies
  │   ├── draft_social_post.py  # Draft-only social posts
  │   ├── draft_invoice.py      # Draft-only invoices
  │   └── health_monitor.py     # Cloud health monitoring
  ├── local_agent/            # Platinum: Local-specific agent
  │   ├── merge_updates.py      # Merge Cloud updates to Dashboard.md
  │   ├── execute_send_email.py # Execute email send (has credentials)
  │   ├── execute_payment.py    # Execute payment (has banking creds)
  │   └── manage_whatsapp.py    # WhatsApp session (local-only)
  └── ...

tests/
  ├── platinum/
  │   ├── test_cloud_local_split.py    # Work-zone specialization
  │   ├── test_vault_sync.py           # Git/Syncthing sync
  │   ├── test_claim_by_move.py        # Double-work prevention
  │   ├── test_security_boundaries.py  # Secrets never sync
  │   └── test_platinum_demo.py        # End-to-end demo workflow
  └── ...
```

### Platinum Tier Safety Validation Checklist

**Cloud Deployment:**
- [ ] Cloud VM provisioned (Oracle Cloud Free Tier, AWS EC2, or Google Cloud)
- [ ] Health monitoring configured (uptime, CPU, memory, disk alerts)
- [ ] Auto-restart configured (systemd service or PM2 process manager)
- [ ] Network security hardened (SSH keys only, no password auth, firewall rules)
- [ ] Health endpoint accessible at `http://<vm-ip>:8000/health`
- [ ] Resource alerts configured (CPU >80%, Memory >80%, Disk >90%)

**Vault Sync:**
- [ ] Git remote configured (GitHub/GitLab private repo) OR Syncthing configured
- [ ] .gitignore excludes: .env, tokens/, sessions/, banking/, credentials/, *.session
- [ ] Sync frequency: Every 60 seconds (configurable in config.yaml)
- [ ] Conflict resolution tested (no data loss in 100 sync cycles)
- [ ] Local-wins rule enforced for Dashboard.md

**Work-Zone Specialization:**
- [ ] Cloud Agent creates draft emails (verified: no send capability)
- [ ] Cloud Agent creates draft social posts (verified: no post capability)
- [ ] Cloud Agent creates draft invoices (verified: no post capability)
- [ ] Local Agent approves and executes send/post/payment
- [ ] Claim-by-move prevents double-work (tested with concurrent actions)

**Security Boundaries:**
- [ ] Cloud has NO access to WhatsApp session (verified via file permissions)
- [ ] Cloud has NO access to banking credentials (verified via .gitignore)
- [ ] Cloud has NO access to payment tokens (verified via code audit)
- [ ] Local stores secrets in OS Credential Manager (verified via config)
- [ ] Vault sync excludes all secret files (verified via sync log)

**Cloud Odoo:**
- [ ] Odoo deployed on VM with HTTPS (SSL/TLS certificate valid)
- [ ] Automated backups configured (daily, encrypted, off-site storage)
- [ ] Health endpoint accessible (https://<domain>/web/health)
- [ ] Cloud Agent creates draft invoices only (verified via code audit)
- [ ] Local Agent approves and posts invoices (verified via integration test)

**Platinum Demo (End-to-End):**
- [ ] Step 1: Email arrives while Local offline (simulated)
- [ ] Step 2: Cloud drafts reply (draft file created in /Drafts/emails/)
- [ ] Step 3: Cloud writes approval file (/Pending_Approval/email/)
- [ ] Step 4: Local returns (vault sync completes, user notified)
- [ ] Step 5: User approves (file moved to /Approved/)
- [ ] Step 6: Local executes send via Email MCP/Skill
- [ ] Step 7: Local logs action (audit log entry created)
- [ ] Step 8: Local moves task to /Done/

**Integration Tests:**
- [ ] Cloud/Local agents operate concurrently without conflicts
- [ ] Vault sync completes within 60 seconds (measured over 100 syncs)
- [ ] Claim-by-move prevents double-work (tested with 50 concurrent actions)
- [ ] Local merges Cloud updates into Dashboard.md every 5 minutes
- [ ] Security boundaries enforced (attempted secret access blocked and logged)

**Chaos Tests:**
- [ ] Cloud VM restarts → Local continues operating (verified)
- [ ] Vault sync fails → Local queues updates, retries after 60 seconds
- [ ] Network partition → Cloud queues drafts, syncs when restored
- [ ] Odoo cloud unavailable → Cloud drafts invoices, queues for retry

---

## Emergency Procedures (Platinum Tier Extensions)

- **Cloud VM compromised**: Immediately revoke SSH keys, terminate VM, restore from backup, rotate all credentials
- **Vault sync corruption**: Restore vault from Local backup (Git history or Syncthing versioning), verify integrity
- **Cloud Agent runaway**: Local Agent sends STOP signal via `/Signals/critical/STOP_CLOUD`, restart Cloud Agent
- **Security boundary breach detected**: Immediately halt all Cloud operations, audit all synced files, rotate credentials
- **Odoo backup failure**: Alert Local Agent, manual backup triggered, investigate backup system
- **A2A communication failure**: Fallback to file-based handoffs, alert Local Agent, debug A2A channel
- **Platinum Demo failure**: Rollback to Gold Tier configuration, investigate failure point, re-test

---

## Platinum Tier Governance

**Amendment Requirements**:
Platinum Tier amendments require:
1. Cloud VM setup and testing (4 hours)
2. Vault sync configuration (Git or Syncthing) validation (2 hours)
3. Security boundary audit (verify no secrets synced) (2 hours)
4. Platinum Demo end-to-end validation (2 hours)
5. Chaos testing (Cloud VM failure, sync failure, network partition) (4 hours)

**Version**: 6.0.0 | **Ratified**: 2026-04-02 | **Last Amended**: 2026-04-02 (Platinum Tier preparation)
