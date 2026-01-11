# Email Tracking Implementation

## Overview

This document describes the email tracking system that monitors opens and clicks in real-time, automatically updating campaign statistics.

## Features

### 1. **Tracking Pixel for Email Opens**

- A transparent 1x1 pixel GIF is automatically injected into every campaign email
- When the recipient opens the email, their email client requests the pixel image
- The request triggers an event that records the email open

### 2. **Link Click Tracking**

- All links in campaign emails are automatically wrapped with tracking URLs
- When recipients click links, they are redirected through the tracking system
- Each click is recorded before redirecting to the original destination
- Preserves original link attributes (classes, styles, etc.)

### 3. **Real-Time Statistics Updates**

- Campaign analysis page automatically refreshes statistics every 15 seconds
- Shows "Updated Xs ago" timestamp to indicate data freshness
- Updates without requiring page reload

## How It Works

### Backend Implementation

#### 1. Email Sending (`campaigns/tasks.py`)

**Tracking Pixel Injection:**

```python
def _inject_tracking_pixel(html_body, tracking_url):
    """Injects a 1x1 transparent tracking pixel before </body> tag"""
    pixel_img = f'<img src="{tracking_url}" alt="" width="1" height="1" style="display:none;" />'
    if '</body>' in html_body:
        return html_body.replace('</body>', f'{pixel_img}</body>')
    return html_body + pixel_img
```

**Link Wrapping:**

```python
def _wrap_links_with_tracking(html_body, tracking_base_url, subscriber_email):
    """Wraps all <a> tags with tracking redirects using regex"""
    # Skips: #anchors, mailto: links, existing tracking links
    # Preserves: all HTML attributes (class, style, target, etc.)
```

**Email Sending Flow:**

1. `send_campaign_email()` creates an `EmailEvent` record with a unique tracking ID
2. Tracking URLs are generated: `/analytics/track/open/{tracking_id}/?email={email}`
3. Tracking pixel is injected into HTML body
4. All links are wrapped with click tracking: `/analytics/track/click/{tracking_id}/?email={email}&url={original_url}`
5. Email is sent with tracking in place

#### 2. Event Processing (`campaigns/tasks.py`)

**Open Tracking:**

```python
def process_email_open(tracking_id, subscriber_email):
    """Records email open event (once per subscriber)"""
    # Checks if already opened to prevent duplicates
    # Updates EmailEvent with opened_at timestamp
    # Increments campaign.open_count
```

**Click Tracking:**

```python
def process_email_click(tracking_id, subscriber_email, link_url):
    """Records link click event (allows multiple clicks)"""
    # Creates new EmailEvent for each click
    # Increments campaign.click_count
```

#### 3. Statistics API (`campaigns/views.py`)

**Endpoint:** `GET /api/campaigns/<uuid:campaign_id>/stats/`

**Returns:**

```json
{
  "campaign": { "id": "...", "name": "..." },
  "overall_stats": {
    "sent_count": 100,
    "open_count": 45,
    "click_count": 12,
    "open_rate": "45.0%",
    "click_rate": "12.0%"
  },
  "email_stats": [
    {
      "email_id": "...",
      "subject": "Welcome Email",
      "sent": 100,
      "opened": 45,
      "clicked": 12,
      "unique_opens": 42,
      "open_rate": "45.0%",
      "click_rate": "12.0%"
    }
  ],
  "recent_events": [
    {
      "id": "...",
      "event_type": "opened",
      "subscriber_email": "user@example.com",
      "timestamp": "2024-01-15T10:30:00Z",
      "subject": "Welcome Email"
    }
  ]
}
```

### Frontend Implementation

#### Auto-Refresh JavaScript (`templates/campaigns/campaign_analysis.html`)

**Key Features:**

- Fetches fresh statistics every 15 seconds
- Updates metric cards with new data
- Shows "Updated Xs ago" timestamp
- Starts after 5-second initial delay
- Console logging for debugging

