# Simple SMTP Setup - Using Port 587 (Submission)

Since SquirrelMail works with username `founders` and password `aspen45`, you can use the same mail server configuration.

## Option 1: Use Port 587 (Submission Port with TLS)

Port 587 is the standard submission port and is often simpler to configure than port 25.

### Update your `.env` file:

```bash
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=localhost
EMAIL_PORT=587
EMAIL_HOST_USER=founders
EMAIL_HOST_PASSWORD=aspen45
EMAIL_USE_TLS=True
EMAIL_USE_SSL=False
DEFAULT_FROM_EMAIL=DripEmails <founders@dripemails.org>
```

### Check if port 587 is configured in Postfix:

```bash
# Check master.cf for submission service
sudo grep -A 10 "^submission" /etc/postfix/master.cf
```

If submission service isn't configured, you might need to enable it, but port 587 with TLS is usually simpler than port 25.

## Option 2: Use Third-Party SMTP Service (Easiest)

Services like SendGrid, Mailgun, or AWS SES are very simple to set up:

### SendGrid (Free tier: 100 emails/day)

```bash
# In your .env:
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.sendgrid.net
EMAIL_PORT=587
EMAIL_HOST_USER=apikey
EMAIL_HOST_PASSWORD=your_sendgrid_api_key
EMAIL_USE_TLS=True
DEFAULT_FROM_EMAIL=DripEmails <founders@dripemails.org>
```

### Mailgun (Free tier: 5,000 emails/month)

```bash
# In your .env:
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.mailgun.org
EMAIL_PORT=587
EMAIL_HOST_USER=postmaster@your-domain.mailgun.org
EMAIL_HOST_PASSWORD=your_mailgun_password
EMAIL_USE_TLS=True
DEFAULT_FROM_EMAIL=DripEmails <founders@dripemails.org>
```

## Option 3: Find What SquirrelMail Uses

Check SquirrelMail's configuration to see what SMTP server it uses:

```bash
# Check SquirrelMail config
sudo find /etc -name "config.php" -path "*squirrelmail*" 2>/dev/null
# or
sudo find /usr/share -name "config.php" -path "*squirrelmail*" 2>/dev/null

# Look for SMTP settings in the config
```

Then use the same settings in Django.

## Option 4: Use Your Custom SMTP Server (No Auth)

If you want to keep it simple, use your custom SMTP server without authentication:

```bash
# Run your custom SMTP server with --no-auth
python manage.py run_smtp_server --no-auth --port 1025

# In your .env:
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=localhost
EMAIL_PORT=1025
EMAIL_HOST_USER=
EMAIL_HOST_PASSWORD=
EMAIL_USE_TLS=False
DEFAULT_FROM_EMAIL=DripEmails <founders@dripemails.org>
```

But this won't send to external servers - it only receives emails locally.

## Recommendation

**Try Option 1 first** (port 587 with TLS) - it's the simplest if your mail server already supports it. If that doesn't work, **Option 2 (SendGrid/Mailgun)** is the easiest and most reliable for production.

