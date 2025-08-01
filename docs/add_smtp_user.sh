#!/bin/sh

# SMTP User Management Script
# This script adds users for SMTP authentication without Dovecot

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

# Check if username is provided
if [ -z "$1" ]; then
    print_error "Usage: $0 <username>"
    print_status "Example: $0 founders"
    exit 1
fi

USERNAME="$1"

print_status "Adding SMTP user: $USERNAME"

# Check if user already exists
if id "$USERNAME" >/dev/null 2>&1; then
    print_warning "User $USERNAME already exists"
else
    # Create user
    print_status "Creating user $USERNAME..."
    useradd -m -s /bin/bash "$USERNAME"
    print_success "User $USERNAME created"
fi

# Set password
print_status "Setting password for $USERNAME..."
passwd "$USERNAME"

# Add user to mail group
print_status "Adding user to mail group..."
usermod -a -G mail "$USERNAME"

# Create mail directory
print_status "Creating mail directory..."
mkdir -p "/home/$USERNAME/Maildir"
chown "$USERNAME:mail" "/home/$USERNAME/Maildir"
chmod 700 "/home/$USERNAME/Maildir"

print_success "SMTP user $USERNAME has been configured successfully!"
print_status "You can now use this user for SMTP authentication"
print_status "Username: $USERNAME"
print_status "Email: $USERNAME@dripemails.org" 