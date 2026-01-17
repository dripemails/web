# Ollama Quick Start Guide

Quick reference for setting up and using Ollama with Django DripEmails.

## 🚀 Quick Setup (5 Minutes)

### Local Development

1. **Install Ollama:**

   ```bash
   # Windows (PowerShell as Admin)
   winget install Ollama.Ollama

   # macOS
   brew install ollama

   # Linux
   curl -fsSL https://ollama.com/install.sh | sh
   ```

2. **Start Ollama:**

   ```bash
   ollama serve
   ```

3. **Install Model:**

   ```bash
   ollama pull llama3.2:1b
   ```

4. **Configure Django (.env):**

   ```bash
   OLLAMA_BASE_URL=http://localhost:11434
   OLLAMA_MODEL=llama3.2:1b
   ```

5. **Test:**
   ```bash
   python manage.py shell
   >>> from campaigns.ai_utils import generate_email_content
   >>> result = generate_email_content("Product Launch", context="New tablet")
   >>> print(result['subject'])
   ```

---

## 🌐 Remote Server Setup

### Server Side (Ubuntu/Debian)

```bash
# 1. Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# 2. Configure for remote access
sudo systemctl edit ollama.service
# Add: Environment="OLLAMA_HOST=0.0.0.0:11434"

# 3. Restart service
sudo systemctl daemon-reload
sudo systemctl restart ollama

# 4. Open firewall
sudo ufw allow 11434/tcp

# 5. Install model
ollama pull llama3.2:1b

# 6. Get server IP
curl ifconfig.me
```

### Django Side

1. **Get your Ollama server IP:**

   ```bash
   # On the Ollama server
   curl ifconfig.me
   # Example output: 192.168.1.100
   ```

2. **Update production settings:**

   Edit `dripemails/live.py`:

   ```python
   # Ollama Configuration
   OLLAMA_BASE_URL = os.environ.get('OLLAMA_BASE_URL', 'http://192.168.1.100:11434')
   OLLAMA_MODEL = os.environ.get('OLLAMA_MODEL', 'llama3.2:1b')
   ```

3. **Update local settings:**

   Edit `dripemails/settings.py`:

   ```python
   # Ollama Configuration
   OLLAMA_BASE_URL = env('OLLAMA_BASE_URL', default='http://localhost:11434')
   OLLAMA_MODEL = env('OLLAMA_MODEL', default='llama3.2:1b')
   ```

4. **Test connection:**
   ```bash
   curl http://192.168.1.100:11434/api/tags
   ```

---

## 📝 Configuration Examples

### Scenario 1: Local Development

```python
# .env
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2:1b
```

### Scenario 2: Separate Server on Same Network

```python
# Production .env
OLLAMA_BASE_URL=http://192.168.1.100:11434
OLLAMA_MODEL=llama3.2:1b
```

### Scenario 3: Cloud Server

```python
# Production .env
OLLAMA_BASE_URL=http://10.0.1.50:11434
OLLAMA_MODEL=llama3.2:1b
```

### Scenario 4: With Domain Name

```python
# Production .env
OLLAMA_BASE_URL=https://ollama.yourdomain.com
OLLAMA_MODEL=llama3.2:1b
```

---

## ✅ Testing Checklist

- [ ] Ollama service is running: `sudo systemctl status ollama`
- [ ] Model is installed: `ollama list`
- [ ] Port is open: `sudo netstat -tlnp | grep 11434`
- [ ] Firewall allows connections: `sudo ufw status`
- [ ] Can connect locally: `curl http://localhost:11434/api/tags`
- [ ] Can connect remotely: `curl http://SERVER_IP:11434/api/tags`
- [ ] Django can generate emails: Test in Django admin

---

## 🔧 Common Issues

### "Connection refused"

```bash
# Check if Ollama is running
sudo systemctl status ollama

# Check if listening on correct interface
sudo netstat -tlnp | grep 11434

# Should show: 0.0.0.0:11434 (not 127.0.0.1:11434)
```

### "Model not found"

```bash
# List installed models
ollama list

# Pull the model
ollama pull llama3.2:1b
```

### Slow responses

```bash
# Use smaller/faster model
ollama pull llama3.2:1b-instruct-q4_0

# Update .env
OLLAMA_MODEL=llama3.2:1b-instruct-q4_0
```

---

## 📊 Model Comparison

| Model            | Size  | RAM  | Speed  | Quality    |
| ---------------- | ----- | ---- | ------ | ---------- |
| llama3.2:1b      | 4.7GB | 8GB  | ⚡⚡   | ⭐⭐⭐⭐   |
| llama3.2:1b-q4_0 | 2.5GB | 4GB  | ⚡⚡⚡ | ⭐⭐⭐     |
| llama3.1:70b     | 40GB  | 64GB | ⚡     | ⭐⭐⭐⭐⭐ |

**Recommendation:** Start with `llama3.2:1b` for best balance.

---

## 🔐 Security Tips

1. **Don't expose to internet:**

   ```bash
   # Only allow from specific IP
   sudo ufw allow from YOUR_DJANGO_IP to any port 11434
   ```

2. **Use private network:** Keep Ollama on internal network

3. **Monitor usage:** Check logs regularly
   ```bash
   sudo journalctl -u ollama -f
   ```

---

## 📚 See Also

- [Full Setup Guide](ollama_remote_setup.md) - Detailed instructions
- [Ollama API Documentation](https://github.com/ollama/ollama/blob/main/docs/api.md)
- [Available Models](https://ollama.com/library)

---

## 🆘 Getting Help

1. Check Ollama status: `sudo systemctl status ollama`
2. Check logs: `sudo journalctl -u ollama -n 100`
3. Test API: `curl http://localhost:11434/api/tags`
4. See [troubleshooting guide](ollama_remote_setup.md#troubleshooting)
