# DripEmails SMTP Server

A modern, async SMTP server built with `aiosmtpd` for Python 3.11+. Perfect for development, testing, and production email handling.

## 🚀 Features

- **Modern Async Architecture**: Built with `aiosmtpd` for high-performance async email handling
- **Python 3.11+ Compatible**: Optimized for modern Python versions
- **Django Integration**: Seamless integration with Django applications
- **Webhook Support**: Forward email metadata to external services
- **Database Logging**: Store email metadata in your database
- **Rate Limiting**: Built-in protection against spam and abuse
- **Authentication**: Support for PLAIN and LOGIN authentication
- **Debug Mode**: Comprehensive logging and debugging capabilities
- **Production Ready**: Designed for both development and production use

## 📋 Requirements

- Python 3.11 or higher
- `aiosmtpd>=1.4.4`
- Optional: Django 4.0+ for database integration
- Optional: `aiohttp>=3.8.0` for webhook support

## 🛠️ Installation

### From PyPI (Coming Soon)

```bash
pip install dripemails-smtp-server
```

### From Source

```bash
git clone https://github.com/dripemails/smtp_server.git
cd smtp_server
pip install -e .
```

## 🚀 Quick Start

### Basic Usage

```python
from core.smtp_server import create_smtp_server

# Create server with default configuration
server = create_smtp_server()

# Start server on localhost:1025
server.start('localhost', 1025)

# Keep server running
import time
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    server.stop()
```

### Django Integration

```python
# In your Django management command
from django.core.management.base import BaseCommand
from core.smtp_server import run_smtp_server

class Command(BaseCommand):
    help = 'Run SMTP server'
    
    def handle(self, *args, **options):
        config = {
            'debug': True,
            'save_to_database': True,
            'allowed_domains': ['yourdomain.com'],
        }
        run_smtp_server('localhost', 1025, config)
```

### Command Line Usage

```bash
# Run with debug mode
python -m core.smtp_server --debug --port 1025

# Run with custom configuration
python -m core.smtp_server --config smtp_config.json --port 1025

# Run without authentication (allow anonymous access)
python manage.py run_smtp_server --no-auth --port 1025

# Combine options: no-auth with debug mode
python manage.py run_smtp_server --no-auth --debug --port 1025
```

## ⚙️ Configuration

### Basic Configuration

```python
config = {
    'debug': False,                    # Enable debug output
    'save_to_database': True,          # Save emails to database
    'log_to_file': True,               # Log to file
    'log_file': 'email_log.jsonl',     # Log file path
    'allowed_domains': [               # Allowed recipient domains
        'yourdomain.com',
        'localhost',
        '127.0.0.1'
    ],
    'webhook_url': None,               # Webhook URL for notifications
    'forward_to_webhook': False,       # Enable webhook forwarding
    'auth_enabled': True,              # Enable authentication (set False for --no-auth)
    'allowed_users': ['founders'],     # Allowed users for auth
}
```

### Configuration File (JSON)

```json
{
    "debug": true,
    "save_to_database": true,
    "log_to_file": true,
    "log_file": "email_log.jsonl",
    "allowed_domains": ["yourdomain.com", "localhost"],
    "webhook_url": "https://api.yourdomain.com/webhook",
    "forward_to_webhook": true,
    "auth_enabled": true,
    "allowed_users": ["founders", "admin"],
    "max_message_size": 10485760,
    "timeout": 30
}
```

## 🔧 Django Integration

### 1. Add to INSTALLED_APPS

```python
INSTALLED_APPS = [
    # ... other apps
    'core',
]
```

### 2. Run Migrations

```bash
python manage.py makemigrations core
python manage.py migrate
```

### 3. Create Management Command

```python
# core/management/commands/run_smtp_server.py
from django.core.management.base import BaseCommand
from core.smtp_server import run_smtp_server

class Command(BaseCommand):
    help = 'Run SMTP server'
    
    def add_arguments(self, parser):
        parser.add_argument('--port', type=int, default=1025)
        parser.add_argument('--debug', action='store_true')
        parser.add_argument('--config', type=str)
    
    def handle(self, *args, **options):
        config = {
            'debug': options['debug'],
            'save_to_database': True,
        }
        run_smtp_server('localhost', options['port'], config)
```

### 4. Run Server

```bash
# With authentication (default)
python manage.py run_smtp_server --debug --port 1025

# Without authentication (for local development)
python manage.py run_smtp_server --no-auth --debug --port 1025
```

## 📧 Email Processing

### Email Metadata Structure

```python
{
    'from': 'sender@example.com',
    'to': 'recipient@yourdomain.com',
    'subject': 'Test Email',
    'date': '2024-01-01T12:00:00',
    'message_id': '<unique-message-id>',
    'received_at': '2024-01-01T12:00:00.123456',
    'size': 1024,
    'body': 'Email content...'
}
```

### Database Model (Django)

```python
from django.db import models

class EmailLog(models.Model):
    sender = models.EmailField(max_length=254)
    recipient = models.EmailField(max_length=254)
    subject = models.CharField(max_length=255)
    body = models.TextField()
    message_id = models.CharField(max_length=255, blank=True)
    received_at = models.DateTimeField(auto_now_add=True)
    size = models.IntegerField(default=0)
    processed = models.BooleanField(default=False)
    error_message = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-received_at']
        indexes = [
            models.Index(fields=['sender']),
            models.Index(fields=['recipient']),
            models.Index(fields=['received_at']),
        ]
```

