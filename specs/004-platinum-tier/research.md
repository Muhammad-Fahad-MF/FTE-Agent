# Phase 0 Research: Platinum Tier - Cloud + Local Executive

**Feature**: Platinum Tier (v6.0.0)
**Branch**: `004-platinum-tier-cloud-executive`
**Date**: 2026-04-02
**Status**: Complete

---

## Technical Context Resolution

### Language/Version: ✅ RESOLVED

**Decision**: Python 3.13+ (same as Gold Tier)

**Rationale**: 
- Gold Tier already requires Python 3.13+ for type safety and modern async features
- Platinum Tier extends Gold Tier architecture (no version change needed)
- Python 3.13 provides improved async performance for concurrent Cloud/Local operations

**Alternatives Considered**:
- Python 3.11: Rejected (project already standardized on 3.13)
- Python 3.12: Rejected (marginal benefits over 3.13)

---

### Primary Dependencies: ✅ RESOLVED

**Decision**: Extend Gold Tier dependencies with Platinum-specific additions

**Core Dependencies** (from Gold Tier):
```
watchdog>=3.0.0          # File system monitoring
requests>=2.31.0         # HTTP API calls
google-auth>=2.23.0      # Gmail API authentication
google-auth-oauthlib>=1.1.0
google-auth-httplib2>=0.1.1
google-api-python-client>=2.104.0
playwright>=1.40.0       # WhatsApp Web automation
python-dotenv>=1.0.0     # Environment variable management
pydantic>=2.5.0          # Data validation
pytest>=7.4.0            # Testing framework
pytest-cov>=4.1.0        # Coverage reporting
pytest-asyncio>=0.21.0   # Async test support
ruff>=0.1.6              # Linting
black>=23.11.0           # Code formatting
mypy>=1.7.0              # Type checking
bandit>=1.7.0            # Security scanning
isort>=5.12.0            # Import sorting
```

**Platinum Tier Additions**:
```
# Cloud VM deployment
fabric>=3.2.0            # Remote deployment automation
paramiko>=3.3.0          # SSH connectivity (Cloud VM setup)

# Vault sync (Git-based)
GitPython>=3.1.40        # Git operations for vault sync

# Alternative: Syncthing support (optional)
# syncthing-python>=1.0.0  # Syncthing API (if Syncthing chosen over Git)

# Process management
psutil>=5.9.0            # System monitoring (CPU, memory, disk)

# Health endpoint
fastapi>=0.104.0         # Health endpoint API
uvicorn>=0.24.0          # ASGI server for health endpoint

# Odoo Cloud deployment
docker>=6.1.0            # Docker Compose for Odoo deployment
docker-compose>=1.29.0   # Docker Compose (if not bundled with Docker)

# Security & encryption
cryptography>=41.0.0     # Secret encryption (backup encryption)
pycryptodome>=3.19.0     # AES-256 encryption for backups

# Monitoring & alerting
prometheus-client>=0.19.0  # Metrics export (optional, advanced monitoring)
```

**Rationale**:
- Fabric/Paramiko: Standard for remote Linux VM deployment automation
- GitPython: Native Git operations for vault sync (built-in conflict resolution)
- FastAPI/Uvicorn: Lightweight health endpoint (<500ms response time requirement)
- Psutil: Cross-platform system monitoring (CPU, memory, disk metrics)
- Docker/Docker-Compose: Odoo Community deployment with HTTPS
- Cryptography: AES-256 backup encryption (security requirement)

**Alternatives Considered**:
- Ansible vs Fabric: Ansible rejected (overkill for single-VM deployment; Fabric simpler)
- Syncthing vs Git: Git chosen for Phase 1 (built-in version control, audit trail); Syncthing remains optional
- Flask vs FastAPI: FastAPI chosen (async support, automatic OpenAPI docs, better performance)

---

### Storage: ✅ RESOLVED

**Decision**: Dual storage architecture (Local + Cloud)

