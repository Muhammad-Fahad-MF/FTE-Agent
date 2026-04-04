# Cloud VM Setup Runbook

**Purpose**: Step-by-step guide for provisioning and configuring Oracle Cloud Free Tier VM for FTE-Agent Cloud deployment.

**Prerequisites**:
- Oracle Cloud account (Free Tier)
- SSH key pair (`~/.ssh/id_rsa.pub`)
- Credit card for billing verification (required by Oracle, no charges for Free Tier)

---

## Step 1: Create Oracle Cloud VM Instance

### 1.1 Access Oracle Cloud Console

1. Navigate to: https://cloud.oracle.com
2. Sign in with your Oracle Cloud account
3. Select your home region (closest to your location for lower latency)

### 1.2 Create Compute Instance

1. In the Oracle Cloud Console, navigate to: **Compute → Instances**
2. Click **Create Instance**
3. Configure the instance:

**Image and Shape**:
- **Image**: Ubuntu Server 22.04 LTS (Canonical Ubuntu)
- **Shape**: `VM.Standard.A1.Flex` (ARM-based Ampere)
- **OCPUs**: 2
- **Memory**: 12 GB

**Networking**:
- **Network**: Select default VCN (or create new)
- **Subnet**: Public subnet
- **Assign public IPv4 address**: ✓ Enabled
- **Choose IPv4 address type**: Ephemeral (free) or Reserved (optional)

**Storage**:
- **Boot Volume Size**: 200 GB (maximum free tier)
- **Performance**: Balanced

**SSH Keys**:
- **Generate a key pair for me**: Download private key
- **OR Upload my public key**: Paste contents of `~/.ssh/id_rsa.pub`

**Boot Volume** (Advanced):
- Keep default settings

### 1.3 Launch and Verify

1. Review configuration
2. Click **Create**
3. Wait for instance status: **Running** (2-5 minutes)
4. Note the **Public IP Address** (displayed in instance details)

### 1.4 Test SSH Connection

```bash
# Test SSH connection (replace with your IP)
ssh -i ~/.ssh/id_rsa ubuntu@<public-ip>

# Expected output: Welcome to Ubuntu 22.04.x LTS
```

**Troubleshooting**:
- **Connection refused**: Wait 1-2 minutes, VM may still be booting
- **Permission denied**: Verify SSH key permissions (`chmod 600 ~/.ssh/id_rsa`)
- **Timeout**: Check Oracle Cloud security list (port 22 must be open)

---

## Step 2: Configure Security Hardening

### 2.1 Update System Packages

```bash
# SSH into VM
ssh -i ~/.ssh/id_rsa ubuntu@<public-ip>

# Update package list
sudo apt update

# Upgrade installed packages
sudo apt upgrade -y
```

### 2.2 Configure UFW Firewall

```bash
# Install UFW (if not installed)
sudo apt install ufw -y

# Set default policies
sudo ufw default deny incoming
sudo ufw default allow outgoing

# Allow SSH (restrict to your IP for production)
sudo ufw allow from <your-ip>/32 to any port 22 proto tcp
# For initial setup (allow from anywhere, restrict later)
sudo ufw allow 22/tcp

# Allow HTTP (for Let's Encrypt)
sudo ufw allow 80/tcp

# Allow HTTPS (for Odoo)
sudo ufw allow 443/tcp

# Allow health endpoint (internal only, bind to localhost)
sudo ufw allow 8000/tcp

# Enable UFW
sudo ufw --force enable

# Verify status
sudo ufw status verbose
```

**Expected Output**:
```
Status: active
Logging: on (low)
Default: deny (incoming), allow (outgoing), deny (routed)
New connections: rate limit

To                         Action      From
--                         ------      ----
22/tcp                     ALLOW       Anywhere
80/tcp                     ALLOW       Anywhere
443/tcp                    ALLOW       Anywhere
8000/tcp                   ALLOW       Anywhere
22/tcp (v6)                ALLOW       Anywhere (v6)
80/tcp (v6)                ALLOW       Anywhere (v6)
443/tcp (v6)               ALLOW       Anywhere (v6)
8000/tcp (v6)              ALLOW       Anywhere (v6)
```

### 2.3 Install Fail2ban

```bash
# Install Fail2ban
sudo apt install fail2ban -y

# Create jail configuration
sudo cat > /etc/fail2ban/jail.local << 'EOF'
[DEFAULT]
bantime = 3600
findtime = 300
maxretry = 5
backend = auto

[sshd]
enabled = true
port = ssh
filter = sshd
logpath = /var/log/auth.log
maxretry = 5
bantime = 3600
EOF

# Start and enable Fail2ban
sudo systemctl start fail2ban
sudo systemctl enable fail2ban

# Verify status
sudo systemctl status fail2ban
```

### 2.4 Configure Automatic Security Updates

```bash
# Install unattended-upgrades
sudo apt install unattended-upgrades -y

# Configure automatic updates
sudo cat > /etc/apt/apt.conf.d/20auto-upgrades << 'EOF'
APT::Periodic::Update-Package-Lists "1";
APT::Periodic::Unattended-Upgrade "1";
APT::Periodic::AutocleanInterval "7";
EOF

# Test configuration
sudo unattended-upgrade --dry-run

# Enable service
sudo systemctl enable unattended-upgrades
sudo systemctl start unattended-upgrades
```

---

## Step 3: Install Dependencies

### 3.1 Install Docker

```bash
# Download Docker installation script
curl -fsSL https://get.docker.com -o get-docker.sh

# Run installation script
sudo sh get-docker.sh

# Add user to docker group (avoid sudo)
sudo usermod -aG docker ubuntu

# Verify Docker installation
docker --version
docker compose version
```

**Expected Output**:
```
Docker version 24.x.x, build ...
Docker Compose version v2.x.x
```

### 3.2 Install Python 3.13

```bash
# Install Python 3.13 and dependencies
sudo apt install software-properties-common -y
sudo add-apt-repository ppa:deadsnakes/ppa -y
sudo apt update
sudo apt install python3.13 python3.13-venv python3.13-dev python3-pip -y

# Verify Python installation
python3.13 --version
pip3 --version
```

### 3.3 Install Git

```bash
# Install Git
sudo apt install git -y

# Configure Git
git config --global user.name "Your Name"
git config --global user.email "your-email@example.com"

# Verify Git installation
git --version
```

---

## Step 4: Create Directory Structure

```bash
# Create FTE-Agent directories
sudo mkdir -p /home/ubuntu/fte-agent/{src,vault,logs,scripts,backups}

# Set ownership
sudo chown -R ubuntu:ubuntu /home/ubuntu/fte-agent

# Set permissions
chmod 755 /home/ubuntu/fte-agent
```

---

## Step 5: Verify Installation

### 5.1 System Health Check

```bash
# Check disk space
df -h

# Check memory
free -h

# Check CPU info
lscpu

# Check UFW status
sudo ufw status verbose

# Check Fail2ban status
sudo systemctl status fail2ban

# Check Docker status
sudo systemctl status docker

# Check Python version
python3.13 --version
```

### 5.2 Network Connectivity

```bash
# Test internet connectivity
ping -c 4 google.com

# Test port accessibility (from local machine)
nmap -p 22,80,443,8000 <public-ip>
```

---

## Acceptance Criteria

- [x] VM created with 2 OCPU, 12GB RAM, 200GB storage
- [x] SSH connection succeeds with key-based authentication
- [x] Public IP responds to ping within 100ms
- [x] UFW firewall allows only ports 22, 80, 443, 8000
- [x] Fail2ban bans IP after 5 failed SSH attempts
- [x] Automatic security updates enabled
- [x] Docker and Docker Compose installed
- [x] Python 3.13 installed
- [x] Directory structure created

---

## Troubleshooting

### VM Not Accessible

1. **Check instance status**: Oracle Cloud Console → Compute → Instances
2. **Verify security list**: Oracle Cloud Console → Networking → Virtual Cloud Networks → Security Lists
3. **Check SSH key**: Ensure public key matches private key used for connection

### Docker Installation Fails

```bash
# Remove existing Docker
sudo apt remove docker docker-engine docker.io containerd runc -y

# Reinstall Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
```

### Python 3.13 Not Available

```bash
# Alternative: Use Python 3.11 (default in Ubuntu 22.04)
sudo apt install python3 python3-venv python3-dev python3-pip -y
python3 --version  # Should be 3.10+
```

---

## Next Steps

After completing this runbook:

1. **P1-T003**: Implement Health Endpoint
2. **P1-T004**: Configure Auto-Restart Service
3. **P1-T005**: Implement Resource Monitoring
4. **P5-T001**: Deploy Odoo with Docker Compose

---

**Last Updated**: 2026-04-02
**Version**: 1.0
**Author**: FTE-Agent Development Team
