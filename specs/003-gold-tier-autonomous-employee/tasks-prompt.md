# Tasks Generation Prompt: Gold Tier Autonomous Employee (Full Implementation)

**Purpose**: Generate complete implementation tasks for Gold Tier Autonomous Employee

**Spec Reference**: `specs/003-gold-tier-autonomous-employee/spec.md`

**Plan Reference**: `specs/003-gold-tier-autonomous-employee/plan.md`

---

## Context

Generate `tasks.md` with **56 implementation tasks** organized into **5 phases** for the complete Gold Tier Autonomous Employee implementation. This delivers 100% of Gold Tier value as specified in the hackathon requirements.

**Target**: Full Gold Tier implementation - all 9 requirements, all 6 MCP servers, all 5 watchers, CEO Briefing, Ralph Wiggum, error recovery, audit logging, documentation.

**Estimated Time**: 40-56 hours (48-56 tasks at ~45 min average)

---

## Gold Tier Requirements (All Must Be Fully Implemented)

1. **Full Cross-Domain Integration**: Personal (Gmail, WhatsApp, banking) + Business (LinkedIn, Twitter, Facebook, Instagram, Odoo accounting)
2. **Odoo Community Integration**: JSON-RPC APIs (Odoo 19+), invoice/payment/expense/reporting
3. **Social Media Integration**: LinkedIn, Twitter/X, Facebook, Instagram with posting, analytics, rate limiting
4. **Multiple MCP Servers**: Email, WhatsApp, Social Media, Odoo, Browser, Filesystem (6 total)
5. **Weekly CEO Briefing**: Monday 8 AM with revenue, expenses, tasks, bottlenecks, subscriptions, cash flow, suggestions
6. **Error Recovery**: Retry (exponential backoff), circuit breakers (5 failures), DLQ, graceful degradation
7. **Comprehensive Audit Logging**: JSON format, 90-day retention, daily rotation, search utility
8. **Ralph Wiggum Loop**: Autonomous multi-step tasks, state persistence, completion detection, max 10 iterations
9. **Documentation**: Architecture, API reference, setup guide, runbook, security disclosure, demo script

---

## Task Requirements

### General Requirements for All Tasks

1. **Task ID Format**: `T001` to `T056` (sequential across all phases)
2. **Priority**: P0 (critical path), P1 (important), P2 (optimization)
3. **Estimated Time**: In minutes (15, 20, 30, 45, 60, 90)
4. **Status**: `pending` (all tasks start as pending)
5. **Acceptance Criteria**: Each task must have 3-5 testable acceptance criteria
6. **Dependencies**: List task IDs that must complete before this task

### Task Template Structure

Each task must follow this exact structure:

```markdown
### T### - Task Title (Priority: P0/P1/P2, ~X min)

**Phase**: Phase N

**Description**: 
[2-3 sentences describing what to implement]

**Acceptance Criteria**:
- [ ] Criterion 1 (testable)
- [ ] Criterion 2 (testable)
- [ ] Criterion 3 (testable)
- [ ] Criterion 4 (testable if complex)

**Dependencies**: T###, T###

**Implementation Notes**:
- File: `src/path/to/file.py`
- Key functions: `function_name()`
- Tests: `tests/unit/test_file.py::test_function`
```

---

## Phase Structure (5 Phases, 56 Tasks Total)

### Phase 1: Foundation (14 tasks, T001-T014, ~8 hours)

**Goal**: Complete foundation with all watchers, approval workflow, error handling, audit logging

**Deliverables**:
- BaseWatcher abstract class
- GmailWatcher (2-min interval)
- WhatsAppWatcher (30-sec interval)
- FileSystemWatcher (60-sec interval)
- DEV_MODE validation
- AuditLogger (JSON, 90-day retention)
- Approval workflow (Pending_Approval → Approved/Rejected)
- Orchestrator skeleton
- Retry handler (exponential backoff, max 3 retries)
- Circuit breaker (5 failures → open, 300s reset)
- Dashboard.md with system status
- Process manager (watcher restart <10s)
- Unit tests for foundation components