**Local Storage** (User Workstation):
```
H:\Programming\FTE-Agent\vault\
├── Inbox/                   # Incoming items (email, WhatsApp, files)
├── Needs_Action/            # Items requiring processing
├── In_Progress/             # Claimed items (Cloud or Local ownership)
│   ├── Cloud/               # Cloud-claimed tasks
│   └── Local/               # Local-claimed tasks
├── Drafts/                  # Cloud-prepared drafts
│   ├── Email/
│   ├── Social/
│   └── Invoices/
├── Pending_Approval/        # Drafts awaiting Local approval
├── Updates/                 # Cloud status updates for Local dashboard
├── Signals/                 # Urgent alerts (security breaches, critical events)
├── Completed/               # Executed actions with audit trail
├── Dashboard.md             # Single-writer (Local only) status dashboard
├── .git/                    # Git metadata (if Git sync chosen)
└── .env                     # Secrets (NEVER synced to Cloud)
```

**Cloud Storage** (Oracle/AWS/Google VM):
```
/home/ubuntu/fte-agent/vault/
├── Inbox/
├── Needs_Action/
├── In_Progress/
│   ├── Cloud/
│   └── Local/
├── Drafts/
├── Pending_Approval/
├── Updates/
├── Signals/
├── Completed/
├── .git/                    # Git metadata
└── .gitignore               # Excludes: .env, tokens/, sessions/, banking/, credentials/
```

**Remote Storage** (Git Remote - GitHub/GitLab Private Repo):
```
git@github.com:<user>/fte-agent-vault.git
├── Inbox/
├── Needs_Action/
├── In_Progress/
├── Drafts/
├── Pending_Approval/
├── Updates/
├── Signals/
├── Completed/
└── Dashboard.md
```

**Odoo Database** (Cloud PostgreSQL):
```
PostgreSQL 14+ (bundled with Odoo)
├── odoo_db
│   ├── account_move           # Invoices (draft/posted)
│   ├── account_move_line      # Invoice lines
│   ├── res_partner            # Customers/Vendors
│   ├── product_template       # Products/Services
│   └── ir_attachment          # File attachments
```

**Rationale**:
- Vault file structure aligns with Gold Tier (backward compatible)
- Git remote serves as sync hub with conflict resolution
- Odoo PostgreSQL stores financial data separately from vault
- Clear separation: secrets (.env) only on Local, never synced

**Alternatives Considered**:
- Syncthing P2P vs Git: Git chosen for audit trail and version control; Syncthing remains optional
- SQLite vs PostgreSQL for Odoo: PostgreSQL required for production Odoo deployment
- Cloud vault sync to Local: Rejected (security model requires Cloud→Local only for drafts)

---

### Testing: ✅ RESOLVED

**Decision**: Extend Gold Tier testing strategy with Platinum-specific tests

**Testing Framework** (from Gold Tier):
```
pytest>=7.4.0                # Core testing framework
pytest-cov>=4.1.0            # Coverage reporting (target: 50-60% overall)
pytest-asyncio>=0.21.0       # Async test support
pytest-mock>=3.12.0          # Mocking utilities
factory-boy>=3.3.0           # Test data factories
faker>=20.0.0                # Fake data generation
```

**Platinum Tier Test Categories**:

1. **Vault Sync Tests** (Critical - P0):
   - Sync completion within 60 seconds (100 operations)
   - Conflict resolution (last-write-wins, local-wins for Dashboard.md)
   - Secret file exclusion (.env, tokens, sessions)
   - Offline queue management (1000+ pending actions)
   - Network partition recovery

2. **Security Boundary Tests** (Critical - P0):
   - Zero secrets on Cloud after 30-day simulation
   - .gitignore enforcement validation
   - Pre-sync secret detection and blocking
   - OS Credential Manager integration (Local only)
   - Security breach attempt detection (100% rate)

3. **Claim-by-Move Tests** (High - P1):
   - Concurrent claim attempts (100+ scenarios)
   - Stale claim detection (>5 minutes)
   - Double-work prevention verification
   - Cross-agent communication (Updates/Signals)

