#!/bin/sh

# Fix Master Program Script
# This script finds and fixes the missing master program issue

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

print_status "Investigating the missing master program issue..."

# Check what's in the Postfix directory
print_status "Checking Postfix directory contents..."
ls -la /usr/lib/postfix/

# Check if master exists in sbin
print_status "Checking for master in sbin..."
if [ -f "/usr/lib/postfix/sbin/master" ]; then
    print_success "Master found in sbin: /usr/lib/postfix/sbin/master"
else
    print_error "Master not found in sbin"
fi

# Check if master exists in the main directory
print_status "Checking for master in main directory..."
if [ -f "/usr/lib/postfix/master" ]; then
    print_success "Master found in main directory: /usr/lib/postfix/master"
else
    print_error "Master not found in main directory"
fi

# Search for master program in the system
print_status "Searching for master program in the system..."
find /usr -name "master" -type f 2>/dev/null | grep postfix || true

# Check if it's a symlink issue
print_status "Checking if master should be a symlink..."
if [ -L "/usr/lib/postfix/master" ]; then
    print_status "Master is a symlink:"
    ls -la /usr/lib/postfix/master
else
    print_status "Master is not a symlink"
fi

# Try to find where master should be
print_status "Checking package contents..."
dpkg -L postfix | grep master || true

# Check if we need to create a symlink
print_status "Attempting to fix master program..."
if [ -f "/usr/lib/postfix/sbin/master" ] && [ ! -f "/usr/lib/postfix/master" ]; then
    print_status "Creating symlink for master..."
    ln -s sbin/master /usr/lib/postfix/master
    print_success "Master symlink created"
elif [ -f "/usr/lib/postfix/sbin/master" ] && [ -L "/usr/lib/postfix/master" ]; then
    print_status "Master symlink already exists"
    ls -la /usr/lib/postfix/master
else
    print_error "Cannot find master program to create symlink"
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

# Check Postfix status
print_status "Checking Postfix status..."
if systemctl is-active --quiet postfix; then
    print_success "Postfix is running successfully"
else
    print_error "Postfix is not running"
    systemctl status postfix --no-pager -l
fi

print_status "Investigation complete!" 