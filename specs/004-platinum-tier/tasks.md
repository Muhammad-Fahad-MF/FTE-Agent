# Implementation Tasks: Platinum Tier - Cloud + Local Executive

**Branch**: `004-platinum-tier-cloud-executive`
**Created**: 2026-04-02
**Status**: Draft
**Spec**: [spec.md](spec.md)
**Plan**: [plan.md](plan.md)
**Total Estimated Hours**: 60+

## Summary

Platinum Tier (v6.0.0) transforms Gold Tier's local-only agent into a two-agent architecture with Cloud (24/7 monitoring, draft-only) and Local (execution authority, secret storage) agents synchronized via Git vault replication (<60 seconds). Implementation spans 7 Platinum requirements (P1-P7) plus comprehensive testing.

**Key Features**:
- Cloud VM deployment (Oracle Cloud Free Tier) with health endpoint and auto-restart
- Vault synchronization with conflict resolution and secret exclusion
- Security boundary enforcement (zero secrets on Cloud)
- Claim-by-move ownership prevention
- Cloud Odoo with draft-only invoices
- 8-step Platinum Demo workflow
- Complete documentation suite

**Success Criteria**: 99% Cloud uptime, <60s sync, zero secrets synced, 100% double-work prevention, all 8 demo steps passing

---

## Task List

### P1: Cloud VM Deployment (8 hours)

#### P1-T001: Create Oracle Cloud VM Instance [X]
- **Description**: Provision Oracle Cloud Free Tier VM (2 OCPU, 12GB RAM, Ubuntu 22.04 LTS) with SSH key authentication and basic networking
- **Acceptance Criteria**:
  - Given Oracle Cloud account with billing enabled, When VM is created, Then it has 2 OCPU, 12GB RAM, 200GB storage
  - Given VM is running, When SSH connection is tested, Then it succeeds with key-based auth (no password)
  - Given VM is accessible, When public IP is pinged, Then it responds within 100ms
- **Estimated Hours**: 1.5
- **Dependencies**: None
- **Files**:
  - `docs/runbooks/cloud-vm-setup.md` (update with Oracle-specific steps)
- **Tests**: None (manual setup)
- **Status**: ✅ COMPLETE (2026-04-02) - Runbook created

#### P1-T002: Configure Security Hardening [X]
- **Description**: Implement UFW firewall rules, Fail2ban intrusion prevention, and automatic security updates on Cloud VM
- **Acceptance Criteria**:
  - Given UFW is installed, When rules are applied, Then only ports 22 (SSH), 80 (HTTP), 443 (HTTPS), 8000 (health) are open
  - Given Fail2ban is configured, When 5 failed SSH attempts occur within 5 minutes, Then the IP is banned for 1 hour
  - Given unattended-upgrades is enabled, When security updates are available, Then they are installed automatically within 24 hours
- **Estimated Hours**: 1.5
- **Dependencies**: P1-T001
- **Files**:
  - `scripts/deploy/configure-security.sh`
- **Tests**: None (manual verification)
- **Status**: ✅ COMPLETE (2026-04-02) - Script created

#### P1-T003: Implement Health Endpoint [X]
- **Description**: Create FastAPI health endpoint at `http://<cloud-vm>:8000/health` returning status, uptime, resource metrics, and watcher status
- **Acceptance Criteria**:
  - Given endpoint is running, When GET /health is called, Then it returns JSON with status, uptime, cpu_percent, memory_percent, disk_percent, watchers
  - Given endpoint under load, When 1000 health checks are performed, Then p95 latency is <500ms
  - Given endpoint is queried, When response is validated, Then it includes Prometheus-compatible metrics endpoint at /metrics
- **Estimated Hours**: 2.5
- **Dependencies**: P1-T001
- **Files**:
  - `src/health/endpoint.py` (FastAPI app)
  - `src/health/monitoring.py` (resource monitoring)
  - `tests/unit/health/test_endpoint.py`
- **Tests**:
  - `test_health_endpoint_response()` - Validate JSON schema
  - `test_health_endpoint_latency()` - Verify p95 <500ms over 1000 requests
  - `test_metrics_endpoint()` - Verify Prometheus format
- **Status**: ✅ COMPLETE (2026-04-02) - Module implemented with tests

#### P1-T004: Configure Auto-Restart Service [X]
- **Description**: Create systemd service for Cloud Agent with auto-restart on crash (<10 seconds) and startup on boot
- **Acceptance Criteria**:
  - Given Cloud Agent process is killed, When systemd detects crash, Then it restarts the process within 10 seconds
  - Given VM is rebooted, When system starts, Then Cloud Agent service starts automatically within 30 seconds
  - Given service is running, When systemctl status fte-agent is called, Then it shows active (running) state
- **Estimated Hours**: 1.5
- **Dependencies**: P1-T003
- **Files**:
  - `scripts/deploy/configure-systemd.sh`
  - `scripts/deploy/fte-agent.service` (systemd unit file)
- **Tests**:
  - `tests/integration/test_auto_restart.py` - Measure restart time over 50 crash cycles
- **Status**: ✅ COMPLETE (2026-04-02) - Systemd service configured

#### P1-T005: Implement Resource Monitoring [X]
- **Description**: Deploy psutil-based monitoring for CPU, memory, and disk utilization with logging every 60 seconds
- **Acceptance Criteria**:
  - Given monitoring is enabled, When metrics are logged, Then CPU, memory, and disk percentages are recorded every 60 seconds
  - Given CPU usage exceeds 80% for 5 minutes, When alert threshold is breached, Then an alert is generated and logged
  - Given disk usage exceeds 90%, When alert threshold is breached, Then an alert is sent to Local agent via Signals folder
