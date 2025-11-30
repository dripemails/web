#!/bin/bash
#
# Fix SASL Authentication - Recreate user and verify configuration
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

print_info "=== Fixing SASL Authentication ==="
echo

# 1. Delete existing user
print_info "1. Removing existing user..."
if [ -f "$SASLDB_PATH" ]; then
    # Try to delete with different formats
    saslpasswd2 -f "$SASLDB_PATH" -u "$DOMAIN" -d "$USERNAME" 2>/dev/null || true
    saslpasswd2 -f "$SASLDB_PATH" -u "$DOMAIN" -d "${USERNAME}@${DOMAIN}" 2>/dev/null || true
    print_info "Old user entries removed"
fi
echo

# 2. Recreate user with just username (no @domain in username)
print_info "2. Creating user with format: $USERNAME (domain: $DOMAIN)"
printf '%s' "$PASSWORD" | saslpasswd2 -f "$SASLDB_PATH" -p -u "$DOMAIN" "$USERNAME"
chmod 600 "$SASLDB_PATH"
chown postfix:postfix "$SASLDB_PATH"
echo

# 3. Verify user
print_info "3. Verifying user creation:"
sasldblistusers2 -f "$SASLDB_PATH"
echo

# 4. Check Postfix SASL configuration
print_info "4. Verifying Postfix SASL configuration..."
if ! grep -q "smtpd_sasl_auth_enable = yes" /etc/postfix/main.cf; then
    print_error "SASL not enabled in main.cf!"
    exit 1
fi

# Check if smtpd_sasl_path is correct
if grep -q "smtpd_sasl_path = smtpd" /etc/postfix/main.cf; then
    print_info "✓ SASL path is configured"
else
    print_warn "SASL path might be missing"
fi
echo

# 5. Test Postfix configuration
print_info "5. Testing Postfix configuration..."
if postfix check; then
    print_info "✓ Postfix configuration is valid"
else
    print_error "✗ Postfix configuration has errors!"
    exit 1
fi
echo

# 6. Restart Postfix
print_info "6. Restarting Postfix..."
systemctl restart postfix
sleep 2
if systemctl is-active --quiet postfix; then
    print_info "✓ Postfix restarted successfully"
else
    print_error "✗ Postfix failed to start!"
    exit 1
fi
echo

# 7. Test authentication
print_info "7. Testing authentication..."
print_info "Testing with username: $USERNAME"
python3 << EOF
import smtplib
import sys

username = "$USERNAME"
password = "$PASSWORD"

try:
    server = smtplib.SMTP('localhost', 25)
    server.ehlo()
    server.login(username, password)
    print("✓ Authentication SUCCESSFUL!")
    server.quit()
    sys.exit(0)
except smtplib.SMTPAuthenticationError as e:
    print(f"✗ Authentication FAILED: {e}")
    print("\\nTrying with full email format...")
    try:
        server = smtplib.SMTP('localhost', 25)
        server.ehlo()
        server.login(f"{username}@{DOMAIN}", password)
        print(f"✓ Authentication SUCCESSFUL with {username}@{DOMAIN}!")
        server.quit()
        sys.exit(0)
    except Exception as e2:
        print(f"✗ Also failed: {e2}")
    sys.exit(1)
except Exception as e:
    print(f"✗ Error: {e}")
    sys.exit(1)
EOF

echo
print_info "=== Fix Complete ==="
print_info "If authentication still fails, check:"
print_info "  1. Password is correct: $PASSWORD"
print_info "  2. Username format: Try both '$USERNAME' and '${USERNAME}@${DOMAIN}'"
print_info "  3. Postfix logs: tail -f /var/log/mail.log"

