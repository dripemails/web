#!/bin/bash

# Certbot Renewal Management Script for Postfix SSL
# This script helps manage and test certificate renewal

set -e

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

# Function to check if running as root
check_root() {
    if [[ $EUID -ne 0 ]]; then
        print_error "This script must be run as root (use sudo)"
        exit 1
    fi
}

# Function to show certificate status
show_certificate_status() {
    print_status "Checking certificate status..."
    echo
    
    if command -v certbot &> /dev/null; then
        certbot certificates
    else
        print_error "Certbot is not installed"
        exit 1
    fi
    
    echo
    print_status "Certificate locations:"
    ls -la /etc/letsencrypt/live/*/ 2>/dev/null || print_warning "No certificates found"
}

# Function to test renewal (dry run)
test_renewal() {
    print_status "Testing certificate renewal (dry run)..."
    echo
    
    if certbot renew --dry-run; then
        print_success "Renewal test completed successfully"
    else
        print_error "Renewal test failed"
        exit 1
    fi
}

# Function to perform actual renewal
perform_renewal() {
    print_status "Performing actual certificate renewal..."
    echo
    
    if certbot renew; then
        print_success "Certificate renewal completed"
        
        # Check if Postfix renewal hook was executed
        if [[ -f "/etc/letsencrypt/renewal-hooks/post/postfix-ssl-renew.sh" ]]; then
            print_status "Postfix renewal hook should have been executed automatically"
        else
            print_warning "Postfix renewal hook not found"
        fi
        
        # Reload Postfix to ensure new certificates are loaded
        print_status "Reloading Postfix service..."
        systemctl reload postfix
        
        if systemctl is-active --quiet postfix; then
            print_success "Postfix reloaded successfully"
        else
            print_error "Postfix reload failed"
            systemctl status postfix
        fi
    else
        print_error "Certificate renewal failed"
        exit 1
    fi
}

# Function to set up automatic renewal
setup_automatic_renewal() {
    print_status "Setting up automatic renewal..."
    echo
    
    # Create systemd timer for automatic renewal
    cat > /etc/systemd/system/certbot-renew.timer << 'EOF'
[Unit]
Description=Certbot Renewal Timer
Documentation=https://certbot.eff.org/docs/using.html#automated-renewals

[Timer]
OnCalendar=*-*-* 02:00:00
RandomizedDelaySec=43200
Persistent=true

[Install]
WantedBy=timers.target
EOF

    # Create systemd service for renewal
    cat > /etc/systemd/system/certbot-renew.service << 'EOF'
[Unit]
Description=Certbot Renewal Service
Documentation=https://certbot.eff.org/docs/using.html#automated-renewals

[Service]
Type=oneshot
ExecStart=/usr/bin/certbot renew --quiet --agree-tos
ExecStartPost=/bin/systemctl reload postfix

[Install]
WantedBy=multi-user.target
EOF

    # Enable and start the timer
    systemctl daemon-reload
    systemctl enable certbot-renew.timer
    systemctl start certbot-renew.timer
    
    print_success "Automatic renewal timer enabled"
    print_status "Certificates will be renewed daily at 2:00 AM (with random delay)"
    
    # Show timer status
    systemctl status certbot-renew.timer
}

# Function to check renewal hook
check_renewal_hook() {
    print_status "Checking renewal hook configuration..."
    echo
    
    HOOK_PATH="/etc/letsencrypt/renewal-hooks/post/postfix-ssl-renew.sh"
    
    if [[ -f "$HOOK_PATH" ]]; then
        print_success "Renewal hook found: $HOOK_PATH"
        echo
        print_status "Renewal hook contents:"
        cat "$HOOK_PATH"
        echo
        
        if [[ -x "$HOOK_PATH" ]]; then
            print_success "Renewal hook is executable"
        else
            print_warning "Renewal hook is not executable, fixing..."
            chmod +x "$HOOK_PATH"
        fi
    else
        print_warning "Renewal hook not found at $HOOK_PATH"
        print_status "You may need to run the main installation script first"
    fi
}

# Function to verify Postfix SSL configuration
verify_postfix_ssl() {
    print_status "Verifying Postfix SSL configuration..."
    echo
    
    # Check if SSL configuration is in main.cf
    if grep -q "smtpd_tls_cert_file" /etc/postfix/main.cf; then
        print_success "SSL configuration found in Postfix main.cf"
        
        # Show SSL settings
        echo
        print_status "Current SSL settings:"
        postconf | grep -E "(smtpd_tls_cert_file|smtpd_tls_key_file|smtpd_tls_security_level)"
    else
        print_warning "SSL configuration not found in Postfix main.cf"
    fi
    
    # Check if SSL ports are configured in master.cf
    if grep -q ":465" /etc/postfix/master.cf; then
        print_success "SSL port 465 configured in master.cf"
    else
        print_warning "SSL port 465 not configured in master.cf"
    fi
}

# Function to show renewal logs
show_renewal_logs() {
    print_status "Showing recent certbot renewal logs..."
    echo
    
    if [[ -f "/var/log/letsencrypt/letsencrypt.log" ]]; then
        tail -n 50 /var/log/letsencrypt/letsencrypt.log
    else
        print_warning "Certbot log file not found"
    fi
    
    echo
    print_status "Recent systemd logs for certbot:"
    journalctl -u certbot-renew.service -n 20 2>/dev/null || print_warning "No certbot systemd logs found"
}

# Function to show help
show_help() {
    echo "Certbot Renewal Management Script for Postfix SSL"
    echo
    echo "Usage: $0 [COMMAND]"
    echo
    echo "Commands:"
    echo "  status     - Show certificate status and information"
    echo "  test       - Test renewal process (dry run)"
    echo "  renew      - Perform actual certificate renewal"
    echo "  auto       - Set up automatic renewal with systemd timer"
    echo "  hook       - Check renewal hook configuration"
    echo "  verify     - Verify Postfix SSL configuration"
    echo "  logs       - Show renewal logs"
    echo "  help       - Show this help message"
    echo
    echo "Examples:"
    echo "  sudo $0 status    # Check certificate status"
    echo "  sudo $0 test      # Test renewal without making changes"
    echo "  sudo $0 renew     # Actually renew certificates"
    echo "  sudo $0 auto      # Set up automatic daily renewal"
}

# Main execution
main() {
    check_root
    
    case "${1:-help}" in
        "status")
            show_certificate_status
            ;;
        "test")
            test_renewal
            ;;
        "renew")
            perform_renewal
            ;;
        "auto")
            setup_automatic_renewal
            ;;
        "hook")
            check_renewal_hook
            ;;
        "verify")
            verify_postfix_ssl
            ;;
        "logs")
            show_renewal_logs
            ;;
        "help"|*)
            show_help
            ;;
    esac
}

# Run main function with all arguments
main "$@" 