**Tasks**:

**T001**: Create BaseWatcher abstract class
- Abstract methods: check_for_updates(), create_action_file()
- Constructor: vault_path, check_interval, logger
- Run loop: continuous with exception handling
- Logging: structured JSON via AuditLogger
- File: `src/watchers/base_watcher.py`

**T002**: Implement GmailWatcher
- 2-minute check interval
- Gmail API integration (google-api-python-client)
- Action file creation in /Needs_Action/ with YAML frontmatter
- Processed ID tracking (prevent duplicates)
- Error handling: API errors, rate limits, auth expiry
- File: `src/watchers/gmail_watcher.py`

**T003**: Implement WhatsAppWatcher
- 30-second check interval
- Playwright persistent context for session management
- Keyword filtering (urgent, asap, invoice, payment, help)
- Action file creation in /Needs_Action/
- Session expiry detection and user alert
- File: `src/watchers/whatsapp_watcher.py`

**T004**: Implement FileSystemWatcher
- 60-second check interval
- Watchdog-based file monitoring
- File copy to /Needs_Action/ with metadata
- Support for dropped files, CSV imports
- File: `src/watchers/filesystem_watcher.py`

**T005**: Create DEV_MODE validation utility
- Read from environment variable
- Validate before any external action
- Clear error message when not set
- Integration with all skills
- File: `src/utils/dev_mode.py`

**T006**: Implement AuditLogger
- JSON format with complete schema (timestamp, level, component, action, dry_run, correlation_id, domain, target, parameters, approval_status, approved_by, result, error, details)
- Write to /Vault/Logs/YYYY-MM-DD.json
- Daily rotation at midnight
- 90-day retention (delete logs older than 90 days)
- File: `src/utils/logger.py`

**T007**: Create approval request template and structure
- YAML frontmatter template (type, action, action_details, created, expires, status, risk_level, approved_by, approved_at)
- File naming: APPROVAL_<action>_<timestamp>.md
- Location: /Vault/Pending_Approval/
- 24-hour expiry logic
- File: `src/templates/approval_request_template.md`

**T008**: Implement request_approval skill
- Create approval request file with all metadata
- Validate required fields
- Set expiry (24 hours from creation)
- Log action to audit
- File: `src/skills/approval_skills.py`

**T009**: Implement check_approval skill
- Check approval file status (approved|rejected|pending|expired)
- Validate approval timestamp
- Return approval decision with metadata
- File: `src/skills/approval_skills.py`

**T010**: Implement expire_approvals skill
- Scan Pending_Approval for expired files (>24 hours)
- Mark as expired, move to archive
- Alert user about expired approvals
- File: `src/skills/approval_skills.py`

**T011**: Create orchestrator skeleton
- Main loop (watch /Needs_Action/, /Approved/)
- Trigger skills based on action file type
- Log all operations with correlation_id
- Graceful shutdown on STOP file
- File: `src/services/orchestrator.py`

**T012**: Implement retry handler
- Exponential backoff: 1s, 2s, 4s
- Max 3 retries
- Typed exception handling (specific error types only)
- Log retry attempts
- File: `src/services/retry_handler.py`

**T013**: Implement circuit breaker
- State machine: closed → open → half_open
- Trip after 5 consecutive failures
- 300-second reset timeout
- Per-service tracking (gmail, whatsapp, odoo, linkedin, twitter, facebook, instagram)
- File: `src/services/circuit_breaker.py`

**T014**: Create Dashboard.md with system status
- System status (running/stopped/degraded)
- Pending approvals count
- Recent actions (last 10)
- Health indicators (watchers, MCPs, storage, circuit breakers)
- Auto-refresh every 5 seconds
- File: `vault/Dashboard.md` (template + update logic)

---

### Phase 2: MCP Servers Core (16 tasks, T015-T030, ~12 hours)

**Goal**: All 6 MCP servers functional with complete API contracts

