# Logrotate Configuration for DripEmails.org

This directory contains logrotate configuration files to automatically rotate and manage log files created by the DripEmails project.

## Files

- `dripemails.conf` - Main logrotate configuration for all DripEmails log files

## Installation

To use this logrotate configuration:

1. **Copy the configuration to logrotate.d:**
   ```bash
   sudo cp docs/logrotate/dripemails.conf /etc/logrotate.d/dripemails
   ```

2. **Set proper permissions:**
   ```bash
   sudo chmod 644 /etc/logrotate.d/dripemails
   sudo chown root:root /etc/logrotate.d/dripemails
   ```

3. **Test the configuration:**
   ```bash
   sudo logrotate -d /etc/logrotate.d/dripemails
   ```
   (The `-d` flag runs in debug/dry-run mode)

4. **Force a test rotation:**
   ```bash
   sudo logrotate -f /etc/logrotate.d/dripemails
   ```

## Log Files Covered

The configuration rotates the following log files:

### Application Logs
- `/home/dripemails/web/logs/*.log` - All Django and application logs
  - `django.log` - Django application logs
  - `spf_check.log` - SPF record checking logs
  - `daphne.log`, `daphne-error.log` - Daphne ASGI server logs
  - `celery.log`, `celerybeat.log` - Celery worker and beat logs
  - `gunicorn.log`, `gunicorn-error.log` - Gunicorn WSGI server logs

### Service Logs (Supervisor)
- `/var/log/gmail_processor.log`, `/var/log/gmail_processor_error.log` - Gmail email processor logs
- `/var/log/imap_crawler.log`, `/var/log/imap_crawler_error.log` - IMAP email crawler logs
- `/var/log/dripemails.log`, `/var/log/dripemails-error.log` - General cron job logs
- `/var/log/supervisor/dripemails*.log` - Supervisor service logs
- `/var/log/supervisor/ollama-server.log`, `/var/log/supervisor/ollama-server-error.log` - Ollama AI server logs (if used)

### Web Server Logs
- `/var/log/nginx/dripemails-access.log`, `/var/log/nginx/dripemails-error.log` - Nginx access and error logs
- `/var/log/uwsgi/dripemails.log` - UWSGI server logs (if used)

## Rotation Settings

- **Frequency**: Daily rotation
- **Retention**: 
  - Application logs: 14 days
  - Service logs: 7 days
  - Nginx logs: 30 days
- **Compression**: Enabled (with delaycompress - compresses previous day's log)
- **Permissions**: Created with appropriate user/group (dripemails:dripemails for app logs, www-data:www-data for nginx)

## Customization

To customize rotation settings, edit `/etc/logrotate.d/dripemails` after installation:

### Common Options:

- `daily` - Rotate daily (other options: `weekly`, `monthly`)
- `rotate N` - Keep N rotated log files
- `compress` - Compress rotated logs
- `delaycompress` - Don't compress the most recent rotated log
- `notifempty` - Don't rotate if log is empty
- `missingok` - Don't error if log file is missing
- `create MODE USER GROUP` - Set permissions for new log files
- `postrotate/endscript` - Commands to run after rotation (e.g., restart services)

### Example: Change retention to 30 days

```bash
/home/dripemails/web/logs/*.log {
    daily
    rotate 30  # Changed from 14 to 30
    # ... rest of config
}
```

## Verification

To verify logrotate is working:

1. **Check logrotate status:**
   ```bash
   sudo logrotate -d /etc/logrotate.d/dripemails
   ```

2. **View logrotate logs:**
   ```bash
   sudo cat /var/log/logrotate.status
   ```

3. **Check rotated logs:**
   ```bash
   ls -lah /home/dripemails/web/logs/
   ls -lah /var/log/gmail_processor.log*
   ls -lah /var/log/imap_crawler.log*
   ```

## Troubleshooting

### Logs not rotating

1. **Check logrotate is running:**
   ```bash
   systemctl status logrotate.timer  # On systemd systems
   ```

2. **Check logrotate configuration syntax:**
   ```bash
   sudo logrotate -d /etc/logrotate.d/dripemails
   ```

3. **Manually trigger rotation:**
   ```bash
   sudo logrotate -f /etc/logrotate.d/dripemails
   ```

### Permission errors

If you see permission errors, ensure log files have correct ownership:

```bash
sudo chown -R dripemails:dripemails /home/dripemails/web/logs/
sudo chown dripemails:dripemails /var/log/gmail_processor.log /var/log/imap_crawler.log
```

### Service restart issues

If services fail to restart after rotation, check the postrotate scripts. You may need to adjust the service restart commands based on your setup.

