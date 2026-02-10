import logging

import requests
from allauth.account.signals import user_signed_up
from django.dispatch import receiver


logger = logging.getLogger(__name__)


@receiver(user_signed_up)
def send_followup_after_signup(request, user, **kwargs):
    """
    After a user signs up (via sign up page or home), send a follow-up email
    using the provided campaign/email and bearer token.
    """
    # If the user has no email, there's nothing to send to
    if not user.email:
        return

    # Use the same structure as the provided Python snippet, but
    # with the real user email and their first/last name.
    url = (
        "https://dripemails.org/api/campaigns/"
        "bab64fff-49bb-457e-bf7f-f014095c6ef0/"
        "emails/282242b1-c3cd-4c0c-9fd6-1618e50c4313/send/"
    )
    headers = {
        # NOTE: This is a sensitive token. Consider moving it to an environment
        # variable if you later decide to rotate/secure it.
        "Authorization": "Bearer 6645063056c3494427ed69d1946fd7f3e4cea53c",
        "Content-Type": "application/json",
    }

    first_name = (user.first_name or "").strip()
    last_name = (user.last_name or "").strip()

    data = {
        "email": user.email,
        "variables": {
            "first_name": first_name,
            "last_name": last_name,
        },
        # Send immediately, bypassing wait_time
        "send_immediately": True,
    }

    try:
        # Fire-and-forget style; we don't want signup to fail if this fails.
        resp = requests.post(url, json=data, headers=headers, timeout=5)
        if resp.status_code >= 400:
            logger.warning(
                "Follow-up signup email request failed: status=%s body=%s",
                resp.status_code,
                resp.text[:500],
            )
    except Exception as exc:
        logger.warning("Error sending follow-up signup email: %s", exc)

