---
id: 010
title: Consolidate Plan Prompt to Single Version
stage: plan
date: 2026-03-07
surface: agent
model: qwen3-coder-plus
feature: sp-plan-prompt-final
branch: main
user: Imperial_Legend
command: Consolidate collaborative plan prompt to single unified prompt
labels: ["plan","prompt-consolidation","single-prompt","production-ready"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
  - .specify/templates/sp-plan-prompt-final.md
tests:
  - N/A (prompt consolidation - no tests run)
---

## Prompt

Consolidate the collaborative /sp.plan prompt (from docs/collaborative-plan-prompt-design.md) into a single, unified prompt without the collaborative framing (three experts, rounds, etc.) that would confuse the AI agent.

The final prompt should:
1. Have a clear expert persona (Technical Architect with 25+ years experience)
2. Include all 10 required sections from the collaborative design
3. Maintain IEEE 1016 structure (4 Design Views)
4. Include failure mode analysis and risk analysis tables
5. Have test-first implementation phases
6. Include quality gates and self-validation checklist
7. Be ready to use directly with Qwen Code CLI

Remove:
- Three expert personas
- Round 1, Round 2, Round 3, Round 4 framing
- Collaborative design session narrative
- Any meta-discussion about the prompt design process

Save the consolidated prompt to .specify/templates/sp-plan-prompt-final.md

## Response snapshot

Created `.specify/templates/sp-plan-prompt-final.md` - a single, unified /sp.plan prompt ready for direct use with Qwen Code CLI:

**Consolidation Changes**:
- ✅ Removed three expert personas (Sarah, Marcus, Priya)
- ✅ Removed 4-round collaborative framing
- ✅ Removed meta-discussion about prompt design
- ✅ Kept all substantive content from collaborative design
- ✅ Single expert persona (Technical Architect with 25+ years)
- ✅ Direct, clear instructions without collaborative narrative

**Final Prompt Structure** (10 sections):
1. Executive Summary (problem, approach, key decisions)
2. Technical Context (language, dependencies, testing, platform, goals)
3. Constitution Compliance Check (all 13 principles with evidence and tests)
4. IEEE 1016 Design Views (Decomposition, Dependency, Interface, Detail)
5. Technology Choices (with alternatives considered and rollback plans)
6. Implementation Phases (test-first, iterative, Phase -1 through Phase 3)
7. Failure Mode Analysis (top 5 failure modes with detection/recovery/prevention)
8. Risk Analysis (top 5 risks with impact, probability, mitigation)
9. Operational Readiness (observability, alerting, deployment, rollback)
10. Supporting Documents (research.md, data-model.md, contracts/, quickstart.md)

**Key Quality Markers**:
- Constitution Compliance Gate (Phase -1, all 13 principles)
- IEEE 1016 4 Design Views (Decomposition, Dependency, Interface, Detail)
- Test-first approach (Red-Green-Refactor cycle in Phase 1)
- Quality gates automated (ruff, black, mypy, bandit, pytest 80%+)
- Failure mode analysis table (5 failure modes)
- Risk analysis table (5 risks)
- Technology choices with rollback plans
- Self-validation checklist before output

**Usage**:
```bash
qwen "[Copy entire prompt from sp-plan-prompt-final.md]"
```

## Outcome

- ✅ Impact: Single, unified prompt ready for direct agent use (no collaborative confusion)
- 🧪 Tests: N/A (prompt consolidation - validated via structural review)
- 📁 Files: .specify/templates/sp-plan-prompt-final.md created
- 🔁 Next prompts: Use final prompt with /sp.plan to create File System Watcher implementation plan
- 🧠 Reflection: Collaborative design produced superior content, but final prompt must be single unified voice for agent clarity

## Evaluation notes (flywheel)

- Failure modes observed: None - consolidation successful
- Graders run and results (PASS/FAIL): N/A
- Prompt variant (if applicable): Collaborative (design process) vs Final (single unified prompt)
- Next experiment (smallest change to try): Compare plan quality between collaborative-framed prompt vs single-voice prompt
