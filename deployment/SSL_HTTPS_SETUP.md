# SSL Certificate and HTTPS Configuration

This document provides comprehensive instructions for setting up SSL/TLS certificates and configuring HTTPS for the DOI Management Application.

## Prerequisites

- Domain name pointing to your server
- Server with public IP address
- Nginx installed and configured
- DNS records properly configured

## Quick Setup Guide

### 1. Automatic Setup with Let's Encrypt (Recommended)

```bash
# Install Certbot
sudo apt update
sudo apt install certbot python3-certbot-nginx

# Generate certificate for your domain
sudo certbot --nginx -d your-domain.com -d www.your-domain.com

# Test automatic renewal
sudo certbot renew --dry-run
```

### 2. Manual Configuration

Use the provided setup script:

```bash
./deployment/scripts/setup-ssl.sh your-domain.com
```

## Detailed Configuration Steps

### Step 1: Install Certbot

Certbot is the official client for Let's Encrypt certificates:

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install certbot python3-certbot-nginx

# CentOS/RHEL
sudo yum install certbot python3-certbot-nginx

# Or using snap (universal)
sudo snap install --classic certbot
sudo ln -s /snap/bin/certbot /usr/bin/certbot
```

### Step 2: Configure Domain Name

Update your Nginx configuration with your actual domain name:

```bash
# Edit the Nginx configuration
sudo nano /etc/nginx/sites-available/doi-app

# Replace 'your-domain.com' with your actual domain
# Example: example.com, doi.example.org, etc.
```

### Step 3: Test Nginx Configuration

Before obtaining SSL certificates:

```bash
# Test Nginx configuration
sudo nginx -t

# Reload Nginx if test passes
sudo systemctl reload nginx
```

### Step 4: Obtain SSL Certificate

#### Option A: Interactive Mode (Recommended for first-time setup)

```bash
sudo certbot --nginx -d your-domain.com -d www.your-domain.com
```

This will:
- Automatically detect your Nginx configuration
- Generate certificates
- Update Nginx configuration for HTTPS
- Set up HTTP to HTTPS redirects

#### Option B: Non-Interactive Mode (For automation)

```bash
sudo certbot --nginx \
  --non-interactive \
  --agree-tos \
  --email your-email@domain.com \
  --domains your-domain.com,www.your-domain.com \
  --redirect
```

### Step 5: Verify SSL Configuration

#### Test SSL Certificate

```bash
# Test SSL certificate
openssl s_client -connect your-domain.com:443 -servername your-domain.com

# Check certificate expiration
echo | openssl s_client -servername your-domain.com -connect your-domain.com:443 2>/dev/null | openssl x509 -noout -dates
```

#### Online SSL Tests

- [SSL Labs SSL Test](https://www.ssllabs.com/ssltest/)
- [SSL Checker](https://www.sslshopper.com/ssl-checker.html)

### Step 6: Set Up Automatic Renewal

Let's Encrypt certificates expire every 90 days. Set up automatic renewal:

```bash
# Test renewal process
sudo certbot renew --dry-run

# Set up cron job for automatic renewal
sudo crontab -e

# Add this line to run renewal twice daily
0 12 * * * /usr/bin/certbot renew --quiet
```

Or use systemd timer (modern approach):

```bash
# Enable automatic renewal
sudo systemctl enable certbot.timer
sudo systemctl start certbot.timer

# Check timer status
sudo systemctl status certbot.timer
```

## Advanced SSL Configuration

### Enhanced Security Settings

The Nginx configuration already includes security best practices:

```nginx
# SSL protocols and ciphers (already in doi-app.conf)
ssl_protocols TLSv1.2 TLSv1.3;
ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384;
ssl_prefer_server_ciphers off;

# Security headers (already configured)
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
```

### OCSP Stapling

Enable OCSP stapling for better performance:

```nginx
# Add to your server block
ssl_stapling on;
ssl_stapling_verify on;
ssl_trusted_certificate /etc/letsencrypt/live/your-domain.com/chain.pem;
resolver 8.8.8.8 8.8.4.4 valid=300s;
resolver_timeout 5s;
```

### Certificate Transparency Monitoring

Monitor your certificates for unauthorized issuance:

- [crt.sh](https://crt.sh/) - Certificate transparency log search
- [Facebook CT Monitor](https://developers.facebook.com/tools/ct/) - Facebook's CT monitoring

## Troubleshooting SSL Issues

### Common Problems and Solutions

#### 1. Certificate Generation Fails

**Problem**: Certbot fails to generate certificate

**Solutions**:
```bash
# Check DNS records
nslookup your-domain.com

# Ensure port 80 is accessible
sudo netstat -tlnp | grep :80

# Check Nginx configuration
sudo nginx -t

# Verify domain ownership
curl -I http://your-domain.com/.well-known/acme-challenge/test
```

#### 2. Mixed Content Errors

**Problem**: Browser shows "mixed content" warnings

**Solution**: Update application URLs to use HTTPS:
```python
# In your environment configuration
APPLICATION_URL=https://your-domain.com
API_BASE_URL=https://your-domain.com/api/v1
```

#### 3. Certificate Not Trusted

**Problem**: Browser shows certificate warnings

**Checks**:
```bash
# Verify certificate chain
openssl s_client -connect your-domain.com:443 -showcerts

