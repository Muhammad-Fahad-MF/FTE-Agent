/sp.tasks # Prompt: Generate Platinum Tier Implementation Tasks

**Command**: `/sp.tasks`
**Feature**: Platinum Tier - Cloud + Local Executive (v6.0.0)
**Spec Reference**: `specs/004-platinum-tier/spec.md`
**Plan Reference**: `specs/004-platinum-tier/plan.md`

---

## Context

**Gold Tier Status**: ✅ Complete (v5.0.0) - All 56 tasks implemented including Odoo accounting, social media integrations (LinkedIn, Gmail, WhatsApp), CEO briefings, Ralph Wiggum loop, and HITL approval workflow.

**Platinum Tier Goal**: Transform Gold Tier's local-only agent into a two-agent architecture:
- **Cloud Agent**: 24/7 always-on monitoring and draft preparation (Oracle Cloud Free Tier VM)
- **Local Agent**: Execution authority, secret storage, user workstation (Windows 10/11)
- **Vault Sync**: Git replication (<60 seconds) with strict security boundaries
- **Security**: Secrets never leave Local (OS Credential Manager), Cloud operates draft-only

**Estimated Implementation**: 60+ hours across 7 Platinum requirements (P1-P7)

**Architecture Summary**:
- **Work-Zone Specialization**: Cloud monitors/drafts, Local approves/executes
- **Claim-by-Move**: Prevents double-work via `/In_Progress/<agent>/` folders
- **Security Boundaries**: Layered defense (.gitignore + pre-sync validation + audit logging)
- **Health Endpoint**: Cloud VM monitoring at `http://<cloud-vm>:8000/health`
- **Cloud Odoo**: Docker Compose deployment with HTTPS, backups, draft-only invoices

---

## Task Generation Requirements

Generate comprehensive implementation tasks (60+ hours) following the Personal_AI_Employee_Hackathon.md patterns:

### 1. Task Structure

Each task MUST include:
- **Task ID**: P1-T001, P1-T002, etc. (organized by Platinum requirement)
- **Title**: 3-7 word descriptive title
- **Description**: Clear, actionable description
- **Acceptance Criteria**: Testable criteria (Given/When/Then format)
- **Estimated Hours**: Realistic time estimate
- **Dependencies**: Links to prerequisite tasks
- **Files**: Expected files to create/modify
- **Tests**: Required tests (unit, integration, chaos)

### 2. Task Categories (P1-P7)

Organize tasks into 7 Platinum requirements:

**P1: Cloud VM Deployment (8 hours)**
- Oracle Cloud VM setup (2 OCPU, 12GB RAM, Ubuntu 22.04)
- Security hardening (UFW, Fail2ban, automatic updates)
- Health endpoint (FastAPI, <500ms response, p95)
- Auto-restart (systemd, <10 seconds)
- Resource monitoring (CPU, memory, disk every 60s)
- Alerting (email/SMS for thresholds)

**P2: Vault Sync (8 hours)**
- Git remote configuration (GitHub/GitLab private repo)
- Sync script (pull/push every 60 seconds)
- Conflict resolution (last-write-wins, local-wins for Dashboard.md)
- Exclusion validation (block .env, tokens/, sessions/, etc.)
- Offline queue management (1000+ pending actions)
- Sync status monitoring (last sync time, conflicts)

**P3: Security Boundaries (8 hours)**
- Secret pattern detection (regex for .env, tokens, etc.)
- Pre-sync validation (block before git add)
- OS Credential Manager integration (Windows)
- Audit logging (all breach attempts)
- Quarantine mechanism (block and alert)
- Security boundary tests (100% detection rate)

**P4: Claim-by-Move (6 hours)**
- Claim file creation (ownership marker)
- Double-work prevention (detect claim, back off)
- Stale claim detection (>5 minutes = reclaimable)
- Cross-agent communication (Updates/, Signals/)
- Claim-by-move tests (100% prevention)

