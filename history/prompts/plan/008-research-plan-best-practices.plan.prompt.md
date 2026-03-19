---
id: 008
title: Research plan.md Best Practices
stage: plan
date: 2026-03-07
surface: agent
model: qwen3-coder-plus
feature: sp-plan-prompt-template
branch: main
user: Imperial_Legend
command: Research plan.md best practices from templates and docs
labels: ["plan","research","template","sdd","architecture"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
  - .specify/templates/sp-plan-prompt-template.md
tests:
  - N/A (research and template creation - no tests run)
---

## Prompt

Research best practices for writing implementation plans (plan.md) by analyzing:
1. Existing plan-template.md in .specify/templates/
2. Panaversity Spec-Kit-Plus documentation
3. IEEE 1016 Design Document standard
4. ISO/IEC/IEEE 42010 Architecture Framework
5. Technical design document best practices from industry

Create a comprehensive prompt template for /sp.plan that includes:
- All required sections (Summary, Technical Context, Constitution Check, Project Structure, Architecture, Technology Choices, Implementation Phases, Complexity Tracking, Risk Analysis, Operational Readiness, Supporting Documents)
- Constitutional Compliance Gates (all 13 principles for FTE-Agent)
- Technology choices with alternatives considered and rationale
- Implementation phases with prerequisites and exit criteria
- Risk analysis template (impact, probability, mitigation)
- Operational readiness (observability, alerting, runbooks, deployment)
- Supporting documents list (research.md, data-model.md, contracts/, quickstart.md)

Review the template 3 times as an engineer before finalizing.

## Response snapshot

Created `.specify/templates/sp-plan-prompt-template.md` with comprehensive research on implementation plan best practices:

**Research Sources Analyzed**:
- FTE-Agent plan-template.md (existing template)
- Panaversity Spec-Kit-Plus workflow documentation
- IEEE 1016 Design Document standard (4 Design Views)
- ISO/IEC/IEEE 42010 Architecture Framework (stakeholder viewpoints)
- Technical design document best practices from industry blogs

**Key Findings**:

**IEEE 1016 Design Views**:
- Decomposition Description (system breakdown into components)
- Dependency Description (component relationships)
- Interface Description (interaction methods)
- Detail Description (low-level logic)

**ISO/IEC/IEEE 42010 Framework**:
- Architecture Views (stakeholder-specific perspectives)
- Viewpoint-specific diagrams (logical, physical, security)
- Link diagrams to stakeholder concerns

**Panaversity Spec-Kit-Plus Workflow**:
- /sp.plan generates 5 documents: plan.md, research.md, data-model.md, contracts/, quickstart.md
- Constitution Check as Phase -1 gate (must pass before implementation)
- Implementation phases: Phase 0 (Foundation), Phase 1 (Core), Phase 2 (Integration), Phase 3 (Validation)
- Every technical decision must trace to requirement

**Template Structure Created** (11 sections):
1. Summary (requirement + technical approach + key decisions)
2. Technical Context (language, dependencies, storage, testing, platform, goals, constraints)
3. Constitution Check (all 13 principles with checkboxes)
4. Project Structure (documentation + source code)
5. Architecture Design (system diagram, component responsibilities, data flow)
6. Technology Choices (with alternatives considered and rationale)
7. Implementation Phases (Phase -1 through Phase 3 with exit criteria)
8. Complexity Tracking (justified violations, technical debt notes)
9. Risk Analysis (top 5 risks with impact, probability, mitigation)
10. Operational Readiness (observability, alerting, runbooks, deployment/rollback)
11. Supporting Documents (research.md, data-model.md, contracts/, quickstart.md)

**Engineering Reviews (3-Pass)**:
1. Completeness & Structure: ✅ All 11 sections, IEEE 1016 aligned, constitution gates
2. Quality Enforcement: ✅ Traced decisions, alternatives documented, no code in plan
3. Constitution Alignment: ✅ All 13 principles, Python Skills pattern, Bronze scope

**Key Quality Markers**:
- Every technical decision traces to requirement from spec.md
- Technology choices include alternatives considered
- Implementation phases have clear prerequisites and exit criteria
- Risk analysis includes top 5 risks with mitigations
- Operational readiness defined (observability, alerting, runbooks)
- No implementation code in plan.md (belongs in source files)

## Outcome

- ✅ Impact: Comprehensive /sp.plan prompt template enables consistent, production-quality implementation plans
- 🧪 Tests: N/A (template creation - validated via 3-pass engineering review)
- 📁 Files: .specify/templates/sp-plan-prompt-template.md created
- 🔁 Next prompts: Use template with /sp.plan to create implementation plan for File System Watcher
- 🧠 Reflection: Research revealed importance of constitutional compliance gates (Phase -1) before any implementation begins

## Evaluation notes (flywheel)

- Failure modes observed: None - template creation successful
- Graders run and results (PASS/FAIL): N/A
- Prompt variant (if applicable): Compact version for Qwen Code CLI context limits
- Next experiment (smallest change to try): Compare plan quality between compact and extended versions
