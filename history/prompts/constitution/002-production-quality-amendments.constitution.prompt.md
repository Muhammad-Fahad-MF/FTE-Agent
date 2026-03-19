---
id: 002
title: Production Quality Amendments
stage: constitution
date: 2026-03-07
surface: agent
model: claude-3-5-sonnet
feature: none
branch: main
user: Imperial_Legend
command: /sp.constitution Add production quality amendments
labels: ["constitution","production-quality","testing","error-handling","quality-gates"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
  - .specify/memory/constitution.md
tests:
  - N/A (constitution amendment - no tests run)
---

## Prompt

/sp.constitution Add production quality amendments to make constitution production-grade:

### VIII. Production-Grade Error Handling
- Typed exceptions with specific error types (no bare `except Exception:`)
- External API calls MUST implement timeout (30s), retry (3x exponential backoff), circuit breaker (5 failures)
- File operations MUST handle PermissionError, FileNotFoundError, DiskFullError
- Every exception MUST be logged with full stack trace AND either recovered or escalated

### IX. Testing Pyramid & Coverage
- Unit tests: 80%+ coverage required (pytest-cov)
- Integration tests: ALL cross-component flows
- Contract tests: ALL public interfaces
- Chaos tests: failure scenarios (kill mid-operation, disk full, corrupt files)

### X. Code Quality Gates (BLOCKING MERGE)
- Linting: ruff check with 0 errors
- Formatting: black enforced (line length 100)
- Type checking: mypy --strict with 0 errors
- Security scan: bandit with 0 high-severity issues

### XI. Logging Schema & Alerting
- Mandatory fields: timestamp, level, component, action, dry_run, correlation_id
- Alerting: >5 errors/min → immediate notification; >10 warnings/10min → Dashboard update

### XII. Performance Budgets
- Watcher interval: ≤60 seconds
- Action file creation: <2 seconds for files <10MB
- Memory usage: ≤500MB normal operation
- Log rotation: 7 days or 100MB per file

## Response snapshot

Constitution amended from v1.0.0 to v2.0.0 with 5 new production-quality principles:

**VIII. Production-Grade Error Handling**: Typed exceptions required, no bare except clauses. External APIs must implement timeout (30s), retry with exponential backoff (3x), circuit breaker (5 failures). File operations must handle PermissionError, FileNotFoundError, DiskFullError explicitly. Every exception logged with full stack trace and either recovered or escalated.

**IX. Testing Pyramid & Coverage**: 80%+ unit test coverage mandatory (pytest-cov). Integration tests for all cross-component flows. Contract tests for all public interfaces. Chaos tests for failure scenarios (mid-operation kill, disk full, file corruption).

**X. Code Quality Gates (BLOCKING MERGE)**: ruff check (0 errors), black formatting (100 char lines), mypy --strict (0 errors, no Any without justification), bandit security scan (0 high-severity issues), isort for imports.

**XI. Logging Schema & Alerting**: Mandatory JSON fields (timestamp, level, component, action, dry_run, correlation_id, details). Alerting thresholds: >5 errors/min → immediate notification, >10 warnings/10min → Dashboard update. Retention: INFO 7 days, ERROR/CRITICAL 30 days.

**XII. Performance Budgets**: Watcher interval ≤60s, action file creation <2s for <10MB files, orchestrator <5s per approval, memory ≤500MB, log rotation at 7 days or 100MB.

Updated Directory Structure to include tests/ folder with unit/, integration/, contract/, chaos/ subdirectories. Added Testing and Quality Tools to Technology Stack. Updated Safety Validation Checklist with quality gate verification tasks.

## Outcome

- ✅ Impact: Constitution v2.0.0 now enforces production-grade error handling, testing coverage, quality gates, logging schema, and performance budgets
- 🧪 Tests: N/A (constitution amendment - validation via grep for placeholder tokens)
- 📁 Files: .specify/memory/constitution.md amended
- 🔁 Next prompts: /sp.specify to create Bronze tier feature specification with new quality requirements
- 🧠 Reflection: Constitution now guarantees production-level code quality through enforceable quality gates and measurable testing requirements

## Evaluation notes (flywheel)

- Failure modes observed: None - shell script for PHR creation unavailable, used agent-native fallback successfully
- Graders run and results (PASS/FAIL): N/A
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): N/A
