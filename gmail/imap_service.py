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

# IMAP folder names need to be encoded using modified UTF-7 encoding
def encode_folder_name(folder_name: str) -> bytes:
    """Encode folder name for IMAP SELECT command using modified UTF-7."""
    try:
        # imaplib uses UTF-8 by default, but some servers may need modified UTF-7
        # Try the folder name as-is first (imaplib should handle it)
        # But if that fails, we'll need to encode it
        return folder_name.encode('utf-8')
    except:
        return folder_name.encode('utf-8', errors='ignore')

def safe_select_folder(mail, folder_name: str) -> tuple:
    """Safely select an IMAP folder, handling special characters.
    
    For folders with special characters like [Gmail]/Sent Mail,
    we need to ensure the folder name is properly formatted.
    Gmail uses UTF-8 encoding for folder names.
    
    The issue is that imaplib might not handle special characters correctly,
    so we try multiple approaches including using the raw IMAP command.
    """
    # Clean the folder name - remove any extra whitespace
    folder_name = folder_name.strip()
    
    # Ensure it's a string, not bytes
    if isinstance(folder_name, bytes):
        folder_name = folder_name.decode('utf-8', errors='ignore')
    
    logger.debug(f"Attempting to select/examine folder: {repr(folder_name)}")
    
    # For Gmail special folders, try examine first (read-only, sometimes works better)
    if folder_name.startswith('[Gmail]'):
        try:
            status, response = mail.examine(folder_name)
            if status == 'OK':
                logger.debug(f"Successfully examined Gmail folder: {folder_name}")
                return status, response
        except Exception as e:
            logger.debug(f"Examine failed for {folder_name}: {str(e)}")
    
    # Method 1: Try direct selection
    try:
        status, response = mail.select(folder_name)
        return status, response
    except (imaplib.IMAP4.error, Exception) as e:
        error_str = str(e).lower()
        logger.debug(f"Direct select failed for {folder_name}: {error_str}")
        
        # If it's a parse/BAD error, try alternative methods
        if 'parse' in error_str or 'bad' in error_str:
            # Method 2: Try examine as fallback
            try:
                status, response = mail.examine(folder_name)
                if status == 'OK':
                    logger.debug(f"Examine succeeded as fallback for: {folder_name}")
                    return status, response
            except Exception as e2:
                logger.debug(f"Examine fallback also failed: {str(e2)}")
            
            # Method 3: Try constructing the IMAP command manually with proper quoting
            # Gmail might need the folder name in quotes in the IMAP command
            try:
                # Use _simple_command which might handle encoding differently
                # The folder name might need to be quoted in the IMAP protocol
                logger.debug(f"Trying _simple_command with folder: {repr(folder_name)}")
                typ, dat = mail._simple_command('SELECT', folder_name)
                logger.debug(f"_simple_command result: {typ}")
                return typ, dat
            except Exception as e3:
                logger.debug(f"_simple_command failed: {str(e3)}")
                
                # Last resort: try using the LIST command to get the exact folder format,
                # then extract and use that format for SELECT
                try:
                    # Re-list folders to get the exact format Gmail uses
                    typ, folders = mail.list()
                    if typ == 'OK':
                        for folder_info in folders:
                            folder_str = folder_info.decode() if isinstance(folder_info, bytes) else str(folder_info)
                            if folder_name in folder_str or folder_name.lower() in folder_str.lower():
                                # Found the folder, now try to extract and use its exact format
                                # Extract the folder name from the LIST response
                                import re
                                quoted = re.findall(r'"([^"]+)"', folder_str)
                                if quoted:
                                    # Try using the last quoted string (usually the folder name)
                                    exact_name = quoted[-1]
                                    if exact_name and exact_name != '/' and exact_name != '.':
                                        logger.debug(f"Trying exact folder name from LIST: {repr(exact_name)}")
                                        try:
                                            status, response = mail.select(exact_name)
                                            if status == 'OK':
                                                return status, response
                                        except:
                                            try:
                                                status, response = mail.examine(exact_name)
                                                if status == 'OK':
                                                    return status, response
                                            except:
                                                pass
                except Exception as e4:
                    logger.debug(f"Re-listing folders failed: {str(e4)}")
        
        # Re-raise the original error if all methods fail
        raise


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
        import re
        
        # Prioritize Gmail folders since they're common
        common_sent_folders = [
            '[Gmail]/Sent Mail',
            'Sent',
            'Sent Messages',
            'Sent Items',
            'INBOX.Sent',
            'INBOX/Sent',
        ]
        
        # First try common folder names directly
        for folder_name in common_sent_folders:
            try:
                status, response = mail.select(folder_name)
                if status == 'OK':
                    logger.info(f"Found sent folder: {folder_name}")
                    return folder_name
                else:
                    logger.debug(f"Failed to select folder '{folder_name}': status={status}, response={response}")
            except Exception as e:
                logger.debug(f"Exception trying to select folder '{folder_name}': {str(e)}")
                continue
        
        # If direct selection fails, list all folders and find one that looks like a sent folder
        try:
            status, folders = mail.list()
            if status == 'OK':
                for folder_info in folders:
                    folder_str = folder_info.decode() if isinstance(folder_info, bytes) else str(folder_info)
                    # Look for folders containing "sent" (case-insensitive)
                    if 'sent' in folder_str.lower():
                        folder_name = None
                        
                        # Use improved parsing logic (same as list_all_folders)
                        # Method 1: Try to extract from quoted strings
                        quoted_matches = re.findall(r'"([^"]+)"', folder_str)
                        if quoted_matches:
                            valid_quoted = [q for q in quoted_matches if q not in ['/', '.'] and q.strip()]
                            if valid_quoted:
                                folder_name = valid_quoted[-1]
                        
                        # Method 2: Try pattern matching
                        if not folder_name:
                            match = re.search(r'["/]\.?\s*"([^"]+)"', folder_str)
                            if match:
                                folder_name = match.group(1)
                            else:
                                match = re.search(r'["/]\.?\s+([A-Za-z0-9_\[\]/]+)', folder_str)
                                if match:
                                    folder_name = match.group(1)
                        
                        # Method 3: Fallback to simple extraction
                        if not folder_name:
                            parts = folder_str.split('"')
                            if len(parts) >= 3:
                                folder_name = parts[-1]
                        
                        if folder_name and folder_name.strip():
                            try:
                                status, _ = mail.select(folder_name)
                                if status == 'OK':
                                    logger.info(f"Found sent folder via listing: {folder_name}")
                                    return folder_name
                            except Exception:
                                continue
        except Exception as e:
            logger.debug(f"Error listing folders to find sent folder: {str(e)}")
        
        logger.warning("Could not find sent folder")
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
    
    def list_all_folders(self, credential: EmailCredential, mail=None, close_connection=True) -> List[str]:
        """List all available IMAP folders.
        
        Args:
            credential: EmailCredential to connect with
            mail: Optional existing IMAP connection (if provided, won't create new connection)
            close_connection: If True, will logout after listing (default: True)
        
        Returns:
            List of folder names (as strings)
        """
        import re
        should_logout = False
        try:
            if mail is None:
                mail = self._connect(credential)
                should_logout = close_connection
            
            status, folders = mail.list()
            
            if status != 'OK':
                logger.warning(f"Could not list folders for {credential.email_address}")
                mail.logout()
                return []
            
            folder_names = []
            for idx, folder_info in enumerate(folders):
                folder_str = folder_info.decode() if isinstance(folder_info, bytes) else str(folder_info)
                
                # Debug: log raw format for all folders containing "sent" or "[gmail]"
                if 'sent' in folder_str.lower() or '[gmail]' in folder_str.lower():
                    logger.info(f"Raw IMAP LIST response for '{folder_str[:50]}...': {repr(folder_str)}")
                
                # IMAP LIST response format can vary:
                # - '(\HasNoChildren) "/" "INBOX"'
                # - '(\HasNoChildren) "." "INBOX"'
                # - '() "/" INBOX'
                # - '(\HasChildren \Noselect) "/" "Folders/Subfolder"'
                # - '(\\HasNoChildren \\UnMarked) "/" "INBOX"'
                # etc.
                
                folder_name = None
                
                # Method 1: Try to extract folder name from quoted strings
                # Find all quoted strings - usually the last one is the folder name
                quoted_matches = re.findall(r'"([^"]+)"', folder_str)
                if quoted_matches:
                    # Filter out separators like "/" or "."
                    # IMPORTANT: Keep the folder name exactly as Gmail returns it
                    valid_quoted = [q for q in quoted_matches if q not in ['/', '.'] and q.strip()]
                    if valid_quoted:
                        # Use the last quoted string (usually the folder name)
                        # Preserve the exact format including special characters
                        folder_name = valid_quoted[-1]
                
                # Method 2: If no quoted folder name, look for pattern: separator "folder"
                # Pattern: ... "/" "folder_name" or ... "/" folder_name
                if not folder_name:
                    # Match: separator (quoted or not) followed by folder name
                    match = re.search(r'["/]\.?\s*"([^"]+)"', folder_str)
                    if match:
                        folder_name = match.group(1)
                    else:
                        # Try without quotes: separator followed by word
                        match = re.search(r'["/]\.?\s+([A-Za-z0-9_\[\]/]+)', folder_str)
                        if match:
                            folder_name = match.group(1)
                
                # Method 3: Try to find the last meaningful token
                if not folder_name:
                    # Split and look for non-flag, non-separator tokens
                    parts = re.split(r'\s+', folder_str)
                    for part in reversed(parts):
                        part = part.strip().strip('"').strip("'")
                        # Skip empty, flags, separators
                        if (part and 
                            part not in ['/', '.', ''] and 
                            not part.startswith('(') and 
                            not part.startswith('\\') and
                            len(part) > 0):
                            folder_name = part
                            break
                
                if folder_name and folder_name.strip():
                    folder_names.append(folder_name.strip())
                elif idx < 3:
                    logger.warning(f"Could not parse folder name from: {repr(folder_str)}")
            
            if should_logout:
                mail.logout()
            return sorted(folder_names)
        except Exception as e:
            logger.error(f"Error listing folders for {credential.email_address}: {str(e)}", exc_info=True)
            if should_logout and 'mail' in locals():
                try:
                    mail.logout()
                except:
                    pass
            return []
    
    def fetch_emails(self, credential: EmailCredential, max_results: int = 50, folders: List[str] = None, all_folders: List[str] = None) -> List[EmailMessage]:
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

            # Find sent folder automatically - use provided folder list or fetch it
            if all_folders is None:
                logger.info(f"Listing all folders to find sent folder for {credential.email_address}...")
                all_folders = self.list_all_folders(credential, mail=mail, close_connection=False)
            else:
                logger.info(f"Using provided folder list ({len(all_folders)} folders) to find sent folder")
            
            logger.info(f"Retrieved {len(all_folders)} folders from IMAP server")
            if len(all_folders) > 0:
                logger.info(f"First few folders: {all_folders[:5]}")
            
            sent_folder = None
            
            # Search through the folder list for sent folders
            # Prioritize folders with "sent mail" (case-insensitive), then just "sent"
            sent_candidates = []
            
            # First, ensure we're in a clean state by selecting INBOX
            try:
                mail.select('INBOX')
            except:
                pass
            
            for folder in all_folders:
                folder_lower = folder.lower()
                # Check if folder name contains "sent"
                if 'sent' in folder_lower:
                    # Add to candidates without verifying selection here
                    # We'll verify when we actually process the folder (which works)
                    folder_clean = folder.strip()
                    sent_candidates.append((folder_clean, 'mail' in folder_lower))
                    logger.info(f"Found sent folder candidate: {folder_clean}")
            
            logger.info(f"Found {len(sent_candidates)} sent folder candidate(s): {[c[0] for c in sent_candidates]}")
            
            # Prefer folders with "mail" in the name (e.g., "[Gmail]/Sent Mail")
            if sent_candidates:
                # Sort: folders with "mail" first, then others
                sent_candidates.sort(key=lambda x: (not x[1], x[0]))
                sent_folder = sent_candidates[0][0]
                logger.info(f"Selected sent folder from candidates: {sent_folder}")
            else:
                logger.warning(f"No sent folder candidates found. Total folders: {len(all_folders)}")
                if len(all_folders) > 0:
                    logger.warning(f"Sample folders: {all_folders[:10]}")
            
            # If not found in list, try the traditional method
            if not sent_folder:
                logger.info("Trying traditional _find_sent_folder method...")
                sent_folder = self._find_sent_folder(mail)
            if sent_folder:
                # Add sent folder to the list if not already there
                if sent_folder not in folders:
                    folders.append(sent_folder)
                # Replace any 'Sent' placeholder with the actual folder name
                folders = [f if f.lower() != 'sent' else sent_folder for f in folders]
                logger.info(f"Will process folders for {credential.email_address}: {folders}")
            else:
                # Remove 'Sent' if we couldn't find it
                folders = [f for f in folders if f.lower() != 'sent']
                # Try to use All Mail as fallback since it includes sent items
                all_mail_folder = self._find_all_mail_folder(mail)
                if all_mail_folder:
                    if all_mail_folder not in folders:
                        folders.append(all_mail_folder)
                    logger.info(f"Could not find sent folder for {credential.email_address}, using All Mail folder instead")
                    logger.info(f"Will process folders for {credential.email_address}: {folders}")
                else:
                    logger.warning(f"Could not find sent folder or All Mail folder for {credential.email_address}, only processing INBOX")
                    logger.info(f"Will process folders for {credential.email_address}: {folders}")

            # Process each folder
            for folder in folders:
                try:
                    logger.info(f"Processing folder: {folder}")
                    # Select folder (we use BODY.PEEK[] when fetching to avoid marking as read)
                    # Some IMAP servers don't support examine(), so we use select() and rely on BODY.PEEK[]
                    # Use safe_select_folder for folders with special characters
                    try:
                        status, response = safe_select_folder(mail, folder)
                    except Exception as select_error:
                        error_msg = str(select_error)
                        
                        # For Gmail special folders that fail, try one more thing:
                        # Use the raw IMAP command with the folder name exactly as Gmail provides it
                        if folder.startswith('[Gmail]'):
                            try:
                                # Try using the raw IMAP command with proper quoting
                                # Gmail might need the folder name quoted in the IMAP protocol
                                logger.info(f"Trying raw IMAP command for Gmail folder: {folder}")
                                # Get the raw folder name from LIST response again
                                typ, folders = mail.list()
                                if typ == 'OK':
                                    for folder_info in folders:
                                        folder_str = folder_info.decode() if isinstance(folder_info, bytes) else str(folder_info)
                                        if folder in folder_str or folder.lower() in folder_str.lower():
                                            # Found matching folder in LIST response
                                            logger.info(f"Found folder in LIST response: {repr(folder_str)}")
                                            # Extract exact folder name format from LIST
                                            import re
                                            quoted = re.findall(r'"([^"]+)"', folder_str)
                                            logger.info(f"Quoted strings found: {quoted}")
                                            if quoted:
                                                # Try all quoted strings, not just the last one
                                                for exact_name in reversed(quoted):
                                                    if exact_name and exact_name not in ['/', '.']:
                                                        logger.info(f"Trying exact folder name from LIST: {repr(exact_name)}")
                                                        # Try with the exact name
                                                        try:
                                                            status, response = mail.select(exact_name)
                                                            logger.info(f"SELECT succeeded with exact name: {repr(exact_name)}, status={status}")
                                                            if status == 'OK':
                                                                break  # Success!
                                                        except Exception as e1:
                                                            logger.debug(f"SELECT failed with {repr(exact_name)}: {str(e1)}")
                                                            try:
                                                                status, response = mail.examine(exact_name)
                                                                logger.info(f"EXAMINE succeeded with exact name: {repr(exact_name)}, status={status}")
                                                                if status == 'OK':
                                                                    break  # Success!
                                                            except Exception as e2:
                                                                logger.debug(f"EXAMINE also failed with {repr(exact_name)}: {str(e2)}")
                                                                continue
                                                else:
                                                    # No quoted name worked, try without quotes
                                                    logger.info(f"No quoted name worked, trying unquoted extraction")
                                                    # Try extracting without quotes
                                                    match = re.search(r'[\s"]+([^"]+?)(?:\s|$)', folder_str)
                                                    if match:
                                                        unquoted_name = match.group(1).strip()
                                                        if unquoted_name and unquoted_name not in ['/', '.']:
                                                            logger.info(f"Trying unquoted folder name: {repr(unquoted_name)}")
                                                            try:
                                                                status, response = mail.select(unquoted_name)
                                                                if status == 'OK':
                                                                    break
                                                            except:
                                                                try:
                                                                    status, response = mail.examine(unquoted_name)
                                                                    if status == 'OK':
                                                                        break
                                                                except:
                                                                    pass
                                            
                                            # If we get here, the exact name didn't work either
                                            logger.warning(f"Could not access Gmail folder '{folder}' even with exact LIST format")
                                            logger.warning(f"Skipping Gmail special folder '{folder}' due to access error")
                                            raise Exception("Gmail folder access failed")
                            except Exception:
                                logger.warning(f"Skipping Gmail special folder '{folder}' due to SELECT/EXAMINE error: {error_msg}")
                                logger.info(f"Note: Gmail special folders may require different access methods or permissions")
                                continue
                        
                        # If safe_select_folder fails, try examine as fallback for non-Gmail folders
                        try:
                            logger.info(f"Select failed for '{folder}', trying examine... (error: {error_msg})")
                            status, response = mail.examine(folder)
                            logger.info(f"Examine succeeded for '{folder}'")
                        except Exception as examine_error:
                            logger.error(f"Could not select or examine folder '{folder}': {error_msg}")
                            logger.debug(f"Examine error: {str(examine_error)}")
                            continue
                    
                    if status != 'OK':
                        logger.warning(f"Could not select folder {folder}: status={status}, response={response}")
                        # For Gmail folders, skip instead of failing completely
                        if folder.startswith('[Gmail]'):
                            logger.info(f"Skipping Gmail folder '{folder}' due to status {status}")
                            continue
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

