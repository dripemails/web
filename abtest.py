"""
Small standalone exporter: generate a static HTML preview for an AB test
without requiring Streamlit. The script bootstraps Django, pulls the
requested campaign and email (default: first available) and writes an
HTML file in `static_dashboards/abtest.html` that shows the original
and revised bodies side-by-side. This uses jQuery in the page (CDN)
and does not attempt to persist edits back to the DB.

Usage: run from the project root with the virtualenv activated:
    python abtest.py [campaign_id] [email_id]

If no IDs are provided the first campaign/email found will be used.
"""

import os
import sys
import pathlib
import webbrowser

# Bootstrap Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dripemails.settings')
import django
django.setup()

from campaigns.models import Campaign, Email


def get_campaign_and_email(campaign_id=None, email_id=None):
    campaigns = list(Campaign.objects.all())
    if not campaigns:
        return None, None
    campaign = None
    if campaign_id:
        try:
            campaign = Campaign.objects.get(id=campaign_id)
        except Campaign.DoesNotExist:
            campaign = campaigns[0]
    else:
        campaign = campaigns[0]

    emails = list(campaign.emails.all().order_by('order'))
    email = None
    if emails:
        if email_id:
            try:
                email = campaign.emails.get(id=email_id)
            except Email.DoesNotExist:
                email = emails[0]
        else:
            email = emails[0]

    return campaign, email


def render_abtest_html(campaign, email, out_path):
    out_path.parent.mkdir(parents=True, exist_ok=True)

    orig_html = (email.body_html or '') if email else ''
    orig_text = (email.body_text or '') if email else ''
    draft_html = orig_html or orig_text

    # Escape closing </script> sequences if needed in content (simple protection)
    safe_draft = draft_html.replace('</script>', '<\/script>')
    safe_orig = orig_html.replace('</script>', '<\/script>') if orig_html else ''

    html_template = """
<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>AB Test Preview</title>
  <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
  <style>body{font-family:Arial,Helvetica,sans-serif;margin:20px}.col{width:48%;display:inline-block;vertical-align:top}.col pre{white-space:pre-wrap;background:#f8f8f8;padding:10px;border-radius:4px}</style>
</head>
<body>
  <h1>AB Test Preview</h1>
  <p>Campaign: {CAMPAIGN_NAME}</p>
  <div class="col">
    <h2>Original</h2>
    <div>
      {SAFE_ORIG}
    </div>
  </div>
  <div class="col" style="float:right">
    <h2>Revised (preview)</h2>
    <textarea id="draft" style="width:100%;height:300px">{SAFE_DRAFT}</textarea>
    <div style="margin-top:8px;color:#666">Note: this preview does not persist edits back to the database.</div>
  </div>

  <div style="clear:both;margin-top:18px">
    <h3>Live Preview</h3>
    <div id="live_preview_html" style="border:1px solid #eee;padding:12px;border-radius:6px;background:#fff">{LIVE_PREVIEW}</div>
  </div>

  <script>
    $(function(){
      $('#draft').on('input', function(){
        var v = $(this).val();
        $('#live_preview_html').html(v);
      });
    });
  </script>
</body>
</html>
"""

    html = html_template.replace('{CAMPAIGN_NAME}', campaign.name if campaign else '—')
    html = html.replace('{SAFE_ORIG}', safe_orig or '<pre>' + (orig_text or 'No content') + '</pre>')
    html = html.replace('{SAFE_DRAFT}', safe_draft)
    html = html.replace('{LIVE_PREVIEW}', safe_draft or '<em>No preview content</em>')

    out_path.write_text(html, encoding='utf-8')


def main():
    campaign_id = sys.argv[1] if len(sys.argv) > 1 else None
    email_id = sys.argv[2] if len(sys.argv) > 2 else None
    campaign, email = get_campaign_and_email(campaign_id, email_id)
    out = pathlib.Path('static_dashboards') / 'abtest.html'
    render_abtest_html(campaign, email, out)
    print(f'Wrote {out.resolve()}')
    webbrowser.open_new_tab(out.resolve().as_uri())


if __name__ == '__main__':
    main()
