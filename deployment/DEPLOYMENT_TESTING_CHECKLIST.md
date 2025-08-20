# Deployment Testing and Verification Checklist

This comprehensive checklist ensures that all deployment components are properly tested and verified before going live.

## Pre-Deployment Testing

### ✅ Environment Validation

- [ ] **Environment Variables**
  - [ ] All required variables are set in `.env`
  - [ ] SECRET_KEY is generated and secure
  - [ ] DATABASE_URL is correct and accessible
  - [ ] SENTRY_DSN is configured (if using error tracking)
  - [ ] SSL certificates are valid and properly configured

- [ ] **Dependencies**
  - [ ] `requirements.txt` is up to date
  - [ ] All Python packages install without errors
  - [ ] System dependencies (MySQL, Nginx) are installed
  - [ ] Virtual environment is properly configured

- [ ] **File Permissions**
  - [ ] Application files have correct ownership (`doi-app:doi-app`)
  - [ ] Log directories are writable
  - [ ] Upload directories have proper permissions
  - [ ] SSL certificates are readable by Nginx

### ✅ Database Testing

- [ ] **Database Connection**
  - [ ] Database server is running and accessible
  - [ ] Connection credentials are valid
  - [ ] Database exists and has proper charset (utf8mb4)
  - [ ] Database user has necessary privileges

- [ ] **Migration Testing**
  - [ ] Database migrations run successfully
  - [ ] All required tables are created
  - [ ] Indexes and constraints are properly applied
  - [ ] Initial data (if any) is loaded correctly

- [ ] **Database Performance**
  - [ ] Connection pooling is configured
  - [ ] Query performance is acceptable
  - [ ] Database backup/restore procedures work

### ✅ Application Testing

- [ ] **Flask Application**
  - [ ] Application starts without errors
  - [ ] All blueprints are registered correctly
  - [ ] Static files are served properly
  - [ ] Template rendering works
  - [ ] Session management functions correctly

- [ ] **Authentication System**
  - [ ] User login/logout works
  - [ ] Password hashing is functional
  - [ ] Session security is enforced
  - [ ] Admin user management is accessible
  - [ ] Permission-based access control works

- [ ] **Core Functionality**
  - [ ] Dashboard displays without errors
  - [ ] Navigation works on all devices
  - [ ] Health check endpoint responds correctly
  - [ ] Error pages display appropriately

## Deployment Testing

### ✅ Gunicorn Configuration

- [ ] **Service Configuration**
  - [ ] Gunicorn starts with correct configuration
  - [ ] Worker processes spawn correctly (4 workers)
  - [ ] Process management works (start/stop/restart)
  - [ ] Application logs to configured location
  - [ ] Systemd service is properly configured

- [ ] **Performance Testing**
  - [ ] Application handles expected load
  - [ ] Response times are acceptable (<1s for most requests)
  - [ ] Memory usage is within limits
  - [ ] CPU usage is reasonable under load

### ✅ Nginx Configuration

- [ ] **Reverse Proxy**
  - [ ] Nginx forwards requests to Gunicorn correctly
  - [ ] Static files are served directly by Nginx
  - [ ] Upload directory access works (if applicable)
  - [ ] Proper error page handling

- [ ] **SSL/HTTPS**
  - [ ] SSL certificate is valid and trusted
  - [ ] HTTP to HTTPS redirect works
  - [ ] SSL configuration passes security tests
  - [ ] Certificate auto-renewal is configured

- [ ] **Security Headers**
  - [ ] All security headers are present
  - [ ] Rate limiting is functional
  - [ ] Content Security Policy is appropriate
  - [ ] HSTS header is set correctly

### ✅ Health Check and Monitoring

- [ ] **Health Check Endpoint**
  - [ ] `/health` endpoint returns valid JSON
  - [ ] Database connectivity check works
  - [ ] System metrics are collected
  - [ ] Response time is under 5 seconds
  - [ ] Proper HTTP status codes (200/503)

- [ ] **Logging System**
  - [ ] Application logs are written correctly
  - [ ] Log rotation works as expected
  - [ ] Log compression runs without errors
  - [ ] Log retention policy is enforced
  - [ ] Request correlation IDs are present

- [ ] **Error Tracking**
  - [ ] Sentry integration captures errors (if configured)
  - [ ] Error notifications are sent appropriately
  - [ ] Performance monitoring data is collected
  - [ ] User context is properly tracked

### ✅ System Integration

