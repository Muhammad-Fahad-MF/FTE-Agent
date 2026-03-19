---
id: 017
title: Consolidate Tasks Prompt to Single Version
stage: tasks
date: 2026-03-07
surface: agent
model: qwen3-coder-plus
feature: sp-tasks-prompt-final
branch: main
user: Imperial_Legend
command: Consolidate collaborative tasks prompt to single unified prompt
labels: ["tasks","prompt-consolidation","single-prompt","tdd","task-breakdown"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
  - .specify/templates/sp-tasks-prompt-final.md
tests:
  - N/A (prompt consolidation - no tests run)
---

## Prompt

Consolidate the collaborative /sp.tasks prompt (from docs/collaborative-tasks-prompt-design.md) into a single, unified prompt without the collaborative framing (three experts, rounds, etc.) that would confuse the AI agent.

The final prompt should:
1. Have a clear expert persona (Technical Lead with 20+ years experience)
2. Include all 5 phases from collaborative design
3. Maintain test-first structure (Red-Green-Refactor)
4. Include task sizing (4-16 hours), parallel markers [P], exact file paths
5. Have dependency ordering and checkpoint validations
6. Be ready to use directly with Qwen Code CLI

Remove:
- Three expert personas
- Round 1, Round 2, Round 3, Round 4 framing
- Collaborative design session narrative
- Any meta-discussion about the prompt design process

Save the consolidated prompt to .specify/templates/sp-tasks-prompt-final.md

## Response snapshot

Created `.specify/templates/sp-tasks-prompt-final.md` - a single, unified /sp.tasks prompt ready for direct use with Qwen Code CLI:

**Consolidation Changes**:
- ✅ Removed three expert personas (Emily, Marcus, Sarah)
- ✅ Removed 4-round collaborative framing
- ✅ Removed meta-discussion about prompt design
- ✅ Kept all substantive content from collaborative design
- ✅ Single expert persona (Technical Lead with 20+ years)
- ✅ Direct, clear instructions without collaborative narrative

**Final Prompt Structure** (5 phases):
1. Phase 0: Setup & Foundation (4-8 hours)
2. Phase 1: User Story 1 - Test-First (16-24 hours)
   - Tests First (RED): T009-T012 (Contract, Unit, Integration)
   - Implementation (GREEN): T013-T016 (audit_logger, base_watcher, filesystem_watcher, skills)
3. Phase 2: User Story 2 - Error Handling (12-16 hours)
4. Phase 3: User Story 3 - Configuration (8-12 hours)
5. Phase 4: Quality Gates & Validation (4-8 hours)

**Key Quality Markers**:
- Test-first structure (Red-Green-Refactor cycle)
- Test ordering: Contract → Unit → Integration → Chaos
- Task sizing 4-16 hours each
- Parallel execution markers [P]
- MVP first approach (US1 only for quick win)
- Exact file paths for every task (e.g., src/filesystem_watcher.py)
- Dependency ordering (models → services → implementation)
- Checkpoint validations after each user story
- Quality gates (ruff, black, mypy, bandit, pytest 80%+)

**Usage**:
```bash
qwen "[Copy entire prompt from sp-tasks-prompt-final.md]"
```

## Outcome

- ✅ Impact: Single, unified prompt ready for direct agent use (no collaborative confusion)
- 🧪 Tests: N/A (prompt consolidation - validated via structural review)
- 📁 Files: .specify/templates/sp-tasks-prompt-final.md created
- 🔁 Next prompts: Use final prompt with /sp.tasks to create task breakdown for File System Watcher
- 🧠 Reflection: Collaborative design produced superior content, but final prompt must be single unified voice for agent clarity

## Evaluation notes (flywheel)

- Failure modes observed: None - consolidation successful
- Graders run and results (PASS/FAIL): N/A
- Prompt variant (if applicable): Collaborative (design process) vs Final (single unified prompt)
- Next experiment (smallest change to try): Compare task breakdown quality between collaborative-framed prompt vs single-voice prompt
