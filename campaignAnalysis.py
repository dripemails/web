"""
Lightweight campaign analysis exporter that uses the Django ORM to
produce a static HTML report with jQuery + Chart.js graphs. This is a
replacement for the Streamlit-based utility and will write an HTML file
to `static_dashboards/campaign_analysis.html` and open it in the
browser. The produced charts render even when there's no data (they
show zeros / placeholders).

Usage: run from the project root:
    python campaignAnalysis.py [campaign_id]

If no campaign_id is provided the first available campaign is used.
"""

import os
import sys
import json
import pathlib
import webbrowser
from collections import defaultdict

# Bootstrap Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dripemails.settings')
import django
django.setup()

from campaigns.models import Campaign, EmailEvent


def get_campaign(campaign_id=None):
    campaigns = list(Campaign.objects.all())
    if not campaigns:
        return None
    if campaign_id:
        try:
            return Campaign.objects.get(id=campaign_id)
        except Campaign.DoesNotExist:
            return campaigns[0]
    return campaigns[0]


def collect_data(campaign):
    by_month = defaultdict(lambda: {'opened': 0, 'clicked': 0, 'sent': 0})
    email_rows = []
    if not campaign:
        return by_month, email_rows

    events = EmailEvent.objects.filter(email__campaign=campaign)
    for ev in events:
        month = ev.created_at.strftime('%Y-%m')
        if ev.event_type == 'opened':
            by_month[month]['opened'] += 1
        elif ev.event_type == 'clicked':
            by_month[month]['clicked'] += 1
        elif ev.event_type == 'sent':
            by_month[month]['sent'] += 1

    for e in campaign.emails.all():
        sent = EmailEvent.objects.filter(email=e, event_type='sent').count()
        opened = EmailEvent.objects.filter(email=e, event_type='opened').count()
        clicked = EmailEvent.objects.filter(email=e, event_type='clicked').count()
        email_rows.append({'subject': e.subject, 'sent': sent, 'opened': opened, 'clicked': clicked})

    return by_month, email_rows


def render_html(campaign, by_month, email_rows, out_path):
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # Prepare JSON-safe data for the page; ensure arrays are present even when empty
    months = sorted(by_month.keys())
    sent = [by_month[m]['sent'] for m in months]
    opened = [by_month[m]['opened'] for m in months]
    clicked = [by_month[m]['clicked'] for m in months]

    labels = [r['subject'] for r in email_rows]
    sent2 = [r['sent'] for r in email_rows]
    opened2 = [r['opened'] for r in email_rows]
    clicked2 = [r['clicked'] for r in email_rows]

    html_template = """
<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>Campaign Analysis</title>
  <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
  <style>body{font-family:Arial,Helvetica,sans-serif;margin:20px}.chart-wrap{max-width:900px;margin-bottom:24px}</style>
</head>
<body>
  <h1>Campaign Analysis — {CAMPAIGN_NAME}</h1>
  <div class="chart-wrap">
    <canvas id="metricsChart" width="400" height="200" data-sent="{METRICS_SENT}" data-opens="{METRICS_OPENS}" data-clicks="{METRICS_CLICKS}"></canvas>
  </div>

  <div class="chart-wrap">
    <h2>Monthly events</h2>
    <canvas id="monthlyChart" width="800" height="300" data-months='{MONTHS_JSON}' data-sent='{MONTHS_SENT}' data-opens='{MONTHS_OPENS}' data-clicks='{MONTHS_CLICKS}'></canvas>
  </div>

  <div class="chart-wrap">
    <h2>Per-email breakdown</h2>
    <canvas id="perEmailChart" width="800" height="300" data-labels='{EMAIL_LABELS}' data-sent='{EMAIL_SENT}' data-opens='{EMAIL_OPENS}' data-clicks='{EMAIL_CLICKS}'></canvas>
  </div>

  <script src="/static/campaigns/js/campaigns-charts.js"></script>
  <script>
    $(function(){
      // If charts have no data, ensure they render with zero values/placeholders
      var monthlyEl = document.getElementById('monthlyChart');
      if(monthlyEl){
        var months = JSON.parse(monthlyEl.dataset.months || '[]');
        if(months.length === 0){
          // provide a placeholder month so Chart.js can render axes
          monthlyEl.dataset.months = JSON.stringify(['No data']);
          monthlyEl.dataset.sent = JSON.stringify([0]);
          monthlyEl.dataset.opens = JSON.stringify([0]);
          monthlyEl.dataset.clicks = JSON.stringify([0]);
        }
      }

      var perEmailEl = document.getElementById('perEmailChart');
      if(perEmailEl){
        var labels = JSON.parse(perEmailEl.dataset.labels || '[]');
        if(labels.length === 0){
          perEmailEl.dataset.labels = JSON.stringify(['No emails']);
          perEmailEl.dataset.sent = JSON.stringify([0]);
          perEmailEl.dataset.opens = JSON.stringify([0]);
          perEmailEl.dataset.clicks = JSON.stringify([0]);
        }
      }
    });
  </script>
</body>
</html>
"""

    html = html_template.replace('{CAMPAIGN_NAME}', campaign.name if campaign else '—')
    html = html.replace('{METRICS_SENT}', str(campaign.sent_count if campaign else 0))
    html = html.replace('{METRICS_OPENS}', str(campaign.open_count if campaign else 0))
    html = html.replace('{METRICS_CLICKS}', str(campaign.click_count if campaign else 0))

    html = html.replace('{MONTHS_JSON}', json.dumps(months))
    html = html.replace('{MONTHS_SENT}', json.dumps(sent))
    html = html.replace('{MONTHS_OPENS}', json.dumps(opened))
    html = html.replace('{MONTHS_CLICKS}', json.dumps(clicked))

    html = html.replace('{EMAIL_LABELS}', json.dumps(labels))
    html = html.replace('{EMAIL_SENT}', json.dumps(sent2))
    html = html.replace('{EMAIL_OPENS}', json.dumps(opened2))
    html = html.replace('{EMAIL_CLICKS}', json.dumps(clicked2))

    out_path.write_text(html, encoding='utf-8')


def main():
    campaign_id = sys.argv[1] if len(sys.argv) > 1 else None
    campaign = get_campaign(campaign_id)
    by_month, email_rows = collect_data(campaign)
    out = pathlib.Path('static_dashboards') / 'campaign_analysis.html'
    render_html(campaign, by_month, email_rows, out)
    print(f'Wrote {out.resolve()}')
    webbrowser.open_new_tab(out.resolve().as_uri())


if __name__ == '__main__':
    main()