**Deliverables**:
- EmailMCP (Gmail API: send, draft, search)
- WhatsAppMCP (Playwright: send, receive, session)
- SocialMCP (LinkedIn, Twitter, Facebook, Instagram handlers)
- OdooMCP (JSON-RPC: invoice, payment, expense, reporting)
- BrowserMCP (Playwright: payment portals)
- FilesystemMCP (extended vault operations)

**Tasks**:

**T015**: Create EmailMCP server skeleton
- MCP server structure (server.py, handlers.py)
- Gmail API authentication (OAuth2)
- Configuration: credentials, scopes
- File: `src/mcp_servers/email_mcp/server.py`

**T016**: Implement send_email handler
- SMTP/Gmail API integration
- Parameters: to, subject, body, attachments
- DEV_MODE validation, dry_run support
- Audit logging
- File: `src/mcp_servers/email_mcp/handlers.py`

**T017**: Implement draft_email handler
- Create draft in Gmail
- Return draft_id for later send
- File: `src/mcp_servers/email_mcp/handlers.py`

**T018**: Implement search_emails handler
- Gmail search queries
- Return matching messages with snippets
- File: `src/mcp_servers/email_mcp/handlers.py`

**T019**: Create WhatsAppMCP server skeleton
- Playwright-based browser automation
- Persistent context for session management
- Session storage and recovery
- File: `src/mcp_servers/whatsapp_mcp/server.py`

**T020**: Implement send_whatsapp handler
- Send message to contact/group
- Session validation before send
- Error handling for session expiry
- File: `src/mcp_servers/whatsapp_mcp/handlers.py`

**T021**: Create SocialMCP server skeleton
- Unified interface for all platforms
- Platform handlers: LinkedIn, Twitter, Facebook, Instagram
- Common methods: post(), get_analytics(), get_insights()
- File: `src/mcp_servers/social_mcp/server.py`

**T022**: Implement LinkedInHandler
- OAuth2 authentication flow
- Post creation (text + optional image)
- Rate limit: 1 post/day enforcement
- Engagement metrics: likes, comments, shares
- File: `src/mcp_servers/social_mcp/linkedin_handler.py`

**T023**: Implement TwitterHandler
- OAuth2 authentication (tweepy)
- Post creation (text 280 chars, optional media)
- Rate limit: 300 posts/15min enforcement
- Engagement metrics: likes, retweets, replies
- File: `src/mcp_servers/social_mcp/twitter_handler.py`

**T024**: Implement FacebookHandler
- Facebook Graph API v18+ integration
- Page post creation
- Rate limit: 200 calls/hour
- Page insights: reach, engagement
- File: `src/mcp_servers/social_mcp/facebook_handler.py`

**T025**: Implement InstagramHandler
- Instagram Graph API integration
- Media post creation (image + caption)
- Rate limit: 25 posts/day
- Engagement metrics: likes, comments, saves
- File: `src/mcp_servers/social_mcp/instagram_handler.py`

**T026**: Implement rate limiting service
- Per-platform tracking (requests remaining, reset time)
- Block requests when limit exceeded
- Schedule retry for next window
- Alert at 80% threshold
- File: `src/services/rate_limiter.py`

**T027**: Create OdooMCP server skeleton
- JSON-RPC 2.0 client setup
- Authentication (db, username, password/api_key)
- Endpoint: /jsonrpc
- Methods: execute_kw (generic RPC call)
- File: `src/mcp_servers/odoo_mcp/server.py`

**T028**: Implement create_invoice skill
- Parameters: partner_id, invoice_date, due_date, lines (description, quantity, price)
- Odoo model: account.move
- Validation: required fields
- Returns: invoice_id
- File: `src/skills/odoo_skills.py`

**T029**: Implement record_payment skill
- Parameters: invoice_id, amount, payment_date, payment_method
- Odoo model: account.payment
- Reconciliation: link to invoice
- File: `src/skills/odoo_skills.py`

**T030**: Implement categorize_expense skill
- Parameters: amount, description, date, account_id
- Odoo model: account.analytic.account
- Category mapping (rules-based)
- File: `src/skills/odoo_skills.py`

---

