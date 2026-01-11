# DripEmails.org Production Deployment Guide

This guide covers deploying DripEmails.org to production using ASGI (Daphne) with MySQL and Redis.

## Prerequisites

- Ubuntu 20.04+ server
- Domain name (dripemails.org)
- SSL certificate
- Root or sudo access

## 1. Server Setup

### Update System
```bash
sudo apt update && sudo apt upgrade -y
```

### Install Dependencies
```bash
sudo apt install -y python3 python3-pip python3-venv nginx postgresql postgresql-contrib redis-server supervisor git curl
```

## 2. Database Setup

### Configure PostgreSQL
```bash
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

### Create Database and User
```bash
sudo -u postgres psql -c "CREATE DATABASE dripemails;"
sudo -u postgres psql -c "CREATE USER dripemails WITH PASSWORD 'password';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE dripemails TO dripemails;"
sudo -u postgres psql -c "ALTER USER dripemails CREATEDB;"
```

## 3. Application Setup

### Create Application Directory
```bash
sudo mkdir -p /home/dripemails/web
sudo chown dripemails:dripemails /home/dripemails/web
```

### Clone/Upload Project
```bash
cd /home/dripemails/web
# Upload your project files here
```

### Create Virtual Environment
```bash
cd /home/dripemails
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
```

### Install Python Dependencies
```bash
pip install django daphne uvicorn gunicorn psycopg2-binary redis celery django-cors-headers django-allauth djangorestframework python-dotenv
```

## 4. Environment Configuration

### Create Environment File
```bash
cd /home/dripemails/web
cp docs/env.example .env
nano .env
```

**Required changes in .env:**
- Set a strong `SECRET_KEY`
- Configure your email settings
- Update any other environment-specific values

### Set Permissions
```bash
sudo chown -R dripemails:dripemails /home/dripemails
sudo chmod -R 755 /home/dripemails
sudo chmod 600 /home/dripemails/web/.env
```

## 5. Django Setup

### Run Migrations
```bash
cd /home/dripemails/web
source ../venv/bin/activate
export DJANGO_SETTINGS_MODULE=docs.live
python manage.py migrate
```

### Create Superuser
```bash
python manage.py createsuperuser
```

### Collect Static Files
```bash
python manage.py collectstatic --noinput
```

## 6. ASGI Server Setup

### Using Daphne (Recommended)
```bash
# Test Daphne
cd /home/dripemails/web
source ../venv/bin/activate
export DJANGO_SETTINGS_MODULE=docs.live
daphne -b 0.0.0.0 -p 8001 docs.live:application
```

### Using Uvicorn (Alternative)
```bash
# Test Uvicorn
cd /home/dripemails/web
source ../venv/bin/activate
export DJANGO_SETTINGS_MODULE=docs.live
uvicorn docs.live:application --host 0.0.0.0 --port 8001
```

## 7. Process Management

### Option A: Supervisor (Recommended)
```bash
sudo cp docs/supervisor.conf /etc/supervisor/conf.d/dripemails.conf
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start dripemails-daphne
sudo supervisorctl start dripemails-celery
sudo supervisorctl start dripemails-celerybeat
```

### Option B: Systemd
```bash
sudo cp docs/dripemails-daphne.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable dripemails-daphne
sudo systemctl start dripemails-daphne
```

## 8. Nginx Configuration

### Create Nginx Config
```bash
sudo cp docs/nginx.conf /etc/nginx/sites-available/dripemails
sudo ln -s /etc/nginx/sites-available/dripemails /etc/nginx/sites-enabled/
sudo rm /etc/nginx/sites-enabled/default
```

### Test and Reload Nginx
```bash
sudo nginx -t
sudo systemctl reload nginx
```

## 9. SSL Certificate (Let's Encrypt)

### Install Certbot
```bash
sudo apt install certbot python3-certbot-nginx
```

### Obtain Certificate
```bash
sudo certbot --nginx -d dripemails.org -d www.dripemails.org -d api.dripemails.org
```

### Auto-renewal
```bash
sudo crontab -e
# Add: 0 12 * * * /usr/bin/certbot renew --quiet
```

## 10. Monitoring and Logs

### View Logs
```bash
# Application logs
tail -f /home/dripemails/web/logs/django.log

# Nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log

# Supervisor logs
sudo supervisorctl tail dripemails-daphne
```

### Health Check
```bash
curl -I https://dripemails.org
```

## 11. Backup Strategy

### Database Backup
```bash
# Create backup script
cat > /home/dripemails/web/backup.sh << 'EOF'
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
pg_dump -h localhost -U dripemails -d dripemails > /home/dripemails/web/backups/db_backup_$DATE.sql
tar -czf /home/dripemails/web/backups/media_backup_$DATE.tar.gz /home/dripemails/web/media/
find /home/dripemails/web/backups/ -name "*.sql" -mtime +7 -delete
find /home/dripemails/web/backups/ -name "*.tar.gz" -mtime +7 -delete
EOF

chmod +x /home/dripemails/web/backup.sh
mkdir -p /home/dripemails/web/backups

# Add to crontab
crontab -e
# Add: 0 2 * * * /home/dripemails/web/backup.sh
```

## 12. Security Checklist

- [ ] Firewall configured (UFW)
- [ ] SSH key authentication only
- [ ] Fail2ban installed
- [ ] Regular security updates
- [ ] Database backups automated
- [ ] SSL certificate installed
- [ ] Environment variables secured
- [ ] File permissions set correctly

## 13. Performance Optimization

### Redis Configuration
```bash
sudo nano /etc/redis/redis.conf
# Set: maxmemory 256mb
# Set: maxmemory-policy allkeys-lru
sudo systemctl restart redis
```

### MySQL Optimization
```bash
sudo nano /etc/mysql/mysql.conf.d/mysqld.cnf
# Add:
[mysqld]
innodb_buffer_pool_size = 256M
query_cache_size = 32M
query_cache_type = 1
```

## 14. Troubleshooting

### Common Issues

**502 Bad Gateway**
- Check if Daphne is running: `sudo supervisorctl status`
- Check logs: `sudo supervisorctl tail dripemails-daphne`

**Database Connection Error**
- Verify PostgreSQL is running: `sudo systemctl status postgresql`
- Check credentials in .env file
- Test connection: `psql -h localhost -U dripemails -d dripemails`

**Static Files Not Loading**
- Run collectstatic: `cd /home/dripemails/web && source ../venv/bin/activate && python manage.py collectstatic --noinput`
- Check Nginx configuration
- Verify file permissions

**Email Not Sending**
- Check email settings in .env
- Verify SMTP credentials
- Check firewall settings

## 15. Maintenance

### Regular Tasks
- Monitor disk space: `df -h`
- Check memory usage: `free -h`
- Review logs for errors
- Update system packages
- Renew SSL certificates
- Test backups

### Updates
```bash
cd /home/dripemails/web
source ../venv/bin/activate
git pull origin main
pip install -r requirements.txt
export DJANGO_SETTINGS_MODULE=docs.live
python manage.py migrate
python manage.py collectstatic --noinput
sudo supervisorctl restart dripemails-daphne
```

## Support

For issues or questions:
1. Check the logs first
2. Review this deployment guide
3. Check Django documentation
4. Contact the development team 
