# Feature Specification: Platinum Tier - Cloud + Local Executive

**Feature Branch**: `004-platinum-tier-cloud-executive`
**Created**: 2026-04-02
**Status**: Draft
**Input**: Platinum Tier Autonomous Employee - Production-ready 24/7 AI agent with Cloud/Local split architecture, vault synchronization, draft-only operations, and strict security boundaries

---

## Executive Summary

Platinum Tier (v6.0.0) introduces a revolutionary two-agent architecture that enables true 24/7 autonomous operation while maintaining strict security boundaries. The system splits responsibilities between a **Cloud Agent** (always-on, draft-only operations) and a **Local Agent** (execution authority, user workstation), synchronized via Git or Syncthing vault replication.

The key innovation is **work-zone specialization**: the Cloud monitors, detects, and prepares drafts continuously while the user is offline, but only the Local agent can execute approved actions. This architecture achieves continuous monitoring and draft preparation without compromising security, as sensitive secrets (credentials, tokens, banking data) never leave the Local environment. The business value is clear: the AI employee works around the clock, preparing everything for execution, while the user retains final control and approves actions when they come online.

**Estimated Implementation Time**: 60+ hours across 7 Platinum requirements (P1-P7)

**Key Innovation**: Two-agent architecture enabling 24/7 operation with strict security boundaries through vault synchronization, draft-only cloud operations, and claim-by-move ownership

**Business Value**: Continuous monitoring and draft preparation while user is offline; Local retains execution authority for security-critical actions

---

## User Scenarios & Testing

### User Story 1 - Cloud 24/7 Monitoring (Priority: P0)

As a **business owner**, I want **the Cloud Agent to monitor email, WhatsApp, and business metrics continuously** so that **no opportunities or urgent matters are missed even when I'm offline or sleeping**.

**Why this priority**: P0 (Critical) - This is the foundational value proposition of Platinum Tier. Without 24/7 monitoring, the system provides no advantage over Gold Tier's local-only operation. This must work independently to deliver immediate business value.

**Independent Test**: Can be tested by deploying Cloud Agent on a VM, configuring watchers (Gmail, WhatsApp), and verifying detection of incoming messages while Local workstation is offline for 8+ hours. Success is measured by Cloud detecting and logging all events within 2 minutes of occurrence.

**Acceptance Scenarios**:

1. **Given** Local workstation is offline for 8 hours, **When** an urgent client email arrives at 3 AM, **Then** Cloud Agent detects it within 2 minutes and creates a draft reply in the vault
2. **Given** Cloud Agent is running on VM, **When** a WhatsApp message with keyword "urgent" arrives, **Then** Cloud flags it in the Updates folder and prepares a draft response
3. **Given** Cloud Agent has been running for 24 hours, **When** Local comes online, **Then** all detected events are synced and presented in a briefing dashboard
4. **Given** Cloud VM experiences a restart mid-operation, **When** it comes back online, **Then** it resumes monitoring without losing track of previously processed messages

---

### User Story 2 - Draft-Only Operations (Priority: P0)

As a **security-conscious user**, I want **the Cloud Agent to prepare drafts but never execute actions** so that **I retain final approval authority over all outbound communications and financial transactions**.

**Why this priority**: P0 (Critical) - This is the core security boundary that enables safe cloud deployment. Without draft-only enforcement, the Cloud would require access to execution credentials, violating the security model.

**Independent Test**: Can be tested by configuring Cloud Agent with read-only API keys and draft creation permissions (no send/execute permissions). Verify over 100 operations that Cloud creates drafts (emails, invoices, social posts) but zero are sent/executed without Local approval.

**Acceptance Scenarios**:

1. **Given** Cloud Agent detects an email requiring a reply, **When** it processes the email, **Then** it creates a draft reply file in `/Drafts/Email/` but does not send it
2. **Given** Cloud Agent identifies a business metric threshold breach, **When** it prepares a CEO briefing update, **Then** it writes to `/Updates/Briefing/` but does not post to social media
3. **Given** Cloud Agent processes an incoming invoice request, **When** it creates an Odoo invoice, **Then** the invoice is saved as "draft" status (unposted) in Odoo
4. **Given** Cloud Agent has prepared 50 draft emails over 24 hours, **When** Local reviews the draft queue, **Then** all 50 drafts are present and unsent, awaiting approval