### Phase 3: CEO Briefing + Ralph Wiggum (14 tasks, T031-T044, ~10 hours)

**Goal**: Monday 8 AM CEO Briefing + autonomous multi-step task completion

**Deliverables**:
- CEOBriefing data model (all 7 components)
- Revenue calculation from Odoo
- Expense analysis with categorization
- Task completion counting
- Bottleneck identification
- Subscription audit
- Cash flow projection
- Proactive suggestions
- Monday 8 AM scheduler
- Ralph Wiggum state persistence
- Completion detection (file movement + promise tag)
- Max iterations handling

**Tasks**:

**T031**: Create CEOBriefing data model
- Fields: generated, period_start, period_end, revenue, expenses, tasks_completed, bottlenecks, subscription_audit, cash_flow_projection, proactive_suggestions
- YAML frontmatter for markdown output
- File: `src/models/ceo_briefing.py`

**T032**: Implement calculate_revenue skill
- Query Odoo for paid invoices (period)
- Sum by source (partner/category)
- Calculate trend vs previous period
- Returns: {total, by_source, trend_percentage}
- File: `src/skills/briefing_skills.py`

**T033**: Implement analyze_expenses skill
- Query Odoo for expenses (period)
- Categorize expenses
- Calculate trend vs previous period
- Returns: {total, by_category, trend_percentage}
- File: `src/skills/briefing_skills.py`

**T034**: Implement count_completed_tasks skill
- Scan /Done/ folder for period
- Count files by type (email, invoice, post)
- Returns: {total, by_type}
- File: `src/skills/briefing_skills.py`

**T035**: Implement identify_bottlenecks skill
- Scan Plan.md files for delayed tasks
- Compare expected vs actual completion
- Threshold: >2 days delay
- Returns: [{task, expected, actual, delay}]
- File: `src/skills/briefing_skills.py`

**T036**: Implement audit_subscriptions skill
- Pattern matching on transactions (Netflix, Spotify, Adobe, etc.)
- Check last login/usage (if available)
- Flag unused >30 days
- Returns: [{name, cost, last_used, recommendation}]
- File: `src/skills/briefing_skills.py`

**T037**: Implement project_cash_flow skill
- 30/60/90 day projections
- Based on historical revenue/expenses
- Returns: {30_day, 60_day, 90_day}
- File: `src/skills/briefing_skills.py`

**T038**: Implement generate_suggestions skill
- Rule-based recommendations
- Rules: unused subscriptions, low revenue trend, high expense trend
- Returns: [{suggestion, priority, action_file}]
- File: `src/skills/briefing_skills.py`

**T039**: Implement generate_ceo_briefing orchestrator
- Call all briefing skills in sequence
- Generate markdown output
- Write to /Vault/Briefings/YYYY-MM-DD_Monday_Briefing.md
- File: `src/skills/briefing_skills.py`

**T040**: Create Monday 8 AM scheduler
- Windows Task Scheduler setup script
- Trigger: Every Monday at 8:00 AM
- Action: Run generate_ceo_briefing skill
- Output: /Vault/Briefings/YYYY-MM-DD_Monday_Briefing.md
- File: `scripts/schedule-ceo-briefing.bat`

**T041**: Create TaskState model for Ralph Wiggum
- Fields: task_id, objective, created, iteration, max_iterations, status, state_data, completion_criteria, completed_criteria, error, completed_at
- YAML frontmatter for markdown state files
- File: `src/models/task_state.py`

**T042**: Implement state_persistence skill
- Create state file: /In_Progress/<agent>/<task-id>.md
- Update state each iteration
- Load state on restart
- File: `src/skills/ralph_wiggum_skills.py`

**T043**: Implement completion_detection skill
- Primary: Detect file movement to /Done/
- Fallback: Parse <promise>TASK_COMPLETE</promise> tag
- Alternative: Check plan checklist 100%
- Signal completion to orchestrator
- File: `src/skills/ralph_wiggum_skills.py`

**T044**: Implement max_iterations_check skill
- Track iteration count (default max: 10)
- On max reached: move to DLQ with status report
- Alert user for manual review
- File: `src/skills/ralph_wiggum_skills.py`

