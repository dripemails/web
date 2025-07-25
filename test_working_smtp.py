#!/usr/bin/env python3
"""
Simple test script to verify the current working state of the SMTP server.

This script tests the basic functionality without the session.peer issues.
"""

import asyncio
import logging
from aiosmtpd.controller import Controller
from aiosmtpd.smtp import SMTP
from aiosmtpd.handlers import Message
from email import message_from_bytes
from email.policy import default


class SimpleMessageHandler(Message):
    """Simple message handler for testing."""
    
    def handle_message(self, message: bytes):
        """Handle received email message."""
        try:
            # Parse the email message
            email_message = message_from_bytes(message, policy=default)
            
            print('=' * 60)
            print('📧 NEW EMAIL RECEIVED')
            print('=' * 60)
            print(f'📤 From: {email_message.get("from", "Unknown")}')
            print(f'📥 To: {email_message.get("to", "Unknown")}')
            print(f'📋 Subject: {email_message.get("subject", "No Subject")}')
            print('-' * 60)
            print('📄 Email Content:')
            print('-' * 60)
            
            # Extract body
            body = ""
            if email_message.is_multipart():
                for part in email_message.walk():
                    if part.get_content_type() == "text/plain":
                        body = part.get_content()
                        print(body[:500] + ('...' if len(body) > 500 else ''))
                        break
                    elif part.get_content_type() == "text/html":
                        if not body:
                            body = part.get_content()
                            print(body[:500] + ('...' if len(body) > 500 else ''))
            else:
                body = email_message.get_content()
                print(body[:500] + ('...' if len(body) > 500 else ''))
            
            print('=' * 60)
            print()
            
        except Exception as e:
            print(f"Error handling message: {e}")


def main():
    """Run simple SMTP server test."""
    print("🧪 Simple SMTP Server Test")
    print("=" * 40)
    
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create handler and server
    handler = SimpleMessageHandler()
    smtp_server = SMTP(handler)
    
    # Create controller
    controller = Controller(
        smtp_server,
        hostname='localhost',
        port=1032
    )
    
    try:
        # Start server
        controller.start()
        print("✅ Simple SMTP server started on localhost:1032")
        print("📧 Ready to receive emails...")
        print("⏹️  Press Ctrl+C to stop")
        
        # Keep running
        try:
            while True:
                import time
                time.sleep(1)
        except KeyboardInterrupt:
            pass
            
    except Exception as e:
        print(f"❌ Error starting server: {e}")
    finally:
        controller.stop()
        print("🛑 Server stopped")


if __name__ == "__main__":
    main() 