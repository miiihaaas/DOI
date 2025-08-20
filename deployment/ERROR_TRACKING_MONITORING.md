# Error Tracking and Monitoring Setup

This document provides comprehensive instructions for setting up error tracking and monitoring for the DOI Management Application.

## Overview

The DOI application uses multiple monitoring layers:

1. **Sentry** - Error tracking and performance monitoring
2. **Application Logs** - Structured logging with rotation
3. **Health Check Endpoints** - Real-time health monitoring
4. **System Metrics** - Resource usage monitoring

## Quick Setup Guide

### 1. Sentry Error Tracking Setup

```bash
# 1. Create account at https://sentry.io
# 2. Create new project for "Flask" application
# 3. Copy the DSN from project settings
# 4. Add to your .env file:
echo "SENTRY_DSN=https://your-key@sentry.io/your-project-id" >> .env
echo "SENTRY_ENVIRONMENT=production" >> .env

# 5. Restart application
sudo systemctl restart doi-app
```

### 2. Basic Monitoring Setup

```bash
# Set up log monitoring
./deployment/scripts/setup-monitoring.sh

# Test error tracking
curl -X POST https://your-domain.com/test-error  # Only in development
```

## Sentry Configuration

### Account Setup

1. **Create Sentry Account**: Go to [sentry.io](https://sentry.io) and create an account
2. **Create Project**: Set up a new Flask project
3. **Get DSN**: Copy the Data Source Name (DSN) from project settings
4. **Configure Teams**: Set up appropriate team access

### Environment Configuration

Add these variables to your `.env` file:

```bash
# Sentry Configuration
SENTRY_DSN=https://your-sentry-key@sentry.io/your-project-id
SENTRY_ENVIRONMENT=production  # or development, staging
SENTRY_SAMPLE_RATE=0.1  # 10% of transactions (optional)
```

### Sentry Features Enabled

The application automatically configures:

- **Error Tracking**: Unhandled exceptions
- **Performance Monitoring**: 10% transaction sampling
- **Logging Integration**: ERROR level logs sent to Sentry
- **Flask Integration**: Request context and user information
- **SQLAlchemy Integration**: Database query monitoring
- **Release Tracking**: Deployment and version tracking

### Advanced Sentry Configuration

#### Custom Error Boundaries

```python
from app.utils.logging import log_error
import sentry_sdk

# Manual error reporting
try:
    risky_operation()
except Exception as e:
    log_error(f"Operation failed: {e}", exc_info=True)
    sentry_sdk.capture_exception(e)
```

#### User Context

```python
from flask_login import current_user
import sentry_sdk

# Add user context to errors
sentry_sdk.set_user({
    "id": current_user.id,
    "email": current_user.email,
    "username": current_user.full_name
})
```

#### Custom Tags and Context

```python
sentry_sdk.set_tag("feature", "doi_generation")
sentry_sdk.set_context("operation", {
    "type": "xml_generation",
    "draft_id": draft.id
})
```

## Application Performance Monitoring

### Performance Metrics

The application tracks:

1. **Response Times** - HTTP request duration
2. **Database Queries** - SQL query performance  
3. **Error Rates** - Exception frequency
4. **Resource Usage** - CPU, memory, disk
5. **Business Metrics** - DOI generation success rate

### Health Check Monitoring

#### Basic Health Check

```bash
# Check application health
curl https://your-domain.com/health

# Expected response (healthy):
{
  "status": "healthy",
  "timestamp": "2025-08-19T14:30:22Z",
  "checks": {
    "database": {
      "status": "healthy",
      "response_time_ms": 12.34
    }
  },
  "metrics": {
    "response_time_ms": 45.67,
    "system": {
      "cpu_percent": 15.2,
      "memory_percent": 45.8
    }
  }
}
```

#### Extended Health Check

```bash
# Check log system health
curl https://your-domain.com/health/logs

# Expected response:
{
  "status": "healthy",
  "timestamp": "2025-08-19T14:30:22Z",
  "log_statistics": {
    "log_files_count": 5,
    "total_log_size_mb": 45.2,
    "current_log_size_mb": 8.7
  }
}
```

### Custom Metrics

#### Business Metrics Tracking

```python
# In DOI generation code
from app.utils.monitoring import track_business_metric

@track_business_metric('doi_generation')
def generate_doi_xml(draft_id):
    try:
        # DOI generation logic
        result = generate_xml(draft_id)
        track_business_metric('doi_generation_success')
        return result
    except Exception as e:
        track_business_metric('doi_generation_failure')
        raise
```

## System Monitoring

### Resource Monitoring

The health check endpoint provides system metrics:

- **CPU Usage**: Current CPU percentage
- **Memory Usage**: RAM usage percentage
- **Disk Space**: Available disk space
- **Process Metrics**: Uptime and process information

### Log Monitoring

#### Log Aggregation

```bash
# View recent errors
tail -f /opt/doi-app/logs/doi_app.log | grep ERROR

# Monitor application activity
tail -f /opt/doi-app/logs/doi_app.log | grep "User activity"

# Check log statistics
./deployment/scripts/log-maintenance.sh stats
```

#### Log Alerts

Set up alerts for critical log patterns:

```bash
# Create log monitoring script
cat > /opt/doi-app/scripts/log-alerts.sh << 'EOF'
#!/bin/bash
LOG_FILE="/opt/doi-app/logs/doi_app.log"

# Check for high error rate
ERROR_COUNT=$(tail -1000 "$LOG_FILE" | grep ERROR | wc -l)
if [ $ERROR_COUNT -gt 10 ]; then
    echo "High error rate detected: $ERROR_COUNT errors in last 1000 lines"
    # Send alert notification
fi

# Check for critical errors
CRITICAL_ERRORS=$(tail -100 "$LOG_FILE" | grep -E "(CRITICAL|Database.*failed|SSL.*error)")
if [ -n "$CRITICAL_ERRORS" ]; then
    echo "Critical errors detected:"
    echo "$CRITICAL_ERRORS"
    # Send urgent notification
fi
EOF

chmod +x /opt/doi-app/scripts/log-alerts.sh

# Add to cron for regular checking
echo "*/5 * * * * /opt/doi-app/scripts/log-alerts.sh" | crontab -
```

## External Monitoring Integration

### Uptime Monitoring

#### UptimeRobot Setup

1. Create account at [UptimeRobot](https://uptimerobot.com)
2. Add HTTP(S) monitor for your domain
3. Set check interval (5 minutes recommended)
4. Configure alert contacts

#### Pingdom Setup

1. Create account at [Pingdom](https://pingdom.com)
2. Set up website monitoring
3. Configure real user monitoring (RUM)
4. Set up alert notifications

### Infrastructure Monitoring

#### Server Monitoring with Netdata

```bash
# Install Netdata (optional)
bash <(curl -Ss https://my-netdata.io/kickstart.sh)

# Access dashboard at http://your-server:19999
# Configure firewall to restrict access
```

#### Simple Server Metrics

```bash
# Create system monitoring script
cat > /opt/doi-app/scripts/system-monitor.sh << 'EOF'
#!/bin/bash

# Collect system metrics
CPU_USAGE=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | awk -F'%' '{print $1}')
MEMORY_USAGE=$(free | grep Mem | awk '{printf("%.1f", ($3/$2) * 100.0)}')
DISK_USAGE=$(df -h / | awk 'NR==2 {print $5}' | sed 's/%//')

# Log metrics
echo "$(date) CPU:${CPU_USAGE}% MEM:${MEMORY_USAGE}% DISK:${DISK_USAGE}%" >> /opt/doi-app/logs/system-metrics.log

# Alert if thresholds exceeded
if (( $(echo "$CPU_USAGE > 80" | bc -l) )); then
    echo "High CPU usage: $CPU_USAGE%"
fi

if (( $(echo "$MEMORY_USAGE > 80" | bc -l) )); then
    echo "High memory usage: $MEMORY_USAGE%"
fi

if [ "$DISK_USAGE" -gt 80 ]; then
    echo "High disk usage: $DISK_USAGE%"
fi
EOF

chmod +x /opt/doi-app/scripts/system-monitor.sh

# Add to cron (every 5 minutes)
echo "*/5 * * * * /opt/doi-app/scripts/system-monitor.sh" | crontab -
```

## Alerting and Notifications

### Email Notifications

#### SMTP Configuration

Add to your `.env` file:

```bash
# Email Configuration
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-app@gmail.com
MAIL_PASSWORD=your-app-password
ADMIN_EMAIL=admin@yourdomain.com
```

#### Alert Email Template

```python
# app/utils/monitoring.py
from flask import current_app
from flask_mail import Mail, Message

def send_alert_email(subject, body, severity='info'):
    """Send alert email to administrators."""
    if not current_app.config.get('MAIL_SERVER'):
        return
    
    mail = Mail(current_app)
    
    msg = Message(
        subject=f"[DOI App - {severity.upper()}] {subject}",
        recipients=[current_app.config.get('ADMIN_EMAIL')],
        body=body,
        sender=current_app.config.get('MAIL_USERNAME')
    )
    
    try:
        mail.send(msg)
        current_app.logger.info(f"Alert email sent: {subject}")
    except Exception as e:
        current_app.logger.error(f"Failed to send alert email: {e}")
```

### Slack Integration

#### Webhook Setup

```bash
# Add Slack webhook to .env
echo "SLACK_WEBHOOK_URL=https://hooks.slack.com/your-webhook-url" >> .env
```

#### Slack Notification Function

```python
import requests
import json

def send_slack_alert(message, severity='info'):
    """Send alert to Slack channel."""
    webhook_url = current_app.config.get('SLACK_WEBHOOK_URL')
    if not webhook_url:
        return
    
    color_map = {
        'info': '#36a64f',      # green
        'warning': '#ff9000',   # orange  
        'error': '#ff0000',     # red
        'critical': '#ff0000'   # red
    }
    
    payload = {
        'attachments': [{
            'color': color_map.get(severity, '#36a64f'),
            'title': f'DOI Application Alert ({severity})',
            'text': message,
            'timestamp': datetime.utcnow().timestamp()
        }]
    }
    
    try:
        response = requests.post(webhook_url, json=payload, timeout=10)
        response.raise_for_status()
    except Exception as e:
        current_app.logger.error(f"Failed to send Slack alert: {e}")
```

## Monitoring Dashboard

### Grafana Setup (Optional)

```bash
# Install Grafana (Ubuntu/Debian)
wget -q -O - https://packages.grafana.com/gpg.key | sudo apt-key add -
echo "deb https://packages.grafana.com/oss/deb stable main" | sudo tee /etc/apt/sources.list.d/grafana.list
sudo apt update && sudo apt install grafana

# Start Grafana
sudo systemctl start grafana-server
sudo systemctl enable grafana-server

# Access at http://your-server:3000 (admin/admin)
```

### Simple HTML Dashboard

Create a basic monitoring dashboard:

```html
<!-- /opt/doi-app/static/monitor.html -->
<!DOCTYPE html>
<html>
<head>
    <title>DOI App Monitoring</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .status-ok { color: green; }
        .status-warning { color: orange; }
        .status-error { color: red; }
        .metric { margin: 10px 0; padding: 10px; border: 1px solid #ddd; }
        .refresh { margin-bottom: 20px; }
    </style>
</head>
<body>
    <h1>DOI Application Monitoring</h1>
    <div class="refresh">
        <button onclick="location.reload()">Refresh</button>
        <span>Last updated: <span id="lastUpdate"></span></span>
    </div>
    
    <div id="healthStatus" class="metric">
        <h3>Application Health</h3>
        <div id="healthData">Loading...</div>
    </div>
    
    <div id="logStatus" class="metric">
        <h3>Log Status</h3>
        <div id="logData">Loading...</div>
    </div>
    
    <script>
        async function fetchHealthStatus() {
            try {
                const response = await fetch('/health');
                const data = await response.json();
                
                let statusClass = 'status-ok';
                if (data.status === 'degraded') statusClass = 'status-warning';
                if (data.status === 'unhealthy') statusClass = 'status-error';
                
                document.getElementById('healthData').innerHTML = `
                    <div class="${statusClass}">Status: ${data.status}</div>
                    <div>Response Time: ${data.metrics.response_time_ms}ms</div>
                    <div>Database: ${data.checks.database?.status || 'unknown'}</div>
                `;
            } catch (error) {
                document.getElementById('healthData').innerHTML = 
                    '<div class="status-error">Failed to fetch health data</div>';
            }
        }
        
        async function fetchLogStatus() {
            try {
                const response = await fetch('/health/logs');
                const data = await response.json();
                
                document.getElementById('logData').innerHTML = `
                    <div>Log Files: ${data.log_statistics.log_files_count}</div>
                    <div>Total Size: ${data.log_statistics.total_log_size_mb} MB</div>
                    <div>Current Log: ${data.log_statistics.current_log_size_mb} MB</div>
                `;
            } catch (error) {
                document.getElementById('logData').innerHTML = 
                    '<div class="status-error">Failed to fetch log data</div>';
            }
        }
        
        // Update timestamp
        document.getElementById('lastUpdate').textContent = new Date().toLocaleString();
        
        // Fetch initial data
        fetchHealthStatus();
        fetchLogStatus();
        
        // Auto-refresh every 30 seconds
        setInterval(() => {
            fetchHealthStatus();
            fetchLogStatus();
            document.getElementById('lastUpdate').textContent = new Date().toLocaleString();
        }, 30000);
    </script>
</body>
</html>
```

## Troubleshooting Monitoring Issues

### Sentry Issues

#### Problem: Sentry not receiving events

**Debugging steps**:
```bash
# Check Sentry DSN configuration
grep SENTRY_DSN .env

# Test Sentry connection
python3 -c "
import sentry_sdk
sentry_sdk.init('YOUR_SENTRY_DSN')
sentry_sdk.capture_message('Test message')
print('Test message sent')
"

# Check application logs for Sentry errors
grep -i sentry /opt/doi-app/logs/doi_app.log
```

#### Problem: Too many Sentry events

**Solution**: Adjust sample rates in `.env`:
```bash
SENTRY_SAMPLE_RATE=0.05  # Reduce to 5%
```

### Health Check Issues

#### Problem: Health check returning 503

**Debugging**:
```bash
# Check application status
sudo systemctl status doi-app

# Check database connectivity
mysql -h $DB_HOST -u $DB_USER -p$DB_PASSWORD $DB_NAME -e "SELECT 1"

# Check logs for errors
tail -f /opt/doi-app/logs/doi_app.log | grep ERROR
```

### Log Monitoring Issues

#### Problem: Logs not rotating

**Solution**:
```bash
# Check log rotation configuration
ls -la /opt/doi-app/logs/

# Force log rotation
sudo ./deployment/scripts/log-maintenance.sh rotate

# Check disk space
df -h /opt/doi-app/logs/
```

## Best Practices

### 1. Alert Fatigue Prevention
- Set appropriate thresholds
- Use escalation policies
- Group related alerts
- Regular alert review and tuning

### 2. Monitoring Coverage
- Monitor all critical paths
- Include business metrics
- Track user experience
- Monitor dependencies

### 3. Incident Response
- Document incident procedures
- Define escalation paths
- Regular incident response drills
- Post-incident reviews

### 4. Data Retention
- Configure appropriate retention periods
- Balance cost vs. historical data needs
- Regular data cleanup
- Compliance considerations

## Security Considerations

### 1. Monitoring Data Security
- Avoid logging sensitive data
- Secure monitoring endpoints
- Encrypt monitoring data in transit
- Access control for monitoring tools

### 2. Alert Security
- Secure notification channels
- Avoid sensitive data in alerts
- Monitor for monitoring system tampering
- Regular security reviews

## Compliance and Auditing

### Audit Trail Requirements
- Log all user activities
- Track system changes
- Monitor access patterns
- Retain logs per compliance requirements

### Compliance Monitoring
- GDPR data processing logs
- Security event monitoring
- Change management tracking
- Performance baseline monitoring