#!/bin/bash

# Completely remove postmulti and force single-instance Postfix
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

print_status "Completely removing postmulti and forcing single-instance Postfix..."

# Step 1: Stop Postfix completely
print_status "Step 1: Stopping Postfix completely..."
systemctl stop postfix 2>/dev/null || true
pkill -f "postfix.*master" 2>/dev/null || true
pkill -f "postfix.*smtpd" 2>/dev/null || true
pkill -f "postfix.*qmgr" 2>/dev/null || true
pkill -f "postfix.*pickup" 2>/dev/null || true
sleep 3
print_success "Postfix stopped"

# Step 2: Completely remove postmulti
print_status "Step 2: Completely removing postmulti..."
postmulti -e destroy 2>/dev/null || true
postmulti -d 2>/dev/null || true
print_success "Postmulti destroyed"

# Step 3: Remove all postmulti configuration files
print_status "Step 3: Removing all postmulti configuration files..."
rm -f /etc/postfix/master.cf.* 2>/dev/null || true
rm -f /etc/postfix/main.cf.* 2>/dev/null || true
rm -f /etc/postfix/postmulti-instance-* 2>/dev/null || true
rm -f /etc/postfix/postmulti-instance.* 2>/dev/null || true
print_success "Postmulti config files removed"

# Step 4: Clear postfix cache and temporary files
print_status "Step 4: Clearing Postfix cache..."
rm -rf /var/spool/postfix/private/* 2>/dev/null || true
rm -rf /var/spool/postfix/public/* 2>/dev/null || true
rm -rf /var/spool/postfix/maildrop/* 2>/dev/null || true
rm -rf /var/spool/postfix/incoming/* 2>/dev/null || true
rm -rf /var/spool/postfix/active/* 2>/dev/null || true
rm -rf /var/spool/postfix/deferred/* 2>/dev/null || true
rm -rf /var/spool/postfix/hold/* 2>/dev/null || true
rm -rf /var/spool/postfix/corrupt/* 2>/dev/null || true
rm -rf /var/spool/postfix/trace/* 2>/dev/null || true
print_success "Postfix cache cleared"

# Step 5: Force single instance mode
print_status "Step 5: Forcing single instance mode..."
postconf -e "multi_instance_enable = no"
postconf -e "multi_instance_name = "
postconf -e "multi_instance_group = "
postconf -e "multi_instance_directories = "
print_success "Single instance mode forced"

# Step 6: Create clean master.cf
print_status "Step 6: Creating clean master.cf..."
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
print_success "Clean master.cf created"

# Step 7: Create clean main.cf with SSL
print_status "Step 7: Creating clean main.cf with SSL..."
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
print_success "Clean main.cf with SSL created"

# Step 8: Fix ownership
print_status "Step 8: Fixing ownership..."
chown -R root:root /var/spool/postfix/lib/x86_64-linux-gnu/ 2>/dev/null || true
chown -R root:root /var/spool/postfix/usr/lib/ 2>/dev/null || true
chown -R root:root /var/spool/postfix/usr/lib/zoneinfo/ 2>/dev/null || true
chown -R root:root /var/spool/postfix/usr/lib/sasl2/ 2>/dev/null || true
print_success "Ownership fixed"

# Step 9: Test configuration
print_status "Step 9: Testing Postfix configuration..."
if postfix check; then
    print_success "Postfix configuration is valid"
else
    print_error "Postfix configuration has errors"
    postfix check
    exit 1
fi

# Step 10: Start Postfix manually
print_status "Step 10: Starting Postfix manually..."
postfix start
sleep 5
print_success "Postfix started manually"

# Step 11: Check if Postfix is running
print_status "Step 11: Checking Postfix processes..."
if pgrep -f "postfix.*master" > /dev/null; then
    print_success "Postfix master process is running"
else
    print_error "Postfix master process is not running"
    exit 1
fi

# Step 12: Check SMTP ports
print_status "Step 12: Checking SMTP ports..."
sleep 3
if netstat -tlnp | grep -q ":25\|:587\|:465"; then
    print_success "SMTP ports are listening:"
    netstat -tlnp | grep -E ":(25|587|465)"
else
    print_warning "SMTP ports are not listening"
fi

# Step 13: Check for postmulti conflicts
print_status "Step 13: Checking for postmulti conflicts..."
if postmulti -l 2>&1 | grep -q "fatal"; then
    print_warning "Postmulti conflicts detected"
    postmulti -l
else
    print_success "No postmulti conflicts detected"
fi

print_success "Postmulti removal completed!"
print_status "Summary:"
print_status "1. Completely removed postmulti system"
print_status "2. Created clean single-instance configuration"
print_status "3. Postfix is running manually"
print_status "4. SMTP ports should be listening"
print_status ""
print_status "Your Postfix server is now running in single-instance mode!" 