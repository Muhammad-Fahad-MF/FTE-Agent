# Security Disclosure: FTE-Agent Gold Tier

**Version**: 3.0.0  
**Last Updated**: 2026-04-02  
**Classification**: Public  
**Branch**: `003-gold-tier-autonomous-employee`

---

## Table of Contents

1. [Security Architecture](#security-architecture)
2. [Credential Management](#credential-management)
3. [Data Protection](#data-protection)
4. [Access Control](#access-control)
5. [Human-in-the-Loop Boundaries](#human-in-the-loop-boundaries)
6. [Audit and Monitoring](#audit-and-monitoring)
7. [Incident Response](#incident-response)
8. [Compliance Considerations](#compliance-considerations)

---

## Security Architecture

### Defense in Depth

The FTE-Agent implements multiple layers of security:

```
┌─────────────────────────────────────────────────────────────┐
│                    Layer 1: Prevention                       │
│  - DEV_MODE kill switch                                     │
│  - Credential isolation                                      │
│  - Input validation                                          │
│  - Type safety (Python 3.13+)                               │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    Layer 2: Detection                        │
│  - Comprehensive audit logging                               │
│  - Circuit breakers                                          │
│  - Anomaly detection (DLQ monitoring)                        │
│  - Health monitoring                                         │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    Layer 3: Response                         │
│  - Automatic fallback mechanisms                             │
│  - Dead Letter Queue quarantine                              │
│  - Alert triggering                                          │
│  - Graceful degradation                                      │
└─────────────────────────────────────────────────────────────┘
```

### Security Principles

**I. Least Privilege**
- Skills only access required resources
- API scopes minimized to necessary permissions
- File system access restricted to vault directories

**II. Defense in Depth**
- Multiple validation layers
- Fallback mechanisms for all external services
- Quarantine for failed actions

**III. Secure by Default**
- DEV_MODE=false by default
- DRY_RUN=true for testing
- All actions logged
- Approval required for sensitive operations

**IV. Fail Secure**
- Circuit breakers open on repeated failures
- Fallback to safe state on errors
- No credential leakage in error messages

---

## Credential Management

### Storage

**Approved Methods**:

| Method | Use Case | Security Level |
|--------|----------|----------------|
| **Windows Credential Manager** | Production (Windows) | High |
| **macOS Keychain** | Production (macOS) | High |
| **Linux Keyring** | Production (Linux) | High |
| **.env file** | Development only | Medium (must be gitignored) |
| **Environment variables** | Cloud deployments | Medium-High |

**NEVER Store Credentials In**:
- Source code repositories
- Obsidian vault
- Log files
- Documentation
- Chat messages

### .env File Security

**Location**: `FTE/.env`

**Permissions**:
```bash
# Windows
icacls .env /grant:r "%USERNAME%:R" /inheritance:r

# Linux/Mac
chmod 600 .env
chown user:user .env
```

**Git Ignore** (already configured):
```gitignore
# .gitignore
.env
.env.*
!.env.example
```

### Credential Rotation

**Schedule**:
- **Routine**: Every 90 days
- **After incident**: Immediately
- **After personnel change**: Within 24 hours

**Process**:
1. Generate new credentials in respective console
2. Update credential store
3. Restart affected services
4. Test integration
5. Archive old credentials securely
6. Document rotation in audit log

**Rotation Checklist**:
- [ ] Gmail API credentials
- [ ] Odoo admin password
- [ ] Social media API tokens
- [ ] Health endpoint auth token
- [ ] Any custom integrations

---

## Data Protection

### Data Classification

| Data Type | Classification | Storage | Encryption |
|-----------|---------------|---------|------------|
| API Credentials | Confidential | Credential Manager | At rest (OS-managed) |
| Email Content | Internal | Vault (Logs) | None (local only) |
| Business Transactions | Confidential | Vault + Odoo | Odoo DB encryption |
| Audit Logs | Internal | Vault | None (local only) |
| Personal Messages | Confidential | Vault | None (local only) |

### Data Retention

| Data Type | Retention Period | Deletion Method |
|-----------|------------------|-----------------|
| Audit Logs | 90 days | Automatic rotation |
| DLQ Items | Indefinite (until resolved) | Manual discard |
| Processed Email IDs | 30 days | Automatic cleanup |
| Circuit Breaker State | Indefinite | Manual reset |
| CEO Briefings | Indefinite | Manual archive |

### Data Backup

**Schedule**: Weekly (automated) or before major changes

**Backup Contents**:
```
vault/
├── State/           # Process state
├── Logs/            # Audit logs (last 90 days)
├── Briefings/       # CEO briefings
└── Dashboard.md     # Current status

FTE/data/
├── circuit_breakers.db
├── failed_actions.db
└── processed_emails.db
```

**Backup Security**:
- Encrypt backup files
- Store in secure location
- Test restoration quarterly

---

## Access Control

### Filesystem Permissions

**Vault Directory**:
```bash
# Windows (PowerShell)
$acl = Get-Acl vault
$accessRule = New-Object System.Security.AccessControl.FileSystemAccessRule(
    "$env:USERNAME", "FullControl", "ContainerInherit,ObjectInherit", "None", "Allow"
)
$acl.SetAccessRule($accessRule)
Set-Acl vault $acl

# Linux/Mac
chmod 700 vault
chown user:user vault
```

**Source Code**:
```bash
# Read-only for service account
chmod 755 src/
chmod 644 src/**/*.py
```

**Configuration**:
```bash
# .env read-only
chmod 400 .env
```

### Network Security

**Default Configuration**:
- Health endpoint: localhost only (127.0.0.1)
- No inbound connections required
- Outbound only to known APIs

**Hardening** (for network deployments):
```bash
# Bind to specific interface
uvicorn src.api.health_endpoint:app --host 192.168.1.100

# Firewall rules (Windows)
netsh advfirewall firewall add rule name="FTE Health" dir=in action=allow protocol=TCP localport=8000

# Firewall rules (Linux)
ufw allow from 192.168.1.0/24 to any port 8000
```

### API Authentication

**Gmail API**:
- OAuth 2.0 with refresh tokens
- Scopes limited to gmail.send, gmail.readonly
- Token stored in credential manager

**Odoo JSON-RPC**:
- Username/password or API key
- HTTPS recommended for production
- Database-specific access

**Social Media APIs**:
- OAuth 2.0 tokens
- Platform-specific permissions
- Token refresh automatic

---

## Human-in-the-Loop Boundaries

### Approval Requirements

**Mandatory Approval** (Cannot be bypassed):
- Payments > $500 (configurable threshold)
- First-time invoice recipients
- High-risk actions (risk_level="high")
- Any action modifying financial records

**Optional Approval** (Configurable):
- Social media posts
- Email replies to external parties
- Expense categorization

**Auto-Approved** (No approval needed):
- Internal email replies
- Invoice generation for known clients
- Routine data queries
- Low-risk operational tasks

### Approval Workflow

```
┌─────────────────────────────────────────────────────────────┐
│  1. Skill detects action requiring approval                 │
│     risk_level = "high" or amount > threshold               │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  2. request_approval() creates approval file                │
│     Location: vault/Pending_Approval/APPROVAL_<id>.md       │
│     Expiry: 24 hours from creation                          │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  3. Human reviews approval request                          │
│     - Check action details                                  │
│     - Verify recipient/amount                               │
│     - Assess risk                                           │
└────────────────────┬────────────────────────────────────────┘
                     │
        ┌────────────┴────────────┐
        │                         │
        ▼                         ▼
    APPROVE                    REJECT
        │                         │
        │                         │
        ▼                         ▼
┌───────────────┐         ┌───────────────┐
│ Move to       │         │ Move to       │
│ /Approved/    │         │ /Rejected/    │
│ Orchestrator  │         │ Logged as     │
│ executes      │         │ rejected      │
└───────────────┘         └───────────────┘
```

### Approval Expiry

**Default**: 24 hours

**After Expiry**:
1. Status changed to "expired"
2. File moved to /Rejected/
3. User notified via Dashboard update
4. Action logged to audit log

**Override** (Emergency only):
```python
from src.skills.request_approval import check_approval

# Force approve (use sparingly!)
status = check_approval("vault/Pending_Approval/APPROVAL_123.md")
if status['status'] == 'expired':
    # Manual override - document reason
    logger.warning("Emergency override for expired approval")
```

---

## Audit and Monitoring

### What Is Logged

**All Actions**:
- External API calls (Gmail, Odoo, Social)
- Approval requests and decisions
- State changes (watcher start/stop, circuit breaker trips)
- Errors and failures
- Configuration changes

**Log Schema**:
```json
{
  "timestamp": "2026-04-02T10:30:00",
  "level": "INFO",
  "component": "send_email_skill",
  "action": "email_sent",
  "dry_run": false,
  "correlation_id": "abc-123-def",
  "domain": "business",
  "target": "user@example.com",
  "parameters": {"subject": "Invoice #1234"},
  "approval_status": "human",
  "approved_by": "admin",
  "result": "success",
  "error": null,
  "details": {"message_id": "msg_123"}
}
```

### Log Access

**Read Access**:
- Service account: Append-only
- Admin users: Read
- Audit tools: Read

**Query Methods**:
```python
# Python API
from src.skills.audit_skills import query_logs, export_to_csv

logs = query_logs(date="2026-04-01", result="failure")
export_to_csv(logs, "audit_export.csv")

# Command line
python -c "from src.skills.audit_skills import query_logs; print(query_logs(date='2026-04-01'))"
```

### Monitoring Alerts

**Automatic Alerts**:
- DLQ size > 10
- Circuit breaker OPEN
- Watcher restart > 3/hour
- Approval queue > 20
- Odoo fallback activated
- Social media rate limit exceeded

**Alert Methods**:
- File in vault/Needs_Action/
- Dashboard.md update
- Email notification (if configured)

---

## Incident Response

### Incident Classification

| Severity | Description | Response Time | Examples |
|----------|-------------|---------------|----------|
| **Critical** | System down, data breach | Immediate | Credential leak, unauthorized access |
| **High** | Major functionality impaired | < 1 hour | Multiple watchers down, Odoo unavailable |
| **Medium** | Minor functionality impaired | < 4 hours | Single watcher down, DLQ growing |
| **Low** | No immediate impact | < 24 hours | Cosmetic issues, documentation updates |

### Incident Response Process

**1. Detection**:
- Automated alerts
- User reports
- Health check failures
- Log analysis

**2. Triage**:
- Classify severity
- Identify affected components
- Determine scope

**3. Containment**:
- Disable affected services
- Activate fallback mechanisms
- Preserve evidence (logs, state)

**4. Eradication**:
- Fix root cause
- Rotate compromised credentials
- Patch vulnerabilities

**5. Recovery**:
- Restore services
- Verify functionality
- Monitor for recurrence

**6. Lessons Learned**:
- Document incident
- Update runbook
- Implement preventive measures

### Security Incident Checklist

**Suspected Breach**:
- [ ] Disable DEV_MODE immediately
- [ ] Rotate all credentials
- [ ] Review audit logs for suspicious activity
- [ ] Notify stakeholders
- [ ] Document timeline
- [ ] File incident report

**Credential Compromise**:
- [ ] Revoke compromised credentials
- [ ] Generate new credentials
- [ ] Update credential store
- [ ] Test all integrations
- [ ] Review access logs

**Unauthorized Access**:
- [ ] Terminate active sessions
- [ ] Change all passwords
- [ ] Review filesystem permissions
- [ ] Check for backdoors
- [ ] Enhance monitoring

---

## Compliance Considerations

### GDPR (EU General Data Protection Regulation)

**If processing EU resident data**:

**Data Minimization**:
- Only collect necessary data
- 90-day log retention (configurable)
- Automatic deletion of processed email IDs

**Right to Access**:
```python
# Export all data for specific user
from src.skills.audit_skills import query_logs, search_logs

user_logs = search_logs(query="user@example.com", field="target")
export_to_csv(user_logs, "user_data_export.csv")
```

**Right to Erasure**:
```python
# Manual deletion (use carefully!)
import os
for log_file in Path("vault/Logs").glob("*.json"):
    content = log_file.read_text()
    # Remove user data (implement carefully)
```

**Data Processing Agreement**: Required if processing personal data for others

### CCPA (California Consumer Privacy Act)

**Consumer Rights**:
- Right to know what data is collected
- Right to delete personal information
- Right to opt-out of sale (not applicable - no data sale)

**Implementation**:
- Maintain data inventory
- Provide data export on request
- Delete upon request (with legal exceptions)

### SOX (Sarbanes-Oxley) - If Used for Financial Reporting

**Requirements**:
- Audit trail for financial transactions
- Access controls
- Change management
- Documentation

**FTE-Agent Compliance**:
- ✅ Comprehensive audit logging
- ✅ Approval workflow for financial actions
- ✅ Credential rotation policy
- ✅ Documentation (this document + runbook)

### Industry Best Practices

**OWASP Top 10 Mitigation**:

| Risk | Mitigation in FTE-Agent |
|------|------------------------|
| A01: Broken Access Control | Filesystem permissions, credential isolation |
| A02: Cryptographic Failures | HTTPS for Odoo, OS-managed credential encryption |
| A03: Injection | Parameterized queries (SQLite), input validation |
| A04: Insecure Design | Security-first architecture (see Security Architecture) |
| A05: Security Misconfiguration | Secure defaults (DEV_MODE=false), documentation |
| A06: Vulnerable Components | Regular dependency updates, pip audit |
| A07: Auth Failures | OAuth 2.0, token refresh, session management |
| A08: Data Integrity | Audit logging, approval workflow |
| A09: Logging Failures | Comprehensive JSON logging, 90-day retention |
| A10: SSRF | Localhost-only binding, outbound-only external calls |

---

## Security Testing

### Automated Scans

**Dependency Audit**:
```bash
# Monthly
pip install pip-audit
pip-audit

# Or use safety
pip install safety
safety check
```

**Static Analysis**:
```bash
# Bandit (security linter)
pip install bandit
bandit -r src/

# SAST tools (optional)
# - SonarQube
# - Semgrep
```

### Penetration Testing

**Recommended**: Annual or after major changes

**Scope**:
- Health endpoint (if exposed)
- Credential storage
- File system access
- API integrations

**Tools**:
- Burp Suite (web testing)
- Nmap (network scanning)
- Custom scripts for API testing

### Security Code Review

**Before Production**:
- Review all new code for security issues
- Check credential handling
- Verify audit logging
- Test approval workflows

**Checklist**:
- [ ] No hardcoded credentials
- [ ] All external actions logged
- [ ] DEV_MODE validation in place
- [ ] Error messages don't leak information
- [ ] Input validation on all user input

---

## Security Contact

**Report Vulnerabilities**:
- Email: security@fte-agent.example.com (configure for your deployment)
- PGP Key: [Provide if applicable]

**Response Time**:
- Critical: Within 24 hours
- High: Within 48 hours
- Medium/Low: Within 1 week

**Disclosure Policy**:
- Coordinated disclosure
- 90-day window for fixes
- Credit given (with permission)

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 3.0.0 | 2026-04-02 | Gold Tier: Added Odoo, social media, DLQ, alerting |
| 2.0.0 | 2026-04-01 | Silver Tier: Added Gmail, WhatsApp, approval workflow |
| 1.0.0 | 2026-03-31 | Initial Bronze Tier release |

---

*Generated by FTE-Agent Development Team*  
*Last Updated: 2026-04-02*
