#!/bin/bash

# Monitoring Setup Script for DOI Application
# This script sets up comprehensive monitoring for the DOI application

set -e

APP_DIR="/opt/doi-app"
MONITORING_DIR="$APP_DIR/monitoring"
SCRIPTS_DIR="$APP_DIR/scripts"
LOGS_DIR="$APP_DIR/logs"

echo "=========================================="
echo "DOI Application Monitoring Setup"
echo "=========================================="

# Function to print colored output
print_status() {
    echo -e "\n\033[1;32m[INFO]\033[0m $1"
}

print_error() {
    echo -e "\n\033[1;31m[ERROR]\033[0m $1"
}

print_warning() {
    echo -e "\n\033[1;33m[WARNING]\033[0m $1"
}

# Check if script is run as root
check_root() {
    if [ "$EUID" -ne 0 ]; then
        print_error "This script must be run as root (use sudo)"
        exit 1
    fi
}

# Create monitoring directory structure
create_directories() {
    print_status "Creating monitoring directory structure..."
    
    mkdir -p "$MONITORING_DIR"
    mkdir -p "$SCRIPTS_DIR"
    mkdir -p "$LOGS_DIR"
    
    # Set proper permissions
    chown -R doi-app:doi-app "$MONITORING_DIR" "$SCRIPTS_DIR" "$LOGS_DIR"
    chmod 755 "$MONITORING_DIR" "$SCRIPTS_DIR" "$LOGS_DIR"
    
    print_status "✓ Directory structure created"
}

# Create system monitoring script
create_system_monitor() {
    print_status "Creating system monitoring script..."
    
    cat > "$SCRIPTS_DIR/system-monitor.sh" << 'EOF'
#!/bin/bash

# System metrics collection script
METRICS_LOG="/opt/doi-app/logs/system-metrics.log"
APP_LOG="/opt/doi-app/logs/doi_app.log"
THRESHOLD_CPU=80
THRESHOLD_MEMORY=80
THRESHOLD_DISK=85

# Collect system metrics
collect_metrics() {
    TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
    
    # CPU usage
    CPU_USAGE=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | awk -F'%' '{print $1}' | sed 's/,/./')
    
    # Memory usage
    MEMORY_USAGE=$(free | grep Mem | awk '{printf("%.1f", ($3/$2) * 100.0)}')
    
    # Disk usage
    DISK_USAGE=$(df -h / | awk 'NR==2 {print $5}' | sed 's/%//')
    
    # Load average
    LOAD_AVG=$(uptime | awk -F'load average:' '{print $2}' | awk '{print $1}' | sed 's/,//')
    
    # Process count
    PROCESS_COUNT=$(ps aux | wc -l)
    
    # DOI app process status
    DOI_APP_STATUS="down"
    if pgrep -f "doi-app" > /dev/null; then
        DOI_APP_STATUS="up"
    fi
    
    # Log metrics
    echo "$TIMESTAMP CPU:${CPU_USAGE}% MEM:${MEMORY_USAGE}% DISK:${DISK_USAGE}% LOAD:${LOAD_AVG} PROCS:${PROCESS_COUNT} APP:${DOI_APP_STATUS}" >> "$METRICS_LOG"
    
    # Check thresholds and alert
    check_thresholds "$CPU_USAGE" "$MEMORY_USAGE" "$DISK_USAGE"
}

# Check thresholds and create alerts
check_thresholds() {
    local cpu=$1
    local memory=$2
    local disk=$3
    
    # CPU threshold
    if (( $(echo "$cpu > $THRESHOLD_CPU" | bc -l 2>/dev/null || echo "0") )); then
        echo "$(date '+%Y-%m-%d %H:%M:%S') ALERT: High CPU usage: $cpu%" >> "$APP_LOG"
    fi
    
    # Memory threshold
    if (( $(echo "$memory > $THRESHOLD_MEMORY" | bc -l 2>/dev/null || echo "0") )); then
        echo "$(date '+%Y-%m-%d %H:%M:%S') ALERT: High memory usage: $memory%" >> "$APP_LOG"
    fi
    
    # Disk threshold
    if [ "$disk" -gt "$THRESHOLD_DISK" ]; then
        echo "$(date '+%Y-%m-%d %H:%M:%S') ALERT: High disk usage: $disk%" >> "$APP_LOG"
    fi
}

