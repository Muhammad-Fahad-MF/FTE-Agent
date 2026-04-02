# Prompt for /sp.constitution: Gold Tier Constitution Update

**Copy and paste this entire prompt into Qwen Code CLI:**

```
/sp.constitution Update constitution.md for Gold Tier Autonomous Employee (v5.0.0)

## Context

Silver Tier (v4.0.0) is COMPLETE with all 115 tasks implemented and tested. We are now starting Gold Tier development (branch: 003-gold-tier-autonomous-employee).

Current constitution version 4.0.0 supports Silver Tier but has critical gaps for Gold Tier requirements.

## Gold Tier Features (G1-G12) Requiring Constitution Support

### P0 Features (Core Gold Tier)
- **G1: Odoo Accounting** - Self-hosted Odoo Community v19+ with JSON-RPC API integration
- **G5: CEO Briefing** - Weekly business audit with revenue tracking from Odoo/bank data
- **G6: Ralph Wiggum Loop** - Autonomous multi-step task completion with stop hook pattern

### P1 Features (Infrastructure)
- **G2-G4: Social Media** - Facebook, Instagram, Twitter/X posting with analytics
- **G7: Multiple MCP Servers** - 5+ coordinated MCP servers (Odoo, Social, Browser, Calendar, Email)
- **G8: Error Recovery** - Advanced retry, fallback queues, graceful degradation
- **G9: Audit Logging** - Enhanced logging with search/query and reporting

### P2 Features (Advanced)
- **G10: Cross-Domain** - Personal + Business domain unification
- **G11: Analytics Dashboard** - Real-time metrics visualization
- **G12: Documentation** - Complete architecture and deployment guides

## Required Constitution Updates

### 1. Add Gold Tier Architecture Section (NEW)

Add a new section after "Silver Tier Architecture" with:

**Gold Tier Architecture Diagram:**
```
┌─────────────────────────────────────────────────────────────┐
│ GOLD TIER: AUTONOMOUS EMPLOYEE                              │
├─────────────────────────────────────────────────────────────┤
│ PERCEPTION LAYER (Extended)                                 │
│ - Gmail, WhatsApp, FileSystem (Silver)                      │
│ - Odoo Webhooks (NEW)                                       │
│ - Bank Transaction Feeds (NEW)                              │
│ - Social Media Mentions (NEW)                               │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│ REASONING LAYER (Extended)                                  │
│ - Qwen Code CLI + Ralph Wiggum Loop (NEW)                   │
│ - Multi-step autonomous task completion                     │
│ - State file management (/In_Progress/<agent>/)             │
│ - Task completion detection (/Done/)                        │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│ ACTION LAYER (Extended)                                     │
│ - Python Skills (Silver)                                    │
│ - MCP Servers (5+ coordinated):                             │
│   * Odoo MCP (invoices, payments, accounting)               │
│   * Social MCP (Facebook, Instagram, Twitter)               │
│   * Browser MCP (Playwright automation)                     │
│   * Calendar MCP (scheduling, meetings)                     │
│   * Email MCP (Gmail API)                                   │
│ - MCP Coordinator (NEW - prevents double-execution)         │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│ CEO BRIEFING ENGINE (NEW)                                   │
│ - Revenue tracking from Odoo/bank data                      │
│ - Expense categorization and analysis                       │
│ - Bottleneck identification                                 │
│ - Proactive suggestions generation                          │
│ - Output: vault/Briefings/CEO_Briefing_YYYYMMDD.md          │
└─────────────────────────────────────────────────────────────┘
```

**Ralph Wiggum Loop Pattern:**
- State file creation: `/In_Progress/<agent>/<task-id>.md`
- Stop hook intercepts Claude exit
- Re-inject prompt if task file not in `/Done/`
- Max iterations: 10 (configurable)
- State persistence across restarts

**Multi-MCP Coordination:**
- Single coordinator process prevents double-execution
- MCP servers isolated (failure doesn't cascade)
- Shared audit logging across all MCPs
- Health monitoring per MCP server

### 2. Update Principle I: Security-First Automation

**Add Gold Tier Extension:**

**Gold Tier Extension**: CEO Briefing MUST include revenue tracking with data sourced from Odoo (self-hosted, local) or bank APIs. All financial data MUST be encrypted at rest. Ralph Wiggum loop MUST implement max iterations (default: 10) with state persistence. Multi-MCP coordination MUST prevent double-execution via distributed locking. Cross-domain data (personal vs business) MUST be tagged and separable in all reports.

### 3. Update Principle VIII: Production-Grade Error Handling

**Add Gold Tier Extension:**

**Gold Tier Extension**: Odoo JSON-RPC calls MUST implement timeout (30 seconds), retry with exponential backoff (1s, 2s, 4s; max 3 retries), and circuit breaker (trip after 5 failures, reset after 300 seconds). Social media API calls (Facebook Graph, Twitter API v2) MUST implement platform-specific rate limit handling (Facebook: 200 calls/hour, Twitter: 300 calls/15min). Fallback mechanisms REQUIRED: when Odoo unavailable, queue invoices in memory; when social media API fails, save draft posts to `/Drafts/`. All MCP server failures MUST be isolated (one MCP failure doesn't affect others).

### 4. Update Principle XIII: AI Reasoning Engine & Python Skills Pattern

**Update Tier Progression Table:**

| Tier | Python Skills Scope | External Dependencies | MCP Servers |
|------|---------------------|----------------------|-------------|
| **Bronze** | File operations only | `watchdog`, `pathlib` | None |
| **Silver** | Email, Web automation, HTTP APIs, Plan generation, Approval workflow | `playwright`, `google-auth`, `requests` | Optional (Email, Browser) |
| **Gold** | Odoo accounting, Social media APIs, Bank integrations, CEO Briefing, Ralph Wiggum loop | Odoo v19+, Facebook Graph API, Twitter API v2, banking APIs | Required (5+: Odoo, Social, Browser, Calendar, Email) |

**Add Ralph Wiggum Pattern Documentation:**

```python
# Ralph Wiggum Stop Hook Pattern (Gold Tier MANDATORY)

