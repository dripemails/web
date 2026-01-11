# Custom SMTP Server Setup Guide

This guide explains how to set up and use the custom SMTP server built with `aiosmtpd` for DripEmails.org.

## Overview

The custom SMTP server provides:
- **Modern async architecture** using `aiosmtpd`
- **Email processing and storage** in Django database
- **Webhook notifications** for real-time email events
- **Rate limiting** and spam protection
- **Comprehensive logging** and monitoring
- **Production-ready** configuration
- **Python 3.12.3 compatible**

## Requirements

- Python 3.12.3 or higher
- Django 5.2.4 or higher
- aiosmtpd 1.4.4 or higher

## Installation

### 1. Install Dependencies

The SMTP server requires `aiosmtpd` which is already included in `requirements.txt`:

```bash
pip install -r requirements.txt
```

### 2. Database Migration

Create and apply the migration for the EmailLog model:

```bash
python manage.py makemigrations core
python manage.py migrate
```

## Quick Start

### Basic Usage

Start the SMTP server with default settings:

```bash
python manage.py run_smtp_server
```

This starts the server on `localhost:1025` with debug mode enabled.

### Advanced Usage

```bash
# Custom port and host
python manage.py run_smtp_server --host 0.0.0.0 --port 587

# Enable database logging
python manage.py run_smtp_server --save-to-db

# Enable file logging
python manage.py run_smtp_server --log-to-file

# Enable webhook forwarding
python manage.py run_smtp_server --webhook-url https://api.example.com/webhook

# All features enabled
python manage.py run_smtp_server \
    --host 0.0.0.0 \
    --port 587 \
    --debug \
    --save-to-db \
    --log-to-file \
    --webhook-url https://api.example.com/webhook
```

## Configuration

### Configuration File

Create a JSON configuration file for advanced settings:

```json
{
    "debug": false,
    "save_to_database": true,
    "log_to_file": true,
    "log_file": "email_log.jsonl",
    "forward_to_webhook": true,
    "webhook_url": "https://api.example.com/webhook",
    "allowed_domains": ["dripemails.org", "example.com"],
    "rate_limit": 100,
    "rate_limit_window": 3600
}
```

Use the configuration file:

```bash
python manage.py run_smtp_server --config smtp_config.json
```

### Environment Variables

You can also configure via environment variables:

```bash
export SMTP_DEBUG=true
export SMTP_SAVE_TO_DB=true
export SMTP_WEBHOOK_URL=https://api.example.com/webhook
export SMTP_LOG_FILE=email_log.jsonl
```

## Django Integration

### Email Settings

Update your Django settings to use the local SMTP server:

```python
# settings.py or live.py
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'localhost'
EMAIL_PORT = 1025  # or your custom port
EMAIL_USE_TLS = False
EMAIL_USE_SSL = False
EMAIL_HOST_USER = 'noreply@dripemails.org'
EMAIL_HOST_PASSWORD = ''  # No password for local server
DEFAULT_FROM_EMAIL = 'noreply@dripemails.org'
```

### Testing Email Sending

Test the email functionality:

```python
from django.core.mail import send_mail

# Send a test email
send_mail(
    subject='Test Email',
    message='This is a test email from DripEmails.',
    from_email='noreply@dripemails.org',
    recipient_list=['test@example.com'],
    fail_silently=False,
)
```

## Production Deployment

### 1. Systemd Service

Create a systemd service file `/etc/systemd/system/dripemails-smtp.service`:

```ini
[Unit]
Description=DripEmails SMTP Server
After=network.target

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=/path/to/dripemails.org
Environment=PATH=/path/to/venv/bin
ExecStart=/path/to/venv/bin/python manage.py run_smtp_server --host 0.0.0.0 --port 587 --save-to-db --log-to-file
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start the service:

```bash
sudo systemctl daemon-reload
sudo systemctl enable dripemails-smtp
sudo systemctl start dripemails-smtp
sudo systemctl status dripemails-smtp
```

### 2. Firewall Configuration

Configure your firewall to allow SMTP traffic:

```bash
# UFW (Ubuntu)
sudo ufw allow 587/tcp
sudo ufw allow 25/tcp

# iptables
sudo iptables -A INPUT -p tcp --dport 587 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 25 -j ACCEPT
```

## Monitoring and Logging

### Server Statistics

The SMTP server provides real-time statistics:

```python
from core.smtp_server import create_smtp_server

