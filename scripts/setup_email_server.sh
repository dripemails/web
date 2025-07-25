#!/bin/bash

# Production Email Server Setup Script for DripEmails
# This script installs and configures Postfix for production email sending

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration variables
DOMAIN=""
SERVER_IP=""
ADMIN_EMAIL=""

echo -e "${BLUE}================================${NC}"
echo -e "${BLUE}  DripEmails Email Server Setup${NC}"
echo -e "${BLUE}================================${NC}"

# Get configuration from user
read -p "Enter your domain name (e.g., dripemails.org): " DOMAIN
read -p "Enter your server IP address: " SERVER_IP
read -p "Enter admin email address: " ADMIN_EMAIL

# Validate inputs
if [[ -z "$DOMAIN" || -z "$SERVER_IP" || -z "$ADMIN_EMAIL" ]]; then
    echo -e "${RED}Error: All fields are required${NC}"
    exit 1
fi

echo -e "${GREEN}Configuration:${NC}"
echo -e "  Domain: $DOMAIN"
echo -e "  Server IP: $SERVER_IP"
echo -e "  Admin Email: $ADMIN_EMAIL"
echo ""

read -p "Continue with installation? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}Installation cancelled${NC}"
    exit 0
fi

echo -e "${BLUE}Starting installation...${NC}"

# Update system
echo -e "${YELLOW}Updating system packages...${NC}"
sudo apt update && sudo apt upgrade -y

# Install required packages
echo -e "${YELLOW}Installing Postfix and related packages...${NC}"
sudo apt install -y postfix postfix-mysql dovecot-core dovecot-imapd dovecot-pop3d \
    spamassassin spamc opendkim opendkim-tools certbot python3-certbot-nginx \
    mailutils

# Configure Postfix
echo -e "${YELLOW}Configuring Postfix...${NC}"

# Create Postfix configuration
sudo tee /etc/postfix/main.cf > /dev/null <<EOF
# Basic Settings
myhostname = mail.$DOMAIN
mydomain = $DOMAIN
myorigin = \$mydomain
inet_interfaces = all
inet_protocols = ipv4

# Network Settings
mydestination = \$myhostname, localhost.\$mydomain, localhost, \$mydomain
mynetworks = 127.0.0.0/8, 10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16
mynetworks_style = subnet

# Security Settings
smtpd_helo_required = yes
smtpd_helo_restrictions = permit_mynetworks, reject_invalid_helo_hostname, reject_non_fqdn_helo_hostname
smtpd_recipient_restrictions = permit_mynetworks, reject_unauth_destination, reject_invalid_hostname, reject_non_fqdn_hostname, reject_non_fqdn_sender, reject_non_fqdn_recipient, reject_unknown_sender_domain, reject_unknown_recipient_domain, reject_rbl_client zen.spamhaus.org, reject_rbl_client bl.spamcop.net

# TLS Settings
smtpd_tls_cert_file = /etc/letsencrypt/live/mail.$DOMAIN/fullchain.pem
smtpd_tls_key_file = /etc/letsencrypt/live/mail.$DOMAIN/privkey.pem
smtpd_tls_security_level = may
smtpd_tls_auth_only = no
smtpd_tls_protocols = !SSLv2, !SSLv3
smtpd_tls_mandatory_protocols = !SSLv2, !SSLv3
smtpd_tls_mandatory_ciphers = medium
smtpd_tls_ciphers = medium
smtpd_tls_mandatory_exclude_ciphers = aNULL, DES, 3DES, MD5, DES+MD5, RC4
smtpd_tls_exclude_ciphers = aNULL, DES, 3DES, MD5, DES+MD5, RC4
smtpd_tls_mandatory_dh1024_auto = yes

# Submission Settings
smtpd_tls_received_header = yes
smtpd_tls_session_cache_database = btree:\${data_directory}/smtpd_scache
smtpd_tls_session_cache_timeout = 3600s
smtpd_tls_loglevel = 1

# Authentication
smtpd_sasl_auth_enable = yes
smtpd_sasl_security_options = noanonymous
smtpd_sasl_local_domain = \$myhostname
smtpd_sasl_authenticated_header = yes

# Relay Settings
smtpd_relay_restrictions = permit_mynetworks, permit_sasl_authenticated, reject_unauth_destination

# Rate Limiting
smtpd_client_connection_rate_limit = 30
smtpd_client_message_rate_limit = 30
smtpd_client_recipient_rate_limit = 30
smtpd_client_restrictions = permit_mynetworks, permit_sasl_authenticated, reject

# Logging
maillog_file = /var/log/mail.log

# DKIM Configuration
milter_default_action = accept
milter_protocol = 2
smtpd_milters = inet:localhost:12301
non_smtpd_milters = inet:localhost:12301
EOF

# Configure submission port
echo -e "${YELLOW}Configuring submission port...${NC}"
sudo tee -a /etc/postfix/master.cf > /dev/null <<EOF

submission inet n       -       y       -       -       smtpd
  -o syslog_name=postfix/submission
  -o smtpd_tls_security_level=encrypt
  -o smtpd_sasl_auth_enable=yes
  -o smtpd_tls_auth_only=yes
  -o smtpd_reject_unlisted_recipient=no
  -o smtpd_client_restrictions=permit_sasl_authenticated,reject
  -o smtpd_helo_restrictions=permit_mynetworks,permit_sasl_authenticated,reject
  -o smtpd_sender_restrictions=permit_mynetworks,permit_sasl_authenticated,reject
  -o smtpd_recipient_restrictions=reject_sasl_authenticated,permit_mynetworks,reject_unauth_destination
  -o milter_macro_daemon_name=ORIGINATING
