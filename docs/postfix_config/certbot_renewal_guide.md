# Certbot Certificate Renewal Guide

This guide covers how certbot handles automatic certificate renewal for your Postfix SSL setup.

## 🔄 How Certbot Renewal Works

### **Automatic Renewal Setup**
The installation script automatically configures:

1. **Renewal Hook**: `/etc/letsencrypt/renewal-hooks/post/postfix-ssl-renew.sh`
2. **Systemd Timer**: Daily renewal at 2:00 AM with random delay
3. **Postfix Integration**: Automatic reload after renewal

### **Renewal Process**
```bash
# Certbot checks certificates daily
certbot renew --quiet --agree-tos

# If renewal is needed:
# 1. Obtains new certificate
# 2. Runs renewal hook
# 3. Reloads Postfix service
```

## 🛠️ Management Commands

### **Check Certificate Status**
```bash
sudo ./manage_certbot_renewal.sh status
```

### **Test Renewal (Dry Run)**
```bash
sudo ./manage_certbot_renewal.sh test
```

### **Perform Manual Renewal**
```bash
sudo ./manage_certbot_renewal.sh renew
```

### **Set Up Automatic Renewal**
```bash
sudo ./manage_certbot_renewal.sh auto
```

### **Verify Configuration**
```bash
sudo ./manage_certbot_renewal.sh verify
```

### **Check Renewal Logs**
```bash
sudo ./manage_certbot_renewal.sh logs
```

## 📋 Manual Renewal Commands

### **Check Certificates**
```bash
certbot certificates
```

### **Test Renewal**
```bash
certbot renew --dry-run
```

### **Force Renewal**
```bash
certbot renew --force-renewal
```

### **Renew Specific Domain**
```bash
certbot renew --cert-name mail.dripemails.org
```

## 🔧 Systemd Timer Management

### **Check Timer Status**
```bash
systemctl status certbot-renew.timer
```

### **Enable Timer**
```bash
systemctl enable certbot-renew.timer
systemctl start certbot-renew.timer
```

### **Disable Timer**
```bash
systemctl stop certbot-renew.timer
systemctl disable certbot-renew.timer
```

### **View Timer Logs**
```bash
journalctl -u certbot-renew.service
```

## 📊 Monitoring Renewal

### **Check Next Renewal**
```bash
systemctl list-timers certbot-renew.timer
```

### **View Certificate Expiry**
```bash
openssl x509 -in /etc/letsencrypt/live/mail.dripemails.org/fullchain.pem -text -noout | grep "Not After"
```

### **Monitor Renewal Logs**
```bash
tail -f /var/log/letsencrypt/letsencrypt.log
```

## 🚨 Troubleshooting

### **Renewal Fails**
```bash
# Check certbot logs
sudo tail -n 50 /var/log/letsencrypt/letsencrypt.log

# Test renewal manually
sudo certbot renew --dry-run

# Check Postfix status
sudo systemctl status postfix
```

### **Postfix Won't Reload**
```bash
# Check Postfix configuration
sudo postfix check

# View Postfix logs
sudo journalctl -u postfix -n 20

# Manual reload
sudo systemctl reload postfix
```

### **Certificate Not Found**
```bash
# List all certificates
sudo certbot certificates

# Check certificate files
sudo ls -la /etc/letsencrypt/live/*/

# Verify certificate validity
sudo openssl x509 -in /etc/letsencrypt/live/mail.dripemails.org/fullchain.pem -text -noout
```

## 🔒 Security Notes

- Certificates auto-renew 30 days before expiry
- Renewal hook sets proper permissions (644/600)
- Postfix reloads automatically after renewal
- Failed renewals are logged for monitoring

## 📅 Renewal Schedule

- **Daily Check**: 2:00 AM with 12-hour random delay
- **Renewal Window**: 30 days before expiry
- **Retry Logic**: Automatic retry on failure
- **Notification**: Logs to systemd journal

## 🎯 Best Practices

1. **Test Regularly**: Run `--dry-run` monthly
2. **Monitor Logs**: Check renewal logs weekly
3. **Backup Configuration**: Keep Postfix config backups
4. **Verify Integration**: Test SSL connections after renewal
5. **Document Changes**: Note any manual interventions

## 📞 Quick Commands Reference

```bash
# Full status check
sudo ./manage_certbot_renewal.sh status

# Test everything works
sudo ./manage_certbot_renewal.sh test

# Manual renewal if needed
sudo ./manage_certbot_renewal.sh renew

# Set up automatic renewal
sudo ./manage_certbot_renewal.sh auto

# Troubleshoot issues
sudo ./manage_certbot_renewal.sh logs
```

This setup ensures your SSL certificates are always up-to-date and Postfix automatically uses the latest certificates without manual intervention. 
