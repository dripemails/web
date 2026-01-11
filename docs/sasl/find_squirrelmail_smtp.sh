#!/bin/bash
#
# Find SquirrelMail SMTP Configuration
#

GREEN='\033[0;32m'
NC='\033[0m'

print_info() { echo -e "${GREEN}[INFO]${NC} $1"; }

print_info "=== Finding SquirrelMail SMTP Configuration ==="
echo

# Find SquirrelMail config files
print_info "1. Searching for SquirrelMail configuration files..."
CONFIG_FILES=$(find /etc /usr/share /var/www -name "config.php" -path "*squirrelmail*" 2>/dev/null | head -5)

if [ -z "$CONFIG_FILES" ]; then
    print_info "SquirrelMail config not found in standard locations"
    print_info "Trying alternative locations..."
    CONFIG_FILES=$(find / -name "config.php" -path "*squirrelmail*" 2>/dev/null | head -5)
fi

if [ -z "$CONFIG_FILES" ]; then
    print_info "Could not find SquirrelMail config"
    print_info "Trying to find SquirrelMail installation..."
    find /etc /usr/share /var/www -type d -name "*squirrelmail*" 2>/dev/null
else
    for config in $CONFIG_FILES; do
        print_info "Found: $config"
        echo
        print_info "SMTP settings:"
        grep -E "smtp|SMTP" "$config" | grep -v "^#" | head -10
        echo
    done
fi

echo
print_info "2. Checking common mail server ports..."
print_info "Port 25 (SMTP):"
netstat -tlnp 2>/dev/null | grep ":25 " || ss -tlnp 2>/dev/null | grep ":25 "
echo
print_info "Port 587 (Submission):"
netstat -tlnp 2>/dev/null | grep ":587 " || ss -tlnp 2>/dev/null | grep ":587 "
echo
print_info "Port 465 (SMTPS):"
netstat -tlnp 2>/dev/null | grep ":465 " || ss -tlnp 2>/dev/null | grep ":465 "
echo

print_info "3. Checking Dovecot (often used with SquirrelMail):"
systemctl status dovecot 2>/dev/null | head -5 || print_info "Dovecot not running or not installed"
echo

print_info "=== Recommendation ==="
print_info "If SquirrelMail works, try using the same SMTP server:"
print_info "  - Check SquirrelMail's config for SMTP host/port"
print_info "  - Use port 587 with TLS (simpler than port 25)"
print_info "  - Or use a third-party service like SendGrid (easiest)"

