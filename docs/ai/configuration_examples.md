# Ollama Configuration Examples

This file contains practical configuration examples for different deployment scenarios.

## 📋 Deployment Scenarios

### Scenario 1: Local Development (Recommended for Testing)

**Setup:**

- Django and Ollama on the same machine
- Good for: Development, testing, learning

**Server Configuration:**

```bash
# Start Ollama (default localhost only)
ollama serve

# Or with systemd
sudo systemctl start ollama
```

**Django Configuration (.env):**

```bash
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.1:8b
```

**Test:**

```bash
curl http://localhost:11434/api/tags
```

---

### Scenario 2: Separate Server (Same Local Network)

**Setup:**

- Django on server A (192.168.1.10)
- Ollama on server B (192.168.1.20)
- Good for: Production, resource isolation

**Ollama Server (192.168.1.20):**

```bash
# Configure Ollama to accept remote connections
sudo systemctl edit ollama.service

# Add this:
[Service]
Environment="OLLAMA_HOST=0.0.0.0:11434"

# Restart
sudo systemctl daemon-reload
sudo systemctl restart ollama

# Open firewall
sudo ufw allow from 192.168.1.10 to any port 11434
# Or allow entire subnet:
sudo ufw allow from 192.168.1.0/24 to any port 11434

# Verify
sudo netstat -tlnp | grep 11434
# Should show: 0.0.0.0:11434
```

**Django Server (192.168.1.10) - Production .env:**

```bash
OLLAMA_BASE_URL=http://192.168.1.20:11434
OLLAMA_MODEL=llama3.1:8b
```

**Django Server (192.168.1.10) - dripemails/live.py:**

```python
# Ollama Configuration
OLLAMA_BASE_URL = os.environ.get('OLLAMA_BASE_URL', 'http://192.168.1.20:11434')
OLLAMA_MODEL = os.environ.get('OLLAMA_MODEL', 'llama3.1:8b')
```

**Test from Django Server:**

```bash
curl http://192.168.1.20:11434/api/tags
ping 192.168.1.20
```

---

### Scenario 3: Cloud Deployment (AWS/DigitalOcean/etc.)

**Setup:**

- Django on App Server (10.0.1.10)
- Ollama on AI Server (10.0.1.20)
- Both in same VPC/private network
- Good for: Scalable production

**Ollama Server (10.0.1.20):**

```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Configure for remote access
sudo tee /etc/systemd/system/ollama.service.d/override.conf > /dev/null <<EOF
[Service]
Environment="OLLAMA_HOST=0.0.0.0:11434"
EOF

sudo systemctl daemon-reload
sudo systemctl restart ollama

# Cloud firewall (AWS Security Group / DO Firewall)
# Add inbound rule:
# - Protocol: TCP
# - Port: 11434
# - Source: 10.0.1.10/32 (Django server IP)

# Verify
curl http://localhost:11434/api/tags
```

**Django Server (10.0.1.10) - .env:**

```bash
OLLAMA_BASE_URL=http://10.0.1.20:11434
OLLAMA_MODEL=llama3.1:8b
```

**Django Server - dripemails/live.py:**

```python
OLLAMA_BASE_URL = os.environ.get('OLLAMA_BASE_URL', 'http://10.0.1.20:11434')
OLLAMA_MODEL = os.environ.get('OLLAMA_MODEL', 'llama3.1:8b')
```

---

### Scenario 4: Domain Name with Reverse Proxy (Production Best Practice)

**Setup:**

- Ollama behind Nginx reverse proxy
- HTTPS with SSL certificate
- Good for: Secure production deployments

**Ollama Server - Install Nginx:**

```bash
sudo apt install nginx certbot python3-certbot-nginx

# Get SSL certificate
sudo certbot --nginx -d ollama.yourdomain.com
```

**Nginx Configuration (/etc/nginx/sites-available/ollama):**

```nginx
server {
    listen 443 ssl http2;
    server_name ollama.yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/ollama.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/ollama.yourdomain.com/privkey.pem;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000" always;

    location / {
        proxy_pass http://localhost:11434;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Increase timeout for AI generation
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;
    }
}

# HTTP to HTTPS redirect
server {
    listen 80;
    server_name ollama.yourdomain.com;
    return 301 https://$server_name$request_uri;
}
```

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/ollama /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

**Django Server - .env:**

```bash
OLLAMA_BASE_URL=https://ollama.yourdomain.com
OLLAMA_MODEL=llama3.1:8b
```

---

### Scenario 5: Multiple Django Servers, One Ollama Server

**Setup:**

- Multiple Django app servers
- Single shared Ollama server
- Load balancer in front
- Good for: High-traffic applications

**Ollama Server (10.0.1.50):**

```bash
# Standard remote setup
sudo systemctl edit ollama.service
# Add: Environment="OLLAMA_HOST=0.0.0.0:11434"

# Allow connections from multiple Django servers
sudo ufw allow from 10.0.1.0/24 to any port 11434
```

**Each Django Server - .env:**

```bash
OLLAMA_BASE_URL=http://10.0.1.50:11434
OLLAMA_MODEL=llama3.1:8b
```

**Considerations:**

- Monitor Ollama server resource usage
- Consider horizontal scaling (multiple Ollama servers)
- Implement request queuing for high load

---

## 🖥️ Hardware Recommendations

### Ollama Server Specs by Usage

**Light Usage (< 100 emails/day):**

