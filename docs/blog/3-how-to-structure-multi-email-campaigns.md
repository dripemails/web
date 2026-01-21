# How to Structure Multi-Email Campaigns on the Edit Page

Creating effective multi-email drip campaigns requires careful planning and strategic sequencing. This guide will walk you through how to structure your campaign with multiple emails on the campaign edit page, including best practices for timing, content flow, and subscriber engagement.

## Understanding Email Sequences

A multi-email campaign (also called a drip sequence) is a series of emails sent automatically over time to your subscribers. Unlike single email blasts, drip campaigns nurture your audience with relevant content delivered at strategic intervals.

**Key Benefits:**

- **Automated Engagement**: Maintain regular contact without manual intervention
- **Personalized Journey**: Guide subscribers through a structured experience
- **Higher Conversion Rates**: Multiple touchpoints increase engagement
- **Relationship Building**: Develop trust through consistent, valuable content
- **Behavioral Triggers**: Send emails based on subscriber actions or timelines

## Accessing the Campaign Edit Page

To start structuring your multi-email campaign:

1. Navigate to your **Dashboard** and find your campaign in the campaigns list
2. Click **Edit** on the campaign you want to modify
3. Scroll to the **Email Sequence** section to view and manage all emails in your campaign

The campaign edit page shows:
- All emails in your sequence ordered by their send order
- Each email's subject, wait time, and order position
- Options to add, edit, delete, and reorder emails
- Tabs for viewing sent emails, pending emails, and IMAP auto-replies

## Creating Your Email Sequence

### Step 1: Add Your First Email

Your campaign starts with the first email in the sequence:

1. Click **Create New Email** in the Email Sequence section
2. Enter a compelling subject line
3. Write your email content (HTML and plain text versions)
4. Set the order to **1** (this is your welcome/initial email)
5. Set wait time to **0 days** (sends immediately when campaign starts)
6. Save your email

**Best Practice**: Your first email should be a welcome message that:
- Introduces yourself or your brand
- Sets expectations for what subscribers will receive
- Provides immediate value (tips, resources, discounts)
- Clearly states the purpose of the campaign

### Step 2: Add Follow-Up Emails

After your first email, add subsequent emails to build your sequence:

1. Click **Create New Email** again
2. For each new email, increment the **order** number (2, 3, 4, etc.)
3. Set appropriate **wait time** intervals between emails
4. Create content that builds on previous emails

**Email Order Structure Example:**

- **Email 1** (Order: 1, Wait: 0 days) - Welcome email
- **Email 2** (Order: 2, Wait: 3 days) - Educational content
- **Email 3** (Order: 3, Wait: 7 days) - Case study or testimonial
- **Email 4** (Order: 4, Wait: 14 days) - Special offer or call-to-action
- **Email 5** (Order: 5, Wait: 30 days) - Re-engagement or advanced content

### Step 3: Set Wait Times Strategically

Wait times determine how long the system waits before sending the next email in the sequence. Choose your timing based on:

**Immediate (0 days)**: First email, urgent announcements

**Short-term (1-3 days)**: Follow-ups, reminders, time-sensitive offers

**Medium-term (4-7 days)**: Educational content, newsletters, regular check-ins

**Long-term (14-30+ days)**: Re-engagement campaigns, advanced content, seasonal promotions

**Best Practices for Wait Times:**

- Start with shorter intervals (2-3 days) to maintain momentum
- Gradually increase spacing to avoid overwhelming subscribers
- Consider your industry and content type when setting timing
- Allow enough time between emails for subscribers to engage with previous content
- Test different timing intervals to see what works best for your audience

### Step 4: Reorder Your Emails

If you need to change the sequence order:

1. Use the drag-and-drop functionality (if available) or manually update order numbers
2. The system sends emails based on their order number (1, 2, 3, etc.)
3. Wait times are calculated from when the previous email in sequence was sent

**Important**: Changing the order of emails affects when subscribers receive them in the sequence. Always verify your sequence flow after reordering.

## Content Strategy for Multi-Email Campaigns

### The Welcome Series (Emails 1-3)

**Email 1: Introduction**
- Who you are and what you do
- What subscribers can expect
- Immediate value proposition

**Email 2: Value Delivery**
- Educational content
- Helpful tips or resources
- Building trust

**Email 3: Engagement**
- Ask questions
- Encourage interaction
- Share case studies or examples

### The Middle Sequence (Emails 4-7)