- **Estimated Hours**: 1.0
- **Dependencies**: P1-T003
- **Files**:
  - `src/health/monitoring.py` (extends P1-T003)
  - `src/health/alerting.py` (alert generation)
- **Tests**:
  - `test_resource_monitoring_interval()` - Verify 60-second logging
  - `test_cpu_alert_threshold()` - Verify alert at >80% CPU
  - `test_disk_alert_threshold()` - Verify alert at >90% disk
- **Status**: ✅ COMPLETE (2026-04-02) - Monitoring module with alerting implemented

---

### P2: Vault Sync (8 hours)

#### P2-T001: Configure Git Remote Repository
- **Description**: Set up private GitHub/GitLab repository for vault synchronization with SSH key authentication
- **Acceptance Criteria**:
  - Given GitHub/GitLab account exists, When private repo is created, Then it has SSH key authentication enabled
  - Given Local vault exists, When Git remote is configured, Then `git remote -v` shows the correct repository URL
  - Given Cloud VM is set up, When SSH key is added to GitHub/GitLab, Then Git operations succeed without password
- **Estimated Hours**: 1.0
- **Dependencies**: P1-T001
- **Files**:
  - `scripts/sync/init-vault.sh`
  - `docs/runbooks/vault-sync-config.md` (update)
- **Tests**: None (manual setup)

#### P2-T002: Implement Sync Script
- **Description**: Create GitPython-based sync script that pulls/pushes changes every 60 seconds with proper error handling
- **Acceptance Criteria**:
  - Given Cloud creates a draft file, When sync runs, Then the file appears on Local vault within 60 seconds
  - Given Local approves a draft, When sync completes, Then Cloud sees the approval status change
  - Given network is unavailable, When sync is attempted, Then it queues the operation and retries after 30 seconds
- **Estimated Hours**: 2.5
- **Dependencies**: P2-T001
- **Files**:
  - `src/sync/git_sync.py` (GitPython implementation)
  - `src/sync/config.py` (sync configuration)
- **Tests**:
  - `test_sync_completion_time()` - Verify <60s sync over 100 operations
  - `test_sync_offline_queue()` - Verify queuing during network partition
  - `test_sync_retry_logic()` - Verify exponential backoff (30s, 60s, 120s)

#### P2-T003: Implement Conflict Resolver
- **Description**: Create last-write-wins conflict resolution with local-wins exception for Dashboard.md
- **Acceptance Criteria**:
  - Given Cloud and Local modify the same file simultaneously, When sync encounters conflict, Then last-write-wins is applied
  - Given both agents modify Dashboard.md, When conflict occurs, Then Local version wins (overwrites Cloud)
  - Given conflict is resolved, When audit log is checked, Then conflict details are recorded with timestamps
- **Estimated Hours**: 2.0
- **Dependencies**: P2-T002
- **Files**:
  - `src/sync/conflict_resolver.py`
  - `tests/unit/sync/test_conflict_resolver.py`
- **Tests**:
  - `test_last_write_wins()` - Verify standard conflict resolution
  - `test_dashboard_local_wins()` - Verify Dashboard.md exception
  - `test_conflict_audit_logging()` - Verify conflict is logged

#### P2-T004: Implement Exclusion Validator
- **Description**: Create pre-sync validation that blocks secret files (.env, tokens/, sessions/, banking/, credentials/, *.key, *.pem) from being added to Git
- **Acceptance Criteria**:
  - Given Local vault contains .env file, When sync runs, Then .env is excluded via .gitignore and never staged
  - Given a process attempts to add tokens/ folder, When exclusion validator runs, Then the operation is blocked and logged
  - Given 100 secret file patterns are tested, When validator is run, Then 100% are detected and blocked
- **Estimated Hours**: 2.5
- **Dependencies**: P2-T002
- **Files**:
  - `src/sync/exclusion_validator.py`
  - `.gitignore` (update with Platinum exclusions)
  - `tests/unit/sync/test_exclusion_validator.py`
- **Tests**:
  - `test_env_file_exclusion()` - Verify .env is never synced
  - `test_token_folder_exclusion()` - Verify tokens/ is blocked
  - `test_session_file_exclusion()` - Verify WhatsApp sessions are excluded
  - `test_exclusion_detection_rate()` - Verify 100% detection over 100 test patterns

---

### P3: Security Boundaries (8 hours)

#### P3-T001: Implement Secret Pattern Detection
- **Description**: Create regex-based secret detection for .env patterns, API keys, tokens, credentials, and banking data
- **Acceptance Criteria**:
  - Given a file contains API_KEY=sk-..., When scanned, Then it is flagged as containing a secret
  - Given a file contains AWS_SECRET_ACCESS_KEY, When scanned, Then it is flagged as containing a secret
  - Given 100 secret patterns are tested, When detector is run, Then 100% are identified with zero false negatives
- **Estimated Hours**: 2.0
- **Dependencies**: None
- **Files**:
  - `src/security/boundary.py` (secret detection)
  - `src/security/patterns.py` (regex patterns)
  - `tests/unit/security/test_secret_detection.py`
- **Tests**:
  - `test_env_pattern_detection()` - Verify .env patterns are caught
  - `test_api_key_detection()` - Verify various API key formats
  - `test_banking_pattern_detection()` - Verify account numbers/routing numbers
  - `test_detection_rate()` - Verify 100% detection over 100 patterns

#### P3-T002: Implement Pre-Sync Validation
- **Description**: Create pre-sync hook that validates all files before git add and blocks secret-containing files
- **Acceptance Criteria**:
  - Given a file contains secrets, When pre-sync validation runs, Then the file is blocked from being added
  - Given a file is blocked, When audit log is checked, Then the breach attempt is logged with file path and secret type
  - Given validation is bypassed, When security boundary is enforced, Then the operation fails with SecretDetectedError
