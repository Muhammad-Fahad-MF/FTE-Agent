---
id: 016
title: Collaborative Tasks Prompt Design
stage: tasks
date: 2026-03-07
surface: agent
model: qwen3-coder-plus
feature: sp-tasks-prompt-collaborative
branch: main
user: Imperial_Legend
command: Three experts collaborate to design ultimate /sp.tasks prompt
labels: ["tasks","collaborative","prompt-engineering","tdd","task-breakdown"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
  - docs/collaborative-tasks-prompt-design.md
tests:
  - N/A (collaborative design session - no tests run)
---

## Prompt

Imagine three different prompt engineering experts are designing a detailed, specific prompt for /sp.tasks using the template (sp-tasks-prompt-template.md) to make agent generate a robust tasks.md with all researched qualities.

**Step 1**: Each expert proposes one distinct prompt approach.
**Step 2**: They review each other's ideas, identifying flaws and potential dead ends.
**Step 3**: Based on the critique, they discard the weakest path, connect good ideas from individual prompts to final prompt, and develop the most promising one further.
**Step 4**: Repeat this until a final, refined prompt is reached.

Expert personas:
- **Dr. Emily Carter**: TDD & Testing Specialist (test-first, Red-Green-Refactor, test ordering)
- **Marcus Johnson**: Agile & Scrum Master (task sizing, parallel execution, MVP strategy)
- **Sarah Chen**: Technical Architect (dependency ordering, exact file paths, architecture alignment)

Document the entire 4-round collaborative process and the final refined prompt.

## Response snapshot

Created `docs/collaborative-tasks-prompt-design.md` documenting a 4-round collaborative design session:

**Round 1 - Initial Proposals**:
- **Expert A (Emily)**: TDD-focused (test ordering: Contract → Unit → Integration → Chaos, Red-Green-Refactor cycle, specific test function names)
- **Expert B (Marcus)**: Agile-focused (task sizing 4-16 hours, [P] parallel markers, MVP first, checkpoint validations)
- **Expert C (Sarah)**: Architecture-focused (exact file paths, dependency ordering, layer-based implementation)

**Round 2 - Cross-Review**:
Each expert reviewed the other two proposals:
- Emily's TDD praised for test ordering but criticized as "no task sizing, no file paths"
- Marcus's Agile praised for task sizing and parallel markers but criticized as "test ordering not explicit"
- Sarah's Architecture praised for file paths and dependencies but criticized as "layer structure over-engineering for Bronze tier"

**Round 3 - Consensus**:
**Agreed Discards**: Layer-based structure, mixed test/implementation ordering, vague file paths, no task sizing
**Agreed Keeps**: Test-first approach (Emily), test ordering (Emily), task sizing 4-16h (Marcus), parallel markers [P] (Marcus), MVP strategy (Marcus), exact file paths (Sarah), dependency ordering (Sarah), checkpoint validations (Marcus)

**Round 4 - Final Synthesis**:
Combined best elements from all three:
1. Test-first structure with Red-Green-Refactor cycle (Emily)
2. Test ordering: Contract → Unit → Integration → Chaos (Emily)
3. Task sizing 4-16 hours each (Marcus)
4. Parallel execution markers [P] (Marcus)
5. MVP first approach (Marcus)
6. Exact file paths for every task (Sarah)
7. Dependency ordering (models → services → implementation) (Sarah)
8. Checkpoint validations after each user story (Marcus)

**Final Prompt Structure** (5 phases):
- Phase 0: Setup & Foundation (4-8 hours)
- Phase 1: User Story 1 - Test-First (16-24 hours)
  - Tests First (RED): T009-T012 (Contract, Unit, Integration)
  - Implementation (GREEN): T013-T016 (audit_logger, base_watcher, filesystem_watcher, skills)
- Phase 2: User Story 2 - Error Handling (12-16 hours)
- Phase 3: User Story 3 - Configuration (8-12 hours)
- Phase 4: Quality Gates & Validation (4-8 hours)

**Key Quality Markers**:
- Exact file paths (e.g., src/filesystem_watcher.py)
- [P] markers for parallel execution
- [Story] labels for traceability (US1, US2, US3)
- Checkpoint validations after each story
- Quality gates (ruff, black, mypy, bandit, pytest 80%+)
- Critical path identified
- Test-first ordering (Red-Green-Refactor)
- Task size 4-16 hours each

## Outcome

- ✅ Impact: Collaborative design produced superior prompt vs any individual proposal
- 🧪 Tests: N/A (design session - validated via expert cross-review)
- 📁 Files: docs/collaborative-tasks-prompt-design.md created
- 🔁 Next prompts: Use final prompt with /sp.tasks to create task breakdown for File System Watcher
- 🧠 Reflection: Three-perspective review (TDD + Agile + Architecture) caught issues single-perspective would miss

## Evaluation notes (flywheel)

- Failure modes observed: None - collaborative design successful
- Graders run and results (PASS/FAIL): N/A
- Prompt variant (if applicable): Collaborative vs individual design
- Next experiment (smallest change to try): Compare task breakdown quality between collaborative-designed prompt and individual-designed prompt
