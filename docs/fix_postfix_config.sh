#!/bin/sh

# Postfix Configuration Fix Script
# This script fixes common Postfix configuration issues and removes Dovecot dependency

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

# Backup current configuration
BACKUP_FILE="/etc/postfix/main.cf.backup.$(date +%Y%m%d_%H%M%S)"
cp /etc/postfix/main.cf "$BACKUP_FILE"
print_success "Configuration backed up to $BACKUP_FILE"

# Install SASL authentication packages
print_status "Installing SASL authentication packages..."
apt update
apt install -y libsasl2-2 libsasl2-modules sasl2-bin

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

# SASL Authentication (without Dovecot)
smtpd_sasl_auth_enable = yes
smtpd_sasl_security_options = noanonymous
smtpd_sasl_local_domain = $myhostname
broken_sasl_auth_clients = yes
smtpd_sasl_type = cyrus

# Relay restrictions
smtpd_relay_restrictions = 
    permit_mynetworks,
    permit_sasl_authenticated,
    reject_unauth_destination

smtpd_recipient_restrictions = 
    permit_mynetworks,
    permit_sasl_authenticated,
    reject_unauth_destination,
    reject_invalid_hostname,
    reject_non_fqdn_hostname,
    reject_non_fqdn_sender,
    reject_non_fqdn_recipient,
    reject_unknown_sender_domain,
    reject_unknown_recipient_domain

# Client restrictions
smtpd_client_restrictions = 
    permit_mynetworks,
    permit_sasl_authenticated,
    reject_unknown_client_hostname

# Helo restrictions
smtpd_helo_required = yes
smtpd_helo_restrictions = 
    permit_mynetworks,
    permit_sasl_authenticated,
    reject_invalid_helo_hostname,
    reject_non_fqdn_helo_hostname

# Sender restrictions
smtpd_sender_restrictions = 
    permit_mynetworks,
    permit_sasl_authenticated,
    reject_non_fqdn_sender,
    reject_unknown_sender_domain

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

# Configure SASL
print_status "Configuring SASL authentication..."
cat > /etc/postfix/sasl/smtpd.conf << 'EOF'
pwcheck_method: saslauthd
mech_list: PLAIN LOGIN
EOF

# Create SASL authentication directory
mkdir -p /etc/postfix/sasl

# Configure saslauthd
print_status "Configuring saslauthd..."
cat > /etc/default/saslauthd << 'EOF'
START=yes
DESC="SASL Authentication Daemon"
MECHANISMS="pam"
OPTIONS="-c -m /var/spool/postfix/var/run/saslauthd"
EOF

# Create saslauthd directory for Postfix
mkdir -p /var/spool/postfix/var/run/saslauthd
chown postfix:sasl /var/spool/postfix/var/run/saslauthd
chmod 710 /var/spool/postfix/var/run/saslauthd

# Restart saslauthd
print_status "Restarting saslauthd..."
systemctl restart saslauthd
systemctl enable saslauthd

# Test configuration
print_status "Testing Postfix configuration..."
if postfix check; then
    print_success "Postfix configuration is valid"
else
    print_error "Postfix configuration has errors"
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
    systemctl status postfix
    exit 1
fi

print_success "Postfix configuration has been fixed!"
print_status "Dovecot dependency has been removed"
print_status "SASL authentication is now configured with saslauthd"
print_status "You can now run the SSL certificate installation script"
print_status "Run: sudo bash install_postfix_ssl.sh dripemails.org" 