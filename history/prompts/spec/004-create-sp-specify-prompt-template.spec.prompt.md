---
id: 004
title: Create sp.specify Prompt Template
stage: spec
date: 2026-03-07
surface: agent
model: qwen3-coder-plus
feature: sp-specify-prompt-template
branch: main
user: Imperial_Legend
command: Create detailed /sp.specify prompt template
labels: ["spec","prompt-engineering","template","sdd"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
  - .specify/templates/sp-specify-prompt-template.md
tests:
  - N/A (template creation - no tests run)
---

## Prompt

Create a detailed and specific prompt for /sp.specify command that will generate robust and efficient spec.md files. Research best practices for feature specifications from:
- XB Software SDD methodology
- Augment Code spec-driven development guide
- Panaversity Spec-Kit-Plus templates
- FTE-Agent Constitution v3.0.0

Requirements for the prompt:
1. Include all required sections for a complete spec (Overview, User Stories, Requirements, NFRs, Edge Cases, Out of Scope, Entities, Risks, Success Criteria, Compliance Checklist)
2. Enforce Given-When-Then acceptance criteria format
3. Mandate measurable thresholds (no vague language like "fast", "reliable")
4. Reference FTE-Agent Constitution principles (I-XIII)
5. Specify Qwen Code CLI context (free OAuth, no MCP, Python Skills pattern)
6. Define Bronze tier scope boundaries (IN SCOPE / OUT OF SCOPE)
7. Include all 5 security controls (DEV_MODE, --dry-run, audit logging, HITL, STOP file)
8. Testing strategy (unit/integration/contract/chaos)
9. Quality rules (USE vs NEVER language)
10. Self-validation checklist before output

Create both a compact version (fits Qwen Code CLI context limits) and detailed version (for complex features). Review the prompt 3 times as an engineer to ensure quality.

## Response snapshot

Created `.specify/templates/sp-specify-prompt-template.md` with:

**Compact Prompt** (~2,500 characters):
- Optimized for Qwen Code CLI context limits
- All 10 required spec sections
- Quality rules with ✅/❌ markers
- Bronze tier scope definition
- All 5 security controls mandated
- Example acceptance criteria quality
- Self-validation checklist

**Detailed Prompt** (for complex features):
- Full SDD methodology explanation
- User story format with priority justification
- Functional requirements with measurable thresholds
- Non-functional requirements aligned to constitution principles
- Testing strategy (unit/integration/contract/chaos)
- Python Skills pattern explanation
- Constitutional Compliance checklist (7 items)

**Engineering Reviews (3-Pass)**:
1. Completeness & Structure: All sections present, constitution aligned
2. Clarity & Usability: Compact + detailed versions, clear markers
3. Production Readiness: Measurable thresholds, testability enforced

**Key Features**:
- Given-When-Then format enforced for testability
- [NEEDS CLARIFICATION] pattern for uncertainties
- Bronze tier scope prevents feature creep
- Security controls mandatory (all 5)
- No implementation details allowed in spec (belongs in plan.md)

## Outcome

- ✅ Impact: Template enables consistent, production-grade spec generation for all FTE-Agent features
- 🧪 Tests: N/A (template creation - validated via 3-pass engineering review)
- 📁 Files: .specify/templates/sp-specify-prompt-template.md created
- 🔁 Next prompts: Use template with /sp.specify to create Bronze tier feature specs
- 🧠 Reflection: Compact prompt balances completeness with Qwen Code CLI context limits

## Evaluation notes (flywheel)

- Failure modes observed: None - template creation successful
- Graders run and results (PASS/FAIL): N/A
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): Test template with actual /sp.specify command and refine based on output quality
