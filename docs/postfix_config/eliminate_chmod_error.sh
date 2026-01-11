#!/bin/sh

# Eliminate Chmod Error Script
# This script finds and eliminates the persistent chmod error

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

print_status "Searching for the source of the chmod error..."

# Search for any script that might be calling chmod with empty domain
print_status "Searching for chmod commands in all renewal hooks..."
find /etc/letsencrypt/renewal-hooks -type f -exec grep -l "chmod.*fullchain.pem" {} \; 2>/dev/null || true

# Check if there's a global post-hook that's being called
print_status "Checking for global post-hook in CLI config..."
if [ -f "/etc/letsencrypt/cli.ini" ]; then
    grep -i "post_hook" /etc/letsencrypt/cli.ini || true
fi

# Check if there are any environment variables being set
print_status "Checking for environment variables..."
env | grep -i domain || true

# Search for any script that might be using $1 or empty variables
print_status "Searching for scripts using \$1 or empty variables..."
find /etc/letsencrypt/renewal-hooks -name "*.sh" -exec grep -l "\$1" {} \; 2>/dev/null || true

# Check if there's a system-wide renewal script
print_status "Checking for system-wide renewal scripts..."
find /etc -name "*renew*" -type f 2>/dev/null | head -10

# Let's check if there's a cron job or systemd timer that might be calling something
print_status "Checking for cron jobs or timers..."
systemctl list-timers | grep -i certbot || true
crontab -l 2>/dev/null | grep -i certbot || true

# Check if there's a global post-hook that's not in the CLI config
print_status "Checking for global post-hook files..."
find /etc -name "*post-hook*" -type f 2>/dev/null || true

# Let's also check if there's a script that's being called by certbot itself
print_status "Checking certbot's own scripts..."
find /usr/lib/python* -name "*certbot*" -type f 2>/dev/null | head -5

# Now let's create a simple test to see what's happening
print_status "Creating a test script to capture the environment..."
cat > /tmp/test_renewal.sh << 'EOF'
#!/bin/sh
echo "=== ENVIRONMENT VARIABLES ==="
env | sort
echo "=== ARGUMENTS ==="
echo "Number of arguments: $#"
for i in "$@"; do
    echo "Argument: '$i'"
done
echo "=== DOMAIN VARIABLES ==="
echo "RENEWED_DOMAINS: '$RENEWED_DOMAINS'"
echo "DOMAIN: '$DOMAIN'"
echo "=== END TEST ==="
EOF

chmod +x /tmp/test_renewal.sh

# Temporarily replace the post-hook with our test script
print_status "Temporarily replacing post-hook with test script..."
cp /etc/letsencrypt/renewal-hooks/post/postfix-ssl-renew.sh /etc/letsencrypt/renewal-hooks/post/postfix-ssl-renew.sh.backup
cp /tmp/test_renewal.sh /etc/letsencrypt/renewal-hooks/post/postfix-ssl-renew.sh

print_status "Running test renewal to see what's happening..."
certbot renew --dry-run 2>&1 | grep -A 20 "Hook 'post-hook'"

# Restore the original script
print_status "Restoring original post-hook script..."
cp /etc/letsencrypt/renewal-hooks/post/postfix-ssl-renew.sh.backup /etc/letsencrypt/renewal-hooks/post/postfix-ssl-renew.sh

print_status "Test completed. Check the output above for clues about the chmod error." 