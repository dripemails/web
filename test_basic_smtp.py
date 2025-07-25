#!/usr/bin/env python3
"""
Simple test for basic aiosmtpd server.
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime


def test_basic_smtp(host='localhost', port=1031):
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


def test_send_email(host='localhost', port=1031):
    """Test sending an email."""
    try:
        print(f"Sending test email...")
        
        # Create message
        msg = MIMEMultipart()
        msg['From'] = 'test@example.com'
        msg['To'] = 'test@dripemails.org'
        msg['Subject'] = f'Basic Test Email - {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}'
        
        # Email body
        body = f"""
        This is a basic test email sent to the aiosmtpd server.
        
        Timestamp: {datetime.now().isoformat()}
        
        If you see this in the server console output, the basic server is working!
        
        Best regards,
        Test Script
        """
        
        msg.attach(MIMEText(body, 'plain'))
        
        # Send email
        server = smtplib.SMTP(host, port)
        server.set_debuglevel(1)
        
        # Send the email
        text = msg.as_string()
        server.sendmail('test@example.com', 'test@dripemails.org', text)
        server.quit()
        
        print("✅ Test email sent successfully!")
        print("📧 Check the server console for the email content.")
        return True
        
    except Exception as e:
        print(f"❌ Failed to send test email: {e}")
        return False


def main():
    """Run basic tests."""
    print("🧪 Basic aiosmtpd Test Suite")
    print("=" * 40)
    
    # Configuration
    host = 'localhost'
    port = 1031
    
    print(f"Testing basic aiosmtpd server on {host}:{port}")
    print("Make sure the basic server is running with: python test_basic_aiosmtpd.py")
    print()
    
    # Run tests
    tests = [
        ("Basic Connection", lambda: test_basic_smtp(host, port)),
        ("Send Test Email", lambda: test_send_email(host, port)),
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
    print("\n" + "=" * 40)
    print("📊 Test Results Summary")
    print("=" * 40)
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("🎉 All tests passed! The basic aiosmtpd server is working correctly.")
    else:
        print("⚠️  Some tests failed. Check the configuration.")


if __name__ == "__main__":
    main() 