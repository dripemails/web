# DripEmails.org - Modern Email Marketing Platform

[![Python](https://img.shields.io/badge/Python-3.11%2B-blue.svg)](https://www.python.org/downloads/)
[![Django](https://img.shields.io/badge/Django-4.0%2B-green.svg)](https://www.djangoproject.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![PyPI](https://img.shields.io/badge/PyPI-dripemails--smtp--server-blue.svg)](https://pypi.org/project/dripemails-smtp-server/)

> **A modern, open-source email marketing platform built with Django and Python 3.11+**

DripEmails.org is a comprehensive email marketing solution that combines powerful drip campaign management, subscriber analytics, and a custom SMTP server. Built with modern web technologies and designed for scalability, it's perfect for businesses looking to take control of their email marketing infrastructure.

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
- **MySQL/PostgreSQL** database
- **Redis** (for caching and Celery)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/dripemails/web.git
   cd web
   ```

2. **Set up Python environment**
   ```bash
   python -m dripemails dripemails
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

8. **Start the SMTP server** (optional)
   ```bash
   python manage.py run_smtp_server --debug --port 1025
   ```

## 📧 SMTP Server Component

DripEmails includes a custom SMTP server built with `aiosmtpd`. You can use it standalone or as part of the full platform.

### Quick SMTP Server Setup

```bash
# Install the standalone SMTP server
pip install dripemails-smtp-server

# Run the server
dripemails-smtp --port 25 --debug
```

### SMTP Server Features
- **Async Performance**: Built with `aiosmtpd` for high performance
- **Authentication**: PLAIN and LOGIN authentication support
- **Rate Limiting**: Built-in spam protection
- **Webhook Integration**: Real-time email processing
- **Django Integration**: Seamless database integration

For detailed SMTP server documentation, see [docs/smtp_server_production_setup.md](docs/smtp_server_production_setup.md).

## 🔧 Configuration

### Django Settings

```python
# Email Configuration
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'localhost'
EMAIL_PORT = 25
EMAIL_HOST_USER = 'your_username'
EMAIL_HOST_PASSWORD = 'your_password'
DEFAULT_FROM_EMAIL = 'noreply@yourdomain.com'

# SMTP Server Configuration
SMTP_SERVER_CONFIG = {
    'host': 'localhost',
    'port': 25,
    'auth_enabled': True,
    'allowed_domains': ['yourdomain.com'],
    'max_message_size': 10485760,  # 10MB
    'rate_limit': 100,  # emails per minute
}
```

### Environment Variables

```bash
# Database
DB_NAME=dripemails
DB_USER=dripemails
DB_PASSWORD=your_password
DB_HOST=localhost

# Email
EMAIL_HOST=localhost
EMAIL_PORT=25
EMAIL_HOST_USER=your_username
EMAIL_HOST_PASSWORD=your_password

# Redis
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

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

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
