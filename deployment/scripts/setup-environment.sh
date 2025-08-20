#!/bin/bash

# Environment Setup Script for DOI Application
# This script helps create and validate the production environment configuration

set -e

ENV_TEMPLATE="production.env.template"
ENV_FILE=".env"
BACKUP_ENV=".env.backup"

echo "=========================================="
echo "DOI Application Environment Setup"
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

# Check if template file exists
if [ ! -f "$ENV_TEMPLATE" ]; then
    print_error "Environment template file '$ENV_TEMPLATE' not found!"
    print_error "Make sure you're running this script from the project root directory."
    exit 1
fi

# Backup existing .env file if it exists
backup_existing_env() {
    if [ -f "$ENV_FILE" ]; then
        print_warning "Existing .env file found. Creating backup..."
        cp "$ENV_FILE" "$BACKUP_ENV.$(date +%Y%m%d_%H%M%S)"
        print_status "Backup created: $BACKUP_ENV.$(date +%Y%m%d_%H%M%S)"
    fi
}

# Generate secure secret key
generate_secret_key() {
    python3 -c "import secrets; print(secrets.token_urlsafe(32))"
}

# Interactive environment setup
interactive_setup() {
    print_status "Starting interactive environment setup..."
    
    # Create temporary .env file
    cp "$ENV_TEMPLATE" "$ENV_FILE"
    
    print_question "Would you like to use interactive setup? (y/n)"
    read -r use_interactive
    
    if [[ "$use_interactive" =~ ^[Yy]$ ]]; then
        
        # Secret Key
        print_question "Generating secure SECRET_KEY..."
        SECRET_KEY=$(generate_secret_key)
        sed -i "s/your-super-secret-key-here-change-this-in-production/$SECRET_KEY/g" "$ENV_FILE"
        print_status "✓ Secret key generated and set"
        
        # Database Configuration
        print_question "Enter database host [localhost]:"
        read -r db_host
        db_host=${db_host:-localhost}
        
        print_question "Enter database port [3306]:"
        read -r db_port
        db_port=${db_port:-3306}
        
        print_question "Enter database name [doi_db]:"
        read -r db_name
        db_name=${db_name:-doi_db}
        
        print_question "Enter database username:"
        read -r db_user
        
        print_question "Enter database password:"
        read -s db_password
        echo
        
        # Update database configuration
        sed -i "s/localhost/$db_host/g" "$ENV_FILE"
        sed -i "s/3306/$db_port/g" "$ENV_FILE"
        sed -i "s/doi_db/$db_name/g" "$ENV_FILE"
        sed -i "s/doi_user/$db_user/g" "$ENV_FILE"
        sed -i "s/your_database_password_here/$db_password/g" "$ENV_FILE"
        
        # Construct DATABASE_URL
        DATABASE_URL="mysql+pymysql://$db_user:$db_password@$db_host:$db_port/$db_name"
        sed -i "s|mysql+pymysql://doi_user:your_password@localhost:3306/doi_db|$DATABASE_URL|g" "$ENV_FILE"
        
        print_status "✓ Database configuration updated"
        
        # Domain Configuration
        print_question "Enter your domain name (e.g., example.com):"
        read -r domain_name
        if [ -n "$domain_name" ]; then
            sed -i "s/your-domain.com/$domain_name/g" "$ENV_FILE"
            sed -i "s|https://your-domain.com|https://$domain_name|g" "$ENV_FILE"
            print_status "✓ Domain configuration updated"
        fi
        
        # Sentry Configuration (optional)
        print_question "Do you want to configure Sentry for error tracking? (y/n)"
        read -r use_sentry
        if [[ "$use_sentry" =~ ^[Yy]$ ]]; then
            print_question "Enter your Sentry DSN:"
            read -r sentry_dsn
            if [ -n "$sentry_dsn" ]; then
                sed -i "s|https://your-sentry-dsn-here@sentry.io/project-id|$sentry_dsn|g" "$ENV_FILE"
                print_status "✓ Sentry configuration updated"
            fi
        fi
        
        print_status "Interactive setup completed!"
        
    else
        print_warning "Skipping interactive setup. Please manually edit $ENV_FILE"
        print_warning "Make sure to update all placeholder values before deployment!"
    fi
}

# Validate environment configuration
validate_environment() {
    print_status "Validating environment configuration..."
    
    if [ ! -f "$ENV_FILE" ]; then
        print_error ".env file not found. Please run setup first."
        return 1
    fi
    
    # Source the environment file
    set -a  # automatically export all variables
    source "$ENV_FILE"
    set +a
    
    errors=0
    
    # Check critical variables
    if [ "$SECRET_KEY" = "your-super-secret-key-here-change-this-in-production" ]; then
        print_error "SECRET_KEY is still set to default value"
        errors=$((errors + 1))
    fi
    
    if [[ "$DATABASE_URL" == *"your_password"* ]]; then
        print_error "DATABASE_URL contains placeholder values"
        errors=$((errors + 1))
    fi
    
    if [[ "$DATABASE_URL" == *"doi_user:your_password"* ]]; then
        print_error "Database credentials are still set to placeholder values"
        errors=$((errors + 1))
    fi
    
    # Test database connection (optional)
    print_question "Would you like to test database connection? (y/n)"
    read -r test_db
    if [[ "$test_db" =~ ^[Yy]$ ]]; then
        print_status "Testing database connection..."
        
        if command -v python3 &> /dev/null; then
            python3 -c "
import os
import sys
sys.path.insert(0, '.')
try:
    from sqlalchemy import create_engine
    engine = create_engine('$DATABASE_URL')
    connection = engine.connect()
    connection.close()
    print('✓ Database connection successful')
except Exception as e:
    print(f'✗ Database connection failed: {e}')
    sys.exit(1)
"
            if [ $? -eq 0 ]; then
                print_status "✓ Database connection test passed"
            else
                print_error "✗ Database connection test failed"
                errors=$((errors + 1))
            fi
        else
            print_warning "Python3 not available, skipping database connection test"
        fi
    fi
    
    if [ $errors -eq 0 ]; then
        print_status "✅ Environment validation passed!"
        return 0
    else
        print_error "❌ Environment validation failed with $errors errors"
        return 1
    fi
}

# Show environment summary
show_summary() {
    print_status "Environment Configuration Summary:"
    echo ""
    echo "Files created/modified:"
    echo "- $ENV_FILE (main environment file)"
    
    if [ -f "$BACKUP_ENV"* ]; then
        echo "- $BACKUP_ENV.* (backup files)"
    fi
    
    echo ""
    echo "Next steps:"
    echo "1. Review and customize $ENV_FILE as needed"
    echo "2. Ensure MySQL database '$DB_NAME' exists and is accessible"
    echo "3. Run deployment script: sudo ./deployment/scripts/deploy.sh"
    echo "4. Configure SSL certificates for HTTPS"
    echo ""
    print_warning "SECURITY NOTE: Never commit .env files to version control!"
}

# Main execution flow
main() {
    case "${1:-setup}" in
        "setup"|"")
            backup_existing_env
            interactive_setup
            validate_environment
            show_summary
            ;;
        "validate")
            validate_environment
            ;;
        "help")
            echo "Usage: $0 [setup|validate|help]"
            echo ""
            echo "Commands:"
            echo "  setup     - Interactive environment setup (default)"
            echo "  validate  - Validate existing environment configuration"
            echo "  help      - Show this help message"
            ;;
        *)
            print_error "Unknown command: $1"
            echo "Use '$0 help' for usage information"
            exit 1
            ;;
    esac
}

# Run main function with all arguments
main "$@"