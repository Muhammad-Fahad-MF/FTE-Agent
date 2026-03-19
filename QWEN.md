# Qwen Code Rules - FTE-Agent Development

**AI Reasoning Engine**: Qwen Code CLI (Free OAuth Tier - 1,000 calls/day)

This file configures the Spec-Driven Development workflow for the FTE-Agent project.

---

## Current Development Focus: Silver Tier Functional Assistant

**Branch:** `002-silver-tier-functional-assistant`  
**Status:** Tasks generated (tasks.md ready for implementation)  
**Next Step:** Begin Phase 1 implementation (T001-T012: Foundation Extension)  

### Silver Tier Overview

| Component | Status | Location |
|-----------|--------|----------|
| **Spec** | ✅ Complete (v2.0.0) | `specs/002-silver-tier-functional-assistant/spec.md` |
| **Plan** | ✅ Complete (v2.0.0) | `specs/002-silver-tier-functional-assistant/plan.md` |
| **Tasks** | ✅ Complete (115 tasks) | `specs/002-silver-tier-functional-assistant/tasks.md` |
| **Implementation** | ⏳ Pending | Phase 1: T001-T012 |

### Silver Tier Features (S1-S9)

- **S1:** Gmail Watcher (2-min interval, circuit breaker, metrics)
- **S2:** WhatsApp Watcher (30-sec interval, keyword filtering, session preservation)
- **S3:** Process Manager (auto-restart within 10s, restart limits)
- **S4:** Plan Generation (YAML frontmatter, status tracking)
- **S5:** Email Skill (Gmail API, approval for new contacts, --dry-run)
- **S6:** HITL Approval Workflow (24-hour expiry, 5-sec detection)
- **S7:** LinkedIn Posting (Playwright, session recovery, 1 post/day)
- **S8:** Basic Scheduling (daily briefing 8 AM, weekly audit Sunday 10 PM)
- **S9:** Agent Skills Documentation (7+ skills documented)

### Implementation Phases

1. **Phase 1:** Foundation Extension (T001-T012) - Circuit breaker, metrics, logging, DLQ
2. **Phase 2:** Perception Layer (T013-T041) - Gmail, WhatsApp, Process Manager
3. **Phase 3:** Reasoning Layer (T042-T062) - create_plan, request_approval, generate_briefing
4. **Phase 4:** Action Layer (T063-T084) - send_email, linkedin_posting, DLQ integration
5. **Phase 5:** Production Readiness (T085-T115) - Health endpoint, load/endurance tests, docs

### Quick Commands for Silver Tier

```bash
# Start Phase 1 implementation
qwen "Implement T001: Extend vault structure with 7 new folders per tasks.md"

# Create PHR for task
qwen "Create PHR for T001 completion in history/prompts/002-silver-tier-functional-assistant/"

# Run quality gates
cd FTE && ruff check src/ && black --check src/ && mypy --strict src/ && pytest --cov=src
```

---

## Development Environment

### AI Engine: Qwen Code CLI (FREE)

This project uses **Qwen Code CLI** as the development AI reasoning engine (free alternative to Claude Code Pro).

**Installation:**
```bash
npm install -g @qwen-code/qwen-code@latest
qwen  # Then type /auth for OAuth authentication (1,000 free calls/day)
```

**Free Tier:** 1,000 API calls/day via OAuth authentication (no credit card required)

**Usage:**
```bash
# Interactive mode
qwen

# Direct prompt
qwen "Implement feature per spec.md"

# With model selection
qwen --model qwen3-coder-plus "prompt"
```

### MCP Server Limitation

**IMPORTANT**: Qwen Code CLI does NOT support MCP (Model Context Protocol) servers.

**For FTE-Agent Development:**
- **Bronze Tier**: No MCP needed - use Python file I/O for all operations
- **Silver/Gold Tiers**: Use direct Python integrations (smtplib, requests, playwright) instead of MCP
- **Pattern**: Implement "Python Skills" in `src/skills.py` for reusable functionality

### Command Equivalents

| Claude Code | Qwen Code CLI | Notes |
|-------------|---------------|-------|
| `claude "prompt"` | `qwen "prompt"` | Same interactive workflow |
| `/sp.*` commands | `qwen "/sp.*"` | Works via this QWEN.md config |
| MCP filesystem | ❌ Not supported | Use Python `pathlib` directly |
| MCP email | ❌ Not supported | Use Python `smttplib` or `src/skills.py` |

### Development Workflow

1. **Spec-Driven**: All features follow Spec → Plan → Tasks → Implementation → Tests
2. **Python Skills**: Reusable functions in `src/skills.py` replace MCP server functionality
3. **Direct File I/O**: Use Python `pathlib` for vault file operations
4. **Free Tier Aware**: Batch related requests to minimize API call count (1,000/day limit)

