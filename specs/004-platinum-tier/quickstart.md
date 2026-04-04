# Quickstart Guide: Platinum Tier - Cloud + Local Executive

**Feature**: Platinum Tier (v6.0.0)
**Branch**: `004-platinum-tier-cloud-executive`
**Date**: 2026-04-02
**Status**: Draft

---

## Overview

This quickstart guide walks you through setting up Platinum Tier's two-agent architecture: Cloud Agent (24/7 monitoring, draft-only) and Local Agent (execution authority, user workstation).

**Estimated Setup Time**: 4-6 hours
**Prerequisites**: Gold Tier v5.0.0 installed and operational

---

## Architecture Summary

```
┌─────────────────────────────────────────────────────────────────┐
│                    PLATINUM TIER ARCHITECTURE                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ☁️ CLOUD AGENT (Oracle/AWS/Google VM)                         │
│  - 24/7 monitoring (Gmail, WhatsApp, business metrics)         │
│  - Draft creation only (NO execution)                          │
│  - Health endpoint: http://<cloud-vm>:8000/health              │
│  - Odoo Community (draft invoices)                             │
│                                                                 │
│  🔄 VAULT SYNC (Git Remote - GitHub/GitLab)                    │
│  - Private repository (SSH key auth)                           │
│  - Sync interval: <60 seconds                                  │
│  - Excludes: .env, tokens/, sessions/, banking/, credentials/  │
│                                                                 │
│  💻 LOCAL AGENT (Windows 10/11 Workstation)                    │
│  - Execution authority (send emails, post invoices)            │
│  - OS Credential Manager (secrets storage)                     │
│  - Approval workflow (HITL)                                    │
│  - Dashboard.md (single-writer)                                │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Phase 1: Cloud VM Setup (1-2 hours)

### Step 1.1: Create Cloud VM (Oracle Cloud Free Tier)

**Oracle Cloud Console**: https://cloud.oracle.com/

1. **Sign in to Oracle Cloud Console**
   - Create account (if new)
   - Verify email and phone

2. **Create VM Instance**
   ```
   Compute → Instances → Create Instance
   
   Configuration:
   - Name: fte-agent-cloud
   - Compartment: <your-compartment>
   - Availability Domain: Any
   - Image: Ubuntu 22.04 LTS (minimal)
   - Shape: VM.Standard.A1.Flex (Always Free)
     - OCPUs: 2
     - Memory: 12 GB
   - Networking:
     - VCN: Default (create new)
     - Subnet: Public
     - Assign public IPv4: Yes
   - SSH keys: Upload your public key (~/.ssh/id_rsa.pub)
   - Boot volume: 50 GB (default)
   ```

3. **Configure Security List**
   ```
   Virtual Cloud Networks → <your-vcn> → Security Lists → Default Security List
   
   Ingress Rules:
   - Port 22 (SSH): Source = Your IP address (restrictive)
   - Port 80 (HTTP): Source = 0.0.0.0/0 (Let's Encrypt)
   - Port 443 (HTTPS): Source = 0.0.0.0/0 (Odoo)
   - Port 8000 (Health): Source = Your IP address (monitoring)
   ```

4. **Note VM Details**
   ```
   Public IP: <cloud-vm-ip>
   SSH Key: ~/.ssh/id_rsa
   Username: ubuntu
   ```

---

### Step 1.2: SSH into Cloud VM

```bash
# Test SSH connection
ssh -i ~/.ssh/id_rsa ubuntu@<cloud-vm-ip>

# Expected output:
# Welcome to Ubuntu 22.04 LTS (GNU/Linux ...)
```

---

### Step 1.3: Security Hardening

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install security tools
sudo apt install ufw fail2ban unattended-upgrades -y

# Configure UFW firewall
sudo ufw allow 22/tcp    # SSH (restrict to your IP in Oracle Console)
sudo ufw allow 80/tcp    # HTTP (Let's Encrypt)
sudo ufw allow 443/tcp   # HTTPS (Odoo)
sudo ufw allow 8000/tcp  # Health endpoint (restrict to your IP)
sudo ufw enable

# Enable automatic security updates
sudo systemctl enable unattended-upgrades
sudo systemctl start unattended-upgrades

# Configure Fail2ban (SSH protection)
sudo systemctl enable fail2ban
sudo systemctl start fail2ban

# Verify services
sudo systemctl status ufw
sudo systemctl status fail2ban
sudo systemctl status unattended-upgrades
```

---

### Step 1.4: Install Dependencies

```bash
# Install Docker (for Odoo)
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker ubuntu

# Install Docker Compose Plugin
sudo apt install docker-compose-plugin -y

# Install Python 3.13
sudo apt install python3.13 python3.13-venv python3-pip git -y

# Verify installations
docker --version
docker compose version
python3 --version
git --version
```

---

### Step 1.5: Create FTE-Agent Directory Structure

```bash
# Create directory structure
mkdir -p /home/ubuntu/fte-agent/{src,vault,logs,backups,odoo-docker}
cd /home/ubuntu/fte-agent

# Set permissions
sudo chown -R ubuntu:ubuntu /home/ubuntu/fte-agent
chmod 700 /home/ubuntu/fte-agent
```

---

## Phase 2: Git Vault Configuration (30 minutes)

### Step 2.1: Create Private Git Repository

**GitHub**: https://github.com/new

```
Repository name: fte-agent-vault
Visibility: Private
Initialize with README: No
Add .gitignore: None
Add license: None
```

**Note Repository URL**: `git@github.com:<user>/fte-agent-vault.git`

---

### Step 2.2: Initialize Local Vault (Windows Workstation)

```powershell
# Navigate to vault directory
cd H:\Programming\FTE-Agent\vault

# Initialize Git repository
git init

# Create .gitignore (CRITICAL - secrets exclusion)
notepad .gitignore
```

**.gitignore Content**:
```gitignore
# Secrets (NEVER sync)
.env
tokens/
sessions/
banking/
credentials/
*.key
*.pem
.os_credential_cache/

# Python artifacts
__pycache__/
*.pyc
*.pyo
.pytest_cache/

# Logs (rotate locally, don't sync)
Logs/*.log
Logs/*.json

# OS files
.DS_Store
Thumbs.db

# IDE files
.idea/
.vscode/
*.swp
*.swo
```

**Save and Commit**:
```powershell
# Add all files
git add .

# Commit
git commit -m "Initial vault structure for Platinum Tier"

# Add remote
git remote add origin git@github.com:<user>/fte-agent-vault.git

# Push to GitHub
git push -u origin main
```

---

### Step 2.3: Clone Vault on Cloud VM

```bash
# SSH into Cloud VM
ssh -i ~/.ssh/id_rsa ubuntu@<cloud-vm-ip>

# Clone vault repository
cd /home/ubuntu/fte-agent
git clone git@github.com:<user>/fte-agent-vault.git vault

# Configure Git
cd vault
git config pull.rebase false  # Use merge strategy
git config user.name "Cloud Agent"
git config user.email "cloud@fte-agent.local"

# Verify vault structure
ls -la
# Expected: Inbox/, Needs_Action/, Dashboard.md, .gitignore
```

---

## Phase 3: Cloud Agent Deployment (1 hour)

### Step 3.1: Install Platinum Tier Dependencies

```bash
# SSH into Cloud VM
ssh -i ~/.ssh/id_rsa ubuntu@<cloud-vm-ip>
cd /home/ubuntu/fte-agent

# Create Python virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install \
  watchdog>=3.0.0 \
  requests>=2.31.0 \
  google-auth>=2.23.0 \
  google-auth-oauthlib>=1.1.0 \
  google-api-python-client>=2.104.0 \
  playwright>=1.40.0 \
  python-dotenv>=1.0.0 \
  pydantic>=2.5.0 \
  psutil>=5.9.0 \
  fastapi>=0.104.0 \
  uvicorn>=0.24.0 \
  GitPython>=3.1.40 \
  fabric>=3.2.0 \
  paramiko>=3.3.0
```

---

### Step 3.2: Configure Cloud Environment

```bash
# Create .env file (Cloud - NO SECRETS)
cd /home/ubuntu/fte-agent
nano .env
```

**.env Content (Cloud)**:
```ini
# Cloud Agent Configuration (DRAFT-ONLY)
DEPLOYMENT_MODE=cloud
DEV_MODE=true

# Vault Configuration
VAULT_PATH=/home/ubuntu/fte-agent/vault
LOG_PATH=/home/ubuntu/fte-agent/logs

# Git Sync Configuration
GIT_REMOTE=git@github.com:<user>/fte-agent-vault.git
SYNC_INTERVAL=60

# Health Endpoint
HEALTH_HOST=127.0.0.1
HEALTH_PORT=8000

# Gmail API (READ-ONLY + DRAFT, NO SEND)
GMAIL_CLIENT_ID=<client-id>
GMAIL_CLIENT_SECRET=<client-secret>
# NOTE: GMAIL_SEND_SCOPE=false (draft-only)

# Odoo Configuration (DRAFT-ONLY)
ODOO_URL=http://localhost:8069
ODOO_DB=odoo_db
ODOO_USER=draft_user
ODOO_PASSWORD=<draft-only-password>
# NOTE: draft_user has NO post/send permissions

# Monitoring
MONITORING_INTERVAL=60
ALERT_THRESHOLD_CPU=80
ALERT_THRESHOLD_MEMORY=80
ALERT_THRESHOLD_DISK=90
```

**Set Permissions**:
```bash
chmod 600 .env
```

---

### Step 3.3: Create Systemd Service (Auto-Restart)

```bash
# Create systemd service file
sudo nano /etc/systemd/system/fte-cloud.service
```

**Service File Content**:
```ini
[Unit]
Description=FTE-Agent Cloud Service
After=network.target docker.service
Requires=docker.service

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/fte-agent
Environment="PATH=/home/ubuntu/fte-agent/venv/bin"
ExecStart=/home/ubuntu/fte-agent/venv/bin/python -m src.orchestrator --mode cloud
Restart=always
RestartSec=10
MemoryLimit=500M
StandardOutput=journal
StandardError=journal
SyslogIdentifier=fte-cloud

[Install]
WantedBy=multi-user.target
```

**Enable and Start Service**:
```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable service (start on boot)
sudo systemctl enable fte-cloud

# Start service
sudo systemctl start fte-cloud

# Check status
sudo systemctl status fte-cloud

# View logs
sudo journalctl -u fte-cloud -f
```

---

### Step 3.4: Deploy Odoo Community (Docker Compose)

```bash
# SSH into Cloud VM
ssh -i ~/.ssh/id_rsa ubuntu@<cloud-vm-ip>
cd /home/ubuntu/fte-agent/odoo-docker

# Create docker-compose.yml
nano docker-compose.yml
```

**docker-compose.yml Content**:
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

**Start Odoo Stack**:
```bash
# Generate secure passwords
openssl rand -base64 32  # Odoo DB password
openssl rand -base64 32  # PostgreSQL password

# Update docker-compose.yml with passwords

# Start Odoo
docker compose up -d

# Check logs
docker compose logs -f odoo

# Odoo will be available at: http://<cloud-vm>:8069
```

---

### Step 3.5: Install Let's Encrypt SSL (Odoo HTTPS)

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx -y

# Request certificate (replace with your domain)
sudo certbot certonly --standalone -d <your-domain.com>

# Certificates will be in: /etc/letsencrypt/live/<your-domain.com>/

# Configure Nginx SSL (see odoo-docker/nginx.conf)
# Restart Nginx
docker compose restart nginx

# Auto-renewal (cron job)
sudo crontab -e
# Add: 0 3 * * * certbot renew --quiet
```

---

## Phase 4: Local Agent Configuration (30 minutes)

### Step 4.1: Update Local Environment

```powershell
# Navigate to FTE-Agent directory
cd H:\Programming\FTE-Agent

# Activate virtual environment (if not already active)
.\venv\Scripts\Activate.ps1

# Install Platinum Tier dependencies
pip install -r requirements-platinum.txt
```

**requirements-platinum.txt**:
```txt
# Platinum Tier additions
fabric>=3.2.0
paramiko>=3.3.0
GitPython>=3.1.40
psutil>=5.9.0
fastapi>=0.104.0
uvicorn>=0.24.0
cryptography>=41.0.0
pycryptodome>=3.19.0
```

---

### Step 4.2: Configure Local Environment

```powershell
# Create .env file (Local - WITH SECRETS)
notepad .env
```

**.env Content (Local)**:
```ini
# Local Agent Configuration (FULL EXECUTION)
DEPLOYMENT_MODE=local
DEV_MODE=true

# Vault Configuration
VAULT_PATH=H:\Programming\FTE-Agent\vault
LOG_PATH=H:\Programming\FTE-Agent\logs

# Git Sync Configuration
GIT_REMOTE=git@github.com:<user>/fte-agent-vault.git
SYNC_INTERVAL=60

# Gmail API (FULL PERMISSIONS - SEND ENABLED)
GMAIL_CLIENT_ID=<client-id>
GMAIL_CLIENT_SECRET=<client-secret>
GMAIL_REDIRECT_URI=http://localhost:8080
# NOTE: Full send scope enabled

# WhatsApp Web (Playwright)
PLAYWRIGHT_BROWSER=chromium

# Odoo Configuration (FULL PERMISSIONS - POST ENABLED)
ODOO_URL=http://<cloud-vm>:8069
ODOO_DB=odoo_db
ODOO_USER=admin
ODOO_PASSWORD=<admin-password>

# Social Media APIs
FACEBOOK_PAGE_ACCESS_TOKEN=<token>
TWITTER_BEARER_TOKEN=<token>
LINKEDIN_ACCESS_TOKEN=<token>

# OS Credential Manager (Windows)
USE_OS_CREDENTIAL_MANAGER=true
```

**Store Secrets in Windows Credential Manager**:
```powershell
# Use keyring library to store secrets in Windows Credential Manager
python -c "import keyring; keyring.set_password('fte-agent', 'gmail_token', '<token>')"
python -c "import keyring; keyring.set_password('fte-agent', 'odoo_password', '<password>')"
```

---

### Step 4.3: Configure Local Git

```powershell
# Configure Git
cd H:\Programming\FTE-Agent\vault
git config pull.rebase false  # Use merge strategy
git config user.name "Local Agent"
git config user.email "local@fte-agent.local"

# Test sync
git pull origin main
git add .
git commit -m "Local configuration update"
git push origin main
```

---

## Phase 5: Health Endpoint Verification (15 minutes)

### Step 5.1: Test Cloud Health Endpoint

```bash
# SSH into Cloud VM
ssh -i ~/.ssh/id_rsa ubuntu@<cloud-vm-ip>

# Test health endpoint
curl http://127.0.0.1:8000/health

# Expected response:
# {
#   "status": "healthy",
#   "uptime_seconds": 120,
#   "resources": {
#     "cpu_percent": 15.2,
#     "memory_percent": 42.5,
#     "disk_percent": 35.0
#   },
#   "watchers": {
#     "gmail": "running",
#     "whatsapp": "running"
#   },
#   "last_sync": "2026-04-02T08:15:30Z"
# }
```

### Step 5.2: Verify Auto-Restart

```bash
# Kill Cloud Agent process
sudo systemctl stop fte-cloud

# Wait 10 seconds
sleep 10

# Check if auto-restarted
sudo systemctl status fte-cloud

# Expected: Active: active (running)
```

---

## Phase 6: Platinum Demo Validation (30 minutes)

### Step 6.1: Run 8-Step Demo Workflow

**Prerequisites**:
- Cloud VM: Healthy (curl health endpoint)
- Local Workstation: Online
- Git Sync: Configured and tested

**Demo Steps**:

1. **Local Goes Offline**
   ```powershell
   # Disconnect Local from network
   # (Disable Wi-Fi or unplug Ethernet)
   ```

2. **Email Arrives**
   ```
   Send test email to: user@company.com
   From: test@example.com
   Subject: Platinum Demo Test
   Body: This is a test email for Platinum Demo validation.
   ```

3. **Cloud Detects Email**
   ```bash
   # SSH into Cloud VM
   ssh -i ~/.ssh/id_rsa ubuntu@<cloud-vm-ip>
   
   # Check vault
   ls -la /home/ubuntu/fte-agent/vault/Inbox/Email/
   # Expected: EMAIL_<timestamp>_<id>.md created
   ```

4. **Cloud Drafts Reply**
   ```bash
   # Wait 2-5 minutes
   ls -la /home/ubuntu/fte-agent/vault/Drafts/Email/
   # Expected: DRAFT_EMAIL_<timestamp>_<id>.md created
   ```

5. **Sync to Local**
   ```powershell
   # Reconnect Local to network
   # Enable Wi-Fi or plug in Ethernet
   
   # Wait for sync (<60 seconds)
   git -C H:\Programming\FTE-Agent\vault pull origin main
   
   # Check vault
   ls H:\Programming\FTE-Agent\vault\Drafts\Email\
   # Expected: Draft email present
   ```

6. **Local Reviews Draft**
   ```powershell
   # Open draft in editor
   notepad H:\Programming\FTE-Agent\vault\Drafts\Email\DRAFT_EMAIL_*.md
   
   # Review content
   ```

7. **Local Approves Draft**
   ```powershell
   # Move to Approved folder
   move H:\Programming\FTE-Agent\vault\Drafts\Email\DRAFT_EMAIL_*.md H:\Programming\FTE-Agent\vault\Approved\Email\
   ```

8. **Local Executes (Sends Email)**
   ```powershell
   # Orchestrator detects approved file
   # Sends email via Gmail API
   # Moves to Completed folder
   ```

**Verification**:
```bash
# Check Cloud vault for completion
ssh -i ~/.ssh/id_rsa ubuntu@<cloud-vm-ip>
ls -la /home/ubuntu/fte-agent/vault/Completed/Email/
# Expected: Email marked as completed with audit trail
```

---

## Troubleshooting

### Issue: Cloud VM Unreachable

**Symptoms**: SSH fails, health endpoint timeout

**Resolution**:
```bash
# Check Oracle Cloud Console
# - VM status: Running
# - Public IP: Correct
# - Security List: Ports 22/80/443/8000 open

# Restart VM (if needed)
# Oracle Console → Instances → fte-agent-cloud → Restart
```

---

### Issue: Git Sync Fails

**Symptoms**: `git pull` fails, conflict errors

**Resolution**:
```powershell
# Local: Check Git status
cd H:\Programming\FTE-Agent\vault
git status

# Resolve conflicts (if any)
# - Dashboard.md: Local-wins (overwrite Cloud version)
# - Other files: Last-write-wins

# Force sync (if needed)
git fetch origin
git reset --hard origin/main  # WARNING: Overwrites local changes
```

---

### Issue: Secret File Synced to Cloud

**Symptoms**: `.env` found on Cloud, security alert

**Resolution**:
```bash
# IMMEDIATE: Rotate compromised credentials
# 1. Change Gmail API credentials
# 2. Change Odoo passwords
# 3. Change social media tokens

# Remove secret from Cloud vault
cd /home/ubuntu/fte-agent/vault
git rm --cached .env
git commit -m "Remove secret file from tracking"
git push origin main

# Verify .gitignore includes .env
cat .gitignore | grep ".env"
```

---

### Issue: Odoo Unavailable

**Symptoms**: Draft invoice creation fails

**Resolution**:
```bash
# SSH into Cloud VM
ssh -i ~/.ssh/id_rsa ubuntu@<cloud-vm-ip>

# Check Odoo status
docker compose ps

# Restart Odoo
docker compose restart odoo

# Check logs
docker compose logs odoo | tail -100
```

---

## Next Steps

1. ✅ Cloud VM deployed and healthy
2. ✅ Git vault configured and syncing
3. ✅ Cloud Agent running (draft-only)
4. ✅ Local Agent configured (full execution)
5. ✅ Health endpoint verified
6. ✅ Platinum Demo validated (8-step workflow)
7. → Monitor for 24 hours (uptime SLA validation)
8. → Configure alerting (email/SMS for Cloud VM down)
9. → Set up daily Odoo backups (encrypted)
10. → Schedule CEO Briefing (Monday 8 AM)

---

**Status**: Quickstart COMPLETE
**Date**: 2026-04-02
**Next**: Monitor and validate 24-hour uptime SLA

---

## Appendix: Command Reference

### Cloud VM Commands

```bash
# SSH into Cloud VM
ssh -i ~/.ssh/id_rsa ubuntu@<cloud-vm-ip>

# Check Cloud Agent status
sudo systemctl status fte-cloud

# View Cloud Agent logs
sudo journalctl -u fte-cloud -f

# Restart Cloud Agent
sudo systemctl restart fte-cloud

# Test health endpoint
curl http://127.0.0.1:8000/health

# Check Odoo status
docker compose ps

# View Odoo logs
docker compose logs -f odoo

# Check disk usage
df -h

# Check memory usage
free -h
```

### Local Commands

```powershell
# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Run orchestrator (Local mode)
python -m src.orchestrator --mode local

# Test vault sync
cd H:\Programming\FTE-Agent\vault
git pull origin main
git push origin main

# View Dashboard
notepad H:\Programming\FTE-Agent\vault\Dashboard.md

# Check audit logs
Get-Content H:\Programming\FTE-Agent\logs\audit_*.json -Tail 50
```
