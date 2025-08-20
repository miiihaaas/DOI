#!/bin/bash

# SSL Certificate Monitoring Script for DOI Application
# This script monitors SSL certificate health and expiration

set -e

DOMAIN=""
WARN_DAYS=30
CRITICAL_DAYS=7
LOG_FILE="/var/log/ssl-monitor.log"
QUIET=false
CHECK_ONLY=false

echo "=========================================="
echo "DOI Application SSL Monitor"
echo "=========================================="

# Function to print colored output
print_status() {
    if [ "$QUIET" = false ]; then
        echo -e "\n\033[1;32m[INFO]\033[0m $1"
    fi
    echo "$(date '+%Y-%m-%d %H:%M:%S') [INFO] $1" >> "$LOG_FILE"
}

print_error() {
    echo -e "\n\033[1;31m[ERROR]\033[0m $1" >&2
    echo "$(date '+%Y-%m-%d %H:%M:%S') [ERROR] $1" >> "$LOG_FILE"
}

print_warning() {
    echo -e "\n\033[1;33m[WARNING]\033[0m $1" >&2
    echo "$(date '+%Y-%m-%d %H:%M:%S') [WARNING] $1" >> "$LOG_FILE"
}

print_critical() {
    echo -e "\n\033[1;31m[CRITICAL]\033[0m $1" >&2
    echo "$(date '+%Y-%m-%d %H:%M:%S') [CRITICAL] $1" >> "$LOG_FILE"
}

# Function to show usage
show_usage() {
    echo "Usage: $0 [OPTIONS] DOMAIN"
    echo ""
    echo "Arguments:"
    echo "  DOMAIN          Domain name to monitor (e.g., example.com)"
    echo ""
    echo "Options:"
    echo "  -w, --warn      Warning threshold in days (default: 30)"
    echo "  -c, --critical  Critical threshold in days (default: 7)"
    echo "  -l, --log       Log file path (default: /var/log/ssl-monitor.log)"
    echo "  -q, --quiet     Suppress console output"
    echo "  --check-only    Only check expiration, don't test connection"
    echo "  -h, --help      Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 example.com"
    echo "  $0 -w 45 -c 14 example.com"
    echo "  $0 --quiet --log /opt/doi-app/logs/ssl.log example.com"
}

# Parse command line arguments
parse_arguments() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            -w|--warn)
                WARN_DAYS="$2"
                shift 2
                ;;
            -c|--critical)
                CRITICAL_DAYS="$2" 
                shift 2
                ;;
            -l|--log)
                LOG_FILE="$2"
                shift 2
                ;;
            -q|--quiet)
                QUIET=true
                shift
                ;;
            --check-only)
                CHECK_ONLY=true
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
                if [ -z "$DOMAIN" ]; then
                    DOMAIN="$1"
                else
                    print_error "Multiple domains not supported in this script"
                    exit 1
                fi
                shift
                ;;
        esac
    done
    
    if [ -z "$DOMAIN" ]; then
        print_error "Domain name is required"
        show_usage
        exit 1
    fi
}

# Initialize log file
init_log() {
    # Create log directory if it doesn't exist
    mkdir -p "$(dirname "$LOG_FILE")"
    
    # Initialize log file
    if [ ! -f "$LOG_FILE" ]; then
        touch "$LOG_FILE"
    fi
    
    print_status "SSL monitoring started for domain: $DOMAIN"
}

# Check if OpenSSL is available
check_prerequisites() {
    if ! command -v openssl &> /dev/null; then
        print_error "OpenSSL is not installed"
        exit 1
    fi
    
    if [ "$CHECK_ONLY" = false ]; then
        if ! command -v curl &> /dev/null; then
            print_warning "curl is not installed, skipping connection tests"
            CHECK_ONLY=true
        fi
    fi
}

# Get certificate expiration date
get_cert_expiry() {
    local domain="$1"
    local port="${2:-443}"
    
    # Get certificate expiration date
    local expiry_output
    expiry_output=$(echo | openssl s_client -servername "$domain" -connect "$domain:$port" 2>/dev/null | openssl x509 -noout -dates 2>/dev/null)
    
    if [ $? -ne 0 ] || [ -z "$expiry_output" ]; then
        print_error "Failed to retrieve certificate for $domain"
        return 1
    fi
    
    # Extract the "not after" date
    local expiry_string
    expiry_string=$(echo "$expiry_output" | grep "notAfter=" | cut -d= -f2)
    
    if [ -z "$expiry_string" ]; then
        print_error "Could not parse certificate expiry date"
        return 1
    fi
    
    echo "$expiry_string"
}