def ralph_wiggum_stop_hook(output: str, task_file: Path) -> bool:
    """
    Intercept Claude exit and re-inject prompt if task incomplete.
    
    Returns:
        True: Allow exit (task complete)
        False: Block exit, re-inject prompt (task incomplete)
    """
    if not is_task_complete(task_file):
        block_exit()
        reinject_prompt(output)
        return False
    return True

# State file pattern:
# /In_Progress/<agent>/<task-id>.md
# - Created when task starts
# - Updated with progress every iteration
# - Moved to /Done/ when complete
# - Max iterations: 10 (configurable in Company_Handbook.md)
```

### 5. Update Technology Stack Section

**Add Gold Tier Dependencies:**

### Gold Tier Dependencies (MANDATORY for G1-G12)
- **Accounting Integration**: 
  - Odoo Community Edition v19+ (self-hosted, local or Docker)
  - JSON-RPC client: `requests>=2.31.0` with custom Odoo RPC wrapper
  - Database: PostgreSQL 14+ (Odoo backend)
  - Setup time: 2 hours (install + configure)
  
- **Social Media APIs**:
  - Facebook Graph API v18.0+ (requires Facebook Developer Account, 1h setup)
  - Instagram Graph API v18.0+ (requires Facebook Business integration)
  - Twitter API v2 (requires Twitter Developer Account, 1h setup; free tier: 1,500 posts/month)
  - LinkedIn API (browser automation via Playwright, no API key required)
  
- **Banking Integration** (for CEO Briefing revenue tracking):
  - Bank API clients (platform-specific) OR
  - CSV import pattern (manual download, automated parsing)
  - Plaid API (optional, for US banks)
  
- **Multi-MCP Coordination**:
  - Node.js v24+ (for MCP server implementations)
  - `@modelcontextprotocol/sdk` for MCP server development
  - Redis (optional, for distributed locking across MCPs)
  
- **Analytics & Visualization**:
  - `prometheus-client>=0.19.0` for metrics exposition
  - `matplotlib>=3.8.0` or `plotly>=5.18.0` for chart generation (Markdown-compatible)
  - SQLite (for metrics persistence, already in Silver)

### 6. Update Directory Structure

**Add Gold Tier Directories:**

```
src/
  ├── ralph_wiggum/         # [GOLD] Ralph Wiggum loop implementation
  │   ├── stop_hook.py        # Stop hook interceptor
  │   ├── state_manager.py    # State file management (/In_Progress/)
  │   └── iteration_tracker.py # Max iterations, retry logic
  ├── mcp_coordinator/      # [GOLD] Multi-MCP coordination
  │   ├── coordinator.py      # Prevents double-execution
  │   ├── health_monitor.py   # MCP health checks
  │   └── distributed_lock.py # Locking for concurrent MCPs
  ├── ceo_briefing/         # [GOLD] CEO Briefing engine
  │   ├── revenue_tracker.py  # Revenue calculation from Odoo/bank
  │   ├── expense_analyzer.py # Expense categorization
  │   ├── bottleneck_detector.py # Identify delays
  │   └── suggestion_generator.py # Proactive recommendations
  └── cross_domain/         # [GOLD] Personal + Business unification
      ├── domain_tagger.py    # Tag actions as personal/business
      └── unified_dashboard.py # Combined view generation

