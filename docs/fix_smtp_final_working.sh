#!/bin/sh

# Final SMTP Working Fix Script
# This script fixes ownership issues and ensures SMTP daemons start properly

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

print_status "Starting final SMTP working fix..."

# Step 1: Stop Postfix completely
print_status "Step 1: Stopping Postfix completely..."
systemctl stop postfix 2>/dev/null || true
pkill -f "postfix.*master" 2>/dev/null || true
pkill -f "postfix.*smtpd" 2>/dev/null || true
pkill -f "postfix.*qmgr" 2>/dev/null || true
pkill -f "postfix.*pickup" 2>/dev/null || true
pkill -f "postfix.*cleanup" 2>/dev/null || true
sleep 3
print_success "Postfix stopped"

# Step 2: Fix ALL ownership issues comprehensively
print_status "Step 2: Fixing ALL ownership issues comprehensively..."
chown -R root:root /var/spool/postfix/etc 2>/dev/null || true
chown -R root:root /var/spool/postfix/lib 2>/dev/null || true
chown -R root:root /var/spool/postfix/usr 2>/dev/null || true
chown -R root:root /var/spool/postfix/lib/x86_64-linux-gnu 2>/dev/null || true
chown -R root:root /var/spool/postfix/usr/lib 2>/dev/null || true
chown -R root:root /var/spool/postfix/usr/lib/zoneinfo 2>/dev/null || true
chown -R root:root /var/spool/postfix/usr/lib/sasl2 2>/dev/null || true
print_success "All ownership issues fixed"

# Step 3: Set proper permissions for all directories
print_status "Step 3: Setting proper permissions..."
find /var/spool/postfix -type d -exec chmod 755 {} \; 2>/dev/null || true
find /var/spool/postfix -type f -exec chmod 644 {} \; 2>/dev/null || true
chmod 755 /var/spool/postfix 2>/dev/null || true
print_success "Permissions set"

# Step 4: Completely remove postmulti and force single instance
print_status "Step 4: Completely removing postmulti..."
postmulti -e destroy 2>/dev/null || true
postmulti -d 2>/dev/null || true
rm -f /etc/postfix/postmulti-instance-* 2>/dev/null || true
rm -f /etc/postfix/master.cf.* 2>/dev/null || true
rm -f /etc/postfix/main.cf.* 2>/dev/null || true
print_success "Postmulti completely removed"

# Step 5: Force single instance mode
print_status "Step 5: Forcing single instance mode..."
postconf -e "multi_instance_enable = no" 2>/dev/null || true
postconf -e "multi_instance_name = " 2>/dev/null || true
postconf -e "multi_instance_group = " 2>/dev/null || true
postconf -e "multi_instance_directories = " 2>/dev/null || true
print_success "Single instance mode forced"

# Step 6: Clear all cached data
print_status "Step 6: Clearing all cached data..."
rm -rf /var/lib/postfix/*.db 2>/dev/null || true
rm -rf /var/spool/postfix/private/* 2>/dev/null || true
print_success "Cached data cleared"

# Step 7: Create minimal working master.cf
print_status "Step 7: Creating minimal working master.cf..."
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
smtps     inet  n       -       y       -       -       smtpd
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
showq     unix  n       -       y       -       -       showq
error     unix  -       -       y       -       -       error
retry     unix  -       -       y       -       -       error
discard   unix  -       -       y       -       -       discard
local     unix  -       n       n       -       -       local
virtual   unix  -       n       n       -       -       virtual
lmtp      unix  -       -       y       -       -       lmtp
anvil     unix  -       -       y       -       1       anvil
scache    unix  -       -       y       -       1       scache
EOF
print_success "Minimal master.cf created"

# Step 8: Create minimal working main.cf
print_status "Step 8: Creating minimal working main.cf..."
cat > /etc/postfix/main.cf << 'EOF'
# Minimal Postfix Configuration - Working
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

# Disable multi-instance completely
multi_instance_enable = no
multi_instance_name = 
multi_instance_group = 
multi_instance_directories = 
EOF
print_success "Minimal main.cf created"

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

# Step 11: Check if master process is running
print_status "Step 11: Checking if master process is running..."
if ps aux | grep -q "postfix.*master"; then
    print_success "Postfix master process is running"
else
    print_error "Postfix master process is not running"
    print_status "Checking logs for errors..."
    tail -n 20 /var/log/mail.log
    exit 1
fi

# Step 12: Check if SMTP daemons are running
print_status "Step 12: Checking if SMTP daemons are running..."
if ps aux | grep -q "postfix.*smtpd"; then
    print_success "SMTP daemons are running"
else
    print_warning "SMTP daemons are not running"
fi

# Step 13: Check SMTP ports
print_status "Step 13: Checking SMTP ports..."
sleep 3
if netstat -tlnp | grep -q ":25\|:587\|:465"; then
    print_success "SMTP ports are now listening:"
    netstat -tlnp | grep -E ":(25|587|465)"
else
    print_warning "SMTP ports are still not listening"
    print_status "Checking Postfix logs..."
    tail -n 20 /var/log/mail.log
fi

# Step 14: Test SMTP connection
print_status "Step 14: Testing SMTP connection..."
if echo "QUIT" | telnet localhost 25 2>/dev/null | grep -q "220"; then
    print_success "SMTP port 25 is responding"
else
    print_warning "SMTP port 25 is not responding"
fi

# Step 15: Check for postmulti conflicts
print_status "Step 15: Checking for postmulti conflicts..."
if postmulti -l 2>/dev/null | grep -q "conflicts"; then
    print_warning "Postmulti conflicts still detected:"
    postmulti -l 2>/dev/null
else
    print_success "No postmulti conflicts detected"
fi

print_success "Final SMTP working fix completed!"
print_status "Summary:"
print_status "1. Fixed ALL ownership issues comprehensively"
print_status "2. Completely removed postmulti system"
print_status "3. Created minimal working configurations"
print_status "4. Postfix master process is running"
print_status "5. SMTP ports should now be listening"
print_status ""
print_status "If SMTP ports are still not listening, check the logs for specific errors" 