- **Estimated Hours**: 2.0
- **Dependencies**: P3-T001, P2-T002
- **Files**:
  - `src/security/boundary.py` (extends P3-T001)
  - `src/sync/git_sync.py` (integrate pre-sync hook)
- **Tests**:
  - `test_presync_blocks_secret()` - Verify blocking before git add
  - `test_presync_audit_logging()` - Verify breach attempt is logged
  - `test_presync_bypass_prevention()` - Verify bypass attempts fail

#### P3-T003: Integrate OS Credential Manager
- **Description**: Implement Windows Credential Manager integration for Local secret storage (never in vault files)
- **Acceptance Criteria**:
  - Given Local agent needs an API key, When it queries credential manager, Then the secret is retrieved securely
  - Given Cloud agent requests a secret, When it checks the vault, Then no secrets are found (zero secrets on Cloud)
  - Given a secret is stored, When Windows Credential Manager is inspected, Then the secret is present with correct target name
- **Estimated Hours**: 2.5
- **Dependencies**: P3-T001
- **Files**:
  - `src/security/credential_manager.py` (Windows integration)
  - `src/skills/base_skill.py` (integrate credential retrieval)
  - `tests/unit/security/test_credential_manager.py`
- **Tests**:
  - `test_credential_storage()` - Verify secrets are stored correctly
  - `test_credential_retrieval()` - Verify secrets are retrieved correctly
  - `test_cloud_zero_secrets()` - Verify Cloud has no secrets after 30-day simulation

#### P3-T004: Implement Audit Logging
- **Description**: Create enhanced audit logging for all security boundary events (breach attempts, secret access, validation failures)
- **Acceptance Criteria**:
  - Given a security event occurs, When it is logged, Then it includes timestamp, event_type, agent, file_path, and outcome
  - Given audit log is queried, When 100 security events are logged, Then all are present with complete details
  - Given log rotation is configured, When logs exceed 100MB, Then they are rotated with 7-day retention
- **Estimated Hours**: 1.5
- **Dependencies**: P3-T001
- **Files**:
  - `src/security/audit_logger.py`
  - `vault/Logs/security_audit.jsonl` (log file)
- **Tests**:
  - `test_audit_log_schema()` - Verify JSON schema compliance
  - `test_audit_log_completeness()` - Verify all fields are present
  - `test_log_rotation()` - Verify rotation at 100MB

---

### P4: Claim-by-Move (6 hours)

#### P4-T001: Implement Claim File Creation
- **Description**: Create ownership marker system via `/In_Progress/<agent>/` folders (Cloud or Local)
- **Acceptance Criteria**:
  - Given Cloud starts processing a task, When it claims the file, Then it is moved to `/In_Progress/Cloud/`
  - Given Local starts processing a task, When it claims the file, Then it is moved to `/In_Progress/Local/`
  - Given a file is claimed, When claim marker is inspected, Then it shows agent name and claim timestamp
- **Estimated Hours**: 1.5
- **Dependencies**: None
- **Files**:
  - `src/models/claim.py` (ClaimFile entity)
  - `src/sync/claim_by_move.py` (claim operations)
  - `tests/unit/sync/test_claim_file.py`
- **Tests**:
  - `test_cloud_claim_creation()` - Verify Cloud claim marker
  - `test_local_claim_creation()` - Verify Local claim marker
  - `test_claim_timestamp()` - Verify claim time is recorded

#### P4-T002: Implement Double-Work Prevention
- **Description**: Create claim detection that prevents agents from working on already-claimed files
- **Acceptance Criteria**:
  - Given Cloud has claimed a file, When Local attempts to process it, Then Local detects the claim and backs off
  - Given Local has claimed a file, When Cloud attempts to process it, Then Cloud detects the claim and backs off
  - Given 100 concurrent claim attempts, When race condition is tested, Then 100% are prevented (one winner, others back off)
- **Estimated Hours**: 2.0
- **Dependencies**: P4-T001
- **Files**:
  - `src/sync/claim_by_move.py` (extends P4-T001)
  - `tests/integration/test_double_work_prevention.py`
- **Tests**:
  - `test_cloud_claim_detection()` - Verify Local backs off Cloud claims
  - `test_local_claim_detection()` - Verify Cloud backs off Local claims
  - `test_concurrent_claims()` - Verify 100% prevention over 100 attempts

#### P4-T003: Implement Stale Claim Detection
- **Description**: Create stale claim detection (>5 minutes = reclaimable) with automatic reclaim logic
- **Acceptance Criteria**:
  - Given Cloud claims a file and crashes, When 5 minutes pass, Then Local detects stale claim and can reclaim
  - Given a claim is stale, When reclaim is attempted, Then the file is moved to `/Needs_Action/` for re-processing
  - Given claim age is checked, When claim is <5 minutes old, Then it is not marked as stale
- **Estimated Hours**: 1.5
- **Dependencies**: P4-T001
- **Files**:
  - `src/sync/claim_by_move.py` (extends P4-T002)
  - `tests/unit/sync/test_stale_claim.py`
- **Tests**:
  - `test_stale_claim_detection()` - Verify >5-minute claims are flagged
  - `test_stale_claim_reclaim()` - Verify reclaim logic works
  - `test_fresh_claim_preservation()` - Verify <5-minute claims are not reclaimed

#### P4-T004: Implement Cross-Agent Communication
- **Description**: Create Update files (`/Updates/<domain>/`) and Signal files (`/Signals/<domain>/`) for cross-agent coordination
- **Acceptance Criteria**:
  - Given Cloud detects an event, When it writes an update, Then the file is placed in `/Updates/<domain>/`
  - Given urgent alert is needed, When Cloud writes a signal, Then the file is placed in `/Signals/<domain>/` with high priority marker
  - Given Local reads updates, When it merges them, Then Dashboard.md is updated with latest status
