# Production Email Server Setup with Postfix

This guide sets up a production-ready email server using Postfix that can actually send emails to real recipients.

## Overview

We'll use **Postfix** as the SMTP server with the following components:
- **Postfix**: Main SMTP server for sending emails
- **Dovecot**: IMAP/POP3 server for receiving emails (optional)
- **SpamAssassin**: Spam filtering
- **DKIM**: Email authentication
- **SPF/DMARC**: Additional email security

## Prerequisites

- Ubuntu/Debian server (recommended)
- Domain name with proper DNS records
- Root or sudo access
- Ports 25, 587, 993 open

## Installation Steps

### 1. Install Postfix and Required Packages

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Postfix and related packages
sudo apt install -y postfix postfix-mysql dovecot-core dovecot-imapd dovecot-pop3d \
    spamassassin spamc opendkim opendkim-tools certbot python3-certbot-nginx

# During Postfix installation, choose "Internet Site"
```

### 2. Configure Postfix

Edit the main Postfix configuration:

```bash
sudo nano /etc/postfix/main.cf
```

Add/update these settings:

```conf
# Basic Settings
myhostname = mail.yourdomain.com
mydomain = yourdomain.com
myorigin = $mydomain
inet_interfaces = all
inet_protocols = ipv4

# Network Settings
mydestination = $myhostname, localhost.$mydomain, localhost, $mydomain
mynetworks = 127.0.0.0/8, 10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16
mynetworks_style = subnet

# Security Settings
smtpd_helo_required = yes
smtpd_helo_restrictions = permit_mynetworks, reject_invalid_helo_hostname, reject_non_fqdn_helo_hostname
smtpd_recipient_restrictions = permit_mynetworks, reject_unauth_destination, reject_invalid_hostname, reject_non_fqdn_hostname, reject_non_fqdn_sender, reject_non_fqdn_recipient, reject_unknown_sender_domain, reject_unknown_recipient_domain, reject_rbl_client zen.spamhaus.org, reject_rbl_client bl.spamcop.net

# TLS Settings
smtpd_tls_cert_file = /etc/letsencrypt/live/mail.yourdomain.com/fullchain.pem
smtpd_tls_key_file = /etc/letsencrypt/live/mail.yourdomain.com/privkey.pem
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
smtpd_tls_session_cache_database = btree:${data_directory}/smtpd_scache
smtpd_tls_session_cache_timeout = 3600s
smtpd_tls_loglevel = 1

# Authentication
smtpd_sasl_auth_enable = yes
smtpd_sasl_security_options = noanonymous
smtpd_sasl_local_domain = $myhostname
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
```

### 3. Configure Submission Port (587)

Edit the submission configuration:

```bash
sudo nano /etc/postfix/master.cf
```

Ensure these lines are uncommented:

```conf
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
```

### 4. Set Up SSL Certificate

```bash
# Get SSL certificate
sudo certbot certonly --standalone -d mail.yourdomain.com

# Set proper permissions
sudo chmod 755 /etc/letsencrypt/live/
sudo chmod 755 /etc/letsencrypt/archive/
```

### 5. Configure DKIM

```bash
# Generate DKIM key
sudo opendkim-genkey -t -s mail -d yourdomain.com

# Move key to proper location
sudo mv mail.private /etc/opendkim/keys/yourdomain.com/mail.private
sudo mv mail.txt /etc/opendkim/keys/yourdomain.com/mail.txt

