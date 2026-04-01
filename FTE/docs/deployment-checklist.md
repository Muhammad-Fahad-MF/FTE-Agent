# Deployment Checklist: Silver Tier Functional Assistant

**Version**: 2.0.0  
**Last Updated**: 2026-04-02  
**Owner**: FTE-Agent Team  
**Classification**: Production Critical

---

## Deployment Types

| Type | Frequency | Scope | Approval Required |
|------|-----------|-------|-------------------|
| **Initial Deployment** | One-time | Full system | Product Owner, Security |
| **Feature Deployment** | Per sprint | New features (Silver → Gold) | Technical Lead |
| **Hotfix Deployment** | As needed | Critical bug fixes | Technical Lead |
| **Scheduled Deployment** | Bi-weekly | Accumulated features | Product Owner |

---

## Pre-Deployment Checklist

### Environment Verification

- [ ] **Target Environment Identified**
  - [ ] Development (DEV)
  - [ ] Staging (STG)
  - [ ] Production (PROD)
  - [ ] Environment variable `ENVIRONMENT` set correctly

- [ ] **System Requirements Met**
  - [ ] Windows 10/11 or Linux/Mac
  - [ ] Python 3.13+ installed: `python --version`
  - [ ] 8GB+ RAM available
  - [ ] 256GB+ free disk space
  - [ ] Network access to external APIs (Gmail, WhatsApp Web, LinkedIn)

- [ ] **Dependencies Installed**
  ```bash
  cd H:\Programming\FTE-Agent\FTE
  pip install -r requirements.txt
  pip list | Select-String "watchdog|playwright|google-auth|fastapi|prometheus"
  ```
  - [ ] All packages installed without errors
  - [ ] Playwright browsers installed: `playwright install`

---

### Code Quality Gates

- [ ] **Linting Passes**
  ```bash
  ruff check src/ tests/ --select E,F,W,I,N,B,C4
  ```
  - [ ] 0 errors
  - [ ] 0 warnings (or documented exceptions)

- [ ] **Formatting Correct**
  ```bash
  black --check src/ tests/ --line-length 100
  ```
  - [ ] All files formatted correctly

- [ ] **Type Checking Passes**
  ```bash
  mypy --strict src/ --no-error-summary
  ```
  - [ ] 0 type errors
  - [ ] All functions have type annotations

- [ ] **Import Order Correct**
  ```bash
  isort --check-only src/ tests/
  ```
  - [ ] 0 errors

- [ ] **Security Scan Passes**
  ```bash
  bandit -r src/ --format custom
  ```
  - [ ] 0 high-severity issues
  - [ ] 0 medium-severity issues (or documented exceptions)

---

### Testing Requirements

- [ ] **Unit Tests Pass**
  ```bash
  pytest tests/unit/ -v --cov=src --cov-report=term-missing
  ```
  - [ ] All tests pass (0 failures)
  - [ ] Coverage ≥80%
  - [ ] No new coverage gaps introduced

- [ ] **Integration Tests Pass**
  ```bash
  pytest tests/integration/ -v
  ```
  - [ ] All tests pass (0 failures)
  - [ ] External API calls mocked or use test credentials

- [ ] **Chaos Tests Pass** (if applicable)
  ```bash
  pytest tests/chaos/ -v
  ```
  - [ ] System recovers from injected failures

- [ ] **Load Tests Pass** (for production deployments)
  ```bash
  pytest tests/load/ -v
  ```
  - [ ] p95 latency <2 seconds
  - [ ] p99 latency <5 seconds
  - [ ] Error rate <1%

- [ ] **Endurance Tests Pass** (for production deployments)
  ```bash
  pytest tests/endurance/ -v
  ```
  - [ ] No memory leaks
  - [ ] No file descriptor leaks
  - [ ] Stable performance over time

---

### Security Verification

- [ ] **Credentials Secured**
  - [ ] `.env` file exists and is NOT in git
  - [ ] `.env.example` updated with new variables
  - [ ] No hardcoded secrets in source code
  - [ ] OAuth2 tokens stored securely

