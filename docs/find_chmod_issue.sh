#!/bin/sh

# Find Chmod Issue Script
# This script finds where the problematic chmod command is coming from

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

print_status "Searching for problematic chmod commands..."

# Search for chmod commands in renewal hooks
print_status "Searching in renewal hooks..."
find /etc/letsencrypt/renewal-hooks -name "*.sh" -exec grep -l "chmod" {} \; 2>/dev/null || true

# Search for chmod commands in the renewal configuration
print_status "Searching in renewal configuration..."
grep -r "chmod" /etc/letsencrypt/renewal/ 2>/dev/null || true

# Search for chmod commands in system-wide scripts
print_status "Searching in system scripts..."
find /etc -name "*.sh" -exec grep -l "chmod.*letsencrypt" {} \; 2>/dev/null || true

# Check if there's a global post-hook
print_status "Checking for global post-hook..."
if [ -f "/etc/letsencrypt/cli.ini" ]; then
    print_status "Global CLI config found:"
    cat /etc/letsencrypt/cli.ini
else
    print_warning "No global CLI config found"
fi

# Check for any environment variables that might be causing this
print_status "Checking environment variables..."
env | grep -i letsencrypt || true

# Search for any scripts that might be called during renewal
print_status "Searching for renewal-related scripts..."
find /etc -name "*renew*" -type f 2>/dev/null || true

# Check the actual renewal configuration more carefully
print_status "Detailed renewal configuration analysis..."
if [ -f "/etc/letsencrypt/renewal/dripemails.org.conf" ]; then
    print_status "Full renewal configuration:"
    cat /etc/letsencrypt/renewal/dripemails.org.conf
fi

# Check if there are any other renewal configurations
print_status "All renewal configurations:"
ls -la /etc/letsencrypt/renewal/ 2>/dev/null || true

print_status "Search complete!" 