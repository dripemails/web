# Postfix SSL Certificate Installation

This directory contains a script to automatically install SSL certificates for Postfix using Let's Encrypt certbot on Ubuntu Server 24.04.1.

## Files

- `install_postfix_ssl.sh` - Main installation script
- `README_postfix_ssl.md` - This documentation file

## Prerequisites

1. **Ubuntu Server 24.04.1** (or compatible)
2. **Postfix** installed via `apt-get`
3. **Root access** (run with `sudo`)
4. **Domain name** pointing to your server
5. **Port 80** available for certificate validation

## Quick Start

1. **Navigate to the docs directory:**
   ```bash
   cd /path/to/dripemails.org/docs
   ```

2. **Run the script as root with your domain:**
   ```bash
   sudo ./install_postfix_ssl.sh mail.dripemails.org
   ```

## What the Script Does

### 1. System Checks
- Verifies Ubuntu 24.04.1 compatibility
- Checks if Postfix is installed
- Installs certbot if not present

### 2. Certificate Acquisition
- Stops Postfix temporarily
- Uses certbot to obtain SSL certificate
- Validates certificate installation

### 3. Postfix Configuration
- Backs up existing configuration
- Configures SSL settings in `main.cf`
- Sets up SSL ports in `master.cf`
- Generates DH parameters for security

### 4. Security Setup
- Sets proper file permissions
- Configures firewall rules
- Enables secure TLS protocols

### 5. Service Management
- Tests configuration validity
- Restarts Postfix service
- Creates automatic renewal script

## Configuration Details

### SSL Ports Configured
- **Port 25** - Standard SMTP
- **Port 465** - SMTPS (SSL/TLS)
- **Port 587** - Submission (STARTTLS)

### Security Features
- TLS 1.2+ only (no legacy protocols)
- Strong cipher suites
- DH parameters for perfect forward secrecy
- Proper file permissions

### Certificate Renewal
- Automatic renewal every 60 days
- Postfix reload after renewal
- Renewal script: `/etc/letsencrypt/renewal-hooks/post/postfix-ssl-renew.sh`

## Testing

### Test SSL Connection
```bash
openssl s_client -connect mail.dripemails.org:465
```

### Check Postfix Status
```bash
systemctl status postfix
```

### View Logs
```bash
journalctl -u postfix -f
```

### Test Certificate Renewal
```bash
certbot renew --dry-run
```

## Troubleshooting

### Common Issues

1. **Permission Denied**
   ```bash
   sudo chmod +x install_postfix_ssl.sh
   ```

2. **Domain Not Resolving**
   - Ensure DNS A record points to server IP
   - Wait for DNS propagation

3. **Port 80 Blocked**
   - Temporarily allow port 80 for certificate validation
   - Configure firewall: `sudo ufw allow 80/tcp`

4. **Postfix Won't Start**
   ```bash
   postfix check
   journalctl -u postfix -n 50
   ```

### Manual Certificate Renewal
```bash
sudo certbot renew
sudo systemctl reload postfix
```

## Files Created/Modified

### Configuration Files
- `/etc/postfix/main.cf` - SSL configuration added
- `/etc/postfix/master.cf` - SSL ports configured
- `/etc/postfix/dh2048.pem` - DH parameters

### Certificates
- `/etc/letsencrypt/live/[domain]/fullchain.pem`
- `/etc/letsencrypt/live/[domain]/privkey.pem`

### Scripts
- `/etc/letsencrypt/renewal-hooks/post/postfix-ssl-renew.sh`

### Backups
- `/etc/postfix/backup_[timestamp]/` - Original configuration

## Security Notes

- Certificates are automatically renewed
- Strong TLS configuration prevents downgrade attacks
- File permissions are set securely
- Firewall rules are configured automatically

## Integration with DripEmails

This SSL setup works with the DripEmails SMTP server configuration. Update your Django settings:

```python
# In live.py or settings.py
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'localhost'
EMAIL_PORT = 587  # Use submission port
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'your_username'
EMAIL_HOST_PASSWORD = 'your_password'
```

## Support

For issues with this script:
1. Check the troubleshooting section above
2. Review Postfix logs: `journalctl -u postfix`
3. Verify certificate status: `certbot certificates`
4. Test SSL connection manually

## License

This script is part of the DripEmails.org project and follows the same license terms. 
