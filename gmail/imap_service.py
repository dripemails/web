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
    
    def test_connection(self, credential: EmailCredential):
        """Test IMAP connection with provided credentials.
        
        Returns:
            tuple: (success: bool, error_message: Optional[str])
        """
        try:
            mail = self._connect(credential)
            mail.logout()
            return True, None
        except Exception as e:
            error_msg = str(e)
            logger.error(f"IMAP connection test failed for {credential.email_address}: {error_msg}")
            
            # Check for application-specific password error
            if 'Application-specific password required' in error_msg or 'ALERT' in error_msg and 'apppasswords' in error_msg.lower():
                return False, 'app_password_required'
            
            return False, error_msg
    
    def _connect(self, credential: EmailCredential) -> imaplib.IMAP4:
        """Connect to IMAP server."""
        if credential.imap_use_ssl:
            mail = imaplib.IMAP4_SSL(credential.imap_host, credential.imap_port or 993)
        else:
            mail = imaplib.IMAP4(credential.imap_host, credential.imap_port or 143)
        
        mail.login(credential.imap_username, credential.imap_password)
        return mail
    
    def _find_sent_folder(self, mail) -> Optional[str]:
        """Find the sent folder by trying common names."""
        common_sent_folders = [
            'Sent',
            '[Gmail]/Sent Mail',
            'Sent Messages',
            'Sent Items',
            'INBOX.Sent',
            'INBOX/Sent',
        ]
        
        for folder_name in common_sent_folders:
            try:
                status, _ = mail.select(folder_name)
                if status == 'OK':
                    logger.info(f"Found sent folder: {folder_name}")
                    return folder_name
            except Exception:
                continue
        
        # Try to list all folders and find one that looks like a sent folder
        try:
            status, folders = mail.list()
            if status == 'OK':
                for folder_info in folders:
                    folder_str = folder_info.decode() if isinstance(folder_info, bytes) else str(folder_info)
                    # Look for folders containing "sent" (case-insensitive)
                    if 'sent' in folder_str.lower():
                        # Extract folder name (format varies: '() "/" "folder_name"' or similar)
                        parts = folder_str.split('"')
                        if len(parts) >= 3:
                            folder_name = parts[-1]
                            try:
                                status, _ = mail.select(folder_name)
                                if status == 'OK':
                                    logger.info(f"Found sent folder: {folder_name}")
                                    return folder_name
                            except Exception:
                                continue
        except Exception as e:
            logger.debug(f"Error listing folders to find sent folder: {str(e)}")
        
        return None
    
    def _find_all_mail_folder(self, mail) -> Optional[str]:
        """Find the All Mail folder by trying common names."""
        common_all_mail_folders = [
            '[Gmail]/All Mail',
            'All Mail',
            'AllMessages',
            'INBOX.All',
        ]
        
        for folder_name in common_all_mail_folders:
            try:
                status, _ = mail.select(folder_name)
                if status == 'OK':
                    logger.info(f"Found All Mail folder: {folder_name}")
                    return folder_name
            except Exception:
                continue
        
        # Try to list all folders and find one that looks like All Mail
        try:
            status, folders = mail.list()
            if status == 'OK':
                for folder_info in folders:
                    folder_str = folder_info.decode() if isinstance(folder_info, bytes) else str(folder_info)
                    # Look for folders containing "all" and "mail" (case-insensitive)
                    folder_lower = folder_str.lower()
                    if ('all' in folder_lower and 'mail' in folder_lower) or 'allmail' in folder_lower:
                        # Extract folder name (format varies: '() "/" "folder_name"' or similar)
                        parts = folder_str.split('"')
                        if len(parts) >= 3:
                            folder_name = parts[-1]
                            try:
                                status, _ = mail.select(folder_name)
                                if status == 'OK':
                                    logger.info(f"Found All Mail folder: {folder_name}")
                                    return folder_name
                            except Exception:
                                continue
        except Exception as e:
            logger.debug(f"Error listing folders to find All Mail folder: {str(e)}")
        
        return None
    
    def fetch_emails(self, credential: EmailCredential, max_results: int = 50, folders: List[str] = None) -> List[EmailMessage]:
        """Fetch latest emails from IMAP folders (default: INBOX and Sent)."""
        from email.parser import BytesParser
        from email.policy import default
        from django.db import IntegrityError
        
        if folders is None:
            folders = ['INBOX']
            # We'll find the sent folder dynamically
        
        try:
            mail = self._connect(credential)
            email_messages: List[EmailMessage] = []

            # Find sent folder automatically
            sent_folder = self._find_sent_folder(mail)
            if sent_folder:
                # Add sent folder to the list if not already there
                if sent_folder not in folders:
                    folders.append(sent_folder)
                # Replace any 'Sent' placeholder with the actual folder name
                folders = [f if f.lower() != 'sent' else sent_folder for f in folders]
            else:
                # Remove 'Sent' if we couldn't find it
                folders = [f for f in folders if f.lower() != 'sent']
                # Try to use All Mail as fallback since it includes sent items
                all_mail_folder = self._find_all_mail_folder(mail)
                if all_mail_folder:
                    if all_mail_folder not in folders:
                        folders.append(all_mail_folder)
                    logger.info(f"Could not find sent folder for {credential.email_address}, using All Mail folder instead")
                else:
                    logger.warning(f"Could not find sent folder or All Mail folder for {credential.email_address}, only processing INBOX")

            # Process each folder
            for folder in folders:
                try:
                    # Select folder (we use BODY.PEEK[] when fetching to avoid marking as read)
                    # Some IMAP servers don't support examine(), so we use select() and rely on BODY.PEEK[]
                    status, _ = mail.select(folder)
                    if status != 'OK':
                        logger.warning(f"Could not select folder {folder}, skipping")
                        continue

                    # Search for all messages (both read and unread) - we don't want to mark them as read
                    # Using 'ALL' instead of 'UNSEEN' to process both read and unread messages
                    # We use 'UID' to fetch by UID without changing message flags
                    status, messages = mail.uid('search', None, 'ALL')
                    if status != 'OK':
                        continue

                    message_ids = messages[0].split()
                    if not message_ids:
                        continue

                    # Limit results per folder and reverse to get newest first
                    folder_limit = max_results // len(folders) if len(folders) > 0 else max_results
                    message_ids = message_ids[-folder_limit:] if len(message_ids) > folder_limit else message_ids
                    message_ids.reverse()

                    for msg_id in message_ids:
                        try:
                            # Fetch message using UID FETCH with BODY.PEEK[] to avoid marking as read
                            # BODY.PEEK[] retrieves the message without setting the \Seen flag
                            status, msg_data = mail.uid('fetch', msg_id, '(BODY.PEEK[])')
                            if status != 'OK':
                                continue

                            # Parse email
                            msg_bytes = msg_data[0][1]
                            msg = BytesParser(policy=default).parsebytes(msg_bytes)

                            # Check if already exists
                            # Use a unique identifier that includes folder to avoid conflicts
                            # Different folders might have the same UID
                            uid = msg_id.decode() if isinstance(msg_id, bytes) else str(msg_id)
                            unique_id = f"{folder}:{uid}"
                            
                            if EmailMessage.objects.filter(
                                credential=credential,
                                provider_message_id=unique_id
                            ).exists():
                                continue

                            # Extract headers
                            subject = self._decode_header(msg.get('Subject', ''))
                            from_header = msg.get('From', '')
                            to_header = msg.get('To', '')
                            cc_header = msg.get('Cc', '')
                            sender_header = msg.get('Sender', '')
                            reply_to_header = msg.get('Reply-To', '')

                            # Parse email addresses and names
                            from_name, from_email = self._extract_name(from_header)
                            to_name_list = self._extract_name_list(to_header)
                            cc_name_list = self._extract_name_list(cc_header)
                            sender_name, sender_email = self._extract_name(sender_header) if sender_header else (from_name, from_email)
                            reply_to_name, reply_to = self._extract_name(reply_to_header) if reply_to_header else ('', '')

                            # Extract just emails for storage
                            to_emails = [email for name, email in to_name_list]
                            cc_emails = [email for name, email in cc_name_list]

                            # Store names in provider_data for later use
                            names_data = {
                                'from_name': from_name,
                                'sender_name': sender_name,
                                'reply_to_name': reply_to_name,
                                'to_names': {email: name for name, email in to_name_list},
                                'cc_names': {email: name for name, email in cc_name_list},
                                'folder': folder,
                            }

                            # Parse date
                            date_str = msg.get('Date', '')
                            try:
                                received_at = parsedate_to_datetime(date_str)
                                if received_at.tzinfo is None:
                                    received_at = timezone.make_aware(received_at)
                            except Exception:
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
                                        except Exception:
                                            pass
                                    elif content_type == 'text/html' and not body_html:
                                        try:
                                            body_html = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                                        except Exception:
                                            pass
                            else:
                                content_type = msg.get_content_type()
                                if content_type == 'text/plain':
                                    try:
                                        body_text = msg.get_payload(decode=True).decode('utf-8', errors='ignore')
                                    except Exception:
                                        pass
                                elif content_type == 'text/html':
                                    try:
                                        body_html = msg.get_payload(decode=True).decode('utf-8', errors='ignore')
                                    except Exception:
                                        pass

                            # Create EmailMessage with unique ID that includes folder
                            try:
                                email_msg = EmailMessage.objects.create(
                                    user=credential.user,
                                    credential=credential,
                                    provider=EmailProvider.IMAP,
                                    provider_message_id=unique_id,  # Use folder:uid format
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
                                    provider_data={'uid': uid, 'original_folder': folder, **names_data},
                                )
                                email_messages.append(email_msg)
                            except IntegrityError:
                                # Email already exists, skip it
                                logger.debug(f"Email {unique_id} already exists, skipping")
                                continue
                        except Exception as e:
                            logger.error(f"Error processing IMAP message {msg_id} in folder {folder}: {str(e)}")
                            continue
                except Exception as e:
                    logger.error(f"Error processing folder {folder}: {str(e)}")
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
    
    def _extract_name(self, header_value: str) -> tuple:
        """Extract name and email from header value. Returns (name, email)."""
        if not header_value:
            return ('', '')
        
        try:
            from email.utils import parseaddr
            name, addr = parseaddr(header_value)
            name = name.strip().strip('"').strip("'")
            addr = addr.strip()
            
            # If name is empty, try to extract from email address
            if not name and addr:
                name = addr.split('@')[0].split('.')[0].title()
            
            return (name, addr)
        except:
            # Fallback: extract email pattern
            import re
            match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', str(header_value))
            email = match.group(0) if match else ''
            name = email.split('@')[0].split('.')[0].title() if email else ''
            return (name, email)
    
    def _extract_name_list(self, header_value: str) -> List[tuple]:
        """Extract list of (name, email) tuples from header value."""
        if not header_value:
            return []
        
        try:
            from email.utils import getaddresses
            addresses = getaddresses([header_value])
            result = []
            for name, addr in addresses:
                if addr.strip():
                    name = name.strip().strip('"').strip("'")
                    # If name is empty, try to extract from email address
                    if not name:
                        name = addr.split('@')[0].split('.')[0].title()
                    result.append((name, addr.strip()))
            return result
        except:
            # Fallback: extract emails with regex
            import re
            emails = re.findall(r'[\w\.-]+@[\w\.-]+\.\w+', str(header_value))
            return [(e.split('@')[0].split('.')[0].title(), e.strip()) for e in emails]