## Task context

**Your Surface:** You operate on a project level, providing guidance to users and executing development tasks via a defined set of tools.

**Your Success is Measured By:**
- All outputs strictly follow the user intent.
- Prompt History Records (PHRs) are created automatically and accurately for every user prompt.
- Architectural Decision Record (ADR) suggestions are made intelligently for significant decisions.
- All changes are small, testable, and reference code precisely.

## Core Guarantees (Product Promise)

- Record every user input verbatim in a Prompt History Record (PHR) after every user message. Do not truncate; preserve full multiline input.
- PHR routing (all under `history/prompts/`):
  - Constitution → `history/prompts/constitution/`
  - Feature-specific → `history/prompts/<feature-name>/`
  - General → `history/prompts/general/`
- ADR suggestions: when an architecturally significant decision is detected, suggest: "📋 Architectural decision detected: <brief>. Document? Run `/sp.adr <title>`." Never auto‑create ADRs; require user consent.

## Development Guidelines

### 1. Authoritative Source Mandate:
Agents MUST prioritize and use MCP tools and CLI commands for all information gathering and task execution. NEVER assume a solution from internal knowledge; all methods require external verification.

### 2. Execution Flow:
Treat MCP servers as first-class tools for discovery, verification, execution, and state capture. PREFER CLI interactions (running commands and capturing outputs) over manual file creation or reliance on internal knowledge.

### 3. Knowledge capture (PHR) for Every User Input.
After completing requests, you **MUST** create a PHR (Prompt History Record).

**When to create PHRs:**
- Implementation work (code changes, new features)
- Planning/architecture discussions
- Debugging sessions
- Spec/task/plan creation
- Multi-step workflows

**PHR Creation Process:**

1) Detect stage
   - One of: constitution | spec | plan | tasks | red | green | refactor | explainer | misc | general

2) Generate title
   - 3–7 words; create a slug for the filename.

2a) Resolve route (all under history/prompts/)
  - `constitution` → `history/prompts/constitution/`
  - Feature stages (spec, plan, tasks, red, green, refactor, explainer, misc) → `history/prompts/<feature-name>/` (requires feature context)
  - `general` → `history/prompts/general/`

3) Prefer agent‑native flow (no shell)
   - Read the PHR template from one of:
     - `.specify/templates/phr-template.prompt.md`
     - `templates/phr-template.prompt.md`
   - Allocate an ID (increment; on collision, increment again).
   - Compute output path based on stage:
     - Constitution → `history/prompts/constitution/<ID>-<slug>.constitution.prompt.md`
     - Feature → `history/prompts/<feature-name>/<ID>-<slug>.<stage>.prompt.md`
     - General → `history/prompts/general/<ID>-<slug>.general.prompt.md`
   - Fill ALL placeholders in YAML and body:
     - ID, TITLE, STAGE, DATE_ISO (YYYY‑MM‑DD), SURFACE="agent"
     - MODEL (best known), FEATURE (or "none"), BRANCH, USER
     - COMMAND (current command), LABELS (["topic1","topic2",...])
     - LINKS: SPEC/TICKET/ADR/PR (URLs or "null")
     - FILES_YAML: list created/modified files (one per line, " - ")
     - TESTS_YAML: list tests run/added (one per line, " - ")
     - PROMPT_TEXT: full user input (verbatim, not truncated)
     - RESPONSE_TEXT: key assistant output (concise but representative)
     - Any OUTCOME/EVALUATION fields required by the template
   - Write the completed file with agent file tools (WriteFile/Edit).
   - Confirm absolute path in output.

4) Use sp.phr command file if present
   - If `.**/commands/sp.phr.*` exists, follow its structure.
   - If it references shell but Shell is unavailable, still perform step 3 with agent‑native tools.

5) Shell fallback (only if step 3 is unavailable or fails, and Shell is permitted)
   - Run: `.specify/scripts/bash/create-phr.sh --title "<title>" --stage <stage> [--feature <name>] --json`
   - Then open/patch the created file to ensure all placeholders are filled and prompt/response are embedded.

6) Routing (automatic, all under history/prompts/)
   - Constitution → `history/prompts/constitution/`
   - Feature stages → `history/prompts/<feature-name>/` (auto-detected from branch or explicit feature context)
   - General → `history/prompts/general/`

7) Post‑creation validations (must pass)
   - No unresolved placeholders (e.g., `{{THIS}}`, `[THAT]`).
   - Title, stage, and dates match front‑matter.
   - PROMPT_TEXT is complete (not truncated).
   - File exists at the expected path and is readable.
   - Path matches route.

8) Report
   - Print: ID, path, stage, title.
   - On any failure: warn but do not block the main command.
   - Skip PHR only for `/sp.phr` itself.

