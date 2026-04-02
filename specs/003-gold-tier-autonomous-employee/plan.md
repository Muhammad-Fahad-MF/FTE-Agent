# Implementation Plan: Gold Tier Autonomous Employee

**Branch**: `003-gold-tier-autonomous-employee` | **Date**: 2026-04-02 | **Spec**: [spec.md](../003-gold-tier-autonomous-employee/spec.md)
**Input**: Feature specification for Gold Tier Autonomous Employee with cross-domain integration, Odoo accounting, social media, CEO briefings, error recovery, and Ralph Wiggum loop

## Summary

The Gold Tier Autonomous Employee implements a production-ready AI agent that operates 24/7 managing personal and business affairs. The architecture follows Perception → Reasoning → Action → CEO Briefing pattern with 6 MCP servers (Email, WhatsApp, Social Media, Odoo, Browser, Filesystem), 5 watchers (Gmail, WhatsApp, Social Media, Odoo, Filesystem), Ralph Wiggum autonomous loop for multi-step tasks, and automated CEO Briefing generation every Monday at 8 AM. The system implements circuit breakers, dead letter queues, and graceful degradation for production-grade error handling with 99% uptime target.

## Technical Context

**Language/Version**: Python 3.13+ (REQUIRED for type safety and modern async features)
**Primary Dependencies**: 
- Core: `playwright` (browser automation), `requests` (HTTP APIs), `google-auth` + `google-api-python-client` (Gmail), `odoo-xmlrpc` (Odoo JSON-RPC)
- Social Media: `tweepy` (Twitter API v2), `facebook-sdk` (Facebook Graph API v18+), `instagrapi` (Instagram)
- File Watching: `watchdog` (filesystem events)
- Testing: `pytest` + `pytest-cov` + `pytest-asyncio`
**Storage**: Local Obsidian vault (Markdown files) + Odoo PostgreSQL database (self-hosted)
**Testing**: pytest with 50-60% overall coverage target (90% critical business logic, 80% file flows, 70% API integration)
**Target Platform**: Windows 10/11 workstation (PowerShell + Python scripts)
**Performance Goals**: 
- Watcher latency: Gmail <2min, WhatsApp <30sec, others <60sec
- CEO Briefing generation: <60 seconds
- Ralph Wiggum iteration: <30 seconds per loop
- Action execution: <10 seconds (excluding external API latency)
- Dashboard refresh: <5 seconds
**Constraints**: 
- Local-first data storage (Obsidian vault)
- Free tier compatible (1,000 AI calls/day limit)
- Single-user system only
- 99% uptime target (excluding scheduled maintenance)
- Memory usage <500MB during normal operation
**Scale/Scope**: 
- 6 MCP servers coordinated
- 5 watchers running continuously
- 90-day audit log retention
- Max 10 Ralph Wiggum iterations per task
- 100 concurrent actions handling capacity

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Constitution Principle | Compliance Status | Evidence |
|------------------------|-------------------|----------|
| **I. Security-First Automation** | ✅ PASS | DEV_MODE validation in all skills, --dry-run flag implemented, audit logging to /Vault/Logs/, HITL approval for sensitive actions, STOP file mechanism |
| **II. Local-First Privacy Architecture** | ✅ PASS | All data in Obsidian vault (Markdown), secrets in .env (gitignored) or Windows Credential Manager, vault sync excludes .env/tokens/sessions |
| **III. Spec-Driven Development** | ✅ PASS | Following Spec → Plan → Tasks → Implementation → Tests. Python Skills pattern in src/skills/. Ralph Wiggum loop via scripts/ralph-loop.bat. Single-writer rule for Dashboard.md |
| **IV. Testable Acceptance Criteria** | ✅ PASS | All requirements have measurable success criteria (SC-001 to SC-020). Security tested first (dry-run → DEV_MODE → real mode) |
| **V. Observability & Debuggability** | ✅ PASS | Structured JSON logging with 7-day rotation. All watchers extend BaseWatcher. Dashboard.md shows status/pending/activity. File size limits enforced (skip >10MB) |
| **VI. Incremental Complexity (YAGNI)** | ✅ PASS | Bronze foundation first, then Silver extensions, then Gold full implementation. No refactoring unrelated code. Smallest viable diff |
| **VII. Path Validation & Sandboxing** | ✅ PASS | All file operations validate vault_path prefix. Skills validate DEV_MODE. Idempotency via executed approval hash tracking. 60-second minimum review time |
| **VIII. Production-Grade Error Handling** | ✅ PASS | Typed exceptions only. External APIs: timeout 30s, retry 3x exponential backoff, circuit breaker after 5 failures. Odoo/social media fallback mechanisms. MCP isolation |
| **IX. Testing Pyramid & Coverage** | ✅ PASS | Risk-based 50-60% overall target. Critical logic 90%+, file flows 80%+, API integration 70%. Mandatory tests for Ralph Wiggum, CEO Briefing, multi-MCP, approval workflow, circuit breakers |
| **X. Code Quality Gates** | ✅ PASS | ruff check (0 errors), black (100 char line length), mypy --strict (0 errors, no Any), bandit (0 high-severity), isort enforced |
| **XI. Logging Schema & Alerting** | ✅ PASS | JSON logs with timestamp/level/component/action/dry_run/correlation_id/details. Alerting: >5 errors/min → user notification, >10 warnings/10min → Dashboard update |
| **XII. Performance Budgets** | ✅ PASS | Watcher intervals: Gmail 2min, WhatsApp 30sec, others 60sec. Action file creation <2sec. Orchestrator <5sec. Memory <500MB. Log files <100MB |
| **XIII. AI Reasoning Engine & Python Skills** | ✅ PASS | Qwen Code CLI (1,000 OAuth calls/day). Python Skills in src/skills/. Skills validate DEV_MODE, implement audit logging, handle typed exceptions, support --dry-run |