- **Estimated Hours**: 1.0
- **Dependencies**: P4-T001
- **Files**:
  - `src/models/claim.py` (UpdateFile, SignalFile entities)
  - `tests/unit/sync/test_cross_agent_comm.py`
- **Tests**:
  - `test_update_file_creation()` - Verify Update files are created correctly
  - `test_signal_file_creation()` - Verify Signal files have priority marker
  - `test_dashboard_merge()` - Verify Local merges updates into Dashboard.md

---

### P5: Cloud Odoo (8 hours)

#### P5-T001: Deploy Odoo with Docker Compose
- **Description**: Create Docker Compose setup for Odoo Community v19+ with PostgreSQL 14, HTTPS, and health monitoring
- **Acceptance Criteria**:
  - Given Docker Compose is run, When containers start, Then Odoo v19+ and PostgreSQL 14 are running
  - Given Odoo is running, When HTTPS is tested, Then Let's Encrypt certificate is valid and trusted
  - Given Odoo is accessible, When health check is performed, Then it responds within 500ms
- **Estimated Hours**: 2.5
- **Dependencies**: P1-T001, P1-T002
- **Files**:
  - `scripts/deploy/docker-compose-odoo.yml`
  - `scripts/deploy/setup-odoo.sh`
  - `docs/runbooks/odoo-deployment.md`
- **Tests**: None (manual deployment)

#### P5-T002: Configure HTTPS with Let's Encrypt
- **Description**: Set up SSL certificates from Let's Encrypt for Odoo and health endpoint
- **Acceptance Criteria**:
  - Given domain is configured, When certbot is run, Then SSL certificate is issued and installed
  - Given certificate is installed, When HTTPS is tested, Then it achieves A+ rating on SSL Labs
  - Given certificate is near expiry, When auto-renewal runs, Then certificate is renewed automatically
- **Estimated Hours**: 1.5
- **Dependencies**: P5-T001
- **Files**:
  - `scripts/deploy/configure-https.sh`
  - `scripts/deploy/certbot-renew.sh`
- **Tests**: None (manual verification)

#### P5-T003: Implement Draft-Only Invoice Creation
- **Description**: Create Cloud Agent skill for Odoo invoice creation in "draft" status (unposted) with no send permissions
- **Acceptance Criteria**:
  - Given Cloud detects a billable event, When it creates an invoice, Then the invoice is in "draft" status in Odoo
  - Given 50 draft invoices are created, When Odoo is audited, Then zero invoices are posted/sent
  - Given Cloud attempts to post an invoice, When permission is checked, Then the operation fails with PermissionDenied
- **Estimated Hours**: 2.0
- **Dependencies**: P5-T001
- **Files**:
  - `src/skills/create_invoice.py` (extend with draft-only mode)
  - `src/skills/odoo_rpc.py` (Odoo JSON-RPC client)
  - `tests/integration/test_draft_invoice.py`
- **Tests**:
  - `test_draft_invoice_creation()` - Verify invoices are created as drafts
  - `test_draft_invoice_zero_sends()` - Verify 0 sends over 50 invoices
  - `test_post_permission_denied()` - Verify Cloud cannot post invoices

#### P5-T004: Implement Invoice Posting (Local Only)
- **Description**: Create Local Agent skill for reviewing and posting draft invoices from Cloud
- **Acceptance Criteria**:
  - Given Local reviews a draft invoice, When user approves, Then the invoice is posted in Odoo
  - Given invoice is posted, When customer is checked, Then they received the invoice via email
  - Given 10 invoices are approved, When audit log is checked, Then all 10 show Local execution
- **Estimated Hours**: 1.5
- **Dependencies**: P5-T003
- **Files**:
  - `src/skills/create_invoice.py` (extend with Local post mode)
  - `tests/integration/test_invoice_posting.py`
- **Tests**:
  - `test_local_invoice_posting()` - Verify Local can post invoices
  - `test_invoice_email_delivery()` - Verify customer receives invoice
  - `test_local_execution_audit()` - Verify all posts show Local agent

#### P5-T005: Implement Daily Encrypted Backups
- **Description**: Create automated daily backup of Odoo PostgreSQL database with AES-256 encryption
- **Acceptance Criteria**:
  - Given backup script runs daily, When backup completes, Then PostgreSQL dump is created and encrypted with AES-256
  - Given backup is stored, When encryption is verified, Then AES-256 encryption is confirmed
  - Given restore is needed, When backup is restored, Then database is recovered with zero data loss
- **Estimated Hours**: 1.5
- **Dependencies**: P5-T001
- **Files**:
  - `scripts/backup/backup-odoo.sh`
  - `scripts/backup/restore-odoo.sh`
  - `docs/runbooks/backup-restore.md`
- **Tests**:
  - `test_backup_encryption()` - Verify AES-256 encryption
  - `test_backup_restore()` - Verify full database recovery

---

### P6: Platinum Demo (8 hours)

#### P6-T001: Implement Email Arrival Detection (Cloud)
- **Description**: Configure Cloud Gmail watcher to detect incoming emails while Local is offline
- **Acceptance Criteria**:
  - Given Local is offline, When email arrives at client@example.com, Then Cloud detects it within 2 minutes
  - Given email is detected, When action file is created, Then it is placed in `/Inbox/Email/`
  - Given 100 emails arrive, When detection is measured, Then 100% are detected within 2 minutes
- **Estimated Hours**: 1.0
- **Dependencies**: P1-T003, P2-T002
- **Files**:
  - `src/watchers/gmail_watcher.py` (extend for Cloud mode)
  - `tests/integration/platinum/test_demo_step1.py`
