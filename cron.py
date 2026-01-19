#!/usr/bin/env python
"""
Cron script to check SPF records for user domains.

This script checks if users have properly configured SPF records
that include DripEmails.org servers.

Usage:
    # SPF Record Checking
    python cron.py check_spf --all-users
    python cron.py check_spf --user-id 123
    python cron.py check_spf --all-users --settings=dripemails.live
    python cron.py check_spf --user-id 123 --settings=dripemails.live
    
    # Process Scheduled Emails
    python cron.py send_scheduled_emails
    python cron.py send_scheduled_emails --settings=dripemails.live
    python cron.py send_scheduled_emails --limit 100
    
    # Process Gmail Emails
    python cron.py process_gmail_emails
    python cron.py process_gmail_emails --settings=dripemails.live
    python cron.py process_gmail_emails --limit 50
    python cron.py process_gmail_emails --periodic
    python cron.py process_gmail_emails --periodic --interval 120
    
    # Crawl IMAP Emails
    python cron.py crawl_imap
    python cron.py crawl_imap --settings=dripemails.live
    python cron.py crawl_imap --limit 50
    python cron.py crawl_imap --periodic
    python cron.py crawl_imap --periodic --interval 120
    
    # Garbage Collection
    python cron.py garbage_collect
    python cron.py garbage_collect --settings=dripemails.live
    python cron.py garbage_collect --limit 1000
    python cron.py garbage_collect --periodic
    python cron.py garbage_collect --periodic --interval 86400
"""

import os
import sys
import django
import dns.resolver
import dns.exception
from typing import Optional, Dict, List, Tuple
import logging
from datetime import datetime
from logging.handlers import RotatingFileHandler
import argparse
import time

# Setup Django - Parse settings argument first
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Parse --settings argument before Django setup
settings_module = 'dripemails.settings'
if '--settings' in sys.argv:
    try:
        idx = sys.argv.index('--settings')
        if idx + 1 < len(sys.argv):
            # Handle both --settings=value and --settings value formats
            settings_value = sys.argv[idx + 1]
            if '=' in settings_value:
                settings_module = settings_value.split('=', 1)[1]
            else:
                settings_module = settings_value
    except (ValueError, IndexError):
        pass

os.environ.setdefault('DJANGO_SETTINGS_MODULE', settings_module)
django.setup()

from django.contrib.auth.models import User
from django.utils import timezone
from analytics.models import UserProfile
from campaigns.models import EmailSendRequest
from campaigns.tasks import _send_single_email_sync

# Import SPF utilities from core module
try:
    from core.spf_utils import (
        extract_domain as spf_extract_domain,
        get_spf_record as spf_get_spf_record,
        check_spf_includes as spf_check_spf_includes,
        REQUIRED_SPF_INCLUDES as SPF_REQUIRED_INCLUDES
    )
    USE_SHARED_SPF_UTILS = True
except ImportError:
    # Fallback to local functions if import fails
    USE_SHARED_SPF_UTILS = False

# Setup logging to file
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOGS_DIR = os.path.join(BASE_DIR, 'logs')
os.makedirs(LOGS_DIR, exist_ok=True)

LOG_FILE = os.path.join(LOGS_DIR, 'spf_check.log')

# Configure logging with both file and console handlers
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Clear any existing handlers
logger.handlers = []

# File handler with rotation (10MB max, keep 5 backups)
file_handler = RotatingFileHandler(
    LOG_FILE,
    maxBytes=10 * 1024 * 1024,  # 10MB
    backupCount=5,
    encoding='utf-8'
)
file_handler.setLevel(logging.INFO)
file_formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
file_handler.setFormatter(file_formatter)

