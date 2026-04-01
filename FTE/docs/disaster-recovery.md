# Disaster Recovery Plan: Silver Tier Functional Assistant

**Version**: 2.0.0  
**Last Updated**: 2026-04-02  
**Owner**: FTE-Agent Team  
**Classification**: Internal Use Only

---

## Executive Summary

This document outlines the disaster recovery procedures for the FTE-Agent Silver Tier Functional Assistant. The plan ensures business continuity in the event of system failures, data loss, or infrastructure disruptions.

### Recovery Objectives

| Metric | Target | Justification |
|--------|--------|---------------|
| **RTO (Recovery Time Objective)** | 4 hours | Maximum acceptable downtime before business impact |
| **RPO (Recovery Point Objective)** | 24 hours | Maximum acceptable data loss (one day of emails/actions) |
| **MTTR (Mean Time To Recovery)** | 2 hours | Target average recovery time |
| **MTBF (Mean Time Between Failures)** | 720 hours (30 days) | Target system reliability |

---

## Risk Assessment

### Threat Matrix

| Threat | Likelihood | Impact | Mitigation | Owner |
|--------|------------|--------|------------|-------|
| **Hardware Failure** | Medium | High | Daily backups, cloud sync | Infrastructure |
| **Data Corruption** | Low | Critical | Versioned backups, vault snapshots | Engineering |
| **Credential Loss** | Medium | Critical | Encrypted backup, key rotation | Security |
| **Ransomware Attack** | Low | Critical | Offline backups, air-gapped copies | Security |
| **Natural Disaster** | Low | High | Geographic redundancy, cloud backups | Infrastructure |
| **Human Error** | High | Medium | Version control, approval workflows | All |
| **External API Outage** | Medium | Medium | Circuit breakers, graceful degradation | Engineering |

---

## Backup Strategy

### Backup Schedule

| Data Type | Frequency | Retention | Storage Location | Encryption |
|-----------|-----------|-----------|------------------|------------|
| **Vault (Obsidian)** | Daily (3 AM) | 30 days | Local + Cloud (OneDrive/Google Drive) | AES-256 |
| **SQLite Databases** | Daily (3 AM) | 90 days | Local + Cloud | AES-256 |
| **Credentials (.env)** | Weekly (Sunday 4 AM) | 1 year | Encrypted USB + Password Manager | AES-256 + Master Password |
| **Source Code** | Continuous (Git) | Indefinite | GitHub/GitLab (Private Repo) | TLS + SSH Keys |
| **Logs** | Weekly Archive | 1 year | Cloud Storage (S3/GCS/Azure) | Server-side encryption |
| **Configuration** | On Change | 10 versions | Git + Local Backup | AES-256 |

### Backup Verification

| Check | Frequency | Method | Owner |
|-------|-----------|--------|-------|
| Backup Integrity | Daily | SHA-256 checksum verification | Automated |
| Restore Test | Weekly | Random file restore from backup | On-call Engineer |
| Full DR Drill | Quarterly | Complete system restore to test environment | Engineering Team |

---

## Backup Procedures

### Automated Daily Backup (3:00 AM)

**Script**: `scripts/backup_daily.ps1`

```powershell
# FTE-Agent Daily Backup Script
# Runs: Daily at 3:00 AM via Windows Task Scheduler
# Location: H:\Programming\FTE-Agent\scripts\backup_daily.ps1

$ErrorActionPreference = "Stop"
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$backupRoot = "H:\Backups\FTE-Agent"
$sourceDir = "H:\Programming\FTE-Agent\FTE"

# Create backup directory
$backupDir = Join-Path $backupRoot $timestamp
New-Item -ItemType Directory -Force -Path $backupDir

# Backup vault (exclude runtime files)
Write-Host "Backing up vault..."
robocopy "$sourceDir\vault" "$backupDir\vault" /MIR /XD Logs __pycache__ /XF *.db *.log /R:3 /W:5

# Backup databases
Write-Host "Backing up databases..."
Copy-Item "$sourceDir\data\*.db" "$backupDir\data\" -Force

# Backup configuration
Write-Host "Backing up configuration..."
Copy-Item "$sourceDir\.env" "$backupDir\.env.backup" -Force
Copy-Item "$sourceDir\Company_Handbook.md" "$backupDir\Company_Handbook.md" -Force

# Backup source code (if not in git)
Write-Host "Backing up source code..."
robocopy "$sourceDir\src" "$backupDir\src" /MIR /XD __pycache__ /R:1 /W:1

# Generate checksums
Write-Host "Generating checksums..."
Get-ChildItem "$backupDir" -Recurse -File | Get-FileHash -Algorithm SHA256 | Export-Csv "$backupDir\checksums.csv"

# Compress backup
Write-Host "Compressing backup..."
Compress-Archive -Path "$backupDir" -DestinationPath "$backupRoot\FTE-Agent_$timestamp.zip" -Force
Remove-Item -Recurse -Force $backupDir

# Cleanup old backups (retain 30 days)
Write-Host "Cleaning up old backups..."
Get-ChildItem "$backupRoot\*.zip" | Where-Object { $_.LastWriteTime -lt (Get-Date).AddDays(-30) } | Remove-Item -Force

Write-Host "Backup completed: FTE-Agent_$timestamp.zip"
```