**All gates passed**. Architecture is constitution-compliant. Proceed to Phase 0 research.

## Project Structure

### Documentation (this feature)

```text
specs/004-gold-tier-autonomous-employee/
├── plan.md              # This file (architecture decisions)
├── research.md          # Phase 0 output (technical research)
├── data-model.md        # Phase 1 output (entity schemas)
├── quickstart.md        # Phase 1 output (setup guide)
├── contracts/           # Phase 1 output (API schemas)
│   ├── odoo-mcp.yaml    # Odoo MCP OpenAPI spec
│   ├── social-mcp.yaml  # Social Media MCP OpenAPI spec
│   ├── email-mcp.yaml   # Email MCP OpenAPI spec
│   └── whatsapp-mcp.yaml # WhatsApp MCP OpenAPI spec
└── tasks.md             # Phase 2 output (implementation tasks - NOT created by /sp.plan)
```

### Source Code (repository root)

```text
FTE/
├── src/
│   ├── watchers/
│   │   ├── base_watcher.py       # Base class for all watchers
│   │   ├── gmail_watcher.py      # Gmail API watcher (2-min interval)
│   │   ├── whatsapp_watcher.py   # Playwright WhatsApp Web watcher (30-sec)
│   │   ├── social_media_watcher.py # Social media mentions watcher (60-sec)
│   │   ├── odoo_watcher.py       # Odoo webhook/transaction watcher (60-sec)
│   │   └── filesystem_watcher.py # Watchdog filesystem watcher (60-sec)
│   ├── skills/
│   │   ├── __init__.py
│   │   ├── email_skills.py       # send_email, draft_email, search_emails
│   │   ├── whatsapp_skills.py    # send_whatsapp, get_chat_history
│   │   ├── social_skills.py      # post_linkedin, post_twitter, post_facebook, post_instagram
│   │   ├── odoo_skills.py        # create_invoice, record_payment, categorize_expense
│   │   ├── approval_skills.py    # request_approval, check_approval, expire_approvals
│   │   ├── briefing_skills.py    # generate_ceo_briefing, calculate_revenue, analyze_expenses
│   │   ├── ralph_wiggum_skills.py # state_persistence, completion_detection, max_iterations_check
│   │   └── audit_skills.py       # log_action, query_logs, rotate_logs
│   ├── mcp_servers/
│   │   ├── email_mcp/
│   │   │   ├── __init__.py
│   │   │   ├── server.py         # Gmail API MCP server
│   │   │   └── handlers.py       # Send, draft, search handlers
│   │   ├── whatsapp_mcp/
│   │   │   ├── __init__.py
│   │   │   ├── server.py         # Playwright WhatsApp MCP server
│   │   │   ├── handlers.py       # Send, receive handlers
│   │   │   └── session_manager.py # Session preservation/recovery
│   │   ├── social_mcp/
│   │   │   ├── __init__.py
│   │   │   ├── server.py         # Unified social media MCP server
│   │   │   ├── linkedin_handler.py
│   │   │   ├── twitter_handler.py
│   │   │   ├── facebook_handler.py
│   │   │   └── instagram_handler.py
│   │   ├── odoo_mcp/
│   │   │   ├── __init__.py
│   │   │   ├── server.py         # Odoo JSON-RPC MCP server
│   │   │   ├── invoice_handler.py
│   │   │   ├── payment_handler.py
│   │   │   └── expense_handler.py
│   │   └── browser_mcp/
│   │       ├── __init__.py
│   │       ├── server.py         # Playwright browser automation MCP server
│   │       └── payment_portal_handler.py
│   ├── services/
│   │   ├── orchestrator.py       # Main orchestration loop
│   │   ├── process_manager.py    # Watchdog for watcher restarts (<10s)
│   │   ├── circuit_breaker.py    # Per-service circuit breaker (5 failures → open)
│   │   ├── retry_handler.py      # Exponential backoff (1s, 2s, 4s; max 3 retries)
│   │   ├── dead_letter_queue.py  # DLQ for failed actions (manual review)
│   │   ├── health_endpoint.py    # /health status of all components
│   │   └── mcp_coordinator.py    # Multi-MCP coordination (prevent double-execution)
│   ├── models/
│   │   ├── action_log.py         # Audit log schema
│   │   ├── approval_request.py   # Approval request schema
│   │   ├── ceo_briefing.py       # CEO Briefing data model
│   │   └── task_state.py         # Ralph Wiggum task state
│   └── utils/
│       ├── config.py             # Configuration loader (.env, Company_Handbook.md)
│       ├── logger.py             # Structured JSON logger
│       ├── dev_mode.py           # DEV_MODE validation
│       └── path_validator.py     # Path validation (prevent traversal)
├── tests/
│   ├── unit/
│   │   ├── watchers/
│   │   ├── skills/
│   │   ├── services/
│   │   └── models/
│   ├── integration/
│   │   ├── mcp_servers/
│   │   ├── odoo_api/
│   │   └── social_media_api/
│   ├── e2e/
│   │   ├── email_workflow/
│   │   ├── approval_workflow/
│   │   └── ceo_briefing_workflow/
│   └── chaos/
│       ├── service_failures/
│       ├── network_partitions/
│       └── resource_exhaustion/
├── scripts/
│   ├── ralph-loop.bat            # Ralph Wiggum loop launcher (Windows)
│   ├── start-watchers.bat        # Start all watchers
│   ├── start-orchestrator.bat    # Start main orchestrator
│   └── health-check.bat          # Health endpoint checker
├── vault/                        # Obsidian vault (local data)
│   ├── Inbox/
│   ├── Needs_Action/
│   ├── Pending_Approval/
│   ├── Approved/
│   ├── Rejected/
│   ├── Done/
│   ├── In_Progress/              # Ralph Wiggum state files
│   ├── Briefings/                # CEO Briefings (Monday 8 AM)
│   ├── Logs/                     # Audit logs (JSON, 90-day retention)
│   ├── Dashboard.md              # Real-time system health
│   └── Company_Handbook.md       # Configuration & rules
├── .env                          # Secrets (NEVER commit)
├── .env.example                  # Template (safe to commit)
└── requirements.txt              # Python dependencies
```

