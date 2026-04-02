# Architecture Plan Generation Prompt: Gold Tier Autonomous Employee

**Purpose**: Generate comprehensive architecture decisions and technical plan for Gold Tier implementation

**Spec Reference**: `specs/004-gold-tier-autonomous-employee/spec.md`

**Hackathon Foundation**: `Personal_AI_Employee_Hackathon.md`

---

## Context

You are creating the architecture plan for the **Gold Tier Autonomous Employee** - a production-ready AI agent that works 24/7 managing both personal and business affairs autonomously.

**Tier Level**: Advanced (40+ hours implementation)

**Based On**: Personal_AI_Employee_Hackathon.md - Gold Tier Requirements

## Gold Tier Requirements (From Hackathon Document)

The Gold Tier must deliver all of the following:

### 1. Full Cross-Domain Integration
- **Personal Domain**: Gmail, WhatsApp, personal banking
- **Business Domain**: Social media (LinkedIn, Twitter/X, Facebook, Instagram), business accounting, project tasks
- **Unified Dashboard**: Single view across all domains in Obsidian

### 2. Accounting System Integration (Odoo Community)
- Self-hosted Odoo Community Edition (local or cloud VM)
- Integration via MCP server using Odoo's JSON-RPC APIs (Odoo 19+)
- Features:
  - Invoice generation and tracking
  - Payment reconciliation
  - Expense categorization
  - Financial reporting
  - Tax preparation support
  - Draft-only mode for cloud, approval required for posting

### 3. Social Media Integration
- **LinkedIn**: Auto-posting about business updates (1 post/day max)
- **Twitter/X**: Post messages, generate engagement summaries
- **Facebook**: Post updates, monitor page insights
- **Instagram**: Post content, track engagement metrics
- All platforms require:
  - Session preservation/recovery
  - Rate limiting compliance
  - Content approval workflow (HITL)
  - Engagement analytics

### 4. Multiple MCP Servers
Implement dedicated MCP servers for:
- **Email MCP**: Gmail API integration (send, draft, search)
- **WhatsApp MCP**: Playwright-based automation with session management
- **Social Media MCP**: Unified interface for LinkedIn, Twitter, Facebook, Instagram
- **Odoo MCP**: JSON-RPC integration for accounting operations
- **Browser MCP**: General web automation for payment portals
- **Filesystem MCP**: Vault operations (built-in, extend with custom actions)

### 5. Weekly Business & Accounting Audit
- **CEO Briefing Generation**: Every Monday 8 AM
- **Components**:
  - Revenue summary (from Odoo/bank transactions)
  - Expense analysis (categorized)
  - Task completion rate
  - Bottleneck identification
  - Subscription audit (flag unused services)
  - Cash flow projection
  - Proactive suggestions
- **Output**: `/Vault/Briefings/YYYY-MM-DD_Monday_Briefing.md`

### 6. Error Recovery & Graceful Degradation
- **Retry Logic**: Exponential backoff for transient errors (max 3 attempts)
- **Circuit Breakers**: Per-service failure tracking (open after 5 consecutive failures)
- **Dead Letter Queue**: Quarantine failed actions for manual review
- **Graceful Degradation**:
  - Gmail down → Queue emails locally
  - Odoo unavailable → Log transactions to markdown, sync later
  - Social media API rate limit → Schedule for retry, notify user
  - WhatsApp session expired → Alert user, preserve state
- **Auto-Recovery**: Watchdog process restarts failed watchers within 10 seconds

### 7. Comprehensive Audit Logging
- **Log Format**: JSON with schema:
```json
{
  "timestamp": "ISO8601",
  "action_type": "string",
  "actor": "claude_code|watcher|orchestrator",
  "domain": "personal|business",
  "target": "string",
  "parameters": {},
  "approval_status": "auto|human|none",
  "approved_by": "string|null",
  "result": "success|failure|pending",
  "error": "string|null"
}
```
- **Retention**: 90 days minimum
- **Location**: `/Vault/Logs/YYYY-MM-DD.json`
- **Daily Rotation**: New file each day
- **Search/Export**: Utility to query logs by date, action, or result

### 8. Ralph Wiggum Loop Implementation
- **Purpose**: Keep Claude working autonomously until task completion
- **Mechanism**: Stop hook that intercepts exit attempts
- **Completion Detection**:
  - File movement to `/Done/` folder
  - Promise tag in output: `<promise>TASK_COMPLETE</promise>`
  - Plan checklist 100% complete