- [ ] **Service Dependencies**
  - [ ] MySQL service starts automatically
  - [ ] Nginx service starts automatically
  - [ ] DOI application service starts automatically
  - [ ] Services restart after system reboot

- [ ] **Network Configuration**
  - [ ] Firewall allows necessary ports (80, 443)
  - [ ] Internal communication works (app ↔ database)
  - [ ] External connectivity is functional
  - [ ] DNS resolution works correctly

## Production Verification

### ✅ Functional Testing

Run through all critical user workflows:

- [ ] **User Authentication**
  - [ ] Admin can log in successfully
  - [ ] Invalid credentials are rejected
  - [ ] Session timeout works correctly
  - [ ] Logout clears session properly

- [ ] **Admin Functions**
  - [ ] User management panel is accessible
  - [ ] New users can be created
  - [ ] User permissions are enforced
  - [ ] Dashboard statistics display correctly

- [ ] **System Functions**
  - [ ] Health checks pass consistently
  - [ ] Log viewing and analysis work
  - [ ] Monitoring dashboards function
  - [ ] Alert systems trigger appropriately

### ✅ Security Testing

- [ ] **Authentication Security**
  - [ ] Password policies are enforced
  - [ ] Session security is maintained
  - [ ] CSRF protection is active
  - [ ] XSS protection is functional

- [ ] **Network Security**
  - [ ] HTTPS is enforced
  - [ ] Security headers are present
  - [ ] Rate limiting prevents abuse
  - [ ] Unnecessary ports are closed

- [ ] **Data Security**
  - [ ] Sensitive data is not logged
  - [ ] Database connections are encrypted
  - [ ] File uploads are validated
  - [ ] Error messages don't leak information

### ✅ Performance Testing

- [ ] **Load Testing**
  - [ ] Application handles concurrent users
  - [ ] Database performance under load
  - [ ] Memory usage remains stable
  - [ ] Response times are consistent

- [ ] **Resource Monitoring**
  - [ ] CPU usage is within expected ranges
  - [ ] Memory consumption is reasonable
  - [ ] Disk space is sufficient
  - [ ] Network bandwidth is adequate

## Post-Deployment Verification

### ✅ 24-Hour Check

After 24 hours of running:

- [ ] **System Stability**
  - [ ] All services remain running
  - [ ] No critical errors in logs
  - [ ] Memory leaks haven't occurred
  - [ ] Database connections are stable

- [ ] **Monitoring Data**
  - [ ] Health checks consistently pass
  - [ ] Performance metrics are normal
  - [ ] Log rotation has occurred
  - [ ] Monitoring alerts function

- [ ] **User Experience**
  - [ ] Application remains responsive
  - [ ] No reported user issues
  - [ ] Authentication continues working
  - [ ] All features function correctly

### ✅ Weekly Check

After one week of operation:

- [ ] **Long-term Stability**
  - [ ] System resources remain stable
  - [ ] Log files are properly rotated
  - [ ] Database performance is consistent
  - [ ] SSL certificate is valid

- [ ] **Backup and Recovery**
  - [ ] Automated backups are working
  - [ ] Backup restoration has been tested
  - [ ] Disaster recovery procedures verified
  - [ ] Documentation is up to date

## Testing Commands and Scripts

### Manual Testing Commands

```bash
# Test application startup
sudo systemctl start doi-app
sudo systemctl status doi-app

# Test health endpoint
curl -f https://your-domain.com/health | jq .

# Test SSL configuration
openssl s_client -connect your-domain.com:443 -servername your-domain.com

# Test database connectivity
mysql -h $DB_HOST -u $DB_USER -p$DB_PASSWORD $DB_NAME -e "SELECT 1"

# Test Nginx configuration
sudo nginx -t
curl -I https://your-domain.com/

# Test log rotation
sudo ./deployment/scripts/log-maintenance.sh rotate

# Test monitoring scripts
sudo -u doi-app ./scripts/system-monitor.sh
sudo -u doi-app ./scripts/health-monitor.sh
```

### Automated Testing Script