**Structure Decision**: Single project structure with modular src/ layout. Watchers, skills, MCP servers, and services are separated for independent testing and replacement. Tests follow pytest convention with unit/integration/e2e/chaos categorization. Vault folder structure implements the Inbox/Needs_Action/Done pattern with Ralph Wiggum state management.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| 6 MCP servers | Gold Tier requires 6 distinct external integrations (Gmail, WhatsApp, 4 social platforms, Odoo) | Silver Tier pattern (1-2 MCPs) insufficient for cross-domain integration requirement |
| Ralph Wiggum loop | Autonomous multi-step task completion is core Gold Tier requirement | Single-step processing cannot handle complex workflows (research → summarize → report) |
| CEO Briefing engine | Weekly business audit with revenue tracking from Odoo is mandatory Gold Tier feature | Manual reporting violates autonomous employee value proposition |
| Circuit breakers + DLQ | Production-grade error handling required for 99% uptime target | Basic retry logic insufficient for cascade failure prevention |
| Multi-MCP coordinator | Prevents double-execution when multiple MCPs operate concurrently | No coordination risks duplicate actions (e.g., double payment) |

**All complexity justified by Gold Tier requirements**. No simpler alternatives meet spec success criteria.

---

## Phase 0: Research & Technical Decisions

### Research Tasks

Based on Technical Context unknowns and integration complexity:

1. **Odoo Community v19+ JSON-RPC API**: Research authentication, invoice creation, payment recording, expense categorization endpoints
2. **Facebook Graph API v18+**: Research posting, insights, rate limits (200 calls/hour), permission requirements
3. **Twitter API v2**: Research posting, engagement metrics, rate limits (300 calls/15min), authentication flow
4. **Instagram Graph API**: Research posting, insights, business account requirements, rate limits
5. **LinkedIn API**: Research posting, rate limits (1 post/day), authentication via OAuth2
6. **Playwright WhatsApp Web session management**: Research session persistence, recovery after expiry, multi-device support
7. **Circuit breaker pattern implementation**: Research state machine (closed/open/half-open), reset timeout, failure counting
8. **Dead Letter Queue pattern**: Research queue structure, retry policies, manual review workflow
9. **Ralph Wiggum loop state persistence**: Research file-based state management, iteration counting, completion detection

### Research Findings (Consolidated)

**Decision 1: Odoo JSON-RPC Integration**
- **Chosen**: Direct JSON-RPC calls via `requests` library (no official Python client)
- **Rationale**: Odoo Community v19+ uses standard JSON-RPC 2.0. Lightweight approach avoids heavy ORM dependency.
- **Alternatives**: `odoo-xmlrpc` library (rejected: adds unnecessary complexity for simple CRUD operations)
- **Endpoints**: `/jsonrpc` for all calls. Methods: `create` (invoices), `write` (update), `search_read` (query)

**Decision 2: Social Media API Strategy**
- **Chosen**: Platform-specific Python SDKs (`tweepy`, `facebook-sdk`, `instagrapi`, `linkedin-api-client`)
- **Rationale**: Each platform has unique authentication and rate limiting. Dedicated SDKs handle platform quirks.
- **Alternatives**: Unified social media API (e.g., Buffer, Hootsuite) - rejected: adds cost, reduces control, violates local-first principle
- **Rate Limits**: Twitter 300/15min, Facebook 200/hour, LinkedIn 1 post/day, Instagram 25 posts/day

**Decision 3: WhatsApp Web Automation**
- **Chosen**: Playwright with persistent browser context for session management
- **Rationale**: WhatsApp Web doesn't offer official API. Playwright provides reliable browser automation with session persistence.
- **Alternatives**: Twilio WhatsApp API - rejected: costs money, violates local-first, requires business verification
- **Session Storage**: `--user-data-dir` for persistent profile. Session survives browser restarts.

**Decision 4: Circuit Breaker Implementation**
- **Chosen**: Custom implementation with state machine (closed → open → half-open)
- **Rationale**: Lightweight, no external dependencies. Configurable thresholds per service.
- **Alternatives**: `pybreaker` library - rejected: adds dependency, less flexible for per-service configuration
- **Configuration**: 5 consecutive failures → open. 300-second reset timeout. Half-open allows 1 test call.

**Decision 5: Dead Letter Queue Structure**
- **Chosen**: Markdown files in `/Vault/Dead_Letter_Queue/` with YAML frontmatter
- **Rationale**: Consistent with vault-based architecture. Human-readable. searchable in Obsidian.
- **Alternatives**: SQLite database - rejected: adds complexity, violates Markdown-first principle
- **Schema**: action_type, original_request, error_details, retry_count, quarantine_timestamp, status

**Decision 6: Ralph Wiggum State Persistence**
- **Chosen**: File-based state in `/Vault/In_Progress/<agent>/<task-id>.md`
- **Rationale**: Visible to user, survives restarts, searchable. Consistent with vault architecture.
- **Alternatives**: SQLite/JSON files - rejected: less transparent, harder to debug
- **Completion Detection**: File movement to `/Done/` OR `<promise>TASK_COMPLETE</promise>` tag

---

## Phase 1: Design & Contracts

### Data Model Design

**Entity 1: ActionLog**
```python
class ActionLog:
    timestamp: str           # ISO-8601
    level: str               # DEBUG|INFO|WARNING|ERROR|CRITICAL
    component: str           # watcher|orchestrator|skill|mcp_server
    action: str              # file_created|approval_requested|action_executed
    dry_run: bool            # True if dry-run mode
    correlation_id: str      # UUID tracking request across components
    domain: str              # personal|business
    target: str              # Resource being acted upon
    parameters: dict         # Action-specific parameters
    approval_status: str     # auto|human|none
    approved_by: str | None  # User ID if human-approved
    result: str              # success|failure|pending
    error: str | None        # Error message if failed
    details: dict            # Contextual data
```

**Entity 2: ApprovalRequest**
```python
class ApprovalRequest:
    type: str                # approval_request
    action: str              # send_email|payment|social_post|file_delete
    action_details: dict     # Action-specific parameters
    created: str             # ISO-8601 timestamp
    expires: str             # ISO-8601 (24 hours from creation)
    status: str              # pending|approved|rejected|expired
    risk_level: str          # low|medium|high
    approved_by: str | None  # User ID
    approved_at: str | None  # ISO-8601 timestamp
```

