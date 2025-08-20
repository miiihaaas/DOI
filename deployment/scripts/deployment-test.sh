#!/bin/bash

# Deployment Testing and Verification Script for DOI Application
# This script performs comprehensive testing of the deployed DOI application

set -e

DOMAIN="localhost"
APP_DIR="/opt/doi-app"
LOG_FILE="$APP_DIR/logs/deployment-test.log"
RESULTS_FILE="/tmp/deployment-test-results-$(date +%Y%m%d_%H%M%S).txt"
VERBOSE=false
SKIP_EXTERNAL=false

echo "=========================================="
echo "DOI Application Deployment Testing"
echo "=========================================="

# Function to print colored output
print_status() {
    local message="$1"
    echo -e "\n\033[1;32m[INFO]\033[0m $message"
    echo "$(date '+%Y-%m-%d %H:%M:%S') [INFO] $message" >> "$LOG_FILE"
}

print_success() {
    local message="$1"
    echo -e "\033[1;32m✅ $message\033[0m"
    echo "$(date '+%Y-%m-%d %H:%M:%S') [SUCCESS] $message" >> "$LOG_FILE"
}

print_error() {
    local message="$1"
    echo -e "\033[1;31m❌ $message\033[0m" >&2
    echo "$(date '+%Y-%m-%d %H:%M:%S') [ERROR] $message" >> "$LOG_FILE"
}

print_warning() {
    local message="$1"
    echo -e "\033[1;33m⚠️  $message\033[0m"
    echo "$(date '+%Y-%m-%d %H:%M:%S') [WARNING] $message" >> "$LOG_FILE"
}

print_debug() {
    local message="$1"
    if [ "$VERBOSE" = true ]; then
        echo -e "\033[1;36m[DEBUG]\033[0m $message"
    fi
    echo "$(date '+%Y-%m-%d %H:%M:%S') [DEBUG] $message" >> "$LOG_FILE"
}

# Function to show usage
show_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -d, --domain DOMAIN    Domain to test (default: localhost)"
    echo "  -v, --verbose          Enable verbose output"
    echo "  --skip-external        Skip external connectivity tests"
    echo "  -h, --help             Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                     # Test localhost"
    echo "  $0 -d example.com      # Test specific domain"
    echo "  $0 -v --skip-external  # Verbose mode, no external tests"
}

# Parse command line arguments
parse_arguments() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            -d|--domain)
                DOMAIN="$2"
                shift 2
                ;;
            -v|--verbose)
                VERBOSE=true
                shift
                ;;
            --skip-external)
                SKIP_EXTERNAL=true
                shift
                ;;
            -h|--help)
                show_usage
                exit 0
                ;;
            -*|--*)
                print_error "Unknown option $1"
                show_usage
                exit 1
                ;;
            *)
                print_error "Unexpected argument: $1"
                show_usage
                exit 1
                ;;
        esac
    done
}

# Initialize testing
init_testing() {
    print_status "Initializing deployment testing..."
    
    # Create log directory if it doesn't exist
    mkdir -p "$(dirname "$LOG_FILE")"
    
    # Initialize log file
    echo "$(date '+%Y-%m-%d %H:%M:%S') [INIT] Deployment testing started" > "$LOG_FILE"
    
    # Initialize results file
    cat > "$RESULTS_FILE" << EOF
DOI Application Deployment Test Results
Generated: $(date)
Domain: $DOMAIN
Test Type: $([ "$SKIP_EXTERNAL" = true ] && echo "Internal Only" || echo "Full")

EOF
    
    print_status "Testing domain: $DOMAIN"
    print_status "Results will be saved to: $RESULTS_FILE"
}

# Test 1: Environment validation
test_environment() {
    print_status "Testing environment configuration..."
    local test_passed=true
    
    # Check .env file
    if [ -f "$APP_DIR/.env" ]; then
        print_success "Environment file exists"
        
        # Check critical environment variables
        if grep -q "SECRET_KEY=" "$APP_DIR/.env" && ! grep -q "SECRET_KEY=dev-secret-key-change-in-production" "$APP_DIR/.env"; then
            print_success "SECRET_KEY is configured and not default"
        else
            print_error "SECRET_KEY is missing or using default value"
            test_passed=false
        fi
        
        if grep -q "DATABASE_URL=" "$APP_DIR/.env"; then
            print_success "DATABASE_URL is configured"
        else
            print_error "DATABASE_URL is missing"
            test_passed=false
        fi
    else
        print_error "Environment file not found at $APP_DIR/.env"
        test_passed=false
    fi
    
    # Check Python virtual environment
    if [ -f "$APP_DIR/venv/bin/python" ]; then
        print_success "Virtual environment exists"
    else
        print_error "Virtual environment not found"
        test_passed=false
    fi
    
    # Check application files
    if [ -f "$APP_DIR/app/__init__.py" ]; then
        print_success "Application files are present"
    else
        print_error "Application files not found"
        test_passed=false
    fi
    
    echo "Environment Test: $([ "$test_passed" = true ] && echo "PASSED" || echo "FAILED")" >> "$RESULTS_FILE"
    return $([ "$test_passed" = true ] && echo 0 || echo 1)
}

