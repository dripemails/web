"""
Tests for DripEmails SMTP Server

This module contains unit tests for the SMTP server functionality.
"""

import pytest
import asyncio
import tempfile
import json
from unittest.mock import Mock, patch, AsyncMock
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from core.smtp_server import (
    EmailProcessor,
    CustomMessageHandler,
    SimpleSMTP,
    SMTPServerManager,
    create_smtp_server,
)


class TestEmailProcessor:
    """Test cases for EmailProcessor class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.config = {
            'debug': False,
            'save_to_database': False,
            'log_to_file': False,
            'forward_to_webhook': False,
        }
        self.processor = EmailProcessor(self.config)
    
    def test_init(self):
        """Test EmailProcessor initialization."""
        assert self.processor.config == self.config
        assert self.processor.stats['emails_received'] == 0
        assert self.processor.stats['emails_processed'] == 0
        assert self.processor.stats['emails_failed'] == 0
    
    def test_extract_body_plain_text(self):
        """Test extracting body from plain text email."""
        from email.message import Message
        
        msg = Message()
        msg['From'] = 'test@example.com'
        msg['To'] = 'recipient@example.com'
        msg['Subject'] = 'Test Email'
        msg.set_content('This is a test email body.')
        
        body = self.processor._extract_body(msg)
        assert body == 'This is a test email body.'
    
    def test_extract_body_multipart(self):
        """Test extracting body from multipart email."""
        from email.message import Message
        
        msg = MIMEMultipart()
        msg['From'] = 'test@example.com'
        msg['To'] = 'recipient@example.com'
        msg['Subject'] = 'Test Email'
        
        text_part = MIMEText('This is the text part.', 'plain')
        html_part = MIMEText('<p>This is the HTML part.</p>', 'html')
        
        msg.attach(text_part)
        msg.attach(html_part)
        
        body = self.processor._extract_body(msg)
        assert body == 'This is the text part.'
    
    def test_process_email_success(self):
        """Test successful email processing."""
        from email.message import Message
        
        msg = Message()
        msg['From'] = 'test@example.com'
        msg['To'] = 'recipient@example.com'
        msg['Subject'] = 'Test Email'
        msg['Message-ID'] = '<test@example.com>'
        msg.set_content('Test email body.')
        
        metadata = self.processor.process_email(msg)
        
        assert metadata['from'] == 'test@example.com'
        assert metadata['to'] == 'recipient@example.com'
        assert metadata['subject'] == 'Test Email'
        assert metadata['body'] == 'Test email body.'
        assert self.processor.stats['emails_processed'] == 1
        assert self.processor.stats['emails_failed'] == 0
    
    def test_process_email_failure(self):
        """Test email processing failure."""
        # Test with invalid message
        metadata = self.processor.process_email(None)
        
        assert 'error' in metadata
        assert self.processor.stats['emails_failed'] == 1
    
    def test_log_to_file(self):
        """Test logging to file."""
        with tempfile.NamedTemporaryFile(mode='w+', delete=False) as f:
            log_file = f.name
        
        try:
            config = self.config.copy()
            config['log_to_file'] = True
            config['log_file'] = log_file
            
            processor = EmailProcessor(config)
            
            from email.message import Message
            msg = Message()
            msg['From'] = 'test@example.com'
            msg['To'] = 'recipient@example.com'
            msg['Subject'] = 'Test Email'
            msg.set_content('Test body.')
            
            processor.process_email(msg)
            
            # Check if log file was created and contains data
            with open(log_file, 'r') as f:
                log_data = f.read()
                assert 'test@example.com' in log_data
                assert 'Test Email' in log_data
        
        finally:
            import os
            os.unlink(log_file)


class TestCustomMessageHandler:
    """Test cases for CustomMessageHandler class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.config = {'debug': False}
        self.processor = EmailProcessor(self.config)
        self.handler = CustomMessageHandler(self.processor, debug=False)
    
    def test_init(self):
        """Test CustomMessageHandler initialization."""
        assert self.handler.processor == self.processor
        assert self.handler.debug is False
    
    def test_handle_message(self):
        """Test message handling."""
        from email.message import Message
        
        msg = Message()
        msg['From'] = 'test@example.com'
        msg['To'] = 'recipient@example.com'
        msg['Subject'] = 'Test Email'
        msg.set_content('Test body.')
        
        message_bytes = msg.as_bytes()
        
        # Should not raise any exceptions
        self.handler.handle_message(message_bytes)
        
        assert self.processor.stats['emails_received'] == 1
    
    def test_print_debug_info(self):
        """Test debug info printing."""
        metadata = {
            'from': 'test@example.com',
            'to': 'recipient@example.com',
            'subject': 'Test Email',
            'date': '2024-01-01T12:00:00',
            'body': 'Test email body content.'
        }
        
        # Should not raise any exceptions
        self.handler._print_debug_info(metadata)


