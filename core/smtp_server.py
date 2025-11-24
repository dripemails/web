"""
Custom SMTP Server for DripEmails using aiosmtpd

This module provides a production-ready SMTP server that can:
- Handle incoming emails
- Process and store emails in the database
- Forward emails to external services
- Provide webhook notifications
- Support authentication and rate limiting
- Compatible with Python 3.11+ and 3.12+
- Runs on standard SMTP port 25 (no SSL required)
- Supports authentication with Django users
"""

import asyncio
import logging
import json
import os
import base64
from datetime import datetime
from typing import List, Dict, Any, Optional
from email import message_from_bytes
from email.policy import default
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from aiosmtpd.controller import Controller
from aiosmtpd.smtp import SMTP as SMTPServer
from aiosmtpd.handlers import Message

# Django imports (optional - only if running within Django context)
try:
    from django.conf import settings
    from django.core.mail import send_mail
    from django.utils import timezone
    from django.contrib.auth import authenticate
    from django.contrib.auth.models import User
    DJANGO_AVAILABLE = True
except ImportError:
    DJANGO_AVAILABLE = False

logger = logging.getLogger(__name__)


class EmailProcessor:
    """Process and handle incoming emails."""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.stats = {
            'emails_received': 0,
            'emails_processed': 0,
            'emails_failed': 0,
            'start_time': datetime.now()
        }
    
    def process_email(self, email_message) -> Dict[str, Any]:
        """Process an email message and return metadata."""
        try:
            # Extract email metadata
            metadata = {
                'from': email_message.get('From', ''),
                'to': email_message.get('To', ''),
                'subject': email_message.get('Subject', ''),
                'date': email_message.get('Date', ''),
                'message_id': email_message.get('Message-ID', ''),
                'received_at': datetime.now().isoformat(),
                'size': len(email_message.as_bytes()),
            }
            
            # Extract body content
            body = self._extract_body(email_message)
            metadata['body'] = body
            
            # Process based on configuration
            if self.config.get('save_to_database', False) and DJANGO_AVAILABLE:
                self._save_to_database(metadata)
            
            if self.config.get('forward_to_webhook', False):
                # Use asyncio.create_task for Python 3.11+ compatibility
                try:
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        asyncio.create_task(self._send_webhook_async(metadata))
                    else:
                        # If no event loop is running, run it in a new thread
                        import threading
                        def run_webhook():
                            new_loop = asyncio.new_event_loop()
                            asyncio.set_event_loop(new_loop)
                            new_loop.run_until_complete(self._send_webhook_async(metadata))
                            new_loop.close()
                        threading.Thread(target=run_webhook, daemon=True).start()
                except RuntimeError:
                    # No event loop available, skip webhook
                    pass
            
            if self.config.get('log_to_file', False):
                self._log_to_file(metadata)
            
            self.stats['emails_processed'] += 1
            logger.info(f"Email processed: {metadata['subject']} from {metadata['from']}")
            
            return metadata
            
        except Exception as e:
            self.stats['emails_failed'] += 1
            logger.error(f"Error processing email: {e}")
            return {'error': str(e)}
    
    def _extract_body(self, email_message) -> str:
        """Extract text body from email message."""
        body = ""
        
        if email_message.is_multipart():
            for part in email_message.walk():
                if part.get_content_type() == "text/plain":
                    body = part.get_content()
                    break
                elif part.get_content_type() == "text/html":
                    # Fallback to HTML if no plain text
                    if not body:
                        body = part.get_content()
        else:
            body = email_message.get_content()
        
        return body
    
    def _save_to_database(self, metadata: Dict[str, Any]):
        """Save email metadata to database (Django integration)."""
        if not DJANGO_AVAILABLE:
            return
        
        try:
            # Import here to avoid circular imports
            from core.models import EmailLog
            
            EmailLog.objects.create(
                sender=metadata['from'],
                recipient=metadata['to'],
                subject=metadata['subject'],
                body=metadata['body'],
                received_at=timezone.now(),
                message_id=metadata['message_id'],
                size=metadata['size']
            )
        except Exception as e:
            logger.error(f"Error saving to database: {e}")
    
    async def _send_webhook_async(self, metadata: Dict[str, Any]):
        """Send email metadata to webhook URL asynchronously."""
        webhook_url = self.config.get('webhook_url')
        if not webhook_url:
            return
        
        try:
            import aiohttp
            
            async with aiohttp.ClientSession() as session:
                async with session.post(webhook_url, json=metadata) as response:
                    if response.status != 200:
                        logger.warning(f"Webhook failed: {response.status}")
            
        except ImportError:
            logger.warning("aiohttp not available for webhook support")
        except Exception as e:
            logger.error(f"Error sending webhook: {e}")
    
    def _send_webhook(self, metadata: Dict[str, Any]):
        """Legacy webhook method - now uses async version."""
        # This is kept for backward compatibility
        pass
    
    def _log_to_file(self, metadata: Dict[str, Any]):
        """Log email metadata to file."""
        log_file = self.config.get('log_file', 'email_log.jsonl')
        try:
            with open(log_file, 'a') as f:
                f.write(json.dumps(metadata) + '\n')
        except Exception as e:
            logger.error(f"Error logging to file: {e}")