mcp_servers/
  ├── odoo_mcp/             # [GOLD] Odoo JSON-RPC wrapper
  ├── social_mcp/           # [GOLD] Facebook, Instagram, Twitter
  ├── browser_mcp/          # [SILVER] Playwright automation
  ├── calendar_mcp/         # [GOLD] Calendar integration
  └── email_mcp/            # [SILVER] Gmail API

data/
  ├── odoo.db               # [GOLD] Odoo SQLite/PostgreSQL
  ├── revenue.db            # [GOLD] Revenue tracking cache
  └── analytics.db          # [GOLD] Analytics data store

vault/
  ├── In_Progress/          # [GOLD] Ralph Wiggum state files
  │   └── <agent>/            # Per-agent state directories
  ├── Drafts/               # [GOLD] Draft posts, invoices
  ├── Briefings/
  │   ├── Daily_*.md        # [SILVER] Daily briefings
  │   ├── Weekly_*.md       # [SILVER] Weekly audits
  │   └── CEO_Briefing_*.md # [GOLD] CEO briefings with revenue
  └── Analytics/            # [GOLD] Charts, metrics reports
```

### 7. Add Gold Tier Safety Validation Checklist

**Replace "Gold Tier (Future - Not Required for Silver)" section with:**

### Gold Tier (REQUIRED for Gold Completion - All Must Pass)

**Odoo Accounting (G1):**
- [ ] Odoo Community v19+ installed and running locally (or Docker container)
- [ ] JSON-RPC connection established (test: create invoice via API)
- [ ] Invoice creation via MCP/Skill works (dry-run verified)
- [ ] Payment tracking updates invoice status
- [ ] Financial reports generated (P&L, balance sheet)
- [ ] Bank transaction import and categorization functional

**Social Media Integration (G2-G4):**
- [ ] Facebook post creation with approval workflow
- [ ] Instagram post creation (images, carousels) with approval
- [ ] Twitter/X tweet creation with approval workflow
- [ ] Analytics retrieval for all platforms (reach, engagement)
- [ ] Weekly summary reports generated automatically

**CEO Briefing (G5):**
- [ ] Weekly audit runs Sunday 10 PM automatically
- [ ] Revenue data pulled from Odoo/bank integration
- [ ] Expense analysis with subscription audit
- [ ] Bottleneck identification (tasks taking too long)
- [ ] Proactive suggestions generated (cost optimization)
- [ ] Briefing format matches template (Executive Summary, Revenue, Tasks, Bottlenecks, Suggestions)

**Ralph Wiggum Loop (G6):**
- [ ] Stop hook intercepts Claude exit correctly
- [ ] State files created in `/In_Progress/<agent>/`
- [ ] Task completion detection (file moved to `/Done/`)
- [ ] Max iterations enforced (default: 10)
- [ ] State persists across application restarts
- [ ] Loop recovery after crash (state file not lost)

**Multi-MCP Coordination (G7):**
- [ ] 5+ MCP servers configured and operational (Odoo, Social, Browser, Calendar, Email)
- [ ] MCP Coordinator prevents double-execution
- [ ] MCP servers isolated (one failure doesn't affect others)
- [ ] Centralized audit logging across all MCPs
- [ ] Health monitoring per MCP server (status page)

**Error Recovery (G8):**
- [ ] All external calls have retry logic with exponential backoff
- [ ] Circuit breakers prevent cascade failures (trip after 5 failures)
- [ ] Fallback mechanisms in place (in-memory queue, draft files)
- [ ] Alert escalation working (4 levels: log → dashboard → alert file → notify)
- [ ] Chaos test: Kill one MCP, verify others continue operating

**Audit Logging (G9):**
- [ ] Enhanced log schema implemented (timestamp, level, component, action, correlation_id, user, details, duration_ms, result)
- [ ] Log search utility functional (query by date, component, action, correlation_id)
- [ ] Log reporting (daily/weekly summaries) generated
- [ ] 90-day log retention enforced

**Cross-Domain (G10):**
- [ ] Domain tagging on all action files (personal vs business)
- [ ] Unified Dashboard.md with domain sections
- [ ] Cross-domain workflows supported (personal email → business lead)
- [ ] Domain filtering in reports

**Analytics Dashboard (G11):**
- [ ] Real-time metrics dashboard (watcher uptime, action completion rate, approval stats, error rates)
- [ ] Visual charts in Dashboard.md (Markdown-compatible)
- [ ] Export functionality (PDF reports, CSV data)

**Documentation (G12):**
- [ ] Gold Tier Architecture document complete (`docs/gold-tier-architecture.md`)
- [ ] Deployment guide complete (`docs/gold-deployment.md`)
- [ ] API Reference complete (`docs/gold-api-reference.md`)
- [ ] Lessons Learned captured (`docs/gold-lessons-learned.md`)

**Integration Tests:**
- [ ] End-to-end: Odoo invoice → CEO Briefing revenue tracking
- [ ] End-to-end: Social media post → Analytics summary
- [ ] End-to-end: Ralph Wiggum loop completes 5-step task autonomously
- [ ] Multi-MCP: 3 MCPs operate concurrently without interference

**Chaos Tests:**
- [ ] Odoo API failure: Verify fallback to draft invoices
- [ ] Social media API rate limit: Verify queuing and retry
- [ ] MCP crash: Verify coordinator detects and continues with remaining MCPs
- [ ] Ralph Wiggum max iterations: Verify graceful halt with state preserved

### 8. Add Gold Tier Performance Budgets

**Add to Principle XII:**

**Gold Tier Extension**: Odoo JSON-RPC calls MUST complete within 5 seconds (excluding external API latency). CEO Briefing generation MUST complete within 60 seconds. Ralph Wiggum iteration MUST complete within 30 seconds per loop. Multi-MCP coordination overhead MUST NOT exceed 100ms. Analytics dashboard refresh MUST complete within 5 seconds. Cross-domain queries MUST complete within 2 seconds.

### 9. Add Gold Tier Emergency Procedures

**Add to Emergency Procedures:**

- **Odoo unavailable**: Queue invoices in `/Drafts/`, retry after 5 minutes, alert user after 3 failures
- **Social media API rate limited**: Save post as draft, schedule retry after rate limit reset (Facebook: 1 hour, Twitter: 15 minutes)
- **Ralph Wiggum infinite loop detected**: Max iterations reached, preserve state, create alert file in `Needs_Action/`
- **MCP Coordinator failure**: All MCPs pause, coordinator restarts within 10 seconds, queued requests processed
- **CEO Briefing generation fails**: Create alert file, retry next scheduled run, notify user of missing data

### 10. Update Version and Governance

**Update version reference:**

**Version**: 5.0.0 | **Ratified**: 2026-04-02 | **Last Amended**: 2026-04-02 (Gold Tier preparation)

**Add to Governance:**

Gold Tier amendments require:
1. Odoo Community v19+ setup and testing (2 hours)
2. Facebook Developer Account setup (1 hour)
3. Twitter Developer Account setup (1 hour)
4. Ralph Wiggum pattern validation (autonomous task completion test)
5. Multi-MCP coordination test (5+ MCPs running concurrently)

## Implementation Instructions

1. **Create backup**: Copy `.specify/memory/constitution.md` to `.specify/memory/constitution.md.v4.0.0.backup`
2. **Update systematically**: Apply all 10 updates above in order
3. **Validate**: Run `grep -i "gold tier" .specify/memory/constitution.md` to verify all mentions updated
4. **Test**: Verify all Gold Tier validation checklist items are testable
5. **Commit**: Create commit with message "feat: Update constitution for Gold Tier Autonomous Employee (v5.0.0)"

## Acceptance Criteria

- [ ] All 10 update sections implemented
- [ ] Gold Tier Architecture diagram included (ASCII art)
- [ ] Ralph Wiggum pattern documented with code example
- [ ] Multi-MCP coordination pattern documented
- [ ] CEO Briefing data model specified
- [ ] Gold Tier dependencies listed with versions
- [ ] Gold Tier validation checklist complete (all G1-G12 items)
- [ ] Performance budgets added for Gold Tier features
- [ ] Emergency procedures extended for Gold Tier
- [ ] Version updated to 5.0.0
- [ ] No Silver Tier functionality broken (backward compatible)
- [ ] All Gold Tier features are testable via checklist items

## Output

After completion, provide:
1. Summary of changes made
2. New file paths created (if any)
3. Modified sections list
4. Version change confirmation (4.0.0 → 5.0.0)
5. Next steps for Gold Tier spec/plan/tasks generation
```

---

## How to Use This Prompt

1. **Copy the entire prompt above** (from `/sp.constitution` to the end)

2. **Run in Qwen Code CLI:**
   ```bash
   qwen
   # Then paste the entire prompt
   ```

3. **Review the changes** before committing:
   ```bash
   git diff .specify/memory/constitution.md
   ```

4. **Create PHR** after completion:
   ```bash
   qwen "Create PHR for constitution.md Gold Tier update in history/prompts/constitution/"
   ```

5. **Next step** after constitution update:
   ```bash
   qwen "Create Gold Tier spec.md per Personal_AI_Employee_Hackathon.md G1-G12"
   ```

---

**Rationale for Comprehensive Prompt:**

This prompt is designed to:
- **Minimize AI hallucination** by providing exact content to add
- **Ensure completeness** by covering all 10 required update areas
- **Maintain backward compatibility** by preserving Silver Tier functionality
- **Enable immediate Gold Tier development** with complete architecture guidance
- **Provide testable acceptance criteria** for validation

The prompt includes ASCII diagrams, code examples, checklists, and specific version requirements to eliminate ambiguity.
