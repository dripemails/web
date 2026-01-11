#!/usr/bin/env python
import urllib.request
import os

static_dir = os.path.join(os.getcwd(), 'static')
os.makedirs(static_dir, exist_ok=True)

# Download jQuery 3.7.1
print("Downloading jQuery 3.7.1...")
jquery_url = 'https://code.jquery.com/jquery-3.7.1.min.js'
jquery_path = os.path.join(static_dir, 'jquery-3.7.1.min.js')
try:
    urllib.request.urlretrieve(jquery_url, jquery_path)
    print(f"✓ jQuery saved to {jquery_path}")
except Exception as e:
    print(f"✗ Failed to download jQuery: {e}")

# Download Tailwind CSS
print("Downloading Tailwind CSS...")
tailwind_url = 'https://cdn.tailwindcss.com'
tailwind_path = os.path.join(static_dir, 'tailwind.css')
try:
    urllib.request.urlretrieve(tailwind_url, tailwind_path)
    print(f"✓ Tailwind CSS saved to {tailwind_path}")
except Exception as e:
    print(f"✗ Failed to download Tailwind CSS: {e}")

print("\nDone!")