# Test 2: Service status
test_services() {
    print_status "Testing service status..."
    local test_passed=true
    
    # Test DOI application service
    if systemctl is-active --quiet doi-app; then
        print_success "DOI application service is running"
        
        # Get service details
        local service_status=$(systemctl show doi-app --property=ActiveState,SubState,LoadState --no-pager)
        print_debug "Service status: $service_status"
    else
        print_error "DOI application service is not running"
        print_debug "Service status: $(systemctl status doi-app --no-pager -l)"
        test_passed=false
    fi
    
    # Test Nginx service
    if systemctl is-active --quiet nginx; then
        print_success "Nginx service is running"
    else
        print_error "Nginx service is not running"
        test_passed=false
    fi
    
    # Test MySQL service
    if systemctl is-active --quiet mysql; then
        print_success "MySQL service is running"
    else
        print_error "MySQL service is not running"
        test_passed=false
    fi
    
    echo "Services Test: $([ "$test_passed" = true ] && echo "PASSED" || echo "FAILED")" >> "$RESULTS_FILE"
    return $([ "$test_passed" = true ] && echo 0 || echo 1)
}

# Test 3: Database connectivity
test_database() {
    print_status "Testing database connectivity..."
    local test_passed=true
    
    # Load environment variables
    if [ -f "$APP_DIR/.env" ]; then
        set -a
        source "$APP_DIR/.env"
        set +a
    fi
    
    # Extract database details from DATABASE_URL
    if [ -n "$DATABASE_URL" ]; then
        local db_user=$(echo "$DATABASE_URL" | sed -n 's/.*:\/\/\([^:]*\):.*/\1/p')
        local db_pass=$(echo "$DATABASE_URL" | sed -n 's/.*:\/\/[^:]*:\([^@]*\)@.*/\1/p')
        local db_host=$(echo "$DATABASE_URL" | sed -n 's/.*@\([^:]*\):.*/\1/p')
        local db_port=$(echo "$DATABASE_URL" | sed -n 's/.*:\([0-9]*\)\/.*/\1/p')
        local db_name=$(echo "$DATABASE_URL" | sed -n 's/.*\/\([^?]*\).*/\1/p')
        
        print_debug "Database connection details: $db_host:$db_port/$db_name as $db_user"
        
        # Test database connection
        if mysql -h "$db_host" -P "$db_port" -u "$db_user" -p"$db_pass" "$db_name" -e "SELECT 1;" > /dev/null 2>&1; then
            print_success "Database connection successful"
            
            # Test table existence
            local table_count=$(mysql -h "$db_host" -P "$db_port" -u "$db_user" -p"$db_pass" "$db_name" -e "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='$db_name';" -s -N 2>/dev/null)
            if [ "$table_count" -gt 0 ]; then
                print_success "Database tables exist ($table_count tables)"
            else
                print_warning "Database has no tables (may need migration)"
            fi
        else
            print_error "Database connection failed"
            test_passed=false
        fi
    else
        print_error "DATABASE_URL not found in environment"
        test_passed=false
    fi
    
    echo "Database Test: $([ "$test_passed" = true ] && echo "PASSED" || echo "FAILED")" >> "$RESULTS_FILE"
    return $([ "$test_passed" = true ] && echo 0 || echo 1)
}

