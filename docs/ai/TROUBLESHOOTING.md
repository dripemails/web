# Ollama Troubleshooting Guide

Common issues and solutions when setting up Ollama with DripEmails.

## 🔴 Connection Refused Error

**Error Message:**
```
HTTPConnectionPool(host='10.124.0.3', port=11434): Max retries exceeded with url: /api/generate 
(Caused by NewConnectionError: Failed to establish a new connection: [Errno 111] Connection refused'))
```

### Step 1: Check if Ollama is Running

**If using Supervisor:**

```bash
# Check supervisor status
sudo supervisorctl status ollama-server

# If not running, start it
sudo supervisorctl start ollama-server

# Check logs
sudo tail -f /var/log/supervisor/ollama-server.log
sudo tail -f /var/log/supervisor/ollama-server-error.log
```

**If using systemd:**

```bash
# Check service status
sudo systemctl status ollama

# If not running, start it
sudo systemctl start ollama

# Check logs
sudo journalctl -u ollama -f
```

**If running manually:**

```bash
# Check if ollama process is running
ps aux | grep ollama

# If not running, start it
OLLAMA_HOST=0.0.0.0:11434 ollama serve
```

### Step 2: Verify Ollama is Listening on the Correct Port

```bash
# Check what's listening on port 11434
sudo netstat -tlnp | grep 11434
# OR
sudo ss -tlnp | grep 11434

# Expected output should show:
# tcp  0  0  0.0.0.0:11434  0.0.0.0:*  LISTEN  <PID>/ollama
```

**If it shows `127.0.0.1:11434` instead of `0.0.0.0:11434`:**
- Ollama is only listening on localhost (not accessible remotely)
- Fix by setting `OLLAMA_HOST=0.0.0.0:11434` in your supervisor/systemd config

### Step 3: Test Connection from Django Server

**From the Django server (where your app runs):**

```bash
# Test basic connectivity
curl http://10.124.0.3:11434/api/tags

# Test with timeout
curl --max-time 10 http://10.124.0.3:11434/api/tags

# Test from Python
python3 -c "import requests; print(requests.get('http://10.124.0.3:11434/api/tags', timeout=5).json())"
```

**Expected Response:**
```json
{"models":[{"name":"llama3.2:1b","modified_at":"...","size":...}]}
```

**If curl fails:**
- The server is not reachable from Django server
- Check network connectivity: `ping 10.124.0.3`
- Check firewall rules (see Step 4)

### Step 4: Check Firewall Rules

**On the Ollama server:**

```bash
# Ubuntu/Debian (UFW)
sudo ufw status
sudo ufw allow 11434/tcp
sudo ufw reload

# CentOS/RHEL (firewalld)
sudo firewall-cmd --list-ports
sudo firewall-cmd --permanent --add-port=11434/tcp
sudo firewall-cmd --reload

# Check iptables
sudo iptables -L -n | grep 11434
```

**If Django and Ollama are on the same server:**
- Firewall should allow localhost connections (usually already allowed)
- Use `localhost` or `127.0.0.1` in your `.env` instead of the IP address

### Step 5: Verify Environment Variables

**On Django server, check your `.env` file:**

```bash
# Check if variables are set
grep OLLAMA /path/to/your/.env

# Should show:
# OLLAMA_BASE_URL=http://10.124.0.3:11434
# OLLAMA_MODEL=llama3.2:1b
# OLLAMA_TIMEOUT=300
```

**Important Notes:**
- If Django and Ollama are on the **same server**, use: `OLLAMA_BASE_URL=http://localhost:11434`
- If Django and Ollama are on **different servers**, use: `OLLAMA_BASE_URL=http://OLLAMA_SERVER_IP:11434`
- Do NOT use `0.0.0.0` in `OLLAMA_BASE_URL` - that's only for binding on the Ollama server

### Step 6: Restart Services

**If you've made changes:**

```bash
# Restart Ollama (Supervisor)
sudo supervisorctl restart ollama-server

# OR Restart Ollama (systemd)
sudo systemctl restart ollama

# Restart Django (if using systemd/gunicorn)
sudo systemctl restart gunicorn
# OR
sudo supervisorctl restart gunicorn

# If using Django runserver, just restart it
```

---

## 🟡 Timeout Errors

**Error Message:**
```
Read timed out. (read timeout=120)
```

### Solutions:

1. **Increase timeout in `.env`:**
   ```bash
   OLLAMA_TIMEOUT=600  # 10 minutes
   ```

2. **Check Ollama server resources:**
   ```bash
   # Check CPU usage
   top
   
   # Check memory
   free -h
   
   # Check disk space
   df -h
   ```

3. **Verify model is downloaded:**
   ```bash
   ollama list
   # Should show llama3.2:1b
   ```

4. **Test model generation manually:**
   ```bash
   ollama run llama3.2:1b "Test prompt"
   ```

---

## 🟢 Model Not Found

**Error Message:**
```
model 'llama3.2:1b' not found
```

### Solution:

```bash
# Pull the model
ollama pull llama3.2:1b

# Verify it's available
ollama list

# Should show:
# llama3.2:1b  <size>  <date>
```

---

## 🔵 Supervisor Configuration Issues

### Check Supervisor Config

```bash
# Check if config file exists
ls -la /etc/supervisor/conf.d/ollama-server.conf

# Validate config syntax
sudo supervisorctl reread
# Should show: ollama-server: available

# If config has errors, check syntax
sudo supervisord -c /etc/supervisor/supervisord.conf
```

### Fix Supervisor Config

Edit `/etc/supervisor/conf.d/ollama-server.conf`:

```ini
[program:ollama-server]
command=ollama serve
directory=/usr/local/bin
user=root
autostart=true
autorestart=true
environment=OLLAMA_HOST="0.0.0.0:11434",OLLAMA_MODEL="llama3.2:1b"
redirect_stderr=true
stdout_logfile=/var/log/supervisor/ollama-server.log
stderr_logfile=/var/log/supervisor/ollama-server-error.log
```

Then:

```bash
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start ollama-server
```

---

## 🔍 Quick Diagnostic Commands

Run these on your Ollama server to diagnose issues:

```bash
# 1. Check if Ollama is installed
which ollama
ollama --version

# 2. Check if service is running
sudo systemctl status ollama
# OR
sudo supervisorctl status ollama-server

# 3. Check if port is listening
sudo netstat -tlnp | grep 11434

# 4. Check firewall
sudo ufw status | grep 11434
# OR
sudo firewall-cmd --list-ports | grep 11434

# 5. Test local connection
curl http://localhost:11434/api/tags

# 6. Test remote connection (from Django server)
curl http://OLLAMA_SERVER_IP:11434/api/tags

# 7. Check logs
sudo tail -50 /var/log/supervisor/ollama-server.log
# OR
sudo journalctl -u ollama -n 50
```

---

## 📋 Common Configuration Mistakes

### ❌ Wrong: Using 0.0.0.0 in Django .env
```bash
OLLAMA_BASE_URL=http://0.0.0.0:11434  # WRONG - 0.0.0.0 is for binding, not connecting
```

### ✅ Correct: Using actual IP or localhost
```bash
# Same server
OLLAMA_BASE_URL=http://localhost:11434

# Different server
OLLAMA_BASE_URL=http://10.124.0.3:11434
```

### ❌ Wrong: Not setting OLLAMA_HOST on Ollama server
```bash
# Ollama only listens on localhost by default
ollama serve  # Only accessible from same machine
```

### ✅ Correct: Binding to all interfaces
```bash
# In supervisor/systemd config
OLLAMA_HOST=0.0.0.0:11434

# Or when running manually
OLLAMA_HOST=0.0.0.0:11434 ollama serve
```

---

## 🆘 Still Having Issues?

1. **Check Django logs:**
   ```bash
   # Wherever your Django logs are
   tail -f /var/log/django/error.log
   ```

2. **Enable debug logging in Django:**
   In `dripemails/live.py`, temporarily add:
   ```python
   LOGGING = {
       'version': 1,
       'handlers': {
           'console': {
               'class': 'logging.StreamHandler',
           },
       },
       'loggers': {
           'campaigns.ai_utils': {
               'handlers': ['console'],
               'level': 'DEBUG',
           },
       },
   }
   ```

3. **Test from Django shell:**
   ```bash
   python manage.py shell
   >>> from campaigns.ai_utils import generate_email_content
   >>> result = generate_email_content("Test", context="Testing")
   ```

4. **Check network connectivity:**
   ```bash
   # From Django server to Ollama server
   ping OLLAMA_SERVER_IP
   telnet OLLAMA_SERVER_IP 11434
   ```

