# Operational Runbook: Silver Tier Functional Assistant

**Version**: 2.0.0  
**Last Updated**: 2026-04-02  
**Owner**: FTE-Agent Team  
**Status**: Production Ready

---

## Quick Reference

| Issue | Symptom | Immediate Action | Escalation |
|-------|---------|------------------|------------|
| Watcher Crashed | Dashboard.md shows "DOWN" | Check logs, restart watcher | If restart fails >3 times |
| Session Expired | WhatsApp/LinkedIn auth failure | Re-authenticate via browser | If persists, check OAuth tokens |
| API Quota Exceeded | Gmail API 429 errors | Wait 1 hour, reduce frequency | If critical, request quota increase |
| Disk Full | Log rotation fails, DB errors | Clear old logs, expand disk | If recurring, increase retention policy |
| Circuit Breaker OPEN | API calls failing fast | Check external service status | If service healthy, reset breaker |
| Memory High | >200MB per watcher | Check for leaks, restart | If persists, profile memory |

---

## System Overview

### Components

| Component | Process | Port | Health Endpoint |
|-----------|---------|------|-----------------|
| Gmail Watcher | `python src/watchers/gmail_watcher.py` | - | `/health/gmail` |
| WhatsApp Watcher | `python src/watchers/whatsapp_watcher.py` | - | `/health/whatsapp` |
| FileSystem Watcher | `python src/filesystem_watcher.py` | - | `/health/filesystem` |
| Process Manager | `python src/process_manager.py` | - | `/health/process_manager` |
| Health API | `uvicorn src.api.health_endpoint:app` | 8000 | `/health` |

### Data Stores

| Database | Path | Purpose | Retention |
|----------|------|---------|-----------|
| Circuit Breakers | `FTE/data/circuit_breakers.db` | State persistence | Indefinite |
| Processed Emails | `FTE/data/processed_emails.db` | Deduplication | 30 days |
| Failed Actions | `FTE/data/failed_actions.db` | DLQ storage | 90 days |
| Metrics | `FTE/data/metrics.db` | Prometheus metrics | 7 days |

### Log Locations

| Log Type | Path | Rotation | Retention |
|----------|------|----------|-----------|
| Application | `FTE/vault/Logs/app_*.log` | 100MB or daily | 7 days INFO, 30 days ERROR |
| Audit | `FTE/vault/Logs/audit_*.log` | 100MB or daily | 1 year |
| Access | `FTE/vault/Logs/access_*.log` | 100MB or daily | 30 days |

---

## Common Issues & Troubleshooting

### 1. Watcher Crashed

**Symptoms:**
- Dashboard.md shows watcher status as "DOWN" or "CRASHED"
- No new action files created in `vault/Needs_Action/`
- Process Manager logs show restart attempts

**Diagnosis:**
```bash
# Check watcher logs
cd H:\Programming\FTE-Agent\FTE
Get-Content vault\Logs\app_*.log -Tail 100 | Select-String "gmail_watcher|whatsapp_watcher"

# Check Process Manager status
python src/process_manager.py --status

# Check health endpoint
curl http://localhost:8000/health
```

**Resolution:**
1. **Automatic Restart**: Process Manager should auto-restart within 10 seconds
2. **Manual Restart**:
   ```bash
   # Stop all watchers
   python src/process_manager.py --stop
   
   # Start all watchers
   python src/process_manager.py --start
   ```
3. **Check Root Cause**:
   - Review logs for exception stack traces
   - Check circuit breaker status: `SELECT * FROM circuit_breakers;`
   - Verify OAuth tokens not expired

**Escalation**: If watcher crashes >3 times in 1 hour:
- Check external API status (Gmail, WhatsApp Web)
- Review rate limiting: `SELECT * FROM rate_limits;`
- Profile memory usage: `python -m memory_profiler src/watchers/gmail_watcher.py`

---

### 2. Session Expired (WhatsApp/LinkedIn)

**Symptoms:**
- WhatsApp Watcher logs: "WhatsAppSessionExpired"
- LinkedIn posting fails with 401 Unauthorized
- Browser session not persisting

**Diagnosis:**
```bash
# Check session files
dir FTE\vault\whatsapp_session\
dir FTE\vault\linkedin_session\

# Check session age
Get-Item FTE\vault\whatsapp_session\storage.json | Select-Object LastWriteTime
```

**Resolution:**
1. **Re-authenticate WhatsApp**:
   ```bash
   python src/watchers/whatsapp_watcher.py --reauth
   ```
   - Scan QR code with WhatsApp mobile app
   - Session saved to `vault/whatsapp_session/storage.json`

2. **Re-authenticate LinkedIn**:
   ```bash
   python src/skills/linkedin_posting.py --reauth
   ```
   - Login via browser
   - Session cookies saved to `vault/linkedin_session/`