# Main execution
collect_metrics
EOF
    
    chmod +x "$SCRIPTS_DIR/system-monitor.sh"
    chown doi-app:doi-app "$SCRIPTS_DIR/system-monitor.sh"
    
    print_status "✓ System monitoring script created"
}

# Create application health monitor
create_health_monitor() {
    print_status "Creating application health monitor..."
    
    cat > "$SCRIPTS_DIR/health-monitor.sh" << 'EOF'
#!/bin/bash

# Application health monitoring script
HEALTH_LOG="/opt/doi-app/logs/health-monitor.log"
DOMAIN="localhost"
PORT="5000"
TIMEOUT=10

# Test application health
test_health() {
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    local health_status="unknown"
    local response_time=0
    
    # Test health endpoint
    local start_time=$(date +%s.%N)
    local http_code=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout $TIMEOUT --max-time $TIMEOUT "http://$DOMAIN:$PORT/health" 2>/dev/null)
    local end_time=$(date +%s.%N)
    
    if [ $? -eq 0 ]; then
        response_time=$(echo "$end_time - $start_time" | bc | awk '{printf "%.2f", $1}')
        
        case $http_code in
            200)
                health_status="healthy"
                ;;
            503)
                health_status="unhealthy"
                ;;
            *)
                health_status="unknown"
                ;;
        esac
    else
        health_status="unreachable"
    fi
    
    # Log health check result
    echo "$timestamp STATUS:$health_status HTTP:$http_code RESPONSE_TIME:${response_time}s" >> "$HEALTH_LOG"
    
    # Alert on unhealthy status
    if [ "$health_status" != "healthy" ]; then
        echo "$timestamp ALERT: Application health check failed - Status: $health_status, HTTP: $http_code" >> "/opt/doi-app/logs/doi_app.log"
    fi
}

# Main execution
test_health
EOF
    
    chmod +x "$SCRIPTS_DIR/health-monitor.sh"
    chown doi-app:doi-app "$SCRIPTS_DIR/health-monitor.sh"
    
    print_status "✓ Application health monitor created"
}

# Create log analyzer script
create_log_analyzer() {
    print_status "Creating log analyzer script..."
    
    cat > "$SCRIPTS_DIR/log-analyzer.sh" << 'EOF'
#!/bin/bash

# Log analysis and alerting script
APP_LOG="/opt/doi-app/logs/doi_app.log"
ANALYSIS_LOG="/opt/doi-app/logs/log-analysis.log"
ERROR_THRESHOLD=10
WARNING_THRESHOLD=20

analyze_logs() {
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    # Analyze last 1000 lines for patterns
    if [ ! -f "$APP_LOG" ]; then
        echo "$timestamp LOG ANALYSIS: Application log not found" >> "$ANALYSIS_LOG"
        return 1
    fi
    
    # Count error patterns
    local error_count=$(tail -1000 "$APP_LOG" | grep -c "ERROR" || echo "0")
    local warning_count=$(tail -1000 "$APP_LOG" | grep -c "WARNING" || echo "0")
    local critical_count=$(tail -1000 "$APP_LOG" | grep -c "CRITICAL" || echo "0")
    
    # Check for specific error patterns
    local db_errors=$(tail -1000 "$APP_LOG" | grep -i "database.*error\|mysql.*error\|connection.*failed" | wc -l || echo "0")
    local auth_failures=$(tail -1000 "$APP_LOG" | grep -i "authentication.*failed\|login.*failed" | wc -l || echo "0")
    local ssl_errors=$(tail -1000 "$APP_LOG" | grep -i "ssl.*error\|certificate.*error" | wc -l || echo "0")
    
    # Log analysis results
    echo "$timestamp ERRORS:$error_count WARNINGS:$warning_count CRITICAL:$critical_count DB_ERRORS:$db_errors AUTH_FAILURES:$auth_failures SSL_ERRORS:$ssl_errors" >> "$ANALYSIS_LOG"
    
    # Generate alerts based on thresholds
    if [ "$error_count" -gt "$ERROR_THRESHOLD" ]; then
        echo "$timestamp ALERT: High error rate detected - $error_count errors in last 1000 log lines" >> "$APP_LOG"
    fi
    
    if [ "$critical_count" -gt 0 ]; then
        echo "$timestamp ALERT: Critical errors detected - $critical_count critical errors found" >> "$APP_LOG"
    fi
    
    if [ "$db_errors" -gt 5 ]; then
        echo "$timestamp ALERT: Database connectivity issues - $db_errors database errors found" >> "$APP_LOG"
    fi
    
    if [ "$auth_failures" -gt 10 ]; then
        echo "$timestamp ALERT: High authentication failure rate - $auth_failures failed attempts found" >> "$APP_LOG"
    fi
}

# Main execution
analyze_logs
EOF
    
    chmod +x "$SCRIPTS_DIR/log-analyzer.sh"
    chown doi-app:doi-app "$SCRIPTS_DIR/log-analyzer.sh"
    
    print_status "✓ Log analyzer script created"
}