---

### User Story 3 - Vault Synchronization (Priority: P0)

As a **user**, I want **my Cloud and Local vaults to stay automatically synchronized** so that **drafts prepared by Cloud are available for my review and execution on Local, and my approvals are visible to Cloud**.

**Why this priority**: P0 (Critical) - Vault sync is the communication mechanism between Cloud and Local agents. Without reliable sync, the two-agent architecture fails. Must work independently with either Git or Syncthing.

**Independent Test**: Can be tested by setting up Git or Syncthing sync between two directories (simulating Cloud and Local), creating files on both sides, and verifying sync completes within 60 seconds with proper conflict resolution. Test with 1000+ files and network interruptions.

**Acceptance Scenarios**:

1. **Given** Cloud creates a draft email in `/Drafts/Email/`, **When** sync runs (within 60 seconds), **Then** the draft appears on Local vault ready for review
2. **Given** Local approves a draft and moves it to `/In_Progress/Local/`, **When** sync completes, **Then** Cloud sees the file is claimed and does not modify it
3. **Given** both Cloud and Local modify the same file simultaneously, **When** sync encounters the conflict, **Then** it resolves using last-write-wins (or local-wins for Dashboard.md)
4. **Given** network partition lasts 4 hours, **When** connectivity is restored, **Then** sync completes successfully with all queued changes applied in correct order

---

### User Story 4 - Security Boundary Enforcement (Priority: P0)

As a **user**, I want **my secrets (credentials, tokens, banking data) to never sync to the Cloud** so that **even if the Cloud VM is compromised, my sensitive data remains secure**.

**Why this priority**: P0 (Critical) - This is the non-negotiable security guarantee of Platinum Tier. A single secret leak to Cloud would violate trust and expose the user to financial/identity risk.

**Independent Test**: Can be tested by auditing Cloud vault contents after 30 days of operation. Verify zero files matching secret patterns (.env, tokens, sessions, banking, credentials) exist on Cloud. Attempt to place a secret file in sync path and verify it is blocked and logged.

**Acceptance Scenarios**:

1. **Given** Local vault contains `.env` file with API keys, **When** sync runs, **Then** the file is excluded via .gitignore and never appears on Cloud
2. **Given** Cloud Agent attempts to access a secret for an operation, **When** it checks the vault, **Then** it finds only draft data (no credentials) and requests Local to execute
3. **Given** a malicious process tries to add a credential file to the sync folder, **When** the security boundary detects it, **Then** the file is blocked, quarantined, and an alert is logged
4. **Given** WhatsApp session files exist on Local, **When** sync runs, **Then** session files are excluded and zero WhatsApp session data appears on Cloud

---

### User Story 5 - Claim-by-Move Ownership (Priority: P1)

As a **system designer**, I want **agents to claim files by moving them to agent-specific folders** so that **double-work is prevented when Cloud and Local might otherwise modify the same task**.

**Why this priority**: P1 (High) - This prevents race conditions and wasted computation. While not as critical as security or monitoring, it ensures efficient operation and prevents confusing state where both agents work on the same task.

**Independent Test**: Can be tested by simulating concurrent Cloud and Local operations on the same task file. Verify that when one agent moves a file to `/In_Progress/<agent>/`, the other agent detects the claim and stops working on it. Test 100+ concurrent claim attempts.

**Acceptance Scenarios**:

1. **Given** Cloud detects an email and starts drafting a reply, **When** it claims the file by moving to `/In_Progress/Cloud/`, **Then** Local sees the claim marker and does not process the same email
2. **Given** Local approves and executes a draft, **When** it moves the file to `/In_Progress/Local/`, **Then** Cloud detects the claim and updates its task tracking accordingly
3. **Given** both Cloud and Local attempt to claim the same file simultaneously, **When** the race condition occurs, **Then** one agent wins (first move) and the other detects the claim and backs off
4. **Given** Cloud claims a file but crashes before completing, **When** Local detects the stale claim (>5 minutes old), **Then** Local can reclaim the file and complete the task

---

### User Story 6 - Cloud Odoo Integration (Priority: P1)

As a **business owner**, I want **the Cloud Agent to create draft invoices in Odoo** so that **I can review and approve them locally before they are sent to customers**.