4. **Cloud/Local Workflow Tests** (Critical - P0):
   - Platinum Demo (8-step end-to-end)
   - Draft-only enforcement (Cloud creates 0 sends in 100 tests)
   - Local execution authority (100% approval rate)
   - Dashboard.md single-writer rule

5. **Cloud Odoo Tests** (High - P1):
   - Draft invoice creation (Cloud)
   - Invoice posting (Local only)
   - HTTPS/SSL validation
   - Backup/restore procedures

6. **Health Endpoint Tests** (High - P1):
   - Response time <500ms (p95)
   - Resource metrics accuracy
   - Watcher status reporting
   - Uptime tracking

7. **Chaos Tests** (High - P1):
   - Cloud VM crash/restart (<10 seconds)
   - Network partition (4+ hours)
   - Odoo API failure (fallback to drafts)
   - Disk exhaustion (>90% usage)

**Coverage Targets** (risk-based):
- Vault Sync: 90%+ (critical business logic)
- Security Boundaries: 90%+ (non-negotiable)
- Claim-by-Move: 80%+ (race condition handling)
- Cloud/Local Workflows: 80%+ (integration tests)
- Health Endpoint: 70%+ (external API)
- Overall Target: 50-60% (as per Constitution v6.0.0)

**Alternatives Considered**:
- 100% coverage: Rejected (Constitution v6.0.0 specifies risk-based 50-60%)
- Integration tests only: Rejected (unit tests needed for complex logic)
- Chaos tests optional: Rejected (P0 requires failure scenario validation)

---

### Target Platform: ✅ RESOLVED

**Decision**: Dual-platform deployment (Cloud VM + Local Workstation)

**Cloud VM Platform**:
```
Provider: Oracle Cloud Free Tier (primary), AWS EC2 t3.medium (fallback)
OS: Ubuntu 22.04 LTS
VM Specs: 2 OCPU, 12GB RAM (Oracle Free), 2 vCPU/4GB RAM (AWS)
Storage: 50GB SSD minimum
Network: Public IP, ports 22/80/443 open (22 restricted to user IP)
Process Manager: systemd (built-in) or PM2
Deployment: Docker Compose for Odoo, Python venv for Agent
```

**Local Workstation Platform**:
```
OS: Windows 10/11 (required for OS Credential Manager)
Python: 3.13+ (same as Gold Tier)
Git: Git for Windows (bundled with Git sync)
Browser: Chrome/Edge (for WhatsApp Web automation)
Credential Storage: Windows Credential Manager (native)
```

**Git Remote Platform**:
```
Provider: GitHub (private repo) or GitLab (private repo)
Access: SSH key authentication only
Branch: main (single branch for vault sync)
```

**Rationale**:
- Oracle Free Tier: Best free VM specs (2 OCPU, 12GB RAM)
- Ubuntu 22.04 LTS: Long-term support, extensive documentation
- Windows 10/11: Required for native OS Credential Manager integration
- GitHub/GitLab: Built-in access control, audit trail, free private repos

**Alternatives Considered**:
- Google Cloud vs Oracle: Oracle Free Tier more generous (always-free vs 12-month trial)
- macOS Local: Rejected (Windows Credential Manager simpler for single-user)
- Linux Local: Possible but requires 1Password CLI (added complexity)
- Multi-cloud: Rejected (single-cloud sufficient for v6.0.0)

---

### Project Type: ✅ RESOLVED

**Decision**: Single project with dual deployment configurations

