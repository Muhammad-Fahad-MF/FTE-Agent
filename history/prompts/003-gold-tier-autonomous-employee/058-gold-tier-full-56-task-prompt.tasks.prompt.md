---
id: "058"
title: "Gold Tier Full Implementation Tasks Prompt"
stage: "tasks"
date_iso: "2026-04-02"
surface: "agent"
model: "qwen3-coder-plus"
feature: "003-gold-tier-autonomous-employee"
branch: "003-gold-tier-autonomous-employee"
user: "Imperial_Legend"
command: "Write prompt for /sp.tasks with 56 detailed tasks for 100% Gold Tier"
labels: ["tasks-generation", "gold-tier", "full-implementation", "no-cuts"]
links:
  spec: "specs/003-gold-tier-autonomous-employee/spec.md"
  plan: "specs/003-gold-tier-autonomous-employee/plan.md"
  ticket: "null"
  adr: "null"
  pr: "null"
files_yaml: |
  - specs/003-gold-tier-autonomous-employee/tasks-prompt.md
tests_yaml: |
  - Tasks prompt validation (56 tasks, 5 phases, 40-56 hours, 100% Gold Tier)
prompt_text: |
  Write a prompt for /sp.tasks with 56 detailed tasks for 100% Gold Tier implementation.

  Create comprehensive tasks generation prompt incorporating:
  - 56 tasks across 5 phases (Foundation, MCP Servers, CEO Briefing + Ralph Wiggum, Production Readiness, Documentation + Testing)
  - All 9 Gold Tier requirements fully implemented (no cuts, no MVP)
  - All 6 MCP servers (Email, WhatsApp, Social Media, Odoo, Browser, Filesystem)
  - All 5 watchers (Gmail, WhatsApp, FileSystem, Social Media, Odoo)
  - CEO Briefing with all 7 components
  - Ralph Wiggum with state persistence, completion detection, max iterations
  - Error recovery with retry, circuit breakers, DLQ, graceful degradation
  - Audit logging with 90-day retention
  - Complete documentation (architecture, API reference, setup guide, runbook, security)

  Phase Breakdown:
  - Phase 1: Foundation (14 tasks, T001-T014, ~8 hours) - Watchers, approval, error handling
  - Phase 2: MCP Servers (16 tasks, T015-T030, ~12 hours) - All 6 MCP servers
  - Phase 3: CEO Briefing + Ralph Wiggum (14 tasks, T031-T044, ~10 hours) - Briefing, autonomous tasks
  - Phase 4: Production Readiness (8 tasks, T045-T052, ~8 hours) - DLQ, health, alerting, fallback
  - Phase 5: Documentation + Testing (4 tasks, T053-T056, ~6 hours) - Docs, integration tests
response_text: |
  Full Gold Tier tasks prompt created successfully at specs/003-gold-tier-autonomous-employee/tasks-prompt.md

  ## Prompt Structure
  - Context: 100% Gold Tier implementation (56 tasks, 40-56 hours)
  - Gold Tier Requirements: All 9 requirements listed (cross-domain, Odoo, social media, MCPs, CEO Briefing, error recovery, audit logging, Ralph Wiggum, documentation)
  - Task Requirements: ID format, priority (P0/P1/P2), time, acceptance criteria (3-5 per task), dependencies
  - Task Template: Exact markdown structure for each task
  - Phase Details: All 56 tasks described with implementation files, key functions, tests
  - Output Format: tasks.md structure with phase summary, status, critical path, success criteria
  - Additional Requirements: Dependency graph, test coverage, documentation, full Gold Tier coverage
  - Constraints: Exactly 56 tasks, 5 phases, 75% P0, 40-56 hours, 100% Gold Tier (no cuts)

  ## Phase Breakdown
  | Phase | Tasks | Focus | Deliverables |
  |-------|-------|-------|--------------|
  | Phase 1 | T001-T014 | Foundation | BaseWatcher, Gmail/WhatsApp/FileSystem watchers, DEV_MODE, AuditLogger (90-day), approval workflow, orchestrator, retry, circuit breaker, Dashboard.md |
  | Phase 2 | T015-T030 | MCP Servers | EmailMCP, WhatsAppMCP, SocialMCP (LinkedIn/Twitter/Facebook/Instagram), OdooMCP, rate limiting |
  | Phase 3 | T031-T044 | CEO Briefing + Ralph Wiggum | CEOBriefing model, revenue/expenses/tasks/bottlenecks/subscriptions/cashflow/suggestions, Monday 8 AM scheduler, TaskState, state persistence, completion detection, max iterations |
  | Phase 4 | T045-T052 | Production | DLQ, health endpoint, alerting, Odoo fallback, social fallback, log query, process manager |
  | Phase 5 | T053-T056 | Docs + Tests | Architecture docs, API reference, setup guide, runbook, security disclosure, integration tests |

  ## Key Features
  - All 6 MCP servers: Email, WhatsApp, Social (4 platforms), Odoo, Browser, Filesystem
  - All 5 watchers: Gmail (2-min), WhatsApp (30-sec), FileSystem (60-sec), Social Media, Odoo
  - CEO Briefing: All 7 components (revenue, expenses, tasks, bottlenecks, subscriptions, cash flow, suggestions)
  - Ralph Wiggum: State persistence, completion detection (file movement + promise tag), max 10 iterations, DLQ escalation
  - Error Recovery: Retry (1s/2s/4s, max 3), circuit breakers (5 failures), DLQ, graceful degradation (fallbacks)
  - Audit Logging: JSON schema, 90-day retention, daily rotation, query utility
  - Documentation: Architecture, API reference, setup guide, runbook, security disclosure

  ## Success Criteria
  - 56 tasks with 3-5 acceptance criteria each
  - All 9 Gold Tier requirements covered
  - 40-56 hours estimated total time
  - 75% P0 tasks (critical path)
  - Complete dependency graph

  ## Next Step
  Run: qwen "Generate tasks per specs/003-gold-tier-autonomous-employee/tasks-prompt.md"
outcome: |
  Full Gold Tier tasks prompt completed. 56 tasks across 5 phases (40-56 hours) for 100% Gold Tier implementation - all 9 requirements, all 6 MCP servers, all 5 watchers, complete CEO Briefing, full Ralph Wiggum loop, production error handling, 90-day audit logging, complete documentation. No cuts, no MVP, no artificial limitations.
evaluation: |
  **Prompt Quality**: Complete coverage of all 9 Gold Tier requirements with 56 detailed tasks
  **Gold Tier Compliance**: 100% - all requirements fully implemented (cross-domain, Odoo, 4-platform social, 6 MCPs, CEO Briefing, error recovery, audit logging, Ralph Wiggum, documentation)
  **Task Granularity**: 15-90 min per task, 3-5 testable acceptance criteria each
  **Implementation Readiness**: All files, functions, tests specified for all 56 tasks
  **Next Phase**: Ready for `/sp.tasks` execution to generate tasks.md
