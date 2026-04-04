#!/bin/bash
# Configure systemd service for FTE-Agent Cloud Agent
# Purpose: Auto-restart on crash (<10 seconds), startup on boot
# Usage: sudo bash configure-systemd.sh

set -e  # Exit on error

echo "=== FTE-Agent Systemd Service Configuration ==="
echo "Date: $(date)"
echo ""

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

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
    print_error "Please run as root (sudo bash configure-systemd.sh)"
    exit 1
fi

# Check if service file exists
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVICE_FILE="$SCRIPT_DIR/fte-agent.service"

if [ ! -f "$SERVICE_FILE" ]; then
    print_error "Service file not found: $SERVICE_FILE"
    exit 1
fi

# Step 1: Copy service file to systemd directory
echo ""
echo "=== Step 1: Installing Service File ==="
cp "$SERVICE_FILE" /etc/systemd/system/fte-agent.service
print_status "Service file installed to /etc/systemd/system/fte-agent.service"

# Step 2: Reload systemd daemon
echo ""
echo "=== Step 2: Reloading Systemd Daemon ==="
systemctl daemon-reload
print_status "Systemd daemon reloaded"

# Step 3: Enable service (start on boot)
echo ""
echo "=== Step 3: Enabling Service ==="
systemctl enable fte-agent.service
print_status "Service enabled (will start on boot)"

# Step 4: Start service
echo ""
echo "=== Step 4: Starting Service ==="
systemctl start fte-agent.service
print_status "Service started"

# Step 5: Verify service status
echo ""
echo "=== Step 5: Verifying Service Status ==="
sleep 2  # Wait for service to initialize

if systemctl is-active --quiet fte-agent.service; then
    print_status "Service is running"
else
    print_error "Service failed to start"
    echo ""
    echo "Service logs:"
    journalctl -u fte-agent.service --no-pager -n 20
    exit 1
fi

# Display service status
echo ""
print_status "Service Status:"
systemctl status fte-agent.service --no-pager | head -20

# Step 6: Test auto-restart
echo ""
echo "=== Step 6: Testing Auto-Restart (Optional) ==="
print_warning "This will kill the service process to test auto-restart"
read -p "Run auto-restart test? (y/N): " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    print_status "Testing auto-restart..."
    
    # Get PID before kill
    PID_BEFORE=$(systemctl show fte-agent.service --property=MainPID --value)
    echo "Current PID: $PID_BEFORE"
    
    # Kill the process
    sudo kill $PID_BEFORE
    print_warning "Process killed, waiting for restart..."
    
    # Wait for restart
    sleep 10
    
    # Get PID after restart
    PID_AFTER=$(systemctl show fte-agent.service --property=MainPID --value)
    echo "New PID: $PID_AFTER"
    
    # Check if restarted
    if [ "$PID_BEFORE" != "$PID_AFTER" ] && [ "$PID_AFTER" != "0" ]; then
        print_status "Auto-restart successful (PID changed: $PID_BEFORE → $PID_AFTER)"
        
        # Calculate restart time (approximate)
        print_status "Restart time: <10 seconds (configured RestartSec=5)"
    else
        print_error "Auto-restart failed"
        exit 1
    fi
else
    print_warning "Auto-restart test skipped"
fi

# Summary
echo ""
echo "=== Systemd Configuration Complete ==="
echo ""
print_status "Configuration summary:"
echo ""
echo "Service: fte-agent"
echo "  - Location: /etc/systemd/system/fte-agent.service"
echo "  - Status: Active and running"
echo "  - Auto-restart: Enabled (RestartSec=5)"
echo "  - Start on boot: Enabled"
echo "  - Resource limits: Memory=500M, CPU=50%"
echo ""
echo "Useful commands:"
echo "  - Check status: systemctl status fte-agent"
echo "  - View logs: journalctl -u fte-agent -f"
echo "  - Restart: sudo systemctl restart fte-agent"
echo "  - Stop: sudo systemctl stop fte-agent"
echo "  - Disable: sudo systemctl disable fte-agent"
echo ""

exit 0