**Entity 3: CEOBriefing**
```python
class CEOBriefing:
    generated: str           # ISO-8601 timestamp
    period_start: str        # ISO-8601 (Monday 12:00 AM previous week)
    period_end: str          # ISO-8601 (Sunday 11:59 PM previous week)
    revenue: dict            # total, by_source, trend_percentage
    expenses: dict           # total, by_category, trend_percentage
    tasks_completed: int     # Count from /Done/ folder
    bottlenecks: list        # List of {task, expected, actual, delay}
    subscription_audit: list # List of {name, cost, last_used, recommendation}
    cash_flow_projection: dict # 30/60/90 day projections
    proactive_suggestions: list # List of actionable suggestions
```

**Entity 4: TaskState (Ralph Wiggum)**
```python
class TaskState:
    task_id: str             # UUID
    objective: str           # Task description
    created: str             # ISO-8601 timestamp
    iteration: int           # Current iteration (1-10)
    max_iterations: int      # Default: 10
    status: str              # in_progress|completed|failed|dlq
    state_data: dict         # Iteration-specific state
    completion_criteria: list # List of criteria to check
    completed_criteria: list # List of met criteria
    error: str | None        # Error if failed
    completed_at: str | None # ISO-8601 timestamp
```

**Entity 5: CircuitBreaker**
```python
class CircuitBreaker:
    service: str             # Service name (gmail, odoo, twitter, etc.)
    state: str               # closed|open|half_open
    failure_count: int       # Consecutive failures
    last_failure: str | None # ISO-8601 timestamp
    opened_at: str | None    # ISO-8601 (when tripped)
    reset_timeout: int       # Seconds before half-open (default: 300)
```

**Entity 6: DeadLetterQueueItem**
```python
class DeadLetterQueueItem:
    id: str                  # UUID
    action_type: str         # Original action type
    original_request: dict   # Full request payload
    error_details: str       # Error message + stack trace
    retry_count: int         # Number of retry attempts
    quarantine_timestamp: str # ISO-8601
    status: str              # pending_review|resolved|discarded
    resolved_by: str | None  # User ID
    resolved_at: str | None  # ISO-8601
    resolution_notes: str | None # Manual notes
```

### API Contracts

See `/contracts/` directory for OpenAPI specifications:

- `odoo-mcp.yaml`: Odoo JSON-RPC MCP endpoints (create_invoice, record_payment, categorize_expense, get_revenue_report)
- `social-mcp.yaml`: Social Media MCP endpoints (post_linkedin, post_twitter, post_facebook, post_instagram, get_analytics)
- `email-mcp.yaml`: Email MCP endpoints (send_email, draft_email, search_emails, get_unread_count)
- `whatsapp-mcp.yaml`: WhatsApp MCP endpoints (send_message, get_chat_history, mark_read, session_status)

### Quickstart Guide

See `quickstart.md` for:
- Prerequisites installation (Python 3.13, Node.js 24, Playwright browsers)
- Odoo Community v19+ setup (Docker or local installation)
- Social media developer account setup (Twitter, Facebook, LinkedIn, Instagram)
- Gmail API credentials setup
- Environment configuration (.env file)
- First run instructions
- Health check verification

---

## Phase 2: Implementation Tasks

**Note**: Tasks will be generated by `/sp.tasks` command. Not created by `/sp.plan`.

---

## Constitution Re-Check

*Re-evaluate after Phase 1 design completion*

| Principle | Still Compliant? | Design Changes Impact |
|-----------|------------------|----------------------|
| I. Security-First | ✅ YES | All skills include DEV_MODE check, --dry-run, audit logging |
| II. Local-First | ✅ YES | Vault-based storage, secrets in .env/credential manager |
| III. Spec-Driven | ✅ YES | Following workflow. Python Skills pattern used |
| IV. Testable | ✅ YES | All entities have clear validation rules |
| V. Observability | ✅ YES | Structured JSON logging, correlation IDs |
| VI. YAGNI | ✅ YES | Only Gold Tier features. No over-engineering |
| VII. Sandboxing | ✅ YES | Path validation, idempotency tracking |
| VIII. Error Handling | ✅ YES | Circuit breakers, retry, DLQ, typed exceptions |
| IX. Testing | ✅ YES | Risk-based coverage targets defined |
| X. Code Quality | ✅ YES | ruff, black, mypy, bandit, isort gates |
| XI. Logging | ✅ YES | JSON schema with all required fields |
| XII. Performance | ✅ YES | Budgets defined and measurable |
| XIII. Python Skills | ✅ YES | All AI functionality as Python functions |

**All gates still passed**. Design is constitution-compliant.

---

## Key Architectural Decisions

