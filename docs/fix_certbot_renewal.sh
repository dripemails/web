#!/bin/sh

# Certbot Renewal Fix Script
# This script fixes certbot renewal configuration issues

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

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
if [ "$(id -u)" -ne 0 ]; then
    print_error "This script must be run as root (use sudo)"
    exit 1
fi

print_status "Fixing Certbot renewal configuration..."

# Check current renewal configuration
print_status "Checking current renewal configuration..."
if [ -f "/etc/letsencrypt/renewal/dripemails.org.conf" ]; then
    print_success "Renewal config found: /etc/letsencrypt/renewal/dripemails.org.conf"
    print_status "Current configuration:"
    cat /etc/letsencrypt/renewal/dripemails.org.conf
else
    print_error "Renewal config not found"
    exit 1
fi

# Check if certificates exist
print_status "Checking certificate files..."
if [ -f "/etc/letsencrypt/live/dripemails.org/fullchain.pem" ]; then
    print_success "Certificate exists: /etc/letsencrypt/live/dripemails.org/fullchain.pem"
else
    print_error "Certificate not found"
    exit 1
fi

# Check post-hook script
print_status "Checking post-hook script..."
if [ -f "/etc/letsencrypt/renewal-hooks/post/postfix-reload.sh" ]; then
    print_status "Post-hook script found. Checking content:"
    cat /etc/letsencrypt/renewal-hooks/post/postfix-reload.sh
else
    print_warning "Post-hook script not found"
fi

# Create a proper post-hook script
print_status "Creating proper post-hook script..."
mkdir -p /etc/letsencrypt/renewal-hooks/post

cat > /etc/letsencrypt/renewal-hooks/post/postfix-reload.sh << 'EOF'
#!/bin/sh

# Post-hook script for certbot renewal
# This script reloads Postfix after certificate renewal

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}[INFO]${NC} Post-hook: Certificate renewed, reloading Postfix..."

# Check if Postfix is running
if systemctl is-active --quiet postfix; then
    # Reload Postfix
    systemctl reload postfix
    echo -e "${GREEN}[SUCCESS]${NC} Postfix reloaded successfully"
else
    echo -e "${RED}[ERROR]${NC} Postfix is not running"
    exit 1
fi

echo -e "${GREEN}[SUCCESS]${NC} Post-hook completed successfully"
EOF

# Make the script executable
chmod +x /etc/letsencrypt/renewal-hooks/post/postfix-reload.sh

# Update the renewal configuration to use the proper post-hook
print_status "Updating renewal configuration..."
cat > /etc/letsencrypt/renewal/dripemails.org.conf << 'EOF'
# renew_before_expiry = 30 days
version = 2.8.0
archive_dir = /etc/letsencrypt/archive/dripemails.org
cert = /etc/letsencrypt/live/dripemails.org/cert.pem
privkey = /etc/letsencrypt/live/dripemails.org/privkey.pem
chain = /etc/letsencrypt/live/dripemails.org/chain.pem
fullchain = /etc/letsencrypt/live/dripemails.org/fullchain.pem

# Options used in the renewal process
[renewalparams]
account = 1234567890abcdef1234567890abcdef
authenticator = standalone
server = https://acme-v02.api.letsencrypt.org/directory
key_type = rsa
[[webroot_map]]
dripemails.org = /var/www/html
post_hook = /etc/letsencrypt/renewal-hooks/post/postfix-reload.sh
EOF

# Test the renewal process
print_status "Testing renewal process..."
if certbot renew --dry-run; then
    print_success "Renewal test completed successfully"
else
    print_error "Renewal test failed"
    exit 1
fi

print_success "Certbot renewal configuration has been fixed!"
print_status "The renewal process should now work properly"
print_status "You can test it again with: certbot renew --dry-run" 