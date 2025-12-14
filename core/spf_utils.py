"""
SPF (Sender Policy Framework) utility functions for checking DNS records.

This module provides functions to check SPF records for user domains.
It's used by both cron.py and the dashboard view.
"""

import dns.resolver
import dns.exception
from typing import Optional, Tuple, List
import logging

logger = logging.getLogger(__name__)

# Required SPF includes for DripEmails.org
REQUIRED_SPF_INCLUDES = ['dripemails.org', 'web.dripemails.org', 'web1.dripemails.org']


def extract_domain(email: str) -> Optional[str]:
    """Extract domain from email address."""
    if not email or '@' not in email:
        return None
    return email.split('@')[1].strip().lower()


def get_spf_record(domain: str) -> Optional[str]:
    """
    Get SPF record for a domain via DNS TXT lookup.
    
    Returns the SPF record string if found, None otherwise.
    """
    try:
        # Try to get TXT records
        txt_records = dns.resolver.resolve(domain, 'TXT')
        
        logger.debug(f"Found {len(txt_records)} TXT record(s) for {domain}")
        
        spf_records_found = []
        # Look for SPF record (starts with "v=spf1")
        for record in txt_records:
            # Join all string parts - decode bytes to strings properly
            record_parts = []
            for part in record.strings:
                if isinstance(part, bytes):
                    try:
                        record_parts.append(part.decode('utf-8'))
                    except UnicodeDecodeError:
                        try:
                            record_parts.append(part.decode('latin-1'))  # Fallback for other encodings
                        except Exception:
                            record_parts.append(str(part))  # Fallback to string representation
                else:
                    record_parts.append(str(part))
            record_str = ''.join(record_parts)
            # Remove surrounding quotes if present
            record_str = record_str.strip('"').strip("'").strip()
            
            # Check if it starts with v=spf1 (case insensitive)
            if record_str.lower().startswith('v=spf1'):
                spf_records_found.append(record_str)
        
        if not spf_records_found:
            logger.debug(f"No SPF record found for {domain}")
            return None
        
        # If multiple SPF records are found, try to pick the one that includes all required servers
        if len(spf_records_found) > 1:
            logger.warning(f"Multiple SPF records found for {domain}. Attempting to select the most comprehensive one.")
            best_spf_record = None
            best_missing_count = len(REQUIRED_SPF_INCLUDES) + 1
            
            for spf_rec in spf_records_found:
                is_valid, missing, found = check_spf_includes(spf_rec)
                if is_valid:  # Found a fully valid one, use it
                    logger.debug(f"Selected fully valid SPF record: {spf_rec}")
                    return spf_rec
                elif len(missing) < best_missing_count:  # Found a more comprehensive one
                    best_missing_count = len(missing)
                    best_spf_record = spf_rec
            
            if best_spf_record:
                logger.debug(f"Selected best available SPF record: {best_spf_record}")
                return best_spf_record
            else:
                return spf_records_found[0]  # Fallback to the first one
        else:
            return spf_records_found[0]
            
    except dns.resolver.NoAnswer:
        logger.debug(f"No TXT records found for {domain}")
    except dns.resolver.NXDOMAIN:
        logger.debug(f"Domain {domain} does not exist (NXDOMAIN)")
    except dns.exception.DNSException as e:
        logger.debug(f"DNS error for {domain}: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error checking SPF for {domain}: {str(e)}", exc_info=True)
    
    return None


def parse_spf_record(spf_record: str) -> dict:
    """Parse SPF record into components."""
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


def quick_spf_check(email: str) -> Tuple[bool, Optional[str]]:
    """
    Quick SPF check for a user's email domain.
    
    Returns:
        (is_valid, spf_record) - is_valid is True if SPF record exists and is valid
    """
    domain = extract_domain(email)
    if not domain:
        return False, None
    
    spf_record = get_spf_record(domain)
    if not spf_record:
        return False, None
    
    is_valid, missing, found = check_spf_includes(spf_record)
    return is_valid, spf_record

