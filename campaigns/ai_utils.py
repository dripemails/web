"""
AI utilities for email generation and topic analysis.
Provides functions for generating email content using Hugging Face API and analyzing email topics using LDA.
"""

import os
import re
import json
import logging
from typing import List, Dict, Tuple, Optional
from collections import defaultdict

# AI imports - Using Hugging Face Inference API
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

# Configure logging
logger = logging.getLogger(__name__)

# Load environment variables from .env file using django-environ
# This ensures the .env file is loaded even if Django isn't fully initialized
try:
    import environ
    # Get the base directory (project root)
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    env_file = os.path.join(base_dir, '.env')
    
    # Create environ.Env instance and read .env file if it exists
    env = environ.Env()
    if os.path.exists(env_file):
        env.read_env(env_file)
    
    # Get values from environ (which reads from .env file and os.environ)
    HUGGINGFACE_API_KEY = env('HUGGINGFACE_API_KEY', default='')
    # Default model: meta-llama/Llama-3.2-1B (requires approval - gated model)
    # Fallback to HuggingFaceH4/zephyr-7b-beta if Llama access is pending
    # User can override with HUGGINGFACE_MODEL in .env
    # Note: meta-llama models require approval. Use HuggingFaceH4/zephyr-7b-beta for immediate access.
    HUGGINGFACE_MODEL = env('HUGGINGFACE_MODEL', default='HuggingFaceH4/zephyr-7b-beta')
except (ImportError, Exception) as e:
    # Fallback to os.environ if django-environ is not available
    logger.warning(f"Could not load .env file using django-environ: {e}. Falling back to os.environ.")
    HUGGINGFACE_API_KEY = os.environ.get("HUGGINGFACE_API_KEY", "")
    # Default model: HuggingFaceH4/zephyr-7b-beta (no approval required)
    # Note: meta-llama models require approval. Use HuggingFaceH4/zephyr-7b-beta for immediate access.
    HUGGINGFACE_MODEL = os.environ.get("HUGGINGFACE_MODEL", "HuggingFaceH4/zephyr-7b-beta")

# Hugging Face configuration
HUGGINGFACE_API_URL = f"https://api-inference.huggingface.co/models/{HUGGINGFACE_MODEL}"


def extract_json(text: str) -> str:
    """
    Extract the first valid JSON object from the model output.
    Safely handles extra text before or after the JSON.
    """
    start = text.find("{")
    end = text.rfind("}")

    if start == -1 or end == -1 or end < start:
        raise ValueError("No JSON object found in model output.")

    return text[start:end+1]

def extract_product_name(subject: str, context: str) -> str:
    """
    Attempts to detect a product name inside subject/context.
    Finds the first CapitalizedWord or CapitalizedWordSequence and returns it.
    Example: "Introducing the AidanPad Pro Max" → "AidanPad Pro Max"
    """
    text = subject + " " + context

    # Common patterns like "the AidanPad", "our AidanPad Ultra"
    patterns = [
        r"\bthe ([A-Z][A-Za-z0-9]*(?: [A-Z][A-Za-z0-9]*)*)",
        r"\bour ([A-Z][A-Za-z0-9]*(?: [A-Z][A-Za-z0-9]*)*)",
        r"\bIntroducing\s+the\s+([A-Z][A-Za-z0-9]*(?: [A-Z][A-Za-z0-9]*)*)",
        r"\bIntroducing\s+([A-Z][A-Za-z0-9]*(?: [A-Z][A-Za-z0-9]*)*)",
        r"\bMeet the ([A-Z][A-Za-z0-9]*(?: [A-Z][A-Za-z0-9]*)*)",
        r"\bTry the ([A-Z][A-Za-z0-9]*(?: [A-Z][A-Za-z0-9]*)*)"
    ]

    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(1).strip()

    # FINAL fallback: first capitalized word sequence
    generic = re.search(r"\b([A-Z][A-Za-z0-9]*(?: [A-Z][A-Za-z0-9]*)*)\b", text)
    if generic:
        return generic.group(1).strip()

    return ""


