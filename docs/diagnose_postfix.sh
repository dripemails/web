#!/bin/sh

# Postfix Diagnostic and Fix Script
# This script diagnoses and fixes Postfix installation issues

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

print_status "Diagnosing Postfix installation..."

# Check Postfix package status
print_status "Checking Postfix package status..."
dpkg -l | grep postfix

# Check if postfix command exists
print_status "Checking postfix command..."
if command -v postfix > /dev/null 2>&1; then
    print_success "postfix command found at: $(which postfix)"
else
    print_error "postfix command not found"
fi

# Check Postfix directories
print_status "Checking Postfix directories..."
for dir in /usr/lib/postfix /usr/sbin /var/lib/postfix /var/spool/postfix; do
    if [ -d "$dir" ]; then
        print_success "Directory exists: $dir"
    else
        print_error "Directory missing: $dir"
    fi
done

# Check Postfix files
print_status "Checking Postfix files..."
for file in /usr/lib/postfix/postfix-script /usr/sbin/postfix /etc/postfix/main.cf; do
    if [ -f "$file" ]; then
        print_success "File exists: $file"
    else
        print_error "File missing: $file"
    fi
done

# Check Postfix service status
print_status "Checking Postfix service status..."
systemctl status postfix --no-pager -l

# Try to find postfix-script in different locations
print_status "Searching for postfix-script..."
find /usr -name "postfix-script" 2>/dev/null || print_warning "postfix-script not found in /usr"

# Check if it's a symlink issue
print_status "Checking for symlinks..."
ls -la /usr/lib/postfix/ | head -10

# Try to fix the installation
print_status "Attempting to fix Postfix installation..."

# Remove Postfix completely
print_status "Removing Postfix completely..."
apt remove --purge postfix -y
apt autoremove -y

# Clean up any remaining files
print_status "Cleaning up remaining files..."
rm -rf /etc/postfix /var/lib/postfix /var/spool/postfix 2>/dev/null || true

# Reinstall Postfix
print_status "Reinstalling Postfix..."
apt update
apt install postfix -y

# Check if postfix-script exists now
print_status "Checking if postfix-script exists after reinstall..."
if [ -f "/usr/lib/postfix/postfix-script" ]; then
    print_success "postfix-script found after reinstall"
else
    print_error "postfix-script still missing after reinstall"
    print_status "Checking what's in /usr/lib/postfix/:"
    ls -la /usr/lib/postfix/
fi

# Check Postfix configuration
print_status "Checking Postfix configuration..."
if postfix check; then
    print_success "Postfix configuration is valid"
else
    print_error "Postfix configuration has errors"
fi

print_status "Diagnosis complete!" 