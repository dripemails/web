# Gmail OAuth Troubleshooting Guide

## Error: "Missing required parameter: client_id"

This error means the Google OAuth flow isn't receiving the `client_id` parameter. This typically happens when:

1. **Environment variables aren't loaded**
2. **Django server wasn't restarted** after adding variables to `.env`
3. **Variables are empty or have typos** in `.env` file

### Quick Fix Steps

1. **Check your `.env` file** (in project root):
   ```bash
   # Should look like this:
   GOOGLE_CLIENT_ID=123456789-abc123def456.apps.googleusercontent.com
   GOOGLE_CLIENT_SECRET=GOCSPX-abc123def456xyz
   GOOGLE_REDIRECT_URI=https://dripemails.org/api/gmail/callback/
   ```

2. **Verify no extra spaces or quotes:**
   ```bash
   # ✅ Correct:
   GOOGLE_CLIENT_ID=123456789-abc123def456.apps.googleusercontent.com
   
   # ❌ Wrong (with quotes):
   GOOGLE_CLIENT_ID="123456789-abc123def456.apps.googleusercontent.com"
   
   # ❌ Wrong (with spaces):
   GOOGLE_CLIENT_ID = 123456789-abc123def456.apps.googleusercontent.com
   ```

3. **Restart your Django server:**
   ```bash
   # Stop the server (Ctrl+C)
   # Then restart:
   python manage.py runserver
   ```

4. **Verify variables are loaded:**
   ```bash
   # In Django shell:
   python manage.py shell
   >>> import os
   >>> print(os.environ.get('GOOGLE_CLIENT_ID'))
   # Should print your client ID, not None or empty string
   ```

### Testing OAuth Configuration

1. **Check the authorization URL endpoint:**
   - Go to: `http://localhost:8000/api/gmail/auth/url/` (or your domain)
   - You should get a JSON response with `auth_url` and `state`
   - If you get an error about missing `client_id`, the environment variables aren't loaded

2. **Verify in Django admin/logs:**
   - Check your Django logs for error messages
   - Look for: "GOOGLE_CLIENT_ID is not set" errors

### Common Issues

#### Issue 1: Variables in `.env` but not loaded

**Solution:**
- Ensure `.env` file is in the project root (same directory as `manage.py`)
- Check that `environ.Env.read_env()` is called in `settings.py`
- Restart Django server

#### Issue 2: Typo in variable name

**Solution:**
- Variable names are case-sensitive
- Must be exactly: `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `GOOGLE_REDIRECT_URI`

#### Issue 3: Empty values

**Solution:**
- Remove any `GOOGLE_*` lines from `.env` that have no value
- Or ensure they have actual values (not empty strings)

#### Issue 4: Multiple `.env` files

**Solution:**
- Django loads `.env` from project root
- Check you're editing the correct `.env` file
- Don't have multiple `.env` files in different locations

### Verification Checklist

- [ ] `.env` file exists in project root
- [ ] `GOOGLE_CLIENT_ID` is set and not empty
- [ ] `GOOGLE_CLIENT_SECRET` is set and not empty
- [ ] `GOOGLE_REDIRECT_URI` is set and matches Google Cloud Console
- [ ] No quotes around values in `.env`
- [ ] No spaces around `=` sign
- [ ] Django server restarted after changes
- [ ] Variables are loaded (check with `os.environ.get()`)

### Testing OAuth Flow

1. **Generate auth URL:**
   ```bash
   curl http://localhost:8000/api/gmail/auth/url/ \
     -H "Authorization: Bearer YOUR_TOKEN"
   ```
   Should return:
   ```json
   {
     "auth_url": "https://accounts.google.com/o/oauth2/auth?...",
     "state": "..."
   }
   ```

2. **Check auth URL contains client_id:**
   - Open the `auth_url` in a browser
   - Should redirect to Google's OAuth consent screen
   - If error about `client_id`, variables aren't loaded

### Debugging Steps

1. **Check environment variables in Django:**
   ```python
   python manage.py shell
   >>> import os
   >>> print("GOOGLE_CLIENT_ID:", os.environ.get('GOOGLE_CLIENT_ID'))
   >>> print("GOOGLE_CLIENT_SECRET:", os.environ.get('GOOGLE_CLIENT_SECRET')[:20] + "...")
   >>> print("GOOGLE_REDIRECT_URI:", os.environ.get('GOOGLE_REDIRECT_URI'))
   ```

2. **Check GmailService initialization:**
   ```python
   python manage.py shell
   >>> from gmail.services import GmailService
   >>> service = GmailService()
   >>> print("Client ID:", service.client_id)
   >>> print("Redirect URI:", service.redirect_uri)
   ```

3. **Test authorization URL generation:**
   ```python
   python manage.py shell
   >>> from gmail.services import GmailService
   >>> from django.contrib.auth.models import User
   >>> user = User.objects.first()
   >>> service = GmailService()
   >>> url = service.get_authorization_url(user)
   >>> print("Auth URL:", url)
   ```

### Still Having Issues?

1. **Check Django logs** for detailed error messages
2. **Verify Google Cloud Console** settings match `.env`
3. **Ensure redirect URI** in Google Cloud Console matches exactly:
   - `https://dripemails.org/api/gmail/callback/` (with trailing slash)
4. **Check server environment** if deploying:
   - Environment variables might need to be set at system level
   - Not just in `.env` file

