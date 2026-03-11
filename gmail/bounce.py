"""
Bounce and Delivery Status Notification (DSN) detection and handling.

When the user's mailbox contains "Undelivered Mail Returned to Sender",
"Delivery Status Notification (Failure)", or similar bounce messages,
we detect them and extract the failed recipient email(s) so they can be
unsubscribed (e.g. set is_active=False) to avoid future sends.
"""
import re
import logging

logger = logging.getLogger(__name__)

# Subject or body phrases that indicate a bounce / DSN (case-insensitive).
BOUNCE_SUBJECT_PATTERNS = [
    r'undelivered\s+mail\s+returned\s+to\s+sender',
    r'delivery\s+status\s+notification\s*\(?\s*failure\s*\)?',
    r'delivery\s+status\s+notification',
    r'mail\s+delivery\s+failed',
    r'mail\s+delivery\s+failure',
    r'mail\s+delivery\s+subsystem',
    r'returned\s+mail',
    r'delivery\s+failure',
    r'message\s+not\s+delivered',
    r'failure\s+notice',
    r'postmaster\s+notice',
]

BOUNCE_BODY_PATTERNS = [
    r'could\s+not\s+be\s+delivered\s+to\s+one\s+or\s+more\s+recipients',
    r'your\s+message\s+could\s+not\s+be\s+delivered',
    r'the\s+mail\s+system',
    r'this\s+is\s+the\s+mail\s+system',
    r'delivery\s+status\s+notification',
    r'undelivered\s+mail',
    r'address\s+not\s+found',
    r'user\s+unknown',
    r'recipient\s+address\s+rejected',
]

# Regex to find email addresses: <addr@domain.com> or standalone addr@domain.com (basic).
EMAIL_IN_ANGLES_RE = re.compile(r'<([a-zA-Z0-9_.+-]+@[a-zA-Z0-9][a-zA-Z0-9.-]*[a-zA-Z0-9])>')
EMAIL_PLAIN_RE = re.compile(r'\b([a-zA-Z0-9_.+-]+@[a-zA-Z0-9][a-zA-Z0-9.-]*[a-zA-Z0-9])\b')

# Common DSN fields where failed recipient addresses appear.
DSN_FIELD_EMAIL_RE = re.compile(
    r'(?:final-recipient|original-recipient|x-failed-recipients|for)\s*[:;]\s*(?:rfc822\s*;\s*)?<?([a-zA-Z0-9_.+-]+@[a-zA-Z0-9][a-zA-Z0-9.-]*[a-zA-Z0-9])>?',
    re.IGNORECASE,
)

SYSTEM_LOCAL_PARTS = {
    'mailer-daemon',
    'postmaster',
    'noreply',
    'no-reply',
    'daemon',
    'bounce',
}


def is_bounce_message(subject: str, body_text: str = '', body_html: str = '') -> bool:
    """
    Return True if the message looks like a bounce or DSN (e.g. Undelivered Mail
    Returned to Sender, Delivery Status Notification (Failure)).
    """
    subject = (subject or '').strip()
    text = (body_text or '') + ' ' + (body_html or '')
    # Strip tags for HTML
    text = re.sub(r'<[^>]+>', ' ', text)
    text = (text or '').strip().lower()
    combined = (subject + ' ' + text).lower()

    for pattern in BOUNCE_SUBJECT_PATTERNS:
        if re.search(pattern, combined, re.IGNORECASE):
            return True
    for pattern in BOUNCE_BODY_PATTERNS:
        if re.search(pattern, combined, re.IGNORECASE):
            return True
    return False


