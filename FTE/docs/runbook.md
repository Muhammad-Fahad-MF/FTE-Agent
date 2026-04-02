# Operational Runbook: Gold Tier Autonomous Employee

**Version**: 3.0.0  
**Last Updated**: 2026-04-02  
**Branch**: `003-gold-tier-autonomous-employee`  
**Status**: Production Ready

---

## Table of Contents

1. [Quick Reference](#quick-reference)
2. [Common Operations](#common-operations)
3. [Troubleshooting](#troubleshooting)
4. [Maintenance Procedures](#maintenance-procedures)
5. [Security Disclosure](#security-disclosure)
6. [Emergency Procedures](#emergency-procedures)

---

## Quick Reference

| Issue | Symptom | Immediate Action | Escalation |
|-------|---------|------------------|------------|
| Watcher Crashed | Dashboard shows "DOWN" | Check Process Manager, auto-restart | If restart fails >3/hour |
| Circuit Breaker OPEN | API calls failing fast | Check external service, wait 5 min | If service healthy, manual reset |
| DLQ Size > 10 | Alert in Dashboard | Review DLQ items, resolve failures | If pattern emerges, investigate root cause |
| Odoo Unavailable | Fallback mode activated | Check Odoo service, transactions queued | If prolonged, manual transaction logging |
| Social API Rate Limit | Posts failing, drafts created | Wait for reset window | If critical, request limit increase |
| Approval Queue > 20 | Backlog alert | Review pending approvals | If aging >24h, auto-expire or escalate |
| Memory High | >500MB total | Check individual watchers, restart if >200MB | If persists, profile for leaks |
| CEO Briefing Failed | Monday 8 AM task failed | Check Odoo connectivity, run manually | If data issues, investigate sources |

---

## Common Operations

### Start All Watchers

**Windows**:
```bash
cd H:\Programming\FTE-Agent\FTE
.\scripts\start-watchers.bat
```

**Linux/Mac**:
```bash
cd /path/to/FTE-Agent/FTE
./scripts/start-watchers.sh
```

**Manual Start**:
```bash
# Start Gmail Watcher
python src/watchers/gmail_watcher.py &

# Start WhatsApp Watcher
python src/watchers/whatsapp_watcher.py &

# Start FileSystem Watcher
python src/filesystem_watcher.py &

# Start Process Manager (monitors all watchers)
python src/process_manager.py
```

### Stop All Watchers

**Graceful Shutdown**:
```bash
# Create STOP file (watchers detect and shutdown)
echo "STOP" > vault/STOP

# Or use Process Manager
# Send SIGTERM to process manager
kill -TERM <pid>
```

**Force Stop**:
```bash
# Kill all Python processes (careful!)
taskkill /F /IM python.exe  # Windows
pkill -f "python.*watcher"  # Linux/Mac
```

### Check System Health

**Via Dashboard**:
```bash
# Open Dashboard.md
notepad vault\Dashboard.md  # Windows
code vault/Dashboard.md     # VS Code
```

**Via Health Endpoint**:
```bash
# Overall health
curl http://localhost:8000/health

# Component health
curl http://localhost:8000/health | jq .components

# Prometheus metrics
curl http://localhost:8000/metrics
```

**Via Command Line**:
```bash
# Check watcher processes
tasklist | findstr python  # Windows
ps aux | grep watcher      # Linux/Mac

# Check log files
dir vault\Logs\*.json /OD  # Windows
ls -lt vault/Logs/*.json   # Linux/Mac
```

### Review Pending Approvals

**List Pending**:
```bash
# Windows PowerShell
Get-ChildItem vault\Pending_Approval\*.md

# Linux/Mac
ls -lt vault/Pending_Approval/*.md
```

**Check Approval Status**:
```python
from src.skills.request_approval import check_approval

status = check_approval("vault/Pending_Approval/APPROVAL_payment_123.md")
print(f"Status: {status['status']}")
print(f"Expires: {status['expires']}")
```

**Process Approvals**:
```bash
# Approve: Move to Approved/
move vault\Pending_Approval\APPROVAL_*.md vault\Approved\

# Reject: Move to Rejected/
move vault\Pending_Approval\APPROVAL_*.md vault\Rejected\
```

### Review Dead Letter Queue

**List DLQ Items**:
```python
from src.skills.dlq_skills import list_dlq_items

# List all pending
pending = list_dlq_items(status="pending_review")
print(f"Pending: {len(pending)}")

# List by action type
email_failures = list_dlq_items(action_type="send_email")
```

**Resolve DLQ Item**:
```python
from src.skills.dlq_skills import resolve_dlq_item

success = resolve_dlq_item(
    item_id="abc-123",
    resolution="Fixed SMTP credentials",
    notes="Updated .env file"
)
```

**Discard DLQ Item**:
```python
from src.skills.dlq_skills import discard_dlq_item

success = discard_dlq_item(
    item_id="xyz-789",
    notes="Action no longer needed"
)
```

### Query Audit Logs

**By Date**:
```python
from src.skills.audit_skills import query_logs

# Today's logs
logs = query_logs(date="2026-04-02")

# Date range
logs = query_logs(date="2026-04-01:2026-04-02")
```

**By Action Type**:
```python
# Email sends
emails = query_logs(action="email_sent")

# Approvals
approvals = query_logs(action="approval_requested")
```

**By Result**:
```python
# Failures only
failures = query_logs(result="failure")

# Get statistics
from src.skills.audit_skills import get_log_statistics
stats = get_log_statistics(days=7)
print(f"Error Rate: {stats['error_rate']}%")
```

**Export to CSV**:
```python
from src.skills.audit_skills import query_logs, export_to_csv

logs = query_logs(date="2026-04-01")
csv_path = export_to_csv(logs, "logs_april_1.csv")
```

### Generate CEO Briefing Manually

```python
from src.skills.briefing_skills import generate_ceo_briefing

result = generate_ceo_briefing()
print(f"Briefing: {result['briefing_path']}")
print(f"Generation time: {result['generation_time_sec']}s")
```

### Schedule/Disable CEO Briefing

**Windows Task Scheduler**:
```bash
# Schedule (Every Monday 8 AM)
.\scripts\schedule-ceo-briefing.bat

# List scheduled tasks
schtasks /Query /TN "FTE-CEO-Briefing"

# Disable
.\scripts\disable-ceo-briefing.bat

# Remove
.\scripts\remove-ceo-briefing.bat
```

**Linux cron**:
```bash
# Edit crontab
crontab -e

# Add: Every Monday 8 AM
0 8 * * 1 cd /path/to/FTE && python -c "from src.skills.briefing_skills import generate_ceo_briefing; generate_ceo_briefing()"
```

---

## Troubleshooting

### Watcher Crashed

**Symptoms**:
- Dashboard shows watcher status "DOWN" or "STOPPED"
- No new action files created
- Process Manager logs show restart attempts

**Diagnosis**:
```bash
# Check Process Manager logs
tail -f vault/Logs/YYYY-MM-DD.json | grep -i "process_manager"

# Check watcher-specific logs
grep "gmail_watcher" vault/Logs/YYYY-MM-DD.json
```

**Resolution**:
1. **Auto-restart**: Process Manager should restart within 10 seconds
2. **Manual restart**:
   ```bash
   # Stop existing (if any)
   taskkill /F /IM python.exe /FI "WINDOWTITLE eq *gmail_watcher*"
   
   # Restart
   python src/watchers/gmail_watcher.py
   ```
3. **Check dependencies**:
   ```bash
   pip install -r FTE/requirements.txt
   playwright install chromium  # For WhatsApp
   ```
4. **Review error logs** for root cause

**If restart fails >3/hour**:
- Check for memory leaks
- Review rate limits
- Check external service health
- Consider increasing check interval

---

### Circuit Breaker OPEN

**Symptoms**:
- `CircuitBreakerOpenError` exceptions
- Dashboard shows circuit breaker "OPEN" for service
- Actions failing immediately without retry

**Diagnosis**:
```python
from src.utils.circuit_breaker import get_circuit_breaker

cb = get_circuit_breaker("gmail")
print(f"State: {cb.get_state()}")
print(f"Failure count: {cb.failure_count}")
```

**Resolution**:
1. **Check external service**:
   ```bash
   # Gmail API
   curl https://www.googleapis.com/gmail/v1/users/me/profile
   
   # Odoo
   curl http://localhost:8069/jsonrpc -d '{"jsonrpc":"2.0","method":"call","params":{"service":"common","method":"version"},"id":1}'
   ```

2. **Wait for auto-reset** (300 seconds / 5 minutes)

3. **Manual reset**:
   ```bash
   curl -X POST http://localhost:8000/health/reset?component=gmail
   ```

4. **If service is healthy**:
   - Check network connectivity
   - Verify credentials
   - Review recent code changes

---

### DLQ Size Growing

**Symptoms**:
- Alert: "DLQ size (X) exceeds threshold (10)"
- Increasing failed actions
- Same failure pattern repeating

**Diagnosis**:
```python
from src.skills.dlq_skills import list_dlq_items, get_dlq_summary

summary = get_dlq_summary()
print(f"Total: {summary['total_failed']}")
print(f"By type: {summary['by_action_type']}")

# Find common failure pattern
failures = list_dlq_items(limit=50)
for f in failures[:5]:
    print(f"Action: {f['original_action']}, Reason: {f['failure_reason']}")
```

**Resolution**:
1. **Identify pattern**: Group by `failure_reason`
2. **Fix root cause**:
   - Credential issues → Update .env
   - Rate limits → Wait or increase limits
   - Service down → Restart service
3. **Bulk resolve**:
   ```python
   from src.skills.dlq_skills import resolve_dlq_item
   
   for item in list_dlq_items(status="pending_review"):
       resolve_dlq_item(item['id'], "Bulk resolution after fix")
   ```

---

### Odoo Fallback Active

**Symptoms**:
- Dashboard shows "Odoo Fallback: ACTIVE"
- Transactions queued in `vault/Odoo_Queue/`
- Fallback logs in `vault/Odoo_Fallback/`

**Diagnosis**:
```python
from src.services.odoo_fallback import get_odoo_fallback_manager

fallback = get_odoo_fallback_manager()
stats = fallback.get_fallback_stats()
print(f"Queued: {stats['queued_count']}")
print(f"Synced: {stats['synced_count']}")
```

**Resolution**:
1. **Check Odoo availability**:
   ```bash
   curl http://localhost:8069/jsonrpc -d '{"jsonrpc":"2.0","method":"call","params":{"service":"common","method":"version"},"id":1}'
   ```

2. **If Odoo down**: Start/restart Odoo service
   ```bash
   # Windows service
   net start odoo
   
   # Linux systemd
   systemctl start odoo
   ```

3. **If Odoo up but unreachable**:
   - Check network/firewall
   - Verify Odoo URL in .env
   - Check database credentials

4. **Manual sync**:
   ```python
   from src.services.odoo_fallback import sync_queued_transactions
   
   result = sync_queued_transactions()
   print(f"Synced: {result['synced']}, Failed: {result['failed']}")
   ```

---

### Social Media Drafts Accumulating

**Symptoms**:
- Posts not going through
- Drafts accumulating in `vault/Drafts/`
- Rate limit errors in logs

**Diagnosis**:
```python
from src.services.social_fallback import get_social_fallback_manager

fallback = get_social_fallback_manager()
stats = fallback.get_fallback_stats()
print(f"Platform stats: {stats['platforms']}")
```

**Resolution**:
1. **Check rate limits**:
   - LinkedIn: 1 post/day
   - Twitter: 300 posts/15 min
   - Facebook: 200 calls/hour
   - Instagram: 25 posts/day

2. **Wait for reset window**

3. **Manual sync**:
   ```python
   from src.services.social_fallback import sync_drafts
   
   result = sync_drafts(platform="linkedin")
   print(f"Posted: {result['posted']}, Failed: {result['failed']}")
   ```

4. **If API issue**:
   - Check API credentials
   - Verify session tokens
   - Review platform API status

---

### WhatsApp Session Expired

**Symptoms**:
- `SessionExpiredError` exceptions
- WhatsApp Web requires QR scan
- Messages not sending

**Resolution**:
1. **Re-authenticate**:
   ```bash
   python scripts/auth/whatsapp_auth.py
   ```

2. **Scan QR code** with WhatsApp mobile app

3. **Verify session saved**:
   ```bash
   dir vault\State\whatsapp_session\
   ```

4. **Test connection**:
   ```python
   from src.skills.whatsapp_skills import send_whatsapp
   
   result = send_whatsapp("+1234567890", "Test message")
   print(f"Status: {result['status']}")
   ```

---

### Gmail API Auth Failure

**Symptoms**:
- `google.auth.exceptions.RefreshError`
- Emails not sending
- 401 Unauthorized errors

**Resolution**:
1. **Check credentials**:
   ```bash
   # Verify file exists
   dir credentials\gmail_credentials.json
   ```

2. **Re-authenticate**:
   ```bash
   python scripts/auth/gmail_auth.py
   ```

3. **Verify scopes in .env**:
   ```
   GMAIL_SCOPES=https://www.googleapis.com/auth/gmail.send,https://www.googleapis.com/auth/gmail.readonly
   ```

4. **Check API enabled**:
   - Go to Google Cloud Console
   - Verify Gmail API is enabled

---

### High Memory Usage

**Symptoms**:
- Memory >500MB total
- Individual watchers >200MB
- System slowing down

**Diagnosis**:
```bash
# Windows
tasklist /V | findstr python

# Linux/Mac
ps aux | grep watcher | awk '{print $2, $6}'
```

**Resolution**:
1. **Restart high-memory watchers**:
   ```bash
   # Stop specific watcher
   taskkill /F /FI "WINDOWTITLE eq *gmail_watcher*"
   
   # Restart
   python src/watchers/gmail_watcher.py
   ```

2. **If persists**: Profile for memory leaks
   ```bash
   pip install memory_profiler
   python -m memory_profiler src/watchers/gmail_watcher.py
   ```

3. **Consider reducing check frequency** in watcher config

---

## Maintenance Procedures

### Daily Checks

**Checklist**:
- [ ] Review Dashboard.md for alerts
- [ ] Check pending approvals (>24h old?)
- [ ] Review DLQ size (<10?)
- [ ] Verify all watchers running
- [ ] Check disk space (>10GB free?)

**Commands**:
```bash
# Quick health check
curl http://localhost:8000/health | jq .status

# Check approvals
Get-ChildItem vault\Pending_Approval\*.md | Where-Object {$_.LastWriteTime -lt (Get-Date).AddHours(-24)}

# Check DLQ
python -c "from src.skills.dlq_skills import get_dlq_summary; print(get_dlq_summary()['total_failed'])"
```

### Weekly Checks

**Checklist**:
- [ ] Review log statistics (error rate <5%?)
- [ ] Audit subscription usage
- [ ] Check circuit breaker history
- [ ] Review watcher restart counts
- [ ] Verify backup integrity

**Commands**:
```python
from src.skills.audit_skills import get_log_statistics

stats = get_log_statistics(days=7)
print(f"Error Rate: {stats['error_rate']}%")
print(f"Total Entries: {stats['total_entries']}")
```

### Monthly Maintenance

**Checklist**:
- [ ] Rotate credentials (if policy requires)
- [ ] Clear old logs (>90 days)
- [ ] Review and archive DLQ items
- [ ] Update dependencies
- [ ] Review performance metrics
- [ ] Test disaster recovery

**Commands**:
```bash
# Clear old logs (careful!)
# Keep last 90 days
find vault/Logs/*.json -mtime +90 -delete  # Linux/Mac

# Update dependencies
pip install --upgrade -r FTE/requirements.txt

# Run tests
pytest --cov=src
```

### Log Rotation

**Automatic**: Daily at midnight (built into AuditLogger)

**Manual** (if needed):
```bash
# Archive current logs
mkdir vault/Logs/archive/YYYY-MM
move vault\Logs\*.json vault\Logs\archive\YYYY-MM\

# Clear old archives (>90 days)
```

### Database Backup

**SQLite Databases**:
```bash
# Backup all databases
mkdir backups
copy FTE\data\*.db backups\
copy vault\State\*.json backups\

# Compress
7z a backups\backup_YYYY-MM-DD.zip backups\*
```

### Credential Rotation

**Schedule**: Monthly or after suspected breach

**Process**:
1. Generate new credentials in respective developer consoles
2. Update `.env` file
3. Restart affected watchers
4. Test each integration
5. Archive old credentials securely

---

## Security Disclosure

### Credential Handling

**Storage**:
- ✅ `.env` file (gitignored via `.gitignore`)
- ✅ Windows Credential Manager / macOS Keychain
- ✅ Environment variables for cloud deployments

**Never Store**:
- ❌ Source code
- ❌ Obsidian vault
- ❌ Log files
- ❌ Version control

**Rotation**:
- Frequency: Monthly or after breach
- Process: Generate new → Update .env → Restart services → Test

---

### Human-in-the-Loop (HITL) Boundaries

**Require Human Approval**:
- Payments >$500 (configurable)
- First-time invoice recipients
- Social media posts (optional, can be auto-approved for trusted content)
- Any action with `risk_level="high"`

**Auto-Approved**:
- Replies to internal emails
- Invoice generation for known clients
- Scheduled social posts (if pre-approved)
- Low-risk routine tasks

**Approval Expiry**:
- Standard: 24 hours
- After expiry: Auto-reject with notification

---

### dry_run Mode Behavior

**When DRY_RUN=true**:
- All external actions logged but NOT executed
- Emails: Content logged, not sent
- Payments: Details logged, not processed
- Posts: Content logged, not published

**Use Cases**:
- Testing new workflows
- Auditing existing processes
- Training/demonstrations
- Debugging issues

**Enable**:
```bash
# In .env
DRY_RUN=true

# Or command line
export DRY_RUN=true
python src/watchers/gmail_watcher.py
```

---

### DEV_MODE Kill Switch

**Purpose**: Prevent accidental external actions

**When DEV_MODE=false**:
- All external API calls blocked
- Clear error: "DEV_MODE not enabled"
- Logs show attempted actions

**Enable for Production**:
```bash
# In .env
DEV_MODE=true
```

**Testing Without DEV_MODE**:
```bash
# Safe testing
DRY_RUN=true
DEV_MODE=false  # Will log but not execute
```

---

### Audit Trail

**What's Logged**:
- All external API calls
- All approval requests
- All state changes
- All errors and failures
- All watcher actions

**Log Location**: `vault/Logs/YYYY-MM-DD.json`

**Retention**: 90 days (automatic)

**Query**:
```python
from src.skills.audit_skills import query_logs

# All actions today
today = query_logs(date="2026-04-02")

# All failures
failures = query_logs(result="failure")

# Export for audit
export_to_csv(today, "audit_export.csv")
```

---

### Access Control

**Filesystem Permissions**:
- Vault: Read/write for service account only
- .env: Read-only for service account
- Logs: Append-only for service account

**Network**:
- Health endpoint: localhost only (default)
- Odoo: Local network or localhost
- External APIs: Outbound only

---

## Emergency Procedures

### Complete System Shutdown

**Graceful**:
```bash
# Create STOP file
echo "STOP" > vault/STOP

# Wait for watchers to detect (up to 60 seconds)
timeout /t 60  # Windows
sleep 60       # Linux/Mac

# Verify all stopped
tasklist | findstr watcher
```

**Emergency**:
```bash
# Kill all Python processes
taskkill /F /IM python.exe  # Windows
pkill -9 python             # Linux/Mac

# Verify
tasklist | findstr python
```

### Data Recovery

**From Backup**:
```bash
# Stop all services first
# Restore databases
copy backups\*.db FTE\data\

# Restore state files
copy backups\*.json vault\State\

# Restart services
```

**Corrupted Logs**:
- Logs are JSON lines format (resilient to corruption)
- If file corrupted: Rename, create new, attempt recovery

**Corrupted Database**:
```bash
# SQLite recovery
sqlite3 data/failed_actions.db ".recover" > recovery.sql
sqlite3 data/failed_actions.db.new < recovery.sql
move /Y data\failed_actions.db.new data\failed_actions.db
```

### Service Outage Response

**External Service Down** (Gmail, Odoo, Social):
1. Activate fallback (automatic)
2. Monitor DLQ for queued actions
3. Communicate ETA to users
4. Resume when service restored

**Internal Service Down** (Watcher, MCP):
1. Process Manager auto-restarts
2. If restart fails, investigate logs
3. Manual restart if needed
4. Escalate if pattern emerges

### Security Incident Response

**Suspected Breach**:
1. **Immediate**: Disable DEV_MODE
   ```bash
   # In .env
   DEV_MODE=false
   ```

2. **Rotate all credentials**:
   - Gmail API
   - Odoo
   - Social media
   - Any other integrations

3. **Review audit logs**:
   ```python
   from src.skills.audit_skills import query_logs, search_logs
   
   # Search for suspicious activity
   suspicious = search_logs(query="unauthorized", field="error")
   ```

4. **Notify stakeholders**

5. **Document incident**

---

## Contact and Escalation

### Support Channels

- **Documentation**: `FTE/docs/`
- **Logs**: `vault/Logs/`
- **Dashboard**: `vault/Dashboard.md`
- **Health Endpoint**: `http://localhost:8000/health`

### Escalation Path

1. **Level 1**: Review this runbook
2. **Level 2**: Check documentation
3. **Level 3**: Contact development team
4. **Level 4**: Emergency incident response

---

*Generated by FTE-Agent Development Team*  
*Last Updated: 2026-04-02*
