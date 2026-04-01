# Changelog: FTE-Agent

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [2.0.0] - 2026-04-02

### Added - Silver Tier Functional Assistant

#### Multi-Source Monitoring (S1-S3)
- **Gmail Watcher** (`src/watchers/gmail_watcher.py`)
  - Monitor Gmail for unread/important emails every 2 minutes
  - OAuth2 authentication with session preservation
  - Circuit breaker for API calls (trips after 5 failures)
  - Processed ID tracking with SQLite (30-day retention)
  - Rate limiting (100 calls/hour, configurable)
  - Metrics: `gmail_watcher_check_duration`, `gmail_watcher_items_processed`

- **WhatsApp Watcher** (`src/watchers/whatsapp_watcher.py`)
  - Monitor WhatsApp Web for keyword messages every 30 seconds
  - Playwright browser automation with headless mode
  - Keyword filtering (urgent, asap, invoice, payment, help)
  - Session preservation to `vault/whatsapp_session/`
  - Circuit breaker for Playwright operations
  - Graceful session expiry detection

- **Process Manager** (`src/process_manager.py`)
  - Auto-restart crashed watchers within 10 seconds
  - Restart limits (max 3/hour per watcher)
  - Memory monitoring (kill if >200MB)
  - Graceful shutdown on SIGINT/SIGTERM
  - Health monitoring every 10 seconds

- **FileSystem Watcher Extension** (`src/filesystem_watcher.py`)
  - Added metrics emission
  - Added circuit breaker for file operations

#### Human-in-the-Loop Approval (S5-S6)
- **Request Approval Skill** (`src/skills/request_approval.py`)
  - Create approval requests with YAML frontmatter
  - 24-hour expiry with auto-rejection
  - Risk level classification (low, medium, high, critical)
  - Approval file move detection (5-second polling)

- **Approval Handler** (`src/approval_handler.py`)
  - Monitor `vault/Pending_Approval/` for approvals
  - Auto-move to Approved/ or Rejected/ based on user action
  - Integration with Dead Letter Queue for expired approvals

#### Action Skills (S7-S9)
- **Send Email Skill** (`src/skills/send_email.py`)
  - Gmail API integration with OAuth2
  - Support for attachments, CC, BCC
  - Approval required for new contacts
  - `--dry-run` mode for testing
  - Rate limiting (50 emails/hour)

- **LinkedIn Posting Skill** (`src/skills/linkedin_posting.py`)
  - Playwright browser automation
  - Session recovery from `vault/linkedin_session/`
  - 1 post/day limit enforced
  - Visibility options (public, connections, group)
  - `--dry-run` mode

- **Generate Briefing Skill** (`src/skills/generate_briefing.py`)
  - Daily briefing (8 AM)
  - Weekly audit (Sunday 10 PM)
  - Summary generation from action files
  - Output to `vault/Briefings/`

#### Production Utilities (Phase 1)
- **Circuit Breaker** (`src/utils/circuit_breaker.py`)
  - Pybreaker-based implementation
  - SQLite persistence (`data/circuit_breakers.db`)
  - Configurable threshold (default: 5 failures)
  - Auto-recovery timeout (default: 60 seconds)
  - State change logging
  - Decorator and context manager patterns
  - Fallback function support

- **Metrics Collector** (`src/metrics/collector.py`)
  - Prometheus client integration
  - SQLite persistence (`data/metrics.db`)
  - Histogram, counter, gauge, timer types
  - `/metrics` endpoint with Prometheus format
  - Connection pooling (max 5 connections)

- **Log Aggregator** (`src/logging/log_aggregator.py`)
  - JSON logging with correlation_id
  - Daily rotation at 100MB
  - Gzip compression for archived logs
  - Retention policy (7 days INFO, 30 days ERROR)
  - Concurrent write support
  - Async logging (non-blocking)

- **Dead Letter Queue** (`src/utils/dead_letter_queue.py`)
  - SQLite storage (`data/failed_actions.db`)
  - Archive failed actions with metadata
  - Retry tracking (max 3 attempts)
  - Manual reprocessing support
  - File output to `vault/Failed_Actions/`

#### Health Endpoint (S10)
- **FastAPI Health Endpoint** (`src/api/health_endpoint.py`)
  - `GET /health` - Overall system status
  - `GET /metrics` - Prometheus-format metrics
  - `GET /ready` - Readiness check
  - Rate limiting (60 requests/minute)
  - Optional authentication token
  - Component status monitoring

#### Documentation (S13)
- **Runbook** (`docs/runbook.md`)
  - Common issues troubleshooting
  - Escalation policy (4 levels)
  - Maintenance procedures
  - Contact information

- **Disaster Recovery Plan** (`docs/disaster-recovery.md`)
  - Backup strategy (daily vault, weekly credentials)
  - Restore procedures (4 scenarios)
  - RTO=4h, RPO=24h targets
  - Quarterly DR drill requirements

- **Deployment Checklist** (`docs/deployment-checklist.md`)
  - Pre-deployment verification
  - Deployment execution steps
  - Post-deployment validation
  - Rollback procedure

