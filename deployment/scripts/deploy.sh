#!/bin/bash

# DOI Application Deployment Script
# This script automates the deployment of the DOI management application

set -e  # Exit on any error

# Configuration
APP_NAME="doi-app"
APP_DIR="/opt/doi-app"
VENV_DIR="$APP_DIR/venv"
SERVICE_NAME="doi-app"
USER="doi-app"
GROUP="doi-app"

echo "=========================================="
echo "DOI Application Deployment Script"
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

# Create application user if it doesn't exist
create_app_user() {
    if ! id -u "$USER" > /dev/null 2>&1; then
        print_status "Creating application user: $USER"
        useradd -r -s /bin/false -d "$APP_DIR" "$USER"
        usermod -a -G "$GROUP" "$USER" 2>/dev/null || groupadd "$GROUP" && usermod -a -G "$GROUP" "$USER"
    else
        print_status "User $USER already exists"
    fi
}

# Create directory structure
create_directories() {
    print_status "Creating application directories"
    mkdir -p "$APP_DIR"
    mkdir -p "$APP_DIR/logs"
    mkdir -p "$APP_DIR/uploads"
    mkdir -p /etc/systemd/system
    
    # Set permissions
    chown -R "$USER:$GROUP" "$APP_DIR"
    chmod -R 755 "$APP_DIR"
    chmod -R 775 "$APP_DIR/logs"
    chmod -R 775 "$APP_DIR/uploads"
}

# Install system dependencies
install_system_dependencies() {
    print_status "Installing system dependencies"
    
    # Update package list
    apt update
    
    # Install required packages
    apt install -y python3 python3-pip python3-venv python3-dev
    apt install -y mysql-server mysql-client libmysqlclient-dev
    apt install -y nginx
    apt install -y git curl wget
    apt install -y certbot python3-certbot-nginx
    
    print_status "System dependencies installed successfully"
}

# Create virtual environment and install Python dependencies
setup_python_environment() {
    print_status "Setting up Python virtual environment"
    
    # Remove existing venv if it exists
    if [ -d "$VENV_DIR" ]; then
        rm -rf "$VENV_DIR"
    fi
    
    # Create new virtual environment
    python3 -m venv "$VENV_DIR"
    
    # Activate virtual environment and install dependencies
    source "$VENV_DIR/bin/activate"
    
    # Upgrade pip
    pip install --upgrade pip
    
    # Install application dependencies
    if [ -f "$APP_DIR/requirements.txt" ]; then
        pip install -r "$APP_DIR/requirements.txt"
    else
        print_warning "requirements.txt not found. Installing basic dependencies."
        pip install flask gunicorn flask-sqlalchemy flask-migrate flask-login flask-wtf flask-caching pymysql
    fi
    
    # Set ownership
    chown -R "$USER:$GROUP" "$VENV_DIR"
    
    print_status "Python environment setup completed"
}

# Copy application files
deploy_application() {
    print_status "Deploying application files"
    
    # Copy application files (assuming script is run from project root)
    if [ -d "app" ]; then
        cp -r app "$APP_DIR/"
        cp -r templates "$APP_DIR/" 2>/dev/null || true
        cp -r static "$APP_DIR/" 2>/dev/null || true
        cp requirements.txt "$APP_DIR/" 2>/dev/null || true
        cp gunicorn_config.py "$APP_DIR/"
        cp -r migrations "$APP_DIR/" 2>/dev/null || true
        
        # Set ownership
        chown -R "$USER:$GROUP" "$APP_DIR"
        
        print_status "Application files deployed successfully"
    else
        print_error "Application directory 'app' not found. Make sure you're running this script from the project root."
        exit 1
    fi
}

# Setup systemd service
setup_systemd_service() {
    print_status "Setting up systemd service"
    
    # Copy systemd service file
    if [ -f "deployment/systemd/doi-app.service" ]; then
        cp "deployment/systemd/doi-app.service" "/etc/systemd/system/"
        
        # Reload systemd and enable service
        systemctl daemon-reload
        systemctl enable "$SERVICE_NAME"
        
        print_status "Systemd service setup completed"
    else
        print_error "Systemd service file not found at deployment/systemd/doi-app.service"
        exit 1
    fi
}

# Run database migrations
run_database_migrations() {
    print_status "Running database migrations"
    
    cd "$APP_DIR"
    source "$VENV_DIR/bin/activate"
    
    # Check if .env file exists
    if [ -f ".env" ]; then
        export $(cat .env | xargs)
    else
        print_warning ".env file not found. Make sure to create it from production.env.template"
    fi
    
    # Initialize database if needed
    if [ ! -d "migrations" ]; then
        print_status "Initializing Flask-Migrate"
        python -m flask db init
    fi
    
    # Run migrations
    python -m flask db upgrade
    
    print_status "Database migrations completed"
}

# Start services
start_services() {
    print_status "Starting services"
    
    # Start and enable MySQL if not running
    systemctl start mysql
    systemctl enable mysql
    
    # Start application service
    systemctl start "$SERVICE_NAME"
    
    # Start and enable Nginx
    systemctl start nginx
    systemctl enable nginx
    
    print_status "Services started successfully"
}

# Verify deployment
verify_deployment() {
    print_status "Verifying deployment"
    
    # Check if service is running
    if systemctl is-active --quiet "$SERVICE_NAME"; then
        print_status "✓ DOI application service is running"
    else
        print_error "✗ DOI application service is not running"
        systemctl status "$SERVICE_NAME"
    fi
    
    # Check if Nginx is running
    if systemctl is-active --quiet nginx; then
        print_status "✓ Nginx service is running"
    else
        print_error "✗ Nginx service is not running"
        systemctl status nginx
    fi
    
    # Test health endpoint (if available)
    print_status "Testing health endpoint..."
    sleep 2  # Give services time to start
    
    if curl -f -s http://localhost:5000/health > /dev/null; then
        print_status "✓ Health endpoint is responding"
    else
        print_warning "Health endpoint test failed or not yet available"
    fi
}

# Main deployment flow
main() {
    print_status "Starting deployment process..."
    
    create_app_user
    create_directories
    install_system_dependencies
    deploy_application
    setup_python_environment
    setup_systemd_service
    run_database_migrations
    start_services
    verify_deployment
    
    echo ""
    echo "=========================================="
    echo "Deployment completed successfully!"
    echo "=========================================="
    echo ""
    echo "Next steps:"
    echo "1. Copy your .env file to $APP_DIR/.env"
    echo "2. Configure Nginx with SSL certificates (see deployment/nginx/doi-app.conf)"
    echo "3. Review logs: journalctl -u $SERVICE_NAME -f"
    echo "4. Test application: http://your-server-ip/"
    echo ""
}

# Run main function
main "$@"