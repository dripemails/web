#!/usr/bin/env python3
"""
Test script for DripEmails SMTP server authentication.

This script tests the SMTP server authentication using the founders account.
Run this after starting the SMTP server with: python manage.py run_smtp_server

Compatible with Python 3.12.3+
"""

import smtplib
import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import sys


def test_smtp_authentication(host='localhost', port=25, username='founders', password='your_password'):
    """Test SMTP authentication with the founders account."""
    try:
        print(f"Testing SMTP authentication on {host}:{port}...")
        print(f"Username: {username}")
        
        # Create SMTP connection
        server = smtplib.SMTP(host, port)
        server.set_debuglevel(1)  # Enable debug output
        
        # Say hello
        server.helo('test-client')
        
        # Check if authentication is supported
        print("Checking authentication capabilities...")
        code, response = server.docmd('EHLO', 'test-client')
        print(f"EHLO response: {code} - {response}")
        
        # Try to authenticate
        print(f"Attempting authentication for user: {username}")
        try:
            server.login(username, password)
            print("✅ Authentication successful!")
            return True
        except smtplib.SMTPAuthenticationError as e:
            print(f"❌ Authentication failed: {e}")
            return False
        except Exception as e:
            print(f"❌ Authentication error: {e}")
            return False
        finally:
            server.quit()
        
    except Exception as e:
        print(f"❌ SMTP connection failed: {e}")
        return False


def send_authenticated_email(host='localhost', port=25, username='founders', password='your_password', 
                           from_email='founders@dripemails.org', to_email='test@dripemails.org'):
    """Send an email using authentication."""
    try:
        print(f"Sending authenticated email from {from_email} to {to_email}...")
        
        # Create message
        msg = MIMEMultipart()
        msg['From'] = from_email
        msg['To'] = to_email
        msg['Subject'] = f'Authenticated Test Email - {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}'
        
        # Email body
        body = f"""
        This is a test email sent using SMTP authentication.
        
        Timestamp: {datetime.now().isoformat()}
        From: {from_email}
        To: {to_email}
        Authenticated User: {username}
        
        This email was sent using authenticated SMTP access.
        
        Best regards,
        DripEmails Founders
        """
        
        msg.attach(MIMEText(body, 'plain'))
        
        # Send email with authentication
        server = smtplib.SMTP(host, port)
        server.set_debuglevel(1)
        
        # Authenticate
        server.login(username, password)
        
        # Send the email
        text = msg.as_string()
        server.sendmail(from_email, to_email, text)
        server.quit()
        
        print("✅ Authenticated email sent successfully!")
        return True
        
    except smtplib.SMTPAuthenticationError as e:
        print(f"❌ Authentication failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Failed to send authenticated email: {e}")
        return False


def test_plain_authentication(host='localhost', port=25, username='founders', password='your_password'):
    """Test PLAIN authentication mechanism."""
    try:
        print(f"Testing PLAIN authentication for user: {username}")
        
        # Create SMTP connection
        server = smtplib.SMTP(host, port)
        server.set_debuglevel(1)
        
        # Say hello
        server.helo('test-client')
        
        # Create PLAIN authentication credentials
        credentials = f'\0{username}\0{password}'
        encoded_credentials = base64.b64encode(credentials.encode('utf-8')).decode('utf-8')
        
        # Send AUTH PLAIN command
        code, response = server.docmd('AUTH', f'PLAIN {encoded_credentials}')
        print(f"AUTH PLAIN response: {code} - {response}")
        
        if code == 235:
            print("✅ PLAIN authentication successful!")
            server.quit()
            return True
        else:
            print(f"❌ PLAIN authentication failed: {response}")
            server.quit()
            return False
            
    except Exception as e:
        print(f"❌ PLAIN authentication error: {e}")
        return False