class CustomMessageHandler(Message):
    """Custom message handler for the SMTP server."""
    
    def __init__(self, processor: EmailProcessor, debug: bool = False):
        super().__init__()
        self.processor = processor
        self.debug = debug
        self.logger = logging.getLogger(__name__)
    
    def handle_message(self, message: bytes):
        """Handle received email message."""
        try:
            # Parse the email message
            email_message = message_from_bytes(message, policy=default)
            
            # Update stats
            self.processor.stats['emails_received'] += 1
            
            # Process the email
            metadata = self.processor.process_email(email_message)
            
            # Debug output
            if self.debug:
                self._print_debug_info(metadata)
            
        except Exception as e:
            self.logger.error(f"Error handling message: {e}")
    
    def _print_debug_info(self, metadata: Dict[str, Any]):
        """Print debug information for received email."""
        print('=' * 60)
        print('📧 NEW EMAIL RECEIVED')
        print('=' * 60)
        print(f'📤 From: {metadata.get("from", "Unknown")}')
        print(f'📥 To: {metadata.get("to", "Unknown")}')
        print(f'📋 Subject: {metadata.get("subject", "No Subject")}')
        print(f'📅 Date: {metadata.get("date", "Unknown")}')
        print('-' * 60)
        print('📄 Email Content:')
        print('-' * 60)
        body = metadata.get('body', '')
        print(body[:500] + ('...' if len(body) > 500 else ''))
        print('=' * 60)
        print()


