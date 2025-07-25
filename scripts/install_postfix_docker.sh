#!/bin/bash

# Docker-based Postfix Email Server Setup for DripEmails
# This script sets up a production-ready email server using Docker

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}================================${NC}"
echo -e "${BLUE}  DripEmails Docker Email Setup${NC}"
echo -e "${BLUE}================================${NC}"

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Docker is not installed. Please install Docker first.${NC}"
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}Docker Compose is not installed. Please install Docker Compose first.${NC}"
    exit 1
fi

# Get configuration
read -p "Enter your domain name (e.g., dripemails.org): " DOMAIN
read -p "Enter your server IP address: " SERVER_IP
read -p "Enter admin email address: " ADMIN_EMAIL

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

# Create directory structure
echo -e "${YELLOW}Creating directory structure...${NC}"
mkdir -p email-server/{config,logs,ssl,dkim}

# Create Docker Compose file
echo -e "${YELLOW}Creating Docker Compose configuration...${NC}"
cat > email-server/docker-compose.yml <<EOF
version: '3.8'

services:
  postfix:
    image: catatnight/postfix
    container_name: dripemails-postfix
    hostname: mail.$DOMAIN
    ports:
      - "25:25"
      - "587:587"
    environment:
      - maildomain=$DOMAIN
      - smtp_user=noreply:$DOMAIN
    volumes:
      - ./config/postfix:/etc/postfix
      - ./logs:/var/log
      - ./ssl:/etc/ssl
      - ./dkim:/etc/opendkim
    restart: unless-stopped
    networks:
      - email-network

  dovecot:
    image: tvial/docker-mailserver
    container_name: dripemails-dovecot
    ports:
      - "993:993"
      - "995:995"
    volumes:
      - ./config/dovecot:/etc/dovecot
      - ./logs:/var/log
    restart: unless-stopped
    networks:
      - email-network

  opendkim:
    image: analogic/poste.io
    container_name: dripemails-opendkim
    volumes:
      - ./dkim:/etc/opendkim
      - ./logs:/var/log
    restart: unless-stopped
    networks:
      - email-network

  nginx:
    image: nginx:alpine
    container_name: dripemails-nginx
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./config/nginx:/etc/nginx/conf.d
      - ./ssl:/etc/ssl
    restart: unless-stopped
    networks:
      - email-network

networks:
  email-network:
    driver: bridge
EOF

# Create Postfix configuration
echo -e "${YELLOW}Creating Postfix configuration...${NC}"
mkdir -p email-server/config/postfix

cat > email-server/config/postfix/main.cf <<EOF
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
smtpd_recipient_restrictions = permit_mynetworks, reject_unauth_destination, reject_invalid_hostname, reject_non_fqdn_hostname, reject_non_fqdn_sender, reject_non_fqdn_recipient, reject_unknown_sender_domain, reject_unknown_recipient_domain

# TLS Settings
smtpd_tls_cert_file = /etc/ssl/certs/mail.$DOMAIN.crt
smtpd_tls_key_file = /etc/ssl/private/mail.$DOMAIN.key
smtpd_tls_security_level = may
smtpd_tls_auth_only = no
smtpd_tls_protocols = !SSLv2, !SSLv3
smtpd_tls_mandatory_protocols = !SSLv2, !SSLv3

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

# DKIM Configuration
milter_default_action = accept
milter_protocol = 2
smtpd_milters = inet:opendkim:12301
non_smtpd_milters = inet:opendkim:12301
EOF

# Create master.cf
cat > email-server/config/postfix/master.cf <<EOF
# Postfix master process configuration file
smtp      inet  n       -       y       -       -       smtpd
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

# Create Nginx configuration
echo -e "${YELLOW}Creating Nginx configuration...${NC}"
mkdir -p email-server/config/nginx

cat > email-server/config/nginx/default.conf <<EOF
server {
    listen 80;
    server_name mail.$DOMAIN;
    
    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }
    
    location / {
        return 301 https://\$server_name\$request_uri;
    }
}

server {
    listen 443 ssl;
    server_name mail.$DOMAIN;
    
    ssl_certificate /etc/ssl/certs/mail.$DOMAIN.crt;
    ssl_certificate_key /etc/ssl/private/mail.$DOMAIN.key;
    
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    
    location / {
        return 200 "DripEmails Mail Server";
        add_header Content-Type text/plain;
    }
}
EOF

# Create SSL certificate (self-signed for now)
echo -e "${YELLOW}Creating SSL certificate...${NC}"
mkdir -p email-server/ssl/{certs,private}

openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout email-server/ssl/private/mail.$DOMAIN.key \
    -out email-server/ssl/certs/mail.$DOMAIN.crt \
    -subj "/C=US/ST=State/L=City/O=DripEmails/CN=mail.$DOMAIN"

