# Qwen Code Rules - FTE-Agent Development

**AI Reasoning Engine**: Qwen Code CLI (Free OAuth Tier - 1,000 calls/day)

This file configures the Spec-Driven Development workflow for the FTE-Agent project.

---

## Current Development Focus: Gold Tier Autonomous Employee

**Branch:** `003-gold-tier-autonomous-employee` (to be created)
**Status:** ✅ Silver Tier COMPLETE - Ready for Gold Tier planning
**Next Step:** Create Gold Tier spec/plan/tasks (G1-G12: 54 hours estimated)

### ✅ Silver Tier Completion Summary (v2.0.0)

| Component | Status | Evidence |
|-----------|--------|----------|
| **Spec** | ✅ Complete (v2.0.0) | `specs/002-silver-tier-functional-assistant/spec.md` |
| **Plan** | ✅ Complete (v2.0.0) | `specs/002-silver-tier-functional-assistant/plan.md` |
| **Tasks** | ✅ Complete (115/115) | `specs/002-silver-tier-functional-assistant/tasks.md` |
| **Implementation** | ✅ Complete | All phases T001-T115 implemented |
| **Tests** | ✅ 85%+ coverage | 44 test files (unit, integration, chaos, load, endurance) |
| **Quality Gates** | ✅ Passing | ruff, black, mypy, bandit, isort |
| **Documentation** | ✅ Complete | README, runbook, DR plan, deployment checklist |
| **Production Status** | ✅ READY | v2.0.0 released (2026-04-02) |

### ✅ Silver Tier Features Delivered (S1-S9)

- **S1:** ✅ Gmail Watcher (2-min interval, circuit breaker, SQLite persistence)
- **S2:** ✅ WhatsApp Watcher (30-sec interval, keyword filtering, session preservation)
- **S3:** ✅ Process Manager (auto-restart <10s, restart limits, memory monitoring)
- **S4:** ✅ Plan Generation (YAML frontmatter, status tracking, file locking)
- **S5:** ✅ Email Skill (Gmail API OAuth2, approval workflow, --dry-run)
- **S6:** ✅ HITL Approval Workflow (24-hour expiry, 5-sec detection, DLQ)
- **S7:** ✅ LinkedIn Posting (Playwright, session recovery, 1 post/day)
- **S8:** ✅ Basic Scheduling (daily briefing 8 AM, weekly audit Sunday 10 PM)
- **S9:** ✅ Agent Skills Documentation (7+ skills in `skills_index.md`)

### 🎯 Gold Tier Features (G1-G12) - 54 Hours Estimated

| ID | Feature | Priority | Hours | Description |
|----|---------|----------|-------|-------------|
| **G1** | Odoo Accounting | P0 | 8h | Self-hosted Odoo Community v19+ with JSON-RPC API |
| **G2** | Facebook Integration | P1 | 4h | Post messages + analytics summaries |
| **G3** | Instagram Integration | P1 | 4h | Post messages + analytics summaries |
| **G4** | Twitter/X Integration | P1 | 4h | Post messages + analytics summaries |
| **G5** | CEO Briefing | P0 | 6h | Weekly business audit with revenue tracking |
| **G6** | Ralph Wiggum Loop | P0 | 6h | Autonomous multi-step task completion |
| **G7** | Multiple MCP Servers | P1 | 4h | Odoo, Social, Browser, Calendar MCPs |
| **G8** | Error Recovery | P1 | 4h | Advanced retry, circuit breaker, fallback |
| **G9** | Audit Logging | P1 | 3h | Enhanced logging with search/reporting |
| **G10** | Cross-Domain | P2 | 4h | Personal + Business unification |
| **G11** | Analytics Dashboard | P2 | 4h | Real-time metrics visualization |
| **G12** | Documentation | P2 | 3h | Architecture, deployment, lessons learned |

### Gold Tier Implementation Phases

1. **Phase 1:** Core Accounting (G1, G5) - 14h - Odoo + CEO Briefing
2. **Phase 2:** Social Media (G2, G3, G4) - 12h - Facebook, Instagram, Twitter
3. **Phase 3:** Autonomous Ops (G6, G8) - 10h - Ralph Wiggum + error recovery
4. **Phase 4:** Infrastructure (G7, G9, G10, G11) - 15h - MCPs, logging, dashboard
5. **Phase 5:** Documentation (G12) - 3h - Complete documentation suite

### Quick Commands for Gold Tier

```bash
# Create Gold Tier branch
git checkout -b 003-gold-tier-autonomous-employee

# Start Gold Tier specification
qwen "Create Gold Tier spec.md per Personal_AI_Employee_Hackathon.md G1-G12"

# Create Gold Tier architecture plan
qwen "Create Gold Tier plan.md with Odoo, social media, Ralph Wiggum architecture"

# Generate Gold Tier tasks
qwen "Generate Gold Tier tasks.md (G1-G12) with acceptance criteria"

# Run quality gates
cd FTE && ruff check src/ && black --check src/ && mypy --strict src/ && pytest --cov=src
```

### Gold Tier Prerequisites

