# AI Email Generation Documentation

This directory contains documentation for setting up and using AI-powered email generation in DripEmails using Ollama.

## 📚 Documentation Files

### [Quick Start Guide](quick_start.md)

**Start here!** Quick 5-minute setup guide for getting Ollama running locally or on a remote server.

- ✅ Simple step-by-step instructions
- ✅ Common configuration examples
- ✅ Quick troubleshooting
- ✅ Model comparison table

**Use this if:** You want to get up and running quickly.

---

### [Remote Server Setup Guide](ollama_remote_setup.md)

**Comprehensive guide** for production deployments with detailed instructions.

- ✅ Complete installation instructions for all platforms
- ✅ Network configuration and security
- ✅ Django integration details
- ✅ Performance optimization
- ✅ In-depth troubleshooting

**Use this if:** You need detailed production setup instructions or are troubleshooting issues.

---

## 🎯 Quick Reference

### Local Development Setup

```bash
# 1. Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# 2. Start Ollama
ollama serve

# 3. Install model
ollama pull llama3.2:1b

# 4. Add to .env
echo "OLLAMA_BASE_URL=http://localhost:11434" >> .env
echo "OLLAMA_MODEL=llama3.2:1b" >> .env
```

### Remote Server Setup

```bash
# On remote server
sudo systemctl edit ollama.service
# Add: Environment="OLLAMA_HOST=0.0.0.0:11434"
sudo systemctl daemon-reload
sudo systemctl restart ollama
sudo ufw allow 11434/tcp

# Get IP
curl ifconfig.me
```

```python
# In dripemails/live.py
OLLAMA_BASE_URL = os.environ.get('OLLAMA_BASE_URL', 'http://YOUR_SERVER_IP:11434')
```

---

## 🔧 Configuration Files

The AI generation system uses Django settings for configuration:

### Development (`dripemails/settings.py`)

```python
OLLAMA_BASE_URL = env('OLLAMA_BASE_URL', default='http://localhost:11434')
OLLAMA_MODEL = env('OLLAMA_MODEL', default='llama3.2:1b')
```

### Production (`dripemails/live.py`)

```python
OLLAMA_BASE_URL = os.environ.get('OLLAMA_BASE_URL', 'http://localhost:11434')
OLLAMA_MODEL = os.environ.get('OLLAMA_MODEL', 'llama3.2:1b')
```

### AI Utilities (`campaigns/ai_utils.py`)

Automatically uses Django settings or falls back to environment variables.

---

## 🌐 Configuration Examples

### Same Machine (Development)

```bash
# .env
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2:1b
```

### Local Network Server

```bash
# .env
OLLAMA_BASE_URL=http://192.168.1.100:11434
OLLAMA_MODEL=llama3.2:1b
```

### Remote Cloud Server

```bash
# .env
OLLAMA_BASE_URL=http://10.0.1.50:11434
OLLAMA_MODEL=llama3.2:1b
```

### With Domain Name & SSL

```bash
# .env
OLLAMA_BASE_URL=https://ollama.yourdomain.com
OLLAMA_MODEL=llama3.2:1b
```

---

## 🧪 Testing

### Test Ollama Connection

```bash
curl http://YOUR_OLLAMA_URL:11434/api/tags
```

### Test from Django

```python
python manage.py shell

from campaigns.ai_utils import generate_email_content
result = generate_email_content(
    subject="Product Launch",
    context="New tablet release"
)
print(result)
```

---

## 📊 Model Selection

| Model            | Size  | RAM Needed | Speed  | Quality   | Best For        |
| ---------------- | ----- | ---------- | ------ | --------- | --------------- |
| llama3.2:1b      | 4.7GB | 8GB        | Medium | High      | **Recommended** |
| llama3.2:1b-q4_0 | 2.5GB | 4GB        | Fast   | Good      | High volume     |
| llama3.1:70b     | 40GB  | 64GB       | Slow   | Excellent | Premium         |

---

## 🔐 Security Considerations

### For Production:

1. **Use Private Network:** Keep Ollama on internal network

   ```bash
   sudo ufw allow from YOUR_DJANGO_SERVER_IP to any port 11434
   ```

2. **Use VPN:** Connect servers via VPN tunnel

3. **Reverse Proxy:** Add Nginx with SSL for HTTPS

4. **Monitor Usage:** Enable logging
   ```python
   logger.info(f"AI generation request: {subject}")
   ```

---

## 🚀 Performance Tips

### 1. Use Caching

Cache generated emails to reduce repeated API calls.

### 2. Async Processing

Use Celery tasks for non-blocking email generation.

### 3. Model Selection

- Development: `llama3.2:1b-q4_0` (faster)
- Production: `llama3.2:1b` (better quality)

### 4. Resource Allocation

- Minimum: 8GB RAM
- Recommended: 16GB RAM
- CPU: 4+ cores

---

## 📝 Environment Variables

| Variable          | Default                  | Description       |
| ----------------- | ------------------------ | ----------------- |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama server URL |
| `OLLAMA_MODEL`    | `llama3.2:1b`            | Model to use      |

**Set in:**

- `.env` file (both local and production)
- System environment variables
- Django settings files

---

## 🆘 Troubleshooting

### Quick Checks

```bash
# Is Ollama running?
sudo systemctl status ollama

# Is model installed?
ollama list

# Can you connect?
curl http://localhost:11434/api/tags

# Check logs
sudo journalctl -u ollama -n 50
```

### Common Issues

**Connection refused:** Ollama not running or firewall blocking
**Model not found:** Run `ollama pull llama3.2:1b`
**Slow responses:** Use smaller model or add more RAM
**Timeout errors:** Increase timeout in `ai_utils.py`

See [Remote Setup Guide](ollama_remote_setup.md#troubleshooting) for detailed solutions.

---

## 📚 Additional Resources

- **Ollama GitHub:** https://github.com/ollama/ollama
- **API Documentation:** https://github.com/ollama/ollama/blob/main/docs/api.md
- **Model Library:** https://ollama.com/library
- **Discord Community:** https://discord.gg/ollama

---

## 🔄 Migration from Hugging Face

The system has been migrated from Hugging Face to Ollama:

### Benefits:

- ✅ No API key required
- ✅ Faster responses (local processing)
- ✅ More privacy (data stays on your server)
- ✅ No rate limits
- ✅ Offline capability

### Changes:

- Removed `HUGGINGFACE_API_KEY` requirement
- Added `OLLAMA_BASE_URL` and `OLLAMA_MODEL` settings
- Updated `campaigns/ai_utils.py` to use Ollama API

---

## 💡 Tips

1. **Start Local:** Test with Ollama on localhost first
2. **Monitor Resources:** Watch RAM and CPU usage
3. **Use Fast Models:** For development, use quantized models (q4_0)
4. **Scale Gradually:** Start with one server, scale as needed
5. **Check Logs:** Regular log monitoring helps catch issues early

---

## 📞 Support

For issues or questions:

1. Check [Quick Start](quick_start.md) for common solutions
2. Review [Remote Setup Guide](ollama_remote_setup.md#troubleshooting)
3. Check Ollama server logs
4. Test with `curl` commands
5. Verify Django settings are loaded correctly

---

**Last Updated:** January 4, 2026  
**Version:** 1.0  
**Tested with:** Ollama 0.1.x, llama3.2:1b, Django 4.x
