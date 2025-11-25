"""
AI utilities for email generation and topic analysis.
Provides functions for generating email content using OpenAI and analyzing email topics using LDA.
"""

import os
import re
import json
from typing import List, Dict, Tuple, Optional
from collections import defaultdict

# NLP imports
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import PorterStemmer
import gensim.models
import gensim.corpora as corpora

# AI imports - Using local LLM via Ollama (llama3.1:8b)
import requests
import json

# Download required NLTK data (run once)
try:
    stopwords.words('english')
except LookupError:
    nltk.download('stopwords')
    nltk.download('punkt')

# Ollama configuration
OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "llama3.1:8b"


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

    # ----- CALL OLLAMA -----
    try:
        response = requests.post(
            OLLAMA_URL,
            json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False},
            timeout=120
        )
        response.raise_for_status()
        raw = response.json().get("response", "").strip()

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
        raise Exception(f"Ollama API error: {str(e)}")



def preprocess_text(text: str) -> List[str]:
    """
    Preprocess email text for topic modeling.
    
    Args:
        text: Raw email text
    
    Returns:
        List of preprocessed tokens
    """
    stop_words = set(stopwords.words('english'))
    ps = PorterStemmer()
    
    # Lowercase and remove special characters
    text = text.lower()
    text = re.sub(r'\W', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    
    # Tokenize
    tokens = word_tokenize(text)
    
    # Remove stopwords and stem
    tokens = [ps.stem(word) for word in tokens if word not in stop_words and len(word) > 2]
    
    return tokens


def analyze_email_topics(
    email_texts: List[str],
    num_topics: int = 5,
    num_words: int = 5
) -> Dict:
    """
    Perform topic modeling on a list of email texts using LDA.
    
    Args:
        email_texts: List of email body texts to analyze
        num_topics: Number of topics to extract (default: 5)
        num_words: Number of words per topic to display (default: 5)
    
    Returns:
        Dictionary containing:
            - 'topics': List of topic tuples with word weights
            - 'dominant_topic_per_email': List of dominant topic for each email
            - 'doc_topics': Document-topic distribution
            - 'success': Boolean indicating success
    """
    if not email_texts or len(email_texts) == 0:
        return {
            'topics': [],
            'dominant_topic_per_email': [],
            'doc_topics': [],
            'success': False,
            'error': 'No email texts provided'
        }
    
    try:
        # Preprocess texts
        processed_texts = [preprocess_text(text) for text in email_texts]
        
        # Filter out texts with no tokens
        processed_texts = [text for text in processed_texts if len(text) > 0]
        
        if not processed_texts:
            return {
                'topics': [],
                'dominant_topic_per_email': [],
                'doc_topics': [],
                'success': False,
                'error': 'No valid tokens after preprocessing'
            }
        
        # Create dictionary and corpus
        id2word = corpora.Dictionary(processed_texts)
        corpus = [id2word.doc2bow(text) for text in processed_texts]
        
        # Adjust num_topics to avoid exceeding number of documents
        effective_num_topics = min(num_topics, len(email_texts))
        
        # Build LDA model
        lda_model = gensim.models.LdaModel(
            corpus=corpus,
            id2word=id2word,
            num_topics=effective_num_topics,
            random_state=100,
            update_every=1,
            chunksize=10,
            passes=10,
            alpha='auto',
            per_word_topics=True
        )
        
        # Extract topics
        topics = lda_model.print_topics(num_words=num_words)
        
        # Get dominant topic for each email
        dominant_topic_per_email = []
        for doc_bow in corpus:
            topic_dist = lda_model.get_document_topics(doc_bow)
            if topic_dist:
                dominant_topic = max(topic_dist, key=lambda x: x[1])
                dominant_topic_per_email.append({
                    'topic_id': dominant_topic[0],
                    'confidence': round(dominant_topic[1], 4)
                })
            else:
                dominant_topic_per_email.append({
                    'topic_id': 0,
                    'confidence': 0
                })
        
        # Get document-topic distribution
        doc_topics = []
        for i, doc_bow in enumerate(corpus):
            topic_dist = dict(lda_model.get_document_topics(doc_bow))
            doc_topics.append(topic_dist)
        
        return {
            'topics': topics,
            'dominant_topic_per_email': dominant_topic_per_email,
            'doc_topics': doc_topics,
            'coherence': 'Not computed',  # Could add coherence score if needed
            'success': True
        }
    
    except Exception as e:
        return {
            'topics': [],
            'dominant_topic_per_email': [],
            'doc_topics': [],
            'success': False,
            'error': f'Topic modeling error: {str(e)}'
        }


def summarize_topics(topics: List[Tuple]) -> List[Dict]:
    """
    Convert raw LDA topics into a more readable format.
    
    Args:
        topics: List of topic tuples from LDA model
    
    Returns:
        List of dictionaries with topic_id and keywords
    """
    result = []
    for topic_id, topic_words in topics:
        # Parse the topic string: "0.0234*\"word1\" + 0.0156*\"word2\" + ..."
        words = []
        weights = []
        
        parts = topic_words.split('+')
        for part in parts:
            match = re.search(r'([\d.]+)\*"([^"]+)"', part.strip())
            if match:
                weight = float(match.group(1))
                word = match.group(2)
                words.append(word)
                weights.append(round(weight, 4))
        
        result.append({
            'topic_id': topic_id,
            'keywords': words,
            'weights': weights,
            'top_word': words[0] if words else 'unknown'
        })
    
    return result