def _get_bounce_match_reasons(subject: str, body_text: str = '', body_html: str = '') -> list:
    """Return human-readable matched bounce indicators for logging."""
    reasons = []
    normalized_subject = (subject or '').strip().lower()
    text = (body_text or '') + ' ' + (body_html or '')
    text = re.sub(r'<[^>]+>', ' ', text)
    normalized_text = (text or '').strip().lower()

    for pattern in BOUNCE_SUBJECT_PATTERNS:
        if re.search(pattern, normalized_subject, re.IGNORECASE):
            reasons.append(f"subject:{pattern}")
    for pattern in BOUNCE_BODY_PATTERNS:
        if re.search(pattern, normalized_text, re.IGNORECASE):
            reasons.append(f"body:{pattern}")

    # Keep deterministic order and de-duplicate in case of overlap.
    return sorted(set(reasons))


def extract_failed_recipients_from_bounce(body_text: str = '', body_html: str = '') -> list:
    """
    From a bounce/DSN message body, extract email addresses that the bounce
    was in reference to (failed recipients). Prefer angle-bracket form
    (e.g. <user@domain.com>), then plain addr@domain.com. Returns a list of
    unique lowercase email strings.
    """
    text = (body_text or '') + ' ' + (body_html or '')
    text = text.replace('&lt;', '<').replace('&gt;', '>')

    emails = set()
    for m in EMAIL_IN_ANGLES_RE.finditer(text):
        emails.add(m.group(1).strip().lower())
    for m in EMAIL_PLAIN_RE.finditer(text):
        addr = m.group(1).strip().lower()
        if '@' in addr and '.' in addr.split('@')[-1]:
            emails.add(addr)

    for m in DSN_FIELD_EMAIL_RE.finditer(text):
        addr = (m.group(1) or '').strip().lower()
        if addr and '@' in addr and '.' in addr.split('@')[-1]:
            emails.add(addr)

    return list(emails)


def _extract_emails_from_text(text: str) -> set:
    found = set()
    if not text:
        return found

    normalized = text.replace('&lt;', '<').replace('&gt;', '>')

    for m in EMAIL_IN_ANGLES_RE.finditer(normalized):
        found.add(m.group(1).strip().lower())
    for m in EMAIL_PLAIN_RE.finditer(normalized):
        addr = m.group(1).strip().lower()
        if '@' in addr and '.' in addr.split('@')[-1]:
            found.add(addr)
    for m in DSN_FIELD_EMAIL_RE.finditer(normalized):
        addr = (m.group(1) or '').strip().lower()
        if addr and '@' in addr and '.' in addr.split('@')[-1]:
            found.add(addr)

    return found


def _looks_like_system_mailbox(addr: str) -> bool:
    local_part = (addr or '').split('@', 1)[0].strip().lower()
    return local_part in SYSTEM_LOCAL_PARTS