**Technical Setup (before starting):**
- [ ] Install Odoo Community v19+ (2h) - https://www.odoo.com/documentation
- [ ] Facebook Developer Account (1h) - Graph API access
- [ ] Twitter Developer Account (1h) - API v2 access
- [ ] Review Odoo JSON-RPC API docs - https://www.odoo.com/documentation/19.0/developer/reference/external_api.html

**Silver Tier Components (must be operational):**
- ✅ Gmail Watcher running
- ✅ WhatsApp Watcher running
- ✅ Process Manager healthy
- ✅ Approval workflow functional
- ✅ Health endpoint at localhost:8000

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
- **Silver Tier**: Use direct Python integrations (smtplib, requests, playwright) instead of MCP
- **Gold Tier**: Use Python Skills pattern for Odoo (JSON-RPC), social media APIs (Graph API, Twitter API v2)
- **Pattern**: Implement "Python Skills" in `src/skills/` for reusable functionality

### Command Equivalents

| Claude Code | Qwen Code CLI | Notes |
|-------------|---------------|-------|
| `claude "prompt"` | `qwen "prompt"` | Same interactive workflow |
| `/sp.*` commands | `qwen "/sp.*"` | Works via this QWEN.md config |
| MCP filesystem | ❌ Not supported | Use Python `pathlib` directly |
| MCP email | ❌ Not supported | Use Python `smtplib` or `src/skills/send_email.py` |
| MCP Odoo | ❌ Not supported | Use Python `requests` with JSON-RPC |
| MCP Social | ❌ Not supported | Use Python `requests` with Graph/Twitter API |

### Development Workflow

1. **Spec-Driven**: All features follow Spec → Plan → Tasks → Implementation → Tests
2. **Python Skills**: Reusable functions in `src/skills/` replace MCP server functionality
3. **Direct File I/O**: Use Python `pathlib` for vault file operations
4. **Free Tier Aware**: Batch related requests to minimize API call count (1,000/day limit)
5. **Gold Tier Pattern**: External APIs via Python `requests` (Odoo JSON-RPC, Facebook Graph, Twitter API v2)

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

---

## Gold Tier Quick Reference

### Key Resources

| Resource | URL | Purpose |
|----------|-----|---------|
| **Odoo Docs** | https://www.odoo.com/documentation | Odoo Community setup & API |
| **Odoo JSON-RPC** | https://www.odoo.com/documentation/19.0/developer/reference/external_api.html | API reference |
| **Facebook Graph** | https://developers.facebook.com/docs/graph-api | Facebook/Instagram posts |
| **Twitter API v2** | https://developer.twitter.com/en/docs/twitter-api | Twitter/X integration |
| **Why Odoo** | https://chatgpt.com/share/6967deaf-9404-8001-9ad7-03017255ebaf | ERP value proposition |

### Gold Tier Architecture Patterns

**Odoo Integration (G1):**
```python
# Python Skill pattern for Odoo JSON-RPC
import requests

def odoo_rpc_call(model, method, args, kwargs):
    """Call Odoo JSON-RPC API"""
    url = "http://localhost:8069/jsonrpc"
    payload = {
        "jsonrpc": "2.0",
        "method": "call",
        "params": {
            "service": "object",
            "db": "odoo_db",
            "uid": 2,  # admin user
            "password": "admin",
            "model": model,
            "method": method,
            "args": args,
            "kwargs": kwargs
        }
    }
    response = requests.post(url, json=payload)
    return response.json().get("result")
```

**Ralph Wiggum Loop (G6):**
```python
# Stop hook pattern for autonomous iteration
def ralph_wiggum_stop_hook(output, task_file):
    """Intercept Claude exit and re-inject if task incomplete"""
    if not is_task_complete(task_file):
        block_exit()
        reinject_prompt(output)
        return False  # Don't allow exit
    return True  # Allow exit
```

**CEO Briefing Template (G5):**
```markdown
# Monday Morning CEO Briefing

## Executive Summary
[One-paragraph overview]

## Revenue
- **This Week**: $X,XXX
- **MTD**: $X,XXX (XX% of target)
- **Trend**: On track / Behind / Ahead

## Completed Tasks
- [x] Task 1
- [x] Task 2

## Bottlenecks
| Task | Expected | Actual | Delay |
|------|----------|--------|-------|
| ... | ... | ... | ... |

## Proactive Suggestions
### Cost Optimization
- [ACTION] Suggestion

## Upcoming Deadlines
- Project: Date
```

### Gold Tier Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Odoo Integration | 100% invoice workflow | Test suite |
| Social Media Posts | 4 platforms | Manual verification |
| CEO Briefing Accuracy | 95% revenue tracking | User validation |
| Ralph Loop Completion | 90% autonomous tasks | Audit logs |
| Error Recovery | 99% auto-recovery | Chaos tests |
| Test Coverage | 85%+ | pytest --cov |
| Quality Gates | 0 errors | ruff, black, mypy, bandit |

---

**Last Updated**: 2026-04-02
**Silver Tier**: ✅ COMPLETE (v2.0.0)
**Gold Tier**: 🎯 READY TO START (v3.0.0)
**Next Action**: Create Gold Tier branch and spec
