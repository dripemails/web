#!/usr/bin/env python3
"""
Simple test script for DripEmails SMTP server.

This script tests basic connectivity and email sending to the SMTP server.
Run this after starting the SMTP server with: python manage.py run_smtp_server --debug --port 1027

Compatible with Python 3.11+
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import sys


def test_basic_connection(host='localhost', port=1030):
    """Test basic SMTP connection."""
    try:
        print(f"Testing connection to {host}:{port}...")
        
        # Create SMTP connection
        server = smtplib.SMTP(host, port)
        server.set_debuglevel(1)  # Enable debug output
        
        # Say hello
        server.helo('test-client')
        
        # Get server capabilities
        code, response = server.docmd('EHLO', 'test-client')
        print(f"EHLO response: {code} - {response}")
        
        server.quit()
        print("✅ Basic connection test successful!")
        return True
        
    except Exception as e:
        print(f"❌ Connection test failed: {e}")
        return False


def test_send_email(host='localhost', port=1030, from_email='test@example.com', to_email='test@dripemails.org'):
    """Test sending an email."""
    try:
        print(f"Sending test email from {from_email} to {to_email}...")
        
        # Create message
        msg = MIMEMultipart()
        msg['From'] = from_email
        msg['To'] = to_email
        msg['Subject'] = f'Test Email - {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}'
        
        # Email body
        body = f"""
        This is a test email sent to the DripEmails SMTP server.
        
        Timestamp: {datetime.now().isoformat()}
        From: {from_email}
        To: {to_email}
        
        If you see this in the SMTP server console output, the server is working correctly!
        
        Best regards,
        Test Script
        """
        
        msg.attach(MIMEText(body, 'plain'))
        
        # Send email
        server = smtplib.SMTP(host, port)
        server.set_debuglevel(1)
        
        # Send the email
        text = msg.as_string()
        server.sendmail(from_email, to_email, text)
        server.quit()
        
        print("✅ Test email sent successfully!")
        print("📧 Check the SMTP server console for the email content.")
        return True
        
    except Exception as e:
        print(f"❌ Failed to send test email: {e}")
        return False


def test_authentication(host='localhost', port=1030, username='founders', password='your_password'):
    """Test authentication (optional)."""
    try:
        print(f"Testing authentication for user: {username}")
        
        # Create SMTP connection
        server = smtplib.SMTP(host, port)
        server.set_debuglevel(1)
        
        # Try to authenticate
        try:
            server.login(username, password)
            print("✅ Authentication successful!")
            server.quit()
            return True
        except smtplib.SMTPAuthenticationError as e:
            print(f"❌ Authentication failed: {e}")
            server.quit()
            return False
            
    except Exception as e:
        print(f"❌ Authentication test error: {e}")
        return False


def main():
    """Run all tests."""
    print("🧪 DripEmails SMTP Server Test Suite")
    print("=" * 50)
    
    # Configuration
    host = 'localhost'
    port = 1030  # Use the port where your server is running
    
    print(f"Testing SMTP server on {host}:{port}")
    print("Make sure the server is running with: python manage.py run_smtp_server --debug --port 1030 --no-auth")
    print()
    
    # Run tests
    tests = [
        ("Basic Connection", lambda: test_basic_connection(host, port)),
        ("Send Test Email", lambda: test_send_email(host, port)),
    ]
    
    # Optional authentication test
    if len(sys.argv) > 1 and sys.argv[1] == '--auth':
        password = input("Enter founders password for authentication test: ")
        if password:
            tests.append(("Authentication", lambda: test_authentication(host, port, 'founders', password)))
    
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
        print("\n💡 Next steps:")
        print("- The server is ready to receive emails")
        print("- Check the server console for incoming email content")
        print("- You can now configure Django to use this SMTP server")
    else:
        print("⚠️  Some tests failed. Check the configuration.")
    
    print("\n💡 Tips:")
    print("- Make sure the SMTP server is running: python manage.py run_smtp_server --debug --port 1030 --no-auth")
    print("- Check the server console for detailed logs")
    print("- Use --auth flag to test authentication: python test_smtp_simple.py --auth")


if __name__ == "__main__":
    main() 