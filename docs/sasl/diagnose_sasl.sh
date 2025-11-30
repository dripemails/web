#!/bin/bash
#
# Diagnose SASL Authentication Issues
#

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

print_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
print_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
print_error() { echo -e "${RED}[ERROR]${NC} $1"; }

SASLDB_PATH="/etc/postfix/sasl/sasldb2"

print_info "=== SASL Authentication Diagnosis ==="
echo

# 1. Check SASL database exists
print_info "1. Checking SASL database..."
if [ -f "$SASLDB_PATH" ]; then
    print_info "✓ SASL database exists: $SASLDB_PATH"
    ls -la "$SASLDB_PATH"
else
    print_error "✗ SASL database not found: $SASLDB_PATH"
    exit 1
fi
echo

# 2. List all users
print_info "2. Listing all SASL users:"
sasldblistusers2 -f "$SASLDB_PATH"
echo

# 3. Check Postfix main.cf SASL settings
print_info "3. Checking Postfix SASL configuration in main.cf:"
grep -E "smtpd_sasl|sasl" /etc/postfix/main.cf || print_warn "No SASL settings found in main.cf"
echo

# 4. Check Postfix master.cf
print_info "4. Checking Postfix master.cf for SASL:"
grep -A 5 "^smtp" /etc/postfix/master.cf | grep -E "smtpd_sasl|sasl" || print_warn "No SASL settings in master.cf smtp service"
echo

# 5. Check SASL configuration file
print_info "5. Checking SASL configuration file:"
if [ -f /etc/postfix/sasl/smtpd.conf ]; then
    cat /etc/postfix/sasl/smtpd.conf
else
    print_error "✗ SASL config file not found: /etc/postfix/sasl/smtpd.conf"
fi
echo

# 6. Test if AUTH is advertised
print_info "6. Testing if SMTP AUTH is advertised:"
if echo "EHLO localhost" | timeout 5 telnet localhost 25 2>/dev/null | grep -q "AUTH"; then
    print_info "✓ SMTP AUTH is advertised"
    echo "EHLO localhost" | timeout 5 telnet localhost 25 2>/dev/null | grep "AUTH"
else
    print_error "✗ SMTP AUTH is NOT advertised"
fi
echo

# 7. Check Postfix logs for authentication errors
print_info "7. Recent Postfix authentication errors:"
tail -20 /var/log/mail.log | grep -i "sasl\|auth" || print_warn "No recent SASL/auth errors in logs"
echo

# 8. Test authentication manually
print_info "8. Testing authentication with Python (like Django):"
USERNAME=${1:-founders@dripemails.org}
PASSWORD=${2:-aspen45}

python3 << EOF
import smtplib
import sys

username = "$USERNAME"
password = "$PASSWORD"

print(f"Testing with username: {username}")
print(f"Password length: {len(password)}")

try:
    server = smtplib.SMTP('localhost', 25)
    server.set_debuglevel(2)  # Full debug output
    server.ehlo()
    
    print("\\nAttempting login...")
    server.login(username, password)
    print("✓ Authentication SUCCESSFUL!")
    server.quit()
    sys.exit(0)
except smtplib.SMTPAuthenticationError as e:
    print(f"\\n✗ Authentication FAILED: {e}")
    sys.exit(1)
except Exception as e:
    print(f"\\n✗ Error: {e}")
    sys.exit(1)
EOF

echo
print_info "=== Diagnosis Complete ==="

