---
id: "057"
title: "Gold Tier 48-Task MVGT Prompt"
stage: "tasks"
date_iso: "2026-04-02"
surface: "agent"
model: "qwen3-coder-plus"
feature: "004-gold-tier-autonomous-employee"
branch: "004-gold-tier-autonomous-employee"
user: "Imperial_Legend"
command: "Write prompt for /sp.tasks with 48 detailed tasks"
labels: ["tasks-generation", "gold-tier", "mvgt", "right-sized-implementation"]
links:
  spec: "specs/003-gold-tier-autonomous-employee/spec.md"
  plan: "specs/004-gold-tier-autonomous-employee/plan.md"
  strategy: "specs/004-gold-tier-autonomous-employee/tasks-strategy.md"
  ticket: "null"
  adr: "null"
  pr: "null"
files_yaml: |
  - specs/004-gold-tier-autonomous-employee/tasks-prompt.md
tests_yaml: |
  - Tasks prompt validation (48 tasks, 4 phases, 15-20 hours)
prompt_text: |
  Now write a prompt for /sp.tasks with 48 detailed tasks for Minimum Viable Gold Tier (MVGT).

  Create comprehensive tasks generation prompt incorporating:
  - 48 tasks across 4 phases (Foundation, Odoo+Social, CEO Briefing+Ralph Wiggum, Production Readiness)
  - Task template structure (ID, priority, time, description, acceptance criteria, dependencies, implementation notes)
  - Phase goals and deliverables
  - Detailed task descriptions for all 48 tasks
  - Output format specification for tasks.md
  - Success criteria for MVGT completion

  MVGT Strategy:
  - Phase 1: Foundation (12 tasks, ~4.5 hours) - Watchers, approval, error handling
  - Phase 2: Odoo + Social (16 tasks, ~6.5 hours) - Accounting, LinkedIn/Twitter posting
  - Phase 3: CEO Briefing + Ralph Wiggum (12 tasks, ~4.5 hours) - Monday briefing, autonomous tasks
  - Phase 4: Production Readiness (8 tasks, ~3.5 hours) - DLQ, health, docs
response_text: |
  Tasks generation prompt created successfully at specs/004-gold-tier-autonomous-employee/tasks-prompt.md

  ## Prompt Structure
  - Context: MVGT strategy (48 tasks, 15-20 hours, 80% Gold Tier value)
  - Task Requirements: ID format, priority, time, acceptance criteria, dependencies
  - Task Template: Exact markdown structure for each task
  - Phase Details: All 48 tasks described with implementation files
  - Output Format: tasks.md structure with phase summary, status, critical path
  - Additional Requirements: Dependency graph, test coverage, documentation, gap fix
  - Constraints: Exactly 48 tasks, 4 phases, 60/40 P0/P1 ratio, 15-20 hours

  ## Phase Breakdown
  | Phase | Tasks | Focus | Deliverables |
  |-------|-------|-------|--------------|
  | Phase 1 | T001-T012 | Foundation | Watchers, approval, retry, circuit breaker |
  | Phase 2 | T013-T028 | Odoo + Social | Accounting, LinkedIn/Twitter, rate limiting |
  | Phase 3 | T029-T040 | CEO Briefing + Ralph Wiggum | Monday briefing, state persistence |
  | Phase 4 | T041-T048 | Production | DLQ, health, alerting, docs |

  ## Key Tasks Included
  - T001-T003: BaseWatcher, GmailWatcher, WhatsAppWatcher
  - T004-T008: DEV_MODE, AuditLogger, approval workflow, orchestrator
  - T009-T010: Retry handler, circuit breaker
  - T013-T017: OdooMCP (invoice, payment, expense, fallback)
  - T018-T023: SocialMCP (LinkedIn, Twitter, rate limiting, session)
  - T029-T037: CEO Briefing (revenue, expenses, tasks, bottlenecks, suggestions)
  - T038-T040: Ralph Wiggum (state persistence, completion detection)
  - T041-T048: DLQ, health endpoint, alerting, 90-day log retention, docs

  ## Next Step
  Run: qwen "Generate tasks per specs/004-gold-tier-autonomous-employee/tasks-prompt.md"
outcome: |
  Tasks prompt completed. 48-task MVGT scope defined across 4 phases (15-20 hours). Ready for /sp.tasks execution to generate tasks.md.
evaluation: |
  **Prompt Quality**: Complete coverage of all 48 tasks with implementation details
  **MVGT Alignment**: 80% Gold Tier value in 60% less time (15-20 hours vs 40-60)
  **Task Granularity**: 15-60 min per task, testable acceptance criteria
  **Implementation Readiness**: All files, functions, tests specified
  **Next Phase**: Ready for `/sp.tasks` execution to generate tasks.md