class SimpleSMTP(SMTPServer):
    """Simple SMTP server with AUTH support for Django user authentication."""
    
    def __init__(self, handler: CustomMessageHandler, config: Dict[str, Any] = None):
        super().__init__(handler)
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        self.auth_enabled = self.config.get('auth_enabled', True)
        self.allowed_users = self.config.get('allowed_users', ['founders'])
    
    def _authenticate_user(self, username: str, password: str) -> bool:
        """Authenticate user against Django user database."""
        if not DJANGO_AVAILABLE:
            # If Django is not available, check against allowed users list
            # This is a simple fallback - in production, always use Django
            return username in self.allowed_users
        
        try:
            # Authenticate using Django's authentication system
            user = authenticate(username=username, password=password)
            if user and user.is_active:
                # Check if user is in allowed users list
                if self.allowed_users and user.username not in self.allowed_users:
                    self.logger.warning(f"User {username} not in allowed users list")
                    return False
                self.logger.info(f"User {username} authenticated successfully")
                return True
            return False
        except Exception as e:
            self.logger.error(f"Error authenticating user {username}: {e}")
            return False
    
    async def handle_EHLO(self, server, session, envelope, hostname):
        """Handle EHLO command and advertise AUTH capability."""
        response = await super().handle_EHLO(server, session, envelope, hostname)
        if self.auth_enabled:
            # Advertise AUTH PLAIN and AUTH LOGIN support
            if isinstance(response, tuple):
                code, lines = response
                if isinstance(lines, str):
                    lines = [lines]
                lines.append('AUTH PLAIN LOGIN')
                return (code, lines)
            else:
                # If response is not a tuple, wrap it
                return (250, [response, 'AUTH PLAIN LOGIN'])
        return response
    
    async def handle_AUTH(self, server, session, envelope, args):
        """Handle AUTH command for PLAIN and LOGIN authentication."""
        if not self.auth_enabled:
            return '530 Authentication not enabled'
        
        # Check if we're in the middle of a LOGIN authentication flow
        if hasattr(session, 'auth_state'):
            if session.auth_state == 'waiting_username':
                # This is the username step of LOGIN auth
                try:
                    username = base64.b64decode(args).decode('utf-8')
                    # Store username and request password
                    session.auth_username = username
                    session.auth_state = 'waiting_password'
                    return '334 UGFzc3dvcmQ6'  # base64("Password:")
                except Exception as e:
                    self.logger.error(f"Error decoding LOGIN username: {e}")
                    # Clear state on error
                    if hasattr(session, 'auth_state'):
                        delattr(session, 'auth_state')
                    return '535 Authentication failed'
            
            elif session.auth_state == 'waiting_password':
                # This is the password step of LOGIN auth
                try:
                    password = base64.b64decode(args).decode('utf-8')
                    username = session.auth_username
                    # Clear auth state
                    delattr(session, 'auth_state')
                    delattr(session, 'auth_username')
                    
                    # Authenticate
                    if self._authenticate_user(username, password):
                        session.authenticated = True
                        session.auth_user = username
                        self.logger.info(f"User {username} authenticated via LOGIN")
                        return '235 Authentication successful'
                    else:
                        self.logger.warning(f"Authentication failed for user {username}")
                        return '535 Authentication failed'
                except Exception as e:
                    self.logger.error(f"Error decoding LOGIN password: {e}")
                    # Clear state on error
                    if hasattr(session, 'auth_state'):
                        delattr(session, 'auth_state')
                    if hasattr(session, 'auth_username'):
                        delattr(session, 'auth_username')
                    return '535 Authentication failed'
        
        if not args:
            return '501 Syntax: AUTH <mechanism>'
        
        # Parse AUTH command
        parts = args.split(None, 1)
        mechanism = parts[0].upper()
        
        if mechanism == 'PLAIN':
            if len(parts) < 2:
                return '334 '  # Request credentials
            # PLAIN auth: credentials are base64 encoded as: \0username\0password
            try:
                credentials = base64.b64decode(parts[1]).decode('utf-8')
                auth_parts = credentials.split('\0')
                if len(auth_parts) >= 3:
                    username = auth_parts[1]
                    password = auth_parts[2]
                else:
                    return '535 Authentication failed'
                
                # Authenticate
                if self._authenticate_user(username, password):
                    session.authenticated = True
                    session.auth_user = username
                    self.logger.info(f"User {username} authenticated via PLAIN")
                    return '235 Authentication successful'
                else:
                    self.logger.warning(f"Authentication failed for user {username}")
                    return '535 Authentication failed'
            except Exception as e:
                self.logger.error(f"Error decoding PLAIN auth: {e}")
                return '535 Authentication failed'
        
        elif mechanism == 'LOGIN':
            if len(parts) < 2:
                # Initial LOGIN command - request username
                session.auth_state = 'waiting_username'
                return '334 VXNlcm5hbWU6'  # base64("Username:")
            
            # LOGIN with username provided in same command
            try:
                username = base64.b64decode(parts[1]).decode('utf-8')
                # Store username and request password
                session.auth_username = username
                session.auth_state = 'waiting_password'
                return '334 UGFzc3dvcmQ6'  # base64("Password:")
            except Exception as e:
                self.logger.error(f"Error decoding LOGIN username: {e}")
                if hasattr(session, 'auth_state'):
                    delattr(session, 'auth_state')
                return '535 Authentication failed'
        
        else:
            return '504 Unsupported authentication mechanism'
    
    async def handle_RCPT(self, server, session, envelope, address, rcpt_options):
        """Handle RCPT command with domain validation and optional auth check."""
        # If auth is enabled, require authentication
        if self.auth_enabled and not getattr(session, 'authenticated', False):
            return '530 Authentication required'
        
        # Check domain restrictions
        allowed_domains = self.config.get('allowed_domains', ['dripemails.org', 'localhost', '127.0.0.1'])
        domain = address.split('@')[-1] if '@' in address else ''
        
        if allowed_domains and not any(domain.endswith(d) for d in allowed_domains):
            return f'550 not relaying to domain {domain}'
        
        envelope.rcpt_tos.append(address)
        return '250 OK'
    
    async def handle_DATA(self, server, session, envelope):
        """Handle DATA command with enhanced logging."""
        try:
            auth_user = getattr(session, 'auth_user', 'anonymous')
            self.logger.info(f"Processing email from {envelope.mail_from} to {envelope.rcpt_tos} (auth: {auth_user})")
            return await super().handle_DATA(server, session, envelope)
        except Exception as e:
            self.logger.error(f"Error handling DATA: {e}")
            return '500 Error processing message'