class TestSMTPServerManager:
    """Test cases for SMTPServerManager class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.config = {
            'debug': False,
            'auth_enabled': False,
            'allowed_domains': ['example.com'],
        }
        self.manager = SMTPServerManager(self.config)
    
    def test_init(self):
        """Test SMTPServerManager initialization."""
        assert self.manager.config == self.config
        assert self.manager.controller is None
        assert isinstance(self.manager.processor, EmailProcessor)
    
    def test_get_stats(self):
        """Test getting server statistics."""
        stats = self.manager.get_stats()
        
        assert 'emails_received' in stats
        assert 'emails_processed' in stats
        assert 'emails_failed' in stats
        assert 'uptime' in stats
        assert 'server_running' in stats
        assert 'auth_enabled' in stats
    
    @patch('core.smtp_server.Controller')
    def test_start_server(self, mock_controller):
        """Test starting the server."""
        mock_controller_instance = Mock()
        mock_controller.return_value = mock_controller_instance
        
        result = self.manager.start('localhost', 1025)
        
        assert result is True
        mock_controller_instance.start.assert_called_once()
    
    def test_stop_server(self):
        """Test stopping the server."""
        # Mock controller
        self.manager.controller = Mock()
        
        self.manager.stop()
        
        self.manager.controller.stop.assert_called_once()


class TestCreateSMTP:
    """Test cases for factory functions."""
    
    def test_create_smtp_server(self):
        """Test create_smtp_server factory function."""
        config = {'debug': True}
        server = create_smtp_server(config)
        
        assert isinstance(server, SMTPServerManager)
        assert server.config == config


@pytest.mark.asyncio
class TestAsyncSMTP:
    """Test cases for async SMTP functionality."""
    
    async def test_simple_smtp_initialization(self):
        """Test SimpleSMTP initialization."""
        config = {'auth_enabled': False}
        handler = CustomMessageHandler(EmailProcessor(config))
        smtp = SimpleSMTP(handler, config)
        
        assert smtp.config == config
        assert smtp.auth_enabled is False
    
    async def test_handle_rcpt_valid_domain(self):
        """Test handling RCPT with valid domain."""
        config = {'allowed_domains': ['example.com']}
        handler = CustomMessageHandler(EmailProcessor(config))
        smtp = SimpleSMTP(handler, config)
        
        # Mock server, session, and envelope
        server = Mock()
        session = Mock()
        envelope = Mock()
        envelope.rcpt_tos = []
        
        result = await smtp.handle_RCPT(
            server, session, envelope, 'test@example.com', []
        )
        
        assert result == '250 OK'
        assert 'test@example.com' in envelope.rcpt_tos
    
    async def test_handle_rcpt_invalid_domain(self):
        """Test handling RCPT with invalid domain."""
        config = {'allowed_domains': ['example.com']}
        handler = CustomMessageHandler(EmailProcessor(config))
        smtp = SimpleSMTP(handler, config)
        
        # Mock server, session, and envelope
        server = Mock()
        session = Mock()
        envelope = Mock()
        envelope.rcpt_tos = []
        
        result = await smtp.handle_RCPT(
            server, session, envelope, 'test@invalid.com', []
        )
        
        assert result == '550 not relaying to domain invalid.com'
        assert len(envelope.rcpt_tos) == 0


if __name__ == "__main__":
    pytest.main([__file__]) 