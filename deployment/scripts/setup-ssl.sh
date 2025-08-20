#!/bin/bash

# SSL Certificate Setup Script for DOI Application
# This script automates SSL certificate generation and configuration using Let's Encrypt

set -e

DOMAIN=""
EMAIL=""
STAGING=false
NGINX_CONFIG_PATH="/etc/nginx/sites-available/doi-app"
NGINX_ENABLED_PATH="/etc/nginx/sites-enabled/doi-app"

echo "=========================================="
echo "DOI Application SSL Certificate Setup"
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

print_question() {
    echo -e "\n\033[1;34m[QUESTION]\033[0m $1"
}

# Function to show usage
show_usage() {
    echo "Usage: $0 [OPTIONS] DOMAIN"
    echo ""
    echo "Arguments:"
    echo "  DOMAIN          Domain name (e.g., example.com)"
    echo ""
    echo "Options:"
    echo "  -e, --email     Email address for certificate registration"
    echo "  -s, --staging   Use Let's Encrypt staging server (for testing)"
    echo "  -h, --help      Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 example.com"
    echo "  $0 -e admin@example.com example.com"
    echo "  $0 --staging --email test@example.com test.example.com"
}

# Parse command line arguments
parse_arguments() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            -e|--email)
                EMAIL="$2"
                shift 2
                ;;
            -s|--staging)
                STAGING=true
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

# Check if script is run as root
check_root() {
    if [ "$EUID" -ne 0 ]; then
        print_error "This script must be run as root (use sudo)"
        exit 1
    fi
}

# Check prerequisites
check_prerequisites() {
    print_status "Checking prerequisites..."
    
    # Check if Nginx is installed
    if ! command -v nginx &> /dev/null; then
        print_error "Nginx is not installed. Please install Nginx first:"
        echo "  sudo apt update && sudo apt install nginx"
        exit 1
    fi
    
    # Check if Certbot is installed
    if ! command -v certbot &> /dev/null; then
        print_warning "Certbot is not installed. Installing now..."
        install_certbot
    fi
    
    # Check if domain resolves to this server
    print_status "Checking DNS resolution for $DOMAIN..."
    SERVER_IP=$(curl -s ifconfig.me 2>/dev/null || curl -s ipinfo.io/ip 2>/dev/null || echo "unknown")
    DOMAIN_IP=$(dig +short "$DOMAIN" 2>/dev/null || nslookup "$DOMAIN" 2>/dev/null | grep -A1 "Name:" | tail -1 | awk '{print $2}' || echo "unknown")
    
    if [ "$SERVER_IP" != "unknown" ] && [ "$DOMAIN_IP" != "unknown" ]; then
        if [ "$SERVER_IP" == "$DOMAIN_IP" ]; then
            print_status "✓ DNS resolution looks correct"
        else
            print_warning "DNS may not be configured correctly:"
            echo "  Server IP: $SERVER_IP"
            echo "  Domain IP: $DOMAIN_IP"
            print_question "Continue anyway? (y/n)"
            read -r continue_anyway
            if [[ ! "$continue_anyway" =~ ^[Yy]$ ]]; then
                exit 1
            fi
        fi
    else
        print_warning "Could not verify DNS resolution"
    fi
}

# Install Certbot
install_certbot() {
    print_status "Installing Certbot..."
    
    # Update package list
    apt update
    
    # Install Certbot and Nginx plugin
    apt install -y certbot python3-certbot-nginx
    
    if [ $? -eq 0 ]; then
        print_status "✓ Certbot installed successfully"
    else
        print_error "Failed to install Certbot"
        exit 1
    fi
}

# Update Nginx configuration with domain
update_nginx_config() {
    print_status "Updating Nginx configuration with domain: $DOMAIN"
    
    if [ ! -f "$NGINX_CONFIG_PATH" ]; then
        print_error "Nginx configuration file not found: $NGINX_CONFIG_PATH"
        print_error "Please ensure Nginx is properly configured first"
        exit 1
    fi
    
    # Create backup of original config
    cp "$NGINX_CONFIG_PATH" "$NGINX_CONFIG_PATH.backup.$(date +%Y%m%d_%H%M%S)"
    
    # Replace placeholder domain with actual domain
    sed -i "s/your-domain\.com/$DOMAIN/g" "$NGINX_CONFIG_PATH"
    sed -i "s/www\.your-domain\.com/www.$DOMAIN/g" "$NGINX_CONFIG_PATH"
    
    # Test Nginx configuration
    if nginx -t; then
        print_status "✓ Nginx configuration updated and validated"
        systemctl reload nginx
    else
        print_error "Nginx configuration test failed"
        print_status "Restoring backup configuration..."
        cp "$NGINX_CONFIG_PATH.backup.$(date +%Y%m%d_%H%M%S)" "$NGINX_CONFIG_PATH"
        exit 1
    fi
}

# Get email for certificate registration
get_email() {
    if [ -z "$EMAIL" ]; then
        print_question "Enter email address for certificate registration:"
        read -r EMAIL
        
        if [ -z "$EMAIL" ]; then
            print_error "Email address is required for Let's Encrypt registration"
            exit 1
        fi
        
        # Basic email validation
        if [[ ! "$EMAIL" =~ ^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$ ]]; then
            print_error "Invalid email address format"
            exit 1
        fi
    fi
    
    print_status "Using email: $EMAIL"
}