**Structure**:
```
H:\Programming\FTE-Agent\
├── src/
│   ├── core/                    # Core orchestrator (shared)
│   ├── watchers/                # Gmail, WhatsApp, FileSystem watchers
│   ├── skills/                  # Python skills (send_email, create_invoice, etc.)
│   ├── approval/                # HITL approval workflow
│   ├── sync/                    # Vault sync (Git/Syncthing) [NEW - Platinum]
│   ├── security/                # Security boundary enforcement [NEW - Platinum]
│   ├── health/                  # Health endpoint [NEW - Platinum]
│   ├── monitoring/              # Resource monitoring [NEW - Platinum]
│   └── models/                  # Data models (Pydantic)
├── scripts/
│   ├── deploy/                  # Cloud VM deployment scripts [NEW - Platinum]
│   ├── sync/                    # Vault sync scripts [NEW - Platinum]
│   ├── backup/                  # Backup/restore scripts [NEW - Platinum]
│   └── ralph-loop.bat           # Ralph Wiggum loop (Gold Tier)
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── contract/
│   ├── chaos/                   # Chaos tests [NEW - Platinum]
│   └── platinum/                # Platinum-specific tests [NEW - Platinum]
├── vault/                       # Local vault (gitignored, backed up separately)
├── specs/
│   └── 004-platinum-tier/       # Platinum Tier spec/plan/tasks
└── docs/
    ├── runbooks/                # Operational runbooks [NEW - Platinum]
    └── architecture/            # Architecture diagrams
```

**Deployment Configurations**:
1. **Cloud Mode**: `DEPLOYMENT_MODE=cloud` (draft-only, no execution)
2. **Local Mode**: `DEPLOYMENT_MODE=local` (full execution authority)

**Rationale**:
- Single codebase: Easier maintenance, testing, deployment
- Deployment mode flag: Same code runs on Cloud and Local with different permissions
- Clear separation: sync/, security/, health/ modules Platinum-specific

**Alternatives Considered**:
- Separate Cloud/Local repos: Rejected (code duplication, sync issues)
- Microservices: Rejected (overkill for single-user system)
- Monorepo with subpackages: Considered but rejected (added complexity)

---

### Performance Goals: ✅ RESOLVED

**Decision**: Measurable performance budgets from spec requirements

| Metric | Target | Measurement Method |
|--------|--------|-------------------|
| Health endpoint response | <500ms (p95) | 1000 health checks over 24h |
| Vault sync completion | <60 seconds | 100 sync operations |
| Claim-by-move detection | <5 seconds | 100 concurrent claim attempts |
| Local merge of Cloud updates | <5 minutes (±30s) | 100 sync measurements |
| Draft creation | <10 seconds per action | 50 draft creations |
| Alert propagation (Cloud→Local) | <30 seconds | 20 alert scenarios |
| Auto-restart after crash | <10 seconds | 50 crash-restart cycles |
| Resource monitoring interval | 60 seconds | Continuous logging |
| Odoo JSON-RPC call | <5 seconds | 50 invoice creations |
| CEO Briefing generation | <60 seconds | 10 briefing generations |

**Rationale**:
- All targets derived from spec success criteria (SC-PT-001 to SC-PT-020)
- Measurable via automated tests and monitoring
- Aligns with Gold Tier performance budgets (Constitution v6.0.0 Section XII)

**Alternatives Considered**:
- Real-time sync (<5 seconds): Rejected (60 seconds sufficient for use case)
- Sub-100ms health endpoint: Rejected (500ms acceptable for monitoring)
- Instant alert propagation: Rejected (30 seconds balances performance/cost)

---

### Constraints: ✅ RESOLVED

**Decision**: Explicit constraints from spec and Constitution

**Hard Constraints** (non-negotiable):
1. Zero secrets synced to Cloud (security boundary)
2. Cloud draft-only operations (no execution)
3. Local single-writer for Dashboard.md
4. Sync exclusion: `.env`, `tokens/`, `sessions/`, `banking/`, `credentials/`, `*.key`, `*.pem`
5. Cloud VM uptime: 99% over 30-day period
6. Auto-restart: <10 seconds after crash
7. Health endpoint: <500ms response time (p95)
8. Vault sync: <60 seconds per cycle
9. Claim-by-move: Prevent 100% of double-work
10. Security breach detection: 100% detection rate

**Soft Constraints** (targets, not hard failures):
1. Cloud VM cost: $0-$65/month (Oracle Free Tier preferred)
2. Vault size: <10GB (performance guideline)
3. Approval queue age: <24 hours (user behavior target)
4. Draft queue size: <50 items (alert threshold)
5. Test coverage: 50-60% overall (risk-based approach)