def process_bounce_and_unsubscribe(email_msg, credential, logger_instance=None):
    """
    If the given EmailMessage looks like a bounce/DSN, extract failed recipient
    emails and unsubscribe them (set is_active=False) for any Subscriber
    belonging to this credential's user. Marks the message as processed.

    Returns (was_bounce: bool, unsubscribed_emails: list).
    """
    from subscribers.models import Subscriber

    log = logger_instance or logger
    subject = email_msg.subject or ''
    body_text = email_msg.body_text or ''
    body_html = email_msg.body_html or ''
    match_reasons = _get_bounce_match_reasons(subject, body_text, body_html)

    if not match_reasons:
        return False, []

    provider = getattr(email_msg, 'provider', '') or 'unknown'
    log.info(
        f"Bounce detected for message {email_msg.id} "
        f"(provider={provider}, from={email_msg.from_email}, subject={subject!r}); "
        f"matched indicators={match_reasons}"
    )

    extracted = set(extract_failed_recipients_from_bounce(body_text, body_html))
    extraction_counts = {'body': len(extracted), 'recipients': 0, 'provider_data': 0}

    # Fallback sources: recipient/header fields can include the original failed address
    # even when body parsing is sparse.
    for addr in getattr(email_msg, 'to_emails_list', []) or []:
        before = len(extracted)
        extracted.update(_extract_emails_from_text(addr))
        extraction_counts['recipients'] += max(0, len(extracted) - before)
    for addr in getattr(email_msg, 'cc_emails_list', []) or []:
        before = len(extracted)
        extracted.update(_extract_emails_from_text(addr))
        extraction_counts['recipients'] += max(0, len(extracted) - before)
    for addr in getattr(email_msg, 'bcc_emails_list', []) or []:
        before = len(extracted)
        extracted.update(_extract_emails_from_text(addr))
        extraction_counts['recipients'] += max(0, len(extracted) - before)

    provider_data = getattr(email_msg, 'provider_data', {}) or {}
    if isinstance(provider_data, dict):
        for key in ['raw_headers', 'headers', 'dsn', 'diagnostic', 'raw', 'envelope_to', 'delivered_to', 'x_failed_recipients']:
            value = provider_data.get(key)
            if isinstance(value, str):
                before = len(extracted)
                extracted.update(_extract_emails_from_text(value))
                extraction_counts['provider_data'] += max(0, len(extracted) - before)
            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, str):
                        before = len(extracted)
                        extracted.update(_extract_emails_from_text(item))
                        extraction_counts['provider_data'] += max(0, len(extracted) - before)
            elif isinstance(value, dict):
                for nested_value in value.values():
                    if isinstance(nested_value, str):
                        before = len(extracted)
                        extracted.update(_extract_emails_from_text(nested_value))
                        extraction_counts['provider_data'] += max(0, len(extracted) - before)

    pre_filter_candidates = sorted(extracted)
    log.info(
        f"Bounce extraction for message {email_msg.id}: "
        f"counts={extraction_counts}, candidates_before_filter={pre_filter_candidates}"
    )

    system_filtered = sorted([addr for addr in extracted if addr and _looks_like_system_mailbox(addr)])
    invalid_filtered = sorted([addr for addr in extracted if not addr or '@' not in addr])
    extracted = {addr for addr in extracted if addr and '@' in addr and not _looks_like_system_mailbox(addr)}

    if system_filtered or invalid_filtered:
        log.info(
            f"Bounce filtering for message {email_msg.id}: "
            f"system_filtered={system_filtered}, invalid_filtered={invalid_filtered}, "
            f"remaining={sorted(extracted)}"
        )

    if not extracted:
        log.info(f"Bounce message {email_msg.id} detected but no recipient emails extracted; marking as processed.")
        email_msg.processed = True
        email_msg.save(update_fields=['processed'])
        return True, []

    user = credential.user
    sender_email = (credential.email_address or '').strip().lower()
    if sender_email in extracted:
        log.info(f"Bounce extraction for message {email_msg.id} includes mailbox owner {sender_email}; skipping owner unsubscribe.")
    unsubscribed = set()
    unmatched_candidates = []
    for addr in extracted:
        if addr == sender_email:
            continue  # Don't unsubscribe the mailbox owner
        try:
            subs = Subscriber.objects.filter(email__iexact=addr, lists__user=user).distinct()
            matched_any = False
            for sub in subs:
                if sub.is_active:
                    sub.is_active = False
                    sub.save(update_fields=['is_active'])
                    unsubscribed.add(addr)
                    matched_any = True
                    log.info(f"Unsubscribed {addr} (subscriber id={sub.id}) due to bounce message {email_msg.id}")
            if not matched_any:
                unmatched_candidates.append(addr)
        except Exception as e:
            log.warning(f"Error unsubscribing {addr} for bounce {email_msg.id}: {e}")

    email_msg.processed = True
    email_msg.save(update_fields=['processed'])
    unsubscribed_list = sorted(unsubscribed)
    log.info(
        f"Processed bounce message {email_msg.id}: "
        f"unsubscribed_count={len(unsubscribed_list)}, unsubscribed={unsubscribed_list}, "
        f"not_found_in_user_lists={sorted(set(unmatched_candidates))}, marked_processed=True"
    )
    return True, unsubscribed_list