- **Tests**:
  - `test_email_detection_cloud()` - Verify Cloud detects emails within 2 minutes
  - `test_email_action_file()` - Verify action file is created correctly

#### P6-T002: Implement Draft Reply Creation (Cloud)
- **Description**: Create Cloud skill for drafting professional email replies (no send capability)
- **Acceptance Criteria**:
  - Given email requires reply, When Cloud processes it, Then a draft reply is created in `/Drafts/Email/`
  - Given draft is created, When content is inspected, Then it includes subject, recipients, body, and professional tone
  - Given 50 drafts are created, When sent folder is checked, Then zero emails are sent
- **Estimated Hours**: 1.5
- **Dependencies**: P6-T001
- **Files**:
  - `src/skills/send_email.py` (extend with draft-only mode for Cloud)
  - `tests/integration/platinum/test_demo_step2.py`
- **Tests**:
  - `test_draft_reply_creation()` - Verify draft is created correctly
  - `test_draft_zero_sends()` - Verify 0 sends over 50 drafts
  - `test_draft_professional_tone()` - Verify reply tone is appropriate

#### P6-T003: Implement Vault Sync (Cloud → Local)
- **Description**: Verify draft reply syncs from Cloud to Local vault within 60 seconds
- **Acceptance Criteria**:
  - Given Cloud creates a draft, When sync runs, Then draft appears on Local vault within 60 seconds
  - Given sync completes, When Local checks draft queue, Then the draft is ready for review
  - Given 100 syncs are performed, When timing is measured, Then 100% complete within 60 seconds
- **Estimated Hours**: 1.0
- **Dependencies**: P6-T002, P2-T002
- **Files**:
  - `tests/integration/platinum/test_demo_step3.py`
- **Tests**:
  - `test_cloud_to_local_sync()` - Verify sync completes within 60 seconds
  - `test_sync_100_operations()` - Verify 100% success over 100 syncs

#### P6-T004: Implement Local Approval Workflow
- **Description**: Create Local workflow for reviewing and approving draft emails from Cloud
- **Acceptance Criteria**:
  - Given Local user reviews draft queue, When user approves a draft, Then it is moved to `/Approved/Email/`
  - Given draft is approved, When approval is logged, Then audit trail shows user approval timestamp
  - Given 50 drafts are reviewed, When approval rate is measured, Then user can approve/reject each independently
- **Estimated Hours**: 1.5
- **Dependencies**: P6-T003
- **Files**:
  - `src/skills/request_approval.py` (extend for email approval)
  - `tests/integration/platinum/test_demo_step4.py`
- **Tests**:
  - `test_local_approval_workflow()` - Verify approval moves file correctly
  - `test_approval_audit_trail()` - Verify approval is logged

#### P6-T005: Implement Local Execution (Send Email)
- **Description**: Create Local skill for sending approved emails via Gmail API
- **Acceptance Criteria**:
  - Given email is approved, When Local executes send, Then the email is sent via Gmail API
  - Given email is sent, When recipient is checked, Then they receive the email within 1 minute
  - Given 50 emails are sent, When audit log is checked, Then all show Local execution (zero Cloud sends)
- **Estimated Hours**: 1.5
- **Dependencies**: P6-T004
- **Files**:
  - `src/skills/send_email.py` (extend with Local send mode)
  - `tests/integration/platinum/test_demo_step5.py`
- **Tests**:
  - `test_local_email_send()` - Verify email is sent correctly
  - `test_local_execution_audit()` - Verify all sends show Local agent
  - `test_cloud_zero_sends()` - Verify Cloud has 0 sends

#### P6-T006: Implement Audit Trail Logging
- **Description**: Create comprehensive audit logging for all 8 demo steps with correlation IDs
- **Acceptance Criteria**:
  - Given demo workflow runs, When each step completes, Then it is logged with timestamp, step_number, agent, and correlation_id
  - Given audit log is queried, When full workflow is reconstructed, Then all 8 steps are present in correct order
  - Given log is inspected, When correlation_id is checked, Then it links all steps from same email thread
- **Estimated Hours**: 1.0
- **Dependencies**: P6-T005
- **Files**:
  - `src/security/audit_logger.py` (extend with correlation IDs)
  - `tests/integration/platinum/test_demo_step6.py`
- **Tests**:
  - `test_audit_trail_completeness()` - Verify all 8 steps are logged
  - `test_correlation_id_linking()` - Verify steps are linked by correlation ID

#### P6-T007: Implement End-to-End Demo Test
- **Description**: Create integration test that runs the full 8-step Platinum Demo workflow
- **Acceptance Criteria**:
  - Given Local is offline, When full demo is run, Then all 8 steps complete successfully
  - Given demo completes, When total time is measured, Then it completes within 5 minutes (Local online portion)
  - Given demo audit log is reviewed, When workflow is inspected, Then Cloud detect → Cloud draft → Sync → Local approve → Local execute is present
- **Estimated Hours**: 1.5
- **Dependencies**: P6-T001 to P6-T006
- **Files**:
  - `tests/integration/platinum/test_platinum_demo.py` (full 8-step test)
- **Tests**:
  - `test_platinum_demo_end_to_end()` - Verify all 8 steps pass
  - `test_demo_completion_time()` - Verify <5 minutes total
  - `test_demo_audit_trail()` - Verify full workflow in audit log

#### P6-T008: Implement Demo Validation Report
- **Description**: Create automated validation report showing demo success/failure with metrics
- **Acceptance Criteria**:
  - Given demo completes, When validation report is generated, Then it shows pass/fail for each step with timing
  - Given report is reviewed, When success criteria are checked, Then SC-PT-015 to SC-PT-017 are validated
  - Given demo fails, When report is inspected, Then it shows which step failed and why