# Create monitoring dashboard script
create_dashboard() {
    print_status "Creating monitoring dashboard..."
    
    cat > "$SCRIPTS_DIR/monitoring-dashboard.sh" << 'EOF'
#!/bin/bash

# Simple monitoring dashboard
LOGS_DIR="/opt/doi-app/logs"
METRICS_LOG="$LOGS_DIR/system-metrics.log"
HEALTH_LOG="$LOGS_DIR/health-monitor.log"
ANALYSIS_LOG="$LOGS_DIR/log-analysis.log"

show_dashboard() {
    clear
    echo "=========================================="
    echo "DOI Application Monitoring Dashboard"
    echo "Last updated: $(date)"
    echo "=========================================="
    echo ""
    
    # System status
    echo "SYSTEM STATUS:"
    if [ -f "$METRICS_LOG" ]; then
        echo "Latest metrics: $(tail -1 $METRICS_LOG 2>/dev/null || echo 'No data')"
    else
        echo "System metrics: No data available"
    fi
    echo ""
    
    # Application health
    echo "APPLICATION HEALTH:"
    if [ -f "$HEALTH_LOG" ]; then
        echo "Latest health: $(tail -1 $HEALTH_LOG 2>/dev/null || echo 'No data')"
    else
        echo "Health status: No data available"
    fi
    echo ""
    
    # Log analysis
    echo "LOG ANALYSIS:"
    if [ -f "$ANALYSIS_LOG" ]; then
        echo "Latest analysis: $(tail -1 $ANALYSIS_LOG 2>/dev/null || echo 'No data')"
    else
        echo "Log analysis: No data available"
    fi
    echo ""
    
    # Recent alerts
    echo "RECENT ALERTS (last 10):"
    if [ -f "$LOGS_DIR/doi_app.log" ]; then
        grep "ALERT:" "$LOGS_DIR/doi_app.log" | tail -10 | while read -r line; do
            echo "  $line"
        done
    else
        echo "  No alerts or log file not found"
    fi
    echo ""
    
    # Service status
    echo "SERVICE STATUS:"
    echo "  DOI App: $(systemctl is-active doi-app 2>/dev/null || echo 'unknown')"
    echo "  Nginx: $(systemctl is-active nginx 2>/dev/null || echo 'unknown')"
    echo "  MySQL: $(systemctl is-active mysql 2>/dev/null || echo 'unknown')"
    echo ""
    
    echo "Press Ctrl+C to exit, or wait for auto-refresh in 30 seconds..."
}

# Continuous dashboard mode
if [ "$1" = "--continuous" ]; then
    while true; do
        show_dashboard
        sleep 30
    done
else
    show_dashboard
fi
EOF
    
    chmod +x "$SCRIPTS_DIR/monitoring-dashboard.sh"
    chown doi-app:doi-app "$SCRIPTS_DIR/monitoring-dashboard.sh"
    
    print_status "✓ Monitoring dashboard created"
}