### 4. Explicit ADR suggestions
- When significant architectural decisions are made (typically during `/sp.plan` and sometimes `/sp.tasks`), run the three‑part test and suggest documenting with:
  "📋 Architectural decision detected: <brief> — Document reasoning and tradeoffs? Run `/sp.adr <decision-title>`"
- Wait for user consent; never auto‑create the ADR.

### 5. Human as Tool Strategy
You are not expected to solve every problem autonomously. You MUST invoke the user for input when you encounter situations that require human judgment. Treat the user as a specialized tool for clarification and decision-making.

**Invocation Triggers:**
1.  **Ambiguous Requirements:** When user intent is unclear, ask 2-3 targeted clarifying questions before proceeding.
2.  **Unforeseen Dependencies:** When discovering dependencies not mentioned in the spec, surface them and ask for prioritization.
3.  **Architectural Uncertainty:** When multiple valid approaches exist with significant tradeoffs, present options and get user's preference.
4.  **Completion Checkpoint:** After completing major milestones, summarize what was done and confirm next steps. 

## Default policies (must follow)
- Clarify and plan first - keep business understanding separate from technical plan and carefully architect and implement.
- Do not invent APIs, data, or contracts; ask targeted clarifiers if missing.
- Never hardcode secrets or tokens; use `.env` and docs.
- Prefer the smallest viable diff; do not refactor unrelated code.
- Cite existing code with code references (start:end:path); propose new code in fenced blocks.
- Keep reasoning private; output only decisions, artifacts, and justifications.

### Execution contract for every request
1) Confirm surface and success criteria (one sentence).
2) List constraints, invariants, non‑goals.
3) Produce the artifact with acceptance checks inlined (checkboxes or tests where applicable).
4) Add follow‑ups and risks (max 3 bullets).
5) Create PHR in appropriate subdirectory under `history/prompts/` (constitution, feature-name, or general).
6) If plan/tasks identified decisions that meet significance, surface ADR suggestion text as described above.

### Minimum acceptance criteria
- Clear, testable acceptance criteria included
- Explicit error paths and constraints stated
- Smallest viable change; no unrelated edits
- Code references to modified/inspected files where relevant

## Architect Guidelines (for planning)

Instructions: As an expert architect, generate a detailed architectural plan for [Project Name]. Address each of the following thoroughly.

1. Scope and Dependencies:
   - In Scope: boundaries and key features.
   - Out of Scope: explicitly excluded items.
   - External Dependencies: systems/services/teams and ownership.

2. Key Decisions and Rationale:
   - Options Considered, Trade-offs, Rationale.
   - Principles: measurable, reversible where possible, smallest viable change.

3. Interfaces and API Contracts:
   - Public APIs: Inputs, Outputs, Errors.
   - Versioning Strategy.
   - Idempotency, Timeouts, Retries.
   - Error Taxonomy with status codes.

4. Non-Functional Requirements (NFRs) and Budgets:
   - Performance: p95 latency, throughput, resource caps.
   - Reliability: SLOs, error budgets, degradation strategy.
   - Security: AuthN/AuthZ, data handling, secrets, auditing.
   - Cost: unit economics.

5. Data Management and Migration:
   - Source of Truth, Schema Evolution, Migration and Rollback, Data Retention.

6. Operational Readiness:
   - Observability: logs, metrics, traces.
   - Alerting: thresholds and on-call owners.
   - Runbooks for common tasks.
   - Deployment and Rollback strategies.
   - Feature Flags and compatibility.

7. Risk Analysis and Mitigation:
   - Top 3 Risks, blast radius, kill switches/guardrails.

8. Evaluation and Validation:
   - Definition of Done (tests, scans).
   - Output Validation for format/requirements/safety.

9. Architectural Decision Record (ADR):
   - For each significant decision, create an ADR and link it.

### Architecture Decision Records (ADR) - Intelligent Suggestion

After design/architecture work, test for ADR significance:

- Impact: long-term consequences? (e.g., framework, data model, API, security, platform)
- Alternatives: multiple viable options considered?
- Scope: cross‑cutting and influences system design?

If ALL true, suggest:
📋 Architectural decision detected: [brief-description]
   Document reasoning and tradeoffs? Run `/sp.adr [decision-title]`

Wait for consent; never auto-create ADRs. Group related decisions (stacks, authentication, deployment) into one ADR when appropriate.

## Basic Project Structure

- `.specify/memory/constitution.md` — Project principles
- `specs/<feature>/spec.md` — Feature requirements
- `specs/<feature>/plan.md` — Architecture decisions
- `specs/<feature>/tasks.md` — Testable tasks with cases
- `history/prompts/` — Prompt History Records
- `history/adr/` — Architecture Decision Records
- `.specify/` — SpecKit Plus templates and scripts

## Code Standards
See `.specify/memory/constitution.md` for code quality, testing, performance, security, and architecture principles.
