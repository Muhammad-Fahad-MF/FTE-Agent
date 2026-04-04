#!/bin/bash
# Configure Security Hardening for FTE-Agent Cloud VM
# Purpose: Implement UFW firewall, Fail2ban, and automatic security updates
# Usage: sudo bash configure-security.sh

set -e  # Exit on error

echo "=== FTE-Agent Cloud VM Security Hardening ==="
echo "Date: $(date)"
echo ""

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    print_error "Please run as root (sudo bash configure-security.sh)"
    exit 1
fi

# Step 1: Update system packages
echo ""
echo "=== Step 1: Updating System Packages ==="
apt update
apt upgrade -y
print_status "System packages updated"

# Step 2: Configure UFW Firewall
echo ""
echo "=== Step 2: Configuring UFW Firewall ==="

# Install UFW if not installed
if ! command -v ufw &> /dev/null; then
    apt install ufw -y
    print_status "UFW installed"
else
    print_status "UFW already installed"
fi

# Reset UFW (optional, for clean slate)
# ufw --force reset

# Set default policies
ufw default deny incoming
ufw default allow outgoing
print_status "Default policies set (deny incoming, allow outgoing)"

# Allow SSH (port 22)
# For production: restrict to specific IP with:
# ufw allow from <your-ip>/32 to any port 22 proto tcp
ufw allow 22/tcp
print_status "SSH (port 22) allowed"

# Allow HTTP (port 80) for Let's Encrypt
ufw allow 80/tcp
print_status "HTTP (port 80) allowed"

# Allow HTTPS (port 443) for Odoo
ufw allow 443/tcp
print_status "HTTPS (port 443) allowed"

# Allow health endpoint (port 8000)
# Note: Should bind to localhost only in production
ufw allow 8000/tcp
print_status "Health endpoint (port 8000) allowed"

# Enable UFW (non-interactive)
ufw --force enable
print_status "UFW firewall enabled"

# Display UFW status
echo ""
print_status "UFW Status:"
ufw status verbose

# Step 3: Install and Configure Fail2ban
echo ""
echo "=== Step 3: Installing Fail2ban ==="

if ! command -v fail2ban-client &> /dev/null; then
    apt install fail2ban -y
    print_status "Fail2ban installed"
else
    print_status "Fail2ban already installed"
fi

# Create Fail2ban jail configuration
cat > /etc/fail2ban/jail.local << 'EOF'
[DEFAULT]
# Ban duration: 1 hour
bantime = 3600
# Time window for counting failures: 5 minutes
findtime = 300
# Number of failures before ban
maxretry = 5
# Backend for log monitoring
backend = auto

# SSH jail configuration
[sshd]
enabled = true
port = ssh
filter = sshd
logpath = /var/log/auth.log
maxretry = 5
bantime = 3600

# Optional: Nginx jail (if web server is installed)
# [nginx-http-auth]
# enabled = true
# port = http,https
# filter = nginx-http-auth
# logpath = /var/log/nginx/error.log
# maxretry = 5
# bantime = 3600
EOF

print_status "Fail2ban jail configuration created"

# Start and enable Fail2ban service
systemctl start fail2ban
systemctl enable fail2ban
print_status "Fail2ban started and enabled"

# Verify Fail2ban status
echo ""
print_status "Fail2ban Status:"
systemctl status fail2ban --no-pager | head -20

# Step 4: Configure Automatic Security Updates
echo ""
echo "=== Step 4: Configuring Automatic Security Updates ==="

# Install unattended-upgrades if not installed
if ! dpkg -l | grep -q unattended-upgrades; then
    apt install unattended-upgrades -y
    print_status "unattended-upgrades installed"
else
    print_status "unattended-upgrades already installed"
fi

# Configure automatic updates
cat > /etc/apt/apt.conf.d/20auto-upgrades << 'EOF'
APT::Periodic::Update-Package-Lists "1";
APT::Periodic::Unattended-Upgrade "1";
APT::Periodic::AutocleanInterval "7";
APT::Periodic::Download-Upgradeable-Packages "1";
APT::Periodic::Install-Unattended "1";
EOF

print_status "Automatic updates configured"

# Test unattended-upgrades configuration
echo ""
print_status "Testing unattended-upgrades configuration..."
if unattended-upgrade --dry-run > /dev/null 2>&1; then
    print_status "Configuration test passed"
else
    print_warning "Configuration test had warnings (check logs)"
fi

# Enable and start unattended-upgrades service
systemctl enable unattended-upgrades
systemctl start unattended-upgrades
print_status "unattended-upgrades service started"

# Step 5: Security Summary
echo ""
echo "=== Security Hardening Complete ==="
echo ""
print_status "Security configuration summary:"
echo ""
echo "Firewall (UFW):"
echo "  - Default: DENY incoming, ALLOW outgoing"
echo "  - Allowed ports: 22 (SSH), 80 (HTTP), 443 (HTTPS), 8000 (Health)"
echo ""
echo "Intrusion Prevention (Fail2ban):"
echo "  - SSH protection: 5 failures → 1 hour ban"
echo "  - Log monitoring: /var/log/auth.log"
echo ""
echo "Automatic Updates:"
echo "  - Security updates: Automatic (within 24 hours)"
echo "  - Package list refresh: Daily"
echo "  - Auto-cleanup: Weekly"
echo ""

# Display final status
echo "Final Security Status:"
echo "----------------------"
echo "UFW Status:"
ufw status | grep -E "^(Status|To|Action)" | head -10
echo ""
echo "Fail2ban Status:"
systemctl is-active fail2ban
echo ""
echo "Unattended-Upgrades Status:"
systemctl is-active unattended-upgrades
echo ""

print_status "Security hardening complete!"
print_warning "Remember to restrict SSH (port 22) to your IP in production"
echo ""
echo "Next steps:"
echo "  1. Configure SSH key authentication (disable password auth)"
echo "  2. Install Docker and Python 3.13"
echo "  3. Deploy FTE-Agent Cloud Agent"
echo ""

exit 0
