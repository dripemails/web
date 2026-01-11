# ai_email.py

import json
import logging
import re
from typing import Dict
from campaigns.ai_utils import generate_email_content as ollama_generate

logger = logging.getLogger(__name__)


def call_hf_model(prompt, user_info=None):
    """
    Backwards-compatible function used for quick HF-style emails.
    """
    try:
        result = generate_email_content(
            subject=prompt[:50],
            recipient="subscriber",
            tone="professional",
            length="medium",
            context=prompt,
            user_info=user_info,
        )

        return result.get('body_html', '').replace('<p>', '').replace('</p>', '\n')

    except Exception as e:
        logger.error(f"Error calling HF model: {e}")
        return ""


def generate_email_content(
    subject: str,
    recipient: str = "subscriber",
    tone: str = "professional",
    length: str = "medium",
    context: str = "",
    user_info: dict = None
) -> Dict[str, str]:
    """
    Main email generation logic.
    """

    topic = subject
    details = context

    instruction = (
        "Do NOT repeat the template sentences in your response. "
        "Only output the email subject on the first line, followed by the email body."
    )

    prompt = (
        f"{instruction}\n\n"
        f"Write an email about {topic}. "
        f"Details: {details}. "
        f"Recipient type: {recipient}. "
        f"Length: {length}. "
        f"Tone: {tone}."
    )

    try:
        generated = ollama_generate(
            prompt=prompt,
            max_tokens=768,
            temperature=0.7
        )

        raw_text = generated.get("body", "") if isinstance(generated, dict) else generated
        raw_text = raw_text.strip()

        # Split subject and body
        lines = [l.strip() for l in raw_text.splitlines() if l.strip()]
        subject_line = lines[0] if lines else subject
        body_text = "\n".join(lines[1:]) if len(lines) > 1 else ""

        # ----------------------------------------
        # Add signature using template values
        # ----------------------------------------
        if user_info:
            name = (
                user_info.get("full_name")
                or f"{user_info.get('first_name', '')} {user_info.get('last_name', '')}".strip()
            )
            email_addr = user_info.get("email", "")

            signature = "\n\nRegards,\n" + name
            if email_addr:
                signature += f"\n{email_addr}"

            body_text += signature

        # HTML paragraph output
        paragraphs = [f"<p>{p}</p>" for p in body_text.split("\n") if p.strip()]
        body_html = "".join(paragraphs)

        return {
            "subject": subject_line,
            "body_html": body_html,
            "success": True,
        }

    except Exception as e:
        logger.error(f"Email generation failed: {e}")
        return {
            "subject": "",
            "body_html": "",
            "success": False,
            "error": str(e),
        }
