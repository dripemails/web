# Quick Start Guide - AI Email Features

Get started with AI-powered email generation and topic analysis in 5 minutes!

## 1️⃣ Setup (1 minute)

### Get OpenAI API Key

1. Visit https://platform.openai.com/api-keys
2. Sign up or log in
3. Create new API key
4. Copy the key

### Set API Key in Your System

```bash
# Windows Command Prompt
set OPENAI_API_KEY=sk-your-api-key-here

# Windows PowerShell
$env:OPENAI_API_KEY="sk-your-api-key-here"

# macOS/Linux (bash/zsh)
export OPENAI_API_KEY=sk-your-api-key-here

# To make permanent, add to ~/.bashrc or ~/.zshrc
```

### Verify Installation

```bash
# Navigate to project
cd web

# Check Django setup
python manage.py check

# Should show: "System check identified no issues (0 silenced)."
```

## 2️⃣ Create an Email with AI (2 minutes)

### Navigate to Email Editor

1. Go to your app → **Campaigns**
2. Click **Create Campaign** or **Edit Campaign**
3. Click **+ Add Email** (or edit existing email)

### Generate Content with AI

1. In the email editor, click **✨ AI Generate**
2. Fill in the modal:
   - **Topic**: e.g., "New AI product launch"
   - **Recipient**: e.g., "customer" (optional)
   - **Tone**: Choose from Professional, Friendly, Persuasive, Casual, Formal
   - **Length**: Short, Medium, or Long
   - **Context**: Any specific details (optional)
3. Click **✨ Generate**
4. Wait 5-15 seconds ⏳
5. Review the generated subject and body
6. Edit if needed
7. Click **Save Template**

**Done!** Your AI-generated email is saved. 🎉

## 3️⃣ Analyze Email Topics (2 minutes)

### Navigate to Analysis Page

1. Go to **Campaigns** → **Email Analysis**
2. Or visit: `/campaigns/email-analysis/`

### Run Topic Analysis

1. Select a campaign from dropdown
2. Adjust the "Number of Topics" slider (try 5 for starters)
3. Click **📊 Analyze Topics**
4. Wait for results... ⏳
5. Explore the results:
   - **Topic Cards**: See discovered topics and keywords
   - **Email Table**: Which topic each email belongs to
   - **Distribution Chart**: Visual breakdown

**Understanding Results:**

- **High Confidence** (>0.7): Email clearly matches this topic
- **Keywords**: Most representative words for that topic
- **Weights**: Importance of each keyword (higher = more important)

## 📍 Where to Find the Features

### Email Generation

- **Page**: Email Template Editor
- **Button**: ✨ AI Generate (top right of editor)
- **URL**: `/campaigns/template/{campaign_id}/`

### Topic Analysis

- **Page**: Email Analysis Dashboard
- **URL**: `/campaigns/email-analysis/`
- **Dropdown**: Select campaign to analyze

## 🔧 Configuration Details

### Environment Variables

```bash
# Required for Email Generation
OPENAI_API_KEY=sk-...

# Optional (already configured)
DJANGO_SETTINGS_MODULE=dripemails.settings
```

### API Endpoints (for developers)

```bash
# Generate email
POST /api/campaigns/{campaign_id}/generate-email/
Body: {
  "subject_topic": "string",
  "recipient": "string",
  "tone": "professional|friendly|persuasive|casual|formal",
  "length": "short|medium|long",
  "context": "string",
  "email_id": "uuid (optional)"
}

# Analyze topics
POST /api/campaigns/{campaign_id}/analyze-topics/
Body: {
  "num_topics": 2-10,
  "num_words": 5
}
```

## ⚠️ Common Issues

### "OPENAI_API_KEY not set"

```bash
# Check if key is set
echo $OPENAI_API_KEY

# If empty, set it (see Setup section above)
```

### Generation taking too long

- OpenAI servers might be busy, wait a minute
- Try again with a simpler topic
- Check your internet connection

### Topic Analysis shows "No data"

- Campaign needs at least 1 email with content
- Save email before running analysis
- Make sure email body is not empty

### Getting rate limited by OpenAI

- Wait 60+ seconds before trying again
- Upgrade your OpenAI plan if frequent
- Consider a larger batch for analysis

## 📚 Learn More

**Detailed Documentation**: See `AI_EMAIL_FEATURES.md`

**Topics Covered:**

- Complete API reference
- Architecture explanation
- Performance tuning
- Advanced usage
- Troubleshooting guide

## 💡 Tips & Tricks

### Email Generation Tips

1. **Be specific with topics**: "Q4 holiday sale" beats "sale"
2. **Test different tones**: Try all 5 to find your brand voice
3. **Use context**: Provide product details, target audience info
4. **Iterate**: Generate multiple versions, pick the best
5. **Edit afterwards**: Generated content is a starting point

### Topic Analysis Tips

1. **Start with 5 topics**: Good default for 10-20 emails
2. **More topics for larger campaigns**: 10 topics for 50+ emails
3. **Fewer topics for cohesive campaigns**: 3 topics if very focused
4. **Run regularly**: Track how topics evolve over time
5. **Export results**: Screenshot for reports/analysis

## 🚀 Next Steps

1. ✅ Set up OpenAI API key
2. ✅ Create a test campaign with a few emails
3. ✅ Generate an email with AI
4. ✅ Analyze topics across your emails
5. ✅ Explore the detailed documentation

## 📞 Support Resources

**OpenAI API Issues**

- https://platform.openai.com/docs/guides/error-handling
- https://status.openai.com

**Topic Analysis Questions**

- Gensim docs: https://radimrehurek.com/gensim/
- NLTK docs: https://www.nltk.org/

**Django Integration**

- Django REST: https://www.django-rest-framework.org/
- Django Docs: https://docs.djangoproject.com/

---

## Performance Notes

**Email Generation**

- Cost: $0.002-0.01 per email
- Time: 5-15 seconds
- Rate: ~3-4 per minute (free tier)

**Topic Analysis**

- Time: 30-60 seconds (10 emails)
- Time: 2-5 minutes (50+ emails)
- Memory: ~100MB for 100 emails
- Best with: 5-50 emails

---

## What Changed in Your App

✅ **New Page**: `/campaigns/email-analysis/` - Topic analysis dashboard
✅ **New Button**: ✨ AI Generate - In email template editor
✅ **New Model**: `EmailAIAnalysis` - Stores AI results
✅ **2 New APIs**: Generate email, Analyze topics
✅ **6 New Dependencies**: openai, nltk, gensim, pandas, + dependencies

---

**You're all set!** Start generating and analyzing emails with AI. 🤖✨

---

_Last Updated: November 2025_