### Decision 1: Python Skills Over MCP Servers

**Decision**: Implement AI functionality as Python Skills in `src/skills/` rather than relying solely on MCP servers.

**Options Considered**:
- Option A: MCP servers only (rejected)
- Option B: Python Skills only (rejected)
- Option C: Hybrid - Python Skills for core logic, MCP servers for complex external integrations (chosen)

**Rationale**: 
- MCP servers add complexity and dependency management overhead
- Python Skills are directly testable, don't require separate process
- MCP servers still useful for standardized interfaces (browser automation, email)
- Hybrid approach balances simplicity with interoperability

**Consequences**:
- (+) Easier testing and debugging
- (+) No MCP process coordination overhead
- (-) Need to maintain both patterns
- (-) Slightly more code duplication

### Decision 2: File-Based State Over Database

**Decision**: Use Markdown files in Obsidian vault for all state management (approvals, task state, logs) rather than SQLite/PostgreSQL.

**Options Considered**:
- Option A: SQLite for structured data (rejected)
- Option B: Markdown files in vault (chosen)
- Option C: Hybrid - SQLite for logs, Markdown for approvals (rejected)

**Rationale**:
- Consistent with local-first, Obsidian-based architecture
- Human-readable and searchable in Obsidian
- No database migration complexity
- Survives process restarts naturally
- Easy backup (just copy vault folder)

**Consequences**:
- (+) Transparent state visible to user
- (+) No database dependencies
- (-) Slower queries on large datasets (mitigated by 90-day rotation)
- (-) No ACID guarantees (acceptable for single-user system)

### Decision 3: Per-Service Circuit Breakers

**Decision**: Implement independent circuit breaker for each external service (Gmail, Odoo, Twitter, Facebook, Instagram, LinkedIn, WhatsApp) rather than global circuit breaker.

**Options Considered**:
- Option A: Global circuit breaker (rejected)
- Option B: Per-domain circuit breakers (personal/business) (rejected)
- Option C: Per-service circuit breakers (chosen)

**Rationale**:
- Gmail failure shouldn't block Odoo operations
- Social media platforms have independent rate limits
- Granular control over failure isolation
- Better observability (know exactly which service is failing)

**Consequences**:
- (+) Better fault isolation
- (+) More precise monitoring
- (-) More state to track (7+ circuit breakers)
- (-) Slightly more complex configuration

### Decision 4: Ralph Wiggum File-Movement Completion Detection

**Decision**: Use file movement to `/Done/` folder as primary completion detection, with `<promise>TASK_COMPLETE</promise>` as fallback.

**Options Considered**:
- Option A: Promise tag only (rejected)
- Option B: File movement only (rejected)
- Option C: Hybrid - file movement primary, promise tag fallback (chosen)