- **API Skills Documentation** (`docs/api-skills.md`)
  - OpenAPI-style specification
  - All 7+ skills documented
  - Error taxonomy
  - Rate limiting table

#### Testing
- **Load Testing** (`tests/load/test_burst_load.py`)
  - 100 emails in 5 minutes scenario
  - p95 <2s, p99 <5s validation
  - Locust-based load generation

- **Endurance Testing** (`tests/endurance/test_7day_simulation.py`)
  - 7-day simulated run in 2 hours
  - Memory leak detection
  - File descriptor leak detection
  - Disk space leak detection

### Changed

- **Vault Structure Extended**
  - Added: `Plans/`, `Pending_Approval/`, `Approved/`, `Rejected/`
  - Added: `Briefings/`, `Templates/`, `Failed_Actions/`
  - Updated `.gitignore` to exclude runtime files

- **Dashboard.md Extended**
  - Watcher status section
  - Circuit breaker states
  - Rate limit usage
  - Memory usage per component

### Fixed

- Path traversal vulnerability in file operations
- Memory leak in Playwright browser contexts
- SQLite connection pool exhaustion under load
- Race condition in approval file detection

### Security

- **DEV_MODE Validation**: All external actions blocked when `DEV_MODE=true`
- **Rate Limiting**: Gmail API (100/hour), WhatsApp (60/hour), LinkedIn (1/day)
- **Circuit Breakers**: All external API calls protected
- **Audit Logging**: All actions logged with correlation_id
- **Credential Management**: OAuth2 tokens stored securely, rotated weekly

### Performance

- Watcher intervals: Gmail (2min ±10s), WhatsApp (30sec ±5s), FileSystem (60sec ±10s)
- Action file creation: p95 <2 seconds
- Approval detection: p95 <5 seconds
- Watcher restart: p95 <10 seconds
- Memory per watcher: <200MB average
- Health check response: p99 <100ms

### Deprecated

- None in this release

### Removed

- None in this release

---

## [1.0.0] - 2026-03-19

### Added - Bronze Tier Foundation

#### Core Components
- **Base Watcher** (`src/base_watcher.py`)
  - Abstract base class for all watchers
  - Common methods: `check_for_updates()`, `create_action_file()`
  - Interval-based scheduling

- **FileSystem Watcher** (`src/filesystem_watcher.py`)
  - Monitor folder for new files using watchdog
  - Create action files in `vault/Needs_Action/`
  - File type detection (invoice, resume, general)

- **Audit Logger** (`src/audit_logger.py`)
  - JSON logging to `vault/Logs/`
  - Correlation ID support
  - Log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL

- **Skills Module** (`src/skills.py`)
  - `create_action_file()`: Create action files
  - `log_audit()`: Write audit entries
  - `validate_path()`: Path traversal prevention
  - `create_alert_file()`: Create critical error alerts

#### Vault Structure
```
vault/
├── Inbox/           # Incoming files
├── Needs_Action/    # Action files
├── Done/            # Completed items
├── Logs/            # Audit logs
└── Dashboard.md     # System status
```

#### Configuration
- **Environment Variables** (`.env`)
  - `DEV_MODE`: Enable/disable external actions
  - `VAULT_PATH`: Base vault directory
  - `LOG_LEVEL`: Logging verbosity

- **Company Handbook** (`Company_Handbook.md`)
  - Configuration settings
  - Watcher intervals
  - Rate limits

#### Testing
- Unit tests for core modules
- Integration tests for file operations
- Quality gates: ruff, black, mypy, bandit, isort

### Security

- DEV_MODE validation for all actions
- Path traversal prevention
- Audit logging for all operations
- STOP file support for emergency halt

### Performance

- FileSystem Watcher interval: 60 seconds
- Action file creation: <1 second
- Log write latency: <10ms

---

## [Unreleased]

### Planned for Gold Tier (3.0.0)
- Multi-tenant support
- Advanced analytics dashboard
- Integration with additional services (Slack, Teams)
- Machine learning for action prioritization
- Mobile app for approvals
- Webhook support for external triggers

### Planned for Platinum Tier (4.0.0)
- Distributed deployment support
- High availability clustering
- Advanced disaster recovery (RTO=1h, RPO=1h)
- Compliance reporting (SOC2, GDPR)
- Enterprise SSO integration

---

## Versioning

This project uses Semantic Versioning (SemVer):
- **MAJOR**: Breaking changes (new tier)
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes (backward compatible)

## Release Schedule

- **Major Releases**: Quarterly (Bronze → Silver → Gold → Platinum)
- **Minor Releases**: Bi-weekly (feature accumulations)
- **Patch Releases**: As needed (critical fixes)

## Support

- **Documentation**: `docs/` directory
- **Issues**: [GitHub Issues](https://github.com/your-org/fte-agent/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-org/fte-agent/discussions)

---

**Latest Version**: 2.0.0 (Silver Tier)  
**Release Date**: 2026-04-02  
**Status**: ✅ Production Ready
