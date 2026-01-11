# How to Launch Drip Emails from DripEmails.org: A Complete Guide

Drip emails are automated email sequences that send messages to subscribers over time. They're perfect for onboarding new users, nurturing leads, and maintaining engagement. This guide will walk you through everything you need to know to launch successful drip email campaigns using DripEmails.org.

## What Are Drip Emails?

Drip emails are a series of automated emails sent to subscribers at predetermined intervals. Unlike a single email blast, drip campaigns automatically send multiple messages over days, weeks, or months, creating a personalized journey for each subscriber.

**Common Use Cases:**

- **Welcome Series**: Introduce new subscribers to your product or service
- **Onboarding**: Guide users through your platform step-by-step
- **Educational Content**: Deliver valuable information over time
- **Product Launches**: Build anticipation with a sequence of announcements
- **Re-engagement**: Win back inactive subscribers

## Getting Started

### Prerequisites

Before launching your first drip campaign, you'll need:

1. **A DripEmails.org Account**: Sign up and log in to your dashboard
2. **Subscribers**: People to send emails to (we'll cover how to add them)
3. **Email Content**: The messages you want to send
4. **SMTP Server** (optional): For local development, you can use the built-in SMTP server

### Understanding the Workflow

The process of launching a drip campaign involves five main steps:

1. **Create a Campaign** - Set up the overall campaign structure
2. **Create Email Templates** - Design the emails in your sequence
3. **Add Subscribers** - Build your subscriber list
4. **Link Subscribers to Campaign** - Connect your list to the campaign
5. **Activate the Campaign** - Launch it and start sending

Let's dive into each step.

---

## Step 1: Create a Campaign

A campaign is the container that holds all your email templates and subscriber information.

### Via Web Interface

1. Navigate to **Campaigns** in your dashboard
2. Click **Create Campaign**
3. Fill in the campaign details:
   - **Name**: Give your campaign a descriptive name (e.g., "Welcome Series Week 1")
   - **Description**: Add notes about the campaign's purpose
   - **Subscriber List**: Select an existing list or create a new one

4. Click **Save**

### Via API

```bash
POST /api/campaigns/
Authorization: Bearer YOUR_API_TOKEN
Content-Type: application/json

{
  "name": "Welcome Series",
  "description": "Onboarding emails for new subscribers",
  "subscriber_list": "list-uuid-here"
}
```

---

## Step 2: Create Email Templates

Each email in your drip sequence is a template. Templates define what gets sent, when it gets sent, and can include dynamic variables.

### Creating Templates via Web Interface

1. Open your campaign and click **Add Email** or navigate to `/campaigns/template/{campaign_id}/`
2. Fill in the template details:
   - **Subject**: The email subject line
   - **Wait Time**: How long to wait before sending this email
   - **Wait Unit**: Minutes, hours, days, weeks, or months
   - **Email Content**: Your email body (HTML supported)

3. Use the WYSIWYG editor to design your email:
   - Format text with bold, italic, colors, and more
   - Add variables like `{{first_name}}`, `{{last_name}}`, `{{email}}`
   - Insert links and images
   - Preview before saving

4. Optionally add a **Footer** from your footer library

5. Click **Save Template**

### AI-Powered Email Generation

DripEmails.org includes AI features to help you create content quickly:

1. Click the **✨ AI Generate** button in the email editor
2. Fill in the form:
   - **Topic**: What is the email about?
   - **Recipient**: Who is this for?
   - **Tone**: Professional, Friendly, Persuasive, Casual, or Formal
   - **Length**: Short, Medium, or Long
   - **Context**: Additional details

3. Click **Generate** and wait 5-15 seconds
4. Review and edit the generated content
5. Save when ready

### Dynamic Variables

Your email templates can include variables that get replaced with subscriber data:

- `{{first_name}}` - Subscriber's first name
- `{{last_name}}` - Subscriber's last name
- `{{full_name}}` - Subscriber's full name
- `{{email}}` - Subscriber's email address

**Example:**

```
Hi {{first_name}},

Welcome to our service! We're excited to have you, {{full_name}}.

You can reach us at support@example.com or reply to {{email}}.

Best regards,
The Team
```

### Creating Templates via API

```bash
POST /api/campaigns/{campaign_id}/emails/
Authorization: Bearer YOUR_API_TOKEN
Content-Type: application/json

{
  "subject": "Welcome to Our Service!",
  "body_html": "<h1>Hi {{first_name}},</h1><p>Welcome!</p>",
  "body_text": "Hi {{first_name}},\n\nWelcome!",
  "wait_time": 1,
  "wait_unit": "days",
  "order": 1
}
```

### Email Sequence Order

The `order` field determines the sequence of emails. Lower numbers are sent first:

- Email 1: `order: 1`, `wait_time: 0` (sent immediately when campaign activates)
- Email 2: `order: 2`, `wait_time: 1`, `wait_unit: "days"` (sent 1 day after email 1)
- Email 3: `order: 3`, `wait_time: 3`, `wait_unit: "days"` (sent 3 days after email 2)

---

## Step 3: Add Subscribers

Subscribers are the people who will receive your drip emails. You can add them individually or in bulk.

### Adding Subscribers via Web Interface

1. Navigate to **Subscribers** in your dashboard
2. Click **Add Subscriber** or **Import Subscribers**
3. For individual adds:
   - Enter email address (required)
   - Add first name and last name (optional)
   - Select subscriber lists to add them to
   - Click **Save**

4. For bulk import:
   - Prepare a CSV file with columns: `email`, `first_name`, `last_name`
   - Click **Import Subscribers**
   - Upload your CSV file
   - Review the preview
   - Click **Import**

### CSV Import Format

Your CSV should look like this:

```csv
email,first_name,last_name
john.doe@example.com,John,Doe
jane.smith@example.com,Jane,Smith
bob@example.com,Bob,
```

### Adding Subscribers via API

```bash
# Add single subscriber
POST /api/subscribers/
Authorization: Bearer YOUR_API_TOKEN
Content-Type: application/json

{
  "email": "user@example.com",
  "first_name": "John",
  "last_name": "Doe"
}

# Import subscribers
POST /api/subscribers/import/
Authorization: Bearer YOUR_API_TOKEN
Content-Type: multipart/form-data

# Upload CSV file in 'file' field
```

---

## Step 4: Link Subscribers to Campaign

A campaign needs a subscriber list. You can either:

1. **Select an existing list** when creating the campaign
2. **Create a new list** and add subscribers to it
3. **Add subscribers to the campaign's list** after creation

### Via Web Interface

1. Open your campaign's edit page
2. Select a **Subscriber List** from the dropdown
3. To add subscribers to the list:
   - Go to **Subscribers**
   - Edit a subscriber or use bulk actions
   - Assign them to the relevant list

### Via API

Subscribers are linked to campaigns through subscriber lists:

```bash
# Get campaign details (shows subscriber_list)
GET /api/campaigns/{campaign_id}/

# Add subscriber to a list
PUT /api/subscribers/{subscriber_id}/
{
  "lists": ["list-uuid-1", "list-uuid-2"]
}
```

---

## Step 5: Activate the Campaign

Once your campaign has emails and subscribers, you're ready to launch!

### Activating via Web Interface

1. Navigate to your campaign
2. Click the **Activate** button
3. Confirm activation

When activated:

- The first email in the sequence is sent immediately to all active subscribers
- Subsequent emails are scheduled based on their `wait_time` and `wait_unit`
- The campaign automatically progresses through the sequence for each subscriber

### Activating via API

```bash
POST /api/campaigns/{campaign_id}/activate/
Authorization: Bearer YOUR_API_TOKEN
```

**Response:**

```json
{
  "message": "Campaign activated successfully"
}
```

### How Automatic Sequencing Works

DripEmails.org automatically handles email sequencing:

1. **When activated**: First email (order: 1) is sent immediately to all subscribers
2. **After each email**: The system checks for the next email in sequence
3. **Scheduling**: The next email is scheduled based on its `wait_time` and `wait_unit`
4. **Sending**: Emails are sent automatically when their scheduled time arrives
5. **Completion**: The sequence continues until all emails are sent

**Example Timeline:**

- Day 0: Campaign activated → Email 1 sent immediately
- Day 1: Email 2 sent (wait_time: 1 day)
- Day 4: Email 3 sent (wait_time: 3 days)
- Day 7: Email 4 sent (wait_time: 3 days)

---

## Sending Individual Emails via API

You can also trigger individual emails programmatically without activating the entire campaign:

### Send Email to Specific Subscriber

```bash
POST /api/campaigns/{campaign_id}/emails/{email_id}/send/
Authorization: Bearer YOUR_API_TOKEN
Content-Type: application/json

{
  "email": "subscriber@example.com",
  "variables": {
    "first_name": "John",
    "last_name": "Doe",
    "full_name": "John Doe"
  }
}
```

### Send with Scheduling

```bash
POST /api/send-email/
Authorization: Bearer YOUR_API_TOKEN
Content-Type: application/json

{
  "email": "subscriber@example.com",
  "campaign_id": "campaign-uuid",
  "email_id": "email-uuid",
  "first_name": "John",
  "last_name": "Doe",
  "schedule": "later",
  "schedule_value": "5",
  "schedule_unit": "minutes"
}
```

**Schedule Options:**

- `"now"` - Send immediately
- `"later"` - Send at a specific time (requires `schedule_value` and `schedule_unit`)

---

## Getting Your API Key

To use the API, you'll need an API key:

1. Log in to your DripEmails.org account
2. Navigate to your **Dashboard** or **Settings**
3. Find the **API Key** section
4. Click **Copy** or **Regenerate** if needed
5. Use it in API requests as: `Authorization: Bearer YOUR_API_KEY`

### Example with cURL

```bash
curl -X POST https://dripemails.org/api/campaigns/{campaign_id}/activate/ \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json"
```

### Example with Python

```python
import requests

api_key = "YOUR_API_KEY"
campaign_id = "your-campaign-uuid"
url = f"https://dripemails.org/api/campaigns/{campaign_id}/activate/"

headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}

response = requests.post(url, headers=headers)
print(response.json())
```

### Example with JavaScript

```javascript
const apiKey = "YOUR_API_KEY";
const campaignId = "your-campaign-uuid";
const url = `https://dripemails.org/api/campaigns/${campaignId}/activate/`;

fetch(url, {
  method: "POST",
  headers: {
    "Authorization": `Bearer ${apiKey}`,
    "Content-Type": "application/json"
  }
})
  .then(response => response.json())
  .then(data => console.log(data));
```

---

## Best Practices

### 1. Start with a Welcome Series

A simple 3-5 email welcome series is perfect for getting started:

- **Email 1** (Day 0): Welcome and introduction
- **Email 2** (Day 1): Key features or benefits
- **Email 3** (Day 3): How to get started
- **Email 4** (Day 7): Success stories or case studies
- **Email 5** (Day 14): Call to action or next steps

### 2. Use Personalization

Always use `{{first_name}}` and other variables to personalize your emails. Personalized emails have higher open and click rates.

### 3. Space Out Your Emails

Don't overwhelm subscribers:

- **Minimum**: 1 day between emails
- **Recommended**: 2-3 days for most campaigns
- **Maximum**: 7 days for low-touch campaigns

### 4. Test Before Launching

Use the **Send Test** feature to preview emails:

1. Open an email template
2. Click **Send Test**
3. Enter a test email address
4. Review the email in your inbox

### 5. Monitor Campaign Performance

After launching, check your analytics:

- **Open Rates**: How many subscribers opened your emails
- **Click Rates**: How many clicked links
- **Unsubscribes**: Monitor for issues

### 6. Keep Subject Lines Clear

- Keep subject lines under 50 characters
- Be specific about the email content
- Use personalization when appropriate

### 7. Include Unsubscribe Links

DripEmails.org automatically adds unsubscribe links, but ensure your emails are compliant with email marketing regulations.

---

## Troubleshooting

### Campaign Won't Activate

**Problem**: You see an error when trying to activate.

**Solutions**:

- Ensure the campaign has at least one email template
- Verify the campaign has a subscriber list
- Check that the subscriber list has active subscribers

### Emails Not Sending

**Problem**: Campaign is activated but emails aren't being sent.

**Solutions**:

- Check your SMTP server configuration
- Verify subscribers are active (`is_active: true`)
- Check scheduled email processing (if using Celery)
- Review server logs for errors

### Variables Not Replacing

**Problem**: `{{first_name}}` appears literally in emails.

**Solutions**:

- Ensure subscriber data includes the required fields
- Check that variables are spelled correctly (case-sensitive)
- Verify subscriber records exist in the database

### Scheduling Issues

**Problem**: Emails aren't sending at the right time.

**Solutions**:

- Verify `wait_time` and `wait_unit` are set correctly
- Check timezone settings in your user profile
- Ensure scheduled email processing is running (cron job or Celery)

---

## Advanced Features

### A/B Testing

Test different subject lines and content:

1. Create multiple email templates with the same order
2. DripEmails.org can help you test which performs better
3. Use analytics to identify winners

### Conditional Sending

While not built-in, you can achieve conditional sending by:

1. Creating separate campaigns for different segments
2. Using the API to activate campaigns based on conditions
3. Managing subscriber lists to target specific groups

### Integration with Webhooks

Monitor campaign events with webhooks:

- Email sent
- Email opened
- Link clicked
- Unsubscribed

---

## Next Steps

Now that you know how to launch drip emails, here's what to do next:

1. **Create Your First Campaign**: Start with a simple 3-email welcome series
2. **Add Test Subscribers**: Use your own email address to test
3. **Activate and Monitor**: Launch your campaign and watch the analytics
4. **Iterate and Improve**: Use data to refine your campaigns

## Resources

- **API Documentation**: See the README.md for complete API reference
- **Support**: Email founders@dripemails.org for help
- **GitHub**: [dripemails/web](https://github.com/dripemails/web)
- **Documentation**: [docs.dripemails.org](https://docs.dripemails.org)

---

## Conclusion

Launching drip emails with DripEmails.org is straightforward once you understand the workflow:

1. **Create** a campaign
2. **Design** your email templates
3. **Add** subscribers
4. **Link** subscribers to the campaign
5. **Activate** and let automation do the work

The platform handles all the complexity of scheduling, sequencing, and delivery, so you can focus on creating great content and engaging with your audience.

Happy emailing! 📧✨

