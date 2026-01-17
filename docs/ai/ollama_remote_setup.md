# Ollama Remote Server Setup Guide

This guide explains how to set up Ollama on a separate server and configure Django to access it remotely for AI email generation.

## Table of Contents

1. [Installing Ollama on Remote Server](#installing-ollama-on-remote-server)
2. [Installing the llama3.2:1b Model](#installing-the-llama318b-model)
3. [Configuring Ollama for Remote Access](#configuring-ollama-for-remote-access)
4. [Getting the Server IP Address](#getting-the-server-ip-address)
5. [Django Configuration](#django-configuration)
6. [Testing the Connection](#testing-the-connection)
7. [Troubleshooting](#troubleshooting)

---

## Installing Ollama on Remote Server

### For Linux (Ubuntu/Debian)

1. **SSH into your remote server:**

   ```bash
   ssh username@your-server-ip
   ```

2. **Install Ollama:**

   ```bash
   curl -fsSL https://ollama.com/install.sh | sh
   ```

3. **Verify installation:**
   ```bash
   ollama --version
   ```

### For Other Linux Distributions

```bash
# Download and install
curl -L https://ollama.com/download/ollama-linux-amd64 -o /usr/local/bin/ollama
chmod +x /usr/local/bin/ollama

# Create ollama user
useradd -r -s /bin/false -m -d /usr/share/ollama ollama

# Create systemd service
sudo tee /etc/systemd/system/ollama.service > /dev/null <<EOF
[Unit]
Description=Ollama Service
After=network-online.target

[Service]
ExecStart=/usr/local/bin/ollama serve
User=ollama
Group=ollama
Restart=always
RestartSec=3
Environment="OLLAMA_HOST=0.0.0.0:11434"

[Install]
WantedBy=default.target
EOF

# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable ollama
sudo systemctl start ollama
```

---

## Installing the llama3.2:1b Model

1. **Pull the model:**

   ```bash
   ollama pull llama3.2:1b
   ```

2. **Verify the model is installed:**

   ```bash
   ollama list
   ```

   You should see `llama3.2:1b` in the list.

3. **Test the model:**
   ```bash
   ollama run llama3.2:1b "Write a short email subject line about a product launch"
   ```

---

## Configuring Ollama for Remote Access

By default, Ollama only listens on localhost. To accept remote connections:

### Method 1: Systemd Service (Recommended for Linux)

1. **Edit the systemd service:**

   ```bash
   sudo systemctl edit ollama.service
   ```

2. **Add the environment variable:**

   ```ini
   [Service]
   Environment="OLLAMA_HOST=0.0.0.0:11434"
   ```

3. **Reload and restart:**
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl restart ollama
   ```

### Method 2: Environment Variable (Temporary)

```bash
OLLAMA_HOST=0.0.0.0:11434 ollama serve
```

### Method 3: Update Existing Service

If Ollama is already installed as a service:

```bash
# Edit the service file
sudo nano /etc/systemd/system/ollama.service

# Add or modify the Environment line in [Service] section:
Environment="OLLAMA_HOST=0.0.0.0:11434"

# Reload and restart
sudo systemctl daemon-reload
sudo systemctl restart ollama
```

### Firewall Configuration

**Ubuntu/Debian (UFW):**

```bash
sudo ufw allow 11434/tcp
sudo ufw reload
```

**CentOS/RHEL (firewalld):**

```bash
sudo firewall-cmd --permanent --add-port=11434/tcp
sudo firewall-cmd --reload
```

**iptables:**

```bash
sudo iptables -A INPUT -p tcp --dport 11434 -j ACCEPT
sudo iptables-save > /etc/iptables/rules.v4
```

---

## Getting the Server IP Address

### Public IP Address

```bash
# Method 1: Using curl
curl ifconfig.me

# Method 2: Using dig
dig +short myip.opendns.com @resolver1.opendns.com

# Method 3: Using wget
wget -qO- ifconfig.me

# Method 4: Using ip command
ip addr show | grep -oP '(?<=inet\s)\d+(\.\d+){3}' | grep -v 127.0.0.1
```

### Private/Local IP Address

```bash
# On Linux
hostname -I | awk '{print $1}'

# Or
ip addr show | grep "inet " | grep -v 127.0.0.1 | awk '{print $2}' | cut -d/ -f1
```

### Verify Ollama is Accessible

From the server itself:

```bash
curl http://localhost:11434/api/tags
```

From another machine:

```bash
curl http://YOUR_SERVER_IP:11434/api/tags
```

You should get a JSON response with available models.

---

## Django Configuration

### 1. Update `settings.py` (Local Development)

Add to `dripemails/settings.py`:

```python
# Ollama Configuration for Local Development
OLLAMA_BASE_URL = env('OLLAMA_BASE_URL', default='http://localhost:11434')
OLLAMA_MODEL = env('OLLAMA_MODEL', default='llama3.2:1b')
```

### 2. Update `live.py` (Production Server)

Add to `dripemails/live.py`:

```python
# Ollama Configuration for Production
OLLAMA_BASE_URL = os.environ.get('OLLAMA_BASE_URL', 'http://YOUR_OLLAMA_SERVER_IP:11434')
OLLAMA_MODEL = os.environ.get('OLLAMA_MODEL', 'llama3.2:1b')
```

Replace `YOUR_OLLAMA_SERVER_IP` with your actual Ollama server IP address.

### 3. Update `ai_utils.py`

Modify `campaigns/ai_utils.py` to use Django settings:

```python
from django.conf import settings

# Ollama configuration from Django settings
OLLAMA_BASE_URL = getattr(settings, 'OLLAMA_BASE_URL', 'http://localhost:11434')
OLLAMA_MODEL = getattr(settings, 'OLLAMA_MODEL', 'llama3.2:1b')
```

### 4. Environment Variables

**Local Development (.env file):**

```bash
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2:1b
```

**Production Server (.env file):**

```bash
OLLAMA_BASE_URL=http://192.168.1.100:11434
OLLAMA_MODEL=llama3.2:1b
```

### 5. Example Configuration by Environment

| Environment   | OLLAMA_BASE_URL                             | Use Case                              |
| ------------- | ------------------------------------------- | ------------------------------------- |
| Local Dev     | `http://localhost:11434`                    | Ollama running on same machine        |
| Local Network | `http://192.168.1.100:11434`                | Ollama on local network server        |
| Production    | `http://10.0.1.50:11434`                    | Ollama on dedicated production server |
| Cloud         | `http://ollama-server.yourdomain.com:11434` | Ollama with domain name               |

---

## Testing the Connection

### 1. Test from Python Shell

```python
import requests
import json

OLLAMA_URL = "http://YOUR_SERVER_IP:11434"

# Test connection
response = requests.get(f"{OLLAMA_URL}/api/tags")
print("Available models:", response.json())

# Test generation
payload = {
    "model": "llama3.2:1b",
    "prompt": "Write a short email subject about a sale",
    "stream": False
}

response = requests.post(f"{OLLAMA_URL}/api/generate", json=payload)
print("Generated:", response.json()['response'])
```

### 2. Test from Django Shell

```bash
python manage.py shell
```

```python
from campaigns.ai_utils import generate_email_content

result = generate_email_content(
    subject="New Product Launch",
    tone="professional",
    length="medium",
    context="We're launching a new tablet device"
)

print(result)
```

### 3. Test via Django Management Command

Create a test script `test_ollama.py` in your project root:

```python
#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dripemails.settings')
django.setup()

from campaigns.ai_utils import generate_email_content

print("Testing Ollama connection...")
result = generate_email_content(
    subject="Test Email",
    tone="professional",
    context="This is a test"
)

if result.get('success'):
    print("✓ Connection successful!")
    print("Subject:", result.get('subject'))
    print("Body preview:", result.get('body_html')[:200])
else:
    print("✗ Connection failed!")
    print("Error:", result.get('error'))
```

Run it:

```bash
python test_ollama.py
```

---

## Troubleshooting

### Connection Refused

**Problem:** `Connection refused` error when connecting to remote Ollama

**Solutions:**

1. Verify Ollama is running: `sudo systemctl status ollama`
2. Check if listening on all interfaces: `sudo netstat -tlnp | grep 11434`
3. Verify firewall allows port 11434
4. Test locally on server: `curl http://localhost:11434/api/tags`

### Model Not Found

**Problem:** `model 'llama3.2:1b' not found`

**Solutions:**

1. Pull the model: `ollama pull llama3.2:1b`
2. Verify installation: `ollama list`
3. Check exact model name in Django settings

### Timeout Errors

**Problem:** Requests timing out

**Solutions:**

1. Increase timeout in `ai_utils.py`:
   ```python
   response = requests.post(..., timeout=300)  # 5 minutes
   ```
2. Check server resources (CPU/RAM)
3. Consider using a smaller model for faster responses

### Permission Denied

**Problem:** Ollama service won't start

**Solutions:**

```bash
# Fix ownership
sudo chown -R ollama:ollama /usr/share/ollama

# Check service logs
sudo journalctl -u ollama -n 50 --no-pager
```

### Slow Response Times

**Solutions:**

1. Use a smaller model: `ollama pull llama3.2:1b-instruct-q4_0`
2. Increase server resources (RAM/CPU)
3. Enable GPU acceleration if available
4. Use caching for repeated requests

### Network Issues

**Check connectivity:**

```bash
# From Django server to Ollama server
ping YOUR_OLLAMA_SERVER_IP
telnet YOUR_OLLAMA_SERVER_IP 11434
curl http://YOUR_OLLAMA_SERVER_IP:11434/api/tags
```

---

## Security Best Practices

### 1. Use a Firewall

Only allow connections from your Django server:

```bash
# Ubuntu/Debian
sudo ufw allow from YOUR_DJANGO_SERVER_IP to any port 11434

# Or restrict to specific network
sudo ufw allow from 192.168.1.0/24 to any port 11434
```

### 2. Use a Reverse Proxy (Recommended for Production)

Set up Nginx to proxy requests to Ollama:

```nginx
server {
    listen 443 ssl;
    server_name ollama.yourdomain.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location / {
        proxy_pass http://localhost:11434;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

Then use: `OLLAMA_BASE_URL=https://ollama.yourdomain.com`

### 3. Use VPN or Private Network

Keep Ollama on a private network not exposed to the internet.

### 4. Monitor Usage

Add logging to track AI generation usage:

```python
# In ai_utils.py
logger.info(f"Ollama request: model={OLLAMA_MODEL}, prompt_length={len(prompt)}")
```

---

## Performance Optimization

### 1. Model Selection

| Model                     | Size  | Speed  | Quality   | Use Case                 |
| ------------------------- | ----- | ------ | --------- | ------------------------ |
| llama3.2:1b               | 4.7GB | Medium | High      | Production (recommended) |
| llama3.2:1b-instruct-q4_0 | 2.5GB | Fast   | Good      | High volume              |
| llama3.1:70b              | 40GB  | Slow   | Excellent | Premium quality          |

### 2. Caching

Implement response caching in Django:

```python
from django.core.cache import cache

def generate_email_content_cached(subject, **kwargs):
    cache_key = f"email_gen_{hash((subject, str(kwargs)))}"
    cached = cache.get(cache_key)

    if cached:
        return cached

    result = generate_email_content(subject, **kwargs)
    cache.set(cache_key, result, 3600)  # Cache for 1 hour
    return result
```

### 3. Async Processing

For better UX, generate emails asynchronously:

```python
from celery import shared_task

@shared_task
def generate_email_async(campaign_id, subject, **kwargs):
    result = generate_email_content(subject, **kwargs)
    # Save to campaign
    return result
```

---

## Additional Resources

- **Ollama Documentation:** https://github.com/ollama/ollama/blob/main/docs/api.md
- **Available Models:** https://ollama.com/library
- **Model Comparison:** https://ollama.com/library/llama3.1

---

## Quick Reference Commands

```bash
# Server Setup
curl -fsSL https://ollama.com/install.sh | sh
ollama pull llama3.2:1b
OLLAMA_HOST=0.0.0.0:11434 ollama serve

# Get IP Address
curl ifconfig.me
hostname -I

# Test Connection
curl http://localhost:11434/api/tags
curl http://YOUR_IP:11434/api/tags

# Service Management
sudo systemctl status ollama
sudo systemctl restart ollama
sudo journalctl -u ollama -f

# Firewall
sudo ufw allow 11434/tcp
```
