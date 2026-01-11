"""
Email provider services for Gmail, Outlook, and IMAP.
"""
import os
import json
import base64
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict
from django.conf import settings
from django.utils import timezone
from django.contrib.auth.models import User
from .models import EmailCredential, EmailMessage, EmailProvider

logger = logging.getLogger(__name__)


class GmailService:
    """Service for Gmail API integration."""
    
    def __init__(self):
        # Get credentials from environment variables (loaded by Django's environ.Env)
        # These should be set in .env file and loaded by settings.py
        self.client_id = os.environ.get('GOOGLE_CLIENT_ID', '').strip()
        self.client_secret = os.environ.get('GOOGLE_CLIENT_SECRET', '').strip()
        self.redirect_uri = os.environ.get('GOOGLE_REDIRECT_URI', '').strip()
        self.scopes = [
            'https://www.googleapis.com/auth/gmail.readonly',
            'https://www.googleapis.com/auth/gmail.send'
        ]
        
        # Validate configuration
        if not self.client_id:
            error_msg = "GOOGLE_CLIENT_ID is not set. Please add it to your .env file."
            logger.error(error_msg)
            raise ValueError(error_msg)
        if not self.client_secret:
            error_msg = "GOOGLE_CLIENT_SECRET is not set. Please add it to your .env file."
            logger.error(error_msg)
            raise ValueError(error_msg)
        if not self.redirect_uri:
            error_msg = "GOOGLE_REDIRECT_URI is not set. Please add it to your .env file."
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        logger.debug(f"GmailService initialized with client_id: {self.client_id[:20]}..., redirect_uri: {self.redirect_uri}")
    
    def get_authorization_url(self, user: User) -> str:
        """Generate OAuth authorization URL."""
        from google_auth_oauthlib.flow import Flow
        
        # Ensure credentials are set
        if not self.client_id or not self.client_secret or not self.redirect_uri:
            raise ValueError("Gmail OAuth credentials are not configured. Please check your .env file.")
        
        # Create client configuration
        client_config = {
            "web": {
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [self.redirect_uri]
            }
        }
        
        logger.debug(f"Creating OAuth flow with redirect_uri: {self.redirect_uri}")
        
        try:
            flow = Flow.from_client_config(
                client_config,
                scopes=self.scopes,
                redirect_uri=self.redirect_uri
            )
            
            authorization_url, state = flow.authorization_url(
                access_type='offline',
                include_granted_scopes='true',
                prompt='consent'
            )
            
            logger.debug(f"Generated authorization URL: {authorization_url[:100]}...")
            return authorization_url
        except Exception as e:
            logger.error(f"Error creating OAuth flow: {str(e)}", exc_info=True)
            raise ValueError(f"Failed to create OAuth authorization URL: {str(e)}")
    
    def get_state_token(self, user: User) -> str:
        """Generate state token for OAuth flow."""
        import secrets
        state = secrets.token_urlsafe(32)
        # Store in user's profile or session
        return state
    
    def handle_oauth_callback(self, user: User, code: str, state: str) -> Optional[EmailCredential]:
        """Handle OAuth callback and save credentials."""
        from google_auth_oauthlib.flow import Flow
        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build
        
        try:
            flow = Flow.from_client_config(
                {
                    "web": {
                        "client_id": self.client_id,
                        "client_secret": self.client_secret,
                        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                        "token_uri": "https://oauth2.googleapis.com/token",
                        "redirect_uris": [self.redirect_uri]
                    }
                },
                scopes=self.scopes
            )
            flow.redirect_uri = self.redirect_uri
            flow.fetch_token(code=code)
            
            credentials = flow.credentials
            
            # Get user's email address
            service = build('gmail', 'v1', credentials=credentials)
            profile = service.users().getProfile(userId='me').execute()
            email_address = profile.get('emailAddress', '')
            
            # Save or update credential
            credential, created = EmailCredential.objects.update_or_create(
                user=user,
                provider=EmailProvider.GMAIL,
                email_address=email_address,
                defaults={
                    'access_token': credentials.token,
                    'refresh_token': credentials.refresh_token,
                    'token_expiry': timezone.now() + timedelta(seconds=credentials.expiry.timestamp() - datetime.now().timestamp()) if credentials.expiry else None,
                    'email_address': email_address,
                    'is_active': True,
                    'sync_enabled': True,
                }
            )
            
            return credential
        except Exception as e:
            logger.error(f"Error handling Gmail OAuth callback: {str(e)}")
            raise
    
    def get_credentials(self, credential: EmailCredential):
        """Get valid OAuth credentials, refreshing if needed."""
        from google.oauth2.credentials import Credentials
        from google.auth.transport.requests import Request
        
        if not credential.access_token:
            raise ValueError("No access token available")
        
        creds = Credentials(
            token=credential.access_token,
            refresh_token=credential.refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=self.client_id,
            client_secret=self.client_secret
        )
        
        # Refresh if expired
        if creds.expired and creds.refresh_token:
            creds.refresh(Request())
            # Update stored credentials
            credential.access_token = creds.token
            if creds.expiry:
                credential.token_expiry = timezone.now() + timedelta(seconds=(creds.expiry.timestamp() - datetime.now().timestamp()))
            credential.save()
        
        return creds
    
    def fetch_emails(self, credential: EmailCredential, max_results: int = 50) -> List[EmailMessage]:
        """Fetch latest emails from Gmail."""
        from googleapiclient.discovery import build
        import email
        from email.utils import parsedate_to_datetime
        
        try:
            creds = self.get_credentials(credential)
            service = build('gmail', 'v1', credentials=creds)
            
            # Get list of messages
            results = service.users().messages().list(
                userId='me',
                maxResults=max_results,
                q='is:inbox'
            ).execute()
            
            messages = results.get('messages', [])
            email_messages = []
            
            for msg in messages:
                try:
                    # Get full message
                    message = service.users().messages().get(
                        userId='me',
                        id=msg['id'],
                        format='full'
                    ).execute()
                    
                    # Check if already exists
                    if EmailMessage.objects.filter(
                        credential=credential,
                        provider_message_id=msg['id']
                    ).exists():
                        continue
                    
                    # Parse headers
                    headers = {h['name']: h['value'] for h in message['payload'].get('headers', [])}
                    
                    subject = headers.get('Subject', '')
                    from_email = headers.get('From', '').split('<')[-1].replace('>', '').strip()
                    to_emails = headers.get('To', '')
                    cc_emails = headers.get('Cc', '')
                    sender_email = headers.get('Sender', '').split('<')[-1].replace('>', '').strip() if headers.get('Sender') else from_email
                    reply_to = headers.get('Reply-To', '')
                    
                    # Parse date
                    date_str = headers.get('Date', '')
                    try:
                        received_at = parsedate_to_datetime(date_str)
                        if received_at.tzinfo is None:
                            received_at = timezone.make_aware(received_at)
                    except:
                        received_at = timezone.now()
                    
                    # Extract body
                    body_text = ''
                    body_html = ''
                    
                    def extract_body(part):
                        nonlocal body_text, body_html
                        if part.get('mimeType') == 'text/plain':
                            data = part.get('body', {}).get('data', '')
                            if data:
                                body_text = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
                        elif part.get('mimeType') == 'text/html':
                            data = part.get('body', {}).get('data', '')
                            if data:
                                body_html = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
                        
                        for subpart in part.get('parts', []):
                            extract_body(subpart)
                    
                    extract_body(message['payload'])
                    
                    # Create EmailMessage
                    email_msg = EmailMessage.objects.create(
                        user=credential.user,
                        credential=credential,
                        provider=EmailProvider.GMAIL,
                        provider_message_id=msg['id'],
                        thread_id=message.get('threadId', ''),
                        subject=subject,
                        from_email=from_email,
                        to_emails=to_emails,
                        cc_emails=cc_emails,
                        sender_email=sender_email,
                        reply_to=reply_to,
                        body_text=body_text,
                        body_html=body_html,
                        received_at=received_at,
                        provider_data=message
                    )
                    
                    email_messages.append(email_msg)
                except Exception as e:
                    logger.error(f"Error processing Gmail message {msg.get('id', 'unknown')}: {str(e)}")
                    continue
            
            return email_messages
        except Exception as e:
            logger.error(f"Error fetching Gmail emails: {str(e)}")
            raise


class OutlookService:
    """Service for Outlook/Microsoft 365 API integration."""
    # Placeholder for future implementation
    pass


class IMAPService:
    """Service for IMAP email integration."""
    # Placeholder for future implementation
    pass