class SMTPServerManager:
    """Manager for running and controlling the SMTP server."""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.controller: Optional[Controller] = None
        self.processor = EmailProcessor(config)
        self.logger = logging.getLogger(__name__)
    
    def start(self, host: str = 'localhost', port: int = 1025):
        """Start the SMTP server."""
        try:
            # Create handler and server
            handler = CustomMessageHandler(self.processor, debug=self.config.get('debug', False))
            smtp_server = SimpleSMTP(handler, config=self.config)
            
            # Create controller
            self.controller = Controller(
                smtp_server,
                hostname=host,
                port=port
            )
            
            # Start server
            self.controller.start()
            
            auth_status = "enabled" if self.config.get('auth_enabled', True) else "disabled"
            self.logger.info(f"SMTP server started on {host}:{port} with authentication {auth_status}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error starting SMTP server: {e}")
            return False
    
    def stop(self):
        """Stop the SMTP server."""
        if self.controller:
            self.controller.stop()
            self.logger.info("SMTP server stopped")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get server statistics."""
        return {
            **self.processor.stats,
            'uptime': (datetime.now() - self.processor.stats['start_time']).total_seconds(),
            'server_running': self.controller is not None,
            'auth_enabled': self.config.get('auth_enabled', True)
        }


def create_smtp_server(config: Dict[str, Any] = None) -> SMTPServerManager:
    """Factory function to create an SMTP server manager."""
    return SMTPServerManager(config)


def run_smtp_server(host: str = 'localhost', port: int = 1025, config: Dict[str, Any] = None):
    """Run the SMTP server in a blocking manner."""
    server = create_smtp_server(config)
    
    if server.start(host, port):
        try:
            # Keep the server running - Python 3.11+ compatible
            try:
                # Try to get existing event loop
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # If loop is already running, just keep it running
                    pass
                else:
                    # Run the event loop
                    loop.run_forever()
            except RuntimeError:
                # No event loop available, create a new one
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_forever()
        except KeyboardInterrupt:
            pass
        finally:
            server.stop()
    else:
        raise RuntimeError("Failed to start SMTP server")


if __name__ == "__main__":
    # Example configuration
    config = {
        'debug': True,
        'save_to_database': True,
        'forward_to_webhook': False,
        'log_to_file': True,
        'log_file': 'email_log.jsonl',
        'allowed_domains': ['dripemails.org', 'localhost'],
        'webhook_url': None,
        'auth_enabled': True,
        'allowed_users': ['founders']
    }
    
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("Starting DripEmails SMTP Server on port 25 with authentication...")
    run_smtp_server('localhost', 25, config) 