```
CPU: 4 cores
RAM: 8GB
Storage: 20GB SSD
Model: llama3.1:8b-q4_0 (quantized)
```

**Medium Usage (100-1000 emails/day):**

```
CPU: 8 cores
RAM: 16GB
Storage: 50GB SSD
Model: llama3.1:8b
```

**Heavy Usage (1000+ emails/day):**

```
CPU: 16 cores
RAM: 32GB
Storage: 100GB SSD
Model: llama3.1:8b
Consider: Multiple Ollama instances
```

**Premium Quality:**

```
CPU: 32 cores
RAM: 64GB+
Storage: 200GB SSD
Model: llama3.1:70b
Optional: GPU acceleration
```

---

## 📊 Model Performance Comparison

### Available Models

```bash
# Standard (Recommended)
ollama pull llama3.1:8b
# Size: 4.7GB, RAM: 8GB, Quality: ⭐⭐⭐⭐

# Quantized (Faster)
ollama pull llama3.1:8b-instruct-q4_0
# Size: 2.5GB, RAM: 4GB, Quality: ⭐⭐⭐

# Large (Best Quality)
ollama pull llama3.1:70b
# Size: 40GB, RAM: 64GB, Quality: ⭐⭐⭐⭐⭐

# Alternatives
ollama pull mistral:7b
ollama pull codellama:13b
```

### Configuration by Model

**For llama3.1:8b-q4_0 (Fast/Low Memory):**

```bash
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.1:8b-instruct-q4_0
```

**For llama3.1:70b (Premium Quality):**

```bash
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.1:70b
```

---

## 🔍 Monitoring & Logging

### Monitor Ollama Server

```bash
# Watch system resources
htop

# Monitor Ollama logs
sudo journalctl -u ollama -f

# Check memory usage
free -h

# Check disk usage
df -h
```

### Django Logging Configuration

Add to Django settings:

```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': 'logs/ai_generation.log',
        },
    },
    'loggers': {
        'campaigns.ai_utils': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}
```

---

## 🧪 Testing Configurations

### Test Script (save as `test_ollama_config.py`)

```python
#!/usr/bin/env python
"""Test Ollama configuration and connection."""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dripemails.settings')
django.setup()

from django.conf import settings
import requests

print("=" * 60)
print("Ollama Configuration Test")
print("=" * 60)

# Check Django settings
ollama_url = getattr(settings, 'OLLAMA_BASE_URL', 'NOT SET')
ollama_model = getattr(settings, 'OLLAMA_MODEL', 'NOT SET')

print(f"\n✓ Django Settings Loaded")
print(f"  OLLAMA_BASE_URL: {ollama_url}")
print(f"  OLLAMA_MODEL: {ollama_model}")

# Test connection
print(f"\n→ Testing connection to {ollama_url}...")
try:
    response = requests.get(f"{ollama_url}/api/tags", timeout=5)
    response.raise_for_status()
    print("✓ Connection successful!")

    models = response.json().get('models', [])
    print(f"\n✓ Available models ({len(models)}):")
    for model in models:
        print(f"  - {model['name']}")

    # Check if configured model is available
    model_names = [m['name'] for m in models]
    if ollama_model in model_names:
        print(f"\n✓ Configured model '{ollama_model}' is available")
    else:
        print(f"\n✗ Warning: Configured model '{ollama_model}' not found")
        print(f"  Run: ollama pull {ollama_model}")

except requests.exceptions.ConnectionError:
    print(f"✗ Connection failed: Cannot connect to {ollama_url}")
    print("  - Check if Ollama is running")
    print("  - Verify OLLAMA_BASE_URL is correct")
    print("  - Check firewall settings")
    sys.exit(1)
except Exception as e:
    print(f"✗ Error: {e}")
    sys.exit(1)

# Test generation
print(f"\n→ Testing email generation...")
try:
    from campaigns.ai_utils import generate_email_content

    result = generate_email_content(
        subject="Test Email",
        tone="professional",
        context="This is a test"
    )

    if result.get('success'):
        print("✓ Email generation successful!")
        print(f"  Subject: {result.get('subject', 'N/A')[:50]}")
        print(f"  Body: {result.get('body_html', 'N/A')[:100]}...")
    else:
        print("✗ Email generation failed")
        print(f"  Error: {result.get('error', 'Unknown error')}")
        sys.exit(1)

except Exception as e:
    print(f"✗ Generation error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 60)
print("All tests passed! ✓")
print("=" * 60)
```

Run it:

```bash
python test_ollama_config.py
```

---

## 🔒 Security Checklist

- [ ] Ollama not exposed to public internet
- [ ] Firewall rules limit access to specific IPs
- [ ] Using HTTPS for remote connections
- [ ] Regular security updates applied
- [ ] Monitoring enabled for unusual activity
- [ ] Logs reviewed regularly
- [ ] Backup strategy in place
- [ ] Resource limits configured

---

## 📝 Configuration Checklist

Before deploying:

- [ ] Ollama installed and running
- [ ] Model pulled: `ollama pull llama3.1:8b`
- [ ] Remote access configured (if needed)
- [ ] Firewall rules set
- [ ] Django settings updated
- [ ] `.env` file configured
- [ ] Connection tested with curl
- [ ] Django test successful
- [ ] Performance acceptable
- [ ] Monitoring enabled

---

**Need Help?** See [README.md](README.md) for support options.