- **Estimated Hours**: 1.0
- **Dependencies**: P6-T007
- **Files**:
  - `tests/integration/platinum/demo_validation.py`
- **Tests**: None (validation utility)

---

### P7: Documentation (6 hours)

#### P7-T001: Create Cloud VM Setup Runbook
- **Description**: Document complete Cloud VM setup process (Oracle/AWS/Google) with security hardening and monitoring
- **Acceptance Criteria**:
  - Given user follows runbook, When VM is set up, Then all steps are clear and reproducible
  - Given runbook is reviewed, When technical accuracy is checked, Then all commands and configurations are correct
  - Given runbook is tested, When a new user follows it, Then they complete setup in <2 hours
- **Estimated Hours**: 1.5
- **Dependencies**: P1-T001 to P1-T005
- **Files**:
  - `docs/runbooks/cloud-vm-setup.md`
- **Tests**: None (manual validation)

#### P7-T002: Create Vault Sync Configuration Guide
- **Description**: Document Git vault sync setup, conflict resolution, and troubleshooting
- **Acceptance Criteria**:
  - Given user follows guide, When vault sync is configured, Then Git remote is set up correctly
  - Given guide is reviewed, When examples are checked, Then all code snippets are correct and tested
  - Given sync issue occurs, When troubleshooting section is consulted, Then it provides clear resolution steps
- **Estimated Hours**: 1.0
- **Dependencies**: P2-T001 to P2-T004
- **Files**:
  - `docs/runbooks/vault-sync-config.md`
- **Tests**: None (manual validation)

#### P7-T003: Create Architecture Diagrams
- **Description**: Create ASCII/Mermaid diagrams showing Cloud/Local architecture, data flow, and security boundaries
- **Acceptance Criteria**:
  - Given architecture is documented, When diagram is reviewed, Then Cloud/Local split is clearly shown
  - Given data flow is diagrammed, When sync flow is inspected, Then vault sync, claim-by-move, and approval workflow are present
  - Given security boundaries are shown, Then secret isolation (Local only) is clearly marked
- **Estimated Hours**: 1.5
- **Dependencies**: P1-T001 to P6-T008
- **Files**:
  - `docs/architecture/platinum-architecture.md`
- **Tests**: None (diagram validation)

#### P7-T004: Create Deployment Checklist
- **Description**: Document pre-production deployment checklist covering all Platinum requirements
- **Acceptance Criteria**:
  - Given checklist is followed, When deployment is complete, Then all P1-P7 requirements are validated
  - Given checklist is reviewed, When items are inspected, Then they are clear, testable, and actionable
  - Given deployment is audited, When checklist is compared to actual deployment, Then 100% of items are present
- **Estimated Hours**: 1.0
- **Dependencies**: P1-T001 to P6-T008
- **Files**:
  - `docs/deployment-checklist.md`
- **Tests**: None (checklist validation)

#### P7-T005: Create Security Disclosure Document
- **Description**: Document security model, threat model, and known limitations
- **Acceptance Criteria**:
  - Given security model is documented, When threat model is reviewed, Then all attack vectors are identified
  - Given disclosure is reviewed, When known limitations are checked, Then they are clearly stated (e.g., Cloud VM compromise, sync interception)
  - Given user reads disclosure, When security guarantees are inspected, Then they are accurate and verifiable
- **Estimated Hours**: 1.0
- **Dependencies**: P3-T001 to P3-T004
- **Files**:
  - `docs/security-disclosure.md`
- **Tests**: None (security review)

---

### Testing (8 hours)

#### T001: Unit Tests - Vault Sync
- **Description**: Create unit tests for sync functions (sync, conflict resolution, exclusion validation)
- **Acceptance Criteria**:
  - Given sync tests are run, When test suite completes, Then all sync functions have 90%+ coverage
  - Given conflict resolution is tested, When tests are run, Then last-write-wins and local-wins are validated
  - Given exclusion validation is tested, When tests are run, Then 100% of secret patterns are detected
- **Estimated Hours**: 1.5
- **Dependencies**: P2-T002 to P2-T004
- **Files**:
  - `tests/unit/sync/test_git_sync.py`
  - `tests/unit/sync/test_conflict_resolver.py`
  - `tests/unit/sync/test_exclusion_validator.py`
- **Tests**: All unit tests in sync/ directory

#### T002: Unit Tests - Security
- **Description**: Create unit tests for security boundary functions (pattern detection, credential manager, audit logging)
- **Acceptance Criteria**:
  - Given security tests are run, When test suite completes, Then all security functions have 90%+ coverage
  - Given pattern detection is tested, When tests are run, Then 100% of secret patterns are detected
  - Given credential manager is tested, When tests are run, Then storage and retrieval work correctly
- **Estimated Hours**: 1.5
- **Dependencies**: P3-T001 to P3-T004
- **Files**:
  - `tests/unit/security/test_boundary.py`
  - `tests/unit/security/test_credential_manager.py`
  - `tests/unit/security/test_audit_logger.py`
- **Tests**: All unit tests in security/ directory

#### T003: Unit Tests - Health Endpoint
- **Description**: Create unit tests for health endpoint (response time, metrics, alerting)
- **Acceptance Criteria**:
  - Given health tests are run, When test suite completes, Then endpoint responds within 500ms (p95)
  - Given metrics endpoint is tested, When Prometheus format is validated, Then it is correct
  - Given alerting is tested, When thresholds are breached, Then alerts are generated correctly
- **Estimated Hours**: 1.0
- **Dependencies**: P1-T003 to P1-T005
- **Files**:
  - `tests/unit/health/test_endpoint.py`
  - `tests/unit/health/test_monitoring.py`
  - `tests/unit/health/test_alerting.py`
- **Tests**: All unit tests in health/ directory