---

### Phase 4: Production Readiness (8 tasks, T045-T052, ~8 hours)

**Goal**: Error handling, observability, alerting, DLQ

**Deliverables**:
- Dead Letter Queue for failed actions
- DLQ manual review workflow
- Health endpoint (/health status)
- Alerting logic (circuit breaker, DLQ size, watcher restart)
- Graceful degradation (fallback mechanisms)
- Log query utility

**Tasks**:

**T045**: Implement Dead Letter Queue
- DLQItem model (id, action_type, original_request, error_details, retry_count, quarantine_timestamp, status, resolved_by, resolved_at, resolution_notes)
- Quarantine failed actions to /Vault/Dead_Letter_Queue/
- Markdown format with YAML frontmatter
- File: `src/services/dead_letter_queue.py`

**T046**: Create DLQ manual review workflow
- List DLQ items (query by status)
- Resolve item (mark as resolved/discarded)
- Add resolution notes
- File: `src/skills/dlq_skills.py`

**T047**: Implement health_endpoint
- Endpoint: GET /health
- Status: ok/degraded/error
- Components: watchers (running/stopped), MCPs (connected/disconnected), storage (ok/full), circuit_breakers (closed/open)
- File: `src/services/health_endpoint.py`

**T048**: Create alerting logic
- Alert conditions: circuit_breaker_open, dlq_size > 10, watcher_restart > 3/hour, approval_queue > 20
- Alert method: Create file in /Needs_Action/, update Dashboard.md, optional email notification
- File: `src/services/alerting.py`

**T049**: Implement Odoo fallback mechanism
- Detect Odoo unavailability (connection error, timeout)
- Log transaction to /Vault/Odoo_Fallback/YYYY-MM-DD.md
- Queue for later sync
- Alert user when fallback active
- File: `src/services/odoo_fallback.py`

**T050**: Implement social media fallback mechanism
- Detect API unavailability
- Save draft posts to /Vault/Drafts/
- Schedule retry for next available window
- File: `src/services/social_fallback.py`

**T051**: Implement query_logs skill
- Query audit logs by date, action type, result
- Return filtered results
- Export to CSV option
- File: `src/skills/audit_skills.py`

**T052**: Implement process_manager (watchdog for watchers)
- Monitor watcher processes
- Auto-restart within 10 seconds of crash
- Track restart count (alert if >3/hour)
- File: `src/services/process_manager.py`

---

### Phase 5: Documentation + Testing (4 tasks, T053-T056, ~6 hours)

**Goal**: Complete documentation and integration tests

**Deliverables**:
- Architecture documentation
- API reference (all MCP endpoints)
- Setup guide (installation, configuration)
- Operational runbook
- Security disclosure
- Integration tests for all workflows

**Tasks**:

**T053**: Write architecture documentation
- System overview diagram (Perception → Reasoning → Action)
- Component descriptions (watchers, skills, MCPs, services)
- Data flow diagrams
- Ralph Wiggum loop explanation
- CEO Briefing generation flow
- File: `docs/architecture/gold-tier-architecture.md`

**T054**: Write setup guide and API reference
- Prerequisites (Python 3.13, Node.js 24, Odoo v19+, Playwright browsers)
- Installation steps (all dependencies)
- Configuration (.env template, Company_Handbook.md)
- MCP server API reference (all endpoints)
- First run instructions
- Health check verification
- File: `docs/quickstart.md` + `docs/api-reference.md`

**T055**: Write operational runbook and security disclosure
- Common operations (start watchers, check health, review DLQ, approve actions)
- Troubleshooting (watcher crashed, Odoo unavailable, session expired, circuit breaker open)
- Maintenance (log rotation, backup vault, update credentials)
- Security disclosure (credential handling, HITL boundaries, dry_run mode)
- File: `docs/runbook.md` + `docs/security.md`

