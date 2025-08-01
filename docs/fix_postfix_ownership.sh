#!/bin/sh

# Fix Postfix Ownership Script
# This script fixes ownership issues and instance conflicts

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

print_status "Fixing Postfix ownership issues and instance conflicts..."

# Stop Postfix
print_status "Stopping Postfix..."
systemctl stop postfix

# Fix ownership of system directories in /var/spool/postfix
print_status "Fixing ownership of system directories..."
chown -R root:root /var/spool/postfix/lib
chown -R root:root /var/spool/postfix/usr
chown -R root:root /var/spool/postfix/etc
chown -R root:root /var/spool/postfix/dev

# Fix ownership of Postfix-specific directories
print_status "Fixing ownership of Postfix directories..."
chown -R postfix:postfix /var/spool/postfix/{incoming,active,deferred,bounce,defer,flush,trace,private,maildrop,hold,corrupt,public,pid}
chown -R postfix:postdrop /var/spool/postfix/public
chown -R postfix:postdrop /var/spool/postfix/maildrop

# Set proper permissions
print_status "Setting proper permissions..."
chmod -R 755 /var/spool/postfix/lib
chmod -R 755 /var/spool/postfix/usr
chmod -R 755 /var/spool/postfix/etc
chmod -R 755 /var/spool/postfix/dev
chmod 750 /var/spool/postfix/private
chmod 775 /var/spool/postfix/public
chmod 775 /var/spool/postfix/maildrop

# Check for multiple Postfix instances
print_status "Checking for multiple Postfix instances..."
postmulti -l || true

# Remove any conflicting instances
print_status "Removing conflicting instances..."
postmulti -d || true

# Check if there are any remaining instances
print_status "Checking remaining instances..."
postmulti -l || true

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

# Check mail logs for errors
print_status "Checking mail logs for errors..."
sleep 5
if tail -n 20 /var/log/mail.log | grep -q "fatal\|error"; then
    print_warning "Found errors in mail logs:"
    tail -n 20 /var/log/mail.log | grep -i "fatal\|error"
else
    print_success "No errors found in mail logs"
fi

print_success "Postfix ownership issues and instance conflicts have been fixed!"
print_status "Summary:"
print_status "1. Fixed ownership of system directories"
print_status "2. Fixed ownership of Postfix directories"
print_status "3. Set proper permissions"
print_status "4. Removed conflicting instances"
print_status "5. Postfix is running successfully"
print_status ""
print_status "You can now run the configuration script:"
print_status "sudo bash fix_postfix_config.sh" 