#!/bin/bash
#
# Recreate SASL User with Correct Password
# This script deletes and recreates the SASL user interactively
#

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

print_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
print_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
print_error() { echo -e "${RED}[ERROR]${NC} $1"; }

if [ "$EUID" -ne 0 ]; then 
    print_error "Please run as root (use sudo)"
    exit 1
fi

USERNAME=${1:-founders}
PASSWORD=${2:-aspen45}
DOMAIN=$(hostname -d 2>/dev/null || hostname -f 2>/dev/null || echo "dripemails.org")
SASLDB_PATH="/etc/postfix/sasl/sasldb2"

print_info "=== Recreating SASL User ==="
echo

# 1. Delete existing user
print_info "1. Deleting existing user '$USERNAME'..."
if [ -f "$SASLDB_PATH" ]; then
    # Try to delete with different formats
    saslpasswd2 -f "$SASLDB_PATH" -u "$DOMAIN" -d "$USERNAME" 2>/dev/null && print_info "✓ Deleted $USERNAME@$DOMAIN" || print_warn "User might not exist or already deleted"
else
    print_warn "SASL database doesn't exist yet"
fi
echo

# 2. Verify deletion
print_info "2. Verifying deletion:"
if sasldblistusers2 -f "$SASLDB_PATH" 2>/dev/null | grep -q "$USERNAME"; then
    print_warn "User still exists, trying force deletion..."
    # Try alternative deletion method
    sasldblistusers2 -f "$SASLDB_PATH" | grep "$USERNAME" || print_info "User deleted"
else
    print_info "✓ User deleted successfully"
fi
echo

# 3. Create user interactively (most reliable method)
print_info "3. Creating user '$USERNAME@$DOMAIN' with interactive password entry..."
print_warn "You will be prompted to enter the password twice"
print_info "Enter password: $PASSWORD"
echo

# Create user - this will prompt for password
echo -e "${PASSWORD}\n${PASSWORD}" | saslpasswd2 -f "$SASLDB_PATH" -u "$DOMAIN" "$USERNAME"

# Set permissions
chmod 600 "$SASLDB_PATH"
chown postfix:postfix "$SASLDB_PATH"
print_info "✓ User created"
echo

# 4. Verify user
print_info "4. Verifying user creation:"
sasldblistusers2 -f "$SASLDB_PATH"
echo

# 5. Test authentication
print_info "5. Testing authentication..."
python3 << EOF
import smtplib
import sys

username = "$USERNAME"
password = "$PASSWORD"
domain = "$DOMAIN"

# Test with just username first
print(f"Testing with username: {username}")
try:
    server = smtplib.SMTP('localhost', 25)
    server.ehlo()
    server.login(username, password)
    print("✓ SUCCESS with username: " + username)
    server.quit()
    sys.exit(0)
except smtplib.SMTPAuthenticationError as e:
    print(f"✗ FAILED with username: {e}")
    
    # Try with full email
    print(f"\\nTesting with full email: {username}@{domain}")
    try:
        server = smtplib.SMTP('localhost', 25)
        server.ehlo()
        server.login(f"{username}@{domain}", password)
        print(f"✓ SUCCESS with email: {username}@{domain}")
        server.quit()
        sys.exit(0)
    except smtplib.SMTPAuthenticationError as e2:
        print(f"✗ FAILED with email: {e2}")
        sys.exit(1)
except Exception as e:
    print(f"✗ Error: {e}")
    sys.exit(1)
EOF

AUTH_RESULT=$?

echo
if [ $AUTH_RESULT -eq 0 ]; then
    print_info "=== SUCCESS! User recreated and authentication works ==="
    print_info "Update your .env file with the working username format"
else
    print_error "=== Authentication still failing ==="
    print_info "Try checking:"
    print_info "  1. Password is exactly: $PASSWORD"
    print_info "  2. Check Postfix logs: tail -f /var/log/mail.log"
    print_info "  3. Verify user exists: sasldblistusers2 -f $SASLDB_PATH"
fi