# Calculate days until expiration
days_until_expiry() {
    local expiry_date="$1"
    
    # Convert expiry date to epoch
    local expiry_epoch
    expiry_epoch=$(date -d "$expiry_date" +%s 2>/dev/null)
    
    if [ $? -ne 0 ]; then
        print_error "Invalid date format: $expiry_date"
        return 1
    fi
    
    # Get current epoch
    local current_epoch
    current_epoch=$(date +%s)
    
    # Calculate difference in days
    local days_diff
    days_diff=$(( (expiry_epoch - current_epoch) / 86400 ))
    
    echo "$days_diff"
}

# Check SSL certificate
check_ssl_certificate() {
    local domain="$1"
    
    print_status "Checking SSL certificate for $domain..."
    
    # Get certificate expiry
    local expiry_date
    expiry_date=$(get_cert_expiry "$domain")
    
    if [ $? -ne 0 ]; then
        print_error "Failed to get certificate expiry for $domain"
        return 1
    fi
    
    print_status "Certificate expires: $expiry_date"
    
    # Calculate days until expiry
    local days_left
    days_left=$(days_until_expiry "$expiry_date")
    
    if [ $? -ne 0 ]; then
        print_error "Failed to calculate days until expiry"
        return 1
    fi
    
    print_status "Days until expiry: $days_left"
    
    # Check thresholds
    if [ "$days_left" -lt 0 ]; then
        print_critical "CERTIFICATE EXPIRED $((days_left * -1)) days ago!"
        return 2
    elif [ "$days_left" -le "$CRITICAL_DAYS" ]; then
        print_critical "Certificate expires in $days_left days (critical threshold: $CRITICAL_DAYS days)"
        return 2
    elif [ "$days_left" -le "$WARN_DAYS" ]; then
        print_warning "Certificate expires in $days_left days (warning threshold: $WARN_DAYS days)"
        return 1
    else
        print_status "✓ Certificate is valid for $days_left days"
        return 0
    fi
}

# Test SSL connection
test_ssl_connection() {
    local domain="$1"
    
    if [ "$CHECK_ONLY" = true ]; then
        return 0
    fi
    
    print_status "Testing SSL connection to $domain..."
    
    # Test HTTPS connection
    local response_code
    response_code=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 10 --max-time 30 "https://$domain" 2>/dev/null)
    
    if [ $? -eq 0 ] && [[ "$response_code" =~ ^[2-3] ]]; then
        print_status "✓ HTTPS connection successful (HTTP $response_code)"
        return 0
    else
        print_error "HTTPS connection failed (HTTP $response_code)"
        return 1
    fi
}

# Check certificate chain
check_cert_chain() {
    local domain="$1"
    
    print_status "Checking certificate chain for $domain..."
    
    # Get full certificate chain
    local chain_output
    chain_output=$(echo | openssl s_client -servername "$domain" -connect "$domain:443" -showcerts 2>/dev/null)
    
    if [ $? -ne 0 ]; then
        print_error "Failed to retrieve certificate chain"
        return 1
    fi
    
    # Count certificates in chain
    local cert_count
    cert_count=$(echo "$chain_output" | grep -c "BEGIN CERTIFICATE")
    
    print_status "Certificate chain contains $cert_count certificates"
    
    if [ "$cert_count" -lt 2 ]; then
        print_warning "Certificate chain may be incomplete (only $cert_count certificates)"
        return 1
    else
        print_status "✓ Certificate chain appears complete"
        return 0
    fi
}

# Get certificate details
get_cert_details() {
    local domain="$1"
    
    print_status "Retrieving certificate details for $domain..."
    
    # Get certificate info
    local cert_info
    cert_info=$(echo | openssl s_client -servername "$domain" -connect "$domain:443" 2>/dev/null | openssl x509 -noout -text 2>/dev/null)
    
    if [ $? -ne 0 ]; then
        print_error "Failed to retrieve certificate details"
        return 1
    fi
    
    # Extract key information
    local issuer
    issuer=$(echo "$cert_info" | grep "Issuer:" | head -1 | sed 's/^[[:space:]]*//')
    
    local subject
    subject=$(echo "$cert_info" | grep "Subject:" | head -1 | sed 's/^[[:space:]]*//')
    
    local san
    san=$(echo "$cert_info" | grep -A1 "Subject Alternative Name:" | tail -1 | sed 's/^[[:space:]]*//')
    
    print_status "Certificate details:"
    echo "$issuer" | tee -a "$LOG_FILE"
    echo "$subject" | tee -a "$LOG_FILE"
    if [ -n "$san" ]; then
        echo "    Subject Alternative Names: $san" | tee -a "$LOG_FILE"
    fi
    
    # Check if it's a Let's Encrypt certificate
    if echo "$issuer" | grep -q "Let's Encrypt"; then
        print_status "✓ Certificate issued by Let's Encrypt"
    fi
}