# Test 4: Health check endpoint
test_health_check() {
    print_status "Testing health check endpoint..."
    local test_passed=true
    
    # Test health endpoint
    local health_url="http://$DOMAIN:5000/health"
    if [ "$DOMAIN" != "localhost" ] && [ "$DOMAIN" != "127.0.0.1" ]; then
        health_url="https://$DOMAIN/health"
    fi
    
    print_debug "Testing health URL: $health_url"
    
    local health_response=$(curl -s -w "HTTPSTATUS:%{http_code};TIME:%{time_total}" "$health_url" 2>/dev/null)
    local http_code=$(echo "$health_response" | grep -o "HTTPSTATUS:[0-9]*" | cut -d: -f2)
    local response_time=$(echo "$health_response" | grep -o "TIME:[0-9.]*" | cut -d: -f2)
    local health_body=$(echo "$health_response" | sed -E 's/HTTPSTATUS:[0-9]*;TIME:[0-9.]*$//')
    
    if [ "$http_code" = "200" ]; then
        print_success "Health check endpoint responding (HTTP $http_code, ${response_time}s)"
        
        # Validate JSON response
        if echo "$health_body" | jq . > /dev/null 2>&1; then
            print_success "Health check returns valid JSON"
            
            # Check status field
            local health_status=$(echo "$health_body" | jq -r '.status' 2>/dev/null)
            if [ "$health_status" = "healthy" ]; then
                print_success "Application reports healthy status"
            elif [ "$health_status" = "degraded" ]; then
                print_warning "Application reports degraded status"
            else
                print_error "Application reports unhealthy status: $health_status"
                test_passed=false
            fi
        else
            print_error "Health check response is not valid JSON"
            test_passed=false
        fi
    elif [ "$http_code" = "503" ]; then
        print_error "Health check reports service unavailable (HTTP $http_code)"
        test_passed=false
    else
        print_error "Health check endpoint not accessible (HTTP $http_code)"
        test_passed=false
    fi
    
    # Test extended health check
    local health_logs_url="${health_url/\/health/\/health\/logs}"
    if curl -s -f "$health_logs_url" > /dev/null 2>&1; then
        print_success "Extended health check (logs) is accessible"
    else
        print_warning "Extended health check (logs) is not accessible"
    fi
    
    echo "Health Check Test: $([ "$test_passed" = true ] && echo "PASSED" || echo "FAILED")" >> "$RESULTS_FILE"
    echo "  Response Time: ${response_time}s" >> "$RESULTS_FILE"
    return $([ "$test_passed" = true ] && echo 0 || echo 1)
}

# Test 5: Web server and SSL
test_web_server() {
    print_status "Testing web server and SSL configuration..."
    local test_passed=true
    
    if [ "$SKIP_EXTERNAL" = true ] || [ "$DOMAIN" = "localhost" ] || [ "$DOMAIN" = "127.0.0.1" ]; then
        print_warning "Skipping SSL tests for localhost/internal testing"
        echo "Web Server Test: SKIPPED (localhost/internal)" >> "$RESULTS_FILE"
        return 0
    fi
    
    # Test HTTPS connection
    local https_url="https://$DOMAIN"
    if curl -s -I "$https_url" > /dev/null 2>&1; then
        print_success "HTTPS connection successful"
        
        # Check HTTP to HTTPS redirect
        local http_redirect=$(curl -s -I "http://$DOMAIN" | grep -i "location:" | grep -c "https://")
        if [ "$http_redirect" -gt 0 ]; then
            print_success "HTTP to HTTPS redirect is working"
        else
            print_warning "HTTP to HTTPS redirect may not be configured"
        fi
    else
        print_error "HTTPS connection failed"
        test_passed=false
    fi
    
    # Test SSL certificate
    if echo | openssl s_client -servername "$DOMAIN" -connect "$DOMAIN:443" -verify_return_error > /dev/null 2>&1; then
        print_success "SSL certificate is valid"
        
        # Check certificate expiration
        local cert_expiry=$(echo | openssl s_client -servername "$DOMAIN" -connect "$DOMAIN:443" 2>/dev/null | openssl x509 -noout -dates | grep "notAfter=" | cut -d= -f2)
        local expiry_epoch=$(date -d "$cert_expiry" +%s 2>/dev/null)
        local current_epoch=$(date +%s)
        local days_left=$(( (expiry_epoch - current_epoch) / 86400 ))
        
        if [ "$days_left" -gt 30 ]; then
            print_success "SSL certificate valid for $days_left days"
        elif [ "$days_left" -gt 0 ]; then
            print_warning "SSL certificate expires in $days_left days"
        else
            print_error "SSL certificate has expired"
            test_passed=false
        fi
    else
        print_error "SSL certificate validation failed"
        test_passed=false
    fi
    
    # Test security headers
    local security_headers=$(curl -s -I "$https_url")
    local headers_present=0
    
    if echo "$security_headers" | grep -q "Strict-Transport-Security:"; then
        print_success "HSTS header is present"
        ((headers_present++))
    else
        print_warning "HSTS header is missing"
    fi
    
    if echo "$security_headers" | grep -q "X-Frame-Options:"; then
        print_success "X-Frame-Options header is present"
        ((headers_present++))
    else
        print_warning "X-Frame-Options header is missing"
    fi
    
    if echo "$security_headers" | grep -q "X-Content-Type-Options:"; then
        print_success "X-Content-Type-Options header is present"
        ((headers_present++))
    else
        print_warning "X-Content-Type-Options header is missing"
    fi
    
    echo "Web Server Test: $([ "$test_passed" = true ] && echo "PASSED" || echo "FAILED")" >> "$RESULTS_FILE"
    echo "  Security Headers: $headers_present/3 present" >> "$RESULTS_FILE"
    return $([ "$test_passed" = true ] && echo 0 || echo 1)
}

