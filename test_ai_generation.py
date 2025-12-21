"""
Test script for AI email generation
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(__file__))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dripemails.settings')
django.setup()

from campaigns.ai_utils import generate_email_content

# Test generation
print("Testing AI email generation...")
print("=" * 60)

result = generate_email_content(
    subject="Welcome to our new product",
    recipient="new customers",
    tone="friendly",
    length="medium",
    context="We're launching a new fitness tracker called FitBand Pro"
)

print("\n✓ Generation Result:")
print(f"Success: {result.get('success')}")
print(f"\nSubject: {result.get('subject')}")
print(f"\nBody HTML (first 500 chars):")
print(result.get('body_html', '')[:500])
print("\n" + "=" * 60)

if result.get('error'):
    print(f"\n✗ Error: {result.get('error')}")
