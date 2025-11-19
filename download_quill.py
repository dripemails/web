#!/usr/bin/env python
import urllib.request
import os

static_dir = os.path.join(os.getcwd(), 'static')
os.makedirs(static_dir, exist_ok=True)
js_dir = os.path.join(static_dir, 'js')
os.makedirs(js_dir, exist_ok=True)

# Download Quill.js 1.3.7 (stable version)
print("Downloading Quill.js 1.3.7...")

files_to_download = [
    {
        'url': 'https://cdn.jsdelivr.net/npm/quill@1.3.7/dist/quill.min.js',
        'path': os.path.join(js_dir, 'quill.min.js'),
        'name': 'Quill.js (minified)'
    },
    {
        'url': 'https://cdn.jsdelivr.net/npm/quill@1.3.7/dist/quill.snow.css',
        'path': os.path.join(js_dir, 'quill.snow.css'),
        'name': 'Quill Snow Theme CSS'
    },
    {
        'url': 'https://cdn.jsdelivr.net/npm/quill@1.3.7/dist/quill.core.css',
        'path': os.path.join(js_dir, 'quill.core.css'),
        'name': 'Quill Core CSS'
    }
]

for file_info in files_to_download:
    print(f"Downloading {file_info['name']}...")
    try:
        urllib.request.urlretrieve(file_info['url'], file_info['path'])
        print(f"✓ {file_info['name']} saved to {file_info['path']}")
    except Exception as e:
        print(f"✗ Failed to download {file_info['name']}: {e}")

print("Done!")
