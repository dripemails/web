#!/bin/bash

# Completely reinstall Postfix from scratch
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

print_status "Completely reinstalling Postfix from scratch..."

# Step 1: Stop all services
print_status "Step 1: Stopping all services..."
systemctl stop postfix 2>/dev/null || true
pkill -f "postfix.*master" 2>/dev/null || true
pkill -f "postfix.*smtpd" 2>/dev/null || true
pkill -f "postfix.*qmgr" 2>/dev/null || true
pkill -f "postfix.*pickup" 2>/dev/null || true
sleep 3
print_success "All services stopped"

# Step 2: Backup SSL certificates
print_status "Step 2: Backing up SSL certificates..."
if [ -f "/etc/letsencrypt/live/dripemails.org/fullchain.pem" ]; then
    cp /etc/letsencrypt/live/dripemails.org/fullchain.pem /tmp/fullchain.pem.backup
    cp /etc/letsencrypt/live/dripemails.org/privkey.pem /tmp/privkey.pem.backup
    print_success "SSL certificates backed up"
else
    print_warning "SSL certificates not found"
fi

# Step 3: Completely remove Postfix
print_status "Step 3: Completely removing Postfix..."
apt remove --purge postfix postfix-sqlite -y
apt autoremove -y
print_success "Postfix completely removed"

# Step 4: Clean up all Postfix directories
print_status "Step 4: Cleaning up Postfix directories..."
rm -rf /etc/postfix
rm -rf /var/spool/postfix
rm -rf /var/lib/postfix
rm -rf /var/log/mail.log*
print_success "Postfix directories cleaned"

# Step 5: Reinstall Postfix
print_status "Step 5: Reinstalling Postfix..."
apt update
apt install postfix postfix-sqlite -y
print_success "Postfix reinstalled"

# Step 6: Verify binaries exist
print_status "Step 6: Verifying Postfix binaries..."
if [ -f "/usr/lib/postfix/sbin/smtpd" ] && [ -f "/usr/lib/postfix/sbin/qmgr" ] && [ -f "/usr/lib/postfix/sbin/pickup" ]; then
    print_success "All Postfix binaries are present"
else
    print_error "Postfix binaries are missing"
    ls -la /usr/lib/postfix/sbin/
    exit 1
fi

# Step 7: Restore SSL certificates
print_status "Step 7: Restoring SSL certificates..."
if [ -f "/tmp/fullchain.pem.backup" ]; then
    cp /tmp/fullchain.pem.backup /etc/letsencrypt/live/dripemails.org/fullchain.pem
    cp /tmp/privkey.pem.backup /etc/letsencrypt/live/dripemails.org/privkey.pem
    chmod 644 /etc/letsencrypt/live/dripemails.org/fullchain.pem
    chmod 600 /etc/letsencrypt/live/dripemails.org/privkey.pem
    chown root:root /etc/letsencrypt/live/dripemails.org/fullchain.pem
    chown root:root /etc/letsencrypt/live/dripemails.org/privkey.pem
    print_success "SSL certificates restored"
else
    print_warning "SSL certificates not restored"
fi

# Step 8: Create SSL configuration
print_status "Step 8: Creating SSL configuration..."
cat > /etc/postfix/main.cf << 'EOF'
# Postfix Configuration - Production with SSL
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

# SASL Authentication
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

# TLS settings with Let's Encrypt certificates
smtpd_tls_security_level = may
smtpd_tls_auth_only = no
smtpd_tls_cert_file = /etc/letsencrypt/live/dripemails.org/fullchain.pem
smtpd_tls_key_file = /etc/letsencrypt/live/dripemails.org/privkey.pem
smtpd_tls_protocols = !SSLv2, !SSLv3
smtpd_tls_ciphers = high
smtpd_tls_mandatory_protocols = !SSLv2, !SSLv3
smtpd_tls_mandatory_ciphers = high
smtpd_tls_session_cache_database = btree:${data_directory}/smtpd_scache
smtpd_tls_session_cache_timeout = 3600s
smtpd_tls_received_header = yes
smtpd_tls_loglevel = 1

