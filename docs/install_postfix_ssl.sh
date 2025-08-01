#!/bin/sh

# Postfix SSL Certificate Installation Script for Ubuntu Server 24.04.1
# This script uses certbot to obtain and configure SSL certificates for Postfix
# Run this script as root: sudo ./install_postfix_ssl.sh

set -e  # Exit on any error

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
    if [ "$(id -u)" -ne 0 ]; then
        print_error "This script must be run as root (use sudo)"
        exit 1
    fi
}

# Function to check if domain is provided
check_domain() {
    if [ -z "$DOMAIN" ]; then
        print_error "Domain name is required. Usage: $0 <domain>"
        print_status "Example: $0 mail.dripemails.org"
        exit 1
    fi
}

# Function to check system requirements
check_requirements() {
    print_status "Checking system requirements..."
    
    # Check if running Ubuntu 24.04
    if ! grep -q "Ubuntu 24.04" /etc/os-release; then
        print_warning "This script is designed for Ubuntu 24.04.1. You're running:"
        cat /etc/os-release | grep PRETTY_NAME
    fi
    
    # Check if Postfix is installed
    if ! command -v postfix > /dev/null 2>&1; then
        print_error "Postfix is not installed. Please install it first:"
        print_status "sudo apt update && sudo apt install postfix"
        exit 1
    fi
    
    # Check if certbot is installed
    if ! command -v certbot > /dev/null 2>&1; then
        print_status "Installing certbot..."
        apt update
        apt install -y certbot
    fi
    
    print_success "System requirements check completed"
}

# Function to backup Postfix configuration
backup_config() {
    print_status "Backing up Postfix configuration..."
    
    BACKUP_DIR="/etc/postfix/backup_$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$BACKUP_DIR"
    
    cp /etc/postfix/main.cf "$BACKUP_DIR/"
    cp /etc/postfix/master.cf "$BACKUP_DIR/"
    
    print_success "Configuration backed up to $BACKUP_DIR"
}

# Function to obtain SSL certificate
obtain_certificate() {
    print_status "Obtaining SSL certificate for $DOMAIN..."
    
    # Stop Postfix temporarily
    systemctl stop postfix
    
    # Obtain certificate using certbot
    if certbot certonly --standalone -d "$DOMAIN" --non-interactive --agree-tos --email admin@"$DOMAIN"; then
        print_success "SSL certificate obtained successfully"
    else
        print_error "Failed to obtain SSL certificate"
        systemctl start postfix
        exit 1
    fi
}

# Function to configure Postfix with SSL
configure_postfix_ssl() {
    print_status "Configuring Postfix with SSL certificates..."
    
    # SSL certificate paths
    CERT_PATH="/etc/letsencrypt/live/$DOMAIN/fullchain.pem"
    KEY_PATH="/etc/letsencrypt/live/$DOMAIN/privkey.pem"
    
    # Verify certificates exist
    if [ ! -f "$CERT_PATH" ] || [ ! -f "$KEY_PATH" ]; then
        print_error "SSL certificates not found at expected locations"
        exit 1
    fi
    
    # Set proper permissions for Postfix to read certificates
    chmod 644 "$CERT_PATH"
    chmod 600 "$KEY_PATH"
    chown root:root "$CERT_PATH" "$KEY_PATH"
    
    # Configure Postfix main.cf for SSL
    cat >> /etc/postfix/main.cf << EOF

# SSL Configuration for $DOMAIN
smtpd_tls_cert_file = $CERT_PATH
smtpd_tls_key_file = $KEY_PATH
smtpd_tls_security_level = may
smtpd_tls_auth_only = yes
smtpd_tls_protocols = !SSLv2, !SSLv3, !TLSv1, !TLSv1.1
smtpd_tls_mandatory_protocols = !SSLv2, !SSLv3, !TLSv1, !TLSv1.1
smtpd_tls_mandatory_ciphers = high
smtpd_tls_ciphers = high
smtpd_tls_exclude_ciphers = aNULL, DES, 3DES, MD5, DES+MD5, RC4
smtpd_tls_dh1024_param_file = \${config_directory}/dh2048.pem
smtpd_tls_session_cache_database = btree:\${data_directory}/smtpd_scache
smtp_tls_session_cache_database = btree:\${data_directory}/smtp_scache

# Enable TLS for incoming connections
smtpd_tls_received_header = yes
smtpd_tls_loglevel = 1
smtp_tls_loglevel = 1

# Force TLS for authentication
smtpd_tls_auth_only = yes
smtpd_sasl_security_options = noanonymous
smtpd_sasl_tls_security_options = noanonymous

# TLS for outgoing connections
smtp_tls_security_level = may
smtp_tls_cert_file = $CERT_PATH
smtp_tls_key_file = $KEY_PATH
smtp_tls_protocols = !SSLv2, !SSLv3, !TLSv1, !TLSv1.1
smtp_tls_mandatory_protocols = !SSLv2, !SSLv3, !TLSv1, !TLSv1.1
smtp_tls_mandatory_ciphers = high
smtp_tls_ciphers = high
smtp_tls_exclude_ciphers = aNULL, DES, 3DES, MD5, DES+MD5, RC4
EOF
    
    # Generate DH parameters for better security
    print_status "Generating DH parameters (this may take a while)..."
    openssl dhparam -out /etc/postfix/dh2048.pem 2048
    
    # Set proper permissions
    chmod 644 /etc/postfix/dh2048.pem
    chown root:root /etc/postfix/dh2048.pem
    
    print_success "Postfix SSL configuration completed"
}