**Updated Elements:**

- Sent count
- Open count
- Click count
- Open rate (%)
- Click rate (%)
- Last updated timestamp

## Configuration

### Required Settings

**`dripemails/settings.py`:**

```python
# Base URL for tracking links (required)
SITE_URL = os.environ.get('SITE_URL', 'http://localhost:8000')
```

### Environment Variables

```bash
# Windows PowerShell
$env:SITE_URL = "https://yourdomain.com"

# Linux/macOS
export SITE_URL="https://yourdomain.com"
```

**For production deployment**, update `SITE_URL` to your actual domain:

```bash
export SITE_URL="https://web.dripemails.org"
```

## Testing

### 1. Test Email Tracking

**Send a test campaign:**

```bash
cd c:\Users\Aidan\Desktop\alexProject\web
python manage.py shell
```

```python
from campaigns.models import Campaign, Email
from campaigns.tasks import send_campaign_email

# Get a campaign
campaign = Campaign.objects.first()

# Send to test email
send_campaign_email.delay(
    campaign_id=str(campaign.id),
    recipient_email="your-email@example.com"
)
```

**Verify tracking:**

1. Open the email in your email client
2. Check if the tracking pixel loaded (view email source, look for tracking URL)
3. Click a link in the email
4. Go to Campaign Analysis page
5. Verify statistics updated

### 2. Test Real-Time Updates

1. Navigate to: `/campaigns/campaign-analysis/?campaign_id=<your-campaign-uuid>`
2. Open browser DevTools Console (F12)
3. Send test emails or simulate opens/clicks
4. Watch console for: `Campaign stats refreshed: {...}`
5. Observe metrics updating automatically
6. Check timestamp showing "Updated Xs ago"

### 3. Test API Endpoint

```bash
# Get campaign stats
curl http://localhost:8000/api/campaigns/<campaign-uuid>/stats/
```

## Troubleshooting

### Issue: Tracking pixel not loading

**Symptoms:**

- Opens not being tracked
- 404 errors in email client logs

**Solutions:**

1. Verify `SITE_URL` is set correctly
2. Check that `/analytics/track/open/` endpoint is accessible
3. Ensure `EmailEvent` was created before sending
4. Check Django logs for errors

**Debug:**

```python
from campaigns.models import EmailEvent
# Find tracking events
events = EmailEvent.objects.filter(campaign=campaign)
print(f"Total events: {events.count()}")
print(f"Opened: {events.filter(opened_at__isnull=False).count()}")
```

### Issue: Links not redirecting

**Symptoms:**

- Clicks not tracked
- Links broken or not working

**Solutions:**

1. Check link wrapping didn't break HTML
2. Verify tracking URL format: `/analytics/track/click/{id}/?email=...&url=...`
3. Test URL encoding for special characters
4. Check that `analytics` app is included in `INSTALLED_APPS`

**Debug:**

```python
# Test link wrapping
from campaigns.tasks import _wrap_links_with_tracking

html = '<a href="https://example.com">Test</a>'
tracking_url = "http://localhost:8000/analytics/track/click/test-id/"
result = _wrap_links_with_tracking(html, tracking_url, "test@example.com")
print(result)
```

### Issue: Statistics not auto-refreshing

**Symptoms:**

- Page loads but metrics don't update
- Timestamp stuck on "Loading..."

**Solutions:**

1. Open browser DevTools Console (F12)
2. Check for JavaScript errors
3. Verify API endpoint returns valid JSON
4. Check browser network tab for failed requests
5. Ensure `campaign.id` is a valid UUID

**Debug:**

```javascript
// Test API in browser console
fetch("/api/campaigns/YOUR-CAMPAIGN-UUID/stats/")
  .then((r) => r.json())
  .then((data) => console.log(data))
  .catch((err) => console.error(err));
```

### Issue: Duplicate open events

**Symptoms:**

- Open count higher than sent count
- Multiple opens from same subscriber

**Solutions:**