# Set permissions
sudo chown opendkim:opendkim /etc/opendkim/keys/yourdomain.com/mail.private
sudo chmod 600 /etc/opendkim/keys/yourdomain.com/mail.private
```

Edit OpenDKIM configuration:

```bash
sudo nano /etc/opendkim.conf
```

```conf
# OpenDKIM Configuration
Domain                  yourdomain.com
KeyFile                 /etc/opendkim/keys/yourdomain.com/mail.private
Selector                mail
SignHeaders             From,To,Subject,Date,Message-ID
Canonicalization        relaxed/simple
Mode                    sv
SubDomains             No
Socket                  inet:12301@localhost
PidFile                 /var/run/opendkim/opendkim.pid
```

### 6. Configure Postfix with OpenDKIM

Add to `/etc/postfix/main.cf`:

```conf
# DKIM Configuration
milter_default_action = accept
milter_protocol = 2
smtpd_milters = inet:localhost:12301
non_smtpd_milters = inet:localhost:12301
```

### 7. Set Up DNS Records

Add these DNS records for your domain:

```dns
# MX Record
yourdomain.com.    IN  MX  10  mail.yourdomain.com.

# A Record for mail server
mail.yourdomain.com.    IN  A   YOUR_SERVER_IP

# SPF Record
yourdomain.com.    IN  TXT  "v=spf1 mx a ip4:YOUR_SERVER_IP ~all"

# DKIM Record (get the value from mail.txt)
mail._domainkey.yourdomain.com.    IN  TXT  "v=DKIM1; k=rsa; p=YOUR_PUBLIC_KEY"

# DMARC Record
_dmarc.yourdomain.com.    IN  TXT  "v=DMARC1; p=quarantine; rua=mailto:dmarc@yourdomain.com"
```

### 8. Restart Services

```bash
sudo systemctl restart postfix
sudo systemctl restart opendkim
sudo systemctl enable postfix
sudo systemctl enable opendkim
```

### 9. Test Configuration

```bash
# Test Postfix configuration
sudo postfix check

# Test SMTP
telnet localhost 25
telnet localhost 587

# Test DKIM
sudo opendkim-testkey -d yourdomain.com -s mail -k /etc/opendkim/keys/yourdomain.com/mail.private
```

## Django Configuration

Update your Django settings to use the local Postfix server:

```python
# Email Configuration for Production
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'localhost'
EMAIL_PORT = 587
EMAIL_HOST_USER = 'noreply@yourdomain.com'
EMAIL_HOST_PASSWORD = ''  # No password for local submission
EMAIL_USE_TLS = True
EMAIL_USE_SSL = False
DEFAULT_FROM_EMAIL = 'noreply@yourdomain.com'
```

## Monitoring and Maintenance

### Log Monitoring

```bash
# Monitor mail logs
sudo tail -f /var/log/mail.log

# Check mail queue
sudo mailq

# Flush mail queue
sudo postqueue -f
```

### SSL Certificate Renewal

```bash
# Add to crontab for automatic renewal
sudo crontab -e

# Add this line
0 12 * * * /usr/bin/certbot renew --quiet && systemctl reload postfix
```

### Backup Configuration

```bash
# Backup important files
sudo tar -czf postfix-backup-$(date +%Y%m%d).tar.gz \
    /etc/postfix \
    /etc/opendkim \
    /etc/letsencrypt/live/mail.yourdomain.com
```

## Troubleshooting

### Common Issues

1. **Port 25 blocked**: Contact your hosting provider
2. **DNS not propagated**: Wait 24-48 hours
3. **SSL certificate issues**: Check certbot logs
4. **Authentication failures**: Check SASL configuration

### Useful Commands

```bash
# Check Postfix status
sudo systemctl status postfix

# View mail queue
sudo mailq

# Test email sending
echo "Subject: Test" | sendmail your-email@example.com

# Check DNS records
dig MX yourdomain.com
dig TXT yourdomain.com
```

## Security Considerations

1. **Firewall**: Only open necessary ports (25, 587, 993)
2. **Rate Limiting**: Configure to prevent abuse
3. **Authentication**: Require SMTP authentication
4. **TLS**: Enforce TLS for all connections
5. **Monitoring**: Set up log monitoring and alerts

## Performance Optimization

1. **Connection Pooling**: Configure for high-volume sending
2. **Queue Management**: Monitor and optimize queue processing
3. **Resource Limits**: Set appropriate limits for your server capacity
4. **Caching**: Use Redis for session caching

This setup provides a production-ready email server that can handle real email delivery with proper authentication, security, and monitoring. 