# Test 6: Application functionality
test_application() {
    print_status "Testing application functionality..."
    local test_passed=true
    
    local base_url="http://$DOMAIN:5000"
    if [ "$DOMAIN" != "localhost" ] && [ "$DOMAIN" != "127.0.0.1" ]; then
        base_url="https://$DOMAIN"
    fi
    
    # Test main page
    if curl -s -f "$base_url/" > /dev/null; then
        print_success "Main page is accessible"
    else
        print_error "Main page is not accessible"
        test_passed=false
    fi
    
    # Test login page
    if curl -s -f "$base_url/auth/login" > /dev/null; then
        print_success "Login page is accessible"
    else
        print_error "Login page is not accessible"
        test_passed=false
    fi
    
    # Test static files
    if curl -s -f "$base_url/static/css/main.css" > /dev/null 2>&1; then
        print_success "Static files are being served"
    else
        print_warning "Static files may not be properly served"
    fi
    
    # Test error pages
    local error_404=$(curl -s -w "%{http_code}" -o /dev/null "$base_url/nonexistent-page")
    if [ "$error_404" = "404" ]; then
        print_success "404 error page is working"
    else
        print_warning "404 error handling may not be configured correctly"
    fi
    
    echo "Application Test: $([ "$test_passed" = true ] && echo "PASSED" || echo "FAILED")" >> "$RESULTS_FILE"
    return $([ "$test_passed" = true ] && echo 0 || echo 1)
}

# Test 7: Logging system
test_logging() {
    print_status "Testing logging system..."
    local test_passed=true
    
    # Check if log directory exists and is writable
    if [ -d "$APP_DIR/logs" ] && [ -w "$APP_DIR/logs" ]; then
        print_success "Log directory exists and is writable"
    else
        print_error "Log directory issue"
        test_passed=false
    fi
    
    # Check if main log file exists
    if [ -f "$APP_DIR/logs/doi_app.log" ]; then
        print_success "Main application log file exists"
        
        # Check recent log entries
        local recent_logs=$(tail -10 "$APP_DIR/logs/doi_app.log" 2>/dev/null | wc -l)
        if [ "$recent_logs" -gt 0 ]; then
            print_success "Log file contains recent entries"
        else
            print_warning "Log file appears to be empty or very old"
        fi
    else
        print_error "Main application log file not found"
        test_passed=false
    fi
    
    # Check log rotation configuration
    if [ -f "$APP_DIR/logs/doi_app.log.1" ] || [ -f "$APP_DIR/logs/doi_app.log.1.gz" ]; then
        print_success "Log rotation appears to be working"
    else
        print_debug "Log rotation files not present (may not have rotated yet)"
    fi
    
    echo "Logging Test: $([ "$test_passed" = true ] && echo "PASSED" || echo "FAILED")" >> "$RESULTS_FILE"
    return $([ "$test_passed" = true ] && echo 0 || echo 1)
}

