#!/bin/bash

# Fix Dovecot configuration issues
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

print_status "Fixing Dovecot configuration issues..."

# Step 1: Stop Dovecot
print_status "Step 1: Stopping Dovecot..."
systemctl stop dovecot 2>/dev/null || true
sleep 2
print_success "Dovecot stopped"

# Step 2: Backup existing configuration
print_status "Step 2: Backing up existing configuration..."
cp -r /etc/dovecot /etc/dovecot.backup.$(date +%Y%m%d_%H%M%S)
print_success "Configuration backed up"

# Step 3: Remove problematic configuration files
print_status "Step 3: Removing problematic configuration files..."
rm -f /etc/dovecot/conf.d/10-master.conf
rm -f /etc/dovecot/conf.d/10-auth.conf
rm -f /etc/dovecot/conf.d/10-ssl.conf
rm -f /etc/dovecot/conf.d/10-mail.conf
print_success "Problematic config files removed"

# Step 4: Create clean master configuration
print_status "Step 4: Creating clean master configuration..."
cat > /etc/dovecot/conf.d/10-master.conf << 'EOF'
# Dovecot master configuration for SASL
service master {
  # Give the master userdb write access to the db to set quota
  unix_listener auth-userdb {
    mode = 0600
    user = postfix
    group = postfix
  }

  # Auth process is run as this user.
  user = $default_internal_user
}

service auth {
  # Postfix smtp-auth
  unix_listener /var/spool/postfix/private/auth {
    mode = 0666
    user = postfix
    group = postfix
  }
}

service auth-worker {
  # Auth worker process is run as root by default, so that it can access
  # /etc/shadow. If this isn't necessary, the user could be changed to
  # $default_internal_user.
  user = $default_internal_user
}
EOF
print_success "Clean master configuration created"

# Step 5: Create clean auth configuration
print_status "Step 5: Creating clean auth configuration..."
cat > /etc/dovecot/conf.d/10-auth.conf << 'EOF'
# Dovecot authentication configuration
disable_plaintext_auth = no
auth_mechanisms = plain login

# Password database
passdb {
  driver = pam
}

# User database
userdb {
  driver = passwd
}
EOF
print_success "Clean auth configuration created"

# Step 6: Create modern SSL configuration
print_status "Step 6: Creating modern SSL configuration..."
cat > /etc/dovecot/conf.d/10-ssl.conf << 'EOF'
# Dovecot SSL configuration
ssl = yes
ssl_cert = </etc/letsencrypt/live/dripemails.org/fullchain.pem
ssl_key = </etc/letsencrypt/live/dripemails.org/privkey.pem
ssl_min_protocol = TLSv1.2
ssl_cipher_list = ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384
ssl_prefer_server_ciphers = yes
EOF
print_success "Modern SSL configuration created"

# Step 7: Create mail configuration
print_status "Step 7: Creating mail configuration..."
cat > /etc/dovecot/conf.d/10-mail.conf << 'EOF'
# Dovecot mail configuration
mail_location = maildir:~/Maildir
mail_privileged_group = mail
mail_access_groups = mail
EOF
print_success "Mail configuration created"

# Step 8: Create auth directory for Postfix
print_status "Step 8: Creating auth directory for Postfix..."
mkdir -p /var/spool/postfix/private
chown postfix:postfix /var/spool/postfix/private
chmod 755 /var/spool/postfix/private
print_success "Auth directory created"

# Step 9: Fix runtime permissions
print_status "Step 9: Fixing runtime permissions..."
mkdir -p /run/dovecot
chown -R dovecot:dovecot /run/dovecot
chmod 755 /run/dovecot
print_success "Runtime permissions fixed"

# Step 10: Test configuration
print_status "Step 10: Testing Dovecot configuration..."
if doveconf -n > /dev/null 2>&1; then
    print_success "Dovecot configuration is valid"
else
    print_error "Dovecot configuration has errors"
    doveconf -n
    exit 1
fi

# Step 11: Start Dovecot
print_status "Step 11: Starting Dovecot..."
systemctl start dovecot
sleep 3
print_success "Dovecot started"

# Step 12: Check Dovecot status
print_status "Step 12: Checking Dovecot status..."
if systemctl is-active --quiet dovecot; then
    print_success "Dovecot is running successfully"
else
    print_error "Dovecot failed to start"
    systemctl status dovecot --no-pager -l
    exit 1
fi

# Step 13: Test SASL authentication
print_status "Step 13: Testing SASL authentication..."
if [ -S "/var/spool/postfix/private/auth" ]; then
    print_success "SASL socket exists"
else
    print_warning "SASL socket not found"
fi

# Step 14: Check Dovecot logs
print_status "Step 14: Checking Dovecot logs..."
if journalctl -u dovecot --no-pager -n 10 | grep -q "error\|Error"; then
    print_warning "Found errors in Dovecot logs:"
    journalctl -u dovecot --no-pager -n 10
else
    print_success "No errors found in Dovecot logs"
fi

print_success "Dovecot configuration fix completed!"
print_status "Summary:"
print_status "1. Removed duplicate listeners"
print_status "2. Updated SSL configuration to modern standards"
print_status "3. Fixed configuration conflicts"
print_status "4. Dovecot is running successfully"
print_status "5. SASL authentication should work with Postfix"
print_status ""
print_status "Postfix should now be able to authenticate users via Dovecot!" 