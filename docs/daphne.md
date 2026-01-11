# Daphne ASGI Server Setup Guide for DripEmails.org

This guide explains how to install and configure Daphne (ASGI server) for DripEmails.org production deployment using Supervisor.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Installation](#installation)
3. [Configuration](#configuration)
4. [Supervisor Setup](#supervisor-setup)
5. [Nginx Configuration](#nginx-configuration)
6. [Testing](#testing)
7. [Management Commands](#management-commands)
8. [Troubleshooting](#troubleshooting)

## Prerequisites

- Python 3.12+ installed
- Virtual environment set up
- Django project configured
- PostgreSQL database configured
- Supervisor installed
- Nginx installed

## Installation

### 1. Install Daphne

```bash
# Activate your virtual environment
source /home/dripemails/web/dripemails/bin/activate
# Or if venv is elsewhere:
# source /home/dripemails/venv/bin/activate

# Install Daphne
pip install daphne

# Or install from requirements.txt if included
pip install -r requirements.txt
```

### 2. Verify Installation

```bash
# Check Daphne version
daphne --version

# Test Daphne can import your application
cd /home/dripemails/web
python -c "from docs.asgi_settings import application; print('ASGI app loaded successfully')"
```

## Configuration

### 0. Set Environment Variables for User (Optional but Recommended)

To make these environment variables available automatically when the `dripemails` user logs in or runs commands, add them to the user's shell profile:

```bash
# Switch to dripemails user
sudo su - dripemails

# Add to .profile (recommended - works for all shells)
echo 'export DJANGO_SETTINGS_MODULE=dripemails.live' >> ~/.profile
echo 'export PYTHONPATH=/home/dripemails/web' >> ~/.profile

# Or add to .bashrc (if using bash interactively)
echo 'export DJANGO_SETTINGS_MODULE=dripemails.live' >> ~/.bashrc
echo 'export PYTHONPATH=/home/dripemails/web' >> ~/.bashrc

# Reload the profile
source ~/.profile
# or
source ~/.bashrc
```

**Note**: Supervisor already sets these via the `environment` directive in the config, so this is mainly useful for:
- Manual commands when logged in as the `dripemails` user
- Running Django management commands
- Testing Daphne manually

**Alternative**: Create a dedicated environment file:

```bash
# Create environment file
sudo -u dripemails tee /home/dripemails/.dripemails_env > /dev/null << 'EOF'
export DJANGO_SETTINGS_MODULE=dripemails.live
export PYTHONPATH=/home/dripemails/web
EOF

# Source it in .profile
echo 'source ~/.dripemails_env' >> /home/dripemails/.profile
```

### 1. ASGI Application Path

You have two options for the ASGI application path:

**Option A: Using `docs.asgi_settings` (Recommended for production)**
- **Module path**: `docs.asgi_settings:application`
- **File location**: `/home/dripemails/web/docs/asgi_settings.py`
- This uses the production ASGI settings file

**Option B: Using `dripemails.asgi` (Standard Django)**
- **Module path**: `dripemails.asgi:application`
- **File location**: `/home/dripemails/web/dripemails/asgi.py`
- This uses the standard Django ASGI configuration

**Note**: The installation script uses `docs.asgi_settings:application`. If you want to use the standard `dripemails.asgi:application`, update the supervisor command accordingly.

The ASGI file should have an `application` variable that is your ASGI app.

### 2. Environment Variables

Make sure your `.env` file is configured in `/home/dripemails/web/.env`:

```bash
# Django Settings
SECRET_KEY=your-secret-key-here
DEBUG=False
DJANGO_SETTINGS_MODULE=docs.asgi_settings

# Database
DB_NAME=dripemails
DB_USER=dripemails
DB_PASSWORD=your-password
DB_HOST=localhost
DB_PORT=5432

# Email
EMAIL_HOST=localhost
EMAIL_PORT=25
EMAIL_HOST_USER=founders
EMAIL_HOST_PASSWORD=your-password
```

## Supervisor Setup

### 1. Create Supervisor Configuration

Create `/etc/supervisor/conf.d/dripemails-daphne.conf`:

```ini
[program:dripemails-daphne]
command=/home/dripemails/web/dripemails/bin/python -m daphne -b 0.0.0.0 -p 8001 dripemails.asgi:application
directory=/home/dripemails/web
user=dripemails
autostart=true
autorestart=true
startsecs=3
startretries=3
redirect_stderr=true
stdout_logfile=/home/dripemails/web/logs/daphne.log
stderr_logfile=/home/dripemails/web/logs/daphne-error.log
stdout_logfile_maxbytes=50MB
stdout_logfile_backups=10
stderr_logfile_maxbytes=50MB
stderr_logfile_backups=10
environment=DJANGO_SETTINGS_MODULE="dripemails.live",PYTHONPATH="/home/dripemails/web"
stopsignal=TERM
stopwaitsecs=10
killasgroup=true
priority=1000
```

**Alternative**: If you want to use `docs.asgi_settings` instead:
```ini
command=/home/dripemails/web/dripemails/bin/python -m daphne -b 0.0.0.0 -p 8001 docs.asgi_settings:application
environment=DJANGO_SETTINGS_MODULE="docs.asgi_settings",PYTHONPATH="/home/dripemails/web"
```

**Critical Notes:**
1. **`directory=/home/dripemails/web`** - This sets the working directory so Python can find the `dripemails` module. This is **required**!
2. **`PYTHONPATH="/home/dripemails/web"`** - This ensures Python can import modules from the project root. Also **required**!
3. Without both of these, you'll get `ModuleNotFoundError: No module named 'dripemails'`

**Note**: Update the Python path if your venv is in a different location:
- If venv is at `/home/dripemails/venv`: Change `command` to `/home/dripemails/venv/bin/daphne`
- If using system Python: Change `command` to `daphne` (must be in PATH)

### 2. Alternative: Using Virtual Environment Python Directly

If your virtual environment is at `/home/dripemails/web/dripemails`:

```ini
[program:dripemails-daphne]
command=/home/dripemails/web/dripemails/bin/daphne -b 0.0.0.0 -p 8001 docs.asgi_settings:application
directory=/home/dripemails/web
user=dripemails
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/home/dripemails/web/logs/daphne.log
environment=DJANGO_SETTINGS_MODULE="docs.asgi_settings",PYTHONPATH="/home/dripemails/web"
```

### 3. Create Logs Directory

```bash
sudo mkdir -p /home/dripemails/web/logs
sudo chown dripemails:dripemails /home/dripemails/web/logs
sudo chmod 755 /home/dripemails/web/logs
```

### 4. Load Supervisor Configuration

```bash
# Read the new configuration
sudo supervisorctl reread

# Update supervisor with new programs
sudo supervisorctl update

# Start the Daphne service
sudo supervisorctl start dripemails-daphne

# Check status
sudo supervisorctl status dripemails-daphne
```

## Nginx Configuration

### Update Nginx to Proxy to Daphne

Update your nginx configuration (`/etc/nginx/sites-available/dripemails`) to proxy to Daphne on port 8001:

```nginx
server {
    listen 80;
    server_name dripemails.org www.dripemails.org api.dripemails.org docs.dripemails.org web.dripemails.org;
    
    # ... static files configuration ...
    
    # Proxy to Daphne
    location / {
        proxy_pass http://127.0.0.1:8001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
}
```

Then reload nginx:

```bash
sudo nginx -t
sudo systemctl reload nginx
```

## Testing

### 1. Test Daphne Manually

**IMPORTANT**: You **must** run Daphne from the project root directory (`/home/dripemails/web`) so Python can find the `dripemails` module.

**Option A: Using `dripemails.asgi:application`**
```bash
# Change to project root directory (REQUIRED!)
cd /home/dripemails/web

# Set environment variables
export DJANGO_SETTINGS_MODULE=dripemails.live
export PYTHONPATH=/home/dripemails/web

# Run Daphne (must be run from /home/dripemails/web directory)
/home/dripemails/web/dripemails/bin/python -m daphne -b 0.0.0.0 -p 8001 dripemails.asgi:application
```

**Option B: Using `docs.asgi_settings:application`**
```bash
# Change to project root directory (REQUIRED!)
cd /home/dripemails/web

# Set environment variables
export DJANGO_SETTINGS_MODULE=docs.asgi_settings
export PYTHONPATH=/home/dripemails/web

# Run Daphne (must be run from /home/dripemails/web directory)
/home/dripemails/web/dripemails/bin/python -m daphne -b 0.0.0.0 -p 8001 docs.asgi_settings:application
```

**Why `cd` is required**: When Python runs `-m daphne`, it needs to be able to import `dripemails.asgi`. Python looks for modules relative to the current working directory. By running from `/home/dripemails/web`, Python can find the `dripemails` package.

Visit `http://your-server-ip:8001` to verify it's working.

### 2. Test via Supervisor

```bash
# Check if Daphne is running
sudo supervisorctl status dripemails-daphne

# View logs
sudo supervisorctl tail -f dripemails-daphne

# Check if port 8001 is listening
sudo netstat -tlnp | grep 8001
```

### 3. Test Full Stack

```bash
# Test nginx can reach Daphne
curl -I http://localhost:8001
curl -I http://dripemails.org
```

## Management Commands

### Supervisor Commands

```bash
# Start Daphne
sudo supervisorctl start dripemails-daphne

# Stop Daphne
sudo supervisorctl stop dripemails-daphne

# Restart Daphne
sudo supervisorctl restart dripemails-daphne

# View status
sudo supervisorctl status dripemails-daphne

# View logs (real-time)
sudo supervisorctl tail -f dripemails-daphne

# View last 100 lines
sudo supervisorctl tail -100 dripemails-daphne

# Clear logs
sudo supervisorctl clear dripemails-daphne
```

### Manual Daphne Commands

```bash
# IMPORTANT: Always change to project root first!
cd /home/dripemails/web

# Set environment variables
export DJANGO_SETTINGS_MODULE=dripemails.live
export PYTHONPATH=/home/dripemails/web

# Run Daphne in foreground (for debugging)
/home/dripemails/web/dripemails/bin/python -m daphne -b 0.0.0.0 -p 8001 dripemails.asgi:application

# Run with verbose logging
/home/dripemails/web/dripemails/bin/python -m daphne -b 0.0.0.0 -p 8001 -v 2 dripemails.asgi:application

# Run with specific number of threads
/home/dripemails/web/dripemails/bin/python -m daphne -b 0.0.0.0 -p 8001 --threads 4 dripemails.asgi:application
```

**Remember**: The `cd /home/dripemails/web` is **critical** - without it, Python won't be able to find the `dripemails` module!

## Troubleshooting

### Issue: Daphne won't start

**Check logs:**
```bash
sudo supervisorctl tail dripemails-daphne stderr
tail -f /home/dripemails/web/logs/daphne-error.log
```

**Common causes:**
1. **Python path incorrect**: Verify the Python executable path in supervisor config
2. **Module not found**: Check that `docs.asgi_settings` can be imported
3. **Port already in use**: Check if port 8001 is already occupied
   ```bash
   sudo netstat -tlnp | grep 8001
   sudo lsof -i :8001
   ```

### Issue: "ModuleNotFoundError: No module named 'dripemails'" or "No module named 'docs'"

**Solution:**
- **CRITICAL #1**: Ensure `directory=/home/dripemails/web` is set in supervisor config - this sets the working directory
- **CRITICAL #2**: Ensure `PYTHONPATH="/home/dripemails/web"` is set in the supervisor `environment` line
- When running manually, **always** `cd /home/dripemails/web` first before running the command
- Check that the module exists:
  - For `dripemails.asgi`: `/home/dripemails/web/dripemails/asgi.py` must exist
  - For `docs.asgi_settings`: `/home/dripemails/web/docs/asgi_settings.py` must exist
- Test manually (must be run from project root):
  ```bash
  cd /home/dripemails/web  # REQUIRED!
  export PYTHONPATH=/home/dripemails/web
  /home/dripemails/web/dripemails/bin/python -c "import dripemails; print('Module found!')"
  ```

### Issue: "Application not found"

**Solution:**
- Verify `docs/asgi_settings.py` has an `application` variable
- Test import manually:
  ```bash
  cd /home/dripemails/web
  python -c "from docs.asgi_settings import application; print(type(application))"
  ```

### Issue: Permission denied

**Solution:**
```bash
# Check file permissions
ls -la /home/dripemails/web/docs/asgi_settings.py

# Fix ownership
sudo chown -R dripemails:dripemails /home/dripemails/web

# Fix permissions
sudo chmod -R 755 /home/dripemails/web
```

### Issue: Daphne keeps restarting

**Check:**
1. View error logs: `sudo supervisorctl tail dripemails-daphne stderr`
2. Check if database is accessible
3. Verify environment variables are set correctly
4. Check if port 8001 is available

### Issue: Connection refused from Nginx

**Solution:**
1. Verify Daphne is running: `sudo supervisorctl status dripemails-daphne`
2. Check if Daphne is listening on the correct interface:
   ```bash
   sudo netstat -tlnp | grep 8001
   # Should show: 0.0.0.0:8001 or 127.0.0.1:8001
   ```
3. Check firewall rules
4. Verify nginx proxy_pass URL matches Daphne binding

## Additional Supervisor Programs

If you also need Celery workers, add these to supervisor:

### Celery Worker

```ini
[program:dripemails-celery]
command=/home/dripemails/web/dripemails/bin/celery -A dripemails worker --loglevel=info
directory=/home/dripemails/web
user=dripemails
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/home/dripemails/web/logs/celery.log
environment=DJANGO_SETTINGS_MODULE="docs.asgi_settings",PYTHONPATH="/home/dripemails/web"
```

### Celery Beat (Scheduler)

```ini
[program:dripemails-celerybeat]
command=/home/dripemails/web/dripemails/bin/celery -A dripemails beat --loglevel=info
directory=/home/dripemails/web
user=dripemails
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/home/dripemails/web/logs/celerybeat.log
environment=DJANGO_SETTINGS_MODULE="docs.asgi_settings",PYTHONPATH="/home/dripemails/web"
```

## Quick Reference

### Complete Setup Checklist

- [ ] Install Daphne: `pip install daphne`
- [ ] Verify ASGI app: `python -c "from docs.asgi_settings import application"`
- [ ] Create supervisor config: `/etc/supervisor/conf.d/dripemails-daphne.conf`
- [ ] Create logs directory: `mkdir -p /home/dripemails/web/logs`
- [ ] Load supervisor config: `sudo supervisorctl reread && sudo supervisorctl update`
- [ ] Start Daphne: `sudo supervisorctl start dripemails-daphne`
- [ ] Update nginx to proxy to `http://127.0.0.1:8001`
- [ ] Test: `curl http://localhost:8001`
- [ ] Test via nginx: `curl http://dripemails.org`

## Alternative: Using the Installation Script

If you prefer an automated setup, you can use the existing installation script:

```bash
# Make script executable
chmod +x /home/dripemails/web/docs/asgi_installation.sh

# Review and run the script (it will set up everything automatically)
# Note: Review the script first to ensure paths match your setup
```

The script will:
- Install all dependencies
- Create supervisor configurations
- Set up nginx
- Create systemd services (as alternative to supervisor)

## Next Steps

1. Set up SSL certificates with Let's Encrypt
2. Configure monitoring and logging
3. Set up backups
4. Configure firewall rules
5. Set up health checks

