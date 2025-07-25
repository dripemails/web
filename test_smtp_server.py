#!/usr/bin/env python3
"""
Test script for the DripEmails SMTP server.

This script tests the custom SMTP server by sending test emails.
Run this after starting the SMTP server with: python manage.py run_smtp_server

Compatible with Python 3.12.3+
"""

import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import sys


def check_python_version():
    """Check if Python version is compatible."""
    if sys.version_info < (3, 12):
        print("❌ This script requires Python 3.12.3 or higher")
        print(f"   Current version: {sys.version}")
        return False
    print(f"✅ Python version: {sys.version}")
    return True


def test_smtp_connection(host='localhost', port=25):
    """Test basic SMTP connection."""
    try:
        print(f"Testing SMTP connection to {host}:{port}...")
        
        # Create SMTP connection
        server = smtplib.SMTP(host, port)
        server.set_debuglevel(1)  # Enable debug output
        
        # Test connection
        server.helo('test-client')
        print("✅ SMTP connection successful!")
        
        server.quit()
        return True
        
    except Exception as e:
        print(f"❌ SMTP connection failed: {e}")
        return False


def send_test_email(host='localhost', port=25, from_email='test@example.com', to_email='test@dripemails.org'):
    """Send a test email through the SMTP server."""
    try:
        print(f"Sending test email from {from_email} to {to_email}...")
        
        # Create message
        msg = MIMEMultipart()
        msg['From'] = from_email
        msg['To'] = to_email
        msg['Subject'] = f'Test Email - {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}'
        
        # Email body
        body = f"""
        This is a test email sent to verify the DripEmails SMTP server.
        
        Timestamp: {datetime.now().isoformat()}
        From: {from_email}
        To: {to_email}
        Python Version: {sys.version}
        
        If you receive this email, the SMTP server is working correctly!
        
        Best regards,
        DripEmails Test Suite
        """
        
        msg.attach(MIMEText(body, 'plain'))
        
        # Send email
        server = smtplib.SMTP(host, port)
        server.set_debuglevel(1)
        
        text = msg.as_string()
        server.sendmail(from_email, to_email, text)
        server.quit()
        
        print("✅ Test email sent successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Failed to send test email: {e}")
        return False


def send_html_email(host='localhost', port=25, from_email='test@example.com', to_email='test@dripemails.org'):
    """Send an HTML test email."""
    try:
        print(f"Sending HTML test email from {from_email} to {to_email}...")
        
        # Create message
        msg = MIMEMultipart('alternative')
        msg['From'] = from_email
        msg['To'] = to_email
        msg['Subject'] = f'HTML Test Email - {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}'
        
        # Plain text version
        text = f"""
        This is a test email with HTML content.
        
        Timestamp: {datetime.now().isoformat()}
        From: {from_email}
        To: {to_email}
        Python Version: {sys.version}
        
        If you see this plain text, your email client doesn't support HTML.
        """
        
        # HTML version
        html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background-color: #f0f0f0; padding: 10px; border-radius: 5px; }}
                .content {{ margin: 20px 0; }}
                .footer {{ color: #666; font-size: 12px; }}
                .version {{ background-color: #e8f4f8; padding: 5px; border-radius: 3px; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h2>🎉 DripEmails SMTP Server Test</h2>
            </div>
            <div class="content">
                <p>This is a <strong>test email</strong> with HTML content to verify the SMTP server.</p>
                <ul>
                    <li><strong>Timestamp:</strong> {datetime.now().isoformat()}</li>
                    <li><strong>From:</strong> {from_email}</li>
                    <li><strong>To:</strong> {to_email}</li>
                    <li class="version"><strong>Python Version:</strong> {sys.version}</li>
                </ul>
                <p>If you see this HTML content, the SMTP server is working correctly!</p>
            </div>
            <div class="footer">
                <p>Best regards,<br>DripEmails Test Suite</p>
            </div>
        </body>
        </html>
        """
        
        # Attach both versions
        part1 = MIMEText(text, 'plain')
        part2 = MIMEText(html, 'html')
        
        msg.attach(part1)
        msg.attach(part2)
        
        # Send email
        server = smtplib.SMTP(host, port)
        server.set_debuglevel(1)
        
        text = msg.as_string()
        server.sendmail(from_email, to_email, text)
        server.quit()
        
        print("✅ HTML test email sent successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Failed to send HTML test email: {e}")
        return False


def test_rate_limiting(host='localhost', port=25, from_email='test@example.com', to_email='test@dripemails.org'):
    """Test rate limiting by sending multiple emails quickly."""
    print("Testing rate limiting...")
    
    success_count = 0
    for i in range(5):
        try:
            msg = MIMEText(f"Rate limit test email #{i+1}")
            msg['From'] = from_email
            msg['To'] = to_email
            msg['Subject'] = f'Rate Limit Test #{i+1}'
            
            server = smtplib.SMTP(host, port)
            server.sendmail(from_email, to_email, msg.as_string())
            server.quit()
            
            success_count += 1
            print(f"  ✅ Email {i+1} sent")
            
        except Exception as e:
            print(f"  ❌ Email {i+1} failed: {e}")
            break
    
    print(f"Rate limiting test completed: {success_count}/5 emails sent")
    return success_count


def main():
    """Run all SMTP tests."""
    print("🧪 DripEmails SMTP Server Test Suite")
    print("=" * 50)
    
    # Check Python version first
    if not check_python_version():
        sys.exit(1)
    
    # Configuration
    host = 'localhost'
    port = 25
    from_email = 'test@example.com'
    to_email = 'test@dripemails.org'
    
    print(f"Testing SMTP server on {host}:{port}")
    print(f"From: {from_email}")
    print(f"To: {to_email}")
    print()
    
    # Run tests
    tests = [
        ("SMTP Connection", lambda: test_smtp_connection(host, port)),
        ("Plain Text Email", lambda: send_test_email(host, port, from_email, to_email)),
        ("HTML Email", lambda: send_html_email(host, port, from_email, to_email)),
        ("Rate Limiting", lambda: test_rate_limiting(host, port, from_email, to_email)),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n🔍 Running: {test_name}")
        print("-" * 30)
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Results Summary")
    print("=" * 50)
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("🎉 All tests passed! The SMTP server is working correctly.")
    else:
        print("⚠️  Some tests failed. Check the SMTP server configuration.")
    
    print("\n💡 Tips:")
    print("- Make sure the SMTP server is running: python manage.py run_smtp_server")
    print("- Check the server logs for any error messages")
    print("- Verify the port is not blocked by firewall")
    print("- Ensure the database is properly configured if using --save-to-db")
    print("- Confirm Python 3.12.3+ is being used")
    print("- Note: Port 25 requires root privileges on some systems")


if __name__ == "__main__":
    main() 