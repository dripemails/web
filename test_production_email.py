#!/usr/bin/env python
"""
Production Email Server Test Script for DripEmails

This script tests the production Postfix email server to ensure it can send real emails.
Run this after setting up your Postfix server.

Usage:
    python test_production_email.py
"""

import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from django.conf import settings
import os
import django
import sys

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dripemails.live')
django.setup()


def test_production_email():
    """Test sending email through the production Postfix server."""
    
    # Get email configuration from Django settings
    smtp_host = getattr(settings, 'EMAIL_HOST', 'localhost')
    smtp_port = getattr(settings, 'EMAIL_PORT', 587)
    smtp_user = getattr(settings, 'EMAIL_HOST_USER', 'noreply@dripemails.org')
    smtp_password = getattr(settings, 'EMAIL_HOST_PASSWORD', '')
    use_tls = getattr(settings, 'EMAIL_USE_TLS', True)
    use_ssl = getattr(settings, 'EMAIL_USE_SSL', False)
    
    print("🧪 Testing Production Email Server")
    print("=" * 50)
    print(f"SMTP Host: {smtp_host}")
    print(f"SMTP Port: {smtp_port}")
    print(f"SMTP User: {smtp_user}")
    print(f"Use TLS: {use_tls}")
    print(f"Use SSL: {use_ssl}")
    print("=" * 50)
    
    # Get test recipient
    test_recipient = input("Enter test email address: ").strip()
    if not test_recipient:
        print("❌ No email address provided")
        return False
    
    # Create message
    msg = MIMEMultipart()
    msg['From'] = smtp_user
    msg['To'] = test_recipient
    msg['Subject'] = 'DripEmails Production Email Test'
    
    # Email body
    body = f"""
    Hello from DripEmails Production Server!
    
    This is a test email sent from your production Postfix email server.
    
    Server Details:
    - SMTP Host: {smtp_host}
    - SMTP Port: {smtp_port}
    - TLS Enabled: {use_tls}
    - SSL Enabled: {use_ssl}
    
    If you received this email, your production email server is working correctly!
    
    Features:
    ✅ Real email delivery
    ✅ TLS encryption
    ✅ DKIM signing (if configured)
    ✅ SPF/DMARC support
    ✅ Production-ready
    
    Best regards,
    DripEmails Production Server
    """
    
    msg.attach(MIMEText(body, 'plain'))
    
    try:
        # Create SMTP connection
        if use_ssl:
            server = smtplib.SMTP_SSL(smtp_host, smtp_port)
        else:
            server = smtplib.SMTP(smtp_host, smtp_port)
        
        # Enable debug output
        server.set_debuglevel(1)
        
        # Start TLS if required
        if use_tls and not use_ssl:
            server.starttls(context=ssl.create_default_context())
        
        # Authenticate if credentials provided
        if smtp_user and smtp_password:
            server.login(smtp_user, smtp_password)
            print("✅ SMTP authentication successful")
        
        # Send email
        text = msg.as_string()
        server.sendmail(msg['From'], msg['To'], text)
        
        print("✅ Production email sent successfully!")
        print(f"📧 From: {msg['From']}")
        print(f"📧 To: {msg['To']}")
        print(f"📧 Subject: {msg['Subject']}")
        print("\n🎉 Your production email server is working!")
        print("Check the recipient's inbox for the test email.")
        
        server.quit()
        return True
        
    except smtplib.SMTPAuthenticationError as e:
        print(f"❌ SMTP Authentication Error: {e}")
        print("\n💡 If you're using local Postfix without authentication, try:")
        print("   - Set EMAIL_HOST_USER='' in your .env file")
        print("   - Set EMAIL_HOST_PASSWORD='' in your .env file")
        return False
        
    except smtplib.SMTPConnectError as e:
        print(f"❌ SMTP Connection Error: {e}")
        print("\n💡 Make sure:")
        print("   - Postfix server is running")
        print("   - Port 587 is open")
        print("   - Firewall allows SMTP traffic")
        return False
        
    except smtplib.SMTPRecipientsRefused as e:
        print(f"❌ SMTP Recipients Refused: {e}")
        print("\n💡 Check:")
        print("   - Email address is valid")
        print("   - DNS records are configured")
        print("   - Server reputation is good")
        return False
        
    except Exception as e:
        print(f"❌ Unexpected Error: {e}")
        print(f"Error Type: {type(e).__name__}")
        return False


def test_django_email():
    """Test Django's email sending functionality."""
    
    print("\n🧪 Testing Django Email Functionality")
    print("=" * 50)
    
    try:
        from django.core.mail import send_mail
        
        test_recipient = input("Enter test email address for Django test: ").strip()
        if not test_recipient:
            print("❌ No email address provided")
            return False
        
        # Send email using Django
        result = send_mail(
            subject='DripEmails Django Email Test',
            message='This is a test email sent using Django\'s send_mail function.',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[test_recipient],
            fail_silently=False,
        )
        
        if result:
            print("✅ Django email sent successfully!")
            print(f"📧 To: {test_recipient}")
            return True
        else:
            print("❌ Django email failed")
            return False
            
    except Exception as e:
        print(f"❌ Django Email Error: {e}")
        return False


def check_email_config():
    """Check current email configuration."""
    
    print("\n🔍 Current Email Configuration")
    print("=" * 50)
    print(f"EMAIL_BACKEND: {getattr(settings, 'EMAIL_BACKEND', 'Not set')}")
    print(f"EMAIL_HOST: {getattr(settings, 'EMAIL_HOST', 'Not set')}")
    print(f"EMAIL_PORT: {getattr(settings, 'EMAIL_PORT', 'Not set')}")
    print(f"EMAIL_HOST_USER: {getattr(settings, 'EMAIL_HOST_USER', 'Not set')}")
    print(f"EMAIL_USE_TLS: {getattr(settings, 'EMAIL_USE_TLS', 'Not set')}")
    print(f"EMAIL_USE_SSL: {getattr(settings, 'EMAIL_USE_SSL', 'Not set')}")
    print(f"DEFAULT_FROM_EMAIL: {getattr(settings, 'DEFAULT_FROM_EMAIL', 'Not set')}")


if __name__ == '__main__':
    print("🚀 DripEmails Production Email Server Test")
    print("=" * 60)
    
    # Check configuration
    check_email_config()
    
    # Test direct SMTP
    print("\n" + "=" * 60)
    smtp_success = test_production_email()
    
    # Test Django email
    print("\n" + "=" * 60)
    django_success = test_django_email()
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Test Results Summary")
    print("=" * 60)
    print(f"SMTP Test: {'✅ PASS' if smtp_success else '❌ FAIL'}")
    print(f"Django Test: {'✅ PASS' if django_success else '❌ FAIL'}")
    
    if smtp_success and django_success:
        print("\n🎉 All tests passed! Your production email server is ready.")
    else:
        print("\n⚠️  Some tests failed. Check the configuration and try again.")
        print("\n💡 Troubleshooting tips:")
        print("   - Ensure Postfix is running: systemctl status postfix")
        print("   - Check mail logs: tail -f /var/log/mail.log")
        print("   - Verify DNS records are configured")
        print("   - Test SMTP manually: telnet localhost 587") 