"""
AI utilities for email generation and topic analysis.
Provides functions for generating email content using Ollama with local llama3.1:8b model.
"""

import os
import re
import json
import logging
from typing import List, Dict, Tuple, Optional
from collections import defaultdict

# AI imports - Using Ollama for local LLM inference
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

# Configure logging
logger = logging.getLogger(__name__)

# Ollama configuration
OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llama3.1:8b")


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

    # ----- CALL OLLAMA API -----
    try:
        if not REQUESTS_AVAILABLE:
            raise ImportError("requests is required for email generation. Install with: pip install requests")
        
        payload = {
            "model": OLLAMA_MODEL,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.7,
                "top_p": 0.95,
                "num_predict": 1000
            }
        }
        
        response = requests.post(
            f"{OLLAMA_BASE_URL}/api/generate",
            json=payload,
            timeout=120
        )
        
        # Handle 410 Gone errors (model deprecated/removed)
        if response.status_code == 410:
            error_msg = (
                f"Model {current_model} is no longer available (410 Gone). "
                f"Please update HUGGINGFACE_MODEL in your .env file to a different model. "
                f"Try: mistralai/Mistral-7B-Instruct-v0.1, HuggingFaceH4/zephyr-7b-beta, "
                f"or check https://huggingface.co/models for available models."
            )
            raise ValueError(error_msg)
        
        response.raise_for_status()
        
        result_data = response.json()
        raw = result_data.get("response", "").strip()

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
        logger.error(f"Ollama API error: {str(e)}")
        error_msg = f"Failed to generate email. Error: {str(e)}"
        try:
            if hasattr(e, 'response') and e.response is not None:
                if e.response.status_code == 404:
                    error_msg = f"Ollama server not found. Please ensure Ollama is running at {OLLAMA_BASE_URL}"
                elif e.response.status_code == 500:
                    error_msg = "Ollama server error. The model may need to be pulled first. Run: ollama pull llama3.1:8b"
        except:
            pass
        raise ValueError(error_msg)
    except ImportError as e:
        logger.error(f"Import error: {str(e)}")
        raise ValueError(str(e))



def revise_email_content(email_text: str) -> Dict[str, str]:
    """
    Revise an email for grammar, clarity, and professionalism using Ollama.
    
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
        logger.info(f"Revising email content with Ollama model: {OLLAMA_MODEL}...")
        
        if not REQUESTS_AVAILABLE:
            raise ImportError("requests is required for email revision. Install with: pip install requests")
        
        payload = {
            "model": OLLAMA_MODEL,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.7,
                "top_p": 0.95,
                "num_predict": 1500
            }
        }
        
        resp = requests.post(f"{OLLAMA_BASE_URL}/api/generate", json=payload, timeout=120)
        resp.raise_for_status()
        data = resp.json()
        
        # Extract response text from Ollama API response
        revised = data.get('response', '')
        
        if not revised:
            raise ValueError("No response generated from model")
        
        revised = revised.strip()
        
        # Remove any accidentally added subject/metadata lines
        revised = re.sub(r'^(Subject:|From:|To:|Date:)[^\n]*\n?', '', revised, flags=re.IGNORECASE | re.MULTILINE)
        
        return {'revised_text': revised, 'success': True}
        
    except Exception as e:
        logger.error(f"Email revision error: {str(e)}")
        return {'revised_text': email_text, 'success': False, 'error': str(e)}



