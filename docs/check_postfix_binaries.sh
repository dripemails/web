#!/bin/bash

# Check Postfix binaries
set -e

print_status() {
    echo -e "\033[0;34m[INFO]\033[0m $1"
}

print_success() {
    echo -e "\033[0;32m[SUCCESS]\033[0m $1"
}

print_error() {
    echo -e "\033[0;31m[ERROR]\033[0m $1"
}

print_status "Checking Postfix binaries..."

echo "=== /usr/lib/postfix/ ==="
ls -la /usr/lib/postfix/

echo ""
echo "=== /usr/lib/postfix/sbin/ ==="
ls -la /usr/lib/postfix/sbin/

echo ""
echo "=== /usr/sbin/ (Postfix commands) ==="
ls -la /usr/sbin/postfix*

echo ""
print_status "Checking specific binaries..."

# Check if binaries exist in sbin
if [ -f "/usr/lib/postfix/sbin/smtpd" ]; then
    print_success "smtpd exists in /usr/lib/postfix/sbin/"
else
    print_error "smtpd missing from /usr/lib/postfix/sbin/"
fi

if [ -f "/usr/lib/postfix/sbin/qmgr" ]; then
    print_success "qmgr exists in /usr/lib/postfix/sbin/"
else
    print_error "qmgr missing from /usr/lib/postfix/sbin/"
fi

if [ -f "/usr/lib/postfix/sbin/pickup" ]; then
    print_success "pickup exists in /usr/lib/postfix/sbin/"
else
    print_error "pickup missing from /usr/lib/postfix/sbin/"
fi

if [ -f "/usr/lib/postfix/sbin/master" ]; then
    print_success "master exists in /usr/lib/postfix/sbin/"
else
    print_error "master missing from /usr/lib/postfix/sbin/"
fi

echo ""
print_status "Checking symlinks..."
ls -la /usr/lib/postfix/master
ls -la /usr/lib/postfix/postfix-script 