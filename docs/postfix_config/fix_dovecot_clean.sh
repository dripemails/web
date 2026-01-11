#!/bin/bash

# Completely clean up Dovecot configuration and start fresh
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

print_status "Completely cleaning up Dovecot configuration..."

# Step 1: Stop Dovecot
print_status "Step 1: Stopping Dovecot..."
systemctl stop dovecot 2>/dev/null || true
sleep 2
print_success "Dovecot stopped"

# Step 2: Backup existing configuration
print_status "Step 2: Backing up existing configuration..."
cp -r /etc/dovecot /etc/dovecot.backup.$(date +%Y%m%d_%H%M%S)
print_success "Configuration backed up"

# Step 3: Remove ALL configuration files
print_status "Step 3: Removing ALL configuration files..."
rm -rf /etc/dovecot/conf.d/*
print_success "All config files removed"

# Step 4: Create minimal main configuration
print_status "Step 4: Creating minimal main configuration..."
cat > /etc/dovecot/dovecot.conf << 'EOF'
# Dovecot main configuration
protocols = imap pop3

# SSL configuration
ssl = yes
ssl_cert = </etc/letsencrypt/live/dripemails.org/fullchain.pem
ssl_key = </etc/letsencrypt/live/dripemails.org/privkey.pem
ssl_min_protocol = TLSv1.2
ssl_cipher_list = ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384
ssl_prefer_server_ciphers = yes

# Authentication
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

# Mail location
mail_location = maildir:~/Maildir
mail_privileged_group = mail
mail_access_groups = mail

# Services
service master {
  unix_listener auth-userdb {
    mode = 0600
    user = postfix
    group = postfix
  }
  user = $default_internal_user
}

service auth {
  unix_listener /var/spool/postfix/private/auth {
    mode = 0666
    user = postfix
    group = postfix
  }
}

service auth-worker {
  user = $default_internal_user
}

# Namespace
namespace inbox {
  location =
  prefix =
  mailbox Drafts {
    special_use = \Drafts
  }
  mailbox Junk {
    special_use = \Junk
  }
  mailbox Sent {
    special_use = \Sent
  }
  mailbox "Sent Messages" {
    special_use = \Sent
  }
  mailbox Trash {
    special_use = \Trash
  }
}
EOF
print_success "Minimal main configuration created"

# Step 5: Create auth directory for Postfix
print_status "Step 5: Creating auth directory for Postfix..."
mkdir -p /var/spool/postfix/private
chown postfix:postfix /var/spool/postfix/private
chmod 755 /var/spool/postfix/private
print_success "Auth directory created"

# Step 6: Fix runtime permissions
print_status "Step 6: Fixing runtime permissions..."
mkdir -p /run/dovecot
chown -R dovecot:dovecot /run/dovecot
chmod 755 /run/dovecot
print_success "Runtime permissions fixed"

# Step 7: Test configuration
print_status "Step 7: Testing Dovecot configuration..."
if doveconf -n > /dev/null 2>&1; then
    print_success "Dovecot configuration is valid"
else
    print_error "Dovecot configuration has errors"
    doveconf -n
    exit 1
fi

# Step 8: Start Dovecot
print_status "Step 8: Starting Dovecot..."
systemctl start dovecot
sleep 3
print_success "Dovecot started"

# Step 9: Check Dovecot status
print_status "Step 9: Checking Dovecot status..."
if systemctl is-active --quiet dovecot; then
    print_success "Dovecot is running successfully"
else
    print_error "Dovecot failed to start"
    systemctl status dovecot --no-pager -l
    exit 1
fi

# Step 10: Test SASL authentication
print_status "Step 10: Testing SASL authentication..."
if [ -S "/var/spool/postfix/private/auth" ]; then
    print_success "SASL socket exists"
else
    print_warning "SASL socket not found"
fi

# Step 11: Check Dovecot logs
print_status "Step 11: Checking Dovecot logs..."
if journalctl -u dovecot --no-pager -n 10 | grep -q "error\|Error"; then
    print_warning "Found errors in Dovecot logs:"
    journalctl -u dovecot --no-pager -n 10
else
    print_success "No errors found in Dovecot logs"
fi

print_success "Dovecot clean configuration completed!"
print_status "Summary:"
print_status "1. Removed ALL existing configuration files"
print_status "2. Created minimal, clean configuration"
print_status "3. No duplicate listeners"
print_status "4. Dovecot is running successfully"
print_status "5. SASL authentication should work with Postfix"
print_status ""
print_status "Postfix should now be able to authenticate users via Dovecot!" 