# SMTP TLS settings
smtp_tls_security_level = may
smtp_tls_CApath = /etc/ssl/certs
smtp_tls_session_cache_database = btree:${data_directory}/smtp_scache
smtp_tls_session_cache_timeout = 3600s

# Force single instance mode
multi_instance_enable = no
multi_instance_name = 
multi_instance_group = 
multi_instance_directories = 
EOF
print_success "SSL configuration created"

# Step 9: Create master.cf
print_status "Step 9: Creating master.cf..."
cat > /etc/postfix/master.cf << 'EOF'
#
# Postfix master process configuration file
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
  -o smtpd_client_restrictions=permit_mynetworks,permit_sasl_authenticated,reject
  -o smtpd_helo_restrictions=permit_mynetworks,permit_sasl_authenticated
  -o smtpd_sender_restrictions=permit_mynetworks,permit_sasl_authenticated
  -o smtpd_recipient_restrictions=permit_mynetworks,permit_sasl_authenticated,reject_unauth_destination
  -o smtpd_relay_restrictions=permit_mynetworks,permit_sasl_authenticated,reject_unauth_destination
  -o milter_macro_daemon_name=ORIGINATING
smtps     inet  n       -       y       -       -       smtpd
  -o syslog_name=postfix/smtps
  -o smtpd_tls_wrappermode=yes
  -o smtpd_sasl_auth_enable=yes
  -o smtpd_reject_unlisted_recipient=no
  -o smtpd_client_restrictions=permit_mynetworks,permit_sasl_authenticated,reject
  -o smtpd_helo_restrictions=permit_mynetworks,permit_sasl_authenticated
  -o smtpd_sender_restrictions=permit_mynetworks,permit_sasl_authenticated
  -o smtpd_recipient_restrictions=permit_mynetworks,permit_sasl_authenticated,reject_unauth_destination
  -o smtpd_relay_restrictions=permit_mynetworks,permit_sasl_authenticated,reject_unauth_destination
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
print_success "Master.cf created"

# Step 10: Test configuration
print_status "Step 10: Testing Postfix configuration..."
if postfix check; then
    print_success "Postfix configuration is valid"
else
    print_error "Postfix configuration has errors"
    postfix check
    exit 1
fi

# Step 11: Start Postfix
print_status "Step 11: Starting Postfix..."
systemctl start postfix
sleep 5
print_success "Postfix started"

# Step 12: Check status
print_status "Step 12: Checking Postfix status..."
if systemctl is-active --quiet postfix; then
    print_success "Postfix is running successfully"
else
    print_error "Postfix failed to start"
    systemctl status postfix --no-pager -l
    exit 1
fi

# Step 13: Check SMTP ports
print_status "Step 13: Checking SMTP ports..."
sleep 3
if netstat -tlnp | grep -q ":25\|:587\|:465"; then
    print_success "SMTP ports are listening:"
    netstat -tlnp | grep -E ":(25|587|465)"
else
    print_warning "SMTP ports are not listening"
fi

# Step 14: Check for postmulti conflicts
print_status "Step 14: Checking for postmulti conflicts..."
if postmulti -l 2>&1 | grep -q "fatal"; then
    print_warning "Postmulti conflicts detected"
    postmulti -l
else
    print_success "No postmulti conflicts detected"
fi

print_success "Postfix complete reinstallation completed!"
print_status "Summary:"
print_status "1. Postfix completely removed and reinstalled"
print_status "2. All binaries are present in /usr/lib/postfix/"
print_status "3. SSL configuration restored"
print_status "4. Postfix is running successfully"
print_status "5. SMTP ports should be listening"
print_status ""
print_status "Your Postfix server is now fully functional with SSL!" 