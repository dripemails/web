# uWSGI Setup Guide for DripEmails.org

This guide explains how to set up and run DripEmails.org using uWSGI on a production server.

## Prerequisites

- Python 3.11+ installed
- Virtual environment with all dependencies installed
- PostgreSQL database configured
- Redis server running (for Celery)
- Nginx installed (for reverse proxy)

## Installation

### 1. Install uWSGI

```bash
# Activate your virtual environment
source /path/to/dripemails.org/venv/bin/activate

# Install uWSGI
pip install uwsgi
```

### 2. Configure uWSGI

Edit `docs/uwsgi.ini` and update the following paths:

- `pythonpath` - Set to your project root directory
- `chdir` - Set to your project root directory
- `socket` - Adjust if needed (default: 127.0.0.1:8000)
- `logto` - Set to your desired log location
- `processes` - Adjust based on CPU cores (default: 4)
- `threads` - Adjust based on load (default: 2)

Example paths (replace with your actual paths):
```ini
pythonpath = /home/dripemails/web/dripemails.org
chdir = /home/dripemails/web/dripemails.org
logto = /var/log/uwsgi/dripemails.log
```

### 3. Create Log Directory

```bash
sudo mkdir -p /var/log/uwsgi
sudo chown www-data:www-data /var/log/uwsgi
```

### 4. Test uWSGI Configuration

```bash
# Activate virtual environment
source /path/to/dripemails.org/venv/bin/activate

# Test the configuration
uwsgi --ini docs/uwsgi.ini --check-static /path/to/dripemails.org/staticfiles
```

## Running uWSGI

### Manual Start

```bash
source /path/to/dripemails.org/venv/bin/activate
uwsgi --ini docs/uwsgi.ini
```

### Using Systemd (Recommended)

1. Copy the systemd service file:
```bash
sudo cp docs/uwsgi-systemd.service /etc/systemd/system/dripemails-uwsgi.service
```

2. Edit the service file and update paths:
```bash
sudo nano /etc/systemd/system/dripemails-uwsgi.service
```

Update these lines:
- `User=` - Set to your application user (e.g., `www-data` or `dripemails`)
- `Group=` - Set to your application group
- `WorkingDirectory=` - Set to your project root
- `Environment="PATH=..."` - Set to your virtual environment bin directory
- `ExecStart=` - Set to your virtual environment uwsgi binary and config path

3. Reload systemd and start the service:
```bash
sudo systemctl daemon-reload
sudo systemctl enable dripemails-uwsgi
sudo systemctl start dripemails-uwsgi
```

4. Check status:
```bash
sudo systemctl status dripemails-uwsgi
```

### Using Supervisor (Alternative)

If you prefer Supervisor over systemd, create a supervisor config:

```ini
[program:dripemails-uwsgi]
command=/path/to/dripemails.org/venv/bin/uwsgi --ini /path/to/dripemails.org/docs/uwsgi.ini
directory=/path/to/dripemails.org
user=www-data
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/uwsgi/dripemails-supervisor.log
```

## Nginx Configuration

Configure Nginx to proxy requests to uWSGI. Add this to your Nginx site configuration:

```nginx
server {
    listen 80;
    server_name dripemails.org www.dripemails.org;
    
    # Redirect to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name dripemails.org www.dripemails.org;
    
    # SSL configuration
    ssl_certificate /path/to/ssl/cert.pem;
    ssl_certificate_key /path/to/ssl/key.pem;
    
    # Static files
    location /static/ {
        alias /path/to/dripemails.org/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
    
    # Media files
    location /media/ {
        alias /path/to/dripemails.org/media/;
        expires 7d;
        add_header Cache-Control "public";
    }
    
    # Proxy to uWSGI
    location / {
        include uwsgi_params;
        uwsgi_pass 127.0.0.1:8000;
        uwsgi_param Host $host;
        uwsgi_param X-Real-IP $remote_addr;
        uwsgi_param X-Forwarded-For $proxy_add_x_forwarded_for;
        uwsgi_param X-Forwarded-Proto $scheme;
    }
}
```

## Environment Variables

Make sure your `.env` file is properly configured with production settings:

- `SECRET_KEY` - Django secret key
- `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT` - Database credentials
- `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD` - Email settings
- `CELERY_BROKER_URL` - Redis URL for Celery
- `REDIS_URL` - Redis URL for caching

## Monitoring

### Check uWSGI Status

```bash
# If using systemd
sudo systemctl status dripemails-uwsgi

# View logs
sudo tail -f /var/log/uwsgi/dripemails.log

# Check if uWSGI is listening
sudo netstat -tlnp | grep 8000
```

### Reload uWSGI

```bash
# If using systemd
sudo systemctl reload dripemails-uwsgi

# Or touch the reload file
touch /path/to/dripemails.org/reload
```

## Troubleshooting

### Permission Issues

```bash
# Ensure proper ownership
sudo chown -R www-data:www-data /path/to/dripemails.org
sudo chmod -R 755 /path/to/dripemails.org
```

### Port Already in Use

If port 8000 is already in use, either:
1. Change the socket in `uwsgi.ini` to a different port
2. Or use a Unix socket instead:
   ```ini
   socket = /tmp/dripemails.sock
   chmod-socket = 666
   ```

### Static Files Not Loading

1. Collect static files:
   ```bash
   python manage.py collectstatic --noinput
   ```

2. Ensure Nginx is configured to serve static files (see Nginx config above)

### Database Connection Issues

1. Verify PostgreSQL is running:
   ```bash
   sudo systemctl status postgresql
   ```

2. Check database credentials in `.env` file

3. Test connection:
   ```bash
   python manage.py dbshell
   ```

## Performance Tuning

Adjust these settings in `uwsgi.ini` based on your server:

- `processes` - Number of worker processes (2 * CPU cores + 1)
- `threads` - Threads per worker (2-4 is usually good)
- `max-requests` - Restart workers after N requests (5000 is good)
- `harakiri` - Kill workers that take too long (60 seconds)

## Security Notes

- Run uWSGI as a non-root user (www-data or dedicated user)
- Use Unix sockets when possible (more secure than TCP)
- Keep uWSGI and all dependencies updated
- Use HTTPS in production (configured in Nginx)
- Set proper file permissions

