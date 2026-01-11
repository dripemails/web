#!/bin/bash
#
# Complete SASL Fix Script
# Fixes all SASL configuration issues
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

print_info "=== Complete SASL Fix ==="
echo

# 1. Fix smtpd_sasl_path in main.cf
print_info "1. Fixing smtpd_sasl_path in main.cf..."
BACKUP_FILE="/etc/postfix/main.cf.backup.$(date +%Y%m%d_%H%M%S)"
cp /etc/postfix/main.cf "$BACKUP_FILE"
print_info "Backup created: $BACKUP_FILE"

# Remove any incorrect smtpd_sasl_path lines
sed -i '/^smtpd_sasl_path = /d' /etc/postfix/main.cf

# For cyrus SASL, we can try two approaches:
# 1. Use smtpd_sasl_path = smtpd (service name)
# 2. Or omit it and let SASL use defaults
# Let's try omitting it first (cyrus SASL will look for smtpd.conf automatically)
# If that doesn't work, we'll add it back

print_info "✓ Removed smtpd_sasl_path (cyrus SASL will auto-detect from smtpd.conf)"
print_info "If this doesn't work, we'll add 'smtpd_sasl_path = smtpd' back"
echo

# 2. Create SASL config in ALL standard locations
print_info "2. Creating SASL config in standard locations..."

# Create standard SASL directories
mkdir -p /usr/lib/sasl2
mkdir -p /etc/sasl2
mkdir -p /etc/postfix/sasl

# Create the SASL config file with correct content
cat > /etc/postfix/sasl/smtpd.conf << 'EOF'
pwcheck_method: auxprop
auxprop_plugin: sasldb
mech_list: PLAIN LOGIN
sasldb_path: /etc/postfix/sasl/sasldb2
EOF

# Copy to all standard locations
cp /etc/postfix/sasl/smtpd.conf /usr/lib/sasl2/smtpd.conf
cp /etc/postfix/sasl/smtpd.conf /etc/sasl2/smtpd.conf

# Also try creating a symlink
ln -sf /etc/postfix/sasl/smtpd.conf /usr/lib/sasl2/smtpd.conf 2>/dev/null || true
ln -sf /etc/postfix/sasl/smtpd.conf /etc/sasl2/smtpd.conf 2>/dev/null || true

print_info "✓ Created SASL config in:"
print_info "  - /etc/postfix/sasl/smtpd.conf"
print_info "  - /usr/lib/sasl2/smtpd.conf"
print_info "  - /etc/sasl2/smtpd.conf"

# Verify files exist
for file in /etc/postfix/sasl/smtpd.conf /usr/lib/sasl2/smtpd.conf /etc/sasl2/smtpd.conf; do
    if [ -f "$file" ]; then
        print_info "  ✓ $file exists"
    else
        print_warn "  ✗ $file missing"
    fi
done
echo

# 3. Verify SASL database exists and has users
print_info "3. Verifying SASL database..."
SASLDB_PATH="/etc/postfix/sasl/sasldb2"
if [ -f "$SASLDB_PATH" ]; then
    print_info "✓ SASL database exists"
    print_info "Current users:"
    sasldblistusers2 -f "$SASLDB_PATH"
    chmod 600 "$SASLDB_PATH"
    chown postfix:postfix "$SASLDB_PATH"
else
    print_warn "SASL database doesn't exist - you may need to create a user"
fi
echo

# 4. Verify main.cf SASL settings
print_info "4. Verifying main.cf SASL settings:"
grep -E "^smtpd_sasl" /etc/postfix/main.cf || print_warn "No smtpd_sasl settings found"
echo

# 5. Test Postfix configuration
print_info "5. Testing Postfix configuration..."
if postfix check; then
    print_info "✓ Postfix configuration is valid"
else
    print_error "✗ Postfix configuration has errors!"
    print_warn "Restoring backup..."
    cp "$BACKUP_FILE" /etc/postfix/main.cf
    exit 1
fi
echo

# 6. Restart Postfix
print_info "6. Restarting Postfix..."
systemctl restart postfix
sleep 3
if systemctl is-active --quiet postfix; then
    print_info "✓ Postfix restarted successfully"
else
    print_error "✗ Postfix failed to start!"
    systemctl status postfix
    exit 1
fi
echo

# 7. Test if AUTH is advertised
print_info "7. Testing if SMTP AUTH is advertised..."
sleep 2
if echo "EHLO localhost" | timeout 5 telnet localhost 25 2>/dev/null | grep -q "AUTH"; then
    print_info "✓ SMTP AUTH is advertised"
    echo "EHLO localhost" | timeout 5 telnet localhost 25 2>/dev/null | grep "AUTH"
else
    print_warn "SMTP AUTH might not be advertised yet"
    print_info "Trying with explicit smtpd_sasl_path..."
    # Add smtpd_sasl_path if AUTH not advertised
    if ! grep -q "^smtpd_sasl_path" /etc/postfix/main.cf; then
        sed -i '/^smtpd_sasl_type/a smtpd_sasl_path = smtpd' /etc/postfix/main.cf
        print_info "Added smtpd_sasl_path = smtpd"
        systemctl restart postfix
        sleep 2
        if echo "EHLO localhost" | timeout 5 telnet localhost 25 2>/dev/null | grep -q "AUTH"; then
            print_info "✓ SMTP AUTH is now advertised with explicit path"
        fi
    fi
fi
echo

# 8. Final authentication test
print_info "8. Testing authentication..."
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
print("Check Postfix logs: tail -f /var/log/mail.log")
sys.exit(1)
EOF

AUTH_RESULT=$?

echo
if [ $AUTH_RESULT -eq 0 ]; then
    print_info "=== SUCCESS! SASL Authentication is working ==="
else
    print_error "=== Authentication still failing ==="
    print_info "Next steps:"
    print_info "1. Check Postfix logs: tail -f /var/log/mail.log"
    print_info "2. Verify user exists: sasldblistusers2 -f /etc/postfix/sasl/sasldb2"
    print_info "3. Try recreating user: sudo saslpasswd2 -f /etc/postfix/sasl/sasldb2 -u dripemails.org founders"
fi