# Set proper permissions
chmod 600 email-server/ssl/private/mail.$DOMAIN.key
chmod 644 email-server/ssl/certs/mail.$DOMAIN.crt

# Create DKIM key
echo -e "${YELLOW}Creating DKIM key...${NC}"
mkdir -p email-server/dkim/keys/$DOMAIN

# Generate DKIM key using Docker
docker run --rm -v $(pwd)/email-server/dkim:/etc/opendkim analogic/poste.io \
    opendkim-genkey -t -s mail -d $DOMAIN

mv email-server/dkim/mail.private email-server/dkim/keys/$DOMAIN/mail.private
mv email-server/dkim/mail.txt email-server/dkim/keys/$DOMAIN/mail.txt

# Set permissions
chmod 600 email-server/dkim/keys/$DOMAIN/mail.private
chmod 644 email-server/dkim/keys/$DOMAIN/mail.txt

# Start services
echo -e "${YELLOW}Starting email services...${NC}"
cd email-server
docker-compose up -d

# Wait for services to start
echo -e "${YELLOW}Waiting for services to start...${NC}"
sleep 10

# Test services
echo -e "${YELLOW}Testing services...${NC}"
if docker-compose ps | grep -q "Up"; then
    echo -e "${GREEN}Services are running!${NC}"
else
    echo -e "${RED}Some services failed to start${NC}"
    docker-compose logs
    exit 1
fi

# Create DNS records file
echo -e "${YELLOW}Creating DNS records file...${NC}"
cat > /root/dns_records_docker.txt <<EOF
# DNS Records for $DOMAIN (Docker Setup)
# Add these records to your DNS provider:

# MX Record
$DOMAIN.    IN  MX  10  mail.$DOMAIN.

# A Record for mail server
mail.$DOMAIN.    IN  A  $SERVER_IP

# SPF Record
$DOMAIN.    IN  TXT  "v=spf1 mx a ip4:$SERVER_IP ~all"

# DKIM Record
$(cat email-server/dkim/keys/$DOMAIN/mail.txt)

# DMARC Record
_dmarc.$DOMAIN.    IN  TXT  "v=DMARC1; p=quarantine; rua=mailto:dmarc@$DOMAIN"
EOF

# Create Django settings file
echo -e "${YELLOW}Creating Django settings file...${NC}"
cat > /root/django_email_settings_docker.py <<EOF
# Django Email Settings for Production (Docker Setup)
# Add these settings to your Django settings.py or live.py

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'localhost'  # or your server IP
EMAIL_PORT = 587
EMAIL_HOST_USER = 'noreply@$DOMAIN'
EMAIL_HOST_PASSWORD = ''  # No password for local submission
EMAIL_USE_TLS = True
EMAIL_USE_SSL = False
DEFAULT_FROM_EMAIL = 'noreply@$DOMAIN'
EOF

# Create management scripts
echo -e "${YELLOW}Creating management scripts...${NC}"
cat > /usr/local/bin/dripemails-mail-status <<EOF
#!/bin/bash
cd $(pwd)/email-server
echo "=== DripEmails Mail Server Status ==="
docker-compose ps
echo ""
echo "=== Mail Queue ==="
docker-compose exec postfix mailq | head -10
echo ""
echo "=== Recent Logs ==="
docker-compose logs --tail=10 postfix
EOF

cat > /usr/local/bin/dripemails-mail-logs <<EOF
#!/bin/bash
cd $(pwd)/email-server
docker-compose logs -f postfix
EOF

cat > /usr/local/bin/dripemails-mail-restart <<EOF
#!/bin/bash
cd $(pwd)/email-server
docker-compose restart
EOF

chmod +x /usr/local/bin/dripemails-mail-*

echo -e "${GREEN}================================${NC}"
echo -e "${GREEN}  Docker Email Setup Complete!${NC}"
echo -e "${GREEN}================================${NC}"
echo ""
echo -e "${BLUE}Next Steps:${NC}"
echo "1. Add DNS records from /root/dns_records_docker.txt to your DNS provider"
echo "2. Wait 24-48 hours for DNS propagation"
echo "3. Update your Django settings with the configuration in /root/django_email_settings_docker.py"
echo "4. Test email sending with: echo 'Subject: Test' | sendmail $ADMIN_EMAIL"
echo ""
echo -e "${BLUE}Useful Commands:${NC}"
echo "- Check status: dripemails-mail-status"
echo "- View logs: dripemails-mail-logs"
echo "- Restart services: dripemails-mail-restart"
echo "- Stop services: cd email-server && docker-compose down"
echo "- Update services: cd email-server && docker-compose pull && docker-compose up -d"
echo ""
echo -e "${YELLOW}Important:${NC}"
echo "- Make sure ports 25, 587, 80, and 443 are open in your firewall"
echo "- Consider getting a proper SSL certificate from Let's Encrypt"
echo "- Monitor your mail logs for any issues"
echo "- Set up proper backup procedures for the email-server directory" 