def generate_email_content(
    subject: str,
    recipient: str = "subscriber",
    tone: str = "professional",
    length: str = "medium",
    context: str = "",
    first_name: str = "",
    product_name: str = "",
    account_email: str = ""
) -> Dict[str, str]:

    # Apply fallback placeholders
    first_name = first_name or "{{first_name}}"
    # Auto-detect product if missing
    if not product_name.strip():
        detected = extract_product_name(subject, context)
        product_name = detected if detected else "{{product_name}}"

    account_email = account_email or "{{sender_email}}"

    # ----- HEADER & FOOTER -----
    email_header = (
        f"Hi {first_name},<br><br>"
        f"Did you have any questions about the {product_name}?<br><br>"
    )

    email_footer = f"<br>Signed,<br>{account_email}"

    length_desc = {
        "short": "very brief, 2 short paragraphs",
        "medium": "3–4 paragraphs, balanced detail",
        "long": "5+ paragraphs, detailed"
    }.get(length, "3–4 paragraphs, balanced detail")

    # ----- PROMPT -----
    prompt = f"""
    You are an AI that must output ONLY valid JSON. No commentary. No explanations.

Return EXACTLY this format and nothing else:

{{
  "subject": "Short subject line",
  "body_text": "Email body in plain text only."
}}

Rules you MUST follow:
- Output ONLY valid JSON.
- No backticks.
- No text before or after the JSON.
- No markdown.
- No explanation.
- No extra fields.
- No trailing commas.
- Do NOT escape newlines with \\n — just include raw text.
You are an expert marketing email writer.

Write ONLY the main body content of an email.
Do NOT include:
- greetings
- signatures
- salutations
- names
- sign-offs

Write clean paragraphs in plain text only.
NO HTML.

Topic: {subject}
Tone: {tone}
Audience: {recipient}
Length: {length_desc}
Context: {context}

Respond ONLY in valid JSON:

{{
  "subject": "Short subject line",
  "body_text": "Email body in plain text only."
}}
"""

    # ----- CALL HUGGING FACE API -----
    try:
        if not REQUESTS_AVAILABLE:
            raise ImportError("requests is required for email generation. Install with: pip install requests")
        
        if not HUGGINGFACE_API_KEY:
            raise ValueError("HUGGINGFACE_API_KEY environment variable is required. Get your API key from https://huggingface.co/settings/tokens")
        
        headers = {"Authorization": f"Bearer {HUGGINGFACE_API_KEY}"}
        payload = {
            "inputs": prompt,
            "parameters": {
                "max_new_tokens": 1000,
                "temperature": 0.7,
                "top_p": 0.95,
                "return_full_text": False
            }
        }
        
        response = requests.post(
            HUGGINGFACE_API_URL,
            headers=headers,
            json=payload,
            timeout=120
        )
        
        # Handle 410 Gone errors (model deprecated/removed)
        if response.status_code == 410:
            error_msg = (
                f"Model {HUGGINGFACE_MODEL} is no longer available (410 Gone). "
                f"Please update HUGGINGFACE_MODEL in your .env file to a different model. "
                f"Try: mistralai/Mistral-7B-Instruct-v0.1, HuggingFaceH4/zephyr-7b-beta, "
                f"or check https://huggingface.co/models for available models."
            )
            raise ValueError(error_msg)
        
        response.raise_for_status()
        
        result_data = response.json()
        if isinstance(result_data, list) and len(result_data) > 0:
            raw = result_data[0].get("generated_text", "").strip()
        else:
            raw = result_data.get("generated_text", "").strip()

        # Extract & parse JSON safely
        try:
            clean_json = extract_json(raw)
            result = json.loads(clean_json)

            body_text = result.get("body_text", "").strip()

            # Convert plain text → HTML
            paragraphs = [p.strip() for p in body_text.split("\n") if p.strip()]
            html_body = "".join(f"<p>{p}</p>" for p in paragraphs)

            final_html = email_header + html_body + email_footer

            return {
                "subject": result.get("subject", subject),
                "body_html": final_html,
                "success": True
            }

        except Exception as e:
            return {
                "subject": subject,
                "body_html": email_header + "<p>Error: invalid JSON from model.</p>" + email_footer,
                "success": False,
                "error": str(e)
            }

    except requests.exceptions.RequestException as e:
        logger.error(f"Hugging Face API error: {str(e)}")
        error_msg = f"Failed to generate email. Error: {str(e)}"
        try:
            if hasattr(e, 'response') and e.response is not None:
                if e.response.status_code == 401:
                    error_msg = "Invalid Hugging Face API key. Please check your HUGGINGFACE_API_KEY environment variable."
                elif e.response.status_code == 503:
                    error_msg = "Model is loading. Please try again in a few moments."
        except:
            pass
        raise ValueError(error_msg)
    except ImportError as e:
        logger.error(f"Import error: {str(e)}")
        raise ValueError(str(e))



