# DripEmails.org - Modern Email Marketing Platform

[![Python](https://img.shields.io/badge/Python-3.11%2B-blue.svg)](https://www.python.org/downloads/)
[![Django](https://img.shields.io/badge/Django-4.0%2B-green.svg)](https://www.djangoproject.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![PyPI](https://img.shields.io/badge/PyPI-dripemails--smtp--server-blue.svg)](https://pypi.org/project/dripemails-smtp-server/)

> **A modern, open-source email marketing platform built with Django and Python 3.11+**

DripEmails.org is a comprehensive email marketing solution that combines powerful drip campaign management, subscriber analytics, and a custom SMTP server. Built with modern web technologies and designed for scalability, it's perfect for businesses looking to take control of their email marketing infrastructure.

## ⚡ Quick Highlights

**Perfect for Windows Development:**
- 🪟 **Redis is optional**: Works without Redis on Windows development - no setup complexity!
- 🤖 **Celery auto-disables**: On Windows with `DEBUG=True`, Celery automatically disables - no configuration needed
- 📧 **Synchronous email sending**: Emails send immediately without Celery/Redis queues
- 🔓 **`--no-auth` flag**: SMTP authentication automatically disabled for seamless local development

**Zero-Configuration Development:**
Start developing immediately on Windows without installing Redis or configuring Celery. The app intelligently detects your environment and adapts accordingly!

## 🚀 Features

### 📧 **Email Campaign Management**
- **Drip Campaigns**: Create automated email sequences with customizable delays
- **Email Templates**: Rich HTML and text email templates with dynamic content
- **Scheduling**: Advanced email scheduling with timezone support
- **A/B Testing**: Built-in A/B testing for subject lines and content
- **Campaign Analytics**: Detailed tracking and reporting

### 👥 **Subscriber Management**
- **Import/Export**: Bulk subscriber import from CSV/Excel files
- **Segmentation**: Advanced subscriber segmentation and targeting
- **Subscription Management**: Double opt-in, unsubscribe handling
- **Custom Fields**: Extensible subscriber data fields
- **API Integration**: RESTful API for subscriber management

### 📊 **Analytics & Reporting**
- **Real-time Analytics**: Live campaign performance tracking
- **Email Footer Analytics**: Track engagement through custom footers
- **Conversion Tracking**: Monitor click-through rates and conversions
- **Dashboard**: Beautiful, responsive analytics dashboard
- **Export Reports**: Generate detailed reports in multiple formats

### 🔧 **Custom SMTP Server**
- **Built-in SMTP Server**: Custom `aiosmtpd`-based email server
- **Authentication**: Secure SMTP authentication
- **Rate Limiting**: Built-in spam protection and rate limiting
- **Webhook Support**: Real-time email processing notifications
- **Django Integration**: Seamless integration with Django models

### 🛡️ **Security & Compliance**
- **GDPR Compliance**: Built-in privacy controls and data protection
- **Email Authentication**: SPF, DKIM, and DMARC support
- **Secure Authentication**: Django Allauth integration
- **Rate Limiting**: Protection against abuse and spam
- **Data Encryption**: Secure data storage and transmission

### 🎨 **Modern UI/UX**
- **Responsive Design**: Mobile-first, responsive interface
- **Modern Frontend**: Built with React, TypeScript, and Tailwind CSS
- **Dark Mode**: Optional dark theme support
- **Accessibility**: WCAG 2.1 compliant design
- **Progressive Web App**: PWA capabilities for mobile users

## 🏗️ Architecture

```
dripemails.org/
├── 📁 core/                 # Core Django app with SMTP server
├── 📁 campaigns/            # Email campaign management
├── 📁 subscribers/          # Subscriber management
├── 📁 analytics/            # Analytics and reporting
├── 📁 smtp_server/          # Standalone SMTP server package
├── 📁 templates/            # Django templates
├── 📁 static/               # Static assets
├── 📁 docs/                 # Documentation
└── 📁 tests/                # Test suite
```

## 🚀 Quick Start

### Prerequisites

- **Python 3.11+** (3.12.3 recommended)
- **MySQL/PostgreSQL** database (or SQLite for development)
- **Redis** (optional - not required for Windows development or synchronous email sending)

### ⚡ Key Features for Development

**Windows Development Made Easy:**
- ✅ **Redis is optional**: The app works without Redis on Windows development
- ✅ **Celery auto-disables**: On Windows with `DEBUG=True`, Celery is disabled automatically
- ✅ **Synchronous email sending**: Works without Celery/Redis; emails send immediately
- ✅ **`--no-auth` flag**: SMTP authentication automatically disabled for local development

**No Redis? No Problem!**
The application automatically falls back to synchronous email sending when Redis/Celery is unavailable. Perfect for:
- Windows development environments
- Quick local testing
- Low-volume email sending
- Immediate email delivery requirements

**Scheduled Emails Without Redis:**
When you select a schedule option (e.g., "Send in 5 minutes") but Celery/Redis is not available:
- ✅ Email is sent immediately (not queued)
- ✅ You'll see a message: *"Email sent immediately (scheduling requires Celery/Redis, which is not available in this environment)"*
- ✅ Email delivery is guaranteed - no emails are lost
- ✅ Perfect for development and testing on Windows

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/dripemails/web.git
   cd web
   ```

2. **Set up Python environment**
   ```bash
   python -m venv dripemails
   source dripemails/bin/activate  # Linux/macOS
   # or
   dripemails\Scripts\activate     # Windows
   
   pip install -r requirements.txt
   ```

4. **Configure environment**
   ```bash
   cp docs/env.example .env
   # Edit .env with your configuration
   ```

5. **Run migrations**
   ```bash
   python manage.py migrate
   ```

6. **Create superuser**
   ```bash
   python manage.py createsuperuser
   ```

7. **Start the development server**
   ```bash
   python manage.py runserver
   ```
   
   **Windows users:** No Redis needed! The app automatically uses synchronous email sending when `DEBUG=True`.

8. **Start the SMTP server** (optional)
   ```bash
   # For local development (default port 1025, automatic no-auth on Windows)
   python manage.py run_smtp_server
   
   # Custom port
   python manage.py run_smtp_server --port 2525
   
   # For local development with explicit no-auth flag
   python manage.py run_smtp_server --no-auth
   
   # Custom port with no-auth
   python manage.py run_smtp_server --no-auth --port 2525
   
   # For production or with authentication
   python manage.py run_smtp_server --host 0.0.0.0 --port 25
   ```

**Note:** 
- Default port is **1025** to avoid conflicts with Postfix (which typically uses port 25)
- On Windows with `DEBUG=True`, you don't need Redis. The SMTP server automatically runs without authentication, and emails are sent synchronously (immediately) without Celery.
- Press **Ctrl+C** to gracefully stop the server.

## 📧 SMTP Server Component

DripEmails includes a custom SMTP server built with `aiosmtpd` that integrates seamlessly with your Django application.

### Local Development

Run the SMTP server for local testing:

```bash
# Basic local development (default port 1025)
python manage.py run_smtp_server

# With debug mode
python manage.py run_smtp_server --debug

# Custom port
python manage.py run_smtp_server --port 2525

# Custom port with debug mode
python manage.py run_smtp_server --debug --port 2525

# Custom host and port
python manage.py run_smtp_server --host localhost --port 1025

# Disable authentication (for local testing)
python manage.py run_smtp_server --no-auth --port 1025
```

**Local Testing:**
```bash
# Test connection
telnet localhost 1025

# Send test email via Django
python manage.py shell
>>> from django.core.mail import send_mail
>>> send_mail('Test', 'Test message', 'from@example.com', ['to@example.com'])
```

### Production Deployment with Supervisord

For production deployment, use supervisord to manage the SMTP server:

#### 1. Install Supervisord

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install supervisor

# CentOS/RHEL
sudo yum install supervisor
```

#### 2. Create Configuration File

Create `/etc/supervisor/conf.d/dripemails-smtp.conf`:

```ini
[program:dripemails-smtp]
command=/home/dripemails/venv/bin/python /home/dripemails/web/manage.py run_smtp_server --host 0.0.0.0 --port 1025 --save-to-db --log-to-file
directory=/home/dripemails/web
user=dripemails
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/supervisor/dripemails-smtp.log
stdout_logfile_maxbytes=50MB
stdout_logfile_backups=10
environment=DJANGO_SETTINGS_MODULE="dripemails.live"
stopsignal=TERM
stopwaitsecs=10
```

#### 3. Configure and Start Service

```bash
# Update paths in config (replace with your actual paths)
# command=/path/to/venv/bin/python /path/to/project/manage.py run_smtp_server --host 0.0.0.0 --port 1025 --save-to-db --log-to-file
# directory=/path/to/project

# Reload configuration
sudo supervisorctl reread
sudo supervisorctl update

# Start the service
sudo supervisorctl start dripemails-smtp

# Check status
sudo supervisorctl status dripemails-smtp
```

#### 4. Management Commands

```bash
# Start service
sudo supervisorctl start dripemails-smtp

# Stop service
sudo supervisorctl stop dripemails-smtp

# Restart service
sudo supervisorctl restart dripemails-smtp

# View logs
sudo supervisorctl tail dripemails-smtp

# View all services
sudo supervisorctl status
```

### Alternative: Production with Systemd

Create `/etc/systemd/system/dripemails-smtp.service`:

```ini
[Unit]
Description=DripEmails SMTP Server
After=network.target

[Service]
Type=simple
User=dripemails
WorkingDirectory=/home/dripemails/web
Environment="DJANGO_SETTINGS_MODULE=dripemails.live"
ExecStart=/home/dripemails/venv/bin/python manage.py run_smtp_server --host 0.0.0.0 --port 1025 --save-to-db --log-to-file
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable dripemails-smtp
sudo systemctl start dripemails-smtp
sudo systemctl status dripemails-smtp
```

### Port Configuration

**Default Port (Recommended for development)**
```bash
# Default port is 1025 (avoids conflicts with Postfix on port 25)
python manage.py run_smtp_server
```

**Custom Port**
```bash
# Use a different port (e.g., 2525)
python manage.py run_smtp_server --port 2525

# Use port 25 (requires root/admin privileges)
python manage.py run_smtp_server --port 25

# Combine with other options
python manage.py run_smtp_server --port 2525 --no-auth --debug
```

**Production Port Forwarding (if using port 25)**
```bash
# Forward port 25 to 1025 (if you want to use port 25 in production)
sudo iptables -t nat -A PREROUTING -p tcp --dport 25 -j REDIRECT --to-port 1025
```

### SMTP Server Features
- **Async Performance**: Built with `aiosmtpd` for high performance
- **Authentication**: PLAIN and LOGIN authentication support (optional)
- **Rate Limiting**: Built-in spam protection
- **Database Storage**: Automatic email storage in database
- **Logging**: File-based logging for monitoring
- **Auto-restart**: Managed by supervisord or systemd

### SMTP Server Authentication

#### The `--no-auth` Flag

The `--no-auth` flag disables SMTP authentication, allowing anonymous email sending. This is useful for local development.

**When to use `--no-auth`:**
- ✅ Local development on Windows
- ✅ Testing without user accounts
- ✅ Development environments where security is not a concern

**When NOT to use `--no-auth`:**
- ❌ Production environments
- ❌ Shared development servers
- ❌ Any environment exposed to the internet

**Usage:**
```bash
# Disable authentication (allow anonymous access)
python manage.py run_smtp_server --no-auth

# Enable authentication (default)
python manage.py run_smtp_server
```

**Auto-Disable on Windows:**
On Windows with `DEBUG=True`, authentication is automatically disabled for easier local development. You can override this by explicitly enabling authentication if needed.

#### Email Authentication Configuration

Configure email authentication in three places depending on your environment:

##### 1. `.env` File (Development)

For local development, create a `.env` file in the project root:

```bash
# Email Settings - Local Development (No Authentication)
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=localhost
EMAIL_PORT=1025                      # Default port (avoids Postfix conflicts)
EMAIL_HOST_USER=                    # Leave empty for no-auth
EMAIL_HOST_PASSWORD=                # Leave empty for no-auth
EMAIL_USE_TLS=False
DEFAULT_FROM_EMAIL=noreply@dripemails.org

# Or with Authentication (if --no-auth flag is NOT used)
EMAIL_HOST_USER=founders            # Your Django username
EMAIL_HOST_PASSWORD=your_password   # Your Django user password
```

##### 2. `settings.py` (Development Settings)

The development settings automatically handle Windows development:

```python
# Email settings
EMAIL_BACKEND = env('EMAIL_BACKEND')
EMAIL_HOST = env('EMAIL_HOST', default='localhost')
EMAIL_PORT = env('EMAIL_PORT', default=25)
EMAIL_HOST_USER = env('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD', default='')
EMAIL_USE_TLS = env('EMAIL_USE_TLS', default=False)
DEFAULT_FROM_EMAIL = env('DEFAULT_FROM_EMAIL', default='DripEmails <noreply@dripemails.org>')

# Windows development: Automatically handles empty credentials
# Production: Set EMAIL_HOST_USER and EMAIL_HOST_PASSWORD in .env
```

##### 3. `live.py` (Production Settings)

For production, configure authentication in `dripemails/live.py`:

```python
# Email Configuration
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.environ.get('EMAIL_HOST', 'localhost')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', 25))
EMAIL_USE_TLS = False
EMAIL_USE_SSL = False
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER')        # Required for production
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD')  # Required for production
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'founders@dripemails.org')
```

**Production `.env` example:**
```bash
# Email Settings - Production (Authentication Required)
EMAIL_HOST=localhost
EMAIL_PORT=1025                       # Default port (use 25 for production if needed)
EMAIL_HOST_USER=founders              # Your Django username
EMAIL_HOST_PASSWORD=secure_password   # Your Django user password
EMAIL_USE_TLS=False
DEFAULT_FROM_EMAIL=founders@dripemails.org
```

**Important Notes:**
- For **no-auth** (local dev): Leave `EMAIL_HOST_USER` and `EMAIL_HOST_PASSWORD` empty in `.env`
- For **with auth** (production): Set both `EMAIL_HOST_USER` and `EMAIL_HOST_PASSWORD` in `.env`
- The SMTP server must match: Use `--no-auth` flag when credentials are empty, or provide credentials when authentication is enabled
- Windows development with `DEBUG=True` automatically uses no-auth mode

### Documentation
- 📖 [Production Setup Guide](docs/smtp_server_production_setup.md)
- 📖 [Supervisord Setup Guide](docs/supervisord_setup.md)
- 📖 [Supervisord Quick Reference](docs/supervisord_quick_reference.md)

## 🔧 Configuration

### Django Settings

```python
# Email Configuration
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'localhost'
EMAIL_PORT = 1025  # Default port (avoids Postfix conflicts)
EMAIL_HOST_USER = 'your_username'  # Empty for no-auth
EMAIL_HOST_PASSWORD = 'your_password'  # Empty for no-auth
DEFAULT_FROM_EMAIL = 'noreply@yourdomain.com'

# SMTP Server Configuration
SMTP_SERVER_CONFIG = {
    'host': 'localhost',
    'port': 1025,  # Default port (avoids Postfix conflicts on port 25)
    'auth_enabled': True,
    'allowed_domains': ['yourdomain.com'],
    'max_message_size': 10485760,  # 10MB
    'rate_limit': 100,  # emails per minute
}
```

## 🔄 Celery & Asynchronous Email Sending

### Celery is Optional - No Redis Required!

Celery is **not required** for DripEmails to function. The application will automatically use synchronous email sending when Celery/Redis is unavailable.

#### 🪟 Windows Development (Automatic)

**On Windows with `DEBUG=True`:**
- ✅ **Celery auto-disables**: No configuration needed
- ✅ **Redis not required**: Works without Redis installed
- ✅ **Synchronous email sending**: Emails send immediately
- ✅ **No setup complexity**: Just start the server and go!

**How it works:**
The application automatically detects Windows development mode and:
1. Disables Celery (no Redis connection attempts)
2. Sends emails synchronously (immediate delivery)
3. Works seamlessly without any additional setup

#### 🐧 Linux/macOS or Production

**When Celery is used:**
- ✅ Production environments with high email volume
- ✅ Scheduled email campaigns
- ✅ Background task processing
- ✅ Requires Redis to be installed and running

**When Celery is NOT used (synchronous mode):**
- ✅ Windows development (automatic when `DEBUG=True`)
- ✅ Development without Redis
- ✅ Low-volume email sending
- ✅ Immediate email delivery
- ✅ Any environment where Redis is unavailable

#### 📅 Scheduled Emails Behavior

**When Celery/Redis is NOT available:**
- **Scheduled emails are sent immediately** instead of being queued
- The application automatically falls back to synchronous sending
- You'll see a message: *"Email sent immediately (scheduling requires Celery/Redis, which is not available in this environment)"*
- This ensures emails are always sent, even without Celery/Redis

**Example:**
If you use the "Send Email" form and select a schedule option (e.g., "Send in 5 minutes"):
- **With Celery/Redis**: Email is scheduled and sent after 5 minutes
- **Without Celery/Redis**: Email is sent immediately with a notification that scheduling requires Celery/Redis

**Why this behavior?**
- Ensures emails are never lost due to missing Redis/Celery
- Provides a seamless development experience on Windows
- Allows immediate testing without additional setup
- Production deployments with Celery/Redis will use proper scheduling

### Celery Configuration

#### Automatic Detection

The application automatically detects when to use Celery:

- **Windows + DEBUG=True**: Celery **automatically disabled** (synchronous sending, no Redis needed)
- **Linux/macOS or DEBUG=False**: Celery enabled (requires Redis)
- **Manual override**: Set `CELERY_ENABLED=True/False` in `.env` to override auto-detection

#### Manual Configuration

Override automatic detection in your `.env` file:

```bash
# Enable Celery (requires Redis)
CELERY_ENABLED=True
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=django-db

# Disable Celery (synchronous sending)
CELERY_ENABLED=False
```

#### Running Celery Workers (Optional)

If you enable Celery, you need to run workers:

```bash
# Start Celery worker
celery -A dripemails worker -l info

# Start Celery beat (for scheduled tasks)
celery -A dripemails beat -l info
```

**Note:** 
- On Windows development with `DEBUG=True`, you can skip Redis and Celery entirely. Email sending will work synchronously.
- The application automatically detects Windows development and disables Celery - no configuration needed!
- Emails are sent immediately without queuing when Celery is disabled.
- **Scheduled emails**: When Celery is not available, scheduled emails are sent immediately instead of being queued. You'll see a message indicating that scheduling requires Celery/Redis, but the email will still be delivered successfully.

### Environment Variables

```bash
# Database
DB_NAME=dripemails
DB_USER=dripemails
DB_PASSWORD=your_password
DB_HOST=localhost

# Email (Development - No Auth)
EMAIL_HOST=localhost
EMAIL_PORT=1025                      # Default port (avoids Postfix conflicts)
EMAIL_HOST_USER=                    # Empty for no-auth
EMAIL_HOST_PASSWORD=                # Empty for no-auth
EMAIL_USE_TLS=False
DEFAULT_FROM_EMAIL=noreply@dripemails.org

# Email (Production - With Auth)
# EMAIL_HOST=localhost
# EMAIL_PORT=1025                     # Default port (use 25 for production if needed)
# EMAIL_HOST_USER=founders           # Required for production
# EMAIL_HOST_PASSWORD=secure_pass    # Required for production
# EMAIL_USE_TLS=False
# DEFAULT_FROM_EMAIL=founders@dripemails.org

# Celery (Optional)
CELERY_ENABLED=                     # Empty = auto-detect, True/False to override
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=django-db

# Redis (Optional - only needed if CELERY_ENABLED=True)
REDIS_URL=redis://localhost:6379/0

# Django
SECRET_KEY=your_secret_key
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
```

## 📊 API Documentation

DripEmails provides a comprehensive REST API for integration:

### Campaigns API
```bash
# List campaigns
GET /api/campaigns/

# Create campaign
POST /api/campaigns/
{
    "name": "Welcome Series",
    "subject": "Welcome to our platform",
    "content": "<h1>Welcome!</h1>",
    "delay_hours": 24
}

# Send campaign
POST /api/campaigns/{id}/send/
```

### Subscribers API
```bash
# List subscribers
GET /api/subscribers/

# Add subscriber
POST /api/subscribers/
{
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe"
}

# Import subscribers
POST /api/subscribers/import/
```

### Analytics API
```bash
# Get campaign analytics
GET /api/analytics/campaigns/{id}/

# Get subscriber analytics
GET /api/analytics/subscribers/

# Export analytics
GET /api/analytics/export/?format=csv
```

## 🧪 Testing

```bash
# Run all tests
python manage.py test

# Run specific app tests
python manage.py test campaigns
python manage.py test subscribers
python manage.py test analytics

# Run SMTP server tests
cd smtp_server
python -m pytest tests/
```

## 🚀 Deployment

### Production Setup

1. **Set up your server**
   ```bash
   # Install system dependencies
   sudo apt update
   sudo apt install python3.11 python3.11-venv nginx redis-server mysql-server
   ```

2. **Configure Nginx**
   ```bash
   # Copy nginx configuration
   sudo cp docs/nginx.conf /etc/nginx/sites-available/dripemails
   sudo ln -s /etc/nginx/sites-available/dripemails /etc/nginx/sites-enabled/
   ```

3. **Set up SSL**
   ```bash
   sudo certbot --nginx -d yourdomain.com
   ```

4. **Configure SMTP server**
   ```bash
   # Run SMTP server with supervisord
   sudo cp docs/supervisord.conf /etc/supervisor/conf.d/dripemails.conf
   sudo supervisorctl reread
   sudo supervisorctl update
   ```

### Docker Deployment

```bash
# Build and run with Docker Compose
docker-compose up -d

# Or build individual containers
docker build -t dripemails .
docker run -p 8000:8000 dripemails
```

## 📈 Performance

- **Email Processing**: 1000+ emails per minute
- **Database**: Optimized queries with proper indexing
- **Caching**: Redis-based caching for improved performance
- **Async Processing**: Celery for background tasks
- **CDN Ready**: Static assets optimized for CDN delivery

## 🔒 Security

- **Authentication**: Django Allauth with 2FA support
- **Email Security**: SPF, DKIM, DMARC implementation
- **Data Protection**: GDPR-compliant data handling
- **Rate Limiting**: Protection against abuse
- **Input Validation**: Comprehensive input sanitization

## 🤝 Contributing

We welcome contributions from developers around the world! Whether you're interested in contributing code, improving documentation, or adding new features, we'd love to have you join our community.

**Want to get involved?** Email us at **founders@dripemails.org** to introduce yourself and let us know what you'd like to contribute.

For contribution guidelines, please see our [Contributing Guide](CONTRIBUTING.md).

### Development Setup

1. **Fork the repository**
2. **Create a feature branch**
   ```bash
   git checkout -b feature/amazing-feature
   ```
3. **Make your changes**
4. **Run tests**
   ```bash
   python manage.py test
   ```
5. **Submit a pull request**

### Code Style

- **Python**: Follow PEP 8 with Black formatting
- **JavaScript**: ESLint with Prettier
- **CSS**: Tailwind CSS with custom components
- **Documentation**: Comprehensive docstrings and README updates

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Django**: The web framework for perfectionists with deadlines
- **aiosmtpd**: Asynchronous SMTP server implementation
- **Tailwind CSS**: Utility-first CSS framework
- **React**: JavaScript library for building user interfaces
- **Celery**: Distributed task queue

## 📞 Support

- **Documentation**: [docs.dripemails.org](https://docs.dripemails.org)
- **Issues**: [GitHub Issues](https://github.com/dripemails/web/issues)
- **Discussions**: [GitHub Discussions](https://github.com/dripemails/web/discussions)
- **Email**: founders@dripemails.org

## 🌟 Star History

[![Star History Chart](https://api.star-history.com/svg?repos=dripemails/web&type=Date)](https://star-history.com/#dripemails/web&Date)

---

**Made with ❤️ by the DripEmails Team**

*Empowering businesses to take control of their email marketing infrastructure.*
