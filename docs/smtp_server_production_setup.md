# SMTP Server Production Setup Guide

This guide covers deploying the DripEmails SMTP server in production with proper user management and security.

## 🏗️ **Production Architecture**

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Django App    │    │   SMTP Server   │    │   Database      │
│   (dripemails)  │◄──►│   (dripemails)  │    │   (MySQL/PostgreSQL)
│   Port 8000     │    │   Port 25/1025  │    │   Port 3306     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 👤 **User Management Options**

### **Option 1: Same User (Recommended)**
Run both Django and SMTP server as the `dripemails` user.

**Benefits:**
- ✅ Consistent permissions and environment
- ✅ Shared configuration files
- ✅ Easier debugging and maintenance
- ✅ Better security isolation

**Setup:**
```bash
# Create dripemails user if not exists
sudo useradd -r -s /bin/bash -d /home/dripemails dripemails

# Set up project directory
sudo mkdir -p /home/dripemails/web
sudo chown dripemails:dripemails /home/dripemails/web

# Deploy your code
sudo -u dripemails git clone https://github.com/your-repo/dripemails.org.git /home/dripemails/web

# Run SMTP server as dripemails user
sudo -u dripemails python3 /home/dripemails/web/manage.py run_smtp_server --port 1025
```

### **Option 2: Different Users**
Run Django as `dripemails` and SMTP as `root` or dedicated user.

**Benefits:**
- ✅ Can bind directly to port 25
- ✅ Process isolation

**Drawbacks:**
- ❌ Permission complexity
- ❌ Security concerns with root
- ❌ Configuration sharing issues

## 🔧 **Production Deployment Methods**

### **Method 1: Systemd Service (Recommended)**

Create `/etc/systemd/system/dripemails-smtp.service`:

```ini
[Unit]
Description=DripEmails SMTP Server
After=network.target
Wants=network.target

[Service]
Type=simple
User=dripemails
Group=dripemails
WorkingDirectory=/home/dripemails/web
Environment=PATH=/home/dripemails/venv/bin
ExecStart=/home/dripemails/venv/bin/python manage.py run_smtp_server --port 1025
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

**Enable and start:**
```bash
sudo systemctl daemon-reload
sudo systemctl enable dripemails-smtp
sudo systemctl start dripemails-smtp
sudo systemctl status dripemails-smtp
```

### **Method 2: Supervisord**

Create `/etc/supervisor/conf.d/dripemails-smtp.conf`:

```ini
[program:dripemails-smtp]
command=/home/dripemails/venv/bin/python manage.py run_smtp_server --port 1025
directory=/home/dripemails/web
user=dripemails
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/dripemails-smtp.log
environment=PATH="/home/dripemails/venv/bin"
```

**Enable:**
```bash
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start dripemails-smtp
```

### **Method 3: Docker (Alternative)**

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 1025

CMD ["python", "manage.py", "run_smtp_server", "--port", "1025"]
```

## 🌐 **Port 25 Configuration**

### **Option A: Port Forwarding (Recommended)**
```bash
# Forward port 25 to 1025
sudo iptables -t nat -A PREROUTING -p tcp --dport 25 -j REDIRECT --to-port 1025

# Make permanent
sudo iptables-save > /etc/iptables/rules.v4
```

### **Option B: Run as Root (Not Recommended)**
```bash
# Only if you must use port 25 directly
sudo python3 manage.py run_smtp_server --port 25
```

### **Option C: Use Non-Standard Port**
```bash
# Use port 1025 and configure clients accordingly
python3 manage.py run_smtp_server --port 1025
```

## 🔒 **Security Considerations**

### **File Permissions:**
```bash
# Secure the dripemails directory
sudo chown -R dripemails:dripemails /home/dripemails/web
sudo chmod -R 755 /home/dripemails/web
sudo chmod 600 /home/dripemails/web/settings.py
```

