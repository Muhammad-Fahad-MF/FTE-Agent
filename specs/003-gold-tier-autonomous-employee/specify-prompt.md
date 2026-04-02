# /sp.specify Prompt: Gold Tier Autonomous Employee

**Feature Name:** Gold Tier Autonomous Employee  
**Tier Level:** Advanced (40+ hours implementation)  
**Based On:** Personal_AI_Employee_Hackathon.md - Gold Tier Requirements  

---

## Prompt for Spec Generation

```
Create a comprehensive specification for implementing the Gold Tier Autonomous Employee feature for the FTE-Agent project.

## Context

We are building a "Digital FTE" (Full-Time Equivalent) - an AI agent that works 24/7 managing personal and business affairs autonomously. The Gold Tier represents a production-ready autonomous employee with full cross-domain integration.

## Gold Tier Requirements (All Must Be Included)

### 1. Full Cross-Domain Integration
- **Personal Domain:** Gmail, WhatsApp, personal banking
- **Business Domain:** Social media (LinkedIn, Twitter/X, Facebook, Instagram), business accounting, project tasks
- **Unified Dashboard:** Single view across all domains in Obsidian

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
- **LinkedIn:** Auto-posting about business updates (1 post/day max)
- **Twitter/X:** Post messages, generate engagement summaries
- **Facebook:** Post updates, monitor page insights
- **Instagram:** Post content, track engagement metrics
- All platforms require:
  - Session preservation/recovery
  - Rate limiting compliance
  - Content approval workflow (HITL)
  - Engagement analytics

### 4. Multiple MCP Servers
Implement dedicated MCP servers for:
- **Email MCP:** Gmail API integration (send, draft, search)
- **WhatsApp MCP:** Playwright-based automation with session management
- **Social Media MCP:** Unified interface for LinkedIn, Twitter, Facebook, Instagram
- **Odoo MCP:** JSON-RPC integration for accounting operations
- **Browser MCP:** General web automation for payment portals
- **Filesystem MCP:** Vault operations (built-in, extend with custom actions)

### 5. Weekly Business & Accounting Audit
- **CEO Briefing Generation:** Every Monday 8 AM
- **Components:**
  - Revenue summary (from Odoo/bank transactions)
  - Expense analysis (categorized)
  - Task completion rate
  - Bottleneck identification
  - Subscription audit (flag unused services)
  - Cash flow projection
  - Proactive suggestions
- **Output:** `/Vault/Briefings/YYYY-MM-DD_Monday_Briefing.md`

### 6. Error Recovery & Graceful Degradation
- **Retry Logic:** Exponential backoff for transient errors (max 3 attempts)
- **Circuit Breakers:** Per-service failure tracking (open after 5 consecutive failures)
- **Dead Letter Queue:** Quarantine failed actions for manual review
- **Graceful Degradation:**
  - Gmail down → Queue emails locally
  - Odoo unavailable → Log transactions to markdown, sync later
  - Social media API rate limit → Schedule for retry, notify user
  - WhatsApp session expired → Alert user, preserve state
- **Auto-Recovery:** Watchdog process restarts failed watchers within 10 seconds

### 7. Comprehensive Audit Logging
- **Log Format:** JSON with schema:
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
- **Retention:** 90 days minimum
- **Location:** `/Vault/Logs/YYYY-MM-DD.json`
- **Daily Rotation:** New file each day
- **Search/Export:** Utility to query logs by date, action, or result

### 8. Ralph Wiggum Loop Implementation
- **Purpose:** Keep Claude working autonomously until task completion
- **Mechanism:** Stop hook that intercepts exit attempts
- **Completion Detection:**
  - File movement to `/Done/` folder
  - Promise tag in output: `<promise>TASK_COMPLETE</promise>`
  - Plan checklist 100% complete
- **Max Iterations:** Configurable (default: 10)
- **State Persistence:** Save progress between iterations
- **Failure Handling:** After max iterations, move to DLQ with status

### 9. Documentation Requirements
- **Architecture Documentation:** `/docs/architecture/gold-tier-architecture.md`
- **API Reference:** All MCP server endpoints documented
- **Setup Guide:** Step-by-step installation and configuration
- **Runbook:** Common operations and troubleshooting
- **Security Disclosure:** Credential handling, HITL boundaries
- **Demo Script:** End-to-end walkthrough of key features

## Additional Specifications

### Security & Privacy
- **Credential Management:** Environment variables + OS secrets manager
- **Never Store:** Tokens, passwords, session data in vault or git
- **HITL Boundaries:**
  - Payments > $100 or new payees → Always require approval
  - Emails to new contacts → Approval required
  - Social media posts → Approval required (first 10 posts auto-approve after training)
  - File deletions → Always require approval
- **Dry Run Mode:** All actions support `--dry-run` flag
- **Rate Limiting:** Configurable per service (emails/hour, posts/day, etc.)

### Performance Budgets
- **Watcher Latency:** Detect new items within 2 minutes (Gmail), 30 seconds (WhatsApp)
- **Claude Response Time:** Generate plan within 60 seconds of trigger
- **Action Execution:** Complete approved actions within 10 seconds
- **Dashboard Refresh:** Update within 5 seconds of action completion
- **System Availability:** 99% uptime (excluding scheduled maintenance)

### Observability
- **Metrics:** Track per-service success rate, latency, throughput
- **Health Endpoint:** `/health` returns status of all components
- **Alerting:** Notify user on:
  - Circuit breaker open
  - DLQ size > 10
  - Watcher restart > 3 times/hour
  - Approval queue size > 20
- **Dashboard Widget:** Real-time system health in `/Vault/Dashboard.md`

### Testing Requirements
- **Unit Tests:** All watcher logic, retry handlers, circuit breakers
- **Integration Tests:** MCP server endpoints, Odoo API calls
- **End-to-End Tests:** Complete workflows (email receive → process → respond)
- **Load Tests:** Handle 100 concurrent actions
- **Endurance Tests:** 24-hour continuous operation
- **Chaos Tests:** Random service failures, network partitions

## Output Format

Generate the following spec document structure:

1. **Executive Summary** (1 paragraph)
2. **Scope** (In/Out of Scope)
3. **Architecture Overview** (diagram + description)
4. **Component Specifications** (detailed for each of the 9 Gold Tier requirements)
5. **Data Models** (schemas for all file types, logs, approvals)
6. **API Contracts** (MCP server interfaces)
7. **Security Model** (authentication, authorization, data handling)
8. **Error Handling** (taxonomy, retry logic, degradation strategies)
9. **Observability** (metrics, logging, alerting)
10. **Performance Requirements** (budgets, benchmarks)
11. **Testing Strategy** (test pyramid, coverage requirements)
12. **Deployment** (installation, configuration, startup)
13. **Operational Runbook** (monitoring, troubleshooting, maintenance)
14. **Appendix** (references, glossary)

## Success Criteria

The spec is complete when:
- [ ] All 9 Gold Tier requirements are specified in detail
- [ ] Each component has clear interfaces and contracts
- [ ] Security boundaries are explicitly defined
- [ ] Error states and recovery strategies are documented
- [ ] Performance budgets are measurable and testable
- [ ] Observability requirements enable debugging production issues
- [ ] Testing strategy covers unit, integration, E2E, and chaos scenarios
- [ ] Deployment instructions enable reproducible setup
- [ ] Operational runbook enables 24/7 autonomous operation with minimal human intervention

## Constraints

- **Local-First:** All data stored locally in Obsidian vault
- **Privacy-Centric:** No sensitive data leaves the system without approval
- **Human-in-the-Loop:** Sensitive actions always require approval
- **Modular Design:** Each MCP server is independently testable and replaceable
- **Free Tier Compatible:** Work within Claude Code free tier limits (1,000 calls/day)
- **Windows Compatible:** All scripts must work on Windows (PowerShell/Python)

## Non-Goals

- Mobile app development
- Multi-user support (single-user only)
- Real-time collaboration features
- Custom LLM training/fine-tuning
- Voice interface integration

```

