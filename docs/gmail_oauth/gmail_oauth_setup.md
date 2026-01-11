# Gmail OAuth Setup Guide

This guide will walk you through setting up Google OAuth credentials for Gmail integration.

## Step-by-Step Instructions

### 1. Create a Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click on the project dropdown at the top
3. Click **"New Project"**
4. Enter a project name (e.g., "DripEmails Gmail Integration")
5. Click **"Create"**
6. Wait for the project to be created and select it from the dropdown

### 2. Enable Gmail API

1. In your Google Cloud project, go to **"APIs & Services"** → **"Library"**
2. Search for **"Gmail API"**
3. Click on **"Gmail API"** from the results
4. Click **"Enable"**
5. Wait for the API to be enabled (may take a few seconds)

### 3. Configure OAuth Consent Screen

1. Go to **"APIs & Services"** → **"OAuth consent screen"**
2. Choose **"External"** (unless you have a Google Workspace account)
3. Click **"Create"**
4. Fill in the required information:
   - **App name**: DripEmails (or your app name)
   - **User support email**: your-email@example.com
   - **Developer contact information**: your-email@example.com
5. Click **"Save and Continue"**
6. On **"Scopes"** page, click **"Save and Continue"** (we'll add scopes in the credentials)
7. On **"Test users"** page:
   - Add your email address as a test user (if your app is in testing mode)
   - Click **"Save and Continue"**
8. Review and click **"Back to Dashboard"**

**Note:** If your app is in "Testing" mode, only test users can authenticate. You'll need to publish your app for public use, or keep adding test users.

### 4. Create OAuth 2.0 Credentials

1. Go to **"APIs & Services"** → **"Credentials"**
2. Click **"+ CREATE CREDENTIALS"** at the top
3. Select **"OAuth client ID"**
4. If prompted, select **"Web application"** as the application type
5. Configure the OAuth client:
   - **Name**: DripEmails Gmail OAuth (or any descriptive name)
   - **Authorized JavaScript origins**: 
     - Add: `https://dripemails.org`
     - (For development, you can also add: `http://localhost:8000`)
   - **Authorized redirect URIs**:
     - Add: `https://dripemails.org/api/gmail/callback/`
     - (For development, you can also add: `http://localhost:8000/api/gmail/callback/`)
6. Click **"Create"**
7. **Important:** A popup will appear with your credentials:
   - **Client ID**: Copy this (looks like: `123456789-abc123def456.apps.googleusercontent.com`)
   - **Client secret**: Copy this (looks like: `GOCSPX-abc123def456xyz`)
   - **⚠️ Copy both values immediately - you won't be able to see the client secret again!**

### 5. Add Required Scopes (Optional - for production)

When users authenticate, they'll be asked to grant permissions. The following scopes are used:
- `https://www.googleapis.com/auth/gmail.readonly` - To read emails
- `https://www.googleapis.com/auth/gmail.send` - To send auto-reply emails

These are automatically requested during OAuth flow, but you can add them to your OAuth consent screen for better UX.

### 6. Configure Environment Variables

Add the credentials to your `.env` file:

```bash
# Gmail/Email Provider OAuth Settings
GOOGLE_CLIENT_ID=123456789-abc123def456.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-abc123def456xyz
GOOGLE_REDIRECT_URI=https://dripemails.org/api/gmail/callback/
```

**For local development**, you can also add:
```bash
GOOGLE_REDIRECT_URI=http://localhost:8000/api/gmail/callback/
```

Or configure both redirect URIs in Google Cloud Console and use the appropriate one for each environment.

## Redirect URL Configuration

### ✅ Correct Redirect URLs:

**Production:**
```
https://dripemails.org/api/gmail/callback/
```

**Development:**
```
http://localhost:8000/api/gmail/callback/
```

### ❌ Common Mistakes:

- Missing trailing slash: `https://dripemails.org/api/gmail/callback` ❌
- Wrong path: `https://dripemails.org/gmail/callback/` ❌
- HTTP instead of HTTPS for production: `http://dripemails.org/api/gmail/callback/` ❌
- Wrong domain: `https://www.dripemails.org/api/gmail/callback/` ❌ (unless you also configure www)

**The redirect URL must match EXACTLY what's configured in Google Cloud Console.**

## Verification

After setting up, verify your configuration:

1. **Check Google Cloud Console:**
   - Go to **"APIs & Services"** → **"Credentials"**
   - Click on your OAuth 2.0 Client ID
   - Verify the redirect URI matches: `https://dripemails.org/api/gmail/callback/`

2. **Check your `.env` file:**
   - Verify `GOOGLE_CLIENT_ID` is set
   - Verify `GOOGLE_CLIENT_SECRET` is set
   - Verify `GOOGLE_REDIRECT_URI` matches Google Cloud Console

3. **Test the connection:**
   - Go to your dashboard at `https://dripemails.org`
   - Click "Connect Gmail"
   - You should be redirected to Google's OAuth consent screen
   - After granting permissions, you should be redirected back to your dashboard

## Troubleshooting

### "redirect_uri_mismatch" Error

**Problem:** The redirect URI in your request doesn't match what's configured in Google Cloud Console.

**Solution:**
1. Go to Google Cloud Console → Credentials
2. Click on your OAuth 2.0 Client ID
3. Verify the redirect URI is exactly: `https://dripemails.org/api/gmail/callback/`
4. Make sure there are no extra spaces or trailing characters
5. Save the changes
6. Wait a few minutes for changes to propagate

### "access_denied" Error

**Problem:** User denied access or app is in testing mode and user is not a test user.

**Solution:**
1. If app is in testing mode, add the user's email to test users in OAuth consent screen
2. Or publish your app (for public use)
3. Ask user to try again

### "invalid_client" Error

**Problem:** Client ID or Client Secret is incorrect.

**Solution:**
1. Verify `GOOGLE_CLIENT_ID` in `.env` matches Google Cloud Console
2. Verify `GOOGLE_CLIENT_SECRET` in `.env` matches Google Cloud Console
3. If you lost your client secret, you'll need to create a new OAuth client ID

### "insufficient_permissions" Error

**Problem:** Gmail API is not enabled or wrong scopes are requested.

**Solution:**
1. Verify Gmail API is enabled in Google Cloud Console
2. Check that scopes include `gmail.readonly` and `gmail.send`

## Security Best Practices

1. **Never commit credentials to Git:**
   - Keep `.env` file in `.gitignore`
   - Use environment variables in production

2. **Restrict redirect URIs:**
   - Only add production and development URLs you actually use
   - Don't use wildcards in redirect URIs

3. **Rotate credentials if compromised:**
   - Create a new OAuth client ID
   - Update your `.env` file
   - Revoke the old client ID

4. **Use HTTPS in production:**
   - Always use `https://` for production redirect URIs
   - Never use `http://` for production

## Publishing Your App (Optional)

If you want users outside your test list to connect Gmail:

1. Go to **"OAuth consent screen"**
2. Click **"PUBLISH APP"**
3. Fill in any additional required information
4. Submit for verification (if required for sensitive scopes)
5. Once published, any user can connect their Gmail account

**Note:** For basic Gmail scopes (`readonly` and `send`), you typically don't need verification, but Google may require it for production apps.

## Multiple Environments

If you're using the same Google Cloud project for development and production:

1. **Add multiple redirect URIs** in Google Cloud Console:
   - `http://localhost:8000/api/gmail/callback/` (development)
   - `https://dripemails.org/api/gmail/callback/` (production)

2. **Use environment-specific `.env` files:**
   - Development `.env`: `GOOGLE_REDIRECT_URI=http://localhost:8000/api/gmail/callback/`
   - Production `.env`: `GOOGLE_REDIRECT_URI=https://dripemails.org/api/gmail/callback/`

3. **Or use different OAuth client IDs:**
   - Create separate OAuth clients for dev and prod
   - Use different credentials for each environment

## Quick Reference

**Redirect URI (Production):**
```
https://dripemails.org/api/gmail/callback/
```

**Redirect URI (Development):**
```
http://localhost:8000/api/gmail/callback/
```

**Required Scopes:**
- `https://www.googleapis.com/auth/gmail.readonly`
- `https://www.googleapis.com/auth/gmail.send`

**Google Cloud Console:**
- Main page: https://console.cloud.google.com/
- APIs & Services: https://console.cloud.google.com/apis/credentials
- OAuth consent screen: https://console.cloud.google.com/apis/credentials/consent

