<!--
SYNC IMPACT REPORT
==================
Version change: 2.0.0 → 3.0.0 (Major: Qwen Code CLI replaces Claude Code, Python Skills replace MCP)
Modified principles:
  - III. Spec-Driven Development (Claude Code → Qwen Code CLI, Agent Skills → Python Skills)
  - IV. Testable Acceptance Criteria (orchestrator→Claude → orchestrator→Qwen)
  - IX. Testing Pyramid & Coverage (Agent Skills → Python Skills, MCP contracts removed)
Added sections:
  - XIII. AI Reasoning Engine & Python Skills Pattern
Removed sections: None
Templates requiring updates:
  - ✅ .specify/templates/plan-template.md (Constitution Check aligns)
  - ✅ .specify/templates/spec-template.md (Python Skills pattern compatible)
  - ✅ .specify/templates/tasks-template.md (Quality gate tasks mandatory)
  - ⚠️ .specify/templates/commands/*.md (May need Qwen Code CLI command updates)
Follow-up TODOs:
  - TODO(CREATE_README): Create README.md with Qwen Code CLI setup instructions
  - TODO(CREATE_SAFETY_MD): Create SAFETY.md documenting all safety features and limitations
  - TODO(CREATE_QUALITY_MD): Create QUALITY.md with detailed quality gate configuration examples
  - TODO(CREATE_SKILLS_MD): Create src/skills.py with Python Skills implementation
-->

# FTE-Agent Constitution

## Core Principles

### I. Security-First Automation (CRITICAL)

DEV_MODE=true MUST be set before ANY code runs—this is the kill switch for all external actions. The --dry-run flag MUST be implemented and functional in ALL action scripts including watchers, orchestrator, and skills. Audit logging MUST capture EVERY action attempt (success, failure, dry-run) to /vault/Logs/ in JSON format. Human-in-the-Loop (HITL) approval is REQUIRED for ALL sensitive actions including payments, external API calls, and file moves outside the vault. The STOP file mechanism MUST be implemented: creating vault/STOP immediately halts all orchestrator operations.

**Rationale**: Autonomous systems handling business affairs require non-bypassable safety mechanisms. These five security controls (DEV_MODE, --dry-run, audit logging, HITL, STOP file) form the minimum viable safety foundation.

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

### XIII. AI Reasoning Engine & Python Skills Pattern

**AI Reasoning Engine**: Qwen Code CLI (free tier: 1,000 OAuth calls/day) MUST be used for all AI-assisted development. MCP servers are NOT supported—Python Skills pattern MUST be used instead.

**Python Skills Pattern** (MANDATORY):
- All AI functionality MUST be implemented as Python functions in `src/skills.py`
- Skills MUST be callable via: (1) direct Python import, (2) Qwen Code CLI subprocess, (3) CLI wrapper scripts
- Skills MUST validate DEV_MODE before execution
- Skills MUST implement audit logging for all actions
- Skills MUST handle errors with typed exceptions and graceful degradation

**Bronze Tier**: Python Skills for file operations only (no external APIs required)
**Silver Tier**: Python Skills with direct integrations (smtplib for email, requests for HTTP, playwright for web automation)
**Gold Tier**: Python Skills with multiple external services (Odoo JSON-RPC, social media APIs, banking APIs)

**Rationale**: Python Skills provide MCP-like functionality without MCP protocol dependency. This enables free development with Qwen Code CLI while maintaining extensibility for Silver/Gold tiers. Direct Python integrations are easier to test, debug, and deploy.

## Technology Stack

- **Python**: 3.13+ with uv for environment management
- **Obsidian**: v1.10.6+ for vault/GUI
- **AI Reasoning Engine**: Qwen Code CLI (free OAuth tier - 1,000 calls/day)
- **File Monitoring**: watchdog library for file system monitoring
- **External Actions**: Python Skills (src/skills.py) with direct integrations:
  - Email: smtplib, imaplib (Bronze/Silver)
  - HTTP APIs: requests, httpx (Silver/Gold)
  - Web Automation: playwright (Silver/Gold)
  - Accounting: Odoo JSON-RPC (Gold)
  - Social Media: platform-specific APIs (Gold)
- **Testing**: pytest, pytest-cov, pytest-mock
- **Quality Tools**: ruff (linting), black (formatting), mypy (type checking), bandit (security), isort (imports)

## Directory Structure (Non-Negotiable)

```
vault/
  ├── Inbox/              # Drop zone for incoming files
  ├── Needs_Action/       # Action files created by watchers
  ├── Done/               # Completed tasks
  ├── Logs/               # Audit logs (JSON)
  ├── Pending_Approval/   # Waiting for human review
  ├── Approved/           # Human-approved actions ready to execute
  ├── Rejected/           # Declined actions
  ├── Dashboard.md        # System status overview
  └── Company_Handbook.md # Rules of engagement

src/
  ├── base_watcher.py       # Abstract base class
  ├── filesystem_watcher.py # Concrete watcher implementation
  ├── orchestrator.py       # Main orchestration logic
  ├── audit_logger.py       # Structured logging
  └── skills.py             # Python Skills (replaces MCP servers)

scripts/
  ├── ralph-loop.bat        # Autonomous multi-step task loop for Qwen Code CLI
  └── setup-vault.ps1       # Vault initialization script

tests/
  ├── unit/                 # Unit tests (80%+ coverage)
  ├── integration/          # Integration tests
  ├── contract/             # Contract tests
  └── chaos/                # Chaos/failure scenario tests
```

## Safety Validation Checklist

The following MUST pass before any demo:

- [ ] File dropped in Inbox creates action file (with/without --dry-run)
- [ ] Qwen Code CLI reads action file and creates Plan.md
- [ ] Approval file created in Pending_Approval/
- [ ] Moving to Approved/ triggers action
- [ ] All actions logged to /Logs/
- [ ] DEV_MODE prevents external API calls
- [ ] STOP file halts orchestrator
- [ ] pytest --cov=src shows 80%+ coverage
- [ ] ruff check src/ passes with 0 errors
- [ ] mypy --strict src/ passes with 0 errors
- [ ] bandit -r src/ shows 0 high-severity issues
- [ ] Qwen Code CLI installed and authenticated (qwen --version, /auth completed)

## Emergency Procedures

- **Unintended action detected**: Create vault/STOP file immediately
- **Credential compromise suspected**: Rotate credentials, review /Logs/
- **Watcher runaway**: Kill process, check for error loops in logs
- **Performance degradation**: Check memory usage, review log rotation, verify no file handle leaks
- **Qwen API rate limit hit**: Batch requests, implement caching, or wait for daily reset (midnight UTC)

## Development Workflow & Quality Gates

All pull requests MUST verify constitution compliance (security features present, tests passing, quality gates passing). Complexity MUST be justified with rationale and rejected alternatives. Version bump rules MUST follow semantic versioning:

- **MAJOR**: Security principle changes, breaking API changes, quality gate additions, AI engine changes
- **MINOR**: New watcher/skill added, new tier functionality, performance budget changes
- **PATCH**: Bug fixes, clarifications, non-breaking improvements

Constitution amendments require: documentation, approval rationale, and migration plan if breaking.

## Governance

This constitution supersedes all other development practices. Amendments require:

1. Documentation of the proposed change
2. Approval rationale explaining why the change is needed
3. Migration plan if the change is breaking

All PRs and reviews MUST verify compliance with this constitution. Use `.specify/memory/constitution.md` as the single source of truth for runtime development guidance.

**Version**: 3.0.0 | **Ratified**: 2026-03-07 | **Last Amended**: 2026-03-07