# Setup cron jobs for monitoring
setup_cron_jobs() {
    print_status "Setting up monitoring cron jobs..."
    
    # Create cron job for system monitoring (every 5 minutes)
    (crontab -l 2>/dev/null | grep -v "system-monitor.sh"; echo "*/5 * * * * $SCRIPTS_DIR/system-monitor.sh >/dev/null 2>&1") | crontab -
    
    # Create cron job for health monitoring (every 2 minutes)
    (crontab -l 2>/dev/null | grep -v "health-monitor.sh"; echo "*/2 * * * * $SCRIPTS_DIR/health-monitor.sh >/dev/null 2>&1") | crontab -
    
    # Create cron job for log analysis (every 10 minutes)
    (crontab -l 2>/dev/null | grep -v "log-analyzer.sh"; echo "*/10 * * * * $SCRIPTS_DIR/log-analyzer.sh >/dev/null 2>&1") | crontab -
    
    print_status "✓ Monitoring cron jobs configured"
}

# Create systemd service for monitoring (alternative to cron)
create_systemd_timers() {
    print_status "Creating systemd timers for monitoring..."
    
    # System monitoring timer
    cat > /etc/systemd/system/doi-system-monitor.service << EOF
[Unit]
Description=DOI Application System Monitor
After=doi-app.service

[Service]
Type=oneshot
User=doi-app
ExecStart=$SCRIPTS_DIR/system-monitor.sh
EOF

    cat > /etc/systemd/system/doi-system-monitor.timer << EOF
[Unit]
Description=Run DOI System Monitor every 5 minutes
Requires=doi-system-monitor.service

[Timer]
OnCalendar=*:0/5
Persistent=true

[Install]
WantedBy=timers.target
EOF

    # Health monitoring timer
    cat > /etc/systemd/system/doi-health-monitor.service << EOF
[Unit]
Description=DOI Application Health Monitor
After=doi-app.service

[Service]
Type=oneshot
User=doi-app
ExecStart=$SCRIPTS_DIR/health-monitor.sh
EOF

    cat > /etc/systemd/system/doi-health-monitor.timer << EOF
[Unit]
Description=Run DOI Health Monitor every 2 minutes
Requires=doi-health-monitor.service

[Timer]
OnCalendar=*:0/2
Persistent=true

[Install]
WantedBy=timers.target
EOF

    # Reload systemd and enable timers
    systemctl daemon-reload
    systemctl enable doi-system-monitor.timer
    systemctl enable doi-health-monitor.timer
    systemctl start doi-system-monitor.timer
    systemctl start doi-health-monitor.timer
    
    print_status "✓ Systemd monitoring timers created and started"
}

# Create monitoring configuration file
create_config() {
    print_status "Creating monitoring configuration..."
    
    cat > "$MONITORING_DIR/monitoring.conf" << EOF
# DOI Application Monitoring Configuration

# Thresholds
CPU_THRESHOLD=80
MEMORY_THRESHOLD=80
DISK_THRESHOLD=85
ERROR_THRESHOLD=10
RESPONSE_TIME_THRESHOLD=5.0

# Endpoints
HEALTH_ENDPOINT="http://localhost:5000/health"
HEALTH_LOGS_ENDPOINT="http://localhost:5000/health/logs"

# Log files
SYSTEM_METRICS_LOG="$LOGS_DIR/system-metrics.log"
HEALTH_LOG="$LOGS_DIR/health-monitor.log"
ANALYSIS_LOG="$LOGS_DIR/log-analysis.log"
APPLICATION_LOG="$LOGS_DIR/doi_app.log"

# Monitoring intervals (minutes)
SYSTEM_MONITOR_INTERVAL=5
HEALTH_MONITOR_INTERVAL=2
LOG_ANALYSIS_INTERVAL=10

# Retention (days)
METRICS_RETENTION=30
HEALTH_RETENTION=30
ANALYSIS_RETENTION=30
EOF
    
    chown doi-app:doi-app "$MONITORING_DIR/monitoring.conf"
    chmod 644 "$MONITORING_DIR/monitoring.conf"
    
    print_status "✓ Monitoring configuration created"
}

