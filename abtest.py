"""
Small standalone exporter: generate a static HTML preview for an AB test
without requiring Streamlit. The script bootstraps Django, pulls the
requested campaign and email (default: first available) and writes an
HTML file in `static_dashboards/abtest.html` that shows the original
and revised bodies side-by-side. This uses jQuery in the page (CDN)
and does not attempt to persist edits back to the DB.
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

    safe_draft = draft_html.replace('</script>', '<\\/script>')
    safe_orig = orig_html.replace('</script>', '<\\/script>') if orig_html else ''

    html_template = """
<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>AB Test Preview</title>
  <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
  <style>
    body{font-family:Arial,Helvetica,sans-serif;margin:20px}
    .col{width:48%;display:inline-block;vertical-align:top}
    .metric-block{border:1px solid #ddd;padding:12px;border-radius:6px;margin-top:20px;background:#fafafa}
    .metric-block input{width:80px}
    table{border-collapse:collapse;margin-top:10px}
    table td{padding:4px 8px;border-bottom:1px solid #eee}
  </style>
</head>

<body>
  <h1>AB Test Preview</h1>
  <p>Campaign: {CAMPAIGN_NAME}</p>

  <div class="col">
    <h2>Original</h2>
    <div>{SAFE_ORIG}</div>

    <div class="metric-block">
      <h3>Original Metrics</h3>
      Opens: <input id="a_opens" type="number" value="0">
      Clicks: <input id="a_clicks" type="number" value="0">
      Conversions: <input id="a_conv" type="number" value="0">
      <div id="a_results"></div>
    </div>
  </div>

  <div class="col" style="float:right">
    <h2>Revised (preview)</h2>
    <textarea id="draft" style="width:100%;height:300px">{SAFE_DRAFT}</textarea>
    <div style="margin-top:8px;color:#666">Note: this preview does not persist edits back to the database.</div>

    <div class="metric-block">
      <h3>Revised Metrics</h3>
      Opens: <input id="b_opens" type="number" value="0">
      Clicks: <input id="b_clicks" type="number" value="0">
      Conversions: <input id="b_conv" type="number" value="0">
      <div id="b_results"></div>
    </div>
  </div>

  <div style="clear:both;margin-top:18px">
    <h3>Live Preview</h3>
    <div id="live_preview_html"
         style="border:1px solid #eee;padding:12px;border-radius:6px;background:#fff">
      {LIVE_PREVIEW}
    </div>
  </div>

  <div class="metric-block" style="margin-top:30px;">
    <h3>A/B Comparison</h3>
    <div id="ab_comparison"></div>
  </div>

<script>
  function pct(x) { return (x * 100).toFixed(2) + "%"; }

  function computeRates(opens, clicks, conv){
      return {
          open_rate: opens > 0 ? clicks / opens : 0,
          ctr: opens > 0 ? clicks / opens : 0,
          ctor: clicks > 0 ? conv / clicks : 0,
          conv_rate: opens > 0 ? conv / opens : 0
      };
  }

  function zTest(p1, n1, p2, n2){
      if(n1===0 || n2===0) return 0;
      var p = (p1*n1 + p2*n2) / (n1+n2);
      var se = Math.sqrt(p*(1-p)*(1/n1 + 1/n2));
      if(se===0) return 0;
      return (p2 - p1) / se;
  }

  function updateMetrics(){
      var A = {
        opens: parseInt($('#a_opens').val()) || 0,
        clicks: parseInt($('#a_clicks').val()) || 0,
        conv: parseInt($('#a_conv').val()) || 0
      };
      var B = {
        opens: parseInt($('#b_opens').val()) || 0,
        clicks: parseInt($('#b_clicks').val()) || 0,
        conv: parseInt($('#b_conv').val()) || 0
      };

      var ra = computeRates(A.opens, A.clicks, A.conv);
      var rb = computeRates(B.opens, B.clicks, B.conv);

      $('#a_results').html(
        "<table>" +
        "<tr><td>Open Rate:</td><td>" + pct(ra.open_rate) + "</td></tr>" +
        "<tr><td>CTR:</td><td>" + pct(ra.ctr) + "</td></tr>" +
        "<tr><td>CTOR:</td><td>" + pct(ra.ctor) + "</td></tr>" +
        "<tr><td>Conv Rate:</td><td>" + pct(ra.conv_rate) + "</td></tr>" +
        "</table>"
      );

      $('#b_results').html(
        "<table>" +
        "<tr><td>Open Rate:</td><td>" + pct(rb.open_rate) + "</td></tr>" +
        "<tr><td>CTR:</td><td>" + pct(rb.ctr) + "</td></tr>" +
        "<tr><td>CTOR:</td><td>" + pct(rb.ctor) + "</td></tr>" +
        "<tr><td>Conv Rate:</td><td>" + pct(rb.conv_rate) + "</td></tr>" +
        "</table>"
      );

      var z = zTest(ra.conv_rate, A.opens, rb.conv_rate, B.opens);

      $('#ab_comparison').html(
        "<table>" +
        "<tr><td>Conversion Lift:</td><td>" +
        pct(rb.conv_rate - ra.conv_rate) + "</td></tr>" +
        "<tr><td>Z-score:</td><td>" + z.toFixed(3) + "</td></tr>" +
        "<tr><td>Significant? (|z| > 1.96)</td><td>" +
        (Math.abs(z) > 1.96 ? "Yes" : "No") +
        "</td></tr>" +
        "</table>"
      );
  }

  $(function(){
      $('#draft').on('input', function(){
        $('#live_preview_html').html($(this).val());
      });

      $('input').on('input', updateMetrics);
      updateMetrics();
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
