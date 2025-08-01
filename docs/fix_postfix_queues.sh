#!/bin/sh

# Fix Postfix Queues Script
# This script fixes missing queue directories and post-install script

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

print_status "Fixing Postfix queue directories and post-install script..."

# Stop Postfix if running
print_status "Stopping Postfix service..."
systemctl stop postfix 2>/dev/null || true

# Check if post-install script exists
print_status "Checking for post-install script..."
if [ -f "/usr/lib/postfix/post-install" ]; then
    print_success "post-install script found"
else
    print_error "post-install script missing"
fi

# Check queue directories
print_status "Checking queue directories..."
if [ -d "/var/spool/postfix" ]; then
    print_success "Queue directory exists: /var/spool/postfix"
    ls -la /var/spool/postfix/
else
    print_error "Queue directory missing: /var/spool/postfix"
fi

# Try to run post-install manually if it exists
if [ -f "/usr/lib/postfix/post-install" ]; then
    print_status "Running post-install script..."
    /usr/lib/postfix/post-install create-missing
    print_success "post-install script completed"
fi

# Create queue directories manually if needed
print_status "Creating queue directories manually..."
mkdir -p /var/spool/postfix/{incoming,active,deferred,bounce,defer,flush,trace,private,maildrop,hold,corrupt,public}
mkdir -p /var/spool/postfix/{pid,private,public}

# Set proper ownership
print_status "Setting proper ownership..."
chown -R postfix:postfix /var/spool/postfix
chmod -R 755 /var/spool/postfix

# Set special permissions for private directory
print_status "Setting special permissions for private directory..."
chmod 750 /var/spool/postfix/private
chmod 750 /var/spool/postfix/maildrop

# Create necessary files
print_status "Creating necessary files..."
touch /var/spool/postfix/pid/master.pid
chown postfix:postfix /var/spool/postfix/pid/master.pid

# Check if master program exists
print_status "Checking for master program..."
if [ -f "/usr/lib/postfix/sbin/master" ]; then
    print_success "Master program found in sbin"
    if [ ! -f "/usr/lib/postfix/master" ]; then
        print_status "Creating symlink for master..."
        ln -s sbin/master /usr/lib/postfix/master
        print_success "Master symlink created"
    fi
else
    print_error "Master program not found"
fi

# Test Postfix configuration
print_status "Testing Postfix configuration..."
if postfix check; then
    print_success "Postfix configuration is valid"
else
    print_error "Postfix configuration has errors"
    print_status "Configuration errors:"
    postfix check
fi

# Start Postfix
print_status "Starting Postfix..."
systemctl start postfix

# Check Postfix status
print_status "Checking Postfix status..."
if systemctl is-active --quiet postfix; then
    print_success "Postfix is running successfully"
else
    print_error "Postfix failed to start"
    systemctl status postfix --no-pager -l
fi

print_success "Postfix queue directories and post-install issues have been fixed!"
print_status "You can now run the configuration script:"
print_status "sudo bash fix_postfix_config.sh" 