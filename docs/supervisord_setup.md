# Supervisord Setup for DripEmails SMTP Server

This guide explains how to set up and manage the DripEmails SMTP server using supervisord for production deployment.

## Overview

Supervisord is a process control system that allows you to:
- Automatically start the SMTP server on system boot
- Restart the server if it crashes
- Monitor server status and logs
- Manage multiple processes easily
- Provide a web interface for monitoring

## Prerequisites

- Python 3.12.3+
- Django project configured
- Database migrations applied
- Supervisord installed

## Installation

### 1. Install Supervisord

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install supervisor
```

**CentOS/RHEL:**
```bash
sudo yum install supervisor
# or for newer versions
sudo dnf install supervisor
```

**macOS (using Homebrew):**
```bash
brew install supervisor
```

### 2. Verify Installation

```bash
# Check supervisord version
supervisord --version

# Check if supervisord is running
sudo systemctl status supervisor
```

## Configuration

### 1. Create SMTP Server Configuration

Create a supervisord configuration file for the SMTP server:

```bash
sudo nano /etc/supervisor/conf.d/dripemails-smtp.conf
```

Add the following configuration:

```ini
[program:dripemails-smtp]
command=/path/to/your/venv/bin/python /path/to/dripemails.org/manage.py run_smtp_server --host 0.0.0.0 --port 587 --save-to-db --log-to-file
directory=/path/to/dripemails.org
user=www-data
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/supervisor/dripemails-smtp.log
stdout_logfile_maxbytes=50MB
stdout_logfile_backups=10
environment=DJANGO_SETTINGS_MODULE="dripemails.live"
stopsignal=TERM
stopwaitsecs=10
killasgroup=true
priority=1000
```

### 2. Advanced Configuration Options

For more advanced setups, you can use this extended configuration:

```ini
[program:dripemails-smtp]
command=/path/to/your/venv/bin/python /path/to/dripemails.org/manage.py run_smtp_server --host 0.0.0.0 --port 587 --save-to-db --log-to-file --webhook-url https://api.example.com/webhook
directory=/path/to/dripemails.org
user=www-data
group=www-data
autostart=true
autorestart=true
startsecs=10
startretries=3
redirect_stderr=true
stdout_logfile=/var/log/supervisor/dripemails-smtp.log
stdout_logfile_maxbytes=50MB
stdout_logfile_backups=10
stderr_logfile=/var/log/supervisor/dripemails-smtp-error.log
stderr_logfile_maxbytes=50MB
stderr_logfile_backups=10
environment=DJANGO_SETTINGS_MODULE="dripemails.live",PYTHONPATH="/path/to/dripemails.org",DJANGO_ENV="production"
stopsignal=TERM
stopwaitsecs=10
killasgroup=true
priority=1000
exitcodes=0,2
```

### 3. Configuration with Custom Settings

If you want to use a custom configuration file:

```ini
[program:dripemails-smtp]
command=/path/to/your/venv/bin/python /path/to/dripemails.org/manage.py run_smtp_server --config /path/to/dripemails.org/smtp_config.json
directory=/path/to/dripemails.org
user=www-data
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/supervisor/dripemails-smtp.log
stdout_logfile_maxbytes=50MB
stdout_logfile_backups=10
environment=DJANGO_SETTINGS_MODULE="dripemails.live"
stopsignal=TERM
stopwaitsecs=10
killasgroup=true
priority=1000
```

### 4. Debug Mode Configuration

For development or debugging, you can enable debug mode:

```ini
[program:dripemails-smtp-debug]
command=/path/to/your/venv/bin/python /path/to/dripemails.org/manage.py run_smtp_server --debug --host 0.0.0.0 --port 1025
directory=/path/to/dripemails.org
user=www-data
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/supervisor/dripemails-smtp-debug.log
stdout_logfile_maxbytes=50MB
stdout_logfile_backups=10
environment=DJANGO_SETTINGS_MODULE="dripemails.live"
stopsignal=TERM
stopwaitsecs=10
killasgroup=true
priority=1000
```

## Gunicorn Configuration

### 1. Create Gunicorn Supervisor Configuration

If you're using Gunicorn as your WSGI server, create a supervisor configuration:

```bash
sudo nano /etc/supervisor/conf.d/dripemails-gunicorn.conf
```

Add the following configuration:

```ini
[program:dripemails-gunicorn]
command=/home/dripemails/web/gunicorn.sh
directory=/home/dripemails/web
user=dripemails
autostart=true
autorestart=true
startsecs=3
startretries=3
redirect_stderr=true
stdout_logfile=/home/dripemails/web/logs/gunicorn.log
stderr_logfile=/home/dripemails/web/logs/gunicorn-error.log
stdout_logfile_maxbytes=50MB
stdout_logfile_backups=10
stderr_logfile_maxbytes=50MB
stderr_logfile_backups=10
environment=DJANGO_SETTINGS_MODULE="dripemails.live",PYTHONPATH="/home/dripemails/web",VENV="/home/dripemails/web/dripemails"
stopsignal=TERM
stopwaitsecs=10
killasgroup=true
priority=1000
```

**Note**: 
- Make sure the logs directory exists:
  ```bash
  sudo mkdir -p /home/dripemails/web/logs
  sudo chown dripemails:dripemails /home/dripemails/web/logs
  ```

- The `VENV` environment variable is optional - if not set, it defaults to `/home/dripemails/web/dripemails`. To use a different virtual environment, set it in the `environment` line:
  ```ini
  environment=VENV="/path/to/your/venv",DJANGO_SETTINGS_MODULE="dripemails.live",PYTHONPATH="/home/dripemails/web"
  ```

### 2. Make Gunicorn Script Executable

```bash
# Make the gunicorn.sh script executable
sudo chmod +x /home/dripemails/web/gunicorn.sh

