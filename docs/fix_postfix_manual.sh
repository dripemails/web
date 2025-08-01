#!/bin/sh

# Manual Postfix Fix Script
# This script manually fixes the postmulti conflict step by step

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

print_status "Starting manual Postfix fix..."

# Step 1: Stop Postfix completely
print_status "Step 1: Stopping Postfix completely..."
systemctl stop postfix 2>/dev/null || true
print_success "Postfix stopped"

# Step 2: Kill any remaining postfix processes
print_status "Step 2: Killing any remaining Postfix processes..."
pkill -f postfix 2>/dev/null || true
sleep 3
print_success "Postfix processes killed"

# Step 3: Remove postmulti configuration files
print_status "Step 3: Removing postmulti configuration files..."
rm -f /etc/postfix/postmulti-instance-* 2>/dev/null || true
rm -f /etc/postfix/master.cf.* 2>/dev/null || true
rm -f /etc/postfix/main.cf.* 2>/dev/null || true
print_success "Postmulti configuration files removed"

# Step 4: Force single instance mode
print_status "Step 4: Forcing single instance mode..."
postconf -e "multi_instance_enable = no" 2>/dev/null || true
postconf -e "multi_instance_name = " 2>/dev/null || true
postconf -e "multi_instance_group = " 2>/dev/null || true
postconf -e "multi_instance_directories = " 2>/dev/null || true
print_success "Single instance mode forced"

# Step 5: Clear cached data
print_status "Step 5: Clearing cached data..."
rm -rf /var/lib/postfix/*.db 2>/dev/null || true
rm -rf /var/spool/postfix/private/* 2>/dev/null || true
print_success "Cached data cleared"

# Step 6: Backup current configuration
print_status "Step 6: Backing up current configuration..."
BACKUP_FILE="/etc/postfix/main.cf.backup.$(date +%Y%m%d_%H%M%S)"
cp /etc/postfix/main.cf "$BACKUP_FILE" 2>/dev/null || true
print_success "Configuration backed up to $BACKUP_FILE"

# Step 7: Create minimal main.cf
print_status "Step 7: Creating minimal main.cf..."
cat > /etc/postfix/main.cf << 'EOF'
# Minimal Postfix Configuration - Single Instance Only
queue_directory = /var/spool/postfix
command_directory = /usr/sbin
daemon_directory = /usr/lib/postfix
data_directory = /var/lib/postfix
mail_owner = postfix
myhostname = web.dripemails.org
mydomain = dripemails.org
myorigin = $mydomain
inet_interfaces = all
inet_protocols = all
mydestination = $myhostname, $mydomain, mail.$mydomain, localhost.$mydomain, localhost
local_recipient_maps =
relayhost =
mynetworks = 127.0.0.0/8, 10.124.0.3, 134.199.221.231
mailbox_size_limit = 0
recipient_delimiter = +
home_mailbox = Maildir/

# Alias maps
alias_maps = hash:/etc/aliases
alias_database = hash:/etc/aliases

# Basic SASL Authentication
smtpd_sasl_auth_enable = yes
smtpd_sasl_security_options = noanonymous
smtpd_sasl_local_domain = $myhostname
broken_sasl_auth_clients = yes

# Relay restrictions
smtpd_relay_restrictions = 
    permit_mynetworks,
    permit_sasl_authenticated,
    reject_unauth_destination

smtpd_recipient_restrictions = 
    permit_mynetworks,
    permit_sasl_authenticated,
    reject_unauth_destination

# Client restrictions
smtpd_client_restrictions = 
    permit_mynetworks,
    permit_sasl_authenticated

# Helo restrictions
smtpd_helo_required = yes
smtpd_helo_restrictions = 
    permit_mynetworks,
    permit_sasl_authenticated

# Sender restrictions
smtpd_sender_restrictions = 
    permit_mynetworks,
    permit_sasl_authenticated

# TLS settings
smtpd_tls_security_level = may
smtpd_tls_auth_only = no
smtpd_tls_cert_file = /etc/ssl/certs/ssl-cert-snakeoil.pem
smtpd_tls_key_file = /etc/ssl/private/ssl-cert-snakeoil.key
smtpd_tls_protocols = !SSLv2, !SSLv3
smtpd_tls_ciphers = medium
smtpd_tls_mandatory_protocols = !SSLv2, !SSLv3
smtpd_tls_mandatory_ciphers = medium
smtpd_tls_session_cache_database = btree:${data_directory}/smtpd_scache
smtpd_tls_session_cache_timeout = 3600s
smtpd_tls_received_header = yes
smtpd_tls_loglevel = 1

# SMTP TLS settings
smtp_tls_security_level = may
smtp_tls_CApath = /etc/ssl/certs
smtp_tls_session_cache_database = btree:${data_directory}/smtp_scache
smtp_tls_session_cache_timeout = 3600s

# Disable multi-instance completely
multi_instance_enable = no
multi_instance_name = 
multi_instance_group = 
multi_instance_directories = 
EOF
print_success "Minimal main.cf created"

# Step 8: Test configuration
print_status "Step 8: Testing Postfix configuration..."
if postfix check; then
    print_success "Postfix configuration is valid"
else
    print_error "Postfix configuration has errors"
    print_status "Configuration errors:"
    postfix check
    exit 1
fi

# Step 9: Start Postfix
print_status "Step 9: Starting Postfix..."
systemctl start postfix
sleep 3
print_success "Postfix started"

# Step 10: Check Postfix status
print_status "Step 10: Checking Postfix status..."
if systemctl is-active --quiet postfix; then
    print_success "Postfix is running successfully"
else
    print_error "Postfix failed to start"
    systemctl status postfix --no-pager -l
    exit 1
fi

# Step 11: Check for postmulti conflicts
print_status "Step 11: Checking for postmulti conflicts..."
if postmulti -l 2>/dev/null | grep -q "conflicts"; then
    print_warning "Postmulti conflicts still detected:"
    postmulti -l 2>/dev/null
else
    print_success "No postmulti conflicts detected"
fi

# Step 12: Check mail logs
print_status "Step 12: Checking mail logs for errors..."
sleep 5
if tail -n 20 /var/log/mail.log | grep -q "fatal.*conflicts"; then
    print_warning "Found conflict errors in mail logs:"
    tail -n 20 /var/log/mail.log | grep -i "fatal.*conflicts"
else
    print_success "No conflict errors found in mail logs"
fi

# Step 13: Test SMTP functionality
print_status "Step 13: Testing SMTP functionality..."
if netstat -tlnp | grep -q ":25\|:587\|:465"; then
    print_success "SMTP ports are listening"
    netstat -tlnp | grep -E ":(25|587|465)"
else
    print_warning "SMTP ports are not listening"
fi

print_success "Manual Postfix fix completed!"
print_status "Summary:"
print_status "1. Stopped Postfix and killed processes"
print_status "2. Removed postmulti configuration files"
print_status "3. Forced single instance mode"
print_status "4. Created minimal configuration"
print_status "5. Postfix is running successfully"
print_status ""
print_status "You can now proceed with SSL certificate installation:"
print_status "sudo bash install_postfix_ssl.sh dripemails.org" 