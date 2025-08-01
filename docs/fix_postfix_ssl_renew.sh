#!/bin/sh

# Fix Postfix SSL Renew Script
# This script fixes the problematic postfix-ssl-renew.sh script

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

print_status "Fixing the problematic postfix-ssl-renew.sh script..."

# Check the current script
print_status "Current postfix-ssl-renew.sh content:"
if [ -f "/etc/letsencrypt/renewal-hooks/post/postfix-ssl-renew.sh" ]; then
    cat /etc/letsencrypt/renewal-hooks/post/postfix-ssl-renew.sh
else
    print_error "Script not found"
    exit 1
fi

# Backup the original script
print_status "Backing up original script..."
cp /etc/letsencrypt/renewal-hooks/post/postfix-ssl-renew.sh /etc/letsencrypt/renewal-hooks/post/postfix-ssl-renew.sh.backup

# Create a fixed version of the script
print_status "Creating fixed version of the script..."
cat > /etc/letsencrypt/renewal-hooks/post/postfix-ssl-renew.sh << 'EOF'
#!/bin/sh

# Postfix SSL Certificate Renewal Hook
# This script updates Postfix configuration after SSL certificate renewal

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}[INFO]${NC} Postfix SSL renewal hook started..."

# Get the domain from the environment or use a default
DOMAIN="${RENEWED_DOMAINS:-dripemails.org}"

# Check if we have a valid domain
if [ -z "$DOMAIN" ] || [ "$DOMAIN" = "" ]; then
    echo -e "${RED}[ERROR]${NC} No domain specified, using default: dripemails.org"
    DOMAIN="dripemails.org"
fi

# Define certificate paths
CERT_PATH="/etc/letsencrypt/live/$DOMAIN/fullchain.pem"
KEY_PATH="/etc/letsencrypt/live/$DOMAIN/privkey.pem"

# Verify certificates exist
if [ ! -f "$CERT_PATH" ] || [ ! -f "$KEY_PATH" ]; then
    echo -e "${RED}[ERROR]${NC} SSL certificates not found at expected locations"
    echo -e "${RED}[ERROR]${NC} CERT_PATH: $CERT_PATH"
    echo -e "${RED}[ERROR]${NC} KEY_PATH: $KEY_PATH"
    exit 1
fi

# Set proper permissions for Postfix to read certificates
echo -e "${BLUE}[INFO]${NC} Setting certificate permissions..."
chmod 644 "$CERT_PATH"
chmod 600 "$KEY_PATH"
chown root:root "$CERT_PATH" "$KEY_PATH"

# Update Postfix configuration
echo -e "${BLUE}[INFO]${NC} Updating Postfix configuration..."
postconf -e "smtpd_tls_cert_file=$CERT_PATH"
postconf -e "smtpd_tls_key_file=$KEY_PATH"

# Reload Postfix
echo -e "${BLUE}[INFO]${NC} Reloading Postfix..."
if systemctl is-active --quiet postfix; then
    systemctl reload postfix
    echo -e "${GREEN}[SUCCESS]${NC} Postfix reloaded successfully"
else
    echo -e "${RED}[ERROR]${NC} Postfix is not running"
    exit 1
fi

echo -e "${GREEN}[SUCCESS]${NC} Postfix SSL renewal hook completed successfully"
EOF

# Make the script executable
chmod +x /etc/letsencrypt/renewal-hooks/post/postfix-ssl-renew.sh

print_success "Fixed postfix-ssl-renew.sh script created!"

# Test the renewal process again
print_status "Testing renewal process..."
if certbot renew --dry-run; then
    print_success "Renewal test completed successfully!"
else
    print_error "Renewal test still failed"
    exit 1
fi

print_success "Postfix SSL renewal script has been fixed!"
print_status "The renewal process should now work without errors"
print_status "You can test it again with: certbot renew --dry-run" 