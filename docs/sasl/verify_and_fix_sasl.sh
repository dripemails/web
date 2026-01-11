#!/bin/bash
#
# Verify SASL User and Fix Configuration
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

SASLDB_PATH="/etc/postfix/sasl/sasldb2"

print_info "=== Verifying SASL Configuration ==="
echo

# 1. List users
print_info "1. Current SASL users:"
sasldblistusers2 -f "$SASLDB_PATH"
echo

# 2. Check file permissions
print_info "2. File permissions:"
ls -la "$SASLDB_PATH"
echo

# 3. Check Postfix SASL path configuration
print_info "3. Checking Postfix SASL path..."
SASL_PATH=$(grep "^smtpd_sasl_path" /etc/postfix/main.cf | awk '{print $3}')
print_info "Current smtpd_sasl_path: $SASL_PATH"

# The issue might be that smtpd_sasl_path should point to the SASL config
# For cyrus SASL with sasldb, we might need to adjust the path
if [ "$SASL_PATH" = "smtpd" ]; then
    print_warn "smtpd_sasl_path is 'smtpd' - this might need to be different"
    print_info "Checking if we need to update it..."
fi
echo

# 4. Check if we need to set SASL_CONF_PATH
print_info "4. Checking SASL environment..."
# Postfix might need to know where the SASL config is
if [ -f /etc/postfix/sasl/smtpd.conf ]; then
    print_info "✓ SASL config file exists: /etc/postfix/sasl/smtpd.conf"
    cat /etc/postfix/sasl/smtpd.conf
else
    print_error "✗ SASL config file missing!"
fi
echo

# 5. Test with testsaslauthd (if available)
print_info "5. Testing SASL authentication directly..."
if command -v testsaslauthd &> /dev/null; then
    print_info "Testing with testsaslauthd..."
    echo "founders" | testsaslauthd -u founders -p aspen45 -s smtp 2>&1 || true
    echo "founders@dripemails.org" | testsaslauthd -u founders@dripemails.org -p aspen45 -s smtp 2>&1 || true
else
    print_warn "testsaslauthd not available"
fi
echo

# 6. Check Postfix master.cf - might need SASL settings there
print_info "6. Checking if master.cf needs SASL configuration..."
if ! grep -q "smtpd_sasl" /etc/postfix/master.cf; then
    print_warn "master.cf doesn't have smtpd_sasl settings"
    print_info "This might be needed for SASL to work properly"
    
    # Backup master.cf
    cp /etc/postfix/master.cf "/etc/postfix/master.cf.backup.$(date +%Y%m%d_%H%M%S)"
    
    # Add SASL settings to smtp service
    if grep -q "^smtp.*smtpd$" /etc/postfix/master.cf; then
        print_info "Adding SASL settings to master.cf..."
        # Find the smtp line and add SASL options after it
        sed -i '/^smtp.*smtpd$/a\  -o smtpd_sasl_auth_enable=yes\n  -o smtpd_sasl_security_options=noanonymous\n  -o smtpd_sasl_local_domain=$myhostname' /etc/postfix/master.cf
        print_info "✓ Added SASL settings to master.cf"
    fi
else
    print_info "✓ master.cf already has SASL settings"
fi
echo

# 7. Update main.cf to ensure correct SASL path
print_info "7. Verifying main.cf SASL configuration..."
# Check if we need to add SASL_CONF_PATH or update smtpd_sasl_path
if ! grep -q "smtpd_sasl_path.*smtpd" /etc/postfix/main.cf; then
    print_warn "SASL path might be incorrect"
fi

# For cyrus SASL with sasldb, the path should be "smtpd" but we might need
# to ensure the SASL config directory is in the right place
print_info "Current SASL settings in main.cf:"
grep -E "^smtpd_sasl" /etc/postfix/main.cf
echo

# 8. Test Postfix configuration
print_info "8. Testing Postfix configuration..."
if postfix check; then
    print_info "✓ Postfix configuration is valid"
else
    print_error "✗ Postfix configuration has errors!"
    exit 1
fi
echo

# 9. Restart Postfix
print_info "9. Restarting Postfix..."
systemctl restart postfix
sleep 2
if systemctl is-active --quiet postfix; then
    print_info "✓ Postfix restarted"
else
    print_error "✗ Postfix failed to start!"
    exit 1
fi
echo

# 10. Final authentication test
print_info "10. Testing authentication..."
python3 << 'EOF'
import smtplib
import sys

formats = [
    ('founders', 'aspen45'),
    ('founders@dripemails.org', 'aspen45'),
]

for username, password in formats:
    try:
        print(f"\nTrying: {username}")
        server = smtplib.SMTP('localhost', 25)
        server.set_debuglevel(1)
        server.ehlo()
        server.login(username, password)
        print(f"✓ SUCCESS with: {username}")
        server.quit()
        sys.exit(0)
    except smtplib.SMTPAuthenticationError as e:
        print(f"✗ FAILED: {e}")
    except Exception as e:
        print(f"✗ Error: {e}")

print("\n✗ All authentication attempts failed")
sys.exit(1)
EOF

echo
print_info "=== Verification Complete ==="

