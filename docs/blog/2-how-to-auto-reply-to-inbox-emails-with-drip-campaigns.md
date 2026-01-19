# How to Auto-Reply to Inbox Emails with Drip Campaigns

Email auto-replies are automated responses sent to incoming emails based on predefined templates. They're perfect for customer support, acknowledging inquiries, and providing instant responses when you're not available. This guide will walk you through everything you need to know to set up auto-reply campaigns that respond to your inbox emails using DripEmails.org.

## What Are Auto-Reply Campaigns?

Auto-reply campaigns automatically send drip email sequences to people who email you. Unlike traditional auto-responders that send a single message, drip campaigns can send multiple personalized emails over time, creating a conversational experience for your contacts.

**Common Use Cases:**

- **Customer Support**: Provide immediate acknowledgment and follow-up information
- **Lead Nurturing**: Engage with prospects who reach out via email
- **Out-of-Office**: Set up automated responses when you're away
- **Information Requests**: Deliver helpful resources and FAQs
- **Welcome Series**: Onboard new contacts who email you directly

## How It Works

The auto-reply system works in three main steps:

1. **Connect Your IMAP Account** - Link your email account to DripEmails.org
2. **Set Up Your Auto-Reply Campaign** - Create email templates with personalized content
3. **Automated Processing** - The system fetches new emails and sends auto-replies automatically

When someone emails you, the system:
- Detects the incoming email
- Extracts the sender's information (email, name)
- Finds or creates a subscriber for them
- Sends your auto-reply campaign emails
- Tracks all conversations in your dashboard

## Prerequisites

Before setting up auto-replies, you'll need:

1. **A DripEmails.org Account**: Sign up and log in to your dashboard
2. **An Email Account with IMAP**: Most email providers support IMAP (Gmail, Outlook, Yahoo, etc.)
3. **IMAP Credentials**: Your email address, IMAP server, port, username, and password
4. **App Password** (for Gmail): If using Gmail, you'll need an application-specific password

### Getting Gmail App Password

If you're using Gmail, you'll need to create an app-specific password:

