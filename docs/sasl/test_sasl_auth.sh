#!/bin/bash
#
# Test SASL Authentication Script
# This script helps debug SMTP AUTH issues

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

SASLDB_PATH="/etc/postfix/sasl/sasldb2"

print_info "=== SASL Authentication Debug ==="
echo

# 1. List all SASL users
print_info "1. Listing all SASL users:"
if [ -f "$SASLDB_PATH" ]; then
    sasldblistusers2 -f "$SASLDB_PATH"
else
    print_error "SASL database not found at $SASLDB_PATH"
    exit 1
fi
echo

# 2. Test authentication with different username formats
print_info "2. Testing authentication formats..."
echo

USERNAME=${1:-founders}
PASSWORD=${2:-aspen45}
DOMAIN=$(hostname -d 2>/dev/null || hostname -f 2>/dev/null || echo "dripemails.org")

print_info "Testing with username: $USERNAME"
print_info "Testing with password: [hidden]"
print_info "Domain: $DOMAIN"
echo

# 3. Test with Python smtplib
print_info "3. Testing with Python smtplib (like Django does):"
python3 << EOF
import smtplib
import sys

username = "$USERNAME"
password = "$PASSWORD"
domain = "$DOMAIN"

# Test different username formats
formats = [
    username,  # Just username
    f"{username}@{domain}",  # Full email
    f"{username}@{domain}:{username}",  # With realm
]

for user_format in formats:
    try:
        print(f"\\nTrying: '{user_format}'")
        server = smtplib.SMTP('localhost', 25)
        server.set_debuglevel(1)
        server.ehlo()
        try:
            server.login(user_format, password)
            print(f"✓ SUCCESS with format: '{user_format}'")
            server.quit()
            sys.exit(0)
        except smtplib.SMTPAuthenticationError as e:
            print(f"✗ FAILED with format: '{user_format}'")
            print(f"  Error: {e}")
        server.quit()
    except Exception as e:
        print(f"✗ Connection error: {e}")

print("\\n✗ All authentication attempts failed")
sys.exit(1)
EOF

echo
print_info "=== Debug Complete ==="