**Rationale**:
- Hard constraints are security/reliability critical (P0 requirements)
- Soft constraints allow flexibility for trade-offs
- All constraints measurable and testable

---

### Scale/Scope: ✅ RESOLVED

**Decision**: Single-user business scale (as per spec)

**Scale Parameters**:
| Parameter | Value | Notes |
|-----------|-------|-------|
| Users | 1 (single-user system) | Multi-user explicitly out of scope |
| Daily emails | 100-500 | Gmail Watcher 2-min interval |
| Daily WhatsApp messages | 50-200 | WhatsApp Watcher 30-sec interval |
| Daily invoices | 10-50 | Odoo draft invoices |
| Vault files | 1,000-10,000 | Git sync optimized |
| Daily sync operations | 100-1,000 | <60 second target |
| Concurrent claims | 1-10 | Cloud + Local agents |
| Draft queue size | <50 (alert at 50) | Auto-cleanup at 30 days |
| Audit log retention | 90 days | JSON logs in /vault/Logs/ |
| Completed tasks archive | 1 year | Monthly archival |

**Rationale**:
- Single-user focus simplifies architecture (no multi-tenant complexity)
- Scale parameters align with Gold Tier operational data
- Vault size <10GB ensures efficient Git sync performance

**Alternatives Considered**:
- Multi-user support: Rejected (explicitly out of scope for v6.0.0)
- Enterprise scale (10k+ users): Rejected (single-user only)
- Real-time collaboration: Rejected (explicitly out of scope)

---

## Technology Best Practices

### Cloud VM Deployment (Oracle Cloud Free Tier)

**Best Practices**:
1. **VM Configuration**:
   - Use ARM-based Ampere A1 instances (2 OCPU, 12GB RAM free)
   - Ubuntu 22.04 LTS (long-term support)
   - 50GB boot volume (expandable to 200GB free)
   - Public IP with security list (ports 22/80/443)

2. **Security Hardening**:
   - SSH key-only authentication (disable password auth)
   - UFW firewall (allow 22 from user IP only, 80/443 public)
   - Automatic security updates (unattended-upgrades)
   - Fail2ban for SSH brute-force protection
   - Regular OS patching (monthly)

3. **Monitoring Setup**:
   - Install Oracle Cloud Monitoring Agent (built-in)
   - Configure custom health endpoint (FastAPI on port 8000)
   - Set up alerts (email/SMS) for VM downtime
   - Log rotation (7 days INFO, 30 days ERROR)

4. **Process Management**:
   - Use systemd for agent process management (built-in Ubuntu)
   - Configure auto-restart on failure (Restart=always)
   - Set resource limits (MemoryLimit=500M per watcher)
   - Enable logging to journalctl

**Setup Commands** (Oracle Cloud):
```bash
# Create VM (Oracle Cloud Console)
# Compute → Instances → Create Instance
# - Image: Ubuntu 22.04 LTS
# - Shape: VM.Standard.A1.Flex (2 OCPU, 12GB RAM)
# - SSH keys: Upload user's public key

# SSH into VM
ssh -i ~/.ssh/id_rsa ubuntu@<cloud-vm-ip>

# Security hardening
sudo apt update && sudo apt upgrade -y
sudo ufw allow 22/tcp    # SSH (restrict to user IP in Oracle Console)
sudo ufw allow 80/tcp    # HTTP (Let's Encrypt)
sudo ufw allow 443/tcp   # HTTPS (Odoo)
sudo ufw enable
sudo systemctl enable unattended-upgrades
sudo apt install fail2ban -y

# Install Docker (for Odoo)
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker ubuntu

# Install Python 3.13
sudo apt install python3.13 python3.13-venv python3-pip -y
```

**References**:
- Oracle Cloud Free Tier: https://www.oracle.com/cloud/free/
- Oracle Always Free Resources: https://docs.oracle.com/en-us/iaas/Content/FreeTier/freetier_topic-Always_Free_Resources.htm
- Ubuntu Security Hardening: https://ubuntu.com/security/certifications

---

### Git Vault Synchronization