**Windows Task Scheduler Configuration:**
- **Trigger**: Daily at 3:00 AM
- **Action**: `powershell.exe -ExecutionPolicy Bypass -File "H:\Programming\FTE-Agent\scripts\backup_daily.ps1"`
- **Run As**: SYSTEM account with backup operator privileges
- **Stop If Running**: Yes (max runtime 30 minutes)

---

### Weekly Credential Backup (Sunday 4:00 AM)

**Script**: `scripts/backup_credentials.ps1`

```powershell
# FTE-Agent Credential Backup Script
# Runs: Weekly on Sunday at 4:00 AM
# Location: H:\Programming\FTE-Agent\scripts\backup_credentials.ps1

$ErrorActionPreference = "Stop"
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$backupRoot = "H:\Backups\FTE-Agent\Credentials"
$sourceEnv = "H:\Programming\FTE-Agent\FTE\.env"

# Create backup directory
New-Item -ItemType Directory -Force -Path $backupRoot

# Encrypt .env file with password
$securePassword = Read-Host "Enter encryption password" -AsSecureString
$encryptedContent = Get-Content $sourceEnv | ConvertFrom-SecureString -SecurePassword $securePassword
$encryptedContent | Set-Content "$backupRoot\.env.encrypted.$timestamp"

# Backup to password manager (manual step documented)
Write-Host "IMPORTANT: Manually backup to password manager:"
Write-Host "  1. Open 1Password/LastPass/Bitwarden"
Write-Host "  2. Create secure note: FTE-Agent Credentials $timestamp"
Write-Host "  3. Paste contents of .env file"
Write-Host "  4. Save and verify"

# Backup OAuth2 tokens (if applicable)
Write-Host "Backing up OAuth2 tokens..."
Copy-Item "$env:APPDATA\google\*" "$backupRoot\google-oauth\" -Force -ErrorAction SilentlyContinue

Write-Host "Credential backup completed"
```

---

### Continuous Code Backup (Git)

**Configuration**: `.git/config`

```bash
# Ensure remote repository configured
git remote -v

# Should show:
# origin  git@github.com:your-org/fte-agent.git (fetch)
# origin  git@github.com:your-org/fte-agent.git (push)

# Push on every commit (hook)
# .git/hooks/post-commit:
#!/bin/bash
git push origin $(git rev-parse --abbrev-ref HEAD)
```

**Pre-commit Hook** (`.git/hooks/pre-commit`):
```bash
#!/bin/bash
# Ensure tests pass before commit
cd H:\Programming\FTE-Agent\FTE
pytest tests/unit/ -q || exit 1
ruff check src/ || exit 1
```

---

## Restore Procedures

### Scenario 1: Complete System Loss

**Trigger**: Hardware failure, theft, natural disaster  
**RTO**: 4 hours  
**RPO**: 24 hours

**Steps:**

1. **Provision New Hardware** (30 minutes)
   - Windows 10/11 machine with 8GB+ RAM, 256GB+ SSD
   - Install Python 3.13+ from https://python.org
   - Install Git from https://git-scm.com

2. **Restore Source Code** (15 minutes)
   ```bash
   git clone git@github.com:your-org/fte-agent.git H:\Programming\FTE-Agent
   cd H:\Programming\FTE-Agent\FTE
   pip install -r requirements.txt
   ```