- **Max Iterations**: Configurable (default: 10)
- **State Persistence**: Save progress between iterations
- **Failure Handling**: After max iterations, move to DLQ with status

### 9. Documentation Requirements
- **Architecture Documentation**: `/docs/architecture/gold-tier-architecture.md`
- **API Reference**: All MCP server endpoints documented
- **Setup Guide**: Step-by-step installation and configuration
- **Runbook**: Common operations and troubleshooting
- **Security Disclosure**: Credential handling, HITL boundaries
- **Demo Script**: End-to-end walkthrough of key features

## Additional Specifications (From Hackathon)

### Security & Privacy
- **Credential Management**: Environment variables + OS secrets manager
- **Never Store**: Tokens, passwords, session data in vault or git
- **HITL Boundaries**:
  - Payments > $100 or new payees → Always require approval
  - Emails to new contacts → Approval required
  - Social media posts → Approval required (first 10 posts auto-approve after training)
  - File deletions → Always require approval
- **Dry Run Mode**: All actions support `--dry-run` flag
- **Rate Limiting**: Configurable per service (emails/hour, posts/day, etc.)

### Performance Budgets (From Hackathon Architecture)
- **Watcher Latency**: Detect new items within 2 minutes (Gmail), 30 seconds (WhatsApp)
- **Claude Response Time**: Generate plan within 60 seconds of trigger
- **Action Execution**: Complete approved actions within 10 seconds
- **Dashboard Refresh**: Update within 5 seconds of action completion
- **System Availability**: 99% uptime (excluding scheduled maintenance)

### Observability
- **Metrics**: Track per-service success rate, latency, throughput
- **Health Endpoint**: `/health` returns status of all components
- **Alerting**: Notify user on:
  - Circuit breaker open
  - DLQ size > 10
  - Watcher restart > 3 times/hour
  - Approval queue size > 20
- **Dashboard Widget**: Real-time system health in `/Vault/Dashboard.md`

### Testing Requirements
- **Unit Tests**: All watcher logic, retry handlers, circuit breakers
- **Integration Tests**: MCP server endpoints, Odoo API calls
- **End-to-End Tests**: Complete workflows (email receive → process → respond)
- **Load Tests**: Handle 100 concurrent actions
- **Endurance Tests**: 24-hour continuous operation
- **Chaos Tests**: Random service failures, network partitions

## Architecture Patterns From Hackathon

### Perception → Reasoning → Action Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   PERCEPTION    │────▶│    REASONING    │────▶│     ACTION      │
│   (Watchers)    │     │  (Claude Code)  │     │   (MCP Servers) │
└─────────────────┘     └─────────────────┘     └─────────────────┘
       │                       │                       │
       ▼                       ▼                       ▼
- Gmail Watcher         - Reads Inbox/        - Email MCP
- WhatsApp Watcher        Needs_Action        - WhatsApp MCP
- Social Media Watcher  - Creates Plan.md     - Social Media MCP
- Odoo Watcher          - Ralph Wiggum Loop   - Odoo MCP
- Filesystem Watcher    - HITL Decisions      - Browser MCP
                                                - Filesystem MCP