- [ ] **DEV_MODE Validation**
  - [ ] `DEV_MODE=false` in production
  - [ ] `DEV_MODE=true` in development/staging
  - [ ] External actions blocked when `DEV_MODE=true`

- [ ] **Path Validation**
  - [ ] All file operations use absolute paths
  - [ ] Path traversal prevention implemented
  - [ ] Symlink attacks prevented

- [ ] **Rate Limiting Configured**
  - [ ] Gmail API: max 100 calls/hour
  - [ ] WhatsApp: max 60 checks/hour
  - [ ] LinkedIn: max 1 post/day

- [ ] **Circuit Breakers Configured**
  - [ ] Failure threshold: 5 consecutive failures
  - [ ] Recovery timeout: 60 seconds
  - [ ] State persists to SQLite

---

### Backup & Rollback Preparation

- [ ] **Pre-Deployment Backup Created**
  ```powershell
  # Create backup
  $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
  robocopy "H:\Programming\FTE-Agent\FTE" "H:\Backups\FTE-Agent\pre-deploy_$timestamp" /MIR /XD .git .pytest_cache .ruff_cache /XF *.log
  ```
  - [ ] Vault backed up
  - [ ] Databases backed up
  - [ ] Configuration backed up
  - [ ] Backup checksum generated

- [ ] **Rollback Plan Documented**
  - [ ] Rollback command tested in staging
  - [ ] Rollback time estimated <30 minutes
  - [ ] Rollback approval obtained (if production)

- [ ] **Database Migration Plan** (if applicable)
  - [ ] Migration script tested
  - [ ] Rollback migration prepared
  - [ ] Data loss assessment documented

---

### Documentation Review

- [ ] **CHANGELOG.md Updated**
  - [ ] New features documented
  - [ ] Breaking changes highlighted
  - [ ] Deprecations noted
  - [ ] Version number incremented (SemVer)

- [ ] **README.md Updated** (if applicable)
  - [ ] Setup instructions accurate
  - [ ] Feature list current
  - [ ] Badges updated (tests, coverage, version)

- [ ] **Runbook Updated** (if applicable)
  - [ ] New issues documented
  - [ ] Troubleshooting steps added
  - [ ] Escalation contacts current

- [ ] **API Documentation Updated** (if applicable)
  - [ ] New skills documented
  - [ ] Changed parameters noted
  - [ ] Examples updated

---

## Deployment Execution

### Step 1: Stop Existing Processes (5 minutes)

```bash
cd H:\Programming\FTE-Agent\FTE

# Stop all watchers gracefully
python src/process_manager.py --stop

# Verify stopped
python src/process_manager.py --status

# Kill any remaining processes
taskkill /F /IM python.exe /FI "WINDOWTITLE eq FTE*"
```

- [ ] All watchers stopped
- [ ] Process Manager stopped
- [ ] Health endpoint stopped
- [ ] No orphaned Python processes

---

### Step 2: Deploy Code (10 minutes)

**Option A: Git Pull (Production)**
```bash
cd H:\Programming\FTE-Agent
git pull origin main
git checkout v2.0.0  # Tagged release
```

- [ ] Correct branch/tag checked out
- [ ] No merge conflicts
- [ ] Git status clean

**Option B: Manual Deploy (Development)**
```bash
# Copy new files
robocopy "H:\Temp\FTE-New" "H:\Programming\FTE-Agent\FTE" /MIR /XD __pycache__
```

- [ ] Files copied successfully
- [ ] No overwrites of runtime files (.env, *.db)

---

### Step 3: Install Dependencies (5 minutes)

```bash
cd H:\Programming\FTE-Agent\FTE
pip install -r requirements.txt --upgrade
playwright install  # Ensure browsers up-to-date
```

- [ ] All packages installed
- [ ] No dependency conflicts
- [ ] Playwright browsers installed