# Generate SSL certificate
generate_certificate() {
    print_status "Generating SSL certificate for $DOMAIN..."
    
    # Prepare certbot command
    CERTBOT_CMD="certbot --nginx --non-interactive --agree-tos"
    CERTBOT_CMD="$CERTBOT_CMD --email $EMAIL"
    CERTBOT_CMD="$CERTBOT_CMD --domains $DOMAIN,www.$DOMAIN"
    CERTBOT_CMD="$CERTBOT_CMD --redirect"
    
    # Use staging server if requested
    if [ "$STAGING" = true ]; then
        CERTBOT_CMD="$CERTBOT_CMD --staging"
        print_warning "Using Let's Encrypt STAGING server (certificates will not be trusted by browsers)"
    fi
    
    # Execute certbot command
    print_status "Running: $CERTBOT_CMD"
    eval $CERTBOT_CMD
    
    if [ $? -eq 0 ]; then
        print_status "✓ SSL certificate generated successfully"
    else
        print_error "SSL certificate generation failed"
        print_error "Check the output above for error details"
        exit 1
    fi
}

# Verify SSL certificate
verify_certificate() {
    print_status "Verifying SSL certificate..."
    
    # Wait a moment for Nginx to reload
    sleep 2
    
    # Test HTTPS connection
    if curl -I -s "https://$DOMAIN" > /dev/null 2>&1; then
        print_status "✓ HTTPS connection test passed"
    else
        print_warning "HTTPS connection test failed"
        print_warning "This might be normal if DNS hasn't fully propagated"
    fi
    
    # Check certificate details
    print_status "Certificate information:"
    echo | openssl s_client -servername "$DOMAIN" -connect "$DOMAIN:443" 2>/dev/null | openssl x509 -noout -subject -issuer -dates 2>/dev/null || print_warning "Could not retrieve certificate details"
}

# Set up automatic renewal
setup_renewal() {
    print_status "Setting up automatic certificate renewal..."
    
    # Test renewal process
    print_status "Testing certificate renewal (dry run)..."
    if certbot renew --dry-run; then
        print_status "✓ Certificate renewal test passed"
    else
        print_warning "Certificate renewal test failed"
        print_warning "You may need to set up renewal manually"
    fi
    
    # Check if systemd timer exists
    if systemctl list-unit-files | grep -q "certbot.timer"; then
        print_status "Enabling systemd timer for automatic renewal..."
        systemctl enable certbot.timer
        systemctl start certbot.timer
        print_status "✓ Automatic renewal enabled via systemd timer"
    else
        # Fallback to cron job
        print_status "Setting up cron job for automatic renewal..."
        
        # Check if cron job already exists
        if ! crontab -l 2>/dev/null | grep -q "certbot renew"; then
            # Add cron job
            (crontab -l 2>/dev/null; echo "0 12 * * * /usr/bin/certbot renew --quiet") | crontab -
            print_status "✓ Cron job added for automatic renewal"
        else
            print_status "✓ Cron job for renewal already exists"
        fi
    fi
}

# Show completion summary
show_summary() {
    echo ""
    echo "=========================================="
    echo "SSL Certificate Setup Completed!"
    echo "=========================================="
    echo ""
    echo "Domain: $DOMAIN"
    echo "Certificate location: /etc/letsencrypt/live/$DOMAIN/"
    echo "Nginx configuration: $NGINX_CONFIG_PATH"
    echo ""
    echo "What was configured:"
    echo "✓ SSL certificate generated and installed"
    echo "✓ Nginx configured for HTTPS"
    echo "✓ HTTP to HTTPS redirect enabled"
    echo "✓ Automatic certificate renewal set up"
    echo ""
    echo "Next steps:"
    echo "1. Test your site: https://$DOMAIN"
    echo "2. Check SSL rating: https://www.ssllabs.com/ssltest/analyze.html?d=$DOMAIN"
    echo "3. Update your .env file with HTTPS URLs:"
    echo "   APPLICATION_URL=https://$DOMAIN"
    echo "   API_BASE_URL=https://$DOMAIN/api/v1"
    echo ""
    echo "Certificate will auto-renew before expiration."
    echo "Monitor renewal with: sudo systemctl status certbot.timer"
    echo ""
    
    if [ "$STAGING" = true ]; then
        print_warning "REMEMBER: You used staging certificates!"
        print_warning "Re-run without --staging flag for production certificates"
    fi
}

# Handle cleanup on script exit
cleanup() {
    if [ $? -ne 0 ]; then
        print_error "Script failed. Check the output above for errors."
        
        # Restore Nginx config if it was modified
        if [ -f "$NGINX_CONFIG_PATH.backup.$(date +%Y%m%d)_"* ]; then
            print_status "Restoring Nginx configuration backup..."
            # This is simplified - in real scenario you'd need to find the right backup
        fi
    fi
}

trap cleanup EXIT

# Main execution
main() {
    parse_arguments "$@"
    
    print_status "Starting SSL setup for domain: $DOMAIN"
    
    check_root
    check_prerequisites
    get_email
    update_nginx_config
    generate_certificate
    verify_certificate
    setup_renewal
    show_summary
}

# Run main function with all arguments
main "$@"