**Best Practices**:
1. **Repository Setup**:
   - Private GitHub/GitLab repo (free for individuals)
   - SSH key authentication (no passwords)
   - Single branch (main) for simplicity
   - LFS not required (Markdown files only)

2. **Sync Strategy**:
   - Cloud: Pull every 60 seconds, push after draft creation
   - Local: Pull every 60 seconds, push after approval/execution
   - Conflict resolution: Last-write-wins (except Dashboard.md: local-wins)
   - Stale claim detection: >5 minutes old → reclaimable

3. **Git Configuration**:
   ```bash
   # .gitignore (Cloud and Local)
   .env
   tokens/
   sessions/
   banking/
   credentials/
   *.key
   *.pem
   .os_credential_cache/
   __pycache__/
   *.pyc
   .pytest_cache/
   vault/Logs/*.log   # Rotate locally, don't sync
   ```

4. **Conflict Resolution**:
   - Automated merge for Markdown files (last-write-wins)
   - Dashboard.md: Local-wins (single-writer rule enforced)
   - Manual intervention: Git conflict markers for complex conflicts
   - Audit trail: Git log tracks all changes

5. **Offline Queue Management**:
   - Git handles offline queuing automatically (local commits)
   - On reconnect: git push/pull resolves queue
   - Support 1000+ pending actions (Git handles large queues efficiently)
   - Stale detection: Timestamps in claim files (>5 minutes = stale)

**Setup Commands**:
```bash
# Create private repo (GitHub)
# https://github.com/new → Private → fte-agent-vault

# Initialize vault repo (Local)
cd H:\Programming\FTE-Agent\vault
git init
git remote add origin git@github.com:<user>/fte-agent-vault.git
git add .
git commit -m "Initial vault structure"
git push -u origin main

# Configure Cloud VM
ssh ubuntu@<cloud-vm-ip>
cd /home/ubuntu/fte-agent
git clone git@github.com:<user>/fte-agent-vault.git vault
cd vault
git config pull.rebase false  # Use merge strategy
```

**References**:
- GitHub Private Repos: https://docs.github.com/en/repositories/creating-and-managing-repositories/about-repository-visibility
- Git Conflict Resolution: https://git-scm.com/book/en/v2/Git-Branching-Basic-Branching-and-Merging
- GitPython Documentation: https://gitpython.readthedocs.io/

---

### FastAPI Health Endpoint

**Best Practices**:
1. **Endpoint Design**:
   ```python
   @app.get("/health")
   async def health_check():
       return {
           "status": "healthy|degraded|unhealthy",
           "uptime_seconds": 86400,
           "resources": {
               "cpu_percent": 45,
               "memory_percent": 62,
               "disk_percent": 71
           },
           "watchers": {
               "gmail": "running",
               "whatsapp": "running"
           },
           "last_sync": "2026-04-02T08:15:30Z"
       }
   ```

2. **Performance Optimization**:
   - Async endpoint (non-blocking)
   - Cache resource metrics (update every 10 seconds)
   - Minimal computation (return cached values)
   - Target: <500ms p95 response time

3. **Security**:
   - Bind to localhost only (127.0.0.1:8000)
   - Nginx reverse proxy for HTTPS (if external access needed)
   - No authentication required (internal monitoring only)
   - Rate limiting (60 requests/minute)

4. **Monitoring Integration**:
   - Prometheus metrics endpoint (/metrics)
   - Structured logging (JSON format)
   - Health status in logs (healthy/degraded/unhealthy)
   - Alerting on unhealthy status

