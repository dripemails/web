# Hugging Face API Setup for AI Email Generation

This guide will help you set up the Hugging Face API for AI-powered email generation and revision features in your DripEmails application.

## Overview

The application uses Hugging Face's Inference API with the **Mistral-7B-Instruct-v0.2** model, which is powerful enough for:

- Generating professional email content
- Revising emails for grammar, clarity, and tone
- Creating personalized email campaigns

## Prerequisites

- A Hugging Face account (free tier available)
- Internet connection for API calls
- Python `requests` library (already included in requirements.txt)

## Step 1: Create a Hugging Face Account

1. **Visit Hugging Face**

   - Go to [https://huggingface.co/join](https://huggingface.co/join)
   - Sign up for a free account

2. **Verify Your Email**
   - Check your email for the verification link
   - Click the link to activate your account

## Step 2: Generate an API Token

1. **Access Settings**

   - Log in to your Hugging Face account
   - Go to [https://huggingface.co/settings/tokens](https://huggingface.co/settings/tokens)

2. **Create a New Token**

   - Click "New token"
   - Name it something like "DripEmails API"
   - Select "Read" access (inference API only needs read access)
   - Click "Generate token"

3. **Copy Your Token**
   - **Important**: Copy the token immediately and store it securely
   - You won't be able to see it again after closing the page

## Step 3: Configure Your Environment

### Windows (PowerShell)

1. **Set Environment Variable Temporarily** (for current session):

   ```powershell
   $env:HUGGINGFACE_API_KEY = "hf_your_token_here"
   ```

2. **Set Environment Variable Permanently** (recommended):

   ```powershell
   # Set user-level environment variable
   [System.Environment]::SetEnvironmentVariable('HUGGINGFACE_API_KEY', 'hf_your_token_here', 'User')

   # Restart your terminal/VS Code for changes to take effect
   ```

3. **Or Use .env File** (best for development):
   ```powershell
   # Create or edit .env file in your project root
   echo "HUGGINGFACE_API_KEY=hf_your_token_here" >> .env
   ```

### Linux/macOS

1. **Set Environment Variable Temporarily**:

   ```bash
   export HUGGINGFACE_API_KEY="hf_your_token_here"
   ```

2. **Set Environment Variable Permanently**:

   ```bash
   # Add to ~/.bashrc or ~/.zshrc
   echo 'export HUGGINGFACE_API_KEY="hf_your_token_here"' >> ~/.bashrc
   source ~/.bashrc
   ```

3. **Or Use .env File**:
   ```bash
   echo "HUGGINGFACE_API_KEY=hf_your_token_here" >> .env
   ```

## Step 4: Verify Installation

1. **Start Django Server**

   ```powershell
   python manage.py runserver
   ```

2. **The app will automatically connect to Hugging Face API**

3. **Use the AI features** in the Template Revision page (`/campaigns/template-revision/`)

## Environment Variables (Optional)

If you need to customize settings, you can set these environment variables:

**PowerShell:**

```powershell
# Required
$env:HUGGINGFACE_API_KEY = "hf_your_token_here"

# Optional: Use a different model (default is mistralai/Mistral-7B-Instruct-v0.2)
$env:HUGGINGFACE_MODEL = "mistralai/Mistral-7B-Instruct-v0.2"
```

**Linux/macOS:**

```bash
# Required
export HUGGINGFACE_API_KEY="hf_your_token_here"

# Optional: Use a different model
export HUGGINGFACE_MODEL="mistralai/Mistral-7B-Instruct-v0.2"
```

## Available Models

The default model is `mistralai/Mistral-7B-Instruct-v0.2`, but you can use other models from Hugging Face:

### Recommended Models for Email Generation:

1. **mistralai/Mistral-7B-Instruct-v0.2** (default)

   - Balanced performance and quality
   - Fast inference times
   - Good for general email tasks

2. **meta-llama/Meta-Llama-3-8B-Instruct**

   - Higher quality outputs
   - Requires gated access (request access on model page)
   - Better instruction following

3. **HuggingFaceH4/zephyr-7b-beta**

   - Good for conversational emails
   - Fast and efficient
   - No gated access required

4. **microsoft/Phi-3-mini-4k-instruct**
   - Smaller, faster model
   - Good for simple email tasks
   - Lower API costs

To use a different model, set the `HUGGINGFACE_MODEL` environment variable:

```powershell
$env:HUGGINGFACE_MODEL = "HuggingFaceH4/zephyr-7b-beta"
```

## Using the AI Features

### 1. AI Email Generation

Navigate to your campaigns and use the AI generation feature to create email content based on:

- Subject line
- Tone (professional, casual, friendly)
- Length (short, medium, long)
- Target audience
- Additional context

### 2. AI Email Revision

In the Template Revision page:

1. Select a campaign and email
2. Edit your draft in the editor
3. Click "AI Revise" to improve:
   - Grammar and spelling
   - Clarity and readability
   - Professional tone
   - Overall structure

## Pricing & Rate Limits

### Free Tier

- Hugging Face offers a generous free tier for the Inference API
- Rate limits apply (typically 1000 requests/day)
- Sufficient for development and small-scale usage

### Paid Tiers

- For production use with higher volume, consider:
  - Hugging Face Pro ($9/month) - Higher rate limits
  - Inference Endpoints - Dedicated instances for maximum performance

Visit [https://huggingface.co/pricing](https://huggingface.co/pricing) for current pricing details.

## Troubleshooting

### Error: "Invalid API key"

- Double-check your API key is correct
- Ensure the environment variable is set properly
- Restart your terminal/VS Code after setting the variable
- Make sure the key starts with `hf_`

### Error: "Model is loading"

- The first request to a model may take 20-30 seconds as it loads
- Wait a moment and try again
- Subsequent requests will be faster

### Error: "Rate limit exceeded"

- You've hit the free tier rate limit
- Wait for the rate limit to reset (usually 24 hours)
- Consider upgrading to Hugging Face Pro for higher limits

### Error: "Connection timeout"

- Check your internet connection
- The API may be experiencing high load, try again in a moment
- Consider increasing the timeout in the code if needed

### Model Not Working

- Some models require gated access (you need to request access on the model page)
- Ensure the model name is correct
- Try using the default model first: `mistralai/Mistral-7B-Instruct-v0.2`

## Security Best Practices

1. **Never commit your API key to version control**

   - Add `.env` to your `.gitignore` file
   - Use environment variables for sensitive data

2. **Use separate API keys for development and production**

   - Create different tokens for different environments
   - Revoke tokens you're no longer using

3. **Monitor your API usage**

   - Check your usage at [https://huggingface.co/settings/billing](https://huggingface.co/settings/billing)
   - Set up alerts for unexpected usage patterns

4. **Rotate API keys regularly**
   - Generate new tokens periodically
   - Delete old tokens from your Hugging Face account

## Additional Resources

- **Hugging Face Documentation**: [https://huggingface.co/docs](https://huggingface.co/docs)
- **Inference API Docs**: [https://huggingface.co/docs/api-inference/](https://huggingface.co/docs/api-inference/)
- **Model Hub**: [https://huggingface.co/models](https://huggingface.co/models)
- **Community Forum**: [https://discuss.huggingface.co/](https://discuss.huggingface.co/)

## Support

If you encounter issues:

1. Check the [Hugging Face Status Page](https://status.huggingface.co/)
2. Search the [Community Forum](https://discuss.huggingface.co/)
3. Review the API response error messages for specific guidance
4. Contact Hugging Face support for account-related issues

---

## Quick Start Summary

1. Create account at [huggingface.co/join](https://huggingface.co/join)
2. Generate API token at [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens)
3. Set environment variable: `HUGGINGFACE_API_KEY=hf_your_token_here`
4. Start Django server: `python manage.py runserver`
5. Use AI features in the Template Revision page!

That's it! Your AI email generation system is now powered by Hugging Face. 🚀
