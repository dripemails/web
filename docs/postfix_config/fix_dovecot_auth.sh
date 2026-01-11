#!/bin/bash

# Fix Dovecot authentication permissions for Postfix
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

print_status "Fixing Dovecot authentication permissions..."

# Step 1: Check if Dovecot is installed
print_status "Step 1: Checking Dovecot installation..."
if ! command -v dovecot > /dev/null 2>&1; then
    print_warning "Dovecot is not installed. Installing..."
    apt update
    apt install dovecot-core dovecot-imapd dovecot-pop3d -y
    print_success "Dovecot installed"
else
    print_success "Dovecot is installed"
fi

# Step 2: Stop Dovecot
print_status "Step 2: Stopping Dovecot..."
systemctl stop dovecot 2>/dev/null || true
sleep 2
print_success "Dovecot stopped"

# Step 3: Fix permissions for Dovecot runtime directory
print_status "Step 3: Fixing Dovecot runtime permissions..."
mkdir -p /run/dovecot
chown -R dovecot:dovecot /run/dovecot
chmod 755 /run/dovecot
print_success "Runtime permissions fixed"

# Step 4: Create Dovecot configuration for SASL
print_status "Step 4: Creating Dovecot SASL configuration..."
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
  # auth_socket_path points to this userdb socket by default. It's typically
  # used by dovecot-lda, imap, pop3 and lmtp processes.
  unix_listener auth-userdb {
    mode = 0666
    user = postfix
    group = postfix
  }

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
print_success "Dovecot master configuration created"

# Step 5: Configure Dovecot for SASL authentication
print_status "Step 5: Configuring Dovecot for SASL..."
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
print_success "Dovecot auth configuration created"

# Step 6: Configure Dovecot SSL
print_status "Step 6: Configuring Dovecot SSL..."
cat > /etc/dovecot/conf.d/10-ssl.conf << 'EOF'
# Dovecot SSL configuration
ssl = yes
ssl_cert = </etc/letsencrypt/live/dripemails.org/fullchain.pem
ssl_key = </etc/letsencrypt/live/dripemails.org/privkey.pem
ssl_protocols = !SSLv2 !SSLv3 !TLSv1 !TLSv1.1
ssl_cipher_list = ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384
ssl_prefer_server_ciphers = yes
ssl_dh_parameters_length = 2048
EOF
print_success "Dovecot SSL configuration created"

# Step 7: Configure Dovecot mail location
print_status "Step 7: Configuring Dovecot mail location..."
cat > /etc/dovecot/conf.d/10-mail.conf << 'EOF'
# Dovecot mail configuration
mail_location = maildir:~/Maildir
mail_privileged_group = mail
mail_access_groups = mail
EOF
print_success "Dovecot mail configuration created"

# Step 8: Create auth directory for Postfix
print_status "Step 8: Creating auth directory for Postfix..."
mkdir -p /var/spool/postfix/private
chown postfix:postfix /var/spool/postfix/private
chmod 755 /var/spool/postfix/private
print_success "Auth directory created"

# Step 9: Start Dovecot
print_status "Step 9: Starting Dovecot..."
systemctl start dovecot
sleep 3
print_success "Dovecot started"

# Step 10: Check Dovecot status
print_status "Step 10: Checking Dovecot status..."
if systemctl is-active --quiet dovecot; then
    print_success "Dovecot is running successfully"
else
    print_error "Dovecot failed to start"
    systemctl status dovecot --no-pager -l
    exit 1
fi

# Step 11: Test SASL authentication
print_status "Step 11: Testing SASL authentication..."
if [ -S "/var/spool/postfix/private/auth" ]; then
    print_success "SASL socket exists"
else
    print_warning "SASL socket not found"
fi

# Step 12: Check Dovecot logs
print_status "Step 12: Checking Dovecot logs..."
if journalctl -u dovecot --no-pager -n 10 | grep -q "error\|Error"; then
    print_warning "Found errors in Dovecot logs:"
    journalctl -u dovecot --no-pager -n 10
else
    print_success "No errors found in Dovecot logs"
fi

print_success "Dovecot authentication fix completed!"
print_status "Summary:"
print_status "1. Dovecot installed and configured"
print_status "2. SASL authentication configured"
print_status "3. SSL certificates configured"
print_status "4. Permissions fixed for Postfix integration"
print_status "5. Dovecot is running successfully"
print_status ""
print_status "Postfix should now be able to authenticate users via Dovecot!" 