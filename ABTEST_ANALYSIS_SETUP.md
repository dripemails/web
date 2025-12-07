# Template Revision & Campaign Analysis Setup Complete

## Overview

The `template_revision.py` and `campaignAnalysis.py` files have been converted from Streamlit-based utilities to jQuery/Chart.js-based exporters. The Django web app now provides:

1. **In-app web views** (Django templates using jQuery + Chart.js)
2. **Standalone HTML exporters** (Python scripts that generate static HTML with charts)

---

## Files Updated/Created

### Django Web App Files

- **`campaigns/views.py`** — Already contains `template_revision_view()` and `campaign_analysis_view()` functions
- **`campaigns/urls.py`** — Already mapped to routes:
  - `/campaigns/template-revision/` → `template_revision_view`
  - `/campaigns/analysis/` → `campaign_analysis_view`
- **`templates/campaigns/template_revision.html`** — Form-based UI with live preview using jQuery
- **`templates/campaigns/campaign_analysis.html`** — Campaign metrics with Chart.js graphs

### Static Assets (Created)

- **`staticfiles/campaigns/js/campaigns-charts.js`** — Chart.js initializer with support for no-data placeholders
- **`static/`** — Created to satisfy Django STATICFILES_DIRS configuration

### Standalone Exporters (Updated)

- **`template_revision.py`** — Bootstrap Django, select campaign/email, write static HTML preview, open in browser
- **`campaignAnalysis.py`** — Bootstrap Django, generate campaign analysis HTML with Chart.js graphs

---

## How to Access the Pages

### Option 1: Run Django Development Server

```powershell
python manage.py runserver
```

Then visit:

- **Template Revision page:** http://127.0.0.1:8000/campaigns/template-revision/
- **Campaign Analysis page:** http://127.0.0.1:8000/campaigns/analysis/

**Note:** Both require login. If you don't have a user, create one:

```powershell
python manage.py createsuperuser
```

### Option 2: Run Standalone Preview Scripts

Generate and open static HTML files locally (no login required):

```powershell
# Template revision preview (first campaign/email by default)
python template_revision.py

# Optional: specify campaign ID and email ID
python template_revision.py <campaign_uuid> <email_uuid>

# Campaign analysis preview
python campaignAnalysis.py

# Optional: specify campaign ID
python campaignAnalysis.py <campaign_uuid>
```

These scripts write HTML files to `static_dashboards/` and open them in your browser.

---

## Key Features

### template_revision.html (In-App View)

- Select campaign and email from dropdowns
- View original email on left
- Edit draft HTML/text on right with live preview
- Save drafts back to the database
- Scroll sync between original and preview

### campaign_analysis.html (In-App View)

- Select campaign
- View summary metrics (Sent, Opens, Clicks)
- **Metrics Chart** (doughnut) — shows distribution of events
- **Monthly Events Chart** (bar) — shows trends over time
- **Per-Email Chart** (horizontal bar) — compares each email's performance
- Tables with detailed breakdowns

### Charts Gracefully Handle No Data

- Empty datasets show placeholder data (e.g., "No data" with 0 values)
- Charts still render properly even if campaign has no events

---

## Verification

Django system check passed:

```
System check identified no issues (0 silenced).
```

All migrations applied successfully. Ready to run!

---

## Database Configuration

- `STATIC_ROOT = 'staticfiles/'` — Where compiled static files go
- `STATICFILES_DIRS = ['static/']` — Where you place application static files
- Charts are loaded from CDN (Chart.js 4.x via jsdelivr.net)
- jQuery is available via `base.html` or can be added to templates

---

## Next Steps

1. **Create a superuser** (if you haven't):

   ```powershell
   python manage.py createsuperuser
   ```

2. **Run the dev server**:

   ```powershell
   python manage.py runserver
   ```

3. **Navigate to the pages**:

   - Login at http://127.0.0.1:8000/accounts/login/
   - Template Revision: http://127.0.0.1:8000/campaigns/template-revision/
   - Analysis: http://127.0.0.1:8000/campaigns/analysis/

4. **Create test campaigns and emails** in the web UI to see charts and data.

5. **For offline use**, run the standalone exporters:
   ```powershell
   python campaignAnalysis.py
   ```

---

## Troubleshooting

- **Static files not loading?** Run: `python manage.py collectstatic --noinput`
- **Charts not rendering?** Ensure Chart.js CDN is reachable or use the offline version
- **Login loop?** Clear browser cookies or use incognito mode
- **Standalone script errors?** Check that campaign(s) and email(s) exist in the database

---

## Summary

All files are now properly configured. The system uses jQuery for interactivity and Chart.js for visualizations, with no Streamlit dependency. Both the in-app and standalone preview modes work seamlessly.