# Function to configure master.cf for SSL ports
configure_master_ssl() {
    print_status "Configuring Postfix master.cf for SSL ports..."
    
    # Backup master.cf
    cp /etc/postfix/master.cf /etc/postfix/master.cf.backup
    
    # Add SSL configuration to master.cf
    cat >> /etc/postfix/master.cf << EOF

# SSL SMTP on port 465
465      inet  n       -       n       -       -       smtpd
  -o syslog_name=postfix/smtps
  -o smtpd_tls_wrappermode=yes
  -o smtpd_sasl_auth_enable=yes
  -o smtpd_reject_unlisted_recipient=no
  -o smtpd_client_restrictions=\$mua_client_restrictions
  -o smtpd_helo_restrictions=\$mua_helo_restrictions
  -o smtpd_sender_restrictions=\$mua_sender_restrictions
  -o smtpd_recipient_restrictions=
  -o smtpd_relay_restrictions=\$mua_relay_restrictions
  -o smtpd_authentication_filter=permit_sasl_authenticated,reject
  -o smtpd_tls_security_level=encrypt
  -o smtpd_tls_wrappermode=yes
  -o smtpd_sasl_security_options=noanonymous,noplaintext
  -o smtpd_sasl_local_domain=\$myhostname
  -o smtpd_sasl_auth_enable=yes
  -o smtpd_sasl_type=dovecot
  -o smtpd_sasl_path=private/auth
  -o smtpd_sasl_authenticated_header=yes
  -o smtpd_tls_cert_file=$CERT_PATH
  -o smtpd_tls_key_file=$KEY_PATH
  -o smtpd_tls_security_level=encrypt
  -o smtpd_tls_protocols=!SSLv2,!SSLv3,!TLSv1,!TLSv1.1
  -o smtpd_tls_mandatory_protocols=!SSLv2,!SSLv3,!TLSv1,!TLSv1.1
  -o smtpd_tls_mandatory_ciphers=high
  -o smtpd_tls_ciphers=high
  -o smtpd_tls_exclude_ciphers=aNULL,DES,3DES,MD5,DES+MD5,RC4
  -o smtpd_tls_dh1024_param_file=\${config_directory}/dh2048.pem
  -o smtpd_tls_session_cache_database=btree:\${data_directory}/smtpd_scache
  -o smtpd_tls_received_header=yes
  -o smtpd_tls_loglevel=1
  -o smtpd_tls_auth_only=yes
  -o smtpd_sasl_security_options=noanonymous
  -o smtpd_sasl_tls_security_options=noanonymous
EOF
    
    print_success "Master.cf SSL configuration completed"
}

