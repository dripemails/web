#!/usr/bin/env python
import urllib.request
import os

static_dir = os.path.join(os.getcwd(), 'static')
os.makedirs(static_dir, exist_ok=True)

# Download Chart.js 4.0.0
print("Downloading Chart.js 4.0.0...")
chartjs_url = 'https://cdn.jsdelivr.net/npm/chart.js@latest/dist/chart.min.js'
chartjs_path = os.path.join(static_dir, 'chart.min.js')
try:
    urllib.request.urlretrieve(chartjs_url, chartjs_path)
    print(f"✓ Chart.js saved to {chartjs_path}")
except Exception as e:
    print(f"✗ Failed to download Chart.js: {e}")

print("Done!")