# Verify it's executable
ls -l /home/dripemails/web/gunicorn.sh
```

### 3. Alternative: Direct Gunicorn Command

If you prefer to run Gunicorn directly without a shell script:

```ini
[program:dripemails-gunicorn]
command=/home/dripemails/web/dripemails/bin/gunicorn --bind 127.0.0.1:9000 --workers 12 --user dripemails --group dripemails --log-level debug dripemails.wsgi:application
directory=/home/dripemails/web
user=dripemails
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/home/dripemails/web/logs/gunicorn.log
stderr_logfile=/home/dripemails/web/logs/gunicorn-error.log
environment=DJANGO_SETTINGS_MODULE="dripemails.live",PYTHONPATH="/home/dripemails/web"
stopsignal=TERM
stopwaitsecs=10
killasgroup=true
priority=1000
```

### 4. Load and Start Gunicorn

```bash
# Reload supervisor configuration
sudo supervisorctl reread

# Update supervisor with new programs
sudo supervisorctl update

# Start Gunicorn
sudo supervisorctl start dripemails-gunicorn

# Check status
sudo supervisorctl status dripemails-gunicorn
```

## Deployment Steps

### 1. Update Configuration Paths

Replace the paths in the configuration with your actual paths:

```bash
# Find your project path
pwd
# Output: /home/user/workspace/dripemails.org

# Find your virtual environment path
which python
# Output: /home/user/venv/bin/python
```

Update the configuration file accordingly:

```ini
command=/home/user/venv/bin/python /home/user/workspace/dripemails.org/manage.py run_smtp_server --host 0.0.0.0 --port 587 --save-to-db --log-to-file
directory=/home/user/workspace/dripemails.org
```

### 2. Create Log Directory

```bash
sudo mkdir -p /var/log/supervisor
sudo chown www-data:www-data /var/log/supervisor
```

### 3. Reload Supervisord Configuration

```bash
# Reload the configuration
sudo supervisorctl reread

# Update the configuration
sudo supervisorctl update