1. Go to your [Google Account Settings](https://myaccount.google.com/)
2. Navigate to **Security**
3. Enable **2-Step Verification** if not already enabled
4. Go to **App Passwords** (or visit [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords))
5. Select **Mail** and **Other (Custom name)**
6. Enter "DripEmails.org" as the name
7. Click **Generate**
8. Copy the 16-character password (you'll use this instead of your regular password)

**Note**: For Gmail, use:
- **IMAP Host**: `imap.gmail.com`
- **IMAP Port**: `993`
- **Use SSL**: Yes
- **Username**: Your full Gmail address
- **Password**: Your app password (not your regular password)

## Step 1: Connect Your IMAP Account

The first step is to connect your email account to DripEmails.org so the system can monitor your inbox.

### Via Web Interface

1. Log in to your DripEmails.org dashboard
2. Navigate to **Settings** or **Email Accounts**
3. Click **Connect IMAP Account** or **Add Email Account**
4. Fill in your IMAP credentials:
   - **Email Address**: Your email address
   - **IMAP Host**: Your IMAP server (e.g., `imap.gmail.com`)
   - **IMAP Port**: Usually `993` for SSL or `143` for non-SSL
   - **Username**: Your email address or IMAP username
   - **Password**: Your email password or app password (for Gmail)
   - **Use SSL**: Check this if using port 993 (recommended)

5. Click **Test Connection** to verify your credentials
6. Click **Connect** or **Save**

### Common IMAP Server Settings

**Gmail:**
- Host: `imap.gmail.com`
- Port: `993`
- SSL: Yes
- Username: Your full Gmail address
- Password: App password (see above)

**Outlook/Office 365:**
- Host: `outlook.office365.com`
- Port: `993`
- SSL: Yes
- Username: Your full email address
- Password: Your account password

**Yahoo:**
- Host: `imap.mail.yahoo.com`
- Port: `993`
- SSL: Yes
- Username: Your full Yahoo email address
- Password: App password (generate at [yahoo.com/account/security](https://login.yahoo.com/account/security))

**Custom IMAP Server:**
- Host: Your IMAP server hostname
- Port: Usually `993` (SSL) or `143` (non-SSL)
- SSL: Check with your email provider
- Username: As provided by your email provider
- Password: Your email password

### Via API

```bash
POST /api/gmail/imap/connect/
Authorization: Bearer YOUR_API_TOKEN
Content-Type: application/json

{
  "email": "your.email@example.com",
  "host": "imap.gmail.com",
  "port": 993,
  "username": "your.email@example.com",
  "password": "your-app-password",
  "use_ssl": true
}
```

**Response:**

```json
{
  "message": "IMAP account connected successfully!",
  "credential_id": "credential-uuid-here"
}
```

### Automatic Campaign Creation

When you connect your IMAP account, DripEmails.org automatically:

1. **Creates an IMAP Subscriber List** - Named "IMAP - {your-email}"
2. **Creates an IMAP Auto-Reply Campaign** - Named "IMAP Auto-Reply - {your-email}"
3. **Creates a Default Email Template** - A simple acknowledgment template

You can customize these later, but they're ready to use immediately!

## Step 2: Customize Your Auto-Reply Campaign

Once your IMAP account is connected, you'll want to customize your auto-reply email templates to match your voice and needs.

### Accessing Your Campaign

1. Navigate to **Campaigns** in your dashboard
2. Find your **IMAP Auto-Reply** campaign (named "IMAP Auto-Reply - {your-email}")
3. Click to open it

### Editing the Default Template

The default template is a simple acknowledgment. You can customize it:

1. Click on the email template in your campaign
2. Edit the **Subject** line (default: "Re: {{subject}}")
3. Edit the **Email Content** using the WYSIWYG editor
4. Add variables for personalization:
   - `{{first_name}}` - Sender's first name
   - `{{last_name}}` - Sender's last name
   - `{{email}}` - Sender's email address
   - `{{subject}}` - Original email subject

5. Click **Save Template**

### Creating Additional Email Templates

You can create a multi-email sequence for auto-replies:

**Example Sequence:**

1. **Email 1** (Order: 1, Wait: 0 minutes) - Immediate acknowledgment
   ```
   Subject: Re: {{subject}}
   
   Hi {{first_name}},
   
   Thank you for reaching out! I've received your email and will get back to you within 24 hours.
   
   Best regards,
   [Your Name]
   ```

2. **Email 2** (Order: 2, Wait: 1 day) - Follow-up with helpful resources
   ```
   Subject: Here are some resources that might help
   
   Hi {{first_name}},
   
   While you wait for my detailed response, here are some helpful resources:
   - FAQ: [link]
   - Documentation: [link]
   - Support Portal: [link]
   
   I'll be in touch soon!
   
   Best,
   [Your Name]
   ```

3. **Email 3** (Order: 3, Wait: 3 days) - Final follow-up
   ```
   Subject: Following up on your inquiry
   
   Hi {{first_name}},
   
   I wanted to make sure I haven't missed anything. Have you received the information you needed?
   
   If not, please reply to this email and I'll be happy to help.
   
   Best regards,
   [Your Name]
   ```

### AI-Powered Email Generation

Use the AI generator to create professional auto-reply content:

1. Click **✨ AI Generate** in the email editor
2. Fill in the form:
   - **Topic**: "Auto-reply acknowledgment email"
   - **Recipient**: "People who email me"
   - **Tone**: Professional, Friendly, or Casual
   - **Length**: Short, Medium, or Long
   - **Context**: "I want to acknowledge their email and provide helpful information"

3. Click **Generate**
4. Review and customize the generated content
5. Save when ready

### Best Practices for Auto-Reply Templates

1. **Be Personal**: Always use `{{first_name}}` to personalize responses
2. **Set Expectations**: Let people know when they'll hear back from you
3. **Provide Value**: Include helpful links or resources when relevant
4. **Keep It Brief**: Auto-replies should be concise and to the point
5. **Include Original Context**: Reference `{{subject}}` so they know which email you're responding to

## Step 3: Understanding the Automated Process

Once your campaign is set up, DripEmails.org automatically processes incoming emails and sends auto-replies. Here's how it works:

### The Crawl Process

The system runs a `crawl_imap` process (typically via a cron job) that:

1. **Fetches New Emails** - Connects to your IMAP account and retrieves unprocessed emails
2. **Extracts Recipients** - Identifies who to reply to:
   - **From Address**: The primary sender
   - **To Address**: If the email was sent to you
   - **Sender Address**: If different from From (e.g., mailing lists)
3. **Creates Subscribers** - Automatically adds recipients as subscribers to your IMAP list
4. **Sends Auto-Replies** - Triggers your campaign emails for each recipient
5. **Tracks Conversations** - Records all sent and received emails in your dashboard

### Email Detection Logic

The system intelligently determines who should receive auto-replies:

- **Inbox Emails**: Replies are sent to the `From` address
- **Sent Emails**: If processing your Sent folder, extracts recipients from `To`, `Cc`, and `Bcc` fields
- **Mailing Lists**: Handles cases where `From` and `Sender` differ

### Running the Crawl Manually

You can trigger the crawl process manually:

**Via Command Line:**

```bash
python3 cron.py crawl_imap
```

**With Limit:**

```bash
python3 cron.py crawl_imap --limit 50
```

**Automated via Cron:**

Set up a cron job to run `crawl_imap` periodically:

```bash
# Run every 5 minutes
*/5 * * * * cd /path/to/dripemails.org && python3 cron.py crawl_imap
```

## Step 4: Viewing Your Email Conversations

All your email conversations (both sent and received) appear in the **Recent IMAP Emails** section of your dashboard.

### Dashboard View

1. Log in to your dashboard
2. Scroll to the **Recent IMAP Emails** section
3. View all conversations:
   - **Received Emails**: Shown with a blue/indigo theme
   - **Sent Emails**: Shown with a green theme and "Sent Email" badge
   - **With Replies**: Badged with "Replied" indicator

### Email Details

Click any email to expand and view:

- **From/To/Cc**: Full email addresses and names
- **Subject**: Email subject line
- **Content**: Full email body (HTML or text)
- **Auto-Reply Status**: If an auto-reply was sent, see the campaign email that was used
- **Original Email**: The email that triggered the auto-reply (for sent emails)

### Filtering and Search

Use the search and filter options to find specific conversations:

- Search by sender name or email
- Filter by date range
- Filter by campaign association

## Step 5: Advanced Configuration

### Customizing Campaign Settings

You can customize your IMAP Auto-Reply campaign like any other campaign:

1. **Change Campaign Name**: Edit the campaign name in campaign settings
2. **Modify Subscriber List**: Link to a different subscriber list if needed
3. **Add More Emails**: Create additional templates for different scenarios
4. **Adjust Timing**: Change wait times between emails
5. **Pause/Activate**: Temporarily disable auto-replies without disconnecting IMAP

### Creating Multiple Auto-Reply Campaigns

You can create multiple auto-reply campaigns for different purposes:

1. **Support Campaign**: For customer support inquiries
2. **Sales Campaign**: For sales and lead inquiries
3. **General Campaign**: For general inquiries

**To set up multiple campaigns:**

1. Create separate subscriber lists for each type
2. Create campaigns for each list
3. Manually assign subscribers to the appropriate list
4. Or use campaign conditions to route emails to different campaigns

### Filtering Which Emails Trigger Auto-Replies

Currently, all incoming emails trigger auto-replies. To filter:

1. Process emails manually via the dashboard
2. Use campaign conditions to check email content
3. Add custom logic in the `crawl_imap` function

**Future Enhancement**: We plan to add filtering rules (e.g., skip emails from certain domains, only reply to emails with specific subjects, etc.)

## Best Practices

### 1. Personalize Every Response

Always use `{{first_name}}` and other variables to make responses feel personal and authentic.

### 2. Set Clear Expectations

Tell recipients when they'll hear back from you. For example:
> "I'll get back to you within 24 hours during business days."

### 3. Provide Value Upfront

Include helpful links, resources, or FAQs in your auto-replies to answer common questions immediately.

### 4. Don't Over-Reply

Space out your auto-reply sequence appropriately:
- **Immediate**: 0 minutes (acknowledgment)
- **Follow-up**: 1-3 days
- **Final Check-in**: 5-7 days

### 5. Monitor Your Conversations

Regularly check your dashboard to:
- See which emails triggered auto-replies
- Track engagement with your responses
- Identify patterns in incoming emails

### 6. Test Before Going Live

1. Send a test email to yourself
2. Run `crawl_imap` manually
3. Verify the auto-reply was sent correctly
4. Check the dashboard to see the conversation

### 7. Keep Templates Updated

Regularly review and update your auto-reply templates to:
- Reflect current information
- Match seasonal messaging
- Improve based on feedback

## Troubleshooting

### Auto-Replies Not Sending

**Problem**: Emails are being received but auto-replies aren't being sent.

**Solutions:**

1. **Check Campaign Status**: Ensure your IMAP Auto-Reply campaign is active
2. **Verify Crawl Process**: Make sure `crawl_imap` is running (check cron job or run manually)
3. **Check IMAP Connection**: Verify your IMAP credentials are correct and account is connected
4. **Review Logs**: Check application logs for errors during the crawl process
5. **Verify Email Template**: Ensure at least one email template exists in the campaign

### Emails Not Appearing in Dashboard

**Problem**: Sent emails don't show up in "Recent IMAP Emails".

**Solutions:**

1. **Check Email Matching**: Verify the `from_email` in sent emails matches your IMAP credential's email address
2. **Check Provider Data**: Ensure sent emails have `provider_data['sent'] = True` and `provider_data['folder'] = 'Sent'`
3. **Verify Campaign Detection**: Confirm the campaign name contains "IMAP" and "Auto-Reply" (case-insensitive)
4. **Review Logs**: Check for errors during EmailMessage creation in `send_campaign_email`

### IMAP Connection Issues

**Problem**: Can't connect to IMAP server.

**Solutions:**

1. **Verify Credentials**: Double-check username, password, host, and port
2. **Check SSL Settings**: Ensure SSL is enabled for port 993
3. **App Password**: For Gmail, make sure you're using an app password, not your regular password
4. **Firewall/Network**: Check if your network or firewall is blocking IMAP connections
5. **Test Connection**: Use the "Test Connection" button in the UI to diagnose issues

### Duplicate Auto-Replies

**Problem**: The same person is receiving multiple auto-replies.

**Solutions:**

1. **Check Email Processing**: Verify emails are being marked as `processed = True` after sending replies
2. **Review Crawl Frequency**: If running `crawl_imap` too frequently, reduce the interval
3. **Check Subscriber Status**: Ensure subscribers aren't being created multiple times

### Variables Not Replacing

**Problem**: `{{first_name}}` appears literally in emails instead of the actual name.

**Solutions:**

1. **Check Subscriber Data**: Verify subscriber records have `first_name` and `last_name` fields
2. **Verify Variable Syntax**: Ensure variables use double curly braces: `{{variable_name}}`
3. **Check Case Sensitivity**: Variable names are case-sensitive
4. **Review Template**: Ensure variables are in the email body, not just the subject

## API Reference

### Connect IMAP Account

```bash
POST /api/gmail/imap/connect/
Authorization: Bearer YOUR_API_TOKEN
Content-Type: application/json

{
  "email": "your.email@example.com",
  "host": "imap.gmail.com",
  "port": 993,
  "username": "your.email@example.com",
  "password": "your-app-password",
  "use_ssl": true
}
```

### Get IMAP Credentials

```bash
GET /api/gmail/imap/credentials/
Authorization: Bearer YOUR_API_TOKEN
```

### Test IMAP Connection

```bash
POST /api/gmail/imap/test/
Authorization: Bearer YOUR_API_TOKEN
Content-Type: application/json

{
  "credential_id": "credential-uuid-here"
}
```

### Get Recent IMAP Emails

```bash
GET /api/gmail/imap/emails/
Authorization: Bearer YOUR_API_TOKEN
```

**Response:**

```json
{
  "emails": [
    {
      "id": "email-uuid",
      "subject": "Email subject",
      "from_email": "sender@example.com",
      "to_emails": ["recipient@example.com"],
      "body_text": "Email content...",
      "received_at": "2026-01-18T12:00:00Z",
      "is_sent_email": false,
      "campaign_email_id": null,
      "template_variables": {
        "first_name": "John",
        "last_name": "Doe",
        "email": "john@example.com"
      }
    }
  ],
  "pagination": {
    "page": 1,
    "page_size": 50,
    "total": 100
  }
}
```

### Disconnect IMAP Account

```bash
POST /api/gmail/imap/disconnect/
Authorization: Bearer YOUR_API_TOKEN
Content-Type: application/json

{
  "credential_id": "credential-uuid-here"
}
```

## Security Considerations

### App Passwords

Always use app-specific passwords for email accounts that support them (Gmail, Yahoo, etc.). Never use your primary account password.

### Credential Storage

IMAP credentials are encrypted in the database. However, best practices:

1. Use strong, unique passwords for your email accounts
2. Enable 2-factor authentication on your email accounts
3. Regularly rotate app passwords
4. Monitor your account for suspicious activity

### Access Control

Only authorized users can:
- View email conversations
- Modify auto-reply campaigns
- Access IMAP credentials

Ensure proper access controls are in place in your organization.

## Next Steps

Now that you know how to set up auto-replies, here's what to do next:

1. **Connect Your IMAP Account**: Link your email account to DripEmails.org
2. **Customize Your Templates**: Create personalized auto-reply email templates
3. **Test Your Setup**: Send yourself a test email and verify auto-replies work
4. **Monitor Conversations**: Check your dashboard regularly to see incoming and sent emails
5. **Refine Your Campaigns**: Continuously improve your templates based on responses

## Resources

- **API Documentation**: See the README.md for complete API reference
- **Support**: Email founders@dripemails.org for help
- **GitHub**: [dripemails/web](https://github.com/dripemails/web)
- **Documentation**: [docs.dripemails.org](https://docs.dripemails.org)

---

## Conclusion

Setting up auto-replies to inbox emails with DripEmails.org is a powerful way to provide instant responses to your contacts while maintaining a personal touch through drip campaigns. The system automatically:

1. **Monitors** your inbox for new emails
2. **Extracts** sender information and creates subscribers
3. **Sends** personalized auto-reply sequences
4. **Tracks** all conversations in your dashboard

By following this guide, you can set up a complete auto-reply system that engages with your contacts automatically, saving you time while providing excellent customer experience.

Start with a simple acknowledgment template, then expand to multi-email sequences as you see what works best for your use case. Remember to personalize, provide value, and monitor your conversations regularly.

Happy auto-replying! 📧✨
