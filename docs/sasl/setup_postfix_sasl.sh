#!/bin/bash
#
# Postfix SASL Authentication Setup Script
# This script safely configures SMTP AUTH for Postfix
#
# Usage: sudo ./setup_postfix_sasl.sh [username] [password]
# Example: sudo ./setup_postfix_sasl.sh founders aspen45

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    print_error "Please run as root (use sudo)"
    exit 1
fi

# Get username and password from arguments or prompt
USERNAME=${1:-founders}
PASSWORD=${2:-}

if [ -z "$PASSWORD" ]; then
    print_warn "Password not provided as argument"
    read -sp "Enter password for user '$USERNAME': " PASSWORD
    echo
    if [ -z "$PASSWORD" ]; then
        print_error "Password cannot be empty"
        exit 1
    fi
fi

# Get hostname/domain
DOMAIN=$(hostname -d 2>/dev/null || hostname -f 2>/dev/null || echo "dripemails.org")
print_info "Using domain: $DOMAIN"

# Step 1: Install required packages
print_info "Step 1: Installing required packages..."
if ! dpkg -l | grep -q sasl2-bin; then
    apt-get update -qq
    apt-get install -y sasl2-bin libsasl2-modules sasl2-modules
    print_info "Packages installed successfully"
else
    print_info "Packages already installed"
fi

# Step 2: Create SASL directory structure
print_info "Step 2: Creating SASL directory structure..."
mkdir -p /etc/postfix/sasl
chmod 755 /etc/postfix/sasl

# Step 3: Create SASL configuration file
print_info "Step 3: Configuring SASL..."
cat > /etc/postfix/sasl/smtpd.conf << 'EOF'
pwcheck_method: auxprop
auxprop_plugin: sasldb
mech_list: PLAIN LOGIN
EOF

chmod 644 /etc/postfix/sasl/smtpd.conf
chown root:root /etc/postfix/sasl/smtpd.conf
print_info "SASL configuration file created"

# Step 4: Create or update SASL user
print_info "Step 4: Creating SASL user '$USERNAME'..."
SASLDB_PATH="/etc/postfix/sasl/sasldb2"

# Check if user already exists
if [ -f "$SASLDB_PATH" ] && sasldblistusers2 -f "$SASLDB_PATH" 2>/dev/null | grep -q "^$USERNAME@$DOMAIN"; then
    print_warn "User $USERNAME@$DOMAIN already exists. Deleting old entry..."
    # Delete existing user first
    saslpasswd2 -f "$SASLDB_PATH" -u "$DOMAIN" -d "$USERNAME" 2>/dev/null || true
fi

# Create the user using the -f flag to specify database location
# Use printf to avoid issues with echo and newlines
print_info "Creating SASL user..."
if printf '%s' "$PASSWORD" | saslpasswd2 -f "$SASLDB_PATH" -p -u "$DOMAIN" "$USERNAME"; then
    print_info "User creation command succeeded"
else
    print_error "saslpasswd2 command failed"
    print_info "Checking if file was created anyway..."
fi

# Set proper permissions on sasldb2
if [ -f "$SASLDB_PATH" ]; then
    chmod 600 "$SASLDB_PATH"
    chown postfix:postfix "$SASLDB_PATH"
    print_info "SASL user created/updated successfully"
    print_info "File exists at: $SASLDB_PATH"
    ls -la "$SASLDB_PATH"
else
    print_error "Failed to create sasldb2 file at $SASLDB_PATH"
    print_info "Trying to create empty database first..."
    # Try creating an empty database first using sasldblistusers2
    touch "$SASLDB_PATH"
    chmod 600 "$SASLDB_PATH"
    chown postfix:postfix "$SASLDB_PATH"
    # Try again with explicit path
    print_info "Retrying user creation..."
    if printf '%s' "$PASSWORD" | saslpasswd2 -f "$SASLDB_PATH" -p -u "$DOMAIN" "$USERNAME"; then
        chmod 600 "$SASLDB_PATH"
        chown postfix:postfix "$SASLDB_PATH"
        print_info "User created successfully on retry"
    else
        print_error "Still failed to create sasldb2 file"
        print_error "Please check saslpasswd2 installation and permissions"
        exit 1
    fi
fi

# Step 5: Verify user was created
print_info "Step 5: Verifying SASL user..."
if sasldblistusers2 -f "$SASLDB_PATH" | grep -q "^$USERNAME@$DOMAIN"; then
    print_info "User $USERNAME@$DOMAIN verified successfully"
else
    print_error "Failed to verify user creation"
    print_info "Listing all users in database:"
    sasldblistusers2 -f "$SASLDB_PATH" || true
    exit 1
fi

# Step 6: Backup Postfix main.cf
print_info "Step 6: Backing up Postfix configuration..."
BACKUP_FILE="/etc/postfix/main.cf.backup.$(date +%Y%m%d_%H%M%S)"
cp /etc/postfix/main.cf "$BACKUP_FILE"
print_info "Backup created: $BACKUP_FILE"

