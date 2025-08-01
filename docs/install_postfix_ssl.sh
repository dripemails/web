#!/bin/sh

# Postfix SSL Certificate Installation Script
# This script installs and configures SSL certificates for production use

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

# Check if domain is provided
if [ -z "$1" ]; then
    print_error "Usage: $0 <domain>"
    print_error "Example: $0 dripemails.org"
    exit 1
fi

DOMAIN="$1"
print_status "Installing SSL certificates for domain: $DOMAIN"

# Step 1: Install certbot and dependencies
print_status "Step 1: Installing certbot and dependencies..."
apt update
apt install -y certbot python3-certbot-nginx nginx
print_success "Certbot and dependencies installed"

# Step 2: Stop nginx temporarily (if running)
print_status "Step 2: Stopping nginx temporarily..."
systemctl stop nginx 2>/dev/null || true
print_success "Nginx stopped"

# Step 3: Create temporary nginx configuration for certbot
print_status "Step 3: Creating temporary nginx configuration..."
mkdir -p /etc/nginx/sites-available
cat > /etc/nginx/sites-available/certbot << 'EOF'
server {
    listen 80;
    server_name dripemails.org www.dripemails.org;
    
    location /.well-known/acme-challenge/ {
        root /var/www/html;
    }
    
    location / {
        return 301 https://$server_name$request_uri;
    }
}
EOF

# Enable the site
ln -sf /etc/nginx/sites-available/certbot /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default 2>/dev/null || true

# Create webroot directory
mkdir -p /var/www/html/.well-known/acme-challenge
chown -R www-data:www-data /var/www/html

# Test nginx configuration
nginx -t
print_success "Nginx configuration is valid"

# Step 4: Start nginx for certbot
print_status "Step 4: Starting nginx for certbot..."
systemctl start nginx
sleep 3
print_success "Nginx started"

# Step 5: Obtain SSL certificate
print_status "Step 5: Obtaining SSL certificate..."
certbot certonly --webroot -w /var/www/html -d $DOMAIN -d www.$DOMAIN --email admin@$DOMAIN --agree-tos --non-interactive
print_success "SSL certificate obtained"

# Step 6: Stop nginx
print_status "Step 6: Stopping nginx..."
systemctl stop nginx
print_success "Nginx stopped"

# Step 7: Configure Postfix with SSL certificates
print_status "Step 7: Configuring Postfix with SSL certificates..."
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

# Disable multi-instance completely
multi_instance_enable = no
multi_instance_name = 
multi_instance_group = 
multi_instance_directories = 
EOF
print_success "Postfix configured with SSL certificates"

# Step 8: Update master.cf for SSL
print_status "Step 8: Updating master.cf for SSL..."
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
print_success "Master.cf updated for SSL"

# Step 9: Set proper permissions for SSL certificates
print_status "Step 9: Setting proper permissions for SSL certificates..."
chmod 644 /etc/letsencrypt/live/$DOMAIN/fullchain.pem
chmod 600 /etc/letsencrypt/live/$DOMAIN/privkey.pem
chown root:root /etc/letsencrypt/live/$DOMAIN/fullchain.pem
chown root:root /etc/letsencrypt/live/$DOMAIN/privkey.pem
print_success "SSL certificate permissions set"

# Step 10: Test Postfix configuration
print_status "Step 10: Testing Postfix configuration..."
if postfix check; then
    print_success "Postfix configuration is valid"
else
    print_error "Postfix configuration has errors"
    postfix check
    exit 1
fi

# Step 11: Reload Postfix
print_status "Step 11: Reloading Postfix..."
systemctl reload postfix
sleep 3
print_success "Postfix reloaded"

# Step 12: Check Postfix status
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

# Step 14: Test SSL connections
print_status "Step 14: Testing SSL connections..."
if echo "QUIT" | openssl s_client -connect localhost:465 -quiet 2>/dev/null | grep -q "220"; then
    print_success "SSL connection to port 465 is working"
else
    print_warning "SSL connection to port 465 failed"
fi

# Step 15: Set up automatic renewal
print_status "Step 15: Setting up automatic renewal..."
cat > /etc/cron.d/certbot-renew << 'EOF'
# Certbot renewal
0 12 * * * root /usr/bin/certbot renew --quiet --post-hook "systemctl reload postfix"
EOF
print_success "Automatic renewal configured"

# Step 16: Create renewal script
print_status "Step 16: Creating renewal script..."
cat > /usr/local/bin/renew-ssl.sh << 'EOF'
#!/bin/bash
# SSL Certificate Renewal Script
certbot renew --quiet
if [ $? -eq 0 ]; then
    systemctl reload postfix
    echo "SSL certificates renewed successfully"
else
    echo "SSL certificate renewal failed"
    exit 1
fi
EOF
chmod +x /usr/local/bin/renew-ssl.sh
print_success "Renewal script created"

print_success "SSL certificate installation completed!"
print_status "Summary:"
print_status "1. SSL certificates obtained from Let's Encrypt"
print_status "2. Postfix configured with SSL certificates"
print_status "3. All SMTP ports (25, 587, 465) configured with SSL"
print_status "4. Automatic renewal configured"
print_status "5. Postfix is running with SSL support"
print_status ""
print_status "Your Postfix server is now configured with SSL certificates!"
print_status "You can test SSL connections with:"
print_status "openssl s_client -connect dripemails.org:465"
print_status "openssl s_client -connect dripemails.org:587"
print_status ""
print_status "Certificates will automatically renew every 60 days" 