# Check status
sudo supervisorctl status
```

### 4. Start the SMTP Server

```bash
# Start the service
sudo supervisorctl start dripemails-smtp

# Check if it's running
sudo supervisorctl status dripemails-smtp
```

## Management Commands

### Basic Commands

**SMTP Server:**
```bash
# Start the service
sudo supervisorctl start dripemails-smtp

# Stop the service
sudo supervisorctl stop dripemails-smtp

# Restart the service
sudo supervisorctl restart dripemails-smtp

# Check status
sudo supervisorctl status dripemails-smtp

# View logs
sudo supervisorctl tail dripemails-smtp
```

**Gunicorn:**
```bash
# Start Gunicorn
sudo supervisorctl start dripemails-gunicorn

# Stop Gunicorn
sudo supervisorctl stop dripemails-gunicorn

# Restart Gunicorn
sudo supervisorctl restart dripemails-gunicorn

# Check status
sudo supervisorctl status dripemails-gunicorn

# View logs
sudo supervisorctl tail dripemails-gunicorn
```

### Advanced Commands

```bash
# Reload configuration without restarting
sudo supervisorctl reread
sudo supervisorctl update

# Stop all services
sudo supervisorctl stop all

# Start all services
sudo supervisorctl start all

# Restart all services
sudo supervisorctl restart all

# Show all processes
sudo supervisorctl status
```

### Log Management

```bash
# View real-time logs
sudo supervisorctl tail -f dripemails-smtp

# View last 100 lines
sudo supervisorctl tail -100 dripemails-smtp

# Clear logs
sudo supervisorctl clear dripemails-smtp
```

## Monitoring and Troubleshooting

### 1. Check Service Status

```bash
# Check if supervisord is running
sudo systemctl status supervisor

# Check SMTP server status
sudo supervisorctl status dripemails-smtp

# Check if port is listening
sudo netstat -tlnp | grep :587
```

### 2. View Logs

```bash
# Supervisord logs
sudo tail -f /var/log/supervisor/dripemails-smtp.log

# Supervisord error logs
sudo tail -f /var/log/supervisor/dripemails-smtp-error.log

# System logs
sudo journalctl -u supervisor -f
```

### 3. Common Issues and Solutions

**Service won't start:**
```bash
# Check configuration syntax
sudo supervisorctl reread

# Check permissions
sudo chown -R www-data:www-data /path/to/dripemails.org

# Check if port is available
sudo netstat -tlnp | grep :587
```

**Service keeps restarting:**
```bash
# Check error logs
sudo supervisorctl tail dripemails-smtp

# Check Django settings
python manage.py check --deploy

# Test SMTP server manually
python manage.py run_smtp_server --debug
```

**Permission denied:**
```bash
# Fix ownership
sudo chown -R www-data:www-data /path/to/dripemails.org

# Fix permissions
sudo chmod -R 755 /path/to/dripemails.org

# Ensure log directory permissions
sudo chown www-data:www-data /var/log/supervisor
```

## Web Interface (Optional)

### 1. Enable Web Interface

Edit the main supervisord configuration:

```bash
sudo nano /etc/supervisor/supervisord.conf
```

Add or uncomment the web interface section:

```ini
[inet_http_server]
port=127.0.0.1:9001
username=admin
password=your_secure_password
```

### 2. Restart Supervisord

```bash
sudo systemctl restart supervisor
```

### 3. Access Web Interface

Open your browser and go to: `http://127.0.0.1:9001`

## Running Multiple Services

### Group Configuration

You can group related services together for easier management:

```ini
[group:dripemails]
programs=dripemails-gunicorn,dripemails-smtp
priority=999
```

Then manage the entire group:

```bash
# Start all services in the group
sudo supervisorctl start dripemails:*

# Stop all services in the group
sudo supervisorctl stop dripemails:*

# Restart all services in the group
sudo supervisorctl restart dripemails:*

# Check status of all services
sudo supervisorctl status dripemails:*
```

## Multiple SMTP Servers

