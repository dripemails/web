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

    return list(emails)


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

    if not is_bounce_message(subject, body_text, body_html):
        return False, []

    extracted = extract_failed_recipients_from_bounce(body_text, body_html)
    if not extracted:
        log.info(f"Bounce message {email_msg.id} detected but no recipient emails extracted; marking as processed.")
        email_msg.processed = True
        email_msg.save(update_fields=['processed'])
        return True, []

    user = credential.user
    sender_email = (credential.email_address or '').strip().lower()
    unsubscribed = []
    for addr in extracted:
        if addr == sender_email:
            continue  # Don't unsubscribe the mailbox owner
        try:
            subs = Subscriber.objects.filter(email__iexact=addr, lists__user=user).distinct()
            for sub in subs:
                if sub.is_active:
                    sub.is_active = False
                    sub.save(update_fields=['is_active'])
                    unsubscribed.append(addr)
                    log.info(f"Unsubscribed {addr} (subscriber id={sub.id}) due to bounce message {email_msg.id}")
        except Exception as e:
            log.warning(f"Error unsubscribing {addr} for bounce {email_msg.id}: {e}")

    email_msg.processed = True
    email_msg.save(update_fields=['processed'])
    log.info(f"Processed bounce message {email_msg.id}: unsubscribed {len(unsubscribed)} address(es): {unsubscribed}")
    return True, unsubscribed