3. **Verify Session**:
   ```bash
   python src/watchers/whatsapp_watcher.py --test-session
   ```

**Prevention:**
- Sessions persist across restarts (saved to `vault/<service>_session/`)
- Re-authenticate proactively every 30 days
- Monitor Dashboard.md for expiry warnings

**Escalation**: If session expires repeatedly:
- Check for IP address changes (triggers security logout)
- Verify WhatsApp Web not logged out from mobile
- Check LinkedIn security settings for suspicious activity blocks

---

### 3. API Quota Exceeded (Gmail)

**Symptoms:**
- Gmail API returns HTTP 429 Too Many Requests
- Logs: "Rate limit exceeded, skipping check"
- Watcher continues but no new emails processed

**Diagnosis:**
```bash
# Check rate limit counter
sqlite3 FTE\data\rate_limits.db "SELECT * FROM gmail_rate_limit;"

# Check API usage in Google Cloud Console
# https://console.cloud.google.com/apis/api/gmail.googleapis.com/quotas
```

**Resolution:**
1. **Wait for Reset**: Rate limit resets every hour (default: 100 calls/hour)
2. **Reduce Frequency**: Edit `Company_Handbook.md`:
   ```ini
   [Gmail]
   check_interval_seconds = 180  # Increase from 120 to 180
   rate_limit_calls_per_hour = 50  # Reduce from 100 to 50
   ```
3. **Request Quota Increase**:
   - Go to Google Cloud Console
   - Navigate to APIs & Services > Dashboard > Gmail API
   - Request quota increase (requires business justification)

**Monitoring:**
- Dashboard.md shows "Gmail Rate Limit: X/100 calls this hour"
- Alert triggers at 80% quota usage

**Escalation**: If quota consistently exceeded:
- Review email volume patterns
- Implement email filtering (only check important/unread)
- Consider Gmail API paid tier

---

### 4. Disk Full

**Symptoms:**
- Logs: "No space left on device"
- Log rotation fails
- SQLite errors: "unable to open database file"

**Diagnosis:**
```bash
# Check disk usage
Get-PSDrive H:

# Check log directory size
(Get-ChildItem FTE\vault\Logs -Recurse | Measure-Object -Property Length -Sum).Sum / 1MB

# Check database sizes
dir FTE\data\*.db
```

**Resolution:**
1. **Clear Old Logs**:
   ```bash
   # Delete logs older than 7 days
   Get-ChildItem FTE\vault\Logs\*.log | Where-Object { $_.LastWriteTime -lt (Get-Date).AddDays(-7) } | Remove-Item
   ```

2. **Vacuum Databases**:
   ```bash
   sqlite3 FTE\data\circuit_breakers.db "VACUUM;"
   sqlite3 FTE\data\metrics.db "VACUUM;"
   sqlite3 FTE\data\processed_emails.db "VACUUM;"
   ```

3. **Clear DLQ** (if safe):
   ```bash
   # Archive and clear failed actions
   python src/utils/dead_letter_queue.py --archive --clear
   ```

**Prevention:**
- Log rotation configured (100MB or daily)
- Retention policy enforced (7 days INFO, 30 days ERROR)
- Monitor disk usage in Dashboard.md

**Escalation**: If disk fills repeatedly:
- Increase log retention cleanup frequency
- Move logs to separate drive
- Enable cloud log shipping (S3, GCS, Azure Blob)

---

### 5. Circuit Breaker OPEN

**Symptoms:**
- Logs: "Circuit breaker OPEN - skipping Gmail check"
- API calls fail fast without network request
- Dashboard.md shows "Circuit Breaker: OPEN"

**Diagnosis:**
```bash
# Check circuit breaker state
sqlite3 FTE\data\circuit_breakers.db "SELECT * FROM circuit_breakers;"

# Check recent failures
Get-Content FTE\vault\Logs\app_*.log -Tail 200 | Select-String "circuit_breaker|OPEN|CLOSED"
```

**Resolution:**
1. **Wait for Auto-Reset**: Circuit breaker resets after 60 seconds (default)
2. **Manual Reset**:
   ```bash
   python src/utils/circuit_breaker.py --reset --name gmail_watcher
   ```
3. **Check External Service**:
   - Gmail API Status: https://status.cloud.google.com/
   - WhatsApp Web: https://web.whatsapp.com/ (manual check)

**Prevention:**
- Circuit breaker threshold: 5 consecutive failures
- Recovery timeout: 60 seconds
- Failures logged with WARNING level

**Escalation**: If circuit breaker trips repeatedly:
- Check external service health
- Review network connectivity
- Increase failure threshold (if appropriate): Edit `Company_Handbook.md`

---

### 6. High Memory Usage

**Symptoms:**
- Process Manager logs: "Watcher memory exceeds 200MB threshold"
- System slowdown
- Watcher killed by Process Manager

