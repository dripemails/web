#!/bin/sh

# SMTP Debug and Fix Script
# This script diagnoses and fixes the SMTP port issue

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
if [ "$(id -u)" -ne 0 ]; then
    print_error "This script must be run as root (use sudo)"
    exit 1
fi

print_status "Starting SMTP debug and fix..."

# Step 1: Check current Postfix status
print_status "Step 1: Checking current Postfix status..."
systemctl status postfix --no-pager -l

# Step 2: Check what processes are running
print_status "Step 2: Checking Postfix processes..."
ps aux | grep postfix || echo "No postfix processes found"

# Step 3: Check if any ports are listening
print_status "Step 3: Checking listening ports..."
netstat -tlnp | grep -E ":(25|587|465)" || echo "No SMTP ports found"

# Step 4: Check Postfix logs for startup errors
print_status "Step 4: Checking Postfix logs..."
tail -n 50 /var/log/mail.log

# Step 5: Stop Postfix completely
print_status "Step 5: Stopping Postfix completely..."
systemctl stop postfix 2>/dev/null || true
print_success "Postfix stopped"

# Step 6: Kill all postfix processes
print_status "Step 6: Killing all postfix processes..."
pkill -f postfix 2>/dev/null || true
sleep 3
print_success "All postfix processes killed"

# Step 7: Completely disable postmulti
print_status "Step 7: Completely disabling postmulti..."
rm -f /etc/postfix/postmulti-instance-* 2>/dev/null || true
rm -f /etc/postfix/master.cf.* 2>/dev/null || true
rm -f /etc/postfix/main.cf.* 2>/dev/null || true
print_success "Postmulti files removed"

# Step 8: Force single instance mode
print_status "Step 8: Forcing single instance mode..."
postconf -e "multi_instance_enable = no" 2>/dev/null || true
postconf -e "multi_instance_name = " 2>/dev/null || true
postconf -e "multi_instance_group = " 2>/dev/null || true
postconf -e "multi_instance_directories = " 2>/dev/null || true
print_success "Single instance mode forced"

# Step 9: Check for remaining postmulti instances
print_status "Step 9: Checking for remaining postmulti instances..."
postmulti -l 2>/dev/null || echo "No postmulti instances found"

# Step 10: Try to start Postfix manually
print_status "Step 10: Starting Postfix manually..."
postfix start
sleep 5
print_success "Postfix started manually"

# Step 11: Check if it's running
print_status "Step 11: Checking Postfix status after manual start..."
systemctl status postfix --no-pager -l

# Step 12: Check processes again
print_status "Step 12: Checking Postfix processes after manual start..."
ps aux | grep postfix || echo "No postfix processes found"

# Step 13: Check ports again
print_status "Step 13: Checking listening ports after manual start..."
netstat -tlnp | grep -E ":(25|587|465)" || echo "No SMTP ports found"

# Step 14: Check logs again
print_status "Step 14: Checking logs after manual start..."
tail -n 20 /var/log/mail.log

# Step 15: Test SMTP connection
print_status "Step 15: Testing SMTP connection..."
if echo "QUIT" | telnet localhost 25 2>/dev/null | grep -q "220"; then
    print_success "SMTP port 25 is responding"
else
    print_warning "SMTP port 25 is not responding"
fi

# Step 16: Check Postfix configuration
print_status "Step 16: Checking Postfix configuration..."
postfix check

# Step 17: Show current configuration
print_status "Step 17: Showing current configuration..."
postconf -n | head -20

print_status "Debug and fix completed!"
print_status "Check the output above to see what's happening with Postfix"
print_status ""
print_status "If SMTP ports are still not listening, the issue might be:"
print_status "1. Configuration errors in master.cf or main.cf"
print_status "2. Missing dependencies"
print_status "3. Permission issues"
print_status "4. System resource constraints" 