**Why this priority**: P1 (High) - Odoo integration is a key Gold Tier feature that must be adapted for Platinum's draft-only model. This enables continuous accounting operations while maintaining financial control.

**Independent Test**: Can be tested by configuring Cloud with Odoo draft-only permissions (no post/send permissions). Create 50 draft invoices via Cloud, verify all are in "draft" status in Odoo. Local then approves and posts 10 invoices, verifying they are sent to customers.

**Acceptance Scenarios**:

1. **Given** Cloud detects a completed service request via email, **When** it creates an Odoo invoice, **Then** the invoice is created in "draft" status (unposted) with all line items populated
2. **Given** Local reviews a draft invoice, **When** the user approves it, **Then** Local posts the invoice via Odoo API and sends it to the customer
3. **Given** Odoo cloud service is temporarily unavailable, **When** Cloud attempts to create a draft invoice, **Then** it queues the operation and retries after service restoration
4. **Given** Cloud has created 20 draft invoices over 24 hours, **When** Local reviews the invoice queue, **Then** all 20 drafts are present in Odoo with correct amounts and customer details

---

### User Story 7 - Platinum Demo Workflow (Priority: P0)

As a **stakeholder**, I want **to see a complete end-to-end demonstration of the Platinum architecture** so that **I can verify the system works as advertised: email arrives while I'm offline, Cloud drafts a reply, and Local sends it when I approve**.

**Why this priority**: P0 (Critical) - This is the minimum passing gate for Platinum Tier. All 8 steps must work seamlessly to demonstrate the value proposition. This story integrates all other stories into a single workflow.

**Independent Test**: Can be tested by running the full 8-step demo scenario: (1) Local goes offline, (2) Email arrives, (3) Cloud detects email, (4) Cloud drafts reply, (5) Cloud syncs draft to vault, (6) Local comes online, (7) Local reviews and approves draft, (8) Local sends email. Measure total time and verify audit trail.

**Acceptance Scenarios**:

1. **Given** Local workstation is offline, **When** an email arrives at client@example.com with subject "Project Update Request", **Then** Cloud detects it within 2 minutes (Step 1-2)
2. **Given** Cloud detects the email, **When** it processes the content, **Then** it drafts a professional reply acknowledging the request and promising follow-up (Step 3-4)
3. **Given** Cloud has drafted the reply, **When** sync runs, **Then** the draft appears in Local vault within 60 seconds (Step 5)
4. **Given** Local comes online and reviews the draft queue, **When** the user approves the draft, **Then** Local sends the email and logs the completion in the audit trail (Step 6-8)
5. **Given** the full 8-step workflow completes, **When** the audit log is reviewed, **Then** all steps are present with timestamps showing Cloud detect → Cloud draft → Sync → Local approve → Local execute

---

### Edge Cases

- **Email arrives while Local offline for 8 hours**: Cloud detects, drafts, and queues all emails; Local processes entire queue upon return
- **Vault sync conflict (both agents modify same file)**: Conflict resolution applies (last-write-wins generally, local-wins for Dashboard.md); audit log records conflict
- **Cloud VM restarts mid-operation**: Cloud resumes from last known state; in-progress drafts are marked for review; no data loss
- **Network partition during sync**: Both agents operate independently; sync queue builds up; partition heals and sync completes with conflict resolution
- **Odoo cloud unavailable**: Cloud queues draft invoice operations; retries with exponential backoff; alerts Local if unavailable >1 hour
- **Security boundary breach attempt**: Unauthorized secret file creation is blocked, quarantined, and logged; Local is alerted immediately
- **A2A communication failure (Phase 2)**: System falls back to file-based handoffs; degraded but functional operation continues
- **Cloud VM resource exhaustion (>90% disk)**: Cloud alerts Local, pauses non-critical operations, and requests intervention
- **Sync folder exceeds 10GB**: System alerts user to archive old data; sync performance degrades gracefully
- **Local workstation crashes with unapproved drafts**: Cloud continues monitoring; drafts remain in vault; Local recovers and processes queue on restart

---

## Requirements

### Functional Requirements

#### Cloud Deployment (FR-PT-001 to FR-PT-006)