---

## Usage Instructions

1. **Run the Spec Generation:**
   ```bash
   # Navigate to FTE directory
   cd FTE
   
   # Use this prompt with qwen-code
   qwen "Create a Gold Tier specification per specs/003-gold-tier-autonomous-employee/specify-prompt.md"
   ```

2. **Expected Output:**
   - `specs/003-gold-tier-autonomous-employee/spec.md` (comprehensive specification)
   - `specs/003-gold-tier-autonomous-employee/plan.md` (architecture decisions)
   - `specs/003-gold-tier-autonomous-employee/tasks.md` (implementation tasks)

3. **Implementation Phases:**
   - Phase 1: Foundation (MCP servers, watchers, orchestration)
   - Phase 2: Odoo Integration (accounting system)
   - Phase 3: Social Media (LinkedIn, Twitter, Facebook, Instagram)
   - Phase 4: CEO Briefing (audit logic, report generation)
   - Phase 5: Production Readiness (error recovery, observability, testing)

4. **Estimated Timeline:** 40-60 hours of implementation work

---

## Quick Reference: Gold Tier vs Silver Tier

| Feature | Silver Tier | Gold Tier |
|---------|-------------|-----------|
| Domains | Personal OR Business | Personal + Business (integrated) |
| Accounting | Manual tracking | Odoo integration |
| Social Media | LinkedIn only | LinkedIn + Twitter + Facebook + Instagram |
| MCP Servers | 1-2 basic | 6+ specialized |
| Audit | Basic summary | Full CEO Briefing with analytics |
| Error Handling | Basic retry | Circuit breakers + DLQ + graceful degradation |
| Logging | Simple text | Structured JSON with 90-day retention |
| Autonomy | Single-step tasks | Ralph Wiggum multi-step loops |
| Documentation | Basic README | Full architecture + runbooks |

---

**Next Action:** Use this prompt to generate the Gold Tier specification following the Spec-Driven Development workflow.