---

### Step 4: Run Database Migrations (if applicable) (5 minutes)

```bash
cd H:\Programming\FTE-Agent\FTE
python src/utils/migrate.py --upgrade
```

- [ ] Migrations completed successfully
- [ ] No data loss
- [ ] Rollback tested (if required)

---

### Step 5: Update Configuration (5 minutes)

```bash
# Review .env changes
diff H:\Backups\FTE-Agent\pre-deploy_<timestamp>\.env H:\Programming\FTE-Agent\FTE\.env

# Update Company_Handbook.md if needed
```

- [ ] Configuration reviewed
- [ ] New variables added to `.env`
- [ ] Deprecated variables removed

---

### Step 6: Start Processes (5 minutes)

```bash
cd H:\Programming\FTE-Agent\FTE

# Start health endpoint first
uvicorn src.api.health_endpoint:app --host localhost --port 8000 --reload &

# Start process manager
python src/process_manager.py --start

# Verify all watchers started
python src/process_manager.py --status
```

- [ ] Health endpoint running on port 8000
- [ ] Process Manager running
- [ ] Gmail Watcher UP
- [ ] WhatsApp Watcher UP
- [ ] FileSystem Watcher UP

---

### Step 7: Smoke Tests (10 minutes)

```bash
# Health check
curl http://localhost:8000/health

# Metrics endpoint
curl http://localhost:8000/metrics

# Readiness check
curl http://localhost:8000/ready

# Test watcher functionality
python src/watchers/gmail_watcher.py --test-auth
python src/watchers/whatsapp_watcher.py --test-session
```

- [ ] `/health` returns 200 with all components UP
- [ ] `/metrics` returns Prometheus format
- [ ] `/ready` returns 200
- [ ] Gmail authentication valid
- [ ] WhatsApp session valid
- [ ] No errors in logs (past 5 minutes)

---

### Step 8: Functional Validation (15 minutes)

**Test Scenario 1: Gmail Watcher**
- [ ] Send test email to monitored account
- [ ] Verify action file created in `vault/Needs_Action/` within 2 minutes
- [ ] Verify email marked as processed in SQLite

**Test Scenario 2: WhatsApp Watcher**
- [ ] Send test message with keyword "urgent"
- [ ] Verify action file created in `vault/Needs_Action/` within 30 seconds
- [ ] Verify session persists

**Test Scenario 3: Process Manager**
- [ ] Kill a watcher process manually
- [ ] Verify auto-restart within 10 seconds
- [ ] Check Dashboard.md updated

**Test Scenario 4: Health Endpoint**
- [ ] Verify `/health` shows correct component status
- [ ] Verify `/metrics` shows watcher metrics
- [ ] Verify rate limiting works (60+ requests/minute)

---

## Post-Deployment Checklist

### Monitoring Verification

- [ ] **Logs Flowing**
  - [ ] Check `vault/Logs/app_*.log` for recent entries
  - [ ] Log format is JSON with correlation_id
  - [ ] No ERROR or CRITICAL logs in past 5 minutes

- [ ] **Metrics Collection**
  - [ ] `/metrics` endpoint returns data
  - [ ] `watcher_check_duration_seconds` histogram populated
  - [ ] `watcher_restart_count` counter at 0 (if fresh deploy)

- [ ] **Dashboard Updated**
  - [ ] `vault/Dashboard.md` shows all watchers UP
  - [ ] Circuit breakers show CLOSED
  - [ ] Last check timestamps recent (<2 minutes ago)

- [ ] **Alerting Configured**
  - [ ] Email notifications enabled
  - [ ] SMS/WhatsApp alerts configured (if production)
  - [ ] Test alert sent and received

---

### Performance Validation

- [ ] **Watcher Intervals Met**
  - [ ] Gmail: checks every 120 seconds (±10s)
  - [ ] WhatsApp: checks every 30 seconds (±5s)
  - [ ] FileSystem: checks every 60 seconds (±10s)

