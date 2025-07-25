#!/usr/bin/env python
"""
Simple test script to verify the SMTP server is working.

Run this script after starting the SMTP server with:
    python manage.py run_smtp_server

This will send a test email to the local SMTP server.
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from django.conf import settings
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dripemails.settings')
django.setup()


def send_test_email():
    """Send a test email to the local SMTP server."""
    
    # Email configuration
    smtp_host = 'localhost'
    smtp_port = 1025
    
    # Create message
    msg = MIMEMultipart()
    msg['From'] = 'test@dripemails.org'
    msg['To'] = 'user@example.com'
    msg['Subject'] = 'Test Email from DripEmails'
    
    # Email body
    body = """
    Hello from DripEmails!
    
    This is a test email sent to verify that the built-in SMTP server is working correctly.
    
    Features of this setup:
    - No external SMTP service required
    - Perfect for development and testing
    - All emails are displayed in the console
    - No emails are actually sent to real recipients
    
    Best regards,
    DripEmails Team
    """
    
    msg.attach(MIMEText(body, 'plain'))
    
    try:
        # Connect to SMTP server
        server = smtplib.SMTP(smtp_host, smtp_port)
        server.set_debuglevel(1)  # Enable debug output
        
        # Send email
        text = msg.as_string()
        server.sendmail(msg['From'], msg['To'], text)
        
        print("✅ Test email sent successfully!")
        print(f"📧 From: {msg['From']}")
        print(f"📧 To: {msg['To']}")
        print(f"📧 Subject: {msg['Subject']}")
        print("\nCheck the SMTP server console to see the email content.")
        
        server.quit()
        
    except Exception as e:
        print(f"❌ Error sending test email: {e}")
        print("\nMake sure the SMTP server is running with:")
        print("python manage.py run_smtp_server")


if __name__ == '__main__':
    print("🧪 Testing DripEmails SMTP Server")
    print("=" * 40)
    send_test_email() 