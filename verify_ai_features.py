#!/usr/bin/env python
"""
Verification script for AI Email Features
Run this to verify all systems are operational
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dripemails.settings')
django.setup()

print('=' * 70)
print(' AI EMAIL FEATURES - SYSTEM VERIFICATION')
print('=' * 70)
print()

all_good = True

# 1. Check imports
print('1. Checking Imports...')
try:
    from campaigns.ai_utils import (
        generate_email_content,
        analyze_email_topics,
        summarize_topics,
        preprocess_text
    )
    print('   ✓ AI utilities module imports successfully')
except Exception as e:
    print(f'   ✗ AI utilities import failed: {e}')
    all_good = False

try:
    from campaigns.models import Campaign, Email, EmailAIAnalysis
    print('   ✓ Models import successfully (EmailAIAnalysis included)')
except Exception as e:
    print(f'   ✗ Models import failed: {e}')
    all_good = False

try:
    from campaigns.views import (
        generate_email_with_ai,
        analyze_campaign_topics,
        email_analysis_view,
        campaign_analysis_view
    )
    print('   ✓ View functions import successfully')
except Exception as e:
    print(f'   ✗ Views import failed: {e}')
    all_good = False

# 2. Check database model
print()
print('2. Checking Database...')
try:
    from django.db import connection
    from django.db.utils import OperationalError
    
    cursor = connection.cursor()
    try:
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='campaigns_emailaianalysis'"
        )
        result = cursor.fetchone()
        if result:
            print('   ✓ EmailAIAnalysis table exists in database')
        else:
            print('   ✗ EmailAIAnalysis table NOT found')
            all_good = False
    except Exception as e:
        print(f'   ✗ Database query failed: {e}')
        all_good = False
except Exception as e:
    print(f'   ✗ Database connection failed: {e}')
    all_good = False

# 3. Check dependencies
print()
print('3. Checking Dependencies...')
dependencies = {
    'nltk': 'Natural Language Toolkit',
    'gensim': 'Topic Modeling',
    'openai': 'OpenAI API Client',
    'pandas': 'Data Analysis'
}

for module_name, description in dependencies.items():
    try:
        __import__(module_name)
        print(f'   ✓ {module_name:15} ({description})')
    except ImportError:
        print(f'   ✗ {module_name:15} NOT INSTALLED')
        all_good = False

# 4. Check Django URLs
print()
print('4. Checking URL Routing...')
try:
    from django.urls import reverse
    
    # Check if routes exist (will raise NoReverseMatch if not found)
    email_analysis_url = reverse('campaigns:email-analysis')
    print('   ✓ Email analysis route registered')
    
except Exception as e:
    print(f'   ✗ URL routing issue: {e}')
    all_good = False

# 5. Check API endpoints
print()
print('5. Checking API Endpoints...')
api_endpoints = [
    ('generate_email_with_ai', 'Email Generation'),
    ('analyze_campaign_topics', 'Topic Analysis'),
]

for func_name, description in api_endpoints:
    try:
        from campaigns import views
        if hasattr(views, func_name):
            print(f'   ✓ {description:20} endpoint registered')
        else:
            print(f'   ✗ {description:20} endpoint NOT found')
            all_good = False
    except Exception as e:
        print(f'   ✗ Error checking {description}: {e}')
        all_good = False

# 6. Check file structure
print()
print('6. Checking File Structure...')
import os

files_to_check = [
    ('campaigns/ai_utils.py', 'AI Utilities Module'),
    ('templates/campaigns/email_analysis.html', 'Email Analysis Template'),
    ('campaigns/migrations/0006_emailaianalysis.py', 'Database Migration'),
]

for file_path, description in files_to_check:
    full_path = os.path.join(os.path.dirname(__file__), file_path)
    if os.path.exists(full_path):
        print(f'   ✓ {description:30} exists')
    else:
        print(f'   ✗ {description:30} NOT found at {file_path}')
        all_good = False

# 7. Summary
print()
print('=' * 70)
if all_good:
    print(' ✅ ALL SYSTEMS OPERATIONAL')
    print()
    print('Your application is ready for:')
    print('  • Email generation with AI (OpenAI)')
    print('  • Topic analysis on campaigns (LDA)')
    print()
    print('Next Steps:')
    print('  1. Set OpenAI API key: set OPENAI_API_KEY=sk-...')
    print('  2. Navigate to /campaigns/email-analysis/')
    print('  3. Try AI features in email template editor')
else:
    print(' ❌ SOME SYSTEMS NOT OPERATIONAL')
    print()
    print('Please review the errors above and:')
    print('  1. Reinstall dependencies: pip install -r requirements.txt')
    print('  2. Run migrations: python manage.py migrate')
    print('  3. Check Django setup: python manage.py check')

print('=' * 70)