def revise_email_content(email_text: str) -> Dict[str, str]:
    """
    Revise an email for grammar, clarity, and professionalism using Hugging Face API.
    
    Args:
        email_text: The original email content (HTML or plain text)
    
    Returns:
        Dictionary with 'revised_text' and 'success' keys
    """
    
    # Strip HTML tags for analysis if present
    clean_text = re.sub(r'<[^>]+>', ' ', email_text)
    clean_text = re.sub(r'\s+', ' ', clean_text).strip()
    
    if not clean_text:
        return {'revised_text': email_text, 'success': False, 'error': 'Empty email content'}
    
    # Build revision prompt
    prompt = (
        "You are an expert email editor. Review the following email and revise it to:\n"
        "1. Fix any grammar, spelling, or punctuation errors\n"
        "2. Improve clarity and readability\n"
        "3. Maintain a professional tone\n"
        "4. Keep the same general structure and meaning\n"
        "5. Preserve any HTML formatting if present\n\n"
        "Do NOT add subject lines, signatures, or metadata. Only output the revised email body.\n\n"
        f"Original email:\n{email_text}\n\n"
        "Revised email:"
    )
    
    try:
        logger.info(f"Revising email content with Hugging Face model: {HUGGINGFACE_MODEL}...")
        
        if not REQUESTS_AVAILABLE:
            raise ImportError("requests is required for email revision. Install with: pip install requests")
        
        if not HUGGINGFACE_API_KEY:
            raise ValueError("HUGGINGFACE_API_KEY environment variable is required. Get your API key from https://huggingface.co/settings/tokens")
        
        headers = {"Authorization": f"Bearer {HUGGINGFACE_API_KEY}"}
        payload = {
            "inputs": prompt,
            "parameters": {
                "max_new_tokens": 1500,
                "temperature": 0.7,
                "top_p": 0.95,
                "return_full_text": False
            }
        }
        
        resp = requests.post(HUGGINGFACE_API_URL, headers=headers, json=payload, timeout=120)
        resp.raise_for_status()
        data = resp.json()
        
        # Extract response text from Hugging Face API response
        revised = None
        if isinstance(data, list) and len(data) > 0:
            revised = data[0].get('generated_text', '')
        elif isinstance(data, dict):
            revised = data.get('generated_text', '')
        
        if not revised:
            raise ValueError("No response generated from model")
        
        revised = revised.strip()
        
        # Remove any accidentally added subject/metadata lines
        revised = re.sub(r'^(Subject:|From:|To:|Date:)[^\n]*\n?', '', revised, flags=re.IGNORECASE | re.MULTILINE)
        
        return {'revised_text': revised, 'success': True}
        
    except Exception as e:
        logger.error(f"Email revision error: {str(e)}")
        return {'revised_text': email_text, 'success': False, 'error': str(e)}