# Install monitoring dependencies
install_dependencies() {
    print_status "Installing monitoring dependencies..."
    
    # Install bc for calculations
    apt update
    apt install -y bc curl
    
    # Install Python packages if not already installed
    if [ -f "$APP_DIR/venv/bin/pip" ]; then
        "$APP_DIR/venv/bin/pip" install psutil >/dev/null 2>&1 || print_warning "Failed to install psutil"
    fi
    
    print_status "✓ Dependencies installed"
}

# Test monitoring setup
test_monitoring() {
    print_status "Testing monitoring setup..."
    
    # Test system monitor
    if [ -x "$SCRIPTS_DIR/system-monitor.sh" ]; then
        sudo -u doi-app "$SCRIPTS_DIR/system-monitor.sh"
        print_status "✓ System monitor test passed"
    else
        print_error "System monitor script not found or not executable"
    fi
    
    # Test health monitor
    if [ -x "$SCRIPTS_DIR/health-monitor.sh" ]; then
        sudo -u doi-app "$SCRIPTS_DIR/health-monitor.sh"
        print_status "✓ Health monitor test passed"
    else
        print_error "Health monitor script not found or not executable"
    fi
    
    # Test log analyzer
    if [ -x "$SCRIPTS_DIR/log-analyzer.sh" ]; then
        sudo -u doi-app "$SCRIPTS_DIR/log-analyzer.sh"
        print_status "✓ Log analyzer test passed"
    else
        print_error "Log analyzer script not found or not executable"
    fi
}

# Show completion summary
show_summary() {
    echo ""
    echo "=========================================="
    echo "Monitoring Setup Completed!"
    echo "=========================================="
    echo ""
    echo "Created monitoring components:"
    echo "✓ System monitoring script"
    echo "✓ Application health monitor"
    echo "✓ Log analyzer"
    echo "✓ Monitoring dashboard"
    echo "✓ Systemd timers (preferred) or cron jobs"
    echo "✓ Configuration file"
    echo ""
    echo "Monitoring files:"
    echo "- Scripts: $SCRIPTS_DIR/"
    echo "- Config: $MONITORING_DIR/monitoring.conf"
    echo "- Logs: $LOGS_DIR/"
    echo ""
    echo "Usage:"
    echo "- View dashboard: $SCRIPTS_DIR/monitoring-dashboard.sh"
    echo "- Continuous dashboard: $SCRIPTS_DIR/monitoring-dashboard.sh --continuous"
    echo "- Check systemd timers: systemctl list-timers | grep doi"
    echo ""
    echo "Next steps:"
    echo "1. Configure Sentry DSN in .env file for error tracking"
    echo "2. Set up external monitoring (UptimeRobot, Pingdom, etc.)"
    echo "3. Configure alert notifications (email, Slack, etc.)"
    echo "4. Review and adjust monitoring thresholds"
}

# Main execution
main() {
    check_root
    install_dependencies
    create_directories
    create_system_monitor
    create_health_monitor
    create_log_analyzer
    create_dashboard
    create_config
    
    # Choose between systemd timers or cron jobs
    if systemctl --version >/dev/null 2>&1; then
        create_systemd_timers
    else
        setup_cron_jobs
    fi
    
    test_monitoring
    show_summary
}

# Run main function
main "$@"