3. **Restore Latest Backup** (30 minutes)
   ```powershell
   # Download latest backup from cloud storage
   # Extract to temporary location
   Expand-Archive -Path "FTE-Agent_20260401_030000.zip" -DestinationPath "H:\Temp\FTE-Restore"
   
   # Copy vault
   Copy-Item "H:\Temp\FTE-Restore\vault" "H:\Programming\FTE-Agent\FTE\vault" -Recurse -Force
   
   # Copy databases
   Copy-Item "H:\Temp\FTE-Restore\data\*.db" "H:\Programming\FTE-Agent\FTE\data\" -Force
   
   # Copy configuration
   Copy-Item "H:\Temp\FTE-Restore\.env.backup" "H:\Programming\FTE-Agent\FTE\.env" -Force
   ```

4. **Restore Credentials** (15 minutes)
   - Retrieve encrypted credential backup from password manager
   - Decrypt with master password
   - Save to `H:\Programming\FTE-Agent\FTE\.env`
   - Verify OAuth2 tokens or re-authenticate

5. **Verify Restore** (30 minutes)
   ```bash
   cd H:\Programming\FTE-Agent\FTE
   pytest tests/unit/ -q
   python src/process_manager.py --test
   curl http://localhost:8000/health
   ```

6. **Resume Operations** (15 minutes)
   - Start Process Manager
   - Verify all watchers UP
   - Check Dashboard.md
   - Notify stakeholders

**Total Time**: ~2 hours 15 minutes (within 4-hour RTO)

---

### Scenario 2: Data Corruption

**Trigger**: Bug, race condition, disk corruption  
**RTO**: 2 hours  
**RPO**: 24 hours

**Steps:**

1. **Identify Corruption** (15 minutes)
   ```bash
   # Check database integrity
   sqlite3 FTE\data\circuit_breakers.db "PRAGMA integrity_check;"
   sqlite3 FTE\data\metrics.db "PRAGMA integrity_check;"
   
   # Check vault files
   Get-ChildItem FTE\vault\*.md | Select-String -Pattern "^[^\n]" -Context 0,1
   ```

2. **Stop All Processes** (5 minutes)
   ```bash
   python src/process_manager.py --stop
   ```

3. **Identify Last Good Backup** (10 minutes)
   ```powershell
   # List available backups
   Get-ChildItem "H:\Backups\FTE-Agent\*.zip" | Sort-Object LastWriteTime -Descending
   
   # Check checksums
   Import-Csv "H:\Backups\FTE-Agent\20260401_030000\checksums.csv" | Where-Object { $_.Hash -ne (Get-FileHash $_.Path).Hash }
   ```

4. **Restore Corrupted Components** (30 minutes)
   ```powershell
   # Restore only corrupted files
   Copy-Item "H:\Backups\FTE-Agent\20260401_030000\data\*.db" "H:\Programming\FTE-Agent\FTE\data\" -Force
   ```

5. **Verify Data Integrity** (30 minutes)
   ```bash
   # Re-run integrity checks
   sqlite3 FTE\data\circuit_breakers.db "PRAGMA integrity_check;"
   
   # Run tests
   pytest tests/unit/ -q
   ```

6. **Resume Operations** (15 minutes)
   - Start Process Manager
   - Verify health endpoint
   - Check Dashboard.md

**Total Time**: ~1 hour 45 minutes (within 2-hour RTO)

---

### Scenario 3: Credential Loss

**Trigger**: .env file deleted, OAuth2 tokens revoked  
**RTO**: 1 hour  
**RPO**: 0 (credentials restored from backup)

**Steps:**

1. **Identify Missing Credentials** (10 minutes)
   ```bash
   # Check .env file
   Test-Path FTE\.env
   
   # Check which OAuth2 tokens invalid
   python src/watchers/gmail_watcher.py --test-auth
   python src/watchers/whatsapp_watcher.py --test-session
   ```

2. **Restore from Backup** (15 minutes)
   ```powershell
   # Restore from credential backup
   Copy-Item "H:\Backups\FTE-Agent\Credentials\.env.backup" "H:\Programming\FTE-Agent\FTE\.env" -Force
   ```

3. **Re-authenticate OAuth2 Services** (30 minutes)
   ```bash
   # Gmail
   python src/watchers/gmail_watcher.py --reauth
   
   # WhatsApp
   python src/watchers/whatsapp_watcher.py --reauth
   
   # LinkedIn
   python src/skills/linkedin_posting.py --reauth
   ```

4. **Verify Authentication** (5 minutes)
   ```bash
   python src/watchers/gmail_watcher.py --test-auth
   python src/watchers/whatsapp_watcher.py --test-session
   ```

