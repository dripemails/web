#!/bin/bash
#
# Enable Port 587 (Submission) in Postfix
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

print_info "=== Enabling Port 587 (Submission) ==="
echo

# 1. Check current master.cf
print_info "1. Checking current master.cf configuration..."
if grep -q "^submission" /etc/postfix/master.cf; then
    print_info "✓ Submission service found"
    grep -A 15 "^submission" /etc/postfix/master.cf | head -20
else
    print_info "Submission service not found - adding it..."
    
    # Backup
    cp /etc/postfix/master.cf "/etc/postfix/master.cf.backup.$(date +%Y%m%d_%H%M%S)"
    
    # Check if submission is commented out
    if grep -q "^#submission" /etc/postfix/master.cf; then
        print_info "Uncommenting submission service..."
        sed -i 's/^#submission/submission/' /etc/postfix/master.cf
        sed -i '/^submission/,/^#/ s/^#//' /etc/postfix/master.cf
    else
        # Add submission service
        print_info "Adding submission service..."
        cat >> /etc/postfix/master.cf << 'EOF'

# Submission port (587) - for authenticated mail submission
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
    fi
    print_info "✓ Submission service added"
fi
echo

# 2. Verify submission service is not commented
print_info "2. Verifying submission service is active..."
if grep -q "^submission.*smtpd$" /etc/postfix/master.cf; then
    print_info "✓ Submission service is active (not commented)"
else
    print_warn "Submission service might be commented - checking..."
    grep "^submission" /etc/postfix/master.cf
fi
echo

# 3. Ensure SASL is configured in main.cf
print_info "3. Ensuring SASL is configured..."
if ! grep -q "smtpd_sasl_auth_enable = yes" /etc/postfix/main.cf; then
    print_info "Adding SASL configuration to main.cf..."
    cat >> /etc/postfix/main.cf << 'EOF'

# SASL Authentication
smtpd_sasl_type = cyrus
smtpd_sasl_auth_enable = yes
smtpd_sasl_security_options = noanonymous
smtpd_sasl_local_domain = $myhostname
broken_sasl_auth_clients = yes
EOF
    print_info "✓ SASL configuration added"
else
    print_info "✓ SASL already configured"
fi
echo

# 4. Ensure SASL config files exist
print_info "4. Ensuring SASL config files exist..."
mkdir -p /usr/lib/sasl2 /etc/sasl2 /etc/postfix/sasl

cat > /etc/postfix/sasl/smtpd.conf << 'EOF'
pwcheck_method: auxprop
auxprop_plugin: sasldb
mech_list: PLAIN LOGIN
sasldb_path: /etc/postfix/sasl/sasldb2
EOF

cp /etc/postfix/sasl/smtpd.conf /usr/lib/sasl2/smtpd.conf 2>/dev/null || true
cp /etc/postfix/sasl/smtpd.conf /etc/sasl2/smtpd.conf 2>/dev/null || true

print_info "✓ SASL config files created"
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
sleep 3
if systemctl is-active --quiet postfix; then
    print_info "✓ Postfix restarted"
else
    print_error "✗ Postfix failed to start!"
    systemctl status postfix
    exit 1
fi
echo

# 7. Check if port 587 is listening
print_info "7. Checking if port 587 is listening..."
sleep 2
if netstat -tlnp 2>/dev/null | grep ":587 " || ss -tlnp 2>/dev/null | grep ":587 "; then
    print_info "✓ Port 587 is listening!"
    netstat -tlnp 2>/dev/null | grep ":587 " || ss -tlnp 2>/dev/null | grep ":587 "
else
    print_error "✗ Port 587 is NOT listening!"
    print_info "Checking Postfix logs..."
    tail -20 /var/log/mail.log | grep -i "submission\|587\|error" || true
    print_info "Checking master.cf submission service..."
    grep -A 5 "^submission" /etc/postfix/master.cf
fi
echo

# 8. Test connection
print_info "8. Testing connection to port 587..."
if timeout 3 telnet localhost 587 </dev/null 2>&1 | grep -q "Connected\|220"; then
    print_info "✓ Can connect to port 587"
else
    print_warn "Cannot connect to port 587"
    print_info "Trying to see what's listening on port 587..."
    lsof -i :587 2>/dev/null || netstat -tlnp 2>/dev/null | grep 587 || ss -tlnp 2>/dev/null | grep 587 || print_warn "Nothing listening on 587"
fi
echo

print_info "=== Setup Complete ==="
print_info "If port 587 is still not listening, check:"
print_info "  1. Postfix logs: tail -f /var/log/mail.log"
print_info "  2. master.cf: grep -A 10 '^submission' /etc/postfix/master.cf"
print_info "  3. Postfix status: systemctl status postfix"