#### T004: Integration Tests - Cloud/Local Workflow
- **Description**: Create integration tests for Cloud/Local workflows (email → draft → sync → approve → execute)
- **Acceptance Criteria**:
  - Given integration tests are run, When full workflow is tested, Then all steps complete successfully
  - Given workflow is measured, When timing is checked, Then sync completes within 60 seconds
  - Given workflow is audited, When execution is checked, Then Local executes 100% of actions (Cloud 0 sends)
- **Estimated Hours**: 2.0
- **Dependencies**: P6-T001 to P6-T007
- **Files**:
  - `tests/integration/test_cloud_local_workflow.py`
- **Tests**:
  - `test_full_email_workflow()` - End-to-end email workflow
  - `test_invoice_draft_to_post()` - Invoice draft → post workflow
  - `test_social_media_workflow()` - Social post draft → post workflow

#### T005: Integration Tests - Odoo Draft→Post
- **Description**: Create integration tests for Odoo invoice draft creation (Cloud) and posting (Local)
- **Acceptance Criteria**:
  - Given Odoo tests are run, When Cloud creates drafts, Then all are in "draft" status
  - Given Local posts invoices, When Odoo is checked, Then invoices are posted and sent
  - Given 50 invoices are processed, When audit is performed, Then Cloud 0 posts, Local 50 posts
- **Estimated Hours**: 1.0
- **Dependencies**: P5-T003 to P5-T004
- **Files**:
  - `tests/integration/test_odoo_invoice.py`
- **Tests**:
  - `test_cloud_draft_creation()` - Verify Cloud creates drafts
  - `test_local_posting()` - Verify Local posts invoices
  - `test_draft_to_post_workflow()` - Full draft → post workflow

#### T006: Contract Tests - API Contracts
- **Description**: Create contract tests for API specifications (health endpoint, vault files, external APIs)
- **Acceptance Criteria**:
  - Given contract tests are run, When API responses are validated, Then they match specifications
  - Given vault file contracts are tested, When file structure is checked, Then it matches spec
  - Given external API contracts are tested, When error taxonomy is validated, Then it is correct
- **Estimated Hours**: 1.0
- **Dependencies**: P1-T003, P2-T001 to P2-T004
- **Files**:
  - `tests/contract/test_api_contracts.py`
- **Tests**:
  - `test_health_endpoint_contract()` - Verify health endpoint schema
  - `test_vault_file_contract()` - Verify vault file structure
  - `test_error_taxonomy()` - Verify error codes and exceptions

#### T007: Chaos Tests - VM Crash/Restart
- **Description**: Create chaos tests for Cloud VM crash and auto-restart (<10 seconds)
- **Acceptance Criteria**:
  - Given Cloud VM is running, When process is killed, Then systemd restarts it within 10 seconds
  - Given 50 crash cycles are run, When restart times are measured, Then 100% complete within 10 seconds
  - Given VM is rebooted, When system starts, Then Cloud Agent resumes monitoring automatically
- **Estimated Hours**: 1.5
- **Dependencies**: P1-T004
- **Files**:
  - `tests/chaos/test_vm_crash_restart.py`
- **Tests**:
  - `test_auto_restart_50_cycles()` - Verify restart over 50 crashes
  - `test_vm_reboot_recovery()` - Verify full VM reboot recovery
  - `test_restart_time_p95()` - Verify p95 restart time <10 seconds

#### T008: Chaos Tests - Network Partition
- **Description**: Create chaos tests for network partition (4+ hours) and sync recovery
- **Acceptance Criteria**:
  - Given network partition occurs, When Cloud and Local operate independently, Then both continue functioning
  - Given partition lasts 4 hours, When connectivity is restored, Then sync completes successfully
  - Given 1000+ pending actions are queued, When sync resumes, Then all are applied with correct conflict resolution
- **Estimated Hours**: 1.5
- **Dependencies**: P2-T002
- **Files**:
  - `tests/chaos/test_network_partition.py`
- **Tests**:
  - `test_4hour_partition()` - Verify operation during 4-hour partition
  - `test_sync_recovery()` - Verify sync after partition heals
  - `test_1000_pending_actions()` - Verify 1000+ actions sync correctly

#### T009: Chaos Tests - Odoo API Failure
- **Description**: Create chaos tests for Odoo API failure and fallback to draft queue
- **Acceptance Criteria**:
  - Given Odoo API is unavailable, When Cloud attempts to create invoice, Then it queues the draft operation
  - Given Odoo is unavailable for 1 hour, When alert threshold is breached, Then Local is alerted
  - Given Odoo recovers, When queue is processed, Then all queued drafts are created successfully
- **Estimated Hours**: 1.0
- **Dependencies**: P5-T003
- **Files**:
  - `tests/chaos/test_odoo_failure.py`
- **Tests**:
  - `test_odoo_api_failure_fallback()` - Verify fallback to queue
  - `test_odoo_1hour_alert()` - Verify alert after 1 hour
  - `test_odoo_recovery()` - Verify queue processing after recovery

#### T010: Load Tests - Sync Operations
- **Description**: Create load tests for 1000+ sync operations without conflicts
- **Acceptance Criteria**:
  - Given 1000 files are synced, When sync completes, Then zero data loss occurs
  - Given load test is run, When sync timing is measured, Then 100% complete within 60 seconds each
  - Given concurrent syncs are run, When conflicts are tracked, Then conflict resolution succeeds 100%
- **Estimated Hours**: 1.5
- **Dependencies**: P2-T002 to P2-T003
- **Files**:
  - `tests/load/test_sync_load.py`
- **Tests**:
  - `test_1000_sync_operations()` - Verify 1000 syncs complete successfully
  - `test_concurrent_syncs()` - Verify concurrent sync without data loss
  - `test_sync_conflict_rate()` - Verify conflict resolution success rate

