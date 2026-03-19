---
id: 015
title: Research tasks.md Best Practices
stage: tasks
date: 2026-03-07
surface: agent
model: qwen3-coder-plus
feature: sp-tasks-prompt-template
branch: main
user: Imperial_Legend
command: Research tasks.md best practices and create prompt template
labels: ["tasks","research","prompt-template","tdd","task-breakdown"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
  - .specify/templates/sp-tasks-prompt-template.md
tests:
  - N/A (research and template creation - no tests run)
---

## Prompt

Research best practices for writing implementation task breakdowns (tasks.md) by analyzing:
1. Existing tasks-template.md in .specify/templates/
2. Panaversity Spec-Kit-Plus documentation
3. GitHub Spec-Kit repository
4. Agile task breakdown best practices (INVEST criteria, 4-16 hour tasks)
5. TDD best practices (red-green-refactor, test-first ordering)
6. Task dependency mapping (critical path, parallel execution)

Create a comprehensive prompt template for /sp.tasks that includes:
- Task organization by user story (each story = separate phase)
- Dependency ordering (models → services → implementation)
- Parallel execution markers [P]
- Test-first approach (tests before implementation)
- Checkpoint validations after each user story
- Exact file paths for every task
- Task size guidelines (4-16 hours each)
- Quality gates (ruff, black, mypy, bandit, pytest 80%+ coverage)

Review the template 3 times as an engineer before finalizing.

## Response snapshot

Created `.specify/templates/sp-tasks-prompt-template.md` with comprehensive research on task breakdown best practices:

**Research Sources Analyzed**:
- FTE-Agent tasks-template.md (existing template)
- Panaversity Spec-Kit-Plus (task breakdown by user story)
- GitHub Spec-Kit (dependency ordering, parallel markers)
- Agile task breakdown (INVEST criteria, 4-16 hour tasks)
- TDD best practices (red-green-refactor, test-first)
- Critical Path Method (dependency mapping, parallel execution)

**Key Findings**:

**Task Organization**:
- Each user story becomes separate implementation phase
- Tests written before implementation (TDD)
- Dependencies respected (models → services → implementation)
- Parallel opportunities marked with [P]

**Task Size Guidelines**:
- 4-16 hours per task (completable in 1-2 days)
- Small enough for single sprint completion
- Large enough to avoid unnecessary overhead

**Test-First Approach**:
- Contract tests first (interface validation)
- Unit tests second (component behavior)
- Integration tests third (component interaction)
- Chaos tests fourth (failure scenarios)
- Implementation last (make tests pass)

**Template Structure Created** (5 phases):
1. Phase 0: Setup & Foundation (shared infrastructure)
2. Phase 1: User Story 1 (P1 - MVP) - tests first, then implementation
3. Phase 2: User Story 2 (P1 - MVP) - error handling
4. Phase 3: User Story 3 (P2) - configuration
5. Phase 4: Quality Gates & Validation

**Engineering Reviews (3-Pass)**:
1. Task Breakdown Quality: ✅ All stories have phases, test-first, dependencies, parallel markers, file paths
2. Agile Best Practices: ✅ 4-16 hour tasks, independent delivery, MVP first, incremental, parallel strategy
3. TDD Compliance: ✅ Red-Green-Refactor, tests before implementation, contract→unit→integration→chaos, quality gates

**Key Quality Markers**:
- Exact file paths for every task (e.g., src/filesystem_watcher.py)
- [P] markers for parallel execution
- [Story] labels for traceability (US1, US2, US3)
- Checkpoint validations after each user story
- Quality gates blocking merge (ruff, black, mypy, bandit, pytest)
- Critical path identified (Phase 0 → Phase 1 → Phase 2 → Phase 4)

## Outcome

- ✅ Impact: Comprehensive /sp.tasks prompt template enables consistent, production-quality task breakdowns
- 🧪 Tests: N/A (template creation - validated via 3-pass engineering review)
- 📁 Files: .specify/templates/sp-tasks-prompt-template.md created
- 🔁 Next prompts: Use template with /sp.tasks to create task breakdown for File System Watcher
- 🧠 Reflection: Task breakdown quality directly impacts implementation speed and quality - TDD + parallel markers optimize both

## Evaluation notes (flywheel)

- Failure modes observed: None - template creation successful
- Graders run and results (PASS/FAIL): N/A
- Prompt variant (if applicable): Compact version for Qwen Code CLI context limits
- Next experiment (smallest change to try): Compare implementation speed between TDD-ordered tasks vs traditional tasks