### **Firewall Configuration:**
```bash
# Allow SMTP traffic
sudo ufw allow 25/tcp
sudo ufw allow 1025/tcp  # If using non-standard port
```

### **SELinux (if applicable):**
```bash
# Allow Python to bind to network ports
sudo setsebool -P httpd_can_network_connect 1
```

## 📊 **Monitoring and Logging**

### **Log Configuration:**
```python
# In your Django settings
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'smtp_file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/var/log/dripemails-smtp.log',
            'maxBytes': 1024*1024*10,  # 10MB
            'backupCount': 5,
        },
    },
    'loggers': {
        'core.smtp_server': {
            'handlers': ['smtp_file'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}
```

### **Health Checks:**
```bash
# Check if SMTP server is running
sudo systemctl status dripemails-smtp

# Check logs
sudo journalctl -u dripemails-smtp -f

# Test SMTP connection
telnet localhost 25
```

## 🔄 **Integration with Django**

### **Django Settings:**
```python
# settings.py or live.py
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'localhost'
EMAIL_PORT = 1025  # Use the port your SMTP server runs on
EMAIL_USE_TLS = False
EMAIL_USE_SSL = False
EMAIL_HOST_USER = 'founders'
EMAIL_HOST_PASSWORD = 'your_password'
DEFAULT_FROM_EMAIL = 'founders@dripemails.org'
```

### **Celery Integration:**
```python
# tasks.py
from django.core.mail import send_mail

@shared_task
def send_email_task(subject, message, from_email, recipient_list):
    return send_mail(subject, message, from_email, recipient_list)
```

## 🚨 **Troubleshooting**

### **Common Issues:**

1. **Permission Denied:**
   ```bash
   # Check file ownership
   sudo chown -R dripemails:dripemails /home/dripemails/web
   ```

2. **Port Already in Use:**
   ```bash
   # Check what's using the port
   sudo netstat -tlnp | grep :25
   sudo netstat -tlnp | grep :1025
   ```

3. **Service Won't Start:**
   ```bash
   # Check logs
   sudo journalctl -u dripemails-smtp -n 50
   ```

4. **Django Can't Connect:**
   ```bash
   # Test SMTP server manually
   python3 manage.py shell
   >>> from django.core.mail import send_mail
   >>> send_mail('Test', 'Test message', 'from@example.com', ['to@example.com'])
   ```

## 📋 **Deployment Checklist**

- [ ] Create `dripemails` user
- [ ] Set up project directory with correct permissions
- [ ] Install Python dependencies
- [ ] Configure Django settings
- [ ] Set up systemd service or supervisord
- [ ] Configure port forwarding (if using port 25)
- [ ] Set up logging
- [ ] Configure firewall
- [ ] Test SMTP functionality
- [ ] Set up monitoring
- [ ] Document configuration

## 🎯 **Recommended Final Setup**

```bash
# 1. User and directory setup
sudo useradd -r -s /bin/bash -d /home/dripemails dripemails
sudo mkdir -p /home/dripemails/web
sudo chown dripemails:dripemails /home/dripemails/web

# 2. Deploy code
sudo -u dripemails git clone https://github.com/your-repo/dripemails.org.git /home/dripemails/web

# 3. Install dependencies
sudo -u dripemails python3 -m venv /home/dripemails/venv
sudo -u dripemails /home/dripemails/venv/bin/pip install -r /home/dripemails/web/requirements.txt

# 4. Set up systemd service
sudo cp /home/dripemails/web/docs/dripemails-smtp.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable dripemails-smtp
sudo systemctl start dripemails-smtp

# 5. Configure port forwarding
sudo iptables -t nat -A PREROUTING -p tcp --dport 25 -j REDIRECT --to-port 1025
sudo iptables-save > /etc/iptables/rules.v4

# 6. Test
sudo systemctl status dripemails-smtp
telnet localhost 25
```

This setup provides a secure, maintainable, and scalable production environment for your SMTP server. 
