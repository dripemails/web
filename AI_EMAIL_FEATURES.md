# AI Email Features Documentation

This document provides a complete guide to the AI-powered email features now integrated into your application.

## Table of Contents

1. [Overview](#overview)
2. [Features](#features)
3. [Setup & Configuration](#setup--configuration)
4. [Usage Guide](#usage-guide)
5. [API Reference](#api-reference)
6. [Architecture](#architecture)
7. [Troubleshooting](#troubleshooting)

---

## Overview

The application now includes two powerful AI-driven features for email marketing:

1. **AI Email Generation** - Automatically generate professional email content using OpenAI's GPT
2. **Topic Analysis** - Discover hidden topics and themes in your campaign emails using machine learning (LDA)

These features are seamlessly integrated into the email creation and analysis workflows.

---

## Features

### 1. AI Email Generation

**Purpose:** Generate professional, engaging email content with customizable tone and style.

**Key Features:**

- 🎯 **Smart Subject Lines**: Auto-generate compelling subject lines
- 📝 **Professional Body Content**: HTML-formatted email body with proper structure
- 🎨 **Customizable Tone**: Professional, Friendly, Persuasive, Casual, or Formal
- 📏 **Adjustable Length**: Short, Medium, or Long email formats
- 💾 **Direct Save**: Generated content can be saved directly to email templates
- 🔄 **Iterative Refinement**: Generate multiple times with different parameters

**Required:** OpenAI API Key (GPT-3.5-turbo or later)

### 2. Topic Analysis / Topic Modeling

**Purpose:** Automatically discover the main themes and topics discussed across your campaign emails.

**Key Features:**

- 🔍 **Automatic Discovery**: Identifies 2-10 distinct topics using Latent Dirichlet Allocation (LDA)
- 📊 **Visual Results**: Charts and tables showing topic distribution
- 🎯 **Email Mapping**: Shows which topic dominates each email
- 📈 **Keyword Extraction**: Lists top keywords for each discovered topic
- 💡 **No Training Needed**: Works with raw email content, no manual labeling required

**No API Required**: Works offline using machine learning algorithms

---

## Setup & Configuration

### Prerequisites

#### For AI Email Generation:

1. **OpenAI API Key** - Get one at https://platform.openai.com/api-keys
   - Required models: `gpt-3.5-turbo` or newer
   - Estimated cost: ~$0.002 per email generated (highly variable)

#### For Topic Analysis:

1. **Python Libraries** (already installed in requirements.txt):
   - `nltk` - Natural Language Toolkit
   - `gensim` - Topic modeling library
   - `pandas` - Data manipulation

### Configuration

#### 1. Set OpenAI API Key

**Option A: Environment Variable (Recommended for production)**

```bash
# On Windows
set OPENAI_API_KEY=your-api-key-here

# On macOS/Linux
export OPENAI_API_KEY=your-api-key-here

# In Docker or production environments
# Set via environment variable management
```

**Option B: Environment File (.env)**

```bash
# In your project root .env file
OPENAI_API_KEY=sk-...your-key-here...
```

#### 2. Install Dependencies

All required packages are already listed in `requirements.txt`:

```bash
pip install -r requirements.txt
```

Specific AI packages installed:

- `openai==1.3.9` - OpenAI API client
- `nltk==3.8.1` - Natural Language Processing
- `gensim==4.3.2` - Topic Modeling
- `pandas==2.1.4` - Data Analysis

#### 3. Database Migration

The `EmailAIAnalysis` model stores AI results. Migration already applied:

```bash
python manage.py migrate campaigns
```

---

## Usage Guide

### AI Email Generation Workflow

#### Step 1: Navigate to Email Creation

1. Go to **Campaigns → Create Campaign** (or edit existing)
2. In the email template editor, click **✨ AI Generate** button

#### Step 2: Configure Generation Parameters

- **Email Topic/Subject**: What the email is about (e.g., "New product launch", "Summer sale")
- **Recipient**: Who the email is for (e.g., "customer", "developer", "subscriber")
- **Tone**: How the email should sound
  - Professional: Formal, business-like
  - Friendly: Warm, conversational
  - Persuasive: Compelling, call-to-action focused
  - Casual: Relaxed, informal
  - Formal: Official, institutional
- **Length**: Email length
  - Short: 50-100 words
  - Medium: 150-250 words
  - Long: 300+ words
- **Additional Context** (Optional): Any specific details or requirements

#### Step 3: Generate

1. Click **✨ Generate**
2. Wait for AI to process (usually 5-15 seconds)
3. Review the generated subject and body
4. Make edits as needed
5. Click **Save Template** to save

### Topic Analysis Workflow

#### Step 1: Navigate to Email Analysis

1. Go to **Campaigns → Email Analysis** (new page)
2. Or visit `/campaigns/email-analysis/`

#### Step 2: Select Campaign

1. Choose the campaign to analyze from the dropdown
2. Adjust **Number of Topics** slider (2-10 topics)

#### Step 3: Run Analysis

1. Click **📊 Analyze Topics**
2. Wait for analysis (30-60 seconds depending on email count)
3. Results will show:
   - **Topic Cards**: Each topic with top keywords and weights
   - **Email-Topic Table**: Which topic dominates each email
   - **Distribution Chart**: Visual breakdown of topics

#### Step 4: Interpret Results

- **High confidence value** (>0.7): Email clearly matches the topic
- **Lower confidence value** (<0.3): Email touches multiple topics
- **Keywords**: Most representative words for each topic

---

## API Reference

### Email Generation Endpoint

```
POST /api/campaigns/{campaign_id}/generate-email/
```

**Request Body:**

```json
{
  "subject_topic": "New product launch",
  "recipient": "customer",
  "tone": "professional",
  "length": "medium",
  "context": "We have a new AI-powered feature",
  "email_id": null
}
```

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| subject_topic | string | Yes | Topic or subject of the email |
| recipient | string | No | Target recipient type (default: "subscriber") |
| tone | string | No | Email tone (default: "professional") |
| length | string | No | Email length (default: "medium") |
| context | string | No | Additional context for generation |
| email_id | uuid | No | If provided, generated content is saved to this email |

**Response (Success):**

```json
{
  "message": "Email generated successfully",
  "subject": "Introducing Our Latest Innovation",
  "body_html": "<p>Dear Valued Customer,</p>...",
  "saved": false
}
```

**Response (Error):**

```json
{
  "error": "OPENAI_API_KEY environment variable not set",
  "hint": "Please set OPENAI_API_KEY environment variable"
}
```

### Topic Analysis Endpoint

```
POST /api/campaigns/{campaign_id}/analyze-topics/
```

**Request Body:**

```json
{
  "num_topics": 5,
  "num_words": 5
}
```

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| num_topics | integer | No | Number of topics to extract (2-10, default: 5) |
| num_words | integer | No | Words per topic to display (default: 5) |

**Response (Success):**

```json
{
  "message": "Topic analysis completed successfully",
  "success": true,
  "email_count": 12,
  "topics": [
    {
      "topic_id": 0,
      "top_word": "product",
      "keywords": ["product", "feature", "launch", "new", "available"],
      "weights": [0.0456, 0.0312, 0.0289, 0.0267, 0.0245]
    }
  ],
  "dominant_topics": [
    {
      "topic_id": 0,
      "confidence": 0.7823
    }
  ]
}
```

**Response (Error):**

```json
{
  "error": "No emails in campaign to analyze",
  "topics": [],
  "email_count": 0
}
```

---

## Architecture

### File Structure

```
campaigns/
├── ai_utils.py                 # Core AI utility functions
├── models.py                   # Database models (added EmailAIAnalysis)
├── views.py                    # API endpoints and view functions
├── urls.py                     # URL routing
└── migrations/
    └── 0006_emailaianalysis.py # Database migration
templates/campaigns/
├── template.html               # Email editor (updated with AI button)
└── email_analysis.html         # Topic analysis interface
```

### Core Components

#### 1. `ai_utils.py`

**`generate_email_content()`**

- Uses OpenAI API to generate email content
- Input: topic, recipient, tone, length, context
- Output: Dict with 'subject' and 'body_html'
- Handles JSON parsing and error handling

**`analyze_email_topics()`**

- Performs LDA topic modeling on email texts
- Input: List of email texts, number of topics
- Output: Dict with topics, dominant topics, document-topic distribution
- Includes preprocessing: tokenization, stemming, stopword removal

**`preprocess_text()`**

- Text cleaning and normalization
- Removes stopwords, stems words
- Filters tokens by length

**`summarize_topics()`**

- Formats raw LDA output into readable format
- Extracts keywords and weights per topic

#### 2. `models.py` - EmailAIAnalysis

```python
class EmailAIAnalysis(models.Model):
    # Relations
    email = OneToOneField(Email)

    # AI Generation Fields
    generated_subject = CharField(max_length=200)
    generated_body_html = TextField()
    generation_prompt = TextField()
    generation_model = CharField(default='gpt-3.5-turbo')

    # Topic Analysis Fields
    topics_json = JSONField()
    dominant_topics = JSONField()
    topic_analysis_count = IntegerField()

    # Metadata
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)
```

#### 3. API Endpoints (views.py)

**`generate_email_with_ai(request, campaign_id)`**

- POST endpoint: `/api/campaigns/{campaign_id}/generate-email/`
- Validates campaign ownership
- Calls `generate_email_content()`
- Optionally saves to EmailAIAnalysis record

**`analyze_campaign_topics(request, campaign_id)`**

- POST endpoint: `/api/campaigns/{campaign_id}/analyze-topics/`
- Collects all email bodies from campaign
- Calls `analyze_email_topics()`
- Stores results in EmailAIAnalysis record

#### 4. Frontend Integration

**template.html**

- Added "✨ AI Generate" button in email editor
- Modal dialog for generation parameters
- JavaScript handler to call API and update Quill editor

**email_analysis.html**

- New dedicated page for topic analysis
- Campaign selector dropdown
- Interactive slider for number of topics
- Real-time chart rendering with Chart.js
- Results display: topic cards, email-topic table, distribution chart

---

## Troubleshooting

### Issue: "OPENAI_API_KEY environment variable not set"

**Solution:**

```bash
# Test if key is set
python -c "import os; print(os.getenv('OPENAI_API_KEY'))"

# Set the key
# Windows:
set OPENAI_API_KEY=sk-your-key-here

# macOS/Linux:
export OPENAI_API_KEY=sk-your-key-here

# Restart your development server or Django app
```

### Issue: OpenAI API Rate Limit

**Symptoms:** "rate_limit_exceeded" error after multiple generations

**Solutions:**

1. Wait 60 seconds before generating again
2. Upgrade your OpenAI plan: https://platform.openai.com/account/billing/overview
3. Use a lower temperature value (reduces creativity, uses fewer tokens)

### Issue: Topic Analysis Takes Too Long

**Causes:**

- Large number of emails (20+)
- Long email content
- High number of topics (10)

**Solutions:**

1. Reduce number of topics (try 3-5 instead of 10)
2. Analyze subset of emails
3. Use shorter campaign with fewer emails
4. Run analysis during off-peak hours

### Issue: "No email content to analyze"

**Causes:**

- All emails are empty/have no body
- Campaign has no emails

**Solutions:**

1. Create/edit emails with actual content
2. Use HTML editor to add body text
3. Ensure emails are saved before analysis

### Issue: Generated Email Has Weird Formatting

**Causes:**

- API returned malformed HTML
- JSON parsing issue

**Solutions:**

1. Click "✨ AI Generate" again with same parameters
2. Manually edit the generated content
3. Report to OpenAI if consistently broken

### Issue: "nltk" or "gensim" module not found

**Solution:**

```bash
# Reinstall dependencies
pip install -r requirements.txt

# Or specific packages
pip install nltk gensim pandas openai
```

### Issue: Topic Analysis Shows "No data"

**Causes:**

- Campaign has no emails
- All emails are empty

**Solutions:**

1. Add emails to campaign with content
2. Save emails before running analysis
3. Check that body_html field is populated

---

## Performance Considerations

### Email Generation

- **Time**: 5-15 seconds per email
- **Cost**: ~$0.002-0.01 per email
- **Rate Limit**: ~3-4 per minute (OpenAI free tier)
- **Cache**: Store frequently used generations in EmailAIAnalysis

### Topic Analysis

- **Time**: 30-60 seconds for 10 emails, 2-5 minutes for 50+ emails
- **Memory**: ~100MB for 100 emails
- **Scalability**: Works best with 5-50 emails per analysis
- **Parallelization**: Not parallelized (single-threaded)

### Optimization Tips

1. **Batch Analysis**: Analyze full campaigns at once instead of incremental
2. **Cache Results**: Results are saved to DB and can be reused
3. **Lazy Loading**: Only generate when user clicks button
4. **Async Processing**: Consider Celery for long-running analyses (future enhancement)

---

## Future Enhancements

Potential improvements for future versions:

1. **Async Processing**: Use Celery to handle long-running topic analysis
2. **Email Scoring**: Rate generated emails for quality/engagement
3. **A/B Testing**: Generate multiple versions and compare
4. **Custom Tone Templates**: Save user-defined tone preferences
5. **Advanced Topic Visualization**: 3D topic space, interactive exploration
6. **Multi-language Support**: Generate and analyze emails in other languages
7. **Fine-tuned Models**: Train on user's historical email data for better results
8. **Cost Tracking**: Monitor API spending and costs per campaign

---

## Support & Resources

- **OpenAI Documentation**: https://platform.openai.com/docs
- **Gensim Documentation**: https://radimrehurek.com/gensim/
- **NLTK Documentation**: https://www.nltk.org/
- **Django REST Framework**: https://www.django-rest-framework.org/

---

## Changelog

### Version 1.0 (Current)

- ✅ AI email generation with GPT-3.5-turbo
- ✅ Topic modeling with LDA algorithm
- ✅ Database model for storing AI results
- ✅ Web interface for both features
- ✅ RESTful API endpoints
- ✅ Comprehensive error handling
- ✅ Email analysis dashboard

---

**Last Updated:** November 2025
**Author:** Alex Project Team
**Status:** Production Ready