# Check certificate details
openssl x509 -in /etc/letsencrypt/live/your-domain.com/cert.pem -text -noout
```

#### 4. Automatic Renewal Fails

**Problem**: Certificate renewal fails in cron

**Debugging**:
```bash
# Test renewal manually
sudo certbot renew --dry-run

# Check renewal logs
sudo tail -f /var/log/letsencrypt/letsencrypt.log

# Verify cron job
sudo crontab -l
```

### Certificate Validation Commands

```bash
# Check certificate expiration
sudo certbot certificates

# Show certificate details
openssl x509 -in /etc/letsencrypt/live/your-domain.com/cert.pem -text -noout

# Validate certificate chain
openssl verify -CAfile /etc/letsencrypt/live/your-domain.com/chain.pem /etc/letsencrypt/live/your-domain.com/cert.pem

# Test SSL connection
openssl s_client -connect your-domain.com:443 -servername your-domain.com
```

## Alternative Certificate Authorities

While Let's Encrypt is recommended, you can also use:

### Commercial CAs
- **DigiCert** - Enterprise certificates
- **GlobalSign** - Wildcard and EV certificates  
- **Comodo/Sectigo** - Budget-friendly options

### Self-Signed Certificates (Development Only)

```bash
# Generate private key
openssl genrsa -out server.key 2048

# Generate certificate signing request
openssl req -new -key server.key -out server.csr

# Generate self-signed certificate
openssl x509 -req -days 365 -in server.csr -signkey server.key -out server.crt
```

## Security Best Practices

### SSL/TLS Configuration

1. **Use Strong Protocols**: Only TLS 1.2 and 1.3
2. **Disable Weak Ciphers**: Use AEAD ciphers when possible
3. **Enable HSTS**: Prevent protocol downgrade attacks
4. **Use OCSP Stapling**: Improve performance and privacy
5. **Monitor Certificate Expiry**: Set up alerts for renewal

### Application Security

1. **Force HTTPS**: Redirect all HTTP traffic to HTTPS
2. **Secure Cookies**: Set secure flag on all cookies
3. **Content Security Policy**: Prevent XSS attacks
4. **Certificate Pinning**: Consider for high-security applications

### Monitoring and Maintenance

```bash
# Create SSL monitoring script
#!/bin/bash
# ssl-monitor.sh

DOMAIN="your-domain.com"
DAYS_WARN=30

# Check certificate expiry
EXPIRY=$(echo | openssl s_client -servername $DOMAIN -connect $DOMAIN:443 2>/dev/null | openssl x509 -noout -dates | grep notAfter | cut -d= -f2)
EXPIRY_EPOCH=$(date -d "$EXPIRY" +%s)
CURRENT_EPOCH=$(date +%s)
DAYS_LEFT=$(( ($EXPIRY_EPOCH - $CURRENT_EPOCH) / 86400 ))

if [ $DAYS_LEFT -lt $DAYS_WARN ]; then
    echo "WARNING: SSL certificate expires in $DAYS_LEFT days"
    # Send notification (email, Slack, etc.)
fi
```

## Integration with DOI Application

### Environment Configuration

Update your `.env` file:

```bash
# SSL/HTTPS Settings
SSL_REDIRECT=True
FORCE_HTTPS=True
SESSION_COOKIE_SECURE=True

# Application URLs (use HTTPS)
APPLICATION_URL=https://your-domain.com
API_BASE_URL=https://your-domain.com/api/v1
```

### Flask Configuration

The application automatically handles HTTPS redirects in production mode when `SSL_REDIRECT=True`.

### Health Check Updates

SSL status is included in the health check endpoint at `/health`.

## Backup and Recovery

### Certificate Backup

```bash
# Backup Let's Encrypt certificates
sudo tar -czf letsencrypt-backup-$(date +%Y%m%d).tar.gz /etc/letsencrypt/

# Store backup securely (encrypted)
gpg --cipher-algo AES256 --compress-algo 1 --s2k-mode 3 --s2k-digest-algo SHA512 --s2k-count 65536 --symmetric letsencrypt-backup-$(date +%Y%m%d).tar.gz
```

### Certificate Recovery

```bash
# Restore from backup
sudo tar -xzf letsencrypt-backup.tar.gz -C /

# Restart Nginx
sudo systemctl restart nginx
```

## Compliance and Regulations

### GDPR Compliance
- Use appropriate TLS versions
- Implement proper data encryption
- Monitor certificate transparency logs

### Industry Standards
- **PCI DSS**: Requires strong encryption for payment processing
- **HIPAA**: Mandates encryption for healthcare data
- **SOX**: Financial data protection requirements

## Support and Resources

### Documentation
- [Let's Encrypt Documentation](https://letsencrypt.org/docs/)
- [Certbot User Guide](https://certbot.eff.org/docs/)
- [Mozilla SSL Configuration Generator](https://ssl-config.mozilla.org/)

### Community Support
- [Let's Encrypt Community](https://community.letsencrypt.org/)
- [Nginx Forums](https://forum.nginx.org/)

### Emergency Contacts
- Document your certificate authority contact information
- Keep backup contact methods for domain registrar
- Maintain emergency SSL certificate replacement procedures