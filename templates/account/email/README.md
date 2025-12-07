# Django Allauth Email Templates

This directory contains custom email templates for django-allauth that override the default templates. All templates use `{{current_site.name}}` and `{{current_site.domain}}` for dynamic site information.

## Templates

### Base Templates
- **base_message.txt** - Base text template used by all email messages
- **base_message.html** - Base HTML template with styled design (gradient header, modern styling)

### Account Already Exists
- **account_already_exists_subject.txt** - Subject for "account already exists" emails
- **account_already_exists_message.txt** - Text message body
- **account_already_exists_message.html** - Styled HTML message body

### Email Confirmation
- **email_confirmation_subject.txt** - Subject for email confirmation emails
- **email_confirmation_message.txt** - Text message body
- **email_confirmation_message.html** - Styled HTML message body
- **email_confirmation_signup_subject.txt** - Subject for signup confirmation emails
- **email_confirmation_signup_message.txt** - Text message body (extends email_confirmation)
- **email_confirmation_signup_message.html** - Styled HTML message body (extends email_confirmation)

### Password Reset
- **password_reset_key_subject.txt** - Subject for password reset emails
- **password_reset_key_message.txt** - Text message body
- **password_reset_key_message.html** - Styled HTML message body

### Unknown Account
- **unknown_account_subject.txt** - Subject for unknown account emails
- **unknown_account_message.txt** - Text message body
- **unknown_account_message.html** - Styled HTML message body

## Features

### Dynamic Site Information
All templates use:
- `{{current_site.name}}` - Site name (e.g., "DripEmails.org")
- `{{current_site.domain}}` - Site domain (e.g., "dripemails.org")

### Styled HTML Emails
The HTML templates include:
- Modern gradient header (purple/indigo)
- Clean, responsive design
- Styled buttons with hover effects
- Highlight boxes for important information
- Professional footer with site information
- Mobile-friendly layout

### Available Variables
- `{{ email }}` - Email address
- `{{ user_display }}` - User display name
- `{{ activate_url }}` - Email confirmation URL
- `{{ password_reset_url }}` - Password reset URL
- `{{ signup_url }}` - Signup URL
- `{{ username }}` - Username (if applicable)
- `{{ current_site }}` - Current site object

## Customization

To customize the styling, edit `base_message.html`. The design uses:
- Gradient colors: `#667eea` to `#764ba2`
- Font: System font stack for best compatibility
- Responsive: Works on all email clients

To customize content, edit the individual template files.

## Testing

After making changes:
1. Restart Django/Gunicorn
2. Trigger a signup, password reset, or email confirmation
3. Check the email that is sent
4. Verify the content and styling match your changes

## Note

Django-allauth will automatically use HTML templates if they exist, falling back to text templates. Both are provided for maximum compatibility.
