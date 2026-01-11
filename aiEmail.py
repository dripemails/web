# Using local LLM via Ollama (llama3.2:1b)
import requests
import json

OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "llama3.2:1b"

def call_ollama(prompt):
    """
    Send a prompt to the local Ollama server and collect the response.
    Handles streaming and multiline output gracefully.
    """
    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False
            },
            timeout=120
        )
        response.raise_for_status()
        
        # Extract the response text from the JSON response
        response_data = response.json()
        return response_data.get("response", "").strip()
    except requests.exceptions.RequestException as e:
        print(f"Error calling Ollama: {e}")
        return ""

def generate_email(subject, recipient, tone="professional", length="medium"):
    prompt = f"Write a {tone} email to {recipient} about '{subject}'. The email should be {length} in length."
    
    email_content = call_ollama(prompt)
    return email_content