# Step 7: Update Postfix main.cf
print_info "Step 7: Updating Postfix main.cf..."

# Check if SASL config already exists
if grep -q "^smtpd_sasl_type" /etc/postfix/main.cf; then
    print_warn "SASL configuration already exists in main.cf"
    print_info "Updating existing SASL configuration..."
    
    # Remove existing SASL lines
    sed -i '/^smtpd_sasl_type/d' /etc/postfix/main.cf
    sed -i '/^smtpd_sasl_path/d' /etc/postfix/main.cf
    sed -i '/^smtpd_sasl_auth_enable/d' /etc/postfix/main.cf
    sed -i '/^smtpd_sasl_security_options/d' /etc/postfix/main.cf
    sed -i '/^smtpd_sasl_local_domain/d' /etc/postfix/main.cf
    sed -i '/^broken_sasl_auth_clients/d' /etc/postfix/main.cf
fi

# Add SASL configuration
cat >> /etc/postfix/main.cf << EOF

# SMTP AUTH Configuration (added by setup script)
smtpd_sasl_type = cyrus
smtpd_sasl_path = smtpd
smtpd_sasl_auth_enable = yes
smtpd_sasl_security_options = noanonymous
smtpd_sasl_local_domain = \$myhostname
broken_sasl_auth_clients = yes
EOF

# Update recipient restrictions if needed
if grep -q "^smtpd_recipient_restrictions" /etc/postfix/main.cf; then
    print_info "Updating smtpd_recipient_restrictions..."
    # Check if permit_sasl_authenticated is already there
    if ! grep -q "permit_sasl_authenticated" /etc/postfix/main.cf; then
        # Add permit_sasl_authenticated after permit_mynetworks
        sed -i 's/\(permit_mynetworks\)/\1,\n    permit_sasl_authenticated/' /etc/postfix/main.cf
    fi
else
    print_info "Adding smtpd_recipient_restrictions..."
    cat >> /etc/postfix/main.cf << 'EOF'

# Recipient restrictions (added by setup script)
smtpd_recipient_restrictions = 
    permit_mynetworks,
    permit_sasl_authenticated,
    reject_unauth_destination
EOF
fi

# Step 8: Update master.cf if needed
print_info "Step 8: Checking Postfix master.cf..."
if ! grep -q "smtpd_sasl_auth_enable" /etc/postfix/master.cf; then
    # Backup master.cf
    cp /etc/postfix/master.cf "/etc/postfix/master.cf.backup.$(date +%Y%m%d_%H%M%S)"
    
    # Add SASL options to smtp service (if not already there)
    if grep -q "^smtp.*smtpd$" /etc/postfix/master.cf; then
        # Add SASL options after the smtp line
        sed -i '/^smtp.*smtpd$/a\  -o smtpd_sasl_auth_enable=yes\n  -o smtpd_sasl_security_options=noanonymous' /etc/postfix/master.cf
        print_info "Updated master.cf with SASL options"
    fi
else
    print_info "master.cf already has SASL configuration"
fi

# Step 9: Test Postfix configuration
print_info "Step 9: Testing Postfix configuration..."
if postfix check; then
    print_info "Postfix configuration is valid"
else
    print_error "Postfix configuration has errors!"
    print_warn "Restoring backup..."
    cp "$BACKUP_FILE" /etc/postfix/main.cf
    exit 1
fi

# Step 10: Restart Postfix
print_info "Step 10: Restarting Postfix..."
if systemctl restart postfix; then
    print_info "Postfix restarted successfully"
else
    print_error "Failed to restart Postfix"
    exit 1
fi

# Step 11: Verify Postfix is running
sleep 2
if systemctl is-active --quiet postfix; then
    print_info "Postfix is running"
else
    print_error "Postfix is not running!"
    exit 1
fi

# Step 12: Test SASL authentication
print_info "Step 12: Testing SASL authentication..."
# Check if AUTH is advertised
if echo "EHLO localhost" | telnet localhost 25 2>/dev/null | grep -q "AUTH"; then
    print_info "SMTP AUTH is enabled and advertised"
else
    print_warn "SMTP AUTH might not be advertised (this could be normal if testing too quickly)"
fi

# Summary
echo
print_info "=========================================="
print_info "SASL Setup Complete!"
print_info "=========================================="
print_info "Username: $USERNAME@$DOMAIN"
print_info "SASL database: $SASLDB_PATH"
print_info "Configuration backup: $BACKUP_FILE"
echo
print_info "To test authentication, use:"
print_info "  telnet localhost 25"
print_info "  EHLO localhost"
print_info "  (You should see '250-AUTH PLAIN LOGIN')"
echo
print_info "To list SASL users:"
print_info "  sasldblistusers2 -f $SASLDB_PATH"
echo
print_info "To add more users:"
print_info "  sudo saslpasswd2 -u $DOMAIN username"
echo

