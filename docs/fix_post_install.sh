#!/bin/sh

# Fix Post-Install Script
# This script creates the missing post-install script

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

print_status "Creating missing post-install script..."

# Create the post-install script
print_status "Creating post-install script..."
cat > /usr/lib/postfix/post-install << 'EOF'
#!/bin/sh

# Postfix post-install script
# This script handles post-installation tasks for Postfix

set -e

# Function to create missing queue directories
create_missing() {
    echo "Creating missing queue directories..."
    
    # Create queue directories
    mkdir -p /var/spool/postfix/{incoming,active,deferred,bounce,defer,flush,trace,private,maildrop,hold,corrupt,public}
    mkdir -p /var/spool/postfix/{pid,etc,usr,lib,dev}
    
    # Set ownership
    chown -R postfix:postfix /var/spool/postfix
    
    # Set permissions
    chmod -R 755 /var/spool/postfix
    chmod 750 /var/spool/postfix/private
    chmod 750 /var/spool/postfix/maildrop
    chmod 775 /var/spool/postfix/public
    chmod 775 /var/spool/postfix/maildrop
    
    # Create necessary files
    touch /var/spool/postfix/pid/master.pid
    chown postfix:postfix /var/spool/postfix/pid/master.pid
    
    echo "Queue directories created successfully"
}

# Function to configure Postfix
configure() {
    echo "Configuring Postfix..."
    
    # Set compatibility level
    postconf compatibility_level=3.6
    
    # Reload Postfix
    systemctl reload postfix
    
    echo "Postfix configured successfully"
}

# Main script logic
case "$1" in
    create-missing)
        create_missing
        ;;
    configure)
        configure
        ;;
    *)
        echo "Usage: $0 {create-missing|configure}"
        exit 1
        ;;
esac

exit 0
EOF

# Make the script executable
chmod +x /usr/lib/postfix/post-install

print_success "post-install script created"

# Run the post-install script
print_status "Running post-install script..."
/usr/lib/postfix/post-install create-missing

# Set compatibility level
print_status "Setting compatibility level..."
postconf compatibility_level=3.6

# Test Postfix configuration
print_status "Testing Postfix configuration..."
if postfix check; then
    print_success "Postfix configuration is valid"
else
    print_error "Postfix configuration has errors"
    print_status "Configuration errors:"
    postfix check
fi

# Start Postfix
print_status "Starting Postfix..."
systemctl start postfix

# Check Postfix status
print_status "Checking Postfix status..."
if systemctl is-active --quiet postfix; then
    print_success "Postfix is running successfully"
else
    print_error "Postfix failed to start"
    systemctl status postfix --no-pager -l
fi

print_success "Post-install script has been created and Postfix is working!"
print_status "You can now run the configuration script:"
print_status "sudo bash fix_postfix_config.sh" 