server = create_smtp_server()
stats = server.get_stats()
print(f"Emails received: {stats['emails_received']}")
print(f"Emails processed: {stats['emails_processed']}")
print(f"Uptime: {stats['uptime']} seconds")
```

### Log Files

The server creates several log files:

- **Django logs**: `logs/django.log`
- **Email logs**: `email_log.jsonl` (if enabled)
- **System logs**: `/var/log/syslog` (systemd service)

### Monitoring Commands

```bash
# Check server status
sudo systemctl status dripemails-smtp

# View recent logs
tail -f logs/django.log

# View email logs
tail -f email_log.jsonl

# Check email queue
python manage.py shell -c "from core.models import EmailLog; print(EmailLog.objects.count())"
```

## Security Considerations

### 1. Domain Restrictions

The server only accepts emails for configured domains:

```python
config = {
    'allowed_domains': ['dripemails.org', 'yourdomain.com']
}
```

### 2. Rate Limiting

Built-in rate limiting prevents abuse:

- Default: 100 emails per hour per IP
- Configurable via `rate_limit` setting

### 3. Spam Protection

Basic spam detection is included:

```python
# Check if email is spam
email_log = EmailLog.objects.get(id=1)
if email_log.is_spam:
    print("This email appears to be spam")
```

### 4. TLS/SSL

For production, consider using TLS:

```bash
# Generate SSL certificate
sudo certbot certonly --standalone -d mail.dripemails.org

# Update configuration
config = {
    'ssl_cert_file': '/etc/letsencrypt/live/mail.dripemails.org/fullchain.pem',
    'ssl_key_file': '/etc/letsencrypt/live/mail.dripemails.org/privkey.pem'
}
```

## Troubleshooting

### Common Issues

1. **Port already in use**:
   ```bash
   sudo netstat -tlnp | grep :587
   sudo kill -9 <PID>
   ```

2. **Permission denied**:
   ```bash
   sudo chown -R www-data:www-data /path/to/dripemails.org
   sudo chmod -R 755 /path/to/dripemails.org
   ```

3. **Database connection issues**:
   ```bash
   python manage.py check --database default
   python manage.py migrate
   ```

4. **Email not being received**:
   ```bash
   # Check server logs
   tail -f logs/django.log
   
   # Test SMTP connection
   telnet localhost 587
   ```

5. **Python 3.12 compatibility issues**:
   ```bash
   # Ensure you're using Python 3.12.3+
   python --version
   
   # Check aiosmtpd version
   pip show aiosmtpd
   ```

### Debug Mode

Enable debug mode for detailed logging:

```bash
python manage.py run_smtp_server --debug
```

This will print all received emails to the console.

## API Integration

### Webhook Notifications

The server can send webhook notifications for each email:

```json
{
    "from": "sender@example.com",
    "to": "recipient@dripemails.org",
    "subject": "Test Email",
    "body": "Email content...",
    "message_id": "<123@example.com>",
    "received_at": "2024-01-01T12:00:00Z",
    "size": 1024
}
```

### Database Queries

Query email logs programmatically:

```python
from core.models import EmailLog
from django.utils import timezone
from datetime import timedelta

# Recent emails
recent_emails = EmailLog.objects.filter(
    received_at__gte=timezone.now() - timedelta(hours=24)
)

# Emails from specific sender
sender_emails = EmailLog.objects.filter(sender='sender@example.com')

# Unprocessed emails
unprocessed = EmailLog.objects.filter(processed=False)
```

## Performance Optimization

### 1. Database Indexing

The EmailLog model includes optimized indexes for common queries.

### 2. Connection Pooling

For high-volume scenarios, consider using connection pooling:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'OPTIONS': {
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
            'charset': 'utf8mb4',
        },
        'CONN_MAX_AGE': 60,
        'CONN_HEALTH_CHECKS': True,
    }
}
```

### 3. Async Processing

The server uses async processing for better performance:

- Non-blocking email processing
- Concurrent webhook delivery
- Efficient rate limiting

## Support

For issues and questions:

1. Check the logs: `tail -f logs/django.log`
2. Enable debug mode: `--debug`
3. Review this documentation
4. Check the Django management command help: `python manage.py run_smtp_server --help` 
