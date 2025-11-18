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


def generate_email_content(
    subject: str,
    recipient: str = "subscriber",
    tone: str = "professional",
    length: str = "medium",
    context: str = ""
) -> Dict[str, str]:
    """
    Generate email content using local Ollama LLM (llama3.1:8b).
    
    Args:
        subject: The subject or topic of the email
        recipient: Who the email is intended for (default: "subscriber")
        tone: Tone of the email (professional, friendly, persuasive, etc.)
        length: Length of email (short, medium, long)
        context: Additional context/details for email generation
    
    Returns:
        Dictionary with 'subject' and 'body_html' keys
        
    Raises:
        ValueError: If Ollama server is not accessible
        Exception: If API call fails
    """
    
    # Determine length guidance
    length_guidance = {
        'short': '2-3 paragraphs, concise and direct',
        'medium': '4-5 paragraphs, balanced content',
        'long': '6+ paragraphs, detailed and comprehensive'
    }
    
    length_desc = length_guidance.get(length, length_guidance['medium'])
    
    # Build the comprehensive prompt
    prompt_parts = [
        "You are an expert email marketing copywriter. Create a professional and engaging email.",
        "",
        f"Email Purpose/Topic: {subject}",
        f"Target Audience: {recipient}",
        f"Tone: {tone}",
        f"Length: {length_desc}",
    ]
    
    if context and context.strip():
        prompt_parts.extend([
            "",
            "Additional Details:",
            context
        ])
    
    prompt_parts.extend([
        "",
        "Instructions:",
        "1. Create a compelling email subject line that captures attention",
        "2. Write engaging email body content with proper HTML formatting",
        "3. Use the specified tone and include all relevant details from the user input",
        "4. Use basic HTML tags: <p>, <strong>, <em>, <br>, <h3>, <ul>, <li>, <a>",
        "5. Keep the email professional and suitable for marketing/business communication",
        "6. Include a clear call-to-action if appropriate",
        "7. Make the content match the specified tone and length",
        "",
        "IMPORTANT: Respond with ONLY a valid JSON object in this exact format (no other text before or after):",
        "{",
        '    "subject": "The email subject line here",',
        '    "body_html": "The complete email body in HTML format here"',
        "}"
    ])
    
    full_prompt = "\n".join(prompt_parts)
    
    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": OLLAMA_MODEL,
                "prompt": full_prompt,
                "stream": False
            },
            timeout=120
        )
        response.raise_for_status()
        
        # Extract the response text from JSON response
        response_data = response.json()
        response_text = response_data.get("response", "").strip()
        
        # Try to parse as JSON
        try:
            result = json.loads(response_text)
            return {
                'subject': result.get('subject', subject),
                'body_html': result.get('body_html', ''),
                'success': True
            }
        except json.JSONDecodeError:
            # If not JSON, try to extract subject and body
            lines = response_text.split('\n')
            subject_line = next((l for l in lines if l.strip()), subject)
            body = '\n'.join(lines[1:]) if len(lines) > 1 else response_text
            
            return {
                'subject': subject_line,
                'body_html': f"<p>{body}</p>",
                'success': True
            }
    
    except requests.exceptions.RequestException as e:
        raise Exception(f"Ollama API error: {str(e)}. Make sure Ollama is running on localhost:11434")


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