If you need to run multiple SMTP servers (e.g., different ports or configurations):

### 1. Primary SMTP Server

```ini
[program:dripemails-smtp-primary]
command=/path/to/venv/bin/python /path/to/dripemails.org/manage.py run_smtp_server --host 0.0.0.0 --port 587 --save-to-db
directory=/path/to/dripemails.org
user=www-data
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/supervisor/dripemails-smtp-primary.log
environment=DJANGO_SETTINGS_MODULE="dripemails.live"
stopsignal=TERM
stopwaitsecs=10
killasgroup=true
priority=1000
```

### 2. Secondary SMTP Server (Debug/Testing)

```ini
[program:dripemails-smtp-debug]
command=/path/to/venv/bin/python /path/to/dripemails.org/manage.py run_smtp_server --debug --host 0.0.0.0 --port 1025
directory=/path/to/dripemails.org
user=www-data
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/supervisor/dripemails-smtp-debug.log
environment=DJANGO_SETTINGS_MODULE="dripemails.live"
stopsignal=TERM
stopwaitsecs=10
killasgroup=true
priority=1001
```

### 3. Group Configuration

You can also group related services:

```ini
[group:dripemails]
programs=dripemails-smtp-primary,dripemails-smtp-debug
priority=999
```

## Security Considerations

### 1. File Permissions

```bash
# Secure the configuration file
sudo chmod 600 /etc/supervisor/conf.d/dripemails-smtp.conf

# Secure log files
sudo chmod 640 /var/log/supervisor/dripemails-smtp.log
```

### 2. Firewall Configuration

```bash
# Allow SMTP traffic
sudo ufw allow 587/tcp

# Allow supervisord web interface (if enabled)
sudo ufw allow from 127.0.0.1 to any port 9001
```

### 3. User Permissions

```bash
# Create dedicated user for SMTP server
sudo useradd -r -s /bin/false dripemails-smtp

# Update configuration to use dedicated user
# Change user=www-data to user=dripemails-smtp
```

## Backup and Recovery

### 1. Backup Configuration

```bash
# Backup supervisord configuration
sudo cp /etc/supervisor/conf.d/dripemails-smtp.conf /backup/dripemails-smtp.conf.backup

# Backup logs
sudo cp /var/log/supervisor/dripemails-smtp.log /backup/dripemails-smtp.log.backup
```

### 2. Recovery Procedure

```bash
# Restore configuration
sudo cp /backup/dripemails-smtp.conf.backup /etc/supervisor/conf.d/dripemails-smtp.conf

# Reload configuration
sudo supervisorctl reread
sudo supervisorctl update

# Restart service
sudo supervisorctl restart dripemails-smtp
```

## Integration with Monitoring

### 1. Health Check Script

Create a health check script:

```bash
#!/bin/bash
# /usr/local/bin/check-smtp-server.sh

if supervisorctl status dripemails-smtp | grep -q "RUNNING"; then
    echo "SMTP server is running"
    exit 0
else
    echo "SMTP server is not running"
    exit 1
fi
```

### 2. Cron Job for Monitoring

```bash
# Add to crontab
*/5 * * * * /usr/local/bin/check-smtp-server.sh || supervisorctl restart dripemails-smtp
```

## Troubleshooting Checklist

- [ ] Supervisord is installed and running
- [ ] Configuration file syntax is correct
- [ ] Paths in configuration are correct
- [ ] User has proper permissions
- [ ] Port 587 is not in use by another service
- [ ] Django settings are correct
- [ ] Database is accessible
- [ ] Log directory exists and is writable
- [ ] Virtual environment is activated
- [ ] All dependencies are installed

## Support

For issues with supervisord setup:

1. Check supervisord logs: `sudo journalctl -u supervisor`
2. Check SMTP server logs: `sudo supervisorctl tail dripemails-smtp`
3. Verify configuration: `sudo supervisorctl reread`
4. Test manually: `python manage.py run_smtp_server --debug` 