**Diagnosis:**
```bash
# Check memory usage
python -c "import psutil; p = psutil.Process(<PID>); print(p.memory_info().rss / 1024 / 1024)"

# Profile memory
python -m memory_profiler src/watchers/gmail_watcher.py
```

**Resolution:**
1. **Restart Watcher**:
   ```bash
   python src/process_manager.py --restart gmail_watcher
   ```

2. **Profile Memory Leak**:
   ```bash
   # Run with memory profiling
   python -m memory_profiler src/watchers/gmail_watcher.py --duration 300
   ```

3. **Check for Known Issues**:
   - Playwright browser contexts not closed (WhatsApp Watcher)
   - SQLite connections not released
   - Large email attachments cached in memory

**Prevention:**
- Memory threshold: 200MB (configurable)
- Process Manager auto-kills and restarts
- Regular restarts (daily at 3 AM)

**Escalation**: If memory leak persists:
- Profile with `memory_profiler` or `py-spy`
- Check for unclosed resources (browser contexts, DB connections)
- File bug with stack trace and memory profile

---

## Monitoring & Alerting

### Health Check Endpoints

```bash
# Overall health
curl http://localhost:8000/health

# Prometheus metrics
curl http://localhost:8000/metrics

# Readiness check
curl http://localhost:8000/ready
```

### Dashboard Monitoring

Check `FTE/vault/Dashboard.md` every 4 hours for:
- Watcher status (UP/DOWN)
- Circuit breaker states
- Rate limit usage
- Memory usage per watcher
- Last successful check timestamp

### Alerting Thresholds

| Metric | Warning | Critical | Action |
|--------|---------|----------|--------|
| Watcher DOWN | >5 min | >15 min | Restart, then investigate |
| Circuit Breaker OPEN | >1 min | >5 min | Check external service |
| Memory Usage | >150MB | >250MB | Profile, restart if needed |
| Rate Limit | >80% | >95% | Reduce frequency, wait for reset |
| Disk Usage | >80% | >90% | Clear logs, expand disk |
| Error Rate | >5/hour | >20/hour | Investigate root cause |

### Alerting Channels

| Severity | Channel | Response Time |
|----------|---------|---------------|
| WARNING | Email notification | 4 hours |
| CRITICAL | SMS/WhatsApp message | 30 minutes |
| EMERGENCY | Phone call | 5 minutes |

---

## Escalation Policy

### Level 1: Self-Service (0-15 minutes)

**Who**: On-duty operator  
**Actions**:
- Check Dashboard.md
- Review logs
- Restart affected watcher
- Clear disk space if needed

**Escalate If**: Issue persists after 2 restart attempts

---

### Level 2: Technical Support (15-60 minutes)

**Who**: FTE-Agent technical lead  
**Actions**:
- Profile memory/CPU usage
- Check external service status
- Review circuit breaker logs
- Manual database queries

**Escalate If**: Root cause unknown or requires code fix

---

### Level 3: Engineering (1-4 hours)

**Who**: FTE-Agent engineering team  
**Actions**:
- Code debugging
- Performance profiling
- External API vendor contact
- Hotfix deployment

**Escalate If**: System-wide outage or data loss

---

### Level 4: Management (4+ hours)

**Who**: Product owner, engineering manager  
**Actions**:
- Business impact assessment
- Vendor escalation (Google, Meta)
- Customer communication
- Disaster recovery activation

---

## Maintenance Procedures

### Daily Checks (8:00 AM)

- [ ] Review Dashboard.md for overnight issues
- [ ] Check disk space usage
- [ ] Verify all watchers UP
- [ ] Review ERROR logs from past 24 hours

### Weekly Checks (Sunday 10:00 PM)

- [ ] Run weekly audit (automated)
- [ ] Review rate limit patterns
- [ ] Check circuit breaker trip frequency
- [ ] Vacuum SQLite databases
- [ ] Clear logs older than 7 days

### Monthly Checks (1st of month)

- [ ] Rotate OAuth tokens
- [ ] Review memory leak patterns
- [ ] Update dependencies (pip install --upgrade)
- [ ] Review and update runbook
- [ ] Test disaster recovery procedure

---

## Contact Information

| Role | Name | Email | Phone |
|------|------|-------|-------|
| On-Call Operator | [TBD] | [TBD] | [TBD] |
| Technical Lead | [TBD] | [TBD] | [TBD] |
| Engineering Manager | [TBD] | [TBD] | [TBD] |
| Product Owner | [TBD] | [TBD] | [TBD] |

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2026-03-19 | FTE-Agent Team | Initial Bronze tier runbook |
| 2.0.0 | 2026-04-02 | FTE-Agent Team | Silver tier update: Gmail/WhatsApp watchers, circuit breakers, health endpoint |

---

**Next Review Date**: 2026-05-02  
**Document Owner**: FTE-Agent Team  
**Approval Status**: ✅ Production Ready
