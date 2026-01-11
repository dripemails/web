# Local Ollama Setup (Same Server as Django)

This guide explains how to set up Ollama on the same server as Django (recommended for production).

## ✅ Benefits of Local Setup

- **No network issues** - No connection refused errors
- **Lower latency** - Faster response times (localhost connection)
- **Simpler configuration** - No firewall rules needed
- **Better security** - Ollama only accessible from localhost

## 🚀 Quick Setup

### Step 1: Install Ollama on Web Server

**On your web server (web.dripemails.org or web1.dripemails.org):**

```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Verify installation
ollama --version
```

### Step 2: Start Ollama Service

Ollama installs as a systemd service by default. It's already configured to run on localhost:

```bash
# Start Ollama service
sudo systemctl start ollama

# Enable auto-start on boot
sudo systemctl enable ollama

# Check status
sudo systemctl status ollama

# View logs
sudo journalctl -u ollama -f
```

### Step 3: Pull the Model

```bash
# Pull the llama3.2:1b model (this will download ~5GB)
ollama pull llama3.2:1b

# Verify model is available
ollama list
# Should show: llama3.2:1b
```

### Step 4: Test Ollama

```bash
# Test that Ollama is running
curl http://localhost:11434/api/tags

# Should return JSON with your models
```

### Step 5: Configure Django

**In your `.env` file on the web server:**

```bash
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2:1b
OLLAMA_TIMEOUT=300
```

**Note:** The `dripemails/live.py` already defaults to `http://localhost:11434`, so if you set it in `.env`, it will use that. If not, it will use localhost automatically.

### Step 6: Restart Django

```bash
# Restart your Django application (gunicorn, supervisor, etc.)
sudo supervisorctl restart gunicorn
# OR
sudo systemctl restart gunicorn
```

### Step 7: Test from Django

```bash
# Test from Django shell
python manage.py shell
>>> from campaigns.ai_utils import generate_email_content
>>> result = generate_email_content("Test email", context="Testing local Ollama")
>>> print(result['subject'])
```

---

## 🔄 Alternative: Using Supervisor (Optional)

If you prefer to manage Ollama with supervisor instead of systemd:

### Step 1: Stop systemd service

```bash
sudo systemctl stop ollama
sudo systemctl disable ollama
```

### Step 2: Copy supervisor config

```bash
# Copy the supervisor config to your server
sudo cp /path/to/docs/ai/ollama_server.conf /etc/supervisor/conf.d/

# Update the config to use localhost (default - no changes needed for local)
# The config uses OLLAMA_HOST="0.0.0.0:11434" which is fine for localhost access
```

### Step 3: Reload supervisor

```bash
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start ollama-server
sudo supervisorctl status ollama-server
```

---

## 🔍 Verification Checklist

- [ ] Ollama is installed: `ollama --version`
- [ ] Ollama service is running: `sudo systemctl status ollama`
- [ ] Model is downloaded: `ollama list` shows `llama3.2:1b`
- [ ] Ollama responds: `curl http://localhost:11434/api/tags`
- [ ] `.env` file has: `OLLAMA_BASE_URL=http://localhost:11434`
- [ ] Django can connect: Test from Django shell

---

## 🛠️ Troubleshooting

### Ollama service won't start

```bash
# Check logs
sudo journalctl -u ollama -n 50

# Check if port 11434 is already in use
sudo netstat -tlnp | grep 11434

# Restart service
sudo systemctl restart ollama
```

### Model not found

```bash
# Pull the model again
ollama pull llama3.2:1b

# Verify
ollama list
```

### Django can't connect to Ollama

```bash
# Test from command line
curl http://localhost:11434/api/tags

# Check if Ollama is running
sudo systemctl status ollama

# Check Django .env file
grep OLLAMA /path/to/your/.env
```

---

## 📊 Resource Requirements

Running Ollama locally requires:

- **RAM:** 8-16GB minimum (model uses ~5GB, needs extra for processing)
- **CPU:** 4+ cores recommended
- **Storage:** 10GB+ free space (model is ~5GB)
- **Disk:** SSD recommended for faster model loading

---

## 🔒 Security Notes

Since Ollama runs on localhost only:

- ✅ No firewall rules needed
- ✅ No external access possible
- ✅ Only Django on the same server can access it
- ✅ Default configuration is secure

---

## 🚀 Performance Tips

1. **Keep model in memory:** The model loads into RAM on first use, then stays cached
2. **Monitor resources:** Use `htop` or `top` to monitor CPU/RAM usage
3. **Scale horizontally:** If needed, you can run Ollama on a separate server later by changing `OLLAMA_BASE_URL` in `.env`

