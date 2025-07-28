# Quick Start: Custom SMTP Server

Get your custom SMTP server running in 5 minutes!

## Prerequisites

- Python 3.12.3+
- Django project set up
- Database configured
- Founders user account created

## Step 1: Install Dependencies

```bash
pip install -r requirements.txt
```

## Step 2: Run Database Migration

```bash
python manage.py makemigrations core
python manage.py migrate
```

## Step 3: Create Founders Account

Create the founders user account for SMTP authentication:

```bash
python manage.py createsuperuser --username founders
```

## Step 4: Start the SMTP Server

```bash
# Basic start with authentication (requires root for port 25)
sudo python manage.py run_smtp_server

# Alternative: Use a different port (no root required)
python manage.py run_smtp_server --port 1025

# Production start with authentication (requires root for port 25)
sudo python manage.py run_smtp_server --host 0.0.0.0 --port 25 --save-to-db

# Disable authentication (allow anonymous access)
python manage.py run_smtp_server --no-auth
```

## Step 5: Test Authentication

Test the SMTP authentication with the founders account:

```bash
# Test authentication
python test_smtp_auth.py

# Test basic functionality
python test_smtp_server.py
```

## Step 6: Configure Django Email Settings

Update your Django settings (`settings.py` or `live.py`):

```python
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'localhost'
EMAIL_PORT = 25  # Standard SMTP port (no SSL required)
EMAIL_USE_TLS = False
EMAIL_USE_SSL = False
EMAIL_HOST_USER = 'founders'  # Use founders account for authentication
EMAIL_HOST_PASSWORD = 'your_founders_password'  # Founders password
DEFAULT_FROM_EMAIL = 'founders@dripemails.org'
```

## Step 7: Test Email Sending

```python
from django.core.mail import send_mail

send_mail(
    'Test Email',
    'This is a test email from DripEmails!',
    'founders@dripemails.org',
    ['test@example.com'],
    fail_silently=False,
)
```

## That's it! 🎉

Your custom SMTP server is now running with authentication and ready to handle emails.

## Authentication Features

✅ **Founders Account** - Authenticate with the founders user  
✅ **PLAIN Authentication** - Standard SMTP authentication  
✅ **LOGIN Authentication** - Alternative authentication method  
✅ **Security** - Unauthorized users cannot send emails  
✅ **Django Integration** - Uses Django's user authentication system  

## Next Steps

- Check the [full documentation](smtp_server_setup.md) for advanced features
- Set up production deployment with systemd or supervisord
- Configure webhooks and monitoring
- Set up proper firewall rules for port 25

## Troubleshooting

**Server won't start?**
- Check if port is already in use: `netstat -tlnp | grep :25`
- Ensure you have the required permissions (root for port 25)
- Verify Python version: `python --version` (should be 3.12.3+)

**Authentication fails?**
- Ensure the founders user exists: `python manage.py shell -c "from django.contrib.auth.models import User; print(User.objects.filter(username='founders').exists())"`
- Check the password is correct
- Verify authentication is enabled (not using --no-auth)

**Permission denied on port 25?**
- Use `sudo` to run the server: `sudo python manage.py run_smtp_server`
- Or use a different port: `python manage.py run_smtp_server --port 1025`

**Emails not being received?**
- Check server logs: `tail -f logs/django.log`
- Verify Django email settings
- Test with the provided test script

**Database errors?**
- Run migrations: `python manage.py migrate`
- Check database connection settings

**Python compatibility issues?**
- Ensure you're using Python 3.12.3 or higher
- Check aiosmtpd version: `pip show aiosmtpd`

## Port 25 Considerations

- **Root privileges required**: Port 25 is a privileged port on most systems
- **Firewall configuration**: Ensure port 25 is open in your firewall
- **ISP restrictions**: Some ISPs block port 25 for residential connections
- **Alternative ports**: Use port 1025 or 587 for development without root privileges

## Authentication Commands

```bash
# Start with specific allowed users
python manage.py run_smtp_server --allowed-users founders admin

# Disable authentication
python manage.py run_smtp_server --no-auth

# Test authentication
python test_smtp_auth.py
``` 