```

### Watcher Pattern (From Hackathon)

All watchers must follow the base pattern:
- Inherit from `BaseWatcher` class
- Implement `check_for_updates()` abstract method
- Implement `create_action_file()` abstract method
- Run in continuous loop with configurable interval
- Write to `/Needs_Action/` folder with YAML frontmatter

### Ralph Wiggum Loop Pattern

Two completion strategies:
1. **Promise-based**: Claude outputs `<promise>TASK_COMPLETE</promise>`
2. **File movement**: Stop hook detects file moved to `/Done/` folder

### Human-in-the-Loop Pattern

For sensitive actions:
1. Claude writes approval request to `/Pending_Approval/`
2. User moves file to `/Approved/` or `/Rejected/`
3. Orchestrator triggers MCP action on approval

## Output Format

Generate the following `plan.md` structure:

### 1. Executive Summary
- 1-paragraph overview of architecture approach
- Key architectural decisions summary

### 2. System Architecture
- High-level component diagram
- Data flow description
- Integration points

### 3. Component Architecture
For each of the 9 Gold Tier requirements:
- Component description
- Interfaces and contracts
- Dependencies
- Failure modes

### 4. MCP Server Architecture
For each MCP server (6 total):
- Server purpose
- Endpoints/capabilities
- Authentication method
- Error handling

### 5. Watcher Architecture
For each watcher (Gmail, WhatsApp, Social Media, Odoo, Filesystem):
- Watcher purpose
- Check interval
- Action file format
- Error recovery

### 6. Data Architecture
- Vault folder structure
- File schemas (action files, approval requests, logs, briefings)
- Data retention policies
- Backup strategy

### 7. Security Architecture
- Credential storage strategy
- HITL boundaries implementation
- Audit logging approach
- Privacy safeguards

### 8. Error Handling Architecture
- Retry logic implementation
- Circuit breaker design
- Dead Letter Queue structure
- Graceful degradation strategies

### 9. Observability Architecture
- Metrics collection approach
- Health endpoint design
- Alerting thresholds and channels
- Dashboard widget implementation

### 10. Deployment Architecture
- Local deployment (workstation)
- Cloud deployment considerations (for Platinum tier)
- Startup sequence
- Health checks

### 11. Implementation Phases
Break down into 5 phases (matching spec):
- Phase 1: Foundation (MCP servers, watchers, orchestration)
- Phase 2: Odoo Integration (accounting system)
- Phase 3: Social Media (LinkedIn, Twitter, Facebook, Instagram)
- Phase 4: CEO Briefing (audit logic, report generation)
- Phase 5: Production Readiness (error recovery, observability, testing)

### 12. Key Architectural Decisions
Document significant decisions with:
- Decision statement
- Options considered
- Rationale
- Consequences

### 13. Risks and Mitigations
- Top 5 technical risks
- Mitigation strategies
- Contingency plans

### 14. Open Questions
- Unresolved architectural questions
- Decisions requiring user input
- Research needed

## Constraints

From the hackathon document:

- **Local-First**: All data stored locally in Obsidian vault
- **Privacy-Centric**: No sensitive data leaves the system without approval
- **Human-in-the-Loop**: Sensitive actions always require approval
- **Modular Design**: Each MCP server is independently testable and replaceable
- **Free Tier Compatible**: Work within Claude Code free tier limits (1,000 calls/day)
- **Windows Compatible**: All scripts must work on Windows (PowerShell/Python)

## Non-Goals

From the hackathon document:

- Mobile app development
- Multi-user support (single-user only)
- Real-time collaboration features
- Custom LLM training/fine-tuning
- Voice interface integration

## Success Criteria for Plan

The plan is complete when:

- [ ] All 9 Gold Tier requirements have detailed component architecture
- [ ] Each MCP server has clear interface definitions
- [ ] Watcher patterns are fully specified with code templates
- [ ] Data schemas are defined for all file types
- [ ] Security boundaries are explicitly documented
- [ ] Error handling strategies are actionable
- [ ] Observability approach enables production debugging
- [ ] Implementation phases are sequenced logically
- [ ] Key architectural decisions are documented with rationale
- [ ] Risks are identified with mitigation strategies
- [ ] Plan enables task generation (tasks.md) without ambiguity

## Special Considerations

### Bronze/Silver/Gold/Platinum Tier Progression

This plan focuses on **Gold Tier** but should acknowledge:
- Bronze foundation (single watcher, basic vault)
- Silver extensions (2+ watchers, one MCP, basic HITL)
- Gold full implementation (all 9 requirements)
- Platinum cloud deployment (future upgrade path)

### Hackathon Timeline

- **Wednesday Research Meetings**: 10:00 PM Zoom (teaching each other)
- **Estimated Implementation**: 40-60 hours for Gold Tier
- **Demo Requirement**: End-to-end walkthrough of key features

### Faculty/Student Collaboration

All participants will build this Personal AI Employee using Claude Code. The architecture should support:
- Teaching/learning progression
- Incremental complexity
- Reusable patterns across tiers

---

**Your Task**: Generate `specs/004-gold-tier-autonomous-employee/plan.md` following the structure above, incorporating all patterns and requirements from both the spec.md and the Personal_AI_Employee_Hackathon.md document.

Ensure the architecture is:
1. **Actionable**: Developers can implement from this plan
2. **Testable**: Each component has clear validation criteria
3. **Modular**: Components can be built/tested independently
4. **Documented**: All decisions include rationale
5. **Pragmatic**: Balances ideal architecture with hackathon timeline
