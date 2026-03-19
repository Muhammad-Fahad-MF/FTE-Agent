---
id: 001
title: Constitution Security First Principles
stage: constitution
date: 2026-03-07
surface: agent
model: claude-3-5-sonnet
feature: none
branch: main
user: Imperial_Legend
command: /sp.constitution Create constitution for FTE-Agent with Workflow C+ security-first principles
labels: ["constitution","security","spec-driven","bronze-tier"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
  - .specify/memory/constitution.md
tests:
  - N/A (constitution creation - no tests run)
---

## Prompt

/sp.constitution Create constitution for FTE-Agent with Workflow C+ security-first principles

## Project Context

**Project Name**: FTE-Agent (Full-Time Equivalent Agent)
**Purpose**: Build a safe, local-first autonomous AI employee using Claude Code + Obsidian that proactively manages personal and business affairs 24/7
**Architecture**: Hybrid Workflow C+ (Extensibility + Critical Security)
**Implementation Tier**: Bronze (8-12 hours) with foundation for Silver/Green upgrades

## Required Principles to Document

Establish these non-negotiable principles in the constitution:

### 1. Security-First Automation (CRITICAL)
- **DEV_MODE=true** must be set before ANY code runs - this is the kill switch for all external actions
- **--dry-run flag** must be implemented and functional in ALL action scripts (watchers, orchestrator, skills)
- **Audit logging** captures EVERY action attempt (success, failure, dry-run) to /vault/Logs/ in JSON format
- **Human-in-the-Loop (HITL)** approval required for ALL sensitive actions (payments, external API calls, file moves outside vault)
- **STOP file** mechanism: vault/STOP file immediately halts all orchestrator operations

### 2. Local-First Privacy Architecture
- All data stored locally in Obsidian vault (Markdown files)
- Secrets NEVER stored in vault - use .env file (gitignored) or system credential managers
- .env file must be excluded from version control with .gitignore validation
- Vault sync (for Cloud deployment) excludes: .env, tokens, sessions, banking credentials
- Python 3.13+ required for type safety and modern async features

### 3. Spec-Driven Development (MANDATORY PROCESS)
- Every feature requires: Spec → Plan → Tasks → Implementation → Tests
- No code written without prior spec approval
- All AI functionality implemented as Agent Skills (loadable by Claude Code)
- Ralph Wiggum loop pattern for autonomous multi-step task completion
- Single-writer rule: Only orchestrator writes to Dashboard.md

### 4. Testable Acceptance Criteria
- Every principle must be verifiable via test or inspection
- Security features tested before functionality (dry-run validation, STOP file test)
- Integration tests required for: watcher→action file creation, orchestrator→Claude invocation, approval→execution flow
- Test sequence: dry-run → DEV_MODE=true → (optionally) real mode

### 5. Observability & Debuggability
- Structured JSON logging with log rotation (keep last 7 days)
- All watchers extend BaseWatcher for consistent logging and error handling
- Dashboard.md shows: system status, pending count, recent activity (last 10 actions)
- Error paths logged with full stack traces to /vault/Logs/
- File size limits: skip files >10MB, log warning instead of processing

### 6. Incremental Complexity (YAGNI)
- Start with Bronze tier: one watcher, basic orchestrator, HITL approval
- Silver/Gold features only after Bronze fully tested and documented
- No refactoring of unrelated code during feature implementation
- Smallest viable diff for every change
- Code references required for all modified/inspected files

### 7. Path Validation & Sandboxing
- All file operations validate path starts with vault_path (prevent directory traversal)
- Each skill validates DEV_MODE before execution
- Idempotency: track executed approval files by hash, skip duplicates
- Approval validation: execute only if file was in Pending_Approval/ for >60 seconds (human review time)

## Additional Constraints

**Technology Stack**:
- Python 3.13+ with uv for environment management
- Obsidian v1.10.6+ for vault/GUI
- Claude Code (Pro or via API router) as reasoning engine
- watchdog library for file system monitoring
- MCP servers for external actions (email, browser, payments)

**Directory Structure** (non-negotiable):
```
vault/
  ├── Inbox/           # Drop zone for incoming files
  ├── Needs_Action/    # Action files created by watchers
  ├── Done/            # Completed tasks
  ├── Logs/            # Audit logs (JSON)
  ├── Pending_Approval/# Waiting for human review
  ├── Approved/        # Human-approved actions ready to execute
  ├── Rejected/        # Declined actions
  ├── Dashboard.md     # System status overview
  └── Company_Handbook.md # Rules of engagement
src/
  ├── base_watcher.py      # Abstract base class
  ├── filesystem_watcher.py # Concrete watcher implementation
  ├── orchestrator.py      # Main orchestration logic
  └── audit_logger.py      # Structured logging
```

**Safety Validation Checklist** (must pass before any demo):
- [ ] File dropped in Inbox creates action file (with/without --dry-run)
- [ ] Claude reads action file and creates Plan.md
- [ ] Approval file created in Pending_Approval/
- [ ] Moving to Approved/ triggers action
- [ ] All actions logged to /Logs/
- [ ] DEV_MODE prevents external API calls
- [ ] STOP file halts orchestrator

**Emergency Procedures** (document in constitution):
- Unintended action detected: Create vault/STOP file immediately
- Credential compromise suspected: Rotate credentials, review /Logs/
- Watcher runaway: Kill process, check for error loops in logs

## Governance Requirements

- All PRs must verify constitution compliance (security features present, tests passing)
- Version bump rules:
  - MAJOR: Security principle changes, breaking API changes
  - MINOR: New watcher/skill added, new tier functionality
  - PATCH: Bug fixes, clarifications, non-breaking improvements
- Constitution amendments require: documentation, approval rationale, migration plan if breaking

## Output Expectations

1. Fill ALL placeholder tokens in the constitution template - no [PLACEHOLDER] tokens remaining unless explicitly deferred (mark with TODO)
2. Use declarative language: MUST/SHOULD with clear rationale
3. Keep lines <100 chars for readability but avoid awkward breaks
4. Include Sync Impact Report as HTML comment at top of constitution
5. Flag any files needing manual follow-up
6. Suggest commit message in format: `docs: constitution vX.Y.Z (security-first automation + Bronze tier principles)`

## Success Criteria

After this constitution is created:
- ✅ Clear, testable principles for safe AI employee development
- ✅ Security mechanisms documented as non-negotiable requirements
- ✅ Development process (Spec-Driven) codified
- ✅ Architecture constraints (local-first, path validation) specified
- ✅ Emergency procedures documented
- ✅ Version governance established
- ✅ All placeholders resolved or explicitly deferred with TODOs

## Non-Goals (Explicitly Out of Scope)

- Detailed implementation code (belongs in specs/plans/tasks)
- Specific API contracts (belongs in feature specs)
- MCP server configuration details (belongs in plan docs)
- Silver/Gold tier features beyond mentioning as future extensions

## Response snapshot

Created FTE-Agent Constitution v1.0.0 with 7 core principles:
1. Security-First Automation (CRITICAL) - DEV_MODE, --dry-run, audit logging, HITL, STOP file
2. Local-First Privacy Architecture - Obsidian vault, secret isolation, Python 3.13+
3. Spec-Driven Development (MANDATORY PROCESS) - Spec→Plan→Tasks→Implementation→Tests
4. Testable Acceptance Criteria - Security testing before functionality
5. Observability & Debuggability - JSON logging, BaseWatcher extension, Dashboard.md
6. Incremental Complexity (YAGNI) - Bronze tier first, smallest viable diff
7. Path Validation & Sandboxing - Directory traversal prevention, idempotency

Included technology stack, non-negotiable directory structure, safety validation checklist, emergency procedures, and governance rules with semantic versioning policy.

## Outcome

- ✅ Impact: Constitution v1.0.0 ratified with 7 security-first principles for FTE-Agent Bronze tier implementation
- 🧪 Tests: N/A (constitution creation - validation performed via placeholder token grep)
- 📁 Files: .specify/memory/constitution.md created
- 🔁 Next prompts: /sp.specify to create feature specification for Bronze tier foundation
- 🧠 Reflection: Constitution establishes clear safety guardrails before any implementation begins

## Evaluation notes (flywheel)

- Failure modes observed: None - shell script for PHR creation failed, used agent-native fallback
- Graders run and results (PASS/FAIL): N/A
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): N/A
