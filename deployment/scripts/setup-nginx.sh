#!/bin/bash

# Nginx Setup Script for DOI Application

set -e

NGINX_AVAILABLE="/etc/nginx/sites-available"
NGINX_ENABLED="/etc/nginx/sites-enabled"
SITE_NAME="doi-app"
CONFIG_SOURCE="deployment/nginx/doi-app.conf"

echo "=========================================="
echo "Setting up Nginx for DOI Application"
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
if [ "$EUID" -ne 0 ]; then
    print_error "This script must be run as root (use sudo)"
    exit 1
fi

# Check if Nginx is installed
if ! command -v nginx &> /dev/null; then
    print_error "Nginx is not installed. Please install it first:"
    echo "  sudo apt update && sudo apt install nginx"
    exit 1
fi

# Check if config file exists
if [ ! -f "$CONFIG_SOURCE" ]; then
    print_error "Nginx configuration file not found: $CONFIG_SOURCE"
    print_error "Make sure you're running this script from the project root directory"
    exit 1
fi

# Copy configuration file
print_status "Copying Nginx configuration..."
cp "$CONFIG_SOURCE" "$NGINX_AVAILABLE/$SITE_NAME"

# Create symbolic link to enable site
print_status "Enabling site..."
if [ -L "$NGINX_ENABLED/$SITE_NAME" ]; then
    print_warning "Site is already enabled, removing old symlink"
    rm "$NGINX_ENABLED/$SITE_NAME"
fi

ln -s "$NGINX_AVAILABLE/$SITE_NAME" "$NGINX_ENABLED/$SITE_NAME"

# Remove default Nginx site if it exists
if [ -L "$NGINX_ENABLED/default" ]; then
    print_status "Removing default Nginx site"
    rm "$NGINX_ENABLED/default"
fi

# Test Nginx configuration
print_status "Testing Nginx configuration..."
if nginx -t; then
    print_status "✓ Nginx configuration is valid"
else
    print_error "✗ Nginx configuration test failed"
    print_error "Please check the configuration file and try again"
    exit 1
fi

# Create directories for logs if they don't exist
print_status "Creating log directories..."
mkdir -p /var/log/nginx

# Create directories for static files and error pages
print_status "Setting up static file directories..."
mkdir -p /var/www/html

# Create basic error pages if they don't exist
create_error_pages() {
    if [ ! -f "/var/www/html/404.html" ]; then
        cat > /var/www/html/404.html << 'EOF'
<!DOCTYPE html>
<html>
<head>
    <title>404 - Page Not Found</title>
    <style>
        body { font-family: Arial, sans-serif; text-align: center; margin-top: 50px; }
        h1 { color: #333; }
        p { color: #666; }
    </style>
</head>
<body>
    <h1>404 - Page Not Found</h1>
    <p>The page you're looking for doesn't exist.</p>
    <a href="/">Go back to homepage</a>
</body>
</html>
EOF
    fi

    if [ ! -f "/var/www/html/50x.html" ]; then
        cat > /var/www/html/50x.html << 'EOF'
<!DOCTYPE html>
<html>
<head>
    <title>500 - Server Error</title>
    <style>
        body { font-family: Arial, sans-serif; text-align: center; margin-top: 50px; }
        h1 { color: #d32f2f; }
        p { color: #666; }
    </style>
</head>
<body>
    <h1>Server Error</h1>
    <p>We're experiencing technical difficulties. Please try again later.</p>
</body>
</html>
EOF
    fi
}

create_error_pages

# Reload Nginx configuration
print_status "Reloading Nginx..."
systemctl reload nginx

# Check if Nginx is running
if systemctl is-active --quiet nginx; then
    print_status "✓ Nginx is running successfully"
else
    print_warning "Starting Nginx..."
    systemctl start nginx
    
    if systemctl is-active --quiet nginx; then
        print_status "✓ Nginx started successfully"
    else
        print_error "✗ Failed to start Nginx"
        systemctl status nginx
        exit 1
    fi
fi

echo ""
echo "=========================================="
echo "Nginx setup completed successfully!"
echo "=========================================="
echo ""
echo "Configuration details:"
echo "- Site config: $NGINX_AVAILABLE/$SITE_NAME"
echo "- Site enabled: $NGINX_ENABLED/$SITE_NAME"
echo "- Access logs: /var/log/nginx/doi-app-access.log"
echo "- Error logs: /var/log/nginx/doi-app-error.log"
echo ""
echo "Important notes:"
echo "1. Update server_name in the config file with your actual domain"
echo "2. Configure SSL certificates for HTTPS (see SSL setup documentation)"
echo "3. Test the configuration with: nginx -t"
echo "4. Reload Nginx after changes: systemctl reload nginx"
echo ""
echo "Nginx status: $(systemctl is-active nginx)"