## 🔐 Authentication

### Authentication Modes

The SMTP server supports two authentication modes:

1. **With Authentication (Default)**: Requires valid Django user credentials
2. **Without Authentication (`--no-auth`)**: Allows anonymous email sending

### The `--no-auth` Flag

The `--no-auth` flag disables SMTP authentication, allowing anonymous email sending. This is useful for:

- ✅ **Local Development**: Easier testing without user accounts
- ✅ **Internal Networks**: When security is handled at the network level
- ✅ **Development Environments**: Quick setup without authentication configuration
- ✅ **Production with Alternative Security**: When using other security measures (firewall, VPN, etc.)

**⚠️ Security Warning**: Only use `--no-auth` in production if:
- The SMTP server is behind a firewall
- Access is restricted to trusted networks
- You have other security measures in place
- You understand the security implications

#### Usage Examples

```bash
# Run without authentication
python manage.py run_smtp_server --no-auth --port 25

# No-auth with debug mode
python manage.py run_smtp_server --no-auth --debug --port 1025

# No-auth in production (with other security measures)
python manage.py run_smtp_server --no-auth --port 25 --save-to-db --log-to-file
```

#### Django Email Configuration

When using `--no-auth`, configure Django to send emails without authentication:

```python
# In your Django settings (e.g., live.py)
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'localhost'
EMAIL_PORT = 25
# Leave these empty or unset to disable authentication
EMAIL_HOST_USER = ''  # Empty string
EMAIL_HOST_PASSWORD = ''  # Empty string
EMAIL_USE_TLS = False
EMAIL_USE_SSL = False
```

The Django email backend will automatically skip authentication if `EMAIL_HOST_USER` and `EMAIL_HOST_PASSWORD` are empty or not set.

### Supported Authentication Methods

When authentication is enabled (default, without `--no-auth`):

- **PLAIN**: Simple username/password authentication
- **LOGIN**: Base64 encoded credentials

### Django User Authentication

The server integrates with Django's authentication system:

```python
# Users must exist in Django and be active
# Authentication checks against Django's User model
# Supports user groups and permissions
# Default allowed users: ['founders']
```

#### Custom Allowed Users

```bash
# Specify allowed users for authentication
python manage.py run_smtp_server --allowed-users founders admin user1 --port 25
```

## 🌐 Webhook Support

### Webhook Payload

```json
{
    "from": "sender@example.com",
    "to": "recipient@yourdomain.com",
    "subject": "Test Email",
    "date": "2024-01-01T12:00:00",
    "message_id": "<unique-message-id>",
    "received_at": "2024-01-01T12:00:00.123456",
    "size": 1024,
    "body": "Email content..."
}
```

### Configuration

```python
config = {
    'webhook_url': 'https://api.yourdomain.com/webhook',
    'forward_to_webhook': True,
}
```

## 🧪 Testing

### Test Script

```python
import smtplib
from email.mime.text import MIMEText

def test_smtp_server(host='localhost', port=1025):
    # Create message
    msg = MIMEText('Test email content')
    msg['From'] = 'test@example.com'
    msg['To'] = 'test@yourdomain.com'
    msg['Subject'] = 'Test Email'
    
    # Send email
    server = smtplib.SMTP(host, port)
    server.send_message(msg)
    server.quit()
    
    print("Test email sent successfully!")

# Run test
test_smtp_server()
```

### Automated Tests

```bash
# Run tests
pytest tests/

# Run with coverage
pytest --cov=core tests/
```

## 📊 Monitoring

### Server Statistics

```python
server = create_smtp_server()
stats = server.get_stats()

print(f"Emails received: {stats['emails_received']}")
print(f"Emails processed: {stats['emails_processed']}")
print(f"Emails failed: {stats['emails_failed']}")
print(f"Uptime: {stats['uptime']} seconds")
```

### Logging

```python
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

## 🚀 Production Deployment

### Using Supervisord

**With Authentication (Default):**
```ini
[program:dripemails-smtp]
command=python manage.py run_smtp_server --port 25 --save-to-db --log-to-file
directory=/path/to/your/project
user=www-data
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/dripemails-smtp.log
environment=DJANGO_SETTINGS_MODULE="dripemails.live"
```

**Without Authentication (`--no-auth`):**
```ini
[program:dripemails-smtp]
command=python manage.py run_smtp_server --no-auth --port 25 --save-to-db --log-to-file
directory=/path/to/your/project
user=www-data
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/dripemails-smtp.log
environment=DJANGO_SETTINGS_MODULE="dripemails.live"
```

### Using Docker

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 25

CMD ["python", "manage.py", "run_smtp_server", "--port", "25"]
```

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Setup

```bash
# Clone repository
git clone https://github.com/dripemails/smtp_server.git
cd smtp_server

# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Format code
black core/ tests/

# Lint code
flake8 core/ tests/
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Documentation**: [GitHub Wiki](https://github.com/dripemails/smtp_server/wiki)
- **Issues**: [GitHub Issues](https://github.com/dripemails/smtp_server/issues)
- **Discussions**: [GitHub Discussions](https://github.com/dripemails/smtp_server/discussions)
- **Email**: founders@dripemails.org

## 🙏 Acknowledgments

- Built with [aiosmtpd](https://aiosmtpd.readthedocs.io/)
- Inspired by modern async Python patterns
- Community feedback and contributions

---

**Made with ❤️ by the DripEmails Team**
