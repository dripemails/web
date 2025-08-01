#!/bin/sh

# Complete Postfix Fix Script
# This script completely reinstalls Postfix with all components

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

print_status "Completely reinstalling Postfix..."

# Stop Postfix if running
print_status "Stopping Postfix service..."
systemctl stop postfix 2>/dev/null || true

# Remove Postfix completely
print_status "Removing Postfix completely..."
apt remove --purge postfix -y
apt autoremove -y

# Clean up all Postfix files
print_status "Cleaning up Postfix files..."
rm -rf /etc/postfix /var/lib/postfix /var/spool/postfix /var/log/mail.log* 2>/dev/null || true

# Update package lists
print_status "Updating package lists..."
apt update

# Install Postfix with all dependencies
print_status "Installing Postfix with all dependencies..."
apt install -y postfix mailutils

# Check if Postfix was installed correctly
print_status "Verifying Postfix installation..."
if ! command -v postfix > /dev/null 2>&1; then
    print_error "Postfix installation failed"
    exit 1
fi

# Check for essential Postfix files
print_status "Checking essential Postfix files..."
for file in /usr/lib/postfix/sbin/postfix-script /usr/lib/postfix/master /usr/sbin/postfix; do
    if [ -f "$file" ]; then
        print_success "File exists: $file"
    else
        print_error "File missing: $file"
    fi
done

# Create the symlink if needed
print_status "Creating postfix-script symlink..."
if [ ! -L "/usr/lib/postfix/postfix-script" ]; then
    ln -s sbin/postfix-script /usr/lib/postfix/postfix-script
    print_success "Symlink created"
else
    print_success "Symlink already exists"
fi

# Test Postfix configuration
print_status "Testing Postfix configuration..."
if postfix check; then
    print_success "Postfix configuration is valid"
else
    print_error "Postfix configuration has errors"
    print_status "Checking Postfix status:"
    systemctl status postfix --no-pager -l
    exit 1
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
    exit 1
fi

# Enable Postfix to start on boot
print_status "Enabling Postfix to start on boot..."
systemctl enable postfix

print_success "Postfix has been completely reinstalled and is working!"
print_status "You can now run the configuration script:"
print_status "sudo bash fix_postfix_config.sh" 