# Console handler (for immediate feedback)
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)
console_formatter = logging.Formatter(
    '%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
console_handler.setFormatter(console_formatter)

# Add handlers to logger
logger.addHandler(file_handler)
logger.addHandler(console_handler)

logger.info(f"Logging to file: {LOG_FILE}")

# Required SPF includes for DripEmails.org
# Users should include: web.dripemails.org and web1.dripemails.org
# Note: We removed 'dripemails.org' from the required list as the new format
# only requires the web and web1 subdomains
REQUIRED_SPF_INCLUDES = [
    'web.dripemails.org',
    'web1.dripemails.org'
]


def extract_domain(email: str) -> Optional[str]:
    """Extract domain from email address."""
    if '@' not in email:
        return None
    return email.split('@')[1].lower().strip()


def get_spf_record(domain: str) -> Optional[str]:
    """
    Get SPF record for a domain via DNS TXT lookup.
    
    Returns the SPF record string if found, None otherwise.
    Checks all TXT records and returns the first valid SPF record.
    """
    try:
        # Try to get TXT records
        txt_records = dns.resolver.resolve(domain, 'TXT')
        
        logger.info(f"Found {len(txt_records)} TXT record(s) for {domain}")
        
        spf_records = []
        
        # Look for all SPF records (starts with "v=spf1")
        for record in txt_records:
            # Join all string parts - decode bytes to strings properly
            record_parts = []
            for part in record.strings:
                if isinstance(part, bytes):
                    # Decode bytes to string
                    try:
                        decoded = part.decode('utf-8')
                        record_parts.append(decoded)
                    except UnicodeDecodeError:
                        # Fallback to latin-1 if utf-8 fails
                        decoded = part.decode('latin-1')
                        record_parts.append(decoded)
                else:
                    record_parts.append(str(part))
            record_str = ''.join(record_parts)
            # Remove surrounding quotes if present
            record_str = record_str.strip('"').strip("'").strip()
            
            # Remove any 'b' prefix that might be left from string representation
            if record_str.startswith("b'") and record_str.endswith("'"):
                record_str = record_str[2:-1].strip()
            elif record_str.startswith('b"') and record_str.endswith('"'):
                record_str = record_str[2:-1].strip()
            
            # Log what we found for debugging
            logger.info(f"Found TXT record for {domain}: {record_str}")
            
            # Check if it starts with v=spf1 (case insensitive)
            record_lower = record_str.lower().strip()
            if record_lower.startswith('v=spf1'):
                logger.info(f"Found SPF record for {domain}: {record_str}")
                spf_records.append(record_str)
            else:
                logger.debug(f"TXT record does not start with 'v=spf1': {record_str[:100]}...")
        
        # Return the first SPF record found, or None if none found
        if spf_records:
            logger.info(f"Found {len(spf_records)} SPF record(s) for {domain}, using first one")
            return spf_records[0]
        
    except dns.resolver.NoAnswer:
        logger.warning(f"No TXT records found for {domain}")
    except dns.resolver.NXDOMAIN:
        logger.warning(f"Domain {domain} does not exist (NXDOMAIN)")
    except dns.exception.DNSException as e:
        logger.warning(f"DNS error for {domain}: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error checking SPF for {domain}: {str(e)}", exc_info=True)
    
    logger.warning(f"No SPF record found for {domain}")
    return None


def parse_spf_record(spf_record: str) -> Dict[str, List[str]]:
    """
    Parse SPF record and extract includes, mechanisms, etc.
    
    Returns a dict with:
    - 'includes': list of included domains
    - 'mechanisms': list of SPF mechanisms (a, mx, ip4, etc.)
    - 'all': the 'all' mechanism (~all, -all, +all)
    """
    result = {
        'includes': [],
        'mechanisms': [],
        'all': None
    }
    
    if not spf_record.startswith('v=spf1'):
        return result
    
    # Split by spaces and process each part
    parts = spf_record.split()
    
    for part in parts[1:]:  # Skip 'v=spf1'
        part = part.strip()
        if not part:
            continue
        
        # Check for include mechanism
        if part.startswith('include:'):
            include_domain = part.replace('include:', '').strip()
            result['includes'].append(include_domain)
        
        # Check for 'all' mechanism
        elif part in ['~all', '-all', '+all', '?all']:
            result['all'] = part
        
        # Track other mechanisms
        elif ':' in part:
            mechanism = part.split(':')[0]
            result['mechanisms'].append(part)
        else:
            result['mechanisms'].append(part)
    
    return result


def check_spf_includes(spf_record: str) -> Tuple[bool, List[str], List[str]]:
    """
    Check if SPF record includes all required DripEmails.org servers.
    
    Returns:
        (is_valid, missing_includes, found_includes)
    """
    # Clean up the SPF record string
    spf_record = spf_record.strip()
    
    logger.info(f"Checking SPF record: {spf_record}")
    
    parsed = parse_spf_record(spf_record)
    found_includes = []
    missing_includes = []
    
    logger.info(f"Parsed includes: {parsed['includes']}")
    logger.info(f"Required includes: {REQUIRED_SPF_INCLUDES}")
    
    # Check each required include
    for required in REQUIRED_SPF_INCLUDES:
        # Check if it's directly included
        if required in parsed['includes']:
            found_includes.append(required)
            logger.info(f"Found required include: {required}")
        else:
            # Also check if it might be included via a subdomain match
            # (e.g., if dripemails.org is included, web.dripemails.org might be covered)
            found = False
            for included in parsed['includes']:
                if required.endswith('.' + included) or required == included:
                    found = True
                    found_includes.append(required)
                    logger.info(f"Found required include via subdomain match: {required} (matched {included})")
                    break
            
            if not found:
                missing_includes.append(required)
                logger.warning(f"Missing required include: {required}")
    
    is_valid = len(missing_includes) == 0
    logger.info(f"SPF validation result: valid={is_valid}, missing={missing_includes}, found={found_includes}")
    return is_valid, missing_includes, found_includes


def check_user_spf(user: User) -> Dict:
    """
    Check SPF record for a user's email domain.
    
    Returns a dict with:
    - 'user_id': user ID
    - 'email': user email
    - 'domain': extracted domain
    - 'has_spf': whether SPF record exists
    - 'spf_record': the SPF record string
    - 'is_valid': whether SPF includes all required servers
    - 'missing_includes': list of missing required includes
    - 'found_includes': list of found required includes
    - 'error': error message if any
    """
    result = {
        'user_id': user.id,
        'email': user.email,
        'domain': None,
        'has_spf': False,
        'spf_record': None,
        'is_valid': False,
        'missing_includes': [],
        'found_includes': [],
        'error': None
    }
    
    if not user.email:
        result['error'] = 'User has no email address'
        return result
    
    domain = extract_domain(user.email)
    if not domain:
        result['error'] = 'Could not extract domain from email'
        return result
    
    result['domain'] = domain
    
    logger.info(f"Checking SPF for user {user.id} ({user.email}), domain: {domain}")
    
    # Get SPF record
    spf_record = get_spf_record(domain)
    if not spf_record:
        result['error'] = f'No SPF record found for domain {domain}'
        logger.warning(f"User {user.id} ({user.email}): {result['error']}")
        return result
    
    result['has_spf'] = True
    result['spf_record'] = spf_record
    
    # Check if it includes required servers
    is_valid, missing, found = check_spf_includes(spf_record)
    result['is_valid'] = is_valid
    result['missing_includes'] = missing
    result['found_includes'] = found
    
    return result


def update_user_spf_status(user: User, result: Dict):
    """
    Update user profile with SPF verification status.
    
    We'll store this in a JSON field or add a new field to UserProfile.
    For now, we'll log it and could extend UserProfile model later.
    """
    profile, _ = UserProfile.objects.get_or_create(user=user)
    
    # Update SPF verification fields
    profile.spf_verified = result['is_valid']
    profile.spf_last_checked = timezone.now()
    profile.spf_record = result['spf_record'] or ''
    profile.spf_missing_includes = result['missing_includes']
    profile.save(update_fields=['spf_verified', 'spf_last_checked', 'spf_record', 'spf_missing_includes'])
    
    # Verify the save worked
    profile.refresh_from_db()
    logger.info(f"User {user.id} ({user.email}): SPF valid={result['is_valid']}, "
                f"missing={result['missing_includes']}, found={result['found_includes']}")
    logger.info(f"User {user.id} ({user.email}): Saved spf_verified={profile.spf_verified} (verified in DB)")


def check_all_users():
    """Check SPF records for all users."""
    users = User.objects.filter(is_active=True).exclude(email='')
    total = users.count()
    logger.info(f"Checking SPF records for {total} users...")
    
    valid_count = 0
    invalid_count = 0
    no_spf_count = 0
    error_count = 0
    
    for user in users:
        result = check_user_spf(user)
        update_user_spf_status(user, result)
        
        if result['error']:
            error_count += 1
            logger.warning(f"User {user.id} ({user.email}): {result['error']}")
        elif not result['has_spf']:
            no_spf_count += 1
        elif result['is_valid']:
            valid_count += 1
        else:
            invalid_count += 1
            logger.warning(f"User {user.id} ({user.email}): Missing SPF includes: {result['missing_includes']}")
    
    logger.info(f"SPF Check Summary:")
    logger.info(f"  Total users checked: {total}")
    logger.info(f"  Valid SPF records: {valid_count}")
    logger.info(f"  Invalid SPF records: {invalid_count}")
    logger.info(f"  No SPF record: {no_spf_count}")
    logger.info(f"  Errors: {error_count}")


def check_user_by_id(user_id: int):
    """Check SPF record for a specific user."""
    try:
        user = User.objects.get(id=user_id)
        result = check_user_spf(user)
        update_user_spf_status(user, result)
        
        print(f"\nSPF Check Results for User {user_id}:")
        print(f"  Email: {result['email']}")
        print(f"  Domain: {result['domain']}")
        print(f"  Has SPF: {result['has_spf']}")
        if result['spf_record']:
            print(f"  SPF Record: {result['spf_record']}")
        print(f"  Is Valid: {result['is_valid']}")
        if result['found_includes']:
            print(f"  Found Includes: {', '.join(result['found_includes'])}")
        if result['missing_includes']:
            print(f"  Missing Includes: {', '.join(result['missing_includes'])}")
        if result['error']:
            print(f"  Error: {result['error']}")
        print()
        
    except User.DoesNotExist:
        logger.error(f"User with ID {user_id} not found")
        sys.exit(1)


def process_gmail_emails(limit=None):
    """
    Fetch and process Gmail emails for all active Gmail credentials.
    Sends auto-reply emails to From, To, and Sender email addresses.
    """
    from gmail.models import EmailCredential, EmailMessage, EmailProvider
    from gmail.services import GmailService
    from campaigns.models import Campaign, Email
    from subscribers.models import List, Subscriber
    from campaigns.tasks import send_campaign_email
    import re
    
    # Get all active Gmail credentials
    credentials = EmailCredential.objects.filter(
        provider=EmailProvider.GMAIL,
        is_active=True,
        sync_enabled=True
    ).select_related('user')
    
    total_credentials = credentials.count()
    logger.info(f"Processing Gmail emails for {total_credentials} credentials")
    
    if total_credentials == 0:
        logger.info("No active Gmail credentials found")
        return
    
    total_processed = 0
    total_sent = 0
    error_count = 0
    
    service = GmailService()
    
    for credential in credentials:
        try:
            # Fetch latest emails
            logger.info(f"Fetching emails for {credential.email_address}")
            email_messages = service.fetch_emails(credential, max_results=limit or 50)
            
            # Update last sync time
            credential.last_sync_at = timezone.now()
            credential.save(update_fields=['last_sync_at'])
            
            # Process each email
            for email_msg in email_messages:
                if email_msg.processed:
                    continue
                
                try:
                    # Get recipient emails (From, To, Sender)
                    recipients = set()
                    recipients.add(email_msg.from_email)
                    recipients.update(email_msg.to_emails_list)
                    if email_msg.sender_email:
                        recipients.add(email_msg.sender_email)
                    
                    # Find or get Gmail campaign for this credential
                    gmail_campaign = Campaign.objects.filter(
                        user=credential.user,
                        name__icontains='Gmail Auto-Reply',
                        subscriber_list__name__icontains='Gmail'
                    ).first()
                    
                    if not gmail_campaign:
                        logger.warning(f"No Gmail campaign found for user {credential.user.id}")
                        email_msg.processed = True
                        email_msg.save(update_fields=['processed'])
                        continue
                    
                    # Get the first email template from the campaign
                    campaign_email = gmail_campaign.emails.first()
                    if not campaign_email:
                        logger.warning(f"No email template found in Gmail campaign {gmail_campaign.id}")
                        email_msg.processed = True
                        email_msg.save(update_fields=['processed'])
                        continue
                    
                    # Get or create Gmail subscriber list
                    gmail_list = gmail_campaign.subscriber_list
                    if not gmail_list:
                        logger.warning(f"No subscriber list found for Gmail campaign {gmail_campaign.id}")
                        email_msg.processed = True
                        email_msg.save(update_fields=['processed'])
                        continue
                    
                    # Send auto-reply to each recipient
                    for recipient_email in recipients:
                        if not recipient_email or recipient_email == credential.email_address:
                            continue  # Don't send to self
                        
                        # Extract first name from email or use email prefix
                        first_name = recipient_email.split('@')[0].split('.')[0].title()
                        
                        # Get or create subscriber
                        subscriber, created = Subscriber.objects.get_or_create(
                            email=recipient_email,
                            defaults={
                                'first_name': first_name,
                                'is_active': True,
                                'confirmed': True
                            }
                        )
                        
                        # Add to Gmail list if not already
                        if gmail_list not in subscriber.lists.all():
                            subscriber.lists.add(gmail_list)
                        
                        # Send the email
                        try:
                            send_campaign_email(
                                str(campaign_email.id),
                                str(subscriber.id),
                                variables={'first_name': subscriber.first_name or first_name, 'subject': email_msg.subject},
                                original_email_message=email_msg  # Pass the original incoming email message
                            )
                            total_sent += 1
                            logger.info(f"Sent auto-reply to {recipient_email} for Gmail message {email_msg.id}")
                        except Exception as e:
                            logger.error(f"Error sending auto-reply to {recipient_email}: {str(e)}")
                    
                    # Mark email as processed
                    email_msg.processed = True
                    email_msg.campaign_email = campaign_email
                    email_msg.save(update_fields=['processed', 'campaign_email'])
                    total_processed += 1
                    
                except Exception as e:
                    logger.error(f"Error processing Gmail email {email_msg.id}: {str(e)}")
                    error_count += 1
                    continue
            
        except Exception as e:
            logger.error(f"Error processing Gmail for credential {credential.id}: {str(e)}")
            error_count += 1
            continue
    
    logger.info(f"Gmail Processing Summary:")
    logger.info(f"  Credentials processed: {total_credentials}")
    logger.info(f"  Emails processed: {total_processed}")
    logger.info(f"  Auto-replies sent: {total_sent}")
    logger.info(f"  Errors: {error_count}")


def crawl_imap(limit=None):
    """
    Fetch and process IMAP emails for all active IMAP credentials.
    Sends auto-reply emails to From, To, and Sender email addresses.
    """
    from gmail.models import EmailCredential, EmailMessage, EmailProvider
    from gmail.imap_service import IMAPService
    from campaigns.models import Campaign, Email
    from subscribers.models import List, Subscriber
    from campaigns.tasks import send_campaign_email
    import re
    
    # Get all active IMAP credentials
    credentials = EmailCredential.objects.filter(
        provider=EmailProvider.IMAP,
        is_active=True,
        sync_enabled=True
    ).select_related('user')
    
    total_credentials = credentials.count()
    logger.info(f"Processing IMAP emails for {total_credentials} credentials")
    
    if total_credentials == 0:
        logger.info("No active IMAP credentials found")
        return
    
    total_processed = 0
    total_sent = 0
    error_count = 0
    
    service = IMAPService()
    
    for credential in credentials:
        try:
            logger.info(f"=" * 80)
            logger.info(f"Processing IMAP credential: {credential.id} for {credential.email_address} (User: {credential.user.id})")
            logger.info(f"IMAP Host: {credential.imap_host}:{credential.imap_port}, SSL: {credential.imap_use_ssl}")
            logger.info(f"Last sync: {credential.last_sync_at}")
            
            # List all available folders
            all_folders = service.list_all_folders(credential)
            logger.info(f"Available IMAP folders for {credential.email_address} ({len(all_folders)} total):")
            for idx, folder_name in enumerate(all_folders, 1):
                logger.info(f"  {idx}. {folder_name}")
            logger.info(f"--- End of folder list ---")
            
            # Fetch latest emails - pass the folder list so fetch_emails can find the sent folder
            logger.info(f"Fetching emails for {credential.email_address} (max_results: {limit or 50})")
            email_messages = service.fetch_emails(credential, max_results=limit or 50, all_folders=all_folders)
            logger.info(f"Fetched {len(email_messages)} email messages from IMAP")
            
            # Update last sync time
            credential.last_sync_at = timezone.now()
            credential.save(update_fields=['last_sync_at'])
            logger.info(f"Updated last_sync_at to {credential.last_sync_at}")
            
            # Process each email
            for idx, email_msg in enumerate(email_messages, 1):
                logger.info(f"--- Processing email {idx}/{len(email_messages)}: {email_msg.id} ---")
                logger.info(f"  Subject: {email_msg.subject}")
                logger.info(f"  From: {email_msg.from_email}")
                logger.info(f"  To: {email_msg.to_emails}")
                logger.info(f"  Received at: {email_msg.received_at}")
                logger.info(f"  Provider message ID: {email_msg.provider_message_id}")
                logger.info(f"  Already processed: {email_msg.processed}")
                logger.info(f"  Has campaign_email: {email_msg.campaign_email is not None}")
                
                # Skip if already processed (prevents duplicates when same email appears in multiple folders)
                if email_msg.processed and email_msg.campaign_email:
                    logger.info(f"  SKIPPING: Email message {email_msg.id} already processed with campaign_email {email_msg.campaign_email.id}")
                    continue
                
                try:
                    # Get folder and names from provider_data
                    provider_data = email_msg.provider_data or {}
                    folder = provider_data.get('folder', 'INBOX')
                    from_name = provider_data.get('from_name', '')
                    sender_name = provider_data.get('sender_name', '')
                    to_names = provider_data.get('to_names', {})
                    
                    logger.info(f"  Folder: {folder}")
                    logger.info(f"  From name: {from_name}")
                    logger.info(f"  Sender name: {sender_name}")
                    logger.info(f"  To names: {to_names}")
                    
                    # Determine recipients and their names based on folder
                    recipients_with_names = {}
                    logger.info(f"  Determining recipients based on folder '{folder}'...")
                    
                    if folder.upper() == 'INBOX':
                        logger.info(f"  INBOX folder: Processing as incoming email")
                        # For incoming emails, reply to From/Sender
                        if email_msg.from_email and email_msg.from_email != credential.email_address:
                            recipients_with_names[email_msg.from_email] = from_name or sender_name
                            logger.info(f"    Added recipient (From): {email_msg.from_email} ({from_name or sender_name})")
                        else:
                            logger.info(f"    Skipped From email (self or empty): {email_msg.from_email}")
                        if email_msg.sender_email and email_msg.sender_email != credential.email_address:
                            recipients_with_names[email_msg.sender_email] = sender_name or from_name
                            logger.info(f"    Added recipient (Sender): {email_msg.sender_email} ({sender_name or from_name})")
                        else:
                            logger.info(f"    Skipped Sender email (self or empty): {email_msg.sender_email}")
                    else:
                        # For Sent folder or All Mail folder, reply to To recipients
                        # But only if this is a sent email (not an incoming email that also appears in All Mail)
                        # We can distinguish by checking if the from_email matches the credential email
                        is_sent_email = email_msg.from_email == credential.email_address or email_msg.sender_email == credential.email_address
                        logger.info(f"  {folder} folder: is_sent_email={is_sent_email} (from_email={email_msg.from_email}, credential={credential.email_address})")
                        if is_sent_email:
                            logger.info(f"    Processing as sent email: replying to To recipients")
                            # For Sent folder (or other folders), reply to To recipients
                            for to_email in email_msg.to_emails_list:
                                if to_email and to_email != credential.email_address:
                                    to_name = to_names.get(to_email, '')
                                    recipients_with_names[to_email] = to_name
                                    logger.info(f"    Added recipient (To): {to_email} ({to_name})")
                                else:
                                    logger.info(f"    Skipped To email (self or empty): {to_email}")
                        else:
                            logger.info(f"    Processing as incoming email in {folder}: replying to From/Sender")
                            # This is an incoming email that also appears in All Mail, treat it like INBOX
                            if email_msg.from_email and email_msg.from_email != credential.email_address:
                                recipients_with_names[email_msg.from_email] = from_name or sender_name
                                logger.info(f"    Added recipient (From): {email_msg.from_email} ({from_name or sender_name})")
                            if email_msg.sender_email and email_msg.sender_email != credential.email_address:
                                recipients_with_names[email_msg.sender_email] = sender_name or from_name
                                logger.info(f"    Added recipient (Sender): {email_msg.sender_email} ({sender_name or from_name})")
                    
                    logger.info(f"  Total recipients determined: {len(recipients_with_names)}")
                    if not recipients_with_names:
                        logger.warning(f"  No valid recipients found, marking email as processed and skipping")
                        # No valid recipients, mark as processed
                        email_msg.processed = True
                        email_msg.save(update_fields=['processed'])
                        continue
                    
                    # Find or get IMAP campaign for this credential
                    logger.info(f"  Looking for IMAP campaign for user {credential.user.id}...")
                    imap_campaign = Campaign.objects.filter(
                        user=credential.user,
                        name__icontains='IMAP Auto-Reply',
                        subscriber_list__name__icontains='IMAP'
                    ).first()
                    
                    if not imap_campaign:
                        logger.warning(f"  No IMAP campaign found for user {credential.user.id}, marking as processed and skipping")
                        email_msg.processed = True
                        email_msg.save(update_fields=['processed'])
                        continue
                    
                    logger.info(f"  Found IMAP campaign: {imap_campaign.id} - {imap_campaign.name}")
                    
                    # Get the first email template from the campaign
                    campaign_email = imap_campaign.emails.first()
                    if not campaign_email:
                        logger.warning(f"  No email template found in IMAP campaign {imap_campaign.id}, marking as processed and skipping")
                        email_msg.processed = True
                        email_msg.save(update_fields=['processed'])
                        continue
                    
                    logger.info(f"  Found campaign email template: {campaign_email.id} - {campaign_email.subject}")
                    
                    # Get or create IMAP subscriber list
                    imap_list = imap_campaign.subscriber_list
                    if not imap_list:
                        logger.warning(f"  No subscriber list found for IMAP campaign {imap_campaign.id}, marking as processed and skipping")
                        email_msg.processed = True
                        email_msg.save(update_fields=['processed'])
                        continue
                    
                    logger.info(f"  Using subscriber list: {imap_list.id} - {imap_list.name}")
                    
                    # Send auto-reply to each recipient
                    logger.info(f"  Processing {len(recipients_with_names)} recipient(s)...")
                    for recipient_idx, (recipient_email, recipient_name) in enumerate(recipients_with_names.items(), 1):
                        logger.info(f"    Recipient {recipient_idx}/{len(recipients_with_names)}: {recipient_email}")
                        if not recipient_email:
                            logger.warning(f"      Skipping empty recipient email")
                            continue
                        
                        # Parse name into first_name and last_name
                        name_parts = recipient_name.strip().split() if recipient_name else []
                        first_name = name_parts[0] if name_parts else ''
                        last_name = ' '.join(name_parts[1:]) if len(name_parts) > 1 else ''
                        
                        # Fallback to email prefix if no name found
                        if not first_name:
                            first_name = recipient_email.split('@')[0].split('.')[0].title()
                        
                        logger.info(f"      Parsed name: first_name='{first_name}', last_name='{last_name}'")
                        
                        # Get or create subscriber
                        subscriber, created = Subscriber.objects.get_or_create(
                            email=recipient_email,
                            defaults={
                                'first_name': first_name,
                                'last_name': last_name,
                                'is_active': True,
                                'confirmed': True
                            }
                        )
                        
                        if created:
                            logger.info(f"      Created new subscriber: {subscriber.id}")
                        else:
                            logger.info(f"      Found existing subscriber: {subscriber.id}")
                        
                        # Update subscriber name if we have better information
                        if not created and recipient_name:
                            updated = False
                            if first_name and subscriber.first_name != first_name:
                                subscriber.first_name = first_name
                                updated = True
                            if last_name and subscriber.last_name != last_name:
                                subscriber.last_name = last_name
                                updated = True
                            if updated:
                                subscriber.save()
                                logger.info(f"      Updated subscriber name")
                        
                        # Add to IMAP list if not already
                        if imap_list not in subscriber.lists.all():
                            subscriber.lists.add(imap_list)
                            logger.info(f"      Added subscriber to IMAP list")
                        else:
                            logger.info(f"      Subscriber already in IMAP list")
                        
                        # Note: We don't check for duplicate sends based on EmailEvent because:
                        # 1. Each email message is only processed once (checked at the top of the loop)
                        # 2. We want to reply to each new email, even if we've replied to that sender before
                        # 3. The duplicate prevention is handled by the email_msg.processed flag
                        # This allows legitimate replies to multiple emails from the same sender
                        
                        # Send the email with proper name variables
                        try:
                            logger.info(f"      Verifying email and subscriber exist before sending...")
                            # Verify email and subscriber still exist before sending
                            from campaigns.models import Email
                            from subscribers.models import Subscriber
                            
                            try:
                                Email.objects.get(id=campaign_email.id)
                                Subscriber.objects.get(id=subscriber.id, is_active=True)
                                logger.info(f"      Email and subscriber verified")
                            except (Email.DoesNotExist, Subscriber.DoesNotExist) as e:
                                logger.warning(f"      Email {campaign_email.id} or Subscriber {subscriber.id} not found, skipping auto-reply to {recipient_email}")
                                continue
                            
                            logger.info(f"      Sending auto-reply email...")
                            send_campaign_email(
                                str(campaign_email.id),
                                str(subscriber.id),
                                variables={
                                    'first_name': subscriber.first_name or first_name,
                                    'last_name': subscriber.last_name or last_name,
                                    'subject': email_msg.subject
                                },
                                original_email_message=email_msg  # Pass the original incoming email message
                            )
                            total_sent += 1
                            logger.info(f"      ✓ Successfully sent auto-reply to {recipient_email} ({first_name}) for IMAP message {email_msg.id} from folder {folder}")
                        except Exception as e:
                            logger.error(f"      ✗ Error sending auto-reply to {recipient_email}: {str(e)}", exc_info=True)
                            # Continue processing other recipients
                            continue
                    
                    # Mark email as processed
                    logger.info(f"  Marking email {email_msg.id} as processed")
                    email_msg.processed = True
                    email_msg.campaign_email = campaign_email
                    email_msg.save(update_fields=['processed', 'campaign_email'])
                    total_processed += 1
                    logger.info(f"  ✓ Completed processing email {email_msg.id}")
                    
                except Exception as e:
                    logger.error(f"  ✗ Error processing IMAP email {email_msg.id}: {str(e)}", exc_info=True)
                    error_count += 1
                    continue
            
            logger.info(f"Completed processing credential {credential.id}: {len(email_messages)} emails fetched, {total_processed} processed, {total_sent} auto-replies sent")
            
        except Exception as e:
            logger.error(f"✗ Error processing IMAP for credential {credential.id} ({credential.email_address}): {str(e)}", exc_info=True)
            error_count += 1
            continue
    
    logger.info(f"=" * 80)
    logger.info(f"IMAP Processing Summary:")
    logger.info(f"  Credentials processed: {total_credentials}")
    logger.info(f"  Emails processed: {total_processed}")
    logger.info(f"  Auto-replies sent: {total_sent}")
    logger.info(f"  Errors: {error_count}")
    logger.info(f"=" * 80)


def send_scheduled_emails(limit=None):
    """
    Process and send scheduled emails that are due to be sent.
    
    Finds EmailSendRequest objects with status 'pending' or 'queued'
    where scheduled_for <= now() and sends them.
    """
    now = timezone.now()
    
    # Find emails that are due to be sent
    due_emails = EmailSendRequest.objects.filter(
        status__in=['pending', 'queued'],
        scheduled_for__lte=now
    ).select_related('email', 'campaign', 'user', 'subscriber').order_by('scheduled_for')
    
    if limit:
        due_emails = due_emails[:limit]
    
    total = due_emails.count()
    logger.info(f"Found {total} scheduled emails due to be sent")
    
    if total == 0:
        logger.info("No scheduled emails to send")
        return
    
    sent_count = 0
    failed_count = 0
    
    for send_request in due_emails:
        try:
            # Update status to 'queued' to prevent duplicate processing
            send_request.status = 'queued'
            send_request.save(update_fields=['status', 'updated_at'])
            
            # Send the email using the sync function
            _send_single_email_sync(
                str(send_request.email.id),
                send_request.subscriber_email,
                send_request.variables,
                request_id=str(send_request.id)
            )
            
            # The _send_single_email_sync function updates the status to 'sent' on success
            sent_count += 1
            logger.info(f"Sent scheduled email {send_request.id} to {send_request.subscriber_email}")
            
        except Exception as e:
            # Update status to 'failed' on error
            send_request.status = 'failed'
            send_request.error_message = str(e)
            send_request.save(update_fields=['status', 'error_message', 'updated_at'])
            
            failed_count += 1
            logger.error(f"Failed to send scheduled email {send_request.id} to {send_request.subscriber_email}: {str(e)}")
    
    logger.info(f"Scheduled Email Processing Summary:")
    logger.info(f"  Total due: {total}")
    logger.info(f"  Successfully sent: {sent_count}")
    logger.info(f"  Failed: {failed_count}")


def garbage_collect(limit=None):
    """
    Garbage collection: Delete old email messages and send activity records.
    
    Deletes:
    - EmailMessage objects older than DATA_RETENTION_DAYS days
    - EmailSendRequest objects older than DATA_RETENTION_DAYS days
    
    Args:
        limit: Optional limit on number of records to delete per type
    """
    from gmail.models import EmailMessage
    from campaigns.models import EmailSendRequest
    from django.conf import settings
    from datetime import timedelta
    
    # Get retention period from settings
    retention_days = getattr(settings, 'DATA_RETENTION_DAYS', 30)
    cutoff_date = timezone.now() - timedelta(days=retention_days)
    
    logger.info(f"Starting garbage collection for records older than {retention_days} days (before {cutoff_date})")
    
    # Delete old EmailMessage records
    old_email_messages = EmailMessage.objects.filter(received_at__lt=cutoff_date)
    email_message_count = old_email_messages.count()
    
    if limit:
        old_email_messages = old_email_messages[:limit]
    
    deleted_email_messages = old_email_messages.delete()[0]
    logger.info(f"Deleted {deleted_email_messages} EmailMessage records (out of {email_message_count} total matching)")
    
    # Delete old EmailSendRequest records
    old_send_requests = EmailSendRequest.objects.filter(created_at__lt=cutoff_date)
    send_request_count = old_send_requests.count()
    
    if limit:
        old_send_requests = old_send_requests[:limit]
    
    deleted_send_requests = old_send_requests.delete()[0]
    logger.info(f"Deleted {deleted_send_requests} EmailSendRequest records (out of {send_request_count} total matching)")
    
    logger.info(f"Garbage collection complete:")
    logger.info(f"  EmailMessage records deleted: {deleted_email_messages} (of {email_message_count} matching)")
    logger.info(f"  EmailSendRequest records deleted: {deleted_send_requests} (of {send_request_count} matching)")


def main():
    """Main entry point for the cron script."""
    # Re-parse arguments now that we have the full command line
    # (we already parsed --settings above, but need to handle the rest)
    parser = argparse.ArgumentParser(description='DripEmails Cron Script')
    parser.add_argument('--settings', type=str, default='dripemails.settings',
                        help='Django settings module (default: dripemails.settings)')
    parser.add_argument('command', nargs='?', help='Command to run (check_spf, send_scheduled_emails, process_gmail_emails, crawl_imap)')
    parser.add_argument('--user-id', type=int, help='Check SPF for specific user ID')
    parser.add_argument('--all-users', action='store_true', help='Check SPF for all users')
    parser.add_argument('--limit', type=int, help='Limit number of scheduled emails to process')
    parser.add_argument('--periodic', action='store_true', help='Run continuously with periodic execution (for process_gmail_emails or crawl_imap)')
    parser.add_argument('--interval', type=int, default=120, help='Interval in seconds between executions when using --periodic (default: 120 = 2 minutes)')
    
    args = parser.parse_args()
    
    if not args.command:
        print(__doc__)
        parser.print_help()
        sys.exit(1)
    
    if args.command == 'check_spf':
        if args.all_users:
            check_all_users()
        elif args.user_id:
            check_user_by_id(args.user_id)
        else:
            logger.error("Please specify --all-users or --user-id <id>")
            parser.print_help()
            sys.exit(1)
    elif args.command == 'send_scheduled_emails':
        send_scheduled_emails(limit=args.limit)
    elif args.command == 'process_gmail_emails':
        if args.periodic:
            logger.info(f"Starting periodic Gmail email processing (interval: {args.interval} seconds)")
            try:
                while True:
                    try:
                        logger.info(f"Running Gmail email processing cycle at {timezone.now()}")
                        process_gmail_emails(limit=args.limit)
                        logger.info(f"Completed Gmail email processing cycle. Sleeping for {args.interval} seconds...")
                    except KeyboardInterrupt:
                        logger.info("Received interrupt signal. Stopping periodic execution.")
                        raise
                    except Exception as e:
                        logger.error(f"Error in periodic Gmail email processing cycle: {str(e)}", exc_info=True)
                        logger.info(f"Continuing despite error. Will retry in {args.interval} seconds...")
                    
                    time.sleep(args.interval)
            except KeyboardInterrupt:
                logger.info("Periodic Gmail email processing stopped by user")
                sys.exit(0)
        else:
            process_gmail_emails(limit=args.limit)
    elif args.command == 'crawl_imap':
        if args.periodic:
            logger.info(f"Starting periodic IMAP email crawling (interval: {args.interval} seconds)")
            try:
                while True:
                    try:
                        logger.info(f"Running IMAP email crawling cycle at {timezone.now()}")
                        crawl_imap(limit=args.limit)
                        logger.info(f"Completed IMAP email crawling cycle. Sleeping for {args.interval} seconds...")
                    except KeyboardInterrupt:
                        logger.info("Received interrupt signal. Stopping periodic execution.")
                        raise
                    except Exception as e:
                        logger.error(f"Error in periodic IMAP email crawling cycle: {str(e)}", exc_info=True)
                        logger.info(f"Continuing despite error. Will retry in {args.interval} seconds...")
                    
                    time.sleep(args.interval)
            except KeyboardInterrupt:
                logger.info("Periodic IMAP email crawling stopped by user")
                sys.exit(0)
        else:
            crawl_imap(limit=args.limit)
    elif args.command == 'garbage_collect':
        if args.periodic:
            logger.info(f"Starting periodic garbage collection (interval: {args.interval} seconds)")
            try:
                while True:
                    try:
                        logger.info(f"Running garbage collection cycle at {timezone.now()}")
                        garbage_collect(limit=args.limit)
                        logger.info(f"Completed garbage collection cycle. Sleeping for {args.interval} seconds...")
                    except KeyboardInterrupt:
                        logger.info("Received interrupt signal. Stopping periodic execution.")
                        raise
                    except Exception as e:
                        logger.error(f"Error in periodic garbage collection cycle: {str(e)}", exc_info=True)
                        logger.info(f"Continuing despite error. Will retry in {args.interval} seconds...")
                    
                    time.sleep(args.interval)
            except KeyboardInterrupt:
                logger.info("Periodic garbage collection stopped by user")
                sys.exit(0)
        else:
            garbage_collect(limit=args.limit)
    else:
        logger.error(f"Unknown command: {args.command}")
        print(__doc__)
        parser.print_help()
        sys.exit(1)


if __name__ == '__main__':
    main()

