#!/bin/bash

# Fix ownership warnings and start Postfix after SSL installation
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

print_status "Fixing ownership warnings and starting Postfix..."

# Step 1: Fix ownership of problematic directories
print_status "Step 1: Fixing ownership of Postfix directories..."
chown -R root:root /var/spool/postfix/lib/x86_64-linux-gnu/
chown -R root:root /var/spool/postfix/usr/lib/
chown -R root:root /var/spool/postfix/usr/lib/zoneinfo/
chown -R root:root /var/spool/postfix/usr/lib/sasl2/
print_success "Ownership fixed"

# Step 2: Set proper permissions
print_status "Step 2: Setting proper permissions..."
find /var/spool/postfix/lib/x86_64-linux-gnu/ -type d -exec chmod 755 {} \;
find /var/spool/postfix/lib/x86_64-linux-gnu/ -type f -exec chmod 644 {} \;
find /var/spool/postfix/usr/lib/ -type d -exec chmod 755 {} \;
find /var/spool/postfix/usr/lib/ -type f -exec chmod 644 {} \;
print_success "Permissions set"

# Step 3: Test Postfix configuration
print_status "Step 3: Testing Postfix configuration..."
if postfix check; then
    print_success "Postfix configuration is valid"
else
    print_error "Postfix configuration has errors"
    postfix check
    exit 1
fi

# Step 4: Start Postfix
print_status "Step 4: Starting Postfix..."
systemctl start postfix
sleep 3

# Step 5: Check if Postfix is running
print_status "Step 5: Checking Postfix status..."
if systemctl is-active --quiet postfix; then
    print_success "Postfix is running successfully"
else
    print_warning "Postfix failed to start via systemctl, trying manual start..."
    postfix start
    sleep 3
    
    if pgrep -f "postfix.*master" > /dev/null; then
        print_success "Postfix started manually"
    else
        print_error "Postfix failed to start"
        systemctl status postfix --no-pager -l
        exit 1
    fi
fi

# Step 6: Check SMTP ports
print_status "Step 6: Checking SMTP ports..."
sleep 3
if netstat -tlnp | grep -q ":25\|:587\|:465"; then
    print_success "SMTP ports are listening:"
    netstat -tlnp | grep -E ":(25|587|465)"
else
    print_warning "SMTP ports are not listening"
fi

# Step 7: Test SSL connections
print_status "Step 7: Testing SSL connections..."
if echo "QUIT" | openssl s_client -connect localhost:465 -quiet 2>/dev/null | grep -q "220"; then
    print_success "SSL connection to port 465 is working"
else
    print_warning "SSL connection to port 465 failed"
fi

print_success "Postfix ownership fix completed!"
print_status "Summary:"
print_status "1. Fixed ownership of Postfix directories"
print_status "2. Set proper permissions"
print_status "3. Postfix is running successfully"
print_status "4. SMTP ports should be listening"
print_status ""
print_status "You can now test SSL connections:"
print_status "openssl s_client -connect dripemails.org:465"
print_status "openssl s_client -connect dripemails.org:587" 