**P5: Cloud Odoo (8 hours)**
- Docker Compose setup (Odoo v19+, PostgreSQL 14)
- HTTPS configuration (Let's Encrypt)
- Draft-only invoice creation (Cloud)
- Invoice posting (Local only)
- Daily backups (encrypted, AES-256)
- Odoo failure fallback (queue drafts)

**P6: Platinum Demo (8 hours)**
- 8-step workflow implementation
- Email arrival detection (Cloud)
- Draft reply creation (Cloud)
- Vault sync (Cloud → Local)
- Local approval workflow
- Local execution (send email)
- Audit trail logging
- End-to-end test (demo validation)

**P7: Documentation (6 hours)**
- Runbooks (Cloud VM setup, vault sync, Odoo deployment)
- Architecture diagrams (ASCII/Mermaid)
- Deployment checklist
- Security disclosure
- Troubleshooting guide

**Testing (8 hours)**
- Unit tests (sync, security, health)
- Integration tests (Cloud/Local workflows)
- Contract tests (API contracts)
- Chaos tests (VM crash, network partition, Odoo failure)
- Load tests (1000+ sync operations)

### 3. Alignment with Hackathon Patterns

Tasks MUST align with Personal_AI_Employee_Hackathon.md patterns:

**Watcher Pattern** (extends Gold Tier):
- Cloud watchers: Gmail (draft-only), WhatsApp (draft-only), FileSystem
- Local watchers: Same + execution watchers
- All extend `BaseWatcher` class
- Check intervals: Gmail (2 min), WhatsApp (30 sec), FileSystem (60 sec)

**Orchestrator Pattern**:
- Dual orchestrators (Cloud + Local) with independent state machines
- Ralph Wiggum loop for autonomous task completion
- Stop hook checks for claim-by-move before allowing exit

**HITL Approval Workflow**:
- Cloud writes to `/Pending_Approval/<domain>/`
- Local reviews and moves to `/Approved/` or `/Rejected/`
- Orchestrator watches `/Approved/` for execution
- 24-hour expiry, re-approval required after expiry

**Dashboard.md Pattern**:
- Single-writer rule (Local only)
- Cloud writes updates to `/Updates/<domain>/`
- Local merges updates into Dashboard.md
- Shows: system status, pending count, recent activity

**Business Handover**:
- Weekly CEO Briefing generation (Monday 8 AM)
- Revenue tracking from Odoo (Cloud drafts, Local posts)
- Bottleneck identification
- Proactive suggestions (cost optimization)

**Python Skills Pattern** (NO MCP for Platinum):
- All AI functionality as Python functions in `src/skills/`, `src/sync/`, `src/security/`
- Skills validate DEV_MODE before execution
- Skills implement audit logging
- Skills support --dry-run mode
- Qwen Code CLI for AI-assisted development (free tier: 1,000 calls/day)

### 4. Task Dependencies

Map task dependencies clearly:
- P1 (Cloud VM) must complete before P3 (Security), P5 (Odoo)
- P2 (Vault Sync) must complete before P4 (Claim-by-Move)
- P1-P5 must complete before P6 (Platinum Demo)
- All implementation tasks before Testing

### 5. Testing Requirements

Each task MUST include test requirements:

**Unit Tests**:
- Vault sync functions (sync, conflict resolution, exclusion)
- Security boundary functions (pattern detection, validation)
- Health endpoint (response time, metrics)
- Claim-by-move (claim detection, stale handling)

**Integration Tests**:
- Cloud/Local workflow (email → draft → sync → approve → send)
- Odoo draft→post workflow
- Approval workflow with expiry
- Sync conflict resolution

**Chaos Tests**:
- Cloud VM crash → auto-restart <10s
- Network partition (4+ hours) → sync queue on reconnect
- Odoo API failure → fallback to draft queue
- Disk exhaustion (>90%) → alert and pause

**Load Tests**:
- 1000+ sync operations without conflicts
- 100+ concurrent claim attempts
- 50 draft creations in 24 hours

### 6. Success Criteria Mapping

Map tasks to spec success criteria (SC-PT-001 to SC-PT-020):

| Success Criteria | Related Tasks |
|------------------|---------------|
| SC-PT-001: 99% uptime | P1-T003 (Health endpoint), P1-T004 (Auto-restart) |
| SC-PT-002: Health <500ms | P1-T003 (Health endpoint) |
| SC-PT-005: Sync <60s | P2-T002 (Sync script) |
| SC-PT-006: Zero secrets synced | P3-T002 (Exclusion validation) |
| SC-PT-009: Cloud 0 sends | P5-T003 (Draft-only invoices) |
| SC-PT-015: 8-step demo | P6-T001 to P6-T008 (Platinum Demo) |
| ... | ... |

### 7. Quality Gates

All tasks MUST pass quality gates before merge:
- **Linting**: ruff check (0 errors)
- **Formatting**: black (line length 100)
- **Type checking**: mypy --strict (0 errors, all signatures typed)
- **Security scan**: bandit (0 high-severity issues)
- **Import order**: isort enforced
- **Test coverage**: 50-60% overall (critical paths 90%+)

### 8. Definition of Done

Each task is complete when:
- [ ] Implementation code written and committed
- [ ] Unit tests passing (if applicable)
- [ ] Integration tests passing (if applicable)
- [ ] Quality gates passing (ruff, black, mypy, bandit)
- [ ] Documentation updated (if applicable)
- [ ] PHR created for implementation work

---

## Task Output Format

Generate tasks.md with this structure:

```markdown
# Implementation Tasks: Platinum Tier - Cloud + Local Executive

**Branch**: `004-platinum-tier`
**Created**: [DATE]
**Status**: Draft
**Spec**: [spec.md](spec.md)
**Plan**: [plan.md](plan.md)
**Total Estimated Hours**: 60+

## Summary

[Brief summary of implementation plan]

## Task List

### P1: Cloud VM Deployment (8 hours)

#### P1-T001: Create Oracle Cloud VM
- **Description**: ...
- **Acceptance Criteria**:
  - Given ... When ... Then ...
- **Estimated Hours**: 1.5
- **Dependencies**: None
- **Files**:
  - `scripts/deploy/setup-cloud-vm.sh`
- **Tests**: None (manual setup)

...

### P2: Vault Sync (8 hours)
...

### P3: Security Boundaries (8 hours)
...

### P4: Claim-by-Move (6 hours)
...

### P5: Cloud Odoo (8 hours)
...

### P6: Platinum Demo (8 hours)
...

### P7: Documentation (6 hours)
...

### Testing (8 hours)
...

## Success Criteria Mapping

[Table mapping tasks to SC-PT-001 to SC-PT-020]

## Quality Gates

[Quality gate requirements]

## Definition of Done

[DoD checklist]
```

---

## Next Steps After Tasks

1. **Review Tasks**: Stakeholder review for completeness and accuracy
2. **Implement**: Task-by-task execution (P1 → P7)
3. **Test**: Run all tests (unit, integration, chaos, load)
4. **Document**: Complete runbooks and deployment guide
5. **Validate**: Platinum Demo (8-step workflow) passes end-to-end
6. **Release**: v6.0.0 Platinum Tier release

---

**Prompt End** - Use this prompt with `/sp.tasks` to generate Platinum Tier implementation tasks.