**T056**: Write integration tests for all workflows
- Gmail watcher → approval → email send workflow
- Odoo invoice → approval → creation workflow
- Social post → approval → posting workflow
- CEO Briefing generation workflow
- Ralph Wiggum multi-step task workflow
- File: `tests/integration/test_all_workflows.py`

---

## Output Format

Generate `tasks.md` with this exact structure:

```markdown
# Implementation Tasks: Gold Tier Autonomous Employee

**Branch**: `003-gold-tier-autonomous-employee`
**Created**: 2026-04-02
**Spec**: [spec.md](spec.md)
**Plan**: [plan.md](plan.md)
**Total Tasks**: 56
**Estimated Time**: 40-56 hours

## Phase 1: Foundation (T001-T014, ~8 hours)

**Goal**: Complete foundation with all watchers, approval workflow, error handling, audit logging

### T001 - Create BaseWatcher Abstract Class (Priority: P0, ~30 min)
...

### T002 - Implement GmailWatcher (Priority: P0, ~45 min)
...

[Continue for all 56 tasks]

## Phase Summary

| Phase | Tasks | P0 Count | P1 Count | P2 Count | Estimated Time |
|-------|-------|----------|----------|----------|----------------|
| Phase 1: Foundation | 14 | 12 | 2 | 0 | ~8 hours |
| Phase 2: MCP Servers | 16 | 12 | 4 | 0 | ~12 hours |
| Phase 3: CEO Briefing + Ralph Wiggum | 14 | 10 | 4 | 0 | ~10 hours |
| Phase 4: Production Readiness | 8 | 6 | 2 | 0 | ~8 hours |
| Phase 5: Documentation + Testing | 4 | 2 | 2 | 0 | ~6 hours |
| **Total** | **56** | **42** | **14** | **0** | **~44 hours** |

## Task Status Summary

| Status | Count | Percentage |
|--------|-------|------------|
| pending | 56 | 100% |
| in_progress | 0 | 0% |
| completed | 0 | 0% |
| blocked | 0 | 0% |

## Critical Path (P0 Tasks Only)

T001 → T002 → T003 → T004 → T005 → T006 → T008 → T009 → T011 → T012 → T013 → T015 → T016 → T019 → T020 → T021 → T022 → T023 → T024 → T025 → T027 → T028 → T029 → T030 → T031 → T032 → T033 → T039 → T040 → T041 → T042 → T043 → T044 → T045 → T047 → T048 → T053 → T054 → T055 → T056

**Total P0 Tasks**: 42
**Critical Path Time**: ~35 hours

## Gold Tier Success Criteria

Implementation is complete when ALL of the following are verified:

### Cross-Domain Integration
- [ ] GmailWatcher detects new emails within 2 minutes
- [ ] WhatsAppWatcher detects urgent messages within 30 seconds
- [ ] FileSystemWatcher processes dropped files within 60 seconds
- [ ] All action files created in /Needs_Action/ with proper YAML frontmatter

### Odoo Accounting Integration
- [ ] create_invoice skill creates invoices in Odoo via JSON-RPC
- [ ] record_payment skill records payments and reconciles with invoices
- [ ] categorize_expense skill categorizes expenses correctly
- [ ] Fallback to markdown logging when Odoo unavailable

### Social Media Integration
- [ ] LinkedIn posts created with 1 post/day rate limit
- [ ] Twitter posts created with 300 posts/15min rate limit
- [ ] Facebook posts created with 200 calls/hour rate limit
- [ ] Instagram posts created with 25 posts/day rate limit
- [ ] Session preservation and recovery for all platforms
- [ ] Engagement analytics retrieved for all platforms

### CEO Briefing
- [ ] Briefing generated every Monday at 8:00 AM
- [ ] Revenue calculated from Odoo data
- [ ] Expenses analyzed and categorized
- [ ] Task completion counted from /Done/ folder
- [ ] Bottlenecks identified from Plan.md analysis
- [ ] Subscription audit flags unused services
- [ ] Cash flow projection for 30/60/90 days
- [ ] Proactive suggestions generated

### Ralph Wiggum Loop
- [ ] State persistence in /In_Progress/<agent>/<task-id>.md
- [ ] Completion detection via file movement to /Done/
- [ ] Fallback completion via <promise>TASK_COMPLETE</promise> tag
- [ ] Max iterations (10) enforced with DLQ escalation

### Error Recovery
- [ ] Retry with exponential backoff (1s, 2s, 4s; max 3 retries)
- [ ] Circuit breakers trip after 5 consecutive failures
- [ ] Dead Letter Queue quarantines failed actions
- [ ] Graceful degradation when services unavailable
- [ ] Watchers auto-restart within 10 seconds of crash

### Audit Logging
- [ ] All actions logged in JSON format
- [ ] 90-day retention enforced
- [ ] Daily log rotation at midnight
- [ ] Query utility filters by date, action, result

### Documentation
- [ ] Architecture documentation complete
- [ ] API reference for all MCP servers
- [ ] Setup guide with installation steps
- [ ] Operational runbook with troubleshooting
- [ ] Security disclosure with HITL boundaries

### Testing
- [ ] All integration tests pass
- [ ] End-to-end workflows verified
- [ ] Error scenarios tested
```