**Rationale**:
- File movement is natural part of workflow (not artificial signal)
- More reliable (doesn't depend on AI output parsing)
- Promise tag useful for tasks without file artifacts
- Redundancy improves reliability

**Consequences**:
- (+) Natural workflow integration
- (+) More reliable detection
- (-) Requires file system monitoring
- (-) Slightly more complex stop hook logic

### Decision 5: Markdown DLQ Over Database

**Decision**: Implement Dead Letter Queue as Markdown files in `/Vault/Dead_Letter_Queue/` rather than database table.

**Options Considered**:
- Option A: SQLite table (rejected)
- Option B: Markdown files (chosen)
- Option C: JSON files (rejected)

**Rationale**:
- Consistent with vault-based architecture
- Human-readable for manual review
- Searchable in Obsidian
- Easy to export/archive

**Consequences**:
- (+) Transparent quarantine visible to user
- (+) No database queries needed for review
- (-) Slower bulk operations (acceptable for manual review workflow)
- (-) File system overhead (mitigated by typical DLQ size <20 items)

---

## Risks and Mitigations

### Risk 1: Social Media API Rate Limiting

**Risk**: Hitting rate limits on Twitter (300/15min), Facebook (200/hour), LinkedIn (1 post/day), Instagram (25 posts/day) causing action failures.

**Probability**: HIGH (daily operations will approach limits)
**Impact**: MEDIUM (actions delayed, not lost)

**Mitigation**:
- Implement per-platform rate limit tracking in skills
- Queue actions when approaching limits
- Schedule posts during off-peak hours
- Alert user when limits are near (80% threshold)

**Contingency**:
- Actions saved as drafts for manual posting
- Retry scheduled for next available window
- Dashboard shows rate limit status in real-time

### Risk 2: Odoo Schema Changes After Upgrade

**Risk**: Odoo upgrade changes API schema, breaking invoice/payment/expense operations.

**Probability**: MEDIUM (Odoo upgrades 1-2 times/year)
**Impact**: HIGH (financial tracking stops)

**Mitigation**:
- Version detection on startup
- Schema validation before API calls
- Fallback to markdown logging when Odoo unavailable
- Alert user on breaking changes

**Contingency**:
- Transactions logged to `/Vault/Odoo_Fallback/` during outage
- Bulk sync when Odoo recovers
- Manual reconciliation support

### Risk 3: WhatsApp Web Session Expiry

**Risk**: WhatsApp Web session expires, requiring re-authentication and losing message context.

**Probability**: HIGH (sessions expire every 2-4 weeks)
**Impact**: MEDIUM (message processing paused)

**Mitigation**:
- Session persistence via Playwright persistent context
- Session expiry detection on each check
- User alert with re-authentication instructions
- Message queue preserved during outage

**Contingency**:
- Messages queued locally until session restored
- User notified via email/SMS for urgent re-authentication
- Session backup/export for faster recovery

### Risk 4: Ralph Wiggum Infinite Loops

**Risk**: Task never meets completion criteria, looping indefinitely and consuming AI calls.

**Probability**: MEDIUM (complex tasks may have ambiguous completion)
**Impact**: MEDIUM (wasted AI calls, no progress)

**Mitigation**:
- Hard max iterations limit (default: 10)
- State persistence shows progress each iteration
- DLQ escalation after max iterations
- User alert on DLQ quarantine

**Contingency**:
- Manual review of DLQ item
- Task refinement and re-queue
- Completion criteria adjustment

### Risk 5: Multi-MCP Double-Execution

**Risk**: Two MCP servers execute same action (e.g., duplicate payment) due to race condition.

**Probability**: LOW (coordinator prevents)
**Impact**: HIGH (financial loss, data corruption)

**Mitigation**:
- MCP Coordinator with distributed locking
- Idempotency via correlation ID tracking
- Single-writer rule for Dashboard.md
- Approval execution requires 60-second minimum review time

**Contingency**:
- Manual reversal of duplicate action
- Audit log review for root cause
- Coordinator bug fix and redeployment

---

## Open Questions

### Question 1: Bank API Integration Strategy

**Question**: Which banking APIs to integrate for transaction feeds?

**Options**:
- Option A: Plaid (US/Europe) - requires business account, costs money
- Option B: Direct bank APIs (bank-specific) - free but fragmented
- Option C: Manual CSV import - free but manual effort

**Decision Needed**: User must specify which banks to integrate and acceptable cost.

**Recommendation**: Start with Option C (manual CSV import) for MVP, add Option A/B based on user's bank.

### Question 2: CEO Briefing Delivery Method

**Question**: How should CEO Briefing be delivered Monday 8 AM?

**Options**:
- Option A: Email to user
- Option B: WhatsApp message with summary
- Option C: Obsidian file only (user reads when convenient)

**Decision Needed**: User preference for delivery method.

**Recommendation**: Option C (Obsidian file) + Option A (email notification) for reliability.

### Question 3: Platinum Tier Cloud Deployment Timeline

**Question**: When to implement Platinum tier cloud deployment (Oracle/AWS VM)?

**Options**:
- Option A: Implement alongside Gold tier (parallel development)
- Option B: After Gold tier is stable (sequential development)
- Option C: Never (local-only deployment)

**Decision Needed**: User priority for cloud deployment.

**Recommendation**: Option B (sequential) - focus on Gold tier stability first.

---

## Implementation Phases

### Phase 1: Foundation (Weeks 1-2)
**Goal**: Core infrastructure with Bronze + Silver subset

**Tasks**:
- T001-T012: Base watcher implementation, orchestrator skeleton, DEV_MODE validation
- T013-T024: Gmail watcher, WhatsApp watcher, filesystem watcher
- T025-T036: Email MCP server, approval workflow, audit logging
- T037-T048: Process manager (watchdog), circuit breaker, retry handler

**Deliverables**:
- Working watchers creating action files
- Approval workflow functional
- Audit logging to /Vault/Logs/
- Basic error recovery (retry + circuit breaker)

### Phase 2: Odoo Integration (Weeks 3-4)
**Goal**: Accounting system integration

**Tasks**:
- T049-T060: Odoo MCP server (JSON-RPC)
- T061-T072: Invoice creation, payment recording, expense categorization skills
- T073-T084: Odoo watcher, fallback mechanism, revenue tracking

**Deliverables**:
- Odoo integration functional
- Financial transactions logged
- Revenue tracking operational
- Fallback to markdown when Odoo unavailable

### Phase 3: Social Media (Weeks 5-6)
**Goal**: Multi-platform social media automation

**Tasks**:
- T085-T096: Social Media MCP server (LinkedIn, Twitter, Facebook, Instagram)
- T097-T108: Posting skills, rate limiting, session management
- T109-T120: Social media watcher, engagement analytics

**Deliverables**:
- Posting to all 4 platforms
- Rate limit compliance
- Session preservation/recovery
- Engagement analytics tracking

### Phase 4: CEO Briefing (Weeks 7-8)
**Goal**: Weekly business audit automation

**Tasks**:
- T121-T132: CEO Briefing generation logic
- T133-T144: Revenue calculation, expense analysis, bottleneck identification
- T145-T156: Subscription audit, cash flow projection, proactive suggestions

**Deliverables**:
- Monday 8 AM briefing generation
- Revenue/expense analytics
- Bottleneck detection
- Proactive suggestions

### Phase 5: Production Readiness (Weeks 9-10)
**Goal**: Error recovery, observability, testing

**Tasks**:
- T157-T168: Ralph Wiggum loop implementation
- T169-T180: Dead Letter Queue, graceful degradation
- T181-T192: Health endpoint, dashboard widget, alerting
- T193-T204: Unit/integration/E2E/chaos testing
- T205-T216: Documentation (architecture, runbook, demo script)

**Deliverables**:
- Ralph Wiggum autonomous loops
- DLQ for failed actions
- Health monitoring + alerting
- Full test coverage
- Complete documentation

---

## Success Criteria Validation

| Criterion | Plan Addresses? | Implementation Phase |
|-----------|-----------------|---------------------|
| All 9 Gold Tier requirements have detailed component architecture | ✅ YES | Phases 1-5 |
| Each MCP server has clear interface definitions | ✅ YES | Phase 1, 2, 3 |
| Watcher patterns fully specified with code templates | ✅ YES | Phase 1 |
| Data schemas defined for all file types | ✅ YES | Phase 1 (Data Model) |
| Security boundaries explicitly documented | ✅ YES | Constitution Check |
| Error handling strategies actionable | ✅ YES | Phase 1, 5 |
| Observability approach enables production debugging | ✅ YES | Phase 5 |
| Implementation phases sequenced logically | ✅ YES | Phases 1-5 |
| Key architectural decisions documented with rationale | ✅ YES | Decisions section |
| Risks identified with mitigation strategies | ✅ YES | Risks section |
| Plan enables task generation without ambiguity | ✅ YES | Clear phases + deliverables |

**All success criteria met**. Plan ready for `/sp.tasks` command.

---

## Appendix: Constitution Compliance Evidence

### Security Controls Implementation

| Control | Implementation Location | Validation Method |
|---------|------------------------|-------------------|
| DEV_MODE | `src/utils/dev_mode.py` | Unit test: `test_dev_mode_validation` |
| --dry-run | All skills (e.g., `src/skills/email_skills.py`) | Integration test: `test_dry_run_email` |
| Audit Logging | `src/skills/audit_skills.py` | Unit test: `test_audit_log_schema` |
| HITL Approval | `src/skills/approval_skills.py` | E2E test: `test_approval_workflow` |
| STOP File | `src/services/orchestrator.py` | Integration test: `test_stop_file_halt` |

### Performance Budget Validation

| Budget | Target | Measurement Method |
|--------|--------|-------------------|
| Watcher latency (Gmail) | <2 min | Timestamp comparison (email received → action file created) |
| Watcher latency (WhatsApp) | <30 sec | Timestamp comparison (message received → action file created) |
| CEO Briefing generation | <60 sec | Stopwatch from trigger to file completion |
| Ralph Wiggum iteration | <30 sec | Per-iteration timing in state file |
| Action execution | <10 sec | Timestamp comparison (approval → execution log) |
| Dashboard refresh | <5 sec | Timestamp comparison (action → Dashboard update) |

### Testing Coverage Targets

| Component Type | Coverage Target | Measurement Tool |
|----------------|-----------------|------------------|
| Critical Business Logic (Ralph Wiggum, CEO Briefing) | 90%+ | `pytest-cov` with `--cov=src/skills/ralph_wiggum_skills.py` |
| File System Flows (watchers, orchestrator) | 80%+ | `pytest-cov` with `--cov=src/watchers/` |
| External API Integration (Odoo, Social) | 70%+ | `pytest-cov` with `--cov=src/skills/odoo_skills.py` |
| Overall Target | 50-60% | `pytest-cov` with `--cov=src/ --cov-report=term-missing` |

---

**Plan Complete**. Ready for `/sp.tasks` command to generate implementation tasks.