def test_login_authentication(host='localhost', port=25, username='founders', password='your_password'):
    """Test LOGIN authentication mechanism."""
    try:
        print(f"Testing LOGIN authentication for user: {username}")
        
        # Create SMTP connection
        server = smtplib.SMTP(host, port)
        server.set_debuglevel(1)
        
        # Say hello
        server.helo('test-client')
        
        # Encode username and password
        encoded_username = base64.b64encode(username.encode('utf-8')).decode('utf-8')
        encoded_password = base64.b64encode(password.encode('utf-8')).decode('utf-8')
        
        # Send AUTH LOGIN command
        code, response = server.docmd('AUTH', f'LOGIN {encoded_username}')
        print(f"AUTH LOGIN username response: {code} - {response}")
        
        if code == 334:
            # Send password
            code, response = server.docmd(encoded_password)
            print(f"AUTH LOGIN password response: {code} - {response}")
            
            if code == 235:
                print("✅ LOGIN authentication successful!")
                server.quit()
                return True
            else:
                print(f"❌ LOGIN authentication failed: {response}")
                server.quit()
                return False
        else:
            print(f"❌ LOGIN authentication failed at username step: {response}")
            server.quit()
            return False
            
    except Exception as e:
        print(f"❌ LOGIN authentication error: {e}")
        return False


def test_unauthorized_access(host='localhost', port=25):
    """Test that unauthorized users cannot send emails."""
    try:
        print("Testing unauthorized access (should fail)...")
        
        # Create SMTP connection
        server = smtplib.SMTP(host, port)
        server.set_debuglevel(1)
        
        # Say hello
        server.helo('test-client')
        
        # Try to send email without authentication
        msg = MIMEText("This should fail without authentication")
        msg['From'] = 'unauthorized@example.com'
        msg['To'] = 'test@dripemails.org'
        msg['Subject'] = 'Unauthorized Test'
        
        try:
            server.sendmail('unauthorized@example.com', 'test@dripemails.org', msg.as_string())
            print("❌ Unauthorized access succeeded (this should have failed)")
            server.quit()
            return False
        except smtplib.SMTPResponseException as e:
            if e.smtp_code == 530:
                print("✅ Unauthorized access correctly blocked")
                server.quit()
                return True
            else:
                print(f"❌ Unexpected error for unauthorized access: {e}")
                server.quit()
                return False
                
    except Exception as e:
        print(f"❌ Unauthorized access test error: {e}")
        return False


def main():
    """Run all SMTP authentication tests."""
    print("🔐 DripEmails SMTP Authentication Test Suite")
    print("=" * 60)
    
    # Configuration
    host = 'localhost'
    port = 25
    username = 'founders'
    password = 'your_password'  # Replace with actual password
    
    print(f"Testing SMTP authentication on {host}:{port}")
    print(f"Username: {username}")
    print("Note: Replace 'your_password' with the actual founders password")
    print()
    
    # Get password from user if not provided
    if password == 'your_password':
        password = input("Enter the founders password: ")
        if not password:
            print("❌ No password provided. Exiting.")
            sys.exit(1)
    
    # Run tests
    tests = [
        ("SMTP Authentication", lambda: test_smtp_authentication(host, port, username, password)),
        ("PLAIN Authentication", lambda: test_plain_authentication(host, port, username, password)),
        ("LOGIN Authentication", lambda: test_login_authentication(host, port, username, password)),
        ("Authenticated Email", lambda: send_authenticated_email(host, port, username, password)),
        ("Unauthorized Access", lambda: test_unauthorized_access(host, port)),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n🔍 Running: {test_name}")
        print("-" * 40)
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Authentication Test Results Summary")
    print("=" * 60)
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("🎉 All authentication tests passed! The SMTP server is working correctly.")
    else:
        print("⚠️  Some authentication tests failed. Check the configuration.")
    
    print("\n💡 Tips:")
    print("- Make sure the SMTP server is running: python manage.py run_smtp_server")
    print("- Ensure the 'founders' user exists in Django with correct password")
    print("- Check that authentication is enabled (not using --no-auth)")
    print("- Verify the server logs for authentication attempts")
    print("- Use 'python manage.py createsuperuser' to create the founders account")


if __name__ == "__main__":
    main() 