# Test 8: Monitoring system
test_monitoring() {
    print_status "Testing monitoring system..."
    local test_passed=true
    
    # Check if monitoring scripts exist
    local monitoring_scripts=("system-monitor.sh" "health-monitor.sh" "log-analyzer.sh")
    local scripts_found=0
    
    for script in "${monitoring_scripts[@]}"; do
        if [ -f "$APP_DIR/scripts/$script" ] && [ -x "$APP_DIR/scripts/$script" ]; then
            print_success "Monitoring script $script exists and is executable"
            ((scripts_found++))
        else
            print_warning "Monitoring script $script not found or not executable"
        fi
    done
    
    # Check systemd timers or cron jobs
    local timers_active=0
    if systemctl list-timers --no-pager | grep -q "doi.*monitor"; then
        timers_active=$(systemctl list-timers --no-pager | grep "doi.*monitor" | wc -l)
        print_success "Systemd monitoring timers are active ($timers_active)"
    else
        # Check cron jobs
        if crontab -l 2>/dev/null | grep -q "monitor"; then
            local cron_jobs=$(crontab -l 2>/dev/null | grep "monitor" | wc -l)
            print_success "Monitoring cron jobs are configured ($cron_jobs)"
        else
            print_warning "No monitoring timers or cron jobs found"
            test_passed=false
        fi
    fi
    
    # Test monitoring log files
    local monitoring_logs=("system-metrics.log" "health-monitor.log")
    for log_file in "${monitoring_logs[@]}"; do
        if [ -f "$APP_DIR/logs/$log_file" ]; then
            print_success "Monitoring log $log_file exists"
        else
            print_debug "Monitoring log $log_file not yet created"
        fi
    done
    
    echo "Monitoring Test: $([ "$test_passed" = true ] && echo "PASSED" || echo "FAILED")" >> "$RESULTS_FILE"
    echo "  Scripts Found: $scripts_found/${#monitoring_scripts[@]}" >> "$RESULTS_FILE"
    return $([ "$test_passed" = true ] && echo 0 || echo 1)
}

# Generate final report
generate_report() {
    local total_tests=$1
    local passed_tests=$2
    
    print_status "Generating test report..."
    
    local pass_percentage=$(( passed_tests * 100 / total_tests ))
    
    cat >> "$RESULTS_FILE" << EOF

========================================
DEPLOYMENT TEST SUMMARY
========================================

Total Tests: $total_tests
Passed Tests: $passed_tests
Failed Tests: $((total_tests - passed_tests))
Success Rate: $pass_percentage%

Overall Status: $([ "$passed_tests" -eq "$total_tests" ] && echo "✅ ALL TESTS PASSED" || echo "❌ SOME TESTS FAILED")

Test completed at: $(date)
Log file: $LOG_FILE

$([ "$passed_tests" -lt "$total_tests" ] && echo "
⚠️ ATTENTION REQUIRED:
Some tests failed. Please review the detailed logs and address the issues
before considering the deployment successful.

Common issues:
- Check service status: systemctl status doi-app nginx mysql
- Verify environment configuration: cat $APP_DIR/.env
- Check application logs: tail -f $APP_DIR/logs/doi_app.log
- Test health endpoint manually: curl https://$DOMAIN/health
")

EOF
    
    echo ""
    echo "=========================================="
    echo "DEPLOYMENT TEST RESULTS"
    echo "=========================================="
    echo ""
    cat "$RESULTS_FILE"
    echo ""
    print_status "Detailed results saved to: $RESULTS_FILE"
}

# Main execution
main() {
    parse_arguments "$@"
    init_testing
    
    local total_tests=0
    local passed_tests=0
    
    # Run all tests
    print_status "Running deployment verification tests..."
    
    # Test 1: Environment
    ((total_tests++))
    test_environment && ((passed_tests++))
    
    # Test 2: Services
    ((total_tests++))
    test_services && ((passed_tests++))
    
    # Test 3: Database
    ((total_tests++))
    test_database && ((passed_tests++))
    
    # Test 4: Health Check
    ((total_tests++))
    test_health_check && ((passed_tests++))
    
    # Test 5: Web Server/SSL
    ((total_tests++))
    test_web_server && ((passed_tests++))
    
    # Test 6: Application
    ((total_tests++))
    test_application && ((passed_tests++))
    
    # Test 7: Logging
    ((total_tests++))
    test_logging && ((passed_tests++))
    
    # Test 8: Monitoring
    ((total_tests++))
    test_monitoring && ((passed_tests++))
    
    # Generate final report
    generate_report $total_tests $passed_tests
    
    # Return appropriate exit code
    if [ "$passed_tests" -eq "$total_tests" ]; then
        print_status "🎉 All tests passed! Deployment verification successful."
        exit 0
    else
        print_error "⚠️ Some tests failed. Please review and address the issues."
        exit 1
    fi
}

# Run main function with all arguments
main "$@"