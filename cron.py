#!/usr/bin/env python
"""
Cron script to check SPF records for user domains.

This script checks if users have properly configured SPF records
that include DripEmails.org servers.

Usage:
    python cron.py check_spf --all-users
    python cron.py check_spf --user-id 123
    python cron.py check_spf --all-users --settings=dripemails.live
    python cron.py check_spf --user-id 123 --settings=dripemails.live
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
REQUIRED_SPF_INCLUDES = [
    'dripemails.org',
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
    """
    try:
        # Try to get TXT records
        txt_records = dns.resolver.resolve(domain, 'TXT')
        
        # Look for SPF record (starts with "v=spf1")
        for record in txt_records:
            record_str = ''.join([str(part) for part in record.strings])
            if record_str.startswith('v=spf1'):
                return record_str
    except dns.resolver.NoAnswer:
        logger.debug(f"No TXT records found for {domain}")
    except dns.resolver.NXDOMAIN:
        logger.debug(f"Domain {domain} does not exist")
    except dns.exception.DNSException as e:
        logger.warning(f"DNS error for {domain}: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error checking SPF for {domain}: {str(e)}")
    
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
    parsed = parse_spf_record(spf_record)
    found_includes = []
    missing_includes = []
    
    # Check each required include
    for required in REQUIRED_SPF_INCLUDES:
        # Check if it's directly included
        if required in parsed['includes']:
            found_includes.append(required)
        else:
            # Also check if it might be included via a subdomain match
            # (e.g., if dripemails.org is included, web.dripemails.org might be covered)
            found = False
            for included in parsed['includes']:
                if required.endswith('.' + included) or required == included:
                    found = True
                    found_includes.append(required)
                    break
            
            if not found:
                missing_includes.append(required)
    
    is_valid = len(missing_includes) == 0
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
    
    # Get SPF record
    spf_record = get_spf_record(domain)
    if not spf_record:
        result['error'] = 'No SPF record found for domain'
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
    
    logger.info(f"User {user.id} ({user.email}): SPF valid={result['is_valid']}, "
                f"missing={result['missing_includes']}, found={result['found_includes']}")


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


def main():
    """Main entry point for the cron script."""
    # Re-parse arguments now that we have the full command line
    # (we already parsed --settings above, but need to handle the rest)
    parser = argparse.ArgumentParser(description='DripEmails SPF Record Checker')
    parser.add_argument('--settings', type=str, default='dripemails.settings',
                        help='Django settings module (default: dripemails.settings)')
    parser.add_argument('command', nargs='?', help='Command to run (check_spf)')
    parser.add_argument('--user-id', type=int, help='Check SPF for specific user ID')
    parser.add_argument('--all-users', action='store_true', help='Check SPF for all users')
    
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
    else:
        logger.error(f"Unknown command: {args.command}")
        print(__doc__)
        parser.print_help()
        sys.exit(1)


if __name__ == '__main__':
    main()

