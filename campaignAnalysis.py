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


# Compute bounce & complaints & reputation proxy
bounce_count = EmailEvent.objects.filter(email__campaign=campaign, event_type='bounced').count()
complaint_count = EmailEvent.objects.filter(email__campaign=campaign, event_type='complaint').count()

# Simple reputation proxy: complaints / sends (just a placeholder metric)
total_sent = sum(sent)
sender_reputation = 1 - (complaint_count / total_sent) if total_sent else 1


html = html.replace('{BOUNCE_COUNT}', str(bounce_count))
html = html.replace('{COMPLAINT_COUNT}', str(complaint_count))
html = html.replace('{SENDER_REPUTATION}', str(round(sender_reputation, 3)))

    # --- Delivery & Bounce Metrics (safe defaults if missing fields) ---
    sent = getattr(email, 'sent_count', None) or 0
    delivered = getattr(email, 'delivered_count', None) or sent  # assume delivered ≈ sent if missing
    bounced = getattr(email, 'bounced_count', None) or 0

    delivery_rate = (delivered / sent * 100) if sent > 0 else 0
    bounce_rate = (bounced / sent * 100) if sent > 0 else 0

    # Format for HTML injection
    delivery_rate_html = f"{delivery_rate:.2f}%"
    bounce_rate_html = f"{bounce_rate:.2f}%"



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
  <table style="border-collapse:collapse;margin-top:8px;">
      <tr>
        <td style="padding:6px 12px;border:1px solid #ccc;">Sent</td>
        <td style="padding:6px 12px;border:1px solid #ccc;">{SENT_COUNT}</td>
      </tr>
      <tr>
        <td style="padding:6px 12px;border:1px solid #ccc;">Delivered</td>
        <td style="padding:6px 12px;border:1px solid #ccc;">{DELIVERED_COUNT}</td>
      </tr>
      <tr>
        <td style="padding:6px 12px;border:1px solid #ccc;">Delivery Rate</td>
        <td style="padding:6px 12px;border:1px solid #ccc;">{DELIVERY_RATE}</td>
      </tr>
      <tr>
        <td style="padding:6px 12px;border:1px solid #ccc;">Bounced</td>
        <td style="padding:6px 12px;border:1px solid #ccc;">{BOUNCED_COUNT}</td>
      </tr>
      <tr>
        <td style="padding:6px 12px;border:1px solid #ccc;">Bounce Rate</td>
        <td style="padding:6px 12px;border:1px solid #ccc;">{BOUNCE_RATE}</td>
      </tr>
    </table>
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
<div class="chart-wrap">
  <h2>Deliverability & Reputation</h2>
  <p><strong>Bounce Rate:</strong> {BOUNCE_COUNT}</p>
  <p><strong>Spam Complaints:</strong> {COMPLAINT_COUNT}</p>
  <p><strong>Sender Reputation (proxy):</strong> {SENDER_REPUTATION}</p>

  <canvas id="deliverabilityChart" width="600" height="250"
      data-bounces="{BOUNCE_COUNT}"
      data-complaints="{COMPLAINT_COUNT}"
      data-sent="{METRICS_SENT}">
  </canvas>
</div>

<div class="chart-wrap">
  <h2>Scroll Depth (simulated)</h2>
  <p>This static report cannot capture real-time user scroll, but you can simulate scroll-depth distribution below.</p>
  <canvas id="scrollChart" width="600" height="250"></canvas>
</div>

<div class="chart-wrap">
  <h2>Click Heatmap (simulated layout)</h2>
  <div id="heatmapArea"
       style="width:600px;height:300px;border:1px solid #eee;position:relative;background:#fafafa">
  </div>
  <p style="color:#666">Click anywhere above to plot a heatmap point.</p>
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
    // Heatmap click handler (no dependencies)
$(function(){
  $('#heatmapArea').on('click', function(e){
      var off = $(this).offset();
      var x = e.pageX - off.left;
      var y = e.pageY - off.top;
      var dot = $('<div>').css({
          position:'absolute',
          left:x-5,
          top:y-5,
          width:'10px',
          height:'10px',
          background:'rgba(255,0,0,0.5)',
          borderRadius:'50%'
      });
      $(this).append(dot);
  });
});

// Scroll-depth simulation chart
var ctxScroll = document.getElementById('scrollChart').getContext('2d');
new Chart(ctxScroll, {
  type:'bar',
  data:{
    labels:['0–25%','25–50%','50–75%','75–100%'],
    datasets:[{
      label:'Users Reaching Depth',
      data:[30,20,15,10], // placeholder values
    }]
  }
});

// Deliverability chart
var dEl = document.getElementById('deliverabilityChart');
if(dEl){
  var dsent = parseInt(dEl.dataset.sent || 0);
  var dbounce = parseInt(dEl.dataset.bounces || 0);
  var dcomp = parseInt(dEl.dataset.complaints || 0);

  new Chart(dEl.getContext('2d'), {
    type:'pie',
    data:{
      labels:['Delivered','Bounced','Complaints'],
      datasets:[{
        data:[
          Math.max(dsent - dbounce - dcomp, 0),
          dbounce,
          dcomp
        ]
      }]
    }
  });
}

  </script>
</body>
</html>
"""

    html = html_template.replace('{CAMPAIGN_NAME}', campaign.name if campaign else '—')
        html = html.replace('{SENT_COUNT}', str(sent))
    html = html.replace('{DELIVERED_COUNT}', str(delivered))
    html = html.replace('{DELIVERY_RATE}', delivery_rate_html)
    html = html.replace('{BOUNCED_COUNT}', str(bounced))
    html = html.replace('{BOUNCE_RATE}', bounce_rate_html)

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