**Implementation**:
```python
# src/health/endpoint.py
from fastapi import FastAPI
import psutil
import time

app = FastAPI()

start_time = time.time()
last_metrics_update = 0
cached_metrics = {}

def update_metrics():
    global cached_metrics, last_metrics_update
    cached_metrics = {
        "cpu_percent": psutil.cpu_percent(),
        "memory_percent": psutil.virtual_memory().percent,
        "disk_percent": psutil.disk_usage("/").percent
    }
    last_metrics_update = time.time()

@app.get("/health")
async def health_check():
    # Update metrics if older than 10 seconds
    if time.time() - last_metrics_update > 10:
        update_metrics()
    
    uptime = time.time() - start_time
    
    # Determine status
    status = "healthy"
    if cached_metrics.get("cpu_percent", 0) > 80 or cached_metrics.get("memory_percent", 0) > 80:
        status = "degraded"
    if cached_metrics.get("disk_percent", 0) > 90:
        status = "unhealthy"
    
    return {
        "status": status,
        "uptime_seconds": int(uptime),
        "resources": cached_metrics,
        "watchers": {
            "gmail": "running",  # Query actual watcher status
            "whatsapp": "running"
        },
        "last_sync": "2026-04-02T08:15:30Z"  # Query actual sync time
    }
```

**References**:
- FastAPI Documentation: https://fastapi.tiangolo.com/
- Psutil Documentation: https://psutil.readthedocs.io/
- Prometheus Metrics: https://prometheus.io/docs/practices/instrumentation/

---

### Docker Compose for Odoo

**Best Practices**:
1. **Odoo Deployment**:
   - Odoo Community v19+ (latest stable)
   - PostgreSQL 14+ (bundled with Odoo)
   - Docker Compose for orchestration
   - Let's Encrypt for HTTPS

2. **Docker Compose Configuration**:
   ```yaml
   version: '3.8'
   services:
     odoo:
       image: odoo:19.0
       container_name: odoo
       depends_on:
         - postgres
       ports:
         - "8069:8069"
       environment:
         - ODOO_DB_NAME=odoo_db
         - ODOO_DB_USER=odoo
         - ODOO_DB_PASSWORD=<secure-password>
       volumes:
         - odoo-data:/var/lib/odoo
         - ./odoo-custom-addons:/mnt/extra-addons
       restart: unless-stopped
       networks:
         - odoo-network

     postgres:
       image: postgres:14
       container_name: postgres
       environment:
         - POSTGRES_DB=odoo_db
         - POSTGRES_USER=odoo
         - POSTGRES_PASSWORD=<secure-password>
       volumes:
         - postgres-data:/var/lib/postgresql/data
       restart: unless-stopped
       networks:
         - odoo-network

     nginx:
       image: nginx:alpine
       container_name: nginx
       depends_on:
         - odoo
       ports:
         - "80:80"
         - "443:443"
       volumes:
         - ./nginx.conf:/etc/nginx/nginx.conf
         - ./ssl:/etc/nginx/ssl
       restart: unless-stopped
       networks:
         - odoo-network

   volumes:
     odoo-data:
     postgres-data:

   networks:
     odoo-network:
       driver: bridge
   ```

3. **Let's Encrypt SSL Setup**:
   - Use Certbot for certificate provisioning
   - Auto-renewal (cron job)
   - HTTPS redirect in Nginx

4. **Backup Strategy**:
   - Daily PostgreSQL dump (cron job)
   - Encrypt backups with AES-256
   - Store backups on Local vault (via sync)
   - Test restore procedures monthly

**Setup Commands**:
```bash
# Install Docker Compose (if not bundled)
sudo apt install docker-compose-plugin -y

# Create Odoo directory structure
mkdir -p odoo-docker/{odoo-custom-addons,ssl}
cd odoo-docker

# Create docker-compose.yml (paste configuration above)
nano docker-compose.yml

# Generate secure passwords
openssl rand -base64 32  # For Odoo DB password
openssl rand -base64 32  # For PostgreSQL password

# Start Odoo stack
docker compose up -d

# Check logs
docker compose logs -f odoo

# Install Let's Encrypt
sudo apt install certbot python3-certbot-nginx -y
sudo certbot --nginx -d <your-domain.com>
```

**References**:
- Odoo Docker Documentation: https://hub.docker.com/_/odoo
- Docker Compose Specification: https://docs.docker.com/compose/compose-file/
- Let's Encrypt Certbot: https://certbot.eff.org/

---

### Security Boundary Enforcement

