#!/bin/bash
#
# Setup Postfix for Port 587 (Submission Port)
# This is simpler than port 25 and usually works better with authentication
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

print_info "=== Setting up Port 587 (Submission Port) ==="
echo

# 1. Check if submission service exists in master.cf
print_info "1. Checking Postfix master.cf for submission service..."
if grep -q "^submission" /etc/postfix/master.cf; then
    print_info "✓ Submission service already configured"
    grep -A 10 "^submission" /etc/postfix/master.cf | head -15
else
    print_info "Adding submission service to master.cf..."
    
    # Backup master.cf
    cp /etc/postfix/master.cf "/etc/postfix/master.cf.backup.$(date +%Y%m%d_%H%M%S)"
    
    # Add submission service (port 587)
    cat >> /etc/postfix/master.cf << 'EOF'

# Submission port (587) - simpler than port 25
submission inet n       -       y       -       -       smtpd
  -o syslog_name=postfix/submission
  -o smtpd_tls_security_level=encrypt
  -o smtpd_sasl_auth_enable=yes
  -o smtpd_tls_auth_only=yes
  -o smtpd_reject_unlisted_recipient=no
  -o smtpd_client_restrictions=$mua_client_restrictions
  -o smtpd_helo_restrictions=$mua_helo_restrictions
  -o smtpd_sender_restrictions=$mua_sender_restrictions
  -o smtpd_recipient_restrictions=
  -o smtpd_relay_restrictions=permit_sasl_authenticated,reject
  -o milter_macro_daemon_name=ORIGINATING
EOF
    print_info "✓ Added submission service"
fi
echo

# 2. Ensure SASL is configured
print_info "2. Verifying SASL configuration..."
if grep -q "smtpd_sasl_auth_enable = yes" /etc/postfix/main.cf; then
    print_info "✓ SASL is enabled in main.cf"
else
    print_warn "SASL not enabled - adding it..."
    cat >> /etc/postfix/main.cf << 'EOF'

# SASL Authentication
smtpd_sasl_type = cyrus
smtpd_sasl_auth_enable = yes
smtpd_sasl_security_options = noanonymous
smtpd_sasl_local_domain = $myhostname
broken_sasl_auth_clients = yes
EOF
    print_info "✓ Added SASL configuration"
fi
echo

# 3. Ensure SASL config file exists
print_info "3. Ensuring SASL config file exists..."
mkdir -p /usr/lib/sasl2
mkdir -p /etc/sasl2
mkdir -p /etc/postfix/sasl

cat > /etc/postfix/sasl/smtpd.conf << 'EOF'
pwcheck_method: auxprop
auxprop_plugin: sasldb
mech_list: PLAIN LOGIN
sasldb_path: /etc/postfix/sasl/sasldb2
EOF

cp /etc/postfix/sasl/smtpd.conf /usr/lib/sasl2/smtpd.conf
cp /etc/postfix/sasl/smtpd.conf /etc/sasl2/smtpd.conf

print_info "✓ SASL config files created"
echo

# 4. Verify SASL user exists
print_info "4. Verifying SASL user..."
SASLDB_PATH="/etc/postfix/sasl/sasldb2"
if [ -f "$SASLDB_PATH" ]; then
    print_info "Current SASL users:"
    sasldblistusers2 -f "$SASLDB_PATH" || print_warn "No users found"
else
    print_warn "SASL database doesn't exist - you may need to create a user"
    print_info "Create user with: sudo saslpasswd2 -f $SASLDB_PATH -u dripemails.org founders"
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
    print_info "✓ Postfix restarted"
else
    print_error "✗ Postfix failed to start!"
    exit 1
fi
echo

# 7. Test port 587
print_info "7. Testing port 587..."
sleep 2
if netstat -tlnp 2>/dev/null | grep ":587 " || ss -tlnp 2>/dev/null | grep ":587 "; then
    print_info "✓ Port 587 is listening"
else
    print_warn "Port 587 might not be listening (check firewall)"
fi
echo

# 8. Test authentication on port 587
print_info "8. Testing authentication on port 587..."
python3 << 'EOF'
import smtplib
import sys

formats = [
    ('founders', 'aspen45'),
    ('founders@dripemails.org', 'aspen45'),
]

for username, password in formats:
    try:
        print(f"\nTrying port 587 with: {username}")
        server = smtplib.SMTP('localhost', 587)
        server.starttls()  # Enable TLS
        server.ehlo()
        server.login(username, password)
        print(f"✓ SUCCESS on port 587 with: {username}")
        server.quit()
        sys.exit(0)
    except smtplib.SMTPAuthenticationError as e:
        print(f"✗ AUTH FAILED: {e}")
    except Exception as e:
        print(f"✗ Error: {e}")

print("\n✗ All authentication attempts failed on port 587")
sys.exit(1)
EOF

AUTH_RESULT=$?

echo
if [ $AUTH_RESULT -eq 0 ]; then
    print_info "=== SUCCESS! Port 587 is working ==="
    print_info "Update your .env file:"
    print_info "  EMAIL_PORT=587"
    print_info "  EMAIL_USE_TLS=True"
else
    print_error "=== Authentication still failing on port 587 ==="
    print_info "Check:"
    print_info "  1. SASL user exists: sasldblistusers2 -f /etc/postfix/sasl/sasldb2"
    print_info "  2. Postfix logs: tail -f /var/log/mail.log"
fi

