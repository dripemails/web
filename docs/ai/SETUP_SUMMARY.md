# Ollama Setup Summary

Complete documentation for installing Ollama on a separate server and configuring Django to access it remotely.

## 📚 Documentation Overview

All documentation is located in `docs/ai/`:

1. **[README.md](README.md)** - Main overview and navigation guide
2. **[quick_start.md](quick_start.md)** - 5-minute setup guide
3. **[ollama_remote_setup.md](ollama_remote_setup.md)** - Comprehensive installation and configuration
4. **[configuration_examples.md](configuration_examples.md)** - Real-world deployment scenarios

## 🎯 Quick Start

### 1. Install Ollama on Remote Server

```bash
# SSH to your server
ssh username@your-server

# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Configure for remote access
sudo systemctl edit ollama.service
# Add: Environment="OLLAMA_HOST=0.0.0.0:11434"

# Restart
sudo systemctl daemon-reload
sudo systemctl restart ollama

# Open firewall
sudo ufw allow 11434/tcp

# Install model
ollama pull llama3.2:1b

# Get server IP
curl ifconfig.me
```

### 2. Configure Django

**Production (`dripemails/live.py`):**

```python
# Ollama Configuration
OLLAMA_BASE_URL = os.environ.get('OLLAMA_BASE_URL', 'http://YOUR_SERVER_IP:11434')
OLLAMA_MODEL = os.environ.get('OLLAMA_MODEL', 'llama3.2:1b')
```

**Local (`dripemails/settings.py`):**

```python
# Ollama Configuration
OLLAMA_BASE_URL = env('OLLAMA_BASE_URL', default='http://localhost:11434')
OLLAMA_MODEL = env('OLLAMA_MODEL', default='llama3.2:1b')
```

**Environment Variables (`.env`):**

```bash
# Production
OLLAMA_BASE_URL=http://192.168.1.100:11434
OLLAMA_MODEL=llama3.2:1b

# Local
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2:1b
```

### 3. Test Connection

```bash
# Test from command line
curl http://YOUR_SERVER_IP:11434/api/tags

# Test from Django
python manage.py shell
>>> from campaigns.ai_utils import generate_email_content
>>> result = generate_email_content("Test", context="Testing")
>>> print(result)
```

## 📋 Configuration Files Modified

### 1. `dripemails/settings.py`

Added Ollama configuration for local development:

```python
OLLAMA_BASE_URL = env('OLLAMA_BASE_URL', default='http://localhost:11434')
OLLAMA_MODEL = env('OLLAMA_MODEL', default='llama3.2:1b')
```

### 2. `dripemails/live.py`

Added Ollama configuration for production:

```python
OLLAMA_BASE_URL = os.environ.get('OLLAMA_BASE_URL', 'http://localhost:11434')
OLLAMA_MODEL = os.environ.get('OLLAMA_MODEL', 'llama3.2:1b')
```

### 3. `campaigns/ai_utils.py`

Updated to use Django settings:

```python
from django.conf import settings

OLLAMA_BASE_URL = getattr(settings, 'OLLAMA_BASE_URL', 'http://localhost:11434')
OLLAMA_MODEL = getattr(settings, 'OLLAMA_MODEL', 'llama3.2:1b')
```

## 🌐 Deployment Scenarios

### Local Development

- Django and Ollama on same machine
- Use: `http://localhost:11434`

### Local Network

- Django on one machine, Ollama on another
- Use: `http://192.168.1.X:11434`

### Cloud/Production

- Django and Ollama on separate cloud instances
- Use: `http://10.0.1.X:11434`

### With Domain

- Ollama behind reverse proxy with SSL
- Use: `https://ollama.yourdomain.com`

## 🔧 Key Commands

```bash
# Get server IP
curl ifconfig.me
hostname -I

# Check Ollama status
sudo systemctl status ollama

# View logs
sudo journalctl -u ollama -f

# List models
ollama list

# Test connection
curl http://localhost:11434/api/tags

# Test from remote
curl http://YOUR_IP:11434/api/tags
```

## 📊 Recommended Hardware

- **CPU:** 4-8 cores
- **RAM:** 8-16GB minimum
- **Storage:** 20GB+ SSD
- **Network:** Low latency connection between Django and Ollama

## 🔒 Security Notes

1. **Firewall:** Only allow connections from Django server
2. **Private Network:** Keep on internal network if possible
3. **VPN:** Use VPN for internet connections
4. **Reverse Proxy:** Use Nginx with SSL for production

## 📖 Full Documentation

For complete details, see:

- [docs/ai/README.md](README.md) - Main documentation hub
- [docs/ai/quick_start.md](quick_start.md) - Quick setup guide
- [docs/ai/ollama_remote_setup.md](ollama_remote_setup.md) - Comprehensive guide
- [docs/ai/configuration_examples.md](configuration_examples.md) - Real-world examples

---

**Created:** January 4, 2026  
**Location:** `docs/ai/`  
**Django Project:** DripEmails