---

## Additional Requirements

### 1. Dependency Graph

Ensure correct dependencies:
- Phase 1 tasks: No dependencies or depend on earlier Phase 1 tasks
- Phase 2 tasks: Depend on Phase 1 completion (T001-T014)
- Phase 3 tasks: Depend on Phase 1 + relevant Phase 2 tasks
- Phase 4 tasks: Depend on all previous phases
- Phase 5 tasks: Depend on implementation tasks (T001-T052)

### 2. Test Coverage

Include testing tasks:
- T056: Integration tests for all workflows
- Additional unit tests within each implementation task

### 3. Documentation Tasks

Include all documentation:
- T053: Architecture documentation
- T054: Setup guide + API reference
- T055: Runbook + security disclosure

### 4. Full Gold Tier Coverage

Ensure all 9 Gold Tier requirements are covered:
1. Cross-domain integration (T001-T004, T021-T026)
2. Odoo integration (T027-T030, T049)
3. Social media (T021-T026, T050)
4. MCP servers (T015-T030)
5. CEO Briefing (T031-T040)
6. Error recovery (T012-T013, T045-T052)
7. Audit logging (T006, T051)
8. Ralph Wiggum (T041-T044)
9. Documentation (T053-T055)

---

## Constraints

- **Total Tasks**: Exactly 56 (no more, no less)
- **Total Time**: 40-56 hours estimated
- **P0/P1/P2 Ratio**: ~75% P0, ~25% P1, 0% P2 (all tasks are essential)
- **Phases**: Exactly 5 phases
- **Format**: Follow task template exactly
- **Full Gold Tier**: All 9 requirements fully implemented (no cuts, no MVP)

---

## Success Criteria for tasks.md

The generated tasks.md is complete when:
- [ ] All 56 tasks defined with complete template structure
- [ ] Each task has 3-5 testable acceptance criteria
- [ ] Dependencies are correctly specified
- [ ] Estimated times are realistic (15-90 min per task)
- [ ] All files referenced exist or will be created
- [ ] Phase goals are clear and achievable
- [ ] Critical path is identifiable (P0 tasks)
- [ ] Total estimated time is 40-56 hours
- [ ] All 9 Gold Tier requirements are covered
- [ ] All 6 MCP servers are implemented
- [ ] All 5 watchers are implemented
- [ ] CEO Briefing has all 7 components
- [ ] Ralph Wiggum has state persistence + completion detection + max iterations
- [ ] Error recovery has retry + circuit breaker + DLQ + graceful degradation
- [ ] Audit logging has 90-day retention

---

**Your Task**: Generate `specs/003-gold-tier-autonomous-employee/tasks.md` following this prompt exactly. Deliver 100% Gold Tier implementation - all 9 requirements, all 6 MCP servers, all 5 watchers, complete CEO Briefing, full Ralph Wiggum loop, production-grade error handling, comprehensive audit logging, and complete documentation. No cuts, no MVP, no artificial limitations.
