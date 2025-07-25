# Supervisord Quick Reference

Quick reference for managing the DripEmails SMTP server with supervisord.

## Configuration File Location

```bash
/etc/supervisor/conf.d/dripemails-smtp.conf
```

## Basic Configuration Template

```ini
[program:dripemails-smtp]
command=/path/to/venv/bin/python /path/to/dripemails.org/manage.py run_smtp_server --host 0.0.0.0 --port 25 --save-to-db --log-to-file
directory=/path/to/dripemails.org
user=root
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

## Essential Commands

### Service Management

```bash
# Start SMTP server
sudo supervisorctl start dripemails-smtp

# Stop SMTP server
sudo supervisorctl stop dripemails-smtp

# Restart SMTP server
sudo supervisorctl restart dripemails-smtp

# Check status
sudo supervisorctl status dripemails-smtp
```

### Configuration Management

```bash
# Reload configuration
sudo supervisorctl reread

# Update configuration
sudo supervisorctl update

# Reload and restart
sudo supervisorctl reread && sudo supervisorctl update && sudo supervisorctl restart dripemails-smtp
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

### System Management

```bash
# Check all services
sudo supervisorctl status

# Start all services
sudo supervisorctl start all

# Stop all services
sudo supervisorctl stop all

# Restart all services
sudo supervisorctl restart all
```

## Debug Mode Configuration

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
priority=1000
```

## Alternative Port Configuration (No Root Required)

```ini
[program:dripemails-smtp]
command=/path/to/venv/bin/python /path/to/dripemails.org/manage.py run_smtp_server --host 0.0.0.0 --port 1025 --save-to-db --log-to-file
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

## Troubleshooting Commands

```bash
# Check if supervisord is running
sudo systemctl status supervisor

# Check SMTP server status
sudo supervisorctl status dripemails-smtp

# Check if port is listening
sudo netstat -tlnp | grep :25

# View supervisord logs
sudo tail -f /var/log/supervisor/dripemails-smtp.log

# Check configuration syntax
sudo supervisorctl reread
```

## Common Issues & Solutions

### Service Won't Start
```bash
# Check permissions (for port 25)
sudo chown root:root /path/to/dripemails.org/manage.py
sudo chmod +s /path/to/dripemails.org/manage.py

# Check if port is available
sudo netstat -tlnp | grep :25

# Check Django settings
python manage.py check --deploy
```

### Service Keeps Restarting
```bash
# Check error logs
sudo supervisorctl tail dripemails-smtp

# Test manually
sudo python manage.py run_smtp_server --debug

# Check database connection
python manage.py dbshell
```

### Permission Denied on Port 25
```bash
# Use root user in supervisord config
user=root

# Or use alternative port (no root required)
command=... --port 1025
user=www-data
```

### Port Already in Use
```bash
# Check what's using port 25
sudo netstat -tlnp | grep :25

# Stop conflicting service
sudo systemctl stop postfix
sudo systemctl stop exim4

# Or use alternative port
command=... --port 1025
```

## Environment Variables

Common environment variables you can add to the configuration:

```ini
environment=DJANGO_SETTINGS_MODULE="dripemails.live",PYTHONPATH="/path/to/dripemails.org",DJANGO_ENV="production",EMAIL_HOST="localhost",EMAIL_PORT="25"
```

## Log Rotation

Supervisord automatically handles log rotation with these settings:

```ini
stdout_logfile=/var/log/supervisor/dripemails-smtp.log
stdout_logfile_maxbytes=50MB
stdout_logfile_backups=10
```

## Web Interface (Optional)

Add to `/etc/supervisor/supervisord.conf`:

```ini
[inet_http_server]
port=127.0.0.1:9001
username=admin
password=your_secure_password
```

Access at: `http://127.0.0.1:9001`

## Health Check Script

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

## Cron Job for Auto-Restart

```bash
# Add to crontab (check every 5 minutes)
*/5 * * * * /usr/local/bin/check-smtp-server.sh || supervisorctl restart dripemails-smtp
```

## Backup Configuration

```bash
# Backup config
sudo cp /etc/supervisor/conf.d/dripemails-smtp.conf /backup/dripemails-smtp.conf.backup

# Backup logs
sudo cp /var/log/supervisor/dripemails-smtp.log /backup/dripemails-smtp.log.backup
```

## Port Considerations

- **Port 25**: Standard SMTP port, requires root privileges
- **Port 1025**: Alternative port, no root privileges required
- **Port 587**: Submission port, often used for authenticated SMTP
- **Firewall**: Ensure your chosen port is open in firewall rules 