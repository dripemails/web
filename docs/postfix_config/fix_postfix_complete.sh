#!/bin/sh

# Complete Postfix Fix Script
# This script completely fixes Postfix configuration and postmulti conflicts

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

print_status "Starting complete Postfix fix..."

# Stop Postfix completely
print_status "Stopping Postfix..."
systemctl stop postfix
systemctl stop postfix@- 2>/dev/null || true

# Kill any remaining postfix processes
print_status "Killing any remaining Postfix processes..."
pkill -f postfix || true
sleep 2

# Completely disable postmulti
print_status "Disabling postmulti completely..."
postmulti -d 2>/dev/null || true
postmulti -e destroy 2>/dev/null || true

# Remove all postmulti configurations
print_status "Removing postmulti configurations..."
rm -rf /etc/postfix/master.cf.* 2>/dev/null || true
rm -rf /etc/postfix/main.cf.* 2>/dev/null || true
rm -rf /etc/postfix/postmulti-instance-* 2>/dev/null || true

# Force single instance mode
print_status "Forcing single instance mode..."
postconf -e "multi_instance_enable = no"
postconf -e "multi_instance_name = "
postconf -e "multi_instance_group = "
postconf -e "multi_instance_directories = "

# Backup current configuration
BACKUP_FILE="/etc/postfix/main.cf.backup.$(date +%Y%m%d_%H%M%S)"
cp /etc/postfix/main.cf "$BACKUP_FILE"
print_success "Configuration backed up to $BACKUP_FILE"

# Create completely clean main.cf
print_status "Creating clean main.cf configuration..."
cat > /etc/postfix/main.cf << 'EOF'
# Basic Postfix Configuration - Single Instance
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

# TLS settings (single entries only)
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

# Disable postmulti completely
multi_instance_enable = no
multi_instance_name = 
multi_instance_group = 
multi_instance_directories = 
EOF

# Create clean master.cf
print_status "Creating clean master.cf..."
cat > /etc/postfix/master.cf << 'EOF'
#
# Postfix master process configuration file.  For details on the format
# of the file, see the master(5) manual page (command: "man 5 master" or
# on-line: http://www.postfix.org/master.5.html).
#
# Do not forget to execute "postfix reload" after editing this file.
#
# ==========================================================================
# service type  private unpriv  chroot  wakeup  maxproc command + args
#               (yes)   (yes)   (no)    (never) (100)
# ==========================================================================
smtp      inet  n       -       y       -       -       smtpd
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
smtps     inet  n       -       y       -       -       smtpd
  -o syslog_name=postfix/smtps
  -o smtpd_tls_wrappermode=yes
  -o smtpd_sasl_auth_enable=yes
  -o smtpd_reject_unlisted_recipient=no
  -o smtpd_client_restrictions=$mua_client_restrictions
  -o smtpd_helo_restrictions=$mua_helo_restrictions
  -o smtpd_sender_restrictions=$mua_sender_restrictions
  -o smtpd_recipient_restrictions=
  -o smtpd_relay_restrictions=permit_sasl_authenticated,reject
  -o milter_macro_daemon_name=ORIGINATING
pickup    unix  n       -       y       60      1       pickup
cleanup   unix  n       -       y       -       0       cleanup
qmgr      unix  n       -       n       300     1       qmgr
tlsmgr    unix  -       -       y       1000?   1       tlsmgr
rewrite   unix  -       -       y       -       -       trivial-rewrite
bounce    unix  -       -       y       -       0       bounce
defer     unix  -       -       y       -       0       bounce
trace     unix  -       -       y       -       0       bounce
verify    unix  -       -       y       -       1       verify
flush     unix  n       -       y       1000?   0       flush
proxymap  unix  -       -       n       -       -       proxymap
proxywrite unix -       -       n       -       1       proxymap
smtp      unix  -       -       y       -       -       smtp
relay     unix  -       -       y       -       -       smtp
        -o syslog_name=postfix/$service_name
showq     unix  n       -       y       -       -       showq
error     unix  -       -       y       -       -       error
retry     unix  -       -       y       -       -       error
discard   unix  -       -       y       -       -       discard
local     unix  -       n       n       -       -       local
virtual   unix  -       n       n       -       -       virtual
lmtp      unix  -       -       y       -       -       lmtp
anvil     unix  -       -       y       -       1       anvil
scache    unix  -       -       y       -       1       scache
maildrop  unix  -       n       n       -       -       pipe
  flags=DRhu user=vmail argv=/usr/bin/maildrop -d ${recipient}
uucp      unix  -       n       n       -       -       pipe
  flags=Fqhu user=uucp argv=uux -r -n -z -a$sender - $nexthop!rmail ($recipient)
ifmail    unix  -       n       n       -       -       pipe
  flags=F user=ftn argv=/usr/lib/ifmail/ifmail -r $nexthop ($recipient)
bsmtp     unix  -       n       n       -       -       pipe
  flags=Fq. user=bsmtp argv=/usr/lib/bsmtp/bsmtp -t$nexthop -f$sender $recipient
scalemail-backend unix	-	n	n	-	2	pipe
  flags=R user=scalemail argv=/usr/lib/scalemail/bin/scalemail-queue -w -e -m ${extension} ${user}
mailman   unix  -       n       n       -       -       pipe
  flags=FR user=list argv=/usr/lib/mailman/bin/postfix-to-mailman.py
  ${nexthop} ${user}
EOF

# Clear any existing postfix cache
print_status "Clearing Postfix cache..."
rm -rf /var/lib/postfix/*.db 2>/dev/null || true
rm -rf /var/spool/postfix/private/* 2>/dev/null || true

# Test configuration
print_status "Testing Postfix configuration..."
if postfix check; then
    print_success "Postfix configuration is valid"
else
    print_error "Postfix configuration has errors"
    print_status "Configuration errors:"
    postfix check
    exit 1
fi

# Start Postfix
print_status "Starting Postfix..."
systemctl start postfix

# Wait a moment for startup
sleep 3

# Check Postfix status
print_status "Checking Postfix status..."
if systemctl is-active --quiet postfix; then
    print_success "Postfix is running successfully"
else
    print_error "Postfix failed to start"
    systemctl status postfix --no-pager -l
    exit 1
fi

# Check for any remaining postmulti issues
print_status "Checking for remaining postmulti issues..."
if postmulti -l 2>/dev/null | grep -q "conflicts"; then
    print_warning "Postmulti conflicts still detected:"
    postmulti -l 2>/dev/null
else
    print_success "No postmulti conflicts detected"
fi

# Check mail logs for errors
print_status "Checking mail logs for errors..."
sleep 5
if tail -n 20 /var/log/mail.log | grep -q "fatal.*conflicts"; then
    print_warning "Found conflict errors in mail logs:"
    tail -n 20 /var/log/mail.log | grep -i "fatal.*conflicts"
else
    print_success "No conflict errors found in mail logs"
fi

# Test SMTP functionality
print_status "Testing SMTP functionality..."
if netstat -tlnp | grep -q ":25\|:587\|:465"; then
    print_success "SMTP ports are listening"
    netstat -tlnp | grep -E ":(25|587|465)"
else
    print_warning "SMTP ports are not listening"
fi

print_success "Complete Postfix fix completed!"
print_status "Summary:"
print_status "1. Completely disabled postmulti"
print_status "2. Forced single instance mode"
print_status "3. Created clean configurations"
print_status "4. Postfix is running successfully"
print_status ""
print_status "You can now proceed with SSL certificate installation:"
print_status "sudo bash install_postfix_ssl.sh dripemails.org" 