# Function to configure firewall
configure_firewall() {
    print_status "Configuring firewall for SMTP ports..."
    
    # Check if ufw is active
    if ufw status | grep -q "Status: active"; then
        ufw allow 25/tcp   # SMTP
        ufw allow 465/tcp  # SMTPS
        ufw allow 587/tcp  # Submission
        print_success "Firewall rules added for SMTP ports"
    else
        print_warning "UFW is not active. Please configure firewall manually:"
        print_status "sudo ufw allow 25/tcp   # SMTP"
        print_status "sudo ufw allow 465/tcp  # SMTPS"
        print_status "sudo ufw allow 587/tcp  # Submission"
    fi
}

# Function to test configuration
test_configuration() {
    print_status "Testing Postfix configuration..."
    
    # Test configuration syntax
    if postconf -n | grep -q "smtpd_tls_cert_file"; then
        print_success "SSL configuration found in Postfix"
    else
        print_error "SSL configuration not found in Postfix"
        exit 1
    fi
    
    # Test configuration validity
    if postfix check; then
        print_success "Postfix configuration is valid"
    else
        print_error "Postfix configuration has errors"
        exit 1
    fi
}

# Function to restart services
restart_services() {
    print_status "Restarting Postfix service..."
    
    systemctl restart postfix
    
    if systemctl is-active --quiet postfix; then
        print_success "Postfix service is running"
    else
        print_error "Postfix service failed to start"
        systemctl status postfix
        exit 1
    fi
}

# Function to create renewal script
create_renewal_script() {
    print_status "Creating certificate renewal script..."
    
    cat > /etc/letsencrypt/renewal-hooks/post/postfix-ssl-renew.sh << 'EOF'
#!/bin/bash

# Postfix SSL Certificate Renewal Script
# This script is called by certbot after certificate renewal

set -e

DOMAIN="$1"
CERT_PATH="/etc/letsencrypt/live/$DOMAIN/fullchain.pem"
KEY_PATH="/etc/letsencrypt/live/$DOMAIN/privkey.pem"

# Set proper permissions
chmod 644 "$CERT_PATH"
chmod 600 "$KEY_PATH"
chown root:root "$CERT_PATH" "$KEY_PATH"

# Reload Postfix to pick up new certificates
systemctl reload postfix

echo "Postfix SSL certificates renewed and reloaded for $DOMAIN"
EOF
    
    chmod +x /etc/letsencrypt/renewal-hooks/post/postfix-ssl-renew.sh
    
    print_success "Renewal script created"
}

# Function to display final information
display_final_info() {
    print_success "SSL certificate installation completed!"
    echo
    print_status "Configuration Summary:"
    echo "  Domain: $DOMAIN"
    echo "  Certificate: $CERT_PATH"
    echo "  Private Key: $KEY_PATH"
    echo "  SSL Port: 465 (SMTPS)"
    echo "  Standard Port: 25 (SMTP)"
    echo "  Submission Port: 587 (SMTP with STARTTLS)"
    echo
    print_status "Next Steps:"
    echo "  1. Test SSL connection: openssl s_client -connect $DOMAIN:465"
    echo "  2. Check Postfix logs: journalctl -u postfix -f"
    echo "  3. Test email sending with SSL"
    echo "  4. Set up automatic renewal: certbot renew --dry-run"
    echo
    print_status "Certificate will auto-renew every 60 days"
    print_status "Renewal script: /etc/letsencrypt/renewal-hooks/post/postfix-ssl-renew.sh"
}

# Main execution
main() {
    echo "=========================================="
    echo "  Postfix SSL Certificate Installation"
    echo "  Ubuntu Server 24.04.1"
    echo "=========================================="
    echo
    
    # Get domain from command line argument
    DOMAIN="$1"
    
    # Run all functions
    check_root
    check_domain
    check_requirements
    backup_config
    obtain_certificate
    configure_postfix_ssl
    configure_master_ssl
    configure_firewall
    test_configuration
    restart_services
    create_renewal_script
    display_final_info
}

# Run main function with all arguments
main "$@" 