- **FR-PT-001**: System MUST provision a Cloud VM on Oracle Cloud Free Tier, AWS EC2, or Google Cloud with minimum 2GB RAM and 2 vCPU
- **FR-PT-002**: System MUST expose a health endpoint at `http://<cloud-vm>:8000/health` responding with status, uptime, and resource metrics
- **FR-PT-003**: System MUST auto-restart the Cloud Agent process within 10 seconds of crash detection using systemd or PM2
- **FR-PT-004**: System MUST monitor CPU, memory, and disk utilization continuously and log metrics every 60 seconds
- **FR-PT-005**: System MUST trigger alerts when CPU/Memory >80% or Disk >90% for more than 5 minutes
- **FR-PT-006**: System MUST measure and report uptime SLA (target: 99% over 30-day period) via health endpoint logs

#### Work-Zone Specialization (FR-PT-007 to FR-PT-012)

- **FR-PT-007**: Cloud Agent MUST create draft email replies in `/Drafts/Email/` folder but MUST NOT send emails directly
- **FR-PT-008**: Cloud Agent MUST create draft social media posts in `/Drafts/Social/` folder but MUST NOT post to platforms directly
- **FR-PT-009**: Cloud Agent MUST create draft Odoo invoices in "draft" status (unposted) but MUST NOT post or send invoices
- **FR-PT-010**: Local Agent MUST provide an approval workflow for reviewing and approving/rejecting drafts from Cloud
- **FR-PT-011**: Local Agent MUST have exclusive execution authority for sending emails, posting social media, and posting invoices
- **FR-PT-012**: Dashboard.md file MUST be written only by Local Agent (single-writer rule) to prevent sync conflicts

#### Vault Sync (FR-PT-013 to FR-PT-018)

- **FR-PT-013**: System MUST configure Git remote (GitHub/GitLab private repo) OR Syncthing for vault synchronization between Cloud and Local
- **FR-PT-014**: System MUST sync vault changes within 60 seconds of detection (measured over 100 sync operations)
- **FR-PT-015**: System MUST resolve sync conflicts using last-write-wins strategy, except Dashboard.md which uses local-wins
- **FR-PT-016**: System MUST exclude sensitive files from sync: `.env`, `tokens/`, `sessions/`, `banking/`, `credentials/`, `*.key`, `*.pem`
- **FR-PT-017**: System MUST provide sync status monitoring showing last sync time, pending changes, and conflict count
- **FR-PT-018**: System MUST handle offline queue management supporting 1000+ pending actions during extended network partitions

#### Security Boundaries (FR-PT-019 to FR-PT-024)

- **FR-PT-019**: System MUST enforce .gitignore rules preventing secret files from being added to version control or sync
- **FR-PT-020**: System MUST integrate with OS Credential Manager (Windows Credential Manager, macOS Keychain, or 1Password CLI) for Local secret storage
- **FR-PT-021**: System MUST validate secret access attempts and block any Cloud Agent access to Local-only secrets
- **FR-PT-022**: Cloud Agent MUST operate with zero secrets stored locally; all credentials must be on Local only
- **FR-PT-023**: Local Agent MUST store all secrets (API keys, tokens, banking credentials) in OS credential manager, never in vault files
- **FR-PT-024**: System MUST detect and log security boundary breach attempts with 100% detection rate and alert Local immediately

#### Claim-by-Move (FR-PT-025 to FR-PT-027)

- **FR-PT-025**: System MUST implement file ownership detection via `/In_Progress/<agent>/` folder markers (Cloud or Local)
- **FR-PT-026**: System MUST prevent double-work by detecting claim markers and backing off when another agent has claimed a file
- **FR-PT-027**: System MUST provide cross-agent communication via Update files (`/Updates/<domain>/`) and Signal files (`/Signals/<domain>/`)

#### Cloud Odoo (FR-PT-028 to FR-PT-030)

- **FR-PT-028**: Cloud Odoo deployment MUST use HTTPS with SSL certificates from Let's Encrypt for all external API calls
- **FR-PT-029**: System MUST perform automated daily backups of Odoo PostgreSQL database with encrypted storage (AES-256)
- **FR-PT-030**: Cloud Agent MUST create all Odoo invoices in "draft" status; Local Agent MUST have exclusive rights to post/send invoices

---

### Key Entities

