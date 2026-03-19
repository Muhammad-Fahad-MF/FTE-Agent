<!--
SYNC IMPACT REPORT
==================
Version change: 3.0.0 → 4.0.0 (Major: Silver Tier support - multiple watchers, HITL workflow, scheduling, MCP servers)
Modified principles:
  - I. Security-First Automation (added Silver Tier Extension: approval expiry, watcher monitoring)
  - VIII. Production-Grade Error Handling (added Silver Tier Extension: API retry, circuit breaker, session expiry)
  - XII. Performance Budgets (added Silver Tier Extension: watcher intervals, process manager, MCP timeouts)
  - XIII. AI Reasoning Engine & Python Skills Pattern (expanded with tier progression table, skill requirements)
Added sections:
  - Silver Tier Architecture (Perception→Reasoning→Action pattern, HITL workflow, Plan.md generation)
  - Technology Stack (expanded with Bronze/Silver/Gold tier dependencies)
  - Directory Structure (added Silver tier folders: Plans/, Briefings/, Templates/, watchers/, skills/, scheduler/)
  - Safety Validation Checklist (expanded with Bronze and Silver tier validation items)
Removed sections: None
Templates requiring updates:
  - ⚠️ .specify/templates/plan-template.md (Add Silver tier Constitution Check for HITL, watchers, scheduling)
  - ⚠️ .specify/templates/spec-template.md (Add Silver tier dependency requirements, API credentials)
  - ⚠️ .specify/templates/tasks-template.md (Add Silver tier task categories: watcher, MCP, approval, scheduler)
  - ⚠️ .specify/templates/commands/*.md (May need Silver tier workflow examples)
Follow-up TODOs:
  - TODO(CREATE_README): Create README.md with Qwen Code CLI setup instructions
  - TODO(CREATE_SAFETY_MD): Create SAFETY.md documenting all safety features and limitations
  - TODO(CREATE_QUALITY_MD): Create QUALITY.md with detailed quality gate configuration examples
  - TODO(CREATE_SKILLS_MD): Create src/skills/*.py with Python Skills implementations for Silver tier
  - TODO(CREATE_WATCHERS_MD): Create src/watchers/README.md with watcher implementation guide
  - TODO(CREATE_MCP_MD): Create src/mcp_servers/README.md with MCP server setup guide
-->

# FTE-Agent Constitution

## Core Principles

### I. Security-First Automation (CRITICAL)

DEV_MODE=true MUST be set before ANY code runs—this is the kill switch for all external actions. The --dry-run flag MUST be implemented and functional in ALL action scripts including watchers, orchestrator, and skills. Audit logging MUST capture EVERY action attempt (success, failure, dry-run) to /vault/Logs/ in JSON format. Human-in-the-Loop (HITL) approval is REQUIRED for ALL sensitive actions including payments, external API calls, and file moves outside the vault. The STOP file mechanism MUST be implemented: creating vault/STOP immediately halts all orchestrator operations.

**Rationale**: Autonomous systems handling business affairs require non-bypassable safety mechanisms. These five security controls (DEV_MODE, --dry-run, audit logging, HITL, STOP file) form the minimum viable safety foundation.

**Silver Tier Extension**: Approval request files MUST include expiry timestamp (24 hours from creation). Expired approvals MUST be flagged in Dashboard.md and require re-approval before execution. Sensitive action thresholds (e.g., payment amount, email recipient count) MUST be configurable in Company_Handbook.md. All watcher processes MUST be monitored and auto-restarted on crash to prevent silent failures.

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

### IX. Testing Pyramid & Coverage

Unit tests with 80%+ code coverage (measured via pytest-cov) are MANDATORY—every function with business logic MUST have unit tests, and all external dependencies (file system, APIs, databases) MUST be mocked. Integration tests are REQUIRED for ALL cross-component flows: watcher→action file creation, orchestrator→Qwen invocation, approval→execution flow. Contract tests are MANDATORY for ALL public interfaces: BaseWatcher abstract methods, Python Skills input/output schemas. Chaos tests are REQUIRED for failure scenarios: kill watcher mid-operation (verify recovery), fill disk to 95% (verify graceful degradation), corrupt action file (verify error handling).

**Rationale**: The testing pyramid ensures defects are caught at the appropriate level. High coverage prevents regression. Contract tests catch breaking changes. Chaos testing validates resilience under failure conditions.

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

| Tier | Python Skills Scope | External Dependencies |
|------|---------------------|----------------------|
| **Bronze** | File operations only (read, write, move, create action files) | `watchdog`, `pathlib` |
| **Silver** | Email sending (`smtplib`), Web automation (`playwright`), HTTP APIs (`requests`), Plan generation, Approval workflow | `playwright`, `google-auth`, `requests` |
| **Gold** | Multiple external services (Odoo JSON-RPC, social media APIs, banking APIs, accounting integration) | Odoo client, Facebook API, Twitter API, banking APIs |

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

### Gold Tier Dependencies (Future)
- **Accounting**: Odoo JSON-RPC client (Odoo 19+)
- **Social Media**: Platform-specific API clients (Facebook, Instagram, Twitter/X)
- **Banking**: Bank API clients or Playwright for web automation

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
  ├── Templates/          # [SILVER] Plan and approval request templates
  ├── Done/               # Completed tasks
  ├── Logs/               # Audit logs (JSON)
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
  ├── mcp_servers/          # [SILVER] OPTIONAL - MCP servers for external actions
  │   └── email_mcp/          # Email MCP server (Node.js or Python)
  └── scheduler/            # [SILVER] Scheduled task implementations
      ├── daily_briefing.py   # 8:00 AM daily summary
      └── weekly_audit.py     # Sunday 10:00 PM weekly review

scripts/
  ├── ralph-loop.bat        # Autonomous multi-step task loop for Qwen Code CLI
  ├── setup-vault.ps1       # Vault initialization script
  ├── start_watchers.ps1    # [SILVER] Start all watchers via process manager
  └── register_scheduled_tasks.ps1  # [SILVER] Windows Task Scheduler setup

tests/
  ├── unit/                 # Unit tests (80%+ coverage required)
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
- [ ] pytest --cov=src shows 80%+ coverage
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
- [ ] Integration test: watcher→plan→approval→MCP execution completes end-to-end
- [ ] Chaos test: Kill watcher mid-operation, verify recovery within 60 seconds
- [ ] Chaos test: Simulate API failure, verify retry with backoff
- [ ] Chaos test: Fill disk to 95%, verify graceful degradation and alert

### Gold Tier (Future - Not Required for Silver)
- [ ] Odoo accounting integration creates invoices via JSON-RPC
- [ ] Facebook/Instagram posting with approval workflow
- [ ] Twitter/X posting with approval workflow
- [ ] Weekly CEO Briefing with revenue tracking generated
- [ ] Ralph Wiggum loop completes multi-step tasks autonomously
- [ ] Bank transaction monitoring creates alerts for unusual activity

## Emergency Procedures

- **Unintended action detected**: Create vault/STOP file immediately
- **Credential compromise suspected**: Rotate credentials, review /Logs/
- **Watcher runaway**: Kill process, check for error loops in logs
- **Performance degradation**: Check memory usage, review log rotation, verify no file handle leaks
- **Qwen API rate limit hit**: Batch requests, implement caching, or wait for daily reset (midnight UTC)
- **Session expiry detected**: Notify user for re-authentication, pause affected watcher

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

**Version**: 4.0.0 | **Ratified**: 2026-03-07 | **Last Amended**: 2026-03-19