- [ ] **Memory Usage Acceptable**
  - [ ] Gmail Watcher: <200MB
  - [ ] WhatsApp Watcher: <200MB
  - [ ] FileSystem Watcher: <100MB
  - [ ] Process Manager: <50MB

- [ ] **Response Times Acceptable**
  - [ ] Health endpoint: p95 <100ms
  - [ ] Action file creation: p95 <2 seconds
  - [ ] Approval detection: p95 <5 seconds

---

### Security Validation

- [ ] **DEV_MODE Enforced**
  - [ ] External actions blocked when `DEV_MODE=true`
  - [ ] Warning logged on startup

- [ ] **Rate Limiting Active**
  - [ ] Gmail API calls tracked
  - [ ] Warning logged at 80% quota

- [ ] **Circuit Breakers Active**
  - [ ] State persists to SQLite
  - [ ] Test trip/reset functionality

- [ ] **Audit Logging Active**
  - [ ] All actions logged to `vault/Logs/audit_*.log`
  - [ ] Logs include correlation_id
  - [ ] Logs immutable (append-only)

---

### Documentation Updates

- [ ] **Deployment Record Created**
  ```markdown
  ## Deployment [YYYY-MM-DD]
  
  - **Version**: 2.0.0
  - **Environment**: PROD
  - **Deployed By**: [Name]
  - **Changes**: [Link to CHANGELOG]
  - **Issues**: [None / List]
  - **Rollback**: [Not required / Performed]
  ```

- [ ] **Incident Response Plan Updated** (if applicable)
- [ ] **Runbook Updated** (if new issues discovered)
- [ ] **Stakeholders Notified**
  - [ ] Email sent to product owner
  - [ ] Dashboard link shared
  - [ ] Support team briefed

---

## Rollback Procedure

### Trigger Conditions

- [ ] Critical bug discovered (data loss, security vulnerability)
- [ ] Performance degradation >50%
- [ ] System instability (crashes, memory leaks)
- [ ] External dependency failure

### Rollback Steps

**Step 1: Stop Current Deployment** (5 minutes)
```bash
python src/process_manager.py --stop
taskkill /F /IM python.exe /FI "WINDOWTITLE eq FTE*"
```

**Step 2: Restore Backup** (15 minutes)
```powershell
# Restore pre-deployment backup
$backupPath = "H:\Backups\FTE-Agent\pre-deploy_<timestamp>"
robocopy "$backupPath" "H:\Programming\FTE-Agent\FTE" /MIR /XD __pycache__
```

**Step 3: Restart Previous Version** (10 minutes)
```bash
python src/process_manager.py --start
python src/process_manager.py --status
```

**Step 4: Verify Rollback** (10 minutes)
```bash
curl http://localhost:8000/health
python src/process_manager.py --status
```

**Step 5: Post-Rollback Review** (30 minutes)
- Document reason for rollback
- Identify root cause
- Plan remediation
- Communicate to stakeholders

**Total Rollback Time**: ~45 minutes (within 1-hour target)

---

## Deployment Sign-Off

### Development/Staging Deployment

| Role | Name | Signature | Date |
|------|------|-----------|------|
| Deployer | [Name] | [Sign] | [Date] |
| Technical Lead | [Name] | [Sign] | [Date] |

---

### Production Deployment

| Role | Name | Signature | Date |
|------|------|-----------|------|
| Deployer | [Name] | [Sign] | [Date] |
| Technical Lead | [Name] | [Sign] | [Date] |
| Product Owner | [Name] | [Sign] | [Date] |
| Security Officer | [Name] | [Sign] | [Date] |

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2026-03-19 | FTE-Agent Team | Initial Bronze tier checklist |
| 2.0.0 | 2026-04-02 | FTE-Agent Team | Silver tier update: health endpoint, watchers, circuit breakers |

---

**Next Review Date**: 2026-05-02  
**Document Owner**: FTE-Agent Team  
**Approval Status**: ✅ Production Ready