1. Already handled! `process_email_open()` checks for duplicates
2. Verify logic: `EmailEvent.objects.filter(id=tracking_id, opened_at__isnull=False).exists()`

## Database Schema

### EmailEvent Model

```python
class EmailEvent(models.Model):
    id = models.UUIDField(primary_key=True)  # Used as tracking_id
    campaign = models.ForeignKey(Campaign)
    email = models.ForeignKey(Email)
    subscriber_email = models.EmailField()
    event_type = models.CharField()  # sent, opened, clicked, bounced, etc.
    sent_at = models.DateTimeField()
    opened_at = models.DateTimeField(null=True)
    clicked_at = models.DateTimeField(null=True)
    link_clicked = models.URLField(null=True)
```

### Campaign Model

```python
class Campaign(models.Model):
    sent_count = models.IntegerField(default=0)
    open_count = models.IntegerField(default=0)
    click_count = models.IntegerField(default=0)

    @property
    def open_rate(self):
        return f"{(self.open_count / self.sent_count * 100):.1f}%" if self.sent_count > 0 else "0%"

    @property
    def click_rate(self):
        return f"{(self.click_count / self.sent_count * 100):.1f}%" if self.sent_count > 0 else "0%"
```

## Performance Considerations

### Database Queries

- Opens use `.exists()` check (fast, no data transfer)
- Statistics aggregated with `.aggregate()` and `.annotate()`
- Recent events limited to 50 with `.order_by('-created_at')[:50]`

### API Rate Limiting

- Frontend polls every 15 seconds (4 requests/minute)
- Consider adding caching for high-traffic campaigns:

  ```python
  from django.views.decorators.cache import cache_page

  @cache_page(10)  # Cache for 10 seconds
  def campaign_stats_api(request, campaign_id):
      ...
  ```

### Email Client Considerations

- Some email clients block images by default (affects open tracking)
- Corporate firewalls may block tracking pixels
- Privacy-focused clients may not load external images
- Click tracking is more reliable than open tracking

## Security

### URL Validation

```python
# Link wrapping skips potentially dangerous URLs
if href.startswith('#') or href.startswith('mailto:'):
    continue  # Don't wrap
```

### Email Validation

- All subscriber emails validated before tracking
- Prevents injection attacks via email parameter

### Rate Limiting (Recommended)

Consider adding rate limiting to tracking endpoints:

```python
from django.views.decorators.cache import cache_page
from django.utils.decorators import method_decorator
from rest_framework.throttling import UserRateThrottle
```

## Next Steps

### Enhancements to Consider

1. **Heatmap Visualization**

   - Show which links get clicked most
   - Visualize open times (best time to send)

2. **Geolocation Tracking**

   - Track subscriber location from IP
   - Optimize send times by timezone

3. **Device Detection**

   - Track mobile vs desktop opens
   - Optimize email design accordingly

4. **A/B Testing Integration**

   - Compare different subject lines
   - Test email content variations

5. **Export Reports**

   - PDF/CSV export of statistics
   - Scheduled email reports

6. **Webhook Notifications**
   - Real-time alerts for bounces
   - Notify on high unsubscribe rates

## Files Modified

- ✅ `campaigns/tasks.py` - Added tracking injection and event processing
- ✅ `campaigns/views.py` - Added statistics API endpoint
- ✅ `dripemails/urls.py` - Added API route
- ✅ `templates/campaigns/campaign_analysis.html` - Added auto-refresh JavaScript

## Related Documentation

- [HUGGINGFACE_SETUP.md](./HUGGINGFACE_SETUP.md) - AI email generation setup
- [README.md](./README.md) - General project documentation
- [QUICK_START.md](./QUICK_START.md) - Getting started guide

## Support

For issues or questions:

1. Check the troubleshooting section above
2. Review Django logs: `python manage.py runserver` output
3. Test individual components (pixel injection, link wrapping, API)
4. Verify `SITE_URL` configuration