# Check OCSP stapling
check_ocsp_stapling() {
    local domain="$1"
    
    print_status "Checking OCSP stapling for $domain..."
    
    local ocsp_output
    ocsp_output=$(echo | openssl s_client -servername "$domain" -connect "$domain:443" -status 2>/dev/null | grep "OCSP Response Status")
    
    if [ -n "$ocsp_output" ]; then
        print_status "✓ OCSP stapling is enabled"
        echo "    $ocsp_output" | tee -a "$LOG_FILE"
    else
        print_warning "OCSP stapling not detected"
    fi
}

# Generate monitoring report
generate_report() {
    local domain="$1"
    local cert_status="$2"
    local conn_status="$3"
    
    local report_file="/tmp/ssl-monitor-report-$(date +%Y%m%d_%H%M%S).txt"
    
    cat > "$report_file" << EOF
SSL Certificate Monitor Report
Generated: $(date)
Domain: $domain

Certificate Status: $([ "$cert_status" -eq 0 ] && echo "OK" || [ "$cert_status" -eq 1 ] && echo "WARNING" || echo "CRITICAL")
Connection Status: $([ "$conn_status" -eq 0 ] && echo "OK" || echo "FAILED")

Detailed logs available in: $LOG_FILE

EOF
    
    print_status "Report generated: $report_file"
    
    if [ "$QUIET" = false ]; then
        cat "$report_file"
    fi
}

# Send notification (placeholder for future integration)
send_notification() {
    local message="$1"
    local severity="$2"
    
    # This is a placeholder for notification integration
    # You can integrate with email, Slack, webhook, etc.
    
    print_status "Notification: $message (severity: $severity)"
    
    # Example: send email (requires mail command)
    # echo "$message" | mail -s "SSL Certificate Alert" admin@example.com
    
    # Example: send to webhook
    # curl -X POST -H 'Content-type: application/json' --data '{"text":"'$message'"}' YOUR_WEBHOOK_URL
}

# Main monitoring function
monitor_ssl() {
    local domain="$1"
    local cert_status=0
    local conn_status=0
    local overall_status=0
    
    # Check certificate expiration
    check_ssl_certificate "$domain"
    cert_status=$?
    
    # Test connection
    test_ssl_connection "$domain"
    conn_status=$?
    
    # Additional checks
    check_cert_chain "$domain"
    get_cert_details "$domain"
    check_ocsp_stapling "$domain"
    
    # Determine overall status
    if [ "$cert_status" -eq 2 ] || [ "$conn_status" -ne 0 ]; then
        overall_status=2  # Critical
    elif [ "$cert_status" -eq 1 ]; then
        overall_status=1  # Warning
    else
        overall_status=0  # OK
    fi
    
    # Generate report
    generate_report "$domain" "$cert_status" "$conn_status"
    
    # Send notifications based on status
    case $overall_status in
        2)
            send_notification "CRITICAL: SSL certificate issue detected for $domain" "critical"
            ;;
        1)
            send_notification "WARNING: SSL certificate warning for $domain" "warning"
            ;;
        0)
            if [ "$QUIET" = false ]; then
                send_notification "OK: SSL certificate healthy for $domain" "info"
            fi
            ;;
    esac
    
    return $overall_status
}

# Main execution
main() {
    parse_arguments "$@"
    check_prerequisites
    init_log
    
    monitor_ssl "$DOMAIN"
    exit_code=$?
    
    case $exit_code in
        0)
            print_status "✅ SSL monitoring completed successfully"
            ;;
        1)
            print_warning "⚠️ SSL monitoring completed with warnings"
            ;;
        2)
            print_critical "❌ SSL monitoring detected critical issues"
            ;;
    esac
    
    exit $exit_code
}

# Run main function with all arguments
main "$@"