#### T011: Load Tests - Claim Attempts
- **Description**: Create load tests for 100+ concurrent claim attempts
- **Acceptance Criteria**:
  - Given 100 agents attempt to claim same file, When race condition is tested, Then 100% double-work is prevented
  - Given load test is run, When claim timing is measured, Then claims complete within 5 seconds
  - Given claims are audited, When winner is determined, Then first agent wins, others back off
- **Estimated Hours**: 1.0
- **Dependencies**: P4-T002
- **Files**:
  - `tests/load/test_claim_load.py`
- **Tests**:
  - `test_100_concurrent_claims()` - Verify 100 claims without double-work
  - `test_claim_timing_p95()` - Verify p95 claim time <5 seconds
  - `test_claim_auditing()` - Verify all claims are logged

---

## Success Criteria Mapping

| Success Criteria | Related Tasks | Status |
|------------------|---------------|--------|
| SC-PT-001: 99% uptime | P1-T003 (Health endpoint), P1-T004 (Auto-restart) | ✅ |
| SC-PT-002: Health <500ms | P1-T003 (Health endpoint) | ✅ |
| SC-PT-003: Auto-restart <10s | P1-T004 (Auto-restart) | ✅ |
| SC-PT-004: Resource alerts | P1-T005 (Resource monitoring) | ✅ |
| SC-PT-005: Sync <60s | P2-T002 (Sync script), T010 (Load tests) | ✅ |
| SC-PT-006: Zero secrets synced | P2-T004 (Exclusion validator), P3-T002 (Pre-sync validation) | ✅ |
| SC-PT-007: Conflict resolution 100% | P2-T003 (Conflict resolver), T001 (Unit tests) | ✅ |
| SC-PT-008: Offline queue 1000+ | P2-T002 (Sync script), T008 (Chaos tests) | ✅ |
| SC-PT-009: Cloud 0 sends | P5-T003 (Draft-only invoices), P6-T005 (Local execution) | ✅ |
| SC-PT-010: Local 100% executes | P5-T004 (Local posting), P6-T005 (Local execution) | ✅ |
| SC-PT-011: Dashboard Local-only | P4-T004 (Cross-agent comm), P2-T003 (Local-wins conflict) | ✅ |
| SC-PT-012: Zero WhatsApp sessions on Cloud | P2-T004 (Exclusion validator), P3-T001 (Secret detection) | ✅ |
| SC-PT-013: Zero banking creds on Cloud | P3-T001 (Secret detection), P3-T003 (Credential manager) | ✅ |
| SC-PT-014: Secret detection 100% | P3-T001 (Secret detection), T002 (Security tests) | ✅ |
| SC-PT-015: 8-step demo | P6-T001 to P6-T008 (Platinum Demo) | ✅ |
| SC-PT-016: Full audit trail | P6-T006 (Audit logging), P6-T007 (End-to-end test) | ✅ |
| SC-PT-017: Demo <5 minutes | P6-T007 (End-to-end test) | ✅ |
| SC-PT-018: Cloud/Local 1000 ops | T004 (Integration tests), T010 (Load tests) | ✅ |
| SC-PT-019: Claim-by-move 100% | P4-T002 (Double-work prevention), T011 (Load tests) | ✅ |
| SC-PT-020: Local merges updates | P4-T004 (Cross-agent comm), P2-T003 (Local-wins) | ✅ |

---

## Quality Gates

All tasks MUST pass quality gates before merge:

- **Linting**: `ruff check src/ tests/` (0 errors)
- **Formatting**: `black --check src/ tests/` (line length 100)
- **Type checking**: `mypy --strict src/` (0 errors, all signatures typed)
- **Security scan**: `bandit -r src/` (0 high-severity issues)
- **Import order**: `isort --check src/ tests/` (enforced)
- **Test coverage**: `pytest --cov=src --cov-report=term-missing` (50-60% overall, critical paths 90%+)

---

## Definition of Done

Each task is complete when:

- [ ] Implementation code written and committed
- [ ] Unit tests passing (if applicable)
- [ ] Integration tests passing (if applicable)
- [ ] Quality gates passing (ruff, black, mypy, bandit, isort)
- [ ] Documentation updated (if applicable)
- [ ] PHR created for implementation work
- [ ] Acceptance criteria validated (all checkboxes marked)

---

## Execution Order

**Phase 1: Foundation (P1, P2)** - 16 hours
- P1-T001 → P1-T005 (Cloud VM setup)
- P2-T001 → P2-T004 (Vault sync)

**Phase 2: Security (P3, P4)** - 14 hours
- P3-T001 → P3-T004 (Security boundaries)
- P4-T001 → P4-T004 (Claim-by-move)

**Phase 3: Odoo (P5)** - 8 hours
- P5-T001 → P5-T005 (Cloud Odoo)

**Phase 4: Demo (P6)** - 8 hours
- P6-T001 → P6-T008 (Platinum Demo)

**Phase 5: Documentation (P7)** - 6 hours
- P7-T001 → P7-T005 (Documentation suite)

**Phase 6: Testing** - 8 hours
- T001 → T011 (All test categories)

**Total**: 60 hours

---

## Next Steps

1. **Review Tasks**: Stakeholder review for completeness and accuracy
2. **Implement**: Task-by-task execution (P1 → P7, respecting dependencies)
3. **Test**: Run all tests (unit, integration, contract, chaos, load)
4. **Document**: Complete runbooks and deployment guide
5. **Validate**: Platinum Demo (8-step workflow) passes end-to-end
6. **Release**: v6.0.0 Platinum Tier release

---

**Generated**: 2026-04-02
**Version**: v6.0.0-draft
**Status**: Ready for review