**Best Practices**:
1. **Layered Defense**:
   - Layer 1: .gitignore (prevent accidental commits)
   - Layer 2: Pre-sync validation (block secret patterns)
   - Layer 3: Audit logging (detect breach attempts)
   - Layer 4: OS Credential Manager (Local-only secrets)

2. **Secret Pattern Detection**:
   ```python
   # src/security/boundary.py
   SECRET_PATTERNS = [
       r"\.env$",
       r"tokens/",
       r"sessions/",
       r"banking/",
       r"credentials/",
       r".*\.key$",
       r".*\.pem$",
       r"api[_-]?key",
       r"password\s*=",
       r"secret\s*=",
       r"token\s*=",
   ]

   def is_secret_file(file_path: Path) -> bool:
       """Check if file matches secret patterns."""
       for pattern in SECRET_PATTERNS:
           if re.search(pattern, str(file_path), re.IGNORECASE):
               return True
       return False
   ```

3. **Pre-Sync Validation**:
   ```python
   def validate_sync_file(file_path: Path) -> bool:
       """Validate file before syncing to Cloud."""
       if is_secret_file(file_path):
           logger.error(f"SECURITY BREACH ATTEMPT: {file_path}")
           quarantine_file(file_path)
           alert_user("Security boundary breach attempt detected")
           return False
       return True
   ```

4. **OS Credential Manager Integration**:
   - Windows: `keyring` library (Windows Credential Manager)
   - macOS: `keyring` library (Keychain)
   - Cross-platform: 1Password CLI (optional)
   - Secrets never stored in vault files

5. **Audit Logging**:
   - Log all secret access attempts
   - Include: timestamp, file path, agent (Cloud/Local), action
   - Alert Local immediately on Cloud breach attempt
   - Retain logs for 90 days

**References**:
- Keyring Library: https://pypi.org/project/keyring/
- 1Password CLI: https://developer.1password.com/docs/cli/
- Security Best Practices: https://cheatsheetseries.owasp.org/

---

## Research Summary

### All NEEDS CLARIFICATION Items Resolved

| Item | Decision | Rationale |
|------|----------|-----------|
| Language/Version | Python 3.13+ | Aligns with Gold Tier |
| Dependencies | Extended Gold Tier + Platinum-specific | Fabric, GitPython, FastAPI, Docker, Cryptography |
| Storage | Dual (Local + Cloud vault) | Git remote as sync hub |
| Testing | Risk-based 50-60% coverage | Critical paths 90%+ |
| Target Platform | Oracle Cloud + Windows 10/11 | Best free tier, native credential manager |
| Project Type | Single project, dual deployment | Mode flag (cloud/local) |
| Performance Goals | From spec (sync <60s, health <500ms) | Measurable targets |
| Constraints | Hard (security) + Soft (targets) | Non-negotiable security boundaries |
| Scale/Scope | Single-user (100-500 emails/day) | Aligns with spec |

### Technology Choices Validated

- ✅ Oracle Cloud Free Tier: Best free VM (2 OCPU, 12GB RAM)
- ✅ Git sync: Built-in version control, audit trail
- ✅ FastAPI health endpoint: <500ms response time achievable
- ✅ Docker Compose Odoo: Reproducible, easy backups
- ✅ Layered security: Defense in depth (.gitignore + validation + audit)
- ✅ Claim-by-move: Atomic file operations prevent race conditions
- ✅ OS Credential Manager: Native Windows integration

### Alternatives Documented

- Syncthing vs Git: Git chosen for Phase 1 (Syncthing optional)
- AWS vs Oracle: Oracle Free Tier preferred (always-free)
- Ansible vs Fabric: Fabric simpler for single-VM deployment
- Flask vs FastAPI: FastAPI async support, better performance
- Multi-user vs Single-user: Single-user only (v6.0.0 scope)

### Next Steps

1. ✅ Research complete - all unknowns resolved
2. → Phase 1: Generate data-model.md, contracts/, quickstart.md
3. → Update agent context with new technologies
4. → Re-evaluate Constitution Check post-design

---

**Status**: Phase 0 COMPLETE
**Date**: 2026-04-02
**Next**: Phase 1 Design & Contracts