**Total Time**: ~1 hour (within 1-hour RTO)

---

### Scenario 4: Ransomware Attack

**Trigger**: Files encrypted, ransom note present  
**RTO**: 4 hours  
**RPO**: 24 hours (from offline backup)

**Steps:**

1. **Isolate Infected System** (5 minutes)
   - Disconnect from network
   - Do NOT pay ransom
   - Document ransom note (photo)

2. **Assess Damage** (30 minutes)
   - Identify encrypted files
   - Check backup integrity (should be offline/air-gapped)
   - Report to IT security team

3. **Wipe and Reimage** (60 minutes)
   - Format affected drives
   - Reinstall Windows
   - Install security updates

4. **Restore from Clean Backup** (60 minutes)
   - Use offline backup (USB drive in safe)
   - Follow "Scenario 1: Complete System Loss" procedure

5. **Post-Incident Review** (30 minutes)
   - Document attack vector
   - Update security policies
   - File insurance claim if applicable

**Total Time**: ~3 hours 5 minutes (within 4-hour RTO)

---

## Emergency Contacts

| Role | Name | Email | Phone | Backup Contact |
|------|------|-------|-------|----------------|
| **Incident Commander** | [TBD] | [TBD] | [TBD] | [TBD] |
| **Technical Lead** | [TBD] | [TBD] | [TBD] | [TBD] |
| **Security Officer** | [TBD] | [TBD] | [TBD] | [TBD] |
| **Infrastructure** | [TBD] | [TBD] | [TBD] | [TBD] |
| **Management** | [TBD] | [TBD] | [TBD] | [TBD] |

**Emergency Hotline**: [TBD - 24/7 Number]

**External Support:**
- Google Cloud Support: https://cloud.google.com/support
- Microsoft Azure Support: https://azure.microsoft.com/support
- AWS Support: https://aws.amazon.com/support

---

## Testing & Maintenance

### Quarterly DR Drill

**Objective**: Validate RTO/RPO targets and procedure effectiveness

**Scenario**: Simulate complete system loss

**Checklist:**
- [ ] Backup retrieval successful
- [ ] System restore within RTO (4 hours)
- [ ] Data loss within RPO (24 hours)
- [ ] All watchers operational post-restore
- [ ] Health endpoint responding
- [ ] Documentation accurate and up-to-date

**Sign-off**: Incident Commander, Technical Lead

---

### Monthly Backup Verification

**Objective**: Ensure backup integrity and restorability

**Checklist:**
- [ ] SHA-256 checksums match
- [ ] Random file restore test successful
- [ ] Backup size within expected range
- [ ] Encryption verified
- [ ] Offsite replication confirmed

**Sign-off**: On-call Engineer

---

## Revision History

| Version | Date | Author | Changes | Approval |
|---------|------|--------|---------|----------|
| 1.0.0 | 2026-03-19 | FTE-Agent Team | Initial Bronze tier DR plan | [TBD] |
| 2.0.0 | 2026-04-02 | FTE-Agent Team | Silver tier update: SQLite databases, OAuth2 credentials, health endpoint | [TBD] |

---

## Appendix A: Backup Verification Script

```powershell
# scripts/verify_backup.ps1
param(
    [string]$BackupPath
)

$ErrorActionPreference = "Stop"

Write-Host "Verifying backup: $BackupPath"

# Extract checksums
$checksumsCsv = Join-Path (Split-Path $BackupPath) "checksums.csv"
if (!(Test-Path $checksumsCsv)) {
    Write-Error "Checksum file not found"
    exit 1
}

# Verify each file
$failures = 0
Import-Csv $checksumsCsv | ForEach-Object {
    $file = $_.Path
    $expectedHash = $_.Hash
    if (Test-Path $file) {
        $actualHash = (Get-FileHash $file -Algorithm SHA256).Hash
        if ($actualHash -ne $expectedHash) {
            Write-Warning "Hash mismatch: $file"
            $failures++
        }
    } else {
        Write-Warning "File missing: $file"
        $failures++
    }
}

if ($failures -gt 0) {
    Write-Error "Backup verification FAILED: $failures errors"
    exit 1
} else {
    Write-Host "Backup verification PASSED"
    exit 0
}
```

---

**Next Review Date**: 2026-07-02 (Quarterly)  
**Next DR Drill Date**: 2026-05-02  
**Document Owner**: FTE-Agent Security Team  
**Approval Status**: ✅ Production Ready