EOF

# Set up OpenDKIM
echo -e "${YELLOW}Setting up OpenDKIM...${NC}"
sudo mkdir -p /etc/opendkim/keys/$DOMAIN

# Generate DKIM key
sudo opendkim-genkey -t -s mail -d $DOMAIN
sudo mv mail.private /etc/opendkim/keys/$DOMAIN/mail.private
sudo mv mail.txt /etc/opendkim/keys/$DOMAIN/mail.txt

# Set permissions
sudo chown -R opendkim:opendkim /etc/opendkim/keys/$DOMAIN
sudo chmod 600 /etc/opendkim/keys/$DOMAIN/mail.private

# Configure OpenDKIM
sudo tee /etc/opendkim.conf > /dev/null <<EOF
# OpenDKIM Configuration
Domain                  $DOMAIN
KeyFile                 /etc/opendkim/keys/$DOMAIN/mail.private
Selector                mail
SignHeaders             From,To,Subject,Date,Message-ID
Canonicalization        relaxed/simple
Mode                    sv
SubDomains             No
Socket                  inet:12301@localhost
PidFile                 /var/run/opendkim/opendkim.pid
EOF

# Get SSL certificate
echo -e "${YELLOW}Getting SSL certificate...${NC}"
echo -e "${BLUE}Note: Make sure port 80 is open and DNS is configured for mail.$DOMAIN${NC}"
read -p "Press Enter when ready to continue..."

sudo certbot certonly --standalone -d mail.$DOMAIN --email $ADMIN_EMAIL --agree-tos --non-interactive

# Set proper permissions
sudo chmod 755 /etc/letsencrypt/live/
sudo chmod 755 /etc/letsencrypt/archive/

# Restart services
echo -e "${YELLOW}Restarting services...${NC}"
sudo systemctl restart postfix
sudo systemctl restart opendkim
sudo systemctl enable postfix
sudo systemctl enable opendkim

# Test configuration
echo -e "${YELLOW}Testing configuration...${NC}"
sudo postfix check

# Create DNS records file
echo -e "${YELLOW}Creating DNS records file...${NC}"
sudo tee /root/dns_records.txt > /dev/null <<EOF
# DNS Records for $DOMAIN
# Add these records to your DNS provider:

# MX Record
$DOMAIN.    IN  MX  10  mail.$DOMAIN.

# A Record for mail server
mail.$DOMAIN.    IN  A  $SERVER_IP

# SPF Record
$DOMAIN.    IN  TXT  "v=spf1 mx a ip4:$SERVER_IP ~all"

# DKIM Record
$(cat /etc/opendkim/keys/$DOMAIN/mail.txt)

# DMARC Record
_dmarc.$DOMAIN.    IN  TXT  "v=DMARC1; p=quarantine; rua=mailto:dmarc@$DOMAIN"
EOF

# Create Django settings file
echo -e "${YELLOW}Creating Django settings file...${NC}"
sudo tee /root/django_email_settings.py > /dev/null <<EOF
# Django Email Settings for Production
# Add these settings to your Django settings.py or live.py

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'localhost'
EMAIL_PORT = 587
EMAIL_HOST_USER = 'noreply@$DOMAIN'
EMAIL_HOST_PASSWORD = ''  # No password for local submission
EMAIL_USE_TLS = True
EMAIL_USE_SSL = False
DEFAULT_FROM_EMAIL = 'noreply@$DOMAIN'
EOF

# Set up SSL certificate renewal
echo -e "${YELLOW}Setting up SSL certificate renewal...${NC}"
sudo crontab -l 2>/dev/null | { cat; echo "0 12 * * * /usr/bin/certbot renew --quiet && systemctl reload postfix"; } | sudo crontab -

# Create monitoring script
echo -e "${YELLOW}Creating monitoring script...${NC}"
sudo tee /usr/local/bin/mail-monitor.sh > /dev/null <<EOF
#!/bin/bash
# Mail server monitoring script

echo "=== Mail Server Status ==="
echo "Postfix: \$(systemctl is-active postfix)"
echo "OpenDKIM: \$(systemctl is-active opendkim)"
echo ""
echo "=== Mail Queue ==="
mailq | head -10
echo ""
echo "=== Recent Logs ==="
tail -5 /var/log/mail.log
EOF

sudo chmod +x /usr/local/bin/mail-monitor.sh

echo -e "${GREEN}================================${NC}"
echo -e "${GREEN}  Installation Complete!${NC}"
echo -e "${GREEN}================================${NC}"
echo ""
echo -e "${BLUE}Next Steps:${NC}"
echo "1. Add DNS records from /root/dns_records.txt to your DNS provider"
echo "2. Wait 24-48 hours for DNS propagation"
echo "3. Update your Django settings with the configuration in /root/django_email_settings.py"
echo "4. Test email sending with: echo 'Subject: Test' | sendmail $ADMIN_EMAIL"
echo ""
echo -e "${BLUE}Useful Commands:${NC}"
echo "- Monitor mail server: /usr/local/bin/mail-monitor.sh"
echo "- View mail queue: mailq"
echo "- Check logs: tail -f /var/log/mail.log"
echo "- Test SMTP: telnet localhost 587"
echo ""
echo -e "${YELLOW}Important:${NC}"
echo "- Make sure ports 25, 587, and 993 are open in your firewall"
echo "- Monitor your mail logs for any issues"
echo "- Set up proper backup procedures" 