```bash
#!/bin/bash
# deployment-test.sh

echo "Running deployment verification tests..."

# Test 1: Service Status
echo "Testing service status..."
systemctl is-active --quiet doi-app || echo "❌ DOI app service not running"
systemctl is-active --quiet nginx || echo "❌ Nginx service not running"
systemctl is-active --quiet mysql || echo "❌ MySQL service not running"

# Test 2: Health Check
echo "Testing health endpoint..."
if curl -f -s https://your-domain.com/health >/dev/null; then
    echo "✅ Health check passed"
else
    echo "❌ Health check failed"
fi

# Test 3: Database Connection
echo "Testing database connection..."
if mysql -h $DB_HOST -u $DB_USER -p$DB_PASSWORD $DB_NAME -e "SELECT 1" >/dev/null 2>&1; then
    echo "✅ Database connection successful"
else
    echo "❌ Database connection failed"
fi

# Test 4: SSL Certificate
echo "Testing SSL certificate..."
if openssl s_client -connect your-domain.com:443 -servername your-domain.com </dev/null 2>/dev/null | grep -q "Verify return code: 0"; then
    echo "✅ SSL certificate valid"
else
    echo "❌ SSL certificate invalid"
fi

# Test 5: Log System
echo "Testing log system..."
if [ -f "/opt/doi-app/logs/doi_app.log" ] && [ -w "/opt/doi-app/logs/" ]; then
    echo "✅ Log system functional"
else
    echo "❌ Log system issues"
fi

echo "Deployment verification completed."
```

## Troubleshooting Common Issues

### Application Won't Start

**Symptoms**: Service fails to start or crashes immediately

**Debugging steps**:
```bash
# Check service status and logs
sudo systemctl status doi-app -l
sudo journalctl -u doi-app -f

# Check application logs
tail -f /opt/doi-app/logs/doi_app.log

# Check configuration
sudo -u doi-app python -m flask --app app check-config

# Verify environment
sudo -u doi-app env | grep -E "SECRET_KEY|DATABASE_URL"
```

### Database Connection Issues

**Symptoms**: Health check fails, database errors in logs

**Debugging steps**:
```bash
# Test database connection
mysql -h $DB_HOST -u $DB_USER -p$DB_PASSWORD $DB_NAME

# Check database service
sudo systemctl status mysql

# Verify database configuration
grep DATABASE_URL .env

# Check database permissions
mysql -u root -p -e "SHOW GRANTS FOR 'doi_user'@'localhost'"
```

### SSL Certificate Problems

**Symptoms**: Browser warnings, HTTPS not working

**Debugging steps**:
```bash
# Check certificate validity
openssl x509 -in /etc/letsencrypt/live/your-domain.com/cert.pem -text -noout

# Test SSL configuration
./deployment/scripts/ssl-monitor.sh your-domain.com

# Check Nginx SSL configuration
sudo nginx -t
grep ssl /etc/nginx/sites-available/doi-app
```

### Performance Issues

**Symptoms**: Slow response times, high resource usage

**Debugging steps**:
```bash
# Check system resources
htop
df -h
free -m

# Monitor application performance
./scripts/monitoring-dashboard.sh

# Check database performance
mysql -e "SHOW PROCESSLIST"

# Review application logs for slow operations
grep "slow\|timeout" /opt/doi-app/logs/doi_app.log
```

## Rollback Procedures

If critical issues are discovered after deployment:

### 1. Immediate Rollback

```bash
# Stop the problematic service
sudo systemctl stop doi-app

# Restore from backup (if available)
sudo systemctl stop mysql
sudo mysql < /path/to/database/backup.sql
sudo systemctl start mysql

# Revert configuration files
sudo cp /etc/nginx/sites-available/doi-app.backup /etc/nginx/sites-available/doi-app
sudo nginx -t && sudo systemctl reload nginx

# Start with previous known-good configuration
sudo systemctl start doi-app
```

### 2. Gradual Recovery

```bash
# Enable maintenance mode (if implemented)
touch /opt/doi-app/MAINTENANCE_MODE

# Fix issues while in maintenance mode
# Apply fixes, test thoroughly

# Disable maintenance mode
rm /opt/doi-app/MAINTENANCE_MODE

# Monitor closely for issues
```

## Final Deployment Sign-off

Complete this checklist before considering deployment successful:

- [ ] All automated tests pass
- [ ] Manual functional testing completed
- [ ] Security testing shows no critical issues
- [ ] Performance metrics are within acceptable ranges
- [ ] Monitoring and alerting are functional
- [ ] Backup and recovery procedures tested
- [ ] Documentation is updated
- [ ] Team is notified of successful deployment
- [ ] Rollback procedures are documented and tested
- [ ] 24-hour monitoring period completed successfully

**Deployment Sign-off**: 
- Date: ________________
- Deployed by: ________________
- Approved by: ________________
- Issues noted: ________________