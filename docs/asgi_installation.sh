#!/bin/bash

# ASGI Installation Script for DripEmails.org
# This script sets up the production environment with ASGI server

set -e  # Exit on any error

echo "🚀 Starting ASGI installation for DripEmails.org..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   print_error "This script should not be run as root"
   exit 1
fi

# Update system packages
print_status "Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install system dependencies
print_status "Installing system dependencies..."
sudo apt install -y python3 python3-pip python3-venv nginx mysql-server redis-server supervisor git curl

# Install Python dependencies
print_status "Installing Python dependencies..."
pip3 install --upgrade pip

# Create dripemails user and group
print_status "Creating dripemails user and group..."
sudo useradd -m -s /bin/bash dripemails
sudo usermod -aG sudo dripemails

# Create virtual environment
print_status "Creating virtual environment..."
python3 -m venv /home/dripemails/venv
source /home/dripemails/venv/bin/activate

# Install Python packages
print_status "Installing Python packages..."
pip install django daphne uvicorn gunicorn mysqlclient redis celery django-cors-headers django-allauth djangorestframework

# Clone or setup project
print_status "Setting up project directory..."
sudo mkdir -p /home/dripemails/web
sudo chown dripemails:dripemails /home/dripemails/web

# Create necessary directories
sudo -u dripemails mkdir -p /home/dripemails/web/logs
sudo -u dripemails mkdir -p /home/dripemails/web/staticfiles
sudo -u dripemails mkdir -p /home/dripemails/web/media

# Setup environment variables
print_status "Setting up environment variables..."
cat > /home/dripemails/web/.env << EOF
# Django Settings
SECRET_KEY=your-super-secret-key-change-this
DEBUG=False
ALLOWED_HOSTS=dripemails.org,www.dripemails.org,api.dripemails.org

# Database Settings
DB_NAME=dripemails
DB_USER=dripemails
DB_PASSWORD=password
DB_HOST=localhost
DB_PORT=3306

# Email Settings
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=noreply@dripemails.org

# Redis Settings
REDIS_URL=redis://127.0.0.1:6379/1
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
EOF

print_warning "Please edit /home/dripemails/web/.env with your actual values!"

# Setup MySQL
print_status "Setting up MySQL database..."
sudo mysql -e "CREATE DATABASE IF NOT EXISTS dripemails CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
sudo mysql -e "CREATE USER IF NOT EXISTS 'dripemails'@'localhost' IDENTIFIED BY 'password';"
sudo mysql -e "GRANT ALL PRIVILEGES ON dripemails.* TO 'dripemails'@'localhost';"
sudo mysql -e "FLUSH PRIVILEGES;"

# Setup Redis
print_status "Configuring Redis..."
sudo systemctl enable redis-server
sudo systemctl start redis-server

# Create ASGI configuration
print_status "Creating ASGI configuration..."
cat > /home/dripemails/web/asgi.py << 'EOF'
"""
ASGI config for dripemails project.
"""

import os
import sys
from pathlib import Path

# Add project directory to Python path
BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR))

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Set Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'docs.asgi_settings')

from django.core.asgi import get_asgi_application
from django.urls import path
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack

application = get_asgi_application()
EOF

# Create Daphne configuration
print_status "Creating Daphne configuration..."
cat > /home/dripemails/web/daphne.py << 'EOF'
#!/usr/bin/env python3
"""
Daphne configuration for DripEmails.org
"""

import os
import sys
from pathlib import Path

# Add project directory to Python path
BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR))

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Set Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'docs.asgi_settings')

from django.core.asgi import get_asgi_application

application = get_asgi_application()
EOF

# Create Supervisor configuration
print_status "Creating Supervisor configuration..."
sudo tee /etc/supervisor/conf.d/dripemails.conf > /dev/null << EOF
[program:dripemails-daphne]
command=/home/dripemails/venv/bin/daphne -b 0.0.0.0 -p 8001 docs.asgi_settings:application
directory=/home/dripemails/web
user=dripemails
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/home/dripemails/web/logs/daphne.log
environment=PATH="/home/dripemails/venv/bin"

[program:dripemails-celery]
command=/home/dripemails/venv/bin/celery -A dripemails worker --loglevel=info
directory=/home/dripemails/web
user=dripemails
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/home/dripemails/web/logs/celery.log
environment=PATH="/home/dripemails/venv/bin"

[program:dripemails-celerybeat]
command=/home/dripemails/venv/bin/celery -A dripemails beat --loglevel=info
directory=/home/dripemails/web
user=dripemails
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/home/dripemails/web/logs/celerybeat.log
environment=PATH="/home/dripemails/venv/bin"
EOF

# Create Nginx configuration
print_status "Creating Nginx configuration..."
sudo tee /etc/nginx/sites-available/dripemails << EOF
server {
    listen 80;
    server_name dripemails.org www.dripemails.org api.dripemails.org;
    
    # Redirect HTTP to HTTPS
    return 301 https://\$server_name\$request_uri;
}

server {
    listen 443 ssl http2;
    server_name dripemails.org www.dripemails.org api.dripemails.org;
    
    # SSL Configuration (you'll need to add your SSL certificates)
    ssl_certificate /etc/ssl/certs/dripemails.org.crt;
    ssl_certificate_key /etc/ssl/private/dripemails.org.key;
    
    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;
    
    # Static files
    location /static/ {
        alias /home/dripemails/web/staticfiles/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
    
    # Media files
    location /media/ {
        alias /home/dripemails/web/media/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
    
    # Proxy to Daphne
    location / {
        proxy_pass http://127.0.0.1:8001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_cache_bypass \$http_upgrade;
    }
}
EOF

# Enable Nginx site
sudo ln -sf /etc/nginx/sites-available/dripemails /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# Set proper permissions
print_status "Setting proper permissions..."
sudo chown -R dripemails:dripemails /home/dripemails
sudo chmod -R 755 /home/dripemails

# Install additional Python packages
print_status "Installing additional Python packages..."
source /home/dripemails/venv/bin/activate
pip install python-dotenv mysqlclient

# Create systemd service for Daphne (alternative to Supervisor)
print_status "Creating systemd service..."
sudo tee /etc/systemd/system/dripemails-daphne.service << EOF
[Unit]
Description=DripEmails Daphne ASGI Server
After=network.target

[Service]
Type=simple
User=dripemails
Group=dripemails
WorkingDirectory=/home/dripemails/web
Environment=PATH=/home/dripemails/venv/bin
ExecStart=/home/dripemails/venv/bin/daphne -b 0.0.0.0 -p 8001 docs.asgi_settings:application
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd and enable services
sudo systemctl daemon-reload
sudo systemctl enable dripemails-daphne
sudo systemctl enable supervisor
sudo systemctl enable nginx

# Final setup instructions
print_success "ASGI installation completed!"
echo ""
print_status "Next steps:"
echo "1. Copy your Django project files to /home/dripemails/web/"
echo "2. Edit /home/dripemails/web/.env with your actual values"
echo "3. Run migrations: cd /home/dripemails/web && source ../venv/bin/activate && python manage.py migrate"
echo "4. Collect static files: python manage.py collectstatic"
echo "5. Create superuser: python manage.py createsuperuser"
echo "6. Start services: sudo systemctl start dripemails-daphne nginx supervisor"
echo "7. Configure SSL certificates for HTTPS"
echo ""
print_warning "Don't forget to:"
echo "- Set up SSL certificates"
echo "- Configure your domain DNS"
echo "- Set up proper firewall rules"
echo "- Configure backup strategies" 