Focus on:
- **Education**: Deep-dive content, tutorials, guides
- **Social Proof**: Testimonials, success stories, reviews
- **Exclusivity**: Early access, special offers, insider information
- **Community**: Invitations to groups, events, forums

### The Nurture Sequence (Emails 8+)

Long-term engagement through:
- **Advanced Content**: In-depth articles, expert interviews
- **Seasonal Campaigns**: Holiday offers, special events
- **Re-engagement**: Win-back campaigns for inactive subscribers
- **Loyalty Rewards**: Special discounts, VIP benefits

## Using Template Variables

Throughout your email sequence, use template variables to personalize content:

- **`{{first_name}}`** - Subscriber's first name
- **`{{last_name}}`** - Subscriber's last name
- **`{{email}}`** - Subscriber's email address
- **`{{subject}}`** - Email subject line

**Example:**
```
Hi {{first_name}},

Thank you for joining our community! We're excited to have you here, {{first_name}}.

Best regards,
The Team
```

## Monitoring Your Campaign

On the campaign edit page, you can monitor your multi-email campaign through three tabs:

### Sent Emails Tab

View all emails that have been successfully sent:
- See which subscribers received which emails
- Track send times and delivery status
- Review email content and variables used

### Pending Emails Tab

Monitor scheduled emails:
- See which emails are queued to send
- View scheduled send times
- Manually trigger pending emails if needed

### IMAP/Gmail Auto-Reply Emails Tab

For auto-reply campaigns:
- View all auto-replies sent via IMAP or Gmail
- Track which incoming emails triggered responses
- Monitor conversation threads

## Best Practices Summary

### Structure

- **Start with value**: First email should provide immediate benefit
- **Build progressively**: Each email should build on previous content
- **Maintain consistency**: Use similar tone and style throughout
- **Plan the journey**: Map out your subscriber's experience from start to finish

### Timing

- **Don't overwhelm**: Space emails appropriately (minimum 2-3 days apart)
- **Be consistent**: Use regular intervals when possible
- **Consider context**: Align timing with your industry and content type
- **Test and optimize**: Monitor engagement and adjust timing accordingly

### Content

- **Provide value**: Every email should offer something useful
- **Mix content types**: Vary between educational, promotional, and engagement emails
- **Personalize**: Use template variables to make emails feel personal
- **Include CTAs**: Each email should have a clear call-to-action

### Optimization

- **Track performance**: Monitor open rates, click rates, and engagement
- **A/B test**: Experiment with different subjects, timing, and content
- **Refine sequences**: Remove underperforming emails, add new ones
- **Segment audiences**: Create different sequences for different subscriber groups

## Common Campaign Structures

### 5-Email Welcome Series

1. Welcome + immediate value (Day 0)
2. Educational content (Day 3)
3. Social proof/testimonial (Day 7)
4. How-to guide or tutorial (Day 14)
5. Special offer or call-to-action (Day 21)

### 10-Email Nurture Campaign

1. Welcome (Day 0)
2. Getting started guide (Day 2)
3. Best practices (Day 5)
4. Case study (Day 8)
5. Advanced tips (Day 12)
6. Community invitation (Day 16)
7. FAQ and resources (Day 20)
8. Success story (Day 25)
9. Exclusive offer (Day 30)
10. Re-engagement (Day 45)

### 3-Email Onboarding Sequence

1. Welcome and setup (Day 0)
2. First steps tutorial (Day 1)
3. Getting help resources (Day 3)

## Troubleshooting

### Emails Not Sending in Order

- Check that order numbers are sequential (1, 2, 3, etc.)
- Verify wait times are set correctly
- Ensure campaign is active
- Check that subscribers are assigned to the campaign

### Subscribers Receiving Wrong Emails

- Review email order numbers
- Check subscriber assignment to campaigns
- Verify that subscribers haven't been unsubscribed
- Confirm email sequence is correctly structured

### Timing Issues

- Wait times are calculated from when the previous email was sent
- If an email fails to send, subsequent emails may be delayed
- Check pending emails tab to see scheduled send times
- Verify timezone settings for accurate scheduling

## Conclusion

Structuring multi-email campaigns effectively requires planning, strategic timing, and valuable content. By using the campaign edit page to organize your email sequence, set appropriate wait times, and monitor performance, you can create engaging drip campaigns that nurture your subscribers and drive results.

Remember to:
- Start with immediate value
- Space emails appropriately
- Build progressive content
- Monitor and optimize continuously
- Personalize with template variables

With these strategies, your multi-email campaigns will deliver consistent value to your subscribers while building lasting relationships.
