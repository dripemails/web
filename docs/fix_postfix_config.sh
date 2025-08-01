#!/bin/sh

# Postfix Configuration Fix Script
# This script fixes common Postfix configuration issues with simple authentication

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

print_status "Fixing Postfix configuration issues..."

# Check if Postfix is properly installed
print_status "Checking Postfix installation..."
if ! command -v postfix > /dev/null 2>&1; then
    print_error "Postfix is not installed. Installing now..."
    apt update
    apt install -y postfix
elif [ ! -f "/usr/lib/postfix/postfix-script" ]; then
    print_warning "Postfix script is missing. Reinstalling Postfix..."
    apt update
    apt install -y --reinstall postfix
fi

# Verify Postfix installation
if [ ! -f "/usr/lib/postfix/postfix-script" ]; then
    print_error "Postfix installation is still incomplete. Please check your system."
    exit 1
fi

print_success "Postfix installation verified"

# Backup current configuration
BACKUP_FILE="/etc/postfix/main.cf.backup.$(date +%Y%m%d_%H%M%S)"
cp /etc/postfix/main.cf "$BACKUP_FILE"
print_success "Configuration backed up to $BACKUP_FILE"

# Install basic SASL packages
print_status "Installing SASL packages..."
apt update
apt install -y libsasl2-2 libsasl2-modules

# Create a clean main.cf configuration
print_status "Creating clean Postfix configuration..."
cat > /etc/postfix/main.cf << 'EOF'
# Basic Postfix Configuration
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

# Basic SASL Authentication (simple setup)
smtpd_sasl_auth_enable = yes
smtpd_sasl_security_options = noanonymous
smtpd_sasl_local_domain = $myhostname
broken_sasl_auth_clients = yes

# Relay restrictions (simplified)
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

# TLS settings (will be updated by SSL script)
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

# Performance settings
smtpd_tls_session_cache_timeout = 3600s
smtpd_tls_session_cache_database = btree:${data_directory}/smtpd_scache
EOF

# Stop saslauthd if it's running
print_status "Stopping saslauthd service..."
systemctl stop saslauthd 2>/dev/null || true
systemctl disable saslauthd 2>/dev/null || true

# Test configuration
print_status "Testing Postfix configuration..."
if postfix check; then
    print_success "Postfix configuration is valid"
else
    print_error "Postfix configuration has errors"
    print_status "Checking Postfix status:"
    systemctl status postfix --no-pager -l
    exit 1
fi

# Reload Postfix
print_status "Reloading Postfix..."
systemctl reload postfix

# Check Postfix status
print_status "Checking Postfix status..."
if systemctl is-active --quiet postfix; then
    print_success "Postfix is running successfully"
else
    print_error "Postfix failed to start"
    systemctl status postfix --no-pager -l
    exit 1
fi

print_success "Postfix configuration has been fixed!"
print_status "Simplified authentication setup (no saslauthd dependency)"
print_status "You can now run the SSL certificate installation script"
print_status "Run: sudo bash install_postfix_ssl.sh dripemails.org"
print_status ""
print_status "Note: For SMTP authentication, you'll need to create users manually:"
print_status "sudo bash add_smtp_user.sh founders" 