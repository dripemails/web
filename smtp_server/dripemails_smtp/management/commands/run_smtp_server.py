"""
Django management command to run a custom SMTP server using aiosmtpd.

Usage:
    python manage.py run_smtp_server [--port PORT] [--host HOST] [--debug] [--config CONFIG_FILE]

This command starts a modern async SMTP server that can receive emails from your Django application
and handle them appropriately. Perfect for development, testing, and production email handling.
Compatible with Python 3.11+ and 3.12+. Runs on standard SMTP port 25 by default (no SSL required).
Supports authentication with Django users including the 'founders' account.
"""

import asyncio
import argparse
import logging
import json
import os
from pathlib import Path
from django.core.management.base import BaseCommand
from django.conf import settings

# Import our custom SMTP server
from core.smtp_server import create_smtp_server, run_smtp_server


class Command(BaseCommand):
    help = 'Run a custom SMTP server using aiosmtpd for development and testing'

    def add_arguments(self, parser):
        parser.add_argument(
            '--port',
            type=int,
            default=25,
            help='Port to run the SMTP server on (default: 25)'
        )
        parser.add_argument(
            '--host',
            type=str,
            default='localhost',
            help='Host to bind the SMTP server to (default: localhost)'
        )
        parser.add_argument(
            '--debug',
            action='store_true',
            help='Enable debug mode to print emails to console'
        )
        parser.add_argument(
            '--config',
            type=str,
            help='Path to configuration JSON file'
        )
        parser.add_argument(
            '--save-to-db',
            action='store_true',
            help='Save incoming emails to database'
        )
        parser.add_argument(
            '--log-to-file',
            action='store_true',
            help='Log emails to file'
        )
        parser.add_argument(
            '--webhook-url',
            type=str,
            help='Webhook URL to forward emails to'
        )
        parser.add_argument(
            '--no-auth',
            action='store_true',
            help='Disable authentication (allow anonymous access)'
        )
        parser.add_argument(
            '--allowed-users',
            type=str,
            nargs='+',
            default=['founders'],
            help='List of allowed users for authentication (default: founders)'
        )

    def handle(self, *args, **options):
        port = options['port']
        host = options['host']
        debug = options['debug']
        
        # Load configuration
        config = self._load_config(options)
        
        # Set up logging
        logging.basicConfig(
            level=logging.DEBUG if debug else logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'🚀 Starting aiosmtpd server on {host}:{port}...'
            )
        )
        
        if debug:
            self.stdout.write(
                self.style.WARNING(
                    '🐛 Debug mode enabled - emails will be printed to console'
                )
            )
        
        if config.get('save_to_database'):
            self.stdout.write(
                self.style.SUCCESS(
                    '💾 Database logging enabled'
                )
            )
        
        if config.get('log_to_file'):
            self.stdout.write(
                self.style.SUCCESS(
                    f'📄 File logging enabled: {config.get("log_file", "email_log.jsonl")}'
                )
            )
        
        if config.get('webhook_url'):
            self.stdout.write(
                self.style.SUCCESS(
                    f'🔗 Webhook forwarding enabled: {config["webhook_url"]}'
                )
            )
        
        # Authentication status
        if config.get('auth_enabled', True):
            allowed_users = config.get('allowed_users', ['founders'])
            self.stdout.write(
                self.style.SUCCESS(
                    f'🔐 Authentication enabled for users: {", ".join(allowed_users)}'
                )
            )
        else:
            self.stdout.write(
                self.style.WARNING(
                    '⚠️  Authentication disabled - anonymous access allowed'
                )
            )
        
        self.stdout.write(
            self.style.WARNING(
                '⏹️  Press Ctrl+C to stop the server.'
            )
        )
        self.stdout.write('')
        
        try:
            # Run the SMTP server with Python 3.11+ compatible event loop
            self._run_smtp_server(host, port, config)
            
        except KeyboardInterrupt:
            self.stdout.write(
                self.style.SUCCESS('🛑 SMTP server stopped by user.')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error running SMTP server: {e}')
            )
    
    def _run_smtp_server(self, host: str, port: int, config: dict):
        """Run the SMTP server with proper event loop handling for Python 3.11+."""
        server = create_smtp_server(config)
        
        if server.start(host, port):
            try:
                # Python 3.11+ compatible event loop handling
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
    
    def _load_config(self, options):
        """Load configuration from file or command line options."""
        config = {
            'debug': options['debug'],
            'save_to_database': options['save_to_db'],
            'log_to_file': options['log_to_file'],
            'allowed_domains': ['dripemails.org', 'localhost', '127.0.0.1'],
            'auth_enabled': not options['no_auth'],
            'allowed_users': options['allowed_users'],
        }
        
        # Load from config file if specified
        if options['config']:
            config_file = Path(options['config'])
            if config_file.exists():
                try:
                    with open(config_file, 'r') as f:
                        file_config = json.load(f)
                    config.update(file_config)
                    self.stdout.write(
                        self.style.SUCCESS(f'✅ Loaded config from {config_file}')
                    )
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f'❌ Error loading config file: {e}')
                    )
            else:
                self.stdout.write(
                    self.style.WARNING(f'⚠️  Config file not found: {config_file}')
                )
        
        # Override with command line options
        if options['webhook_url']:
            config['webhook_url'] = options['webhook_url']
            config['forward_to_webhook'] = True
        
        if options['log_to_file']:
            config['log_file'] = 'email_log.jsonl'
        
        return config 