1. **Cloud Agent**: 24/7 always-on agent deployed on cloud VM (Oracle/AWS/Google) with draft-only capabilities; monitors email, WhatsApp, and business metrics; creates drafts but cannot execute actions

2. **Local Agent**: User workstation agent running on Windows 10/11 with execution authority; reviews and approves Cloud drafts; stores all secrets in OS credential manager; sends emails, posts social media, posts invoices

3. **Vault Sync**: Git or Syncthing synchronization mechanism replicating vault files between Cloud and Local; enforces sync exclusions for secrets; resolves conflicts; completes within 60 seconds

4. **Claim File**: Ownership marker file in `/In_Progress/<agent>/` folder indicating which agent (Cloud or Local) is working on a task; prevents double-work

5. **Update File**: Status update file in `/Updates/<domain>/` folder written by Cloud to communicate detected events, draft status, and business metrics to Local

6. **Signal File**: Alert/notification file in `/Signals/<domain>/` folder used for urgent cross-agent communication (e.g., security breach alerts, critical event notifications)

7. **Sync Exclusion List**: Configuration defining files/folders never synced to Cloud: `.env`, `tokens/`, `sessions/`, `banking/`, `credentials/`, `*.key`, `*.pem`, WhatsApp session files

8. **Draft Invoice**: Odoo invoice created by Cloud Agent in "draft" status (unposted); contains all line items and customer details; requires Local approval to post and send

9. **Draft Email Reply**: Email reply drafted by Cloud Agent in `/Drafts/Email/` folder; includes subject, recipients, body, attachments; requires Local approval to send

10. **Draft Social Post**: Social media post drafted by Cloud Agent in `/Drafts/Social/` folder; includes platform, content, media, scheduling; requires Local approval to post

11. **A2A Message** (Phase 2 - Optional): Direct agent-to-agent communication message via HTTP/WebSocket; replaces file-based handoffs for real-time coordination

12. **Platinum Demo Workflow**: 8-step end-to-end validation scenario: (1) Local offline, (2) Email arrives, (3) Cloud detects, (4) Cloud drafts, (5) Sync to Local, (6) Local reviews, (7) Local approves, (8) Local executes

---

## Success Criteria

### Cloud Deployment

- **SC-PT-001**: Cloud VM achieves 99% uptime over a 30-day measurement period (verified via health endpoint logs)
- **SC-PT-002**: Health endpoint responds within 500ms (p95 latency) under normal load (verified via 1000 health checks)
- **SC-PT-003**: Auto-restart completes within 10 seconds of crash detection (verified via 50 crash-restart cycles)
- **SC-PT-004**: Resource alerts trigger at >80% CPU/Memory and >90% disk within 5 minutes of threshold breach (verified via 20 test scenarios)

### Vault Sync

- **SC-PT-005**: Sync completes within 60 seconds (measured over 100 sync operations with varying file counts)
- **SC-PT-006**: Zero secret files synced to Cloud (verified via audit of Cloud vault after 30 days of operation)
- **SC-PT-007**: Conflict resolution succeeds in 100% of test cases (verified via 100 intentional conflict scenarios)
- **SC-PT-008**: Offline queue handles 1000+ pending actions without data loss (verified via stress test with network partition)

### Work-Zone Specialization

- **SC-PT-009**: Cloud creates draft emails (0 sends in 100 test cases) - verified via audit of sent email logs
- **SC-PT-010**: Local executes 100% of approved actions (verified via audit trail of all executed actions)
- **SC-PT-011**: Dashboard.md written only by Local (verified via git blame or file audit over 30 days)

### Security

- **SC-PT-012**: Zero WhatsApp session files on Cloud (verified via file system audit after 30 days)
- **SC-PT-013**: Zero banking credentials on Cloud (verified via file content scan and audit)
- **SC-PT-014**: Secret access attempts blocked and logged with 100% detection (verified via 50 breach attempt tests)

### Platinum Demo

- **SC-PT-015**: All 8 demo steps complete successfully in single end-to-end test (verified via demo run-through)
- **SC-PT-016**: Full audit trail present showing Cloud detect → Local execute flow (verified via log inspection)
- **SC-PT-017**: Demo completes within 5 minutes when Local is online (measured from email arrival to send confirmation)

### Integration

- **SC-PT-018**: Cloud/Local operate concurrently without conflicts over 1000 operations (verified via stress test)
- **SC-PT-019**: Claim-by-move prevents 100% of double-work attempts (verified via 100 concurrent claim scenarios)
- **SC-PT-020**: Local merges Cloud updates every 5 minutes (±30 seconds) when online (verified via 100 sync measurements)

---

## Assumptions

1. User has a cloud provider account (Oracle Cloud Free Tier, AWS, or Google Cloud) with billing enabled
2. User has a domain name available for Cloud VM deployment (for HTTPS/SSL certificate provisioning)
3. User has a stable internet connection on Local workstation (for vault sync operations)
4. Git (GitHub/GitLab private repo) OR Syncthing is installed and configured on both Cloud and Local systems
5. Odoo Community v19+ is available and deployed for cloud accounting integration
6. User reviews approval queue at least once daily (during business hours)
7. Cloud VM has minimum 2GB RAM and 2 vCPU resources allocated
8. Local workstation runs Windows 10/11 (for OS Credential Manager integration)
9. Vault size remains under 10GB (for efficient sync performance)
10. User has a backup strategy for Local vault (external drive or cloud backup service)
11. User has basic Linux administration knowledge for Cloud VM setup and maintenance
12. Cloud VM uses Ubuntu 22.04 LTS or similar Linux distribution for deployment

---

## Dependencies

### External System Dependencies

1. **Cloud VM Provider**: Oracle Cloud Free Tier, AWS EC2, or Google Cloud for 24/7 agent hosting
2. **Version Control / Sync**: GitHub/GitLab (private repo) for Git-based sync OR Syncthing for P2P sync
3. **SSL Certificates**: Let's Encrypt for HTTPS certificate provisioning on Cloud VM
4. **Odoo Platform**: Odoo Community v19+ for accounting and invoice management
5. **Database**: PostgreSQL 14+ for Odoo backend (bundled with Odoo deployment)
6. **Process Management**: systemd (built-in) or PM2 for Cloud Agent auto-restart and monitoring
7. **OS Credential Manager**: Windows Credential Manager (Local), or 1Password CLI for cross-platform secret storage
8. **Email Service**: Gmail API (existing Gold Tier dependency) for email monitoring and sending
9. **WhatsApp Service**: WhatsApp Web API (existing Gold Tier dependency) for message monitoring
10. **Domain DNS**: DNS provider for configuring domain records pointing to Cloud VM

---

## Non-Goals

Platinum Tier explicitly does **NOT** include:

1. **Multi-user support**: System is designed for single-user operation only; no concurrent user accounts or permissions
2. **Mobile app development**: No native iOS/Android applications; mobile access via web browser only
3. **Real-time collaboration features**: No simultaneous multi-user editing or live collaboration tools
4. **Custom LLM training**: System uses pre-trained LLM models only; no fine-tuning or custom model training
5. **Voice/video integration**: No voice call or video conferencing capabilities
6. **On-premise datacenter deployment**: Cloud deployment is via public cloud VM only (Oracle/AWS/Google); no private datacenter support
7. **A2A communication (Phase 1)**: Direct agent-to-agent HTTP/WebSocket communication is Phase 2 (optional)
8. **Multi-tenant SaaS offering**: System is single-tenant only; no multi-tenant architecture or SaaS business model support

---

## Security & Compliance

### Security Requirements

1. **SSH Key-Only Authentication**: Cloud VM MUST accept only SSH key authentication (no password authentication); SSH keys stored in Local OS credential manager
2. **Firewall Rules**: Cloud VM firewall MUST allow only ports 80 (HTTP), 443 (HTTPS), and 22 (SSH restricted to Local IP addresses)
3. **Encrypted Backups**: All Odoo database backups MUST be encrypted using AES-256 before storage; encryption keys stored in Local credential manager
4. **Secret Rotation**: All API keys, tokens, and credentials MUST be rotated every 90 days; rotation tracked and alerted
5. **Audit Log Retention**: System MUST retain audit logs for minimum 90 days; logs include all security events, draft creations, approvals, and executions
6. **Security Boundary Breach Detection**: System MUST detect and alert any attempt to sync secret files to Cloud; breaches logged and Local notified within 30 seconds
7. **Vault Sync Integrity**: System MUST verify vault sync integrity using checksums (SHA-256); corrupted syncs detected and rejected
8. **HTTPS Enforcement**: All external API calls from Cloud (Odoo, email, social media) MUST use HTTPS with valid SSL certificates
9. **Principle of Least Privilege**: Cloud Agent operates with minimal permissions (read-only for monitoring, draft-create for actions); execution rights reserved for Local
10. **Intrusion Detection**: Cloud VM MUST run basic intrusion detection (fail2ban or equivalent) to detect and block brute-force SSH attempts

### Compliance Considerations

- **Data Residency**: User is responsible for ensuring Cloud VM region complies with applicable data protection regulations (GDPR, CCPA, etc.)
- **Email Compliance**: Email monitoring and drafting must comply with applicable privacy laws; user responsible for consent management
- **Financial Records**: Odoo invoice handling must comply with local tax and accounting regulations; audit trail supports compliance

---

## Performance Budgets

### Latency Requirements

- **Cloud Health Endpoint**: <500ms response time (p95 latency) under normal load
- **Vault Sync Cycle**: <60 seconds per sync operation (measured over 100 cycles)
- **Claim-by-Move Detection**: <5 seconds to detect and respond to claim markers
- **Local Merge of Cloud Updates**: <5 minutes (±30 seconds) from Cloud write to Local availability
- **Draft Creation**: <10 seconds per draft action (email, invoice, social post)
- **Alert Propagation**: <30 seconds from Cloud detection to Local notification (via sync or signal file)

### Throughput Requirements

- **Email Monitoring**: Process up to 100 emails per hour without backlog
- **WhatsApp Monitoring**: Process up to 500 messages per hour without backlog
- **Sync Operations**: Handle 1000+ file changes per sync cycle without failure
- **Offline Queue**: Support 10,000+ queued actions during extended network partitions (>24 hours)

### Resource Caps

- **Cloud VM CPU**: Average <60% utilization; alert at >80% for 5+ minutes
- **Cloud VM Memory**: Average <70% utilization; alert at >80% for 5+ minutes
- **Cloud VM Disk**: Average <70% utilization; alert at >90% immediately
- **Vault Size**: Target <10GB total; alert at >8GB to prompt archival

---

## Observability Requirements

### Monitoring

1. **Cloud VM Uptime**: Continuous monitoring via health endpoint; uptime percentage calculated over 30-day rolling window
2. **Resource Utilization**: CPU, memory, disk metrics collected every 60 seconds; visualized in dashboard (Local only)
3. **Vault Sync Status**: Last sync time, sync duration, pending changes, conflict count displayed in Local dashboard
4. **Security Boundary Breach Attempts**: All breach attempts logged with timestamp, file path, and action taken; alerts sent to Local
5. **Draft Queue Size**: Number of pending drafts in `/Drafts/` folder tracked and displayed; alert if queue >50 items
6. **Approval Queue Age**: Age of oldest pending approval tracked; alert if any approval >24 hours old
7. **Health Endpoint Availability**: External monitoring of health endpoint availability; alert if endpoint unreachable for >5 minutes

### Alerting

| Alert | Threshold | Channel | Owner |
|-------|-----------|---------|-------|
| Cloud VM Down | Health endpoint unreachable >5 min | Email/SMS | User |
| High CPU/Memory | >80% for 5+ minutes | Dashboard + Log | User |
| High Disk Usage | >90% disk | Dashboard + Log + Email | User |
| Sync Failure | Sync fails 3+ consecutive times | Dashboard | User |
| Security Breach Attempt | Any breach detected | Dashboard + Email (immediate) | User |
| Draft Queue Backlog | >50 pending drafts | Dashboard | User |
| Approval Queue Stale | Any approval >24 hours old | Dashboard (daily summary) | User |
| Odoo Unavailable | Odoo API unreachable >1 hour | Dashboard + Log | User |

### Dashboards

1. **Local Dashboard.md**: Single-writer file (Local only) showing:
   - System health summary (Cloud status, sync status, resource usage)
   - Draft queue (count, oldest item, categories)
   - Approval queue (count, oldest item, priority items)
   - Recent activity log (last 50 actions)
   - Security alerts (last 10 breach attempts)
   - Weekly business metrics (revenue, invoices, tasks completed)

2. **Cloud Updates Folder**: `/Updates/<domain>/` files containing:
   - Detected events summary (emails, messages, metrics)
   - Draft creation log
   - Resource utilization reports
   - Sync status reports

3. **Signal Files**: `/Signals/<domain>/` for urgent notifications:
   - Security breach alerts
   - Critical event notifications
   - System health emergencies

### Logging

- **Log Format**: Structured JSON logs with timestamp, level, component, message, and context
- **Log Rotation**: Daily rotation with 90-day retention; compressed archives
- **Log Aggregation**: Logs from Cloud and Local merged in Local dashboard for unified view
- **Audit Trail**: Immutable log of all draft creations, approvals, executions, and security events

---

## Appendix: Platinum Demo (8-Step Workflow)

### Demo Scenario: Email Arrives While Local Offline

**Purpose**: Demonstrate end-to-end Platinum Tier value proposition

**Steps**:

1. **Local Goes Offline** (User action): User closes laptop or disconnects Local workstation from network at 6:00 PM
2. **Email Arrives** (External trigger): Client sends email to `client@example.com` with subject "Project Update Request" at 3:00 AM
3. **Cloud Detects Email** (Cloud action): Cloud Agent's Gmail watcher detects new email within 2 minutes (by 3:02 AM)
4. **Cloud Drafts Reply** (Cloud action): Cloud Agent analyzes email content and drafts a professional reply acknowledging the request and promising follow-up within 24 hours (by 3:05 AM)
5. **Cloud Syncs Draft** (Sync action): Vault sync runs and copies draft email from Cloud to Local vault within 60 seconds (by 3:06 AM)
6. **Local Comes Online** (User action): User opens laptop and connects to network at 8:00 AM; sync runs and downloads all Cloud drafts
7. **Local Reviews Draft** (User action): User opens Dashboard.md, sees 1 pending email draft in queue, reviews content, and clicks "Approve" at 8:15 AM
8. **Local Executes Send** (Local action): Local Agent sends the email via Gmail API, logs the execution in audit trail, and moves file to `/Completed/` at 8:15:30 AM

**Success Metrics**:

- Total time from email arrival to send: 5 hours 15 minutes 30 seconds (mostly offline time)
- Cloud detection latency: <2 minutes
- Draft creation time: <3 minutes
- Sync latency: <60 seconds
- Local approval-to-send time: <30 seconds
- Audit trail completeness: All 8 steps logged with timestamps

**Evidence**:

- Gmail sent folder shows email sent at 8:15:30 AM
- Audit log shows complete trail: Detect (3:02 AM) → Draft (3:05 AM) → Sync (3:06 AM) → Approve (8:15 AM) → Execute (8:15:30 AM)
- Dashboard.md shows draft queue history and completion status
- Cloud Updates folder shows detection and draft creation logs

---

**Quality Gates Checklist** (for spec author to verify before marking Draft → Review):

- [x] All 7 Platinum requirements (P1-P7) covered in user stories
- [x] 30+ functional requirements with unique IDs (FR-PT-001 to FR-PT-030)
- [x] 20+ success criteria with measurable metrics (SC-PT-001 to SC-PT-020)
- [x] 10+ key entities defined (12 entities total)
- [x] Security boundaries explicitly documented (Security & Compliance section)
- [x] Platinum Demo (8 steps) fully specified (Appendix)
- [x] Vault sync mechanism (Git/Syncthing) detailed (FR-PT-013 to FR-PT-018)
- [x] Claim-by-move rule specified (FR-PT-025 to FR-PT-027)
- [x] Cloud/Local responsibility split clear (Work-Zone Specialization section)
- [x] Phase 2 (A2A) marked as optional (Non-Goals and Key Entities)
- [x] All acceptance criteria testable (verified per user story)
- [x] No contradictions with Constitution v6.0.0 Section XIV (verified)

---

**Next Steps**:

1. **Review Spec**: Stakeholder review of this specification for completeness and accuracy
2. **Create Plan**: Run `/sp.plan` to generate architecture design for Cloud/Local split
3. **Create Tasks**: Run `/sp.tasks` to generate implementation tasks (60+ hours estimated)
4. **Implement**: Phase-by-phase implementation (P1-P7 requirements)
5. **Test**: Platinum Demo validation, chaos testing, load testing
6. **Document**: Deployment guide, runbook, security disclosure
