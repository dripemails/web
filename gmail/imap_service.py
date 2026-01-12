"""
IMAP Service for email integration.
"""
import imaplib
import email
from email.header import decode_header
from email.utils import parsedate_to_datetime
import logging
from typing import List, Optional
from django.utils import timezone
from .models import EmailCredential, EmailMessage, EmailProvider

logger = logging.getLogger(__name__)


class IMAPService:
    """Service for IMAP email integration."""
    
    def __init__(self):
        pass
    
    def test_connection(self, credential: EmailCredential) -> bool:
        """Test IMAP connection with provided credentials."""
        try:
            mail = self._connect(credential)
            mail.logout()
            return True
        except Exception as e:
            logger.error(f"IMAP connection test failed for {credential.email_address}: {str(e)}")
            return False
    
    def _connect(self, credential: EmailCredential) -> imaplib.IMAP4:
        """Connect to IMAP server."""
        if credential.imap_use_ssl:
            mail = imaplib.IMAP4_SSL(credential.imap_host, credential.imap_port or 993)
        else:
            mail = imaplib.IMAP4(credential.imap_host, credential.imap_port or 143)
        
        mail.login(credential.imap_username, credential.imap_password)
        return mail
    
    def fetch_emails(self, credential: EmailCredential, max_results: int = 50) -> List[EmailMessage]:
        """Fetch latest emails from IMAP inbox."""
        from email.parser import BytesParser
        from email.policy import default
        
        try:
            mail = self._connect(credential)
            mail.select('INBOX')
            
            # Search for unread messages (UIDs)
            status, messages = mail.search(None, 'UNSEEN')
            if status != 'OK':
                mail.logout()
                return []
            
            message_ids = messages[0].split()
            # Limit results and reverse to get newest first
            message_ids = message_ids[-max_results:] if len(message_ids) > max_results else message_ids
            message_ids.reverse()
            
            email_messages = []
            
            for msg_id in message_ids:
                try:
                    # Fetch message
                    status, msg_data = mail.fetch(msg_id, '(RFC822)')
                    if status != 'OK':
                        continue
                    
                    # Parse email
                    msg_bytes = msg_data[0][1]
                    msg = BytesParser(policy=default).parsebytes(msg_bytes)
                    
                    # Check if already exists
                    uid = msg_id.decode() if isinstance(msg_id, bytes) else str(msg_id)
                    if EmailMessage.objects.filter(
                        credential=credential,
                        provider_message_id=uid
                    ).exists():
                        continue
                    
                    # Extract headers
                    subject = self._decode_header(msg.get('Subject', ''))
                    from_header = msg.get('From', '')
                    to_header = msg.get('To', '')
                    cc_header = msg.get('Cc', '')
                    sender_header = msg.get('Sender', '')
                    reply_to_header = msg.get('Reply-To', '')
                    
                    # Parse email addresses
                    from_email = self._extract_email(from_header)
                    to_emails = self._extract_email_list(to_header)
                    cc_emails = self._extract_email_list(cc_header)
                    sender_email = self._extract_email(sender_header) if sender_header else from_email
                    reply_to = self._extract_email(reply_to_header) if reply_to_header else ''
                    
                    # Parse date
                    date_str = msg.get('Date', '')
                    try:
                        received_at = parsedate_to_datetime(date_str)
                        if received_at.tzinfo is None:
                            received_at = timezone.make_aware(received_at)
                    except:
                        received_at = timezone.now()
                    
                    # Extract body
                    body_text = ''
                    body_html = ''
                    
                    if msg.is_multipart():
                        for part in msg.walk():
                            content_type = part.get_content_type()
                            if content_type == 'text/plain' and not body_text:
                                try:
                                    body_text = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                                except:
                                    pass
                            elif content_type == 'text/html' and not body_html:
                                try:
                                    body_html = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                                except:
                                    pass
                    else:
                        content_type = msg.get_content_type()
                        if content_type == 'text/plain':
                            try:
                                body_text = msg.get_payload(decode=True).decode('utf-8', errors='ignore')
                            except:
                                pass
                        elif content_type == 'text/html':
                            try:
                                body_html = msg.get_payload(decode=True).decode('utf-8', errors='ignore')
                            except:
                                pass
                    
                    # Create EmailMessage
                    email_msg = EmailMessage.objects.create(
                        user=credential.user,
                        credential=credential,
                        provider=EmailProvider.IMAP,
                        provider_message_id=uid,
                        thread_id='',  # IMAP doesn't have thread IDs like Gmail
                        subject=subject,
                        from_email=from_email,
                        to_emails=','.join(to_emails) if to_emails else '',
                        cc_emails=','.join(cc_emails) if cc_emails else '',
                        sender_email=sender_email,
                        reply_to=reply_to,
                        body_text=body_text,
                        body_html=body_html,
                        received_at=received_at,
                        provider_data={'uid': uid}
                    )
                    
                    email_messages.append(email_msg)
                except Exception as e:
                    logger.error(f"Error processing IMAP message {msg_id}: {str(e)}")
                    continue
            
            mail.logout()
            return email_messages
        except Exception as e:
            logger.error(f"Error fetching IMAP emails for {credential.email_address}: {str(e)}")
            raise
    
    def _decode_header(self, header_value: str) -> str:
        """Decode email header value."""
        if not header_value:
            return ''
        
        try:
            decoded_parts = decode_header(header_value)
            decoded_string = ''
            for part, encoding in decoded_parts:
                if isinstance(part, bytes):
                    if encoding:
                        decoded_string += part.decode(encoding, errors='ignore')
                    else:
                        decoded_string += part.decode('utf-8', errors='ignore')
                else:
                    decoded_string += part
            return decoded_string.strip()
        except:
            return str(header_value)
    
    def _extract_email(self, header_value: str) -> str:
        """Extract email address from header value."""
        if not header_value:
            return ''
        
        try:
            # Try to parse with email.utils
            from email.utils import parseaddr
            name, addr = parseaddr(header_value)
            return addr.strip()
        except:
            # Fallback: extract email pattern
            import re
            match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', str(header_value))
            return match.group(0) if match else str(header_value).strip()
    
    def _extract_email_list(self, header_value: str) -> List[str]:
        """Extract list of email addresses from header value."""
        if not header_value:
            return []
        
        try:
            from email.utils import getaddresses
            addresses = getaddresses([header_value])
            return [addr.strip() for name, addr in addresses if addr.strip()]
        except:
            # Fallback: extract emails with regex
            import re
            emails = re.findall(r'[\w\.-]+@[\w\.-]+\.\w+', str(header_value))
            return [e.strip() for e in emails]

