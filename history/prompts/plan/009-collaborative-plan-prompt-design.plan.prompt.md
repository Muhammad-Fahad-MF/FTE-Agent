---
id: 009
title: Collaborative Plan Prompt Design
stage: plan
date: 2026-03-07
surface: agent
model: qwen3-coder-plus
feature: sp-plan-prompt-collaborative
branch: main
user: Imperial_Legend
command: Three experts collaborate to design ultimate /sp.plan prompt
labels: ["plan","collaborative","prompt-engineering","ieee-1016","test-first"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
  - docs/collaborative-plan-prompt-design.md
tests:
  - N/A (collaborative design session - no tests run)
---

## Prompt

Imagine three different AI-driven development experts with prompt engineering skills are designing a prompt for /sp.plan (with all requirements) to extract maximum agent performance to create a robust plan.md.

**Step 1**: Each expert proposes one distinct initial prompt using the sp-plan-prompt-template.
**Step 2**: They review each other's ideas, identifying flaws and potential dead ends.
**Step 3**: Based on the critique, they discard the weakest path and develop the most promising one further.
**Step 4**: Repeat this until a final, refined prompt is reached.

Expert personas:
- **Dr. Sarah Chen**: Software Architecture Specialist (IEEE 1016, traceability, technical rigor)
- **Marcus Rodriguez**: DevOps & SRE Lead (operational readiness, failure scenarios, production resilience)
- **Priya Sharma**: AI-Assisted Development Specialist (agent performance, prompt engineering, iterative refinement)

Document the entire 4-round collaborative process and the final refined prompt.

## Response snapshot

Created `docs/collaborative-plan-prompt-design.md` documenting a 4-round collaborative design session:

**Round 1 - Initial Proposals**:
- **Expert A (Sarah)**: IEEE 1016 focused (4 Design Views: Decomposition, Dependency, Interface, Detail)
- **Expert B (Marcus)**: Production resilience focused (failure mode analysis, runbooks, rollback plans)
- **Expert C (Priya)**: AI-optimized focused (test-first, explicit file order, quality gates)

**Round 2 - Cross-Review**:
Each expert reviewed the other two proposals:
- Sarah's IEEE 1016 praised for traceability but criticized as "too academic"
- Marcus's operations focus praised for production readiness but criticized as "runbooks belong in quickstart.md"
- Priya's AI optimization praised for test-first but criticized as "too prescriptive on file order"

**Round 3 - Consensus**:
**Agreed Discards**: Day estimates, runbooks in plan.md, overly prescriptive file order, pure academic IEEE 1016
**Agreed Keeps**: IEEE 1016 structure, failure mode analysis, test-first approach, quality gates, rollback plans, AI-optimized guidance

**Round 4 - Final Synthesis**:
Combined best elements from all three:
1. IEEE 1016 backbone (4 Design Views)
2. Failure mode analysis table (5 failure modes with detection/recovery)
3. Test-first implementation (tests before code in Phase 1)
4. Quality gates automated (ruff, black, mypy, bandit, pytest 80%+)
5. Technology choices with rollback plans
6. Constitution compliance as Phase -1 gate
7. Operational readiness (observability, alerting, deployment, rollback)
8. Supporting documents (research.md, data-model.md, contracts/, quickstart.md with runbooks)

**Final Prompt Quality Markers**:
- 13 constitution principles checked with evidence and tests
- IEEE 1016 4 Design Views complete
- Technology choices have alternatives + rollback plans
- Failure mode analysis: top 5 risks with detection + recovery
- Test-first approach (Red-Green-Refactor cycle)
- Quality gates automated
- Operational readiness defined
- Every decision traces to spec.md requirement

## Outcome

- ✅ Impact: Collaborative design produced superior prompt vs any individual proposal
- 🧪 Tests: N/A (design session - validated via expert cross-review)
- 📁 Files: docs/collaborative-plan-prompt-design.md created
- 🔁 Next prompts: Use final prompt with /sp.plan to create File System Watcher implementation plan
- 🧠 Reflection: Three-perspective review (architecture + operations + AI) caught issues single-perspective would miss

## Evaluation notes (flywheel)

- Failure modes observed: None - collaborative design successful
- Graders run and results (PASS/FAIL): N/A
- Prompt variant (if applicable): Collaborative vs individual design
- Next experiment (smallest change to try): Compare plan quality between collaborative-designed prompt and individual-designed prompt
