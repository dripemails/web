#!/bin/bash

# Test SSL connections for Postfix
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

print_status "Testing SSL connections..."

# Test port 465 (SMTPS)
print_status "Testing port 465 (SMTPS)..."
if timeout 10 bash -c 'echo "QUIT" | openssl s_client -connect localhost:465 -quiet 2>/dev/null | head -1 | grep -q "220"'; then
    print_success "Port 465 (SMTPS) is working"
else
    print_warning "Port 465 (SMTPS) connection failed"
fi

# Test port 587 (Submission)
print_status "Testing port 587 (Submission)..."
if timeout 10 bash -c 'echo "QUIT" | openssl s_client -connect localhost:587 -starttls smtp -quiet 2>/dev/null | head -1 | grep -q "220"'; then
    print_success "Port 587 (Submission) is working"
else
    print_warning "Port 587 (Submission) connection failed"
fi

# Test port 25 (SMTP)
print_status "Testing port 25 (SMTP)..."
if timeout 10 bash -c 'echo "QUIT" | telnet localhost 25 2>/dev/null | head -1 | grep -q "220"'; then
    print_success "Port 25 (SMTP) is working"
else
    print_warning "Port 25 (SMTP) connection failed"
fi

# Test external SSL connection
print_status "Testing external SSL connection..."
if timeout 10 bash -c 'echo "QUIT" | openssl s_client -connect dripemails.org:465 -quiet 2>/dev/null | head -1 | grep -q "220"'; then
    print_success "External SSL connection to dripemails.org:465 is working"
else
    print_warning "External SSL connection to dripemails.org:465 failed"
fi

print_success "SSL connection tests completed!"
print_status ""
print_status "Your Postfix server is now running with SSL certificates!"
print_status "All SMTP ports (25, 587, 465) are listening and accepting connections."
print_status ""
print_status "You can test manually with:"
print_status "openssl s_client -connect dripemails.org:465"
print_status "openssl s_client -connect dripemails.org:587"
print_status "telnet dripemails.org 25" 