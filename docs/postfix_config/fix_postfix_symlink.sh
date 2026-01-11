#!/bin/sh

# Postfix Symlink Fix Script
# This script fixes the postfix-script symlink issue

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

print_status "Fixing Postfix symlink issue..."

# Check current state
print_status "Checking current postfix-script locations..."
if [ -f "/usr/lib/postfix/sbin/postfix-script" ]; then
    print_success "postfix-script found at: /usr/lib/postfix/sbin/postfix-script"
else
    print_error "postfix-script not found at expected location"
    exit 1
fi

if [ -f "/usr/lib/postfix/postfix-script" ]; then
    print_warning "postfix-script already exists at: /usr/lib/postfix/postfix-script"
    ls -la /usr/lib/postfix/postfix-script
else
    print_status "Creating symlink for postfix-script..."
    ln -s sbin/postfix-script /usr/lib/postfix/postfix-script
fi

# Verify the symlink
print_status "Verifying symlink..."
if [ -L "/usr/lib/postfix/postfix-script" ]; then
    print_success "Symlink created successfully"
    ls -la /usr/lib/postfix/postfix-script
else
    print_error "Failed to create symlink"
    exit 1
fi

# Test Postfix configuration
print_status "Testing Postfix configuration..."
if postfix check; then
    print_success "Postfix configuration is valid"
else
    print_error "Postfix configuration has errors"
    exit 1
fi

# Reload Postfix
print_status "Reloading Postfix..."
systemctl reload postfix

# Check Postfix status
print_status "Checking Postfix status..."
if systemctl is-active --quiet postfix; then
    print_success "Postfix is running successfully"
else
    print_error "Postfix failed to start"
    systemctl status postfix --no-pager -l
    exit 1
fi

print_success "Postfix symlink issue has been fixed!"
print_status "You can now run the SSL certificate installation script"
print_status "Run: sudo bash install_postfix_ssl.sh dripemails.org" 