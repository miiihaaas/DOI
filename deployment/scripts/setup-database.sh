#!/bin/bash

# Database Setup and Migration Management Script for DOI Application

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"
APP_DIR="/opt/doi-app"

echo "=========================================="
echo "DOI Application Database Setup"
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

# Load environment variables
load_environment() {
    if [ -f "$PROJECT_ROOT/.env" ]; then
        print_status "Loading environment from $PROJECT_ROOT/.env"
        set -a
        source "$PROJECT_ROOT/.env"
        set +a
    elif [ -f "$APP_DIR/.env" ]; then
        print_status "Loading environment from $APP_DIR/.env"
        set -a
        source "$APP_DIR/.env"
        set +a
    else
        print_warning "No .env file found. Using environment variables or defaults."
    fi
}

# Check if MySQL client is available
check_mysql_client() {
    if ! command -v mysql &> /dev/null; then
        print_error "MySQL client not found. Please install mysql-client:"
        echo "  sudo apt update && sudo apt install mysql-client"
        exit 1
    fi
}

# Parse database URL to get connection parameters
parse_database_url() {
    if [ -z "$DATABASE_URL" ]; then
        print_error "DATABASE_URL not set. Please configure your environment."
        exit 1
    fi
    
    # Extract components from DATABASE_URL
    # Format: mysql+pymysql://username:password@host:port/database
    DB_USER=$(echo "$DATABASE_URL" | sed -n 's/.*:\/\/\([^:]*\):.*/\1/p')
    DB_PASS=$(echo "$DATABASE_URL" | sed -n 's/.*:\/\/[^:]*:\([^@]*\)@.*/\1/p')
    DB_HOST=$(echo "$DATABASE_URL" | sed -n 's/.*@\([^:]*\):.*/\1/p')
    DB_PORT=$(echo "$DATABASE_URL" | sed -n 's/.*:\([0-9]*\)\/.*/\1/p')
    DB_NAME=$(echo "$DATABASE_URL" | sed -n 's/.*\/\([^?]*\).*/\1/p')
    
    print_status "Database connection details:"
    echo "  Host: $DB_HOST"
    echo "  Port: $DB_PORT" 
    echo "  Database: $DB_NAME"
    echo "  User: $DB_USER"
}

# Test database connection
test_database_connection() {
    print_status "Testing database connection..."
    
    if mysql -h "$DB_HOST" -P "$DB_PORT" -u "$DB_USER" -p"$DB_PASS" -e "SELECT 1;" > /dev/null 2>&1; then
        print_status "✓ Database connection successful"
        return 0
    else
        print_error "✗ Database connection failed"
        print_error "Please check your database credentials and ensure MySQL server is running"
        return 1
    fi
}

# Create database if it doesn't exist
create_database() {
    print_status "Checking if database '$DB_NAME' exists..."
    
    if mysql -h "$DB_HOST" -P "$DB_PORT" -u "$DB_USER" -p"$DB_PASS" -e "USE $DB_NAME;" > /dev/null 2>&1; then
        print_status "✓ Database '$DB_NAME' already exists"
    else
        print_warning "Database '$DB_NAME' does not exist"
        print_question "Would you like to create it? (y/n)"
        read -r create_db
        
        if [[ "$create_db" =~ ^[Yy]$ ]]; then
            print_status "Creating database '$DB_NAME'..."
            mysql -h "$DB_HOST" -P "$DB_PORT" -u "$DB_USER" -p"$DB_PASS" -e "CREATE DATABASE IF NOT EXISTS $DB_NAME CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
            
            if [ $? -eq 0 ]; then
                print_status "✓ Database '$DB_NAME' created successfully"
            else
                print_error "✗ Failed to create database '$DB_NAME'"
                exit 1
            fi
        else
            print_error "Database creation cancelled. Please create the database manually."
            exit 1
        fi
    fi
}

# Initialize Flask-Migrate if needed
initialize_migrations() {
    print_status "Checking migration status..."
    
    # Change to the appropriate directory
    if [ -d "$APP_DIR" ]; then
        cd "$APP_DIR"
    else
        cd "$PROJECT_ROOT"
    fi
    
    # Activate virtual environment if it exists
    if [ -f "venv/bin/activate" ]; then
        source venv/bin/activate
        print_status "Activated virtual environment"
    fi
    
    # Check if migrations directory exists
    if [ ! -d "migrations" ]; then
        print_status "Initializing Flask-Migrate..."
        flask db init
        
        if [ $? -eq 0 ]; then
            print_status "✓ Flask-Migrate initialized"
        else
            print_error "✗ Failed to initialize Flask-Migrate"
            exit 1
        fi
    else
        print_status "✓ Migrations directory already exists"
    fi
}

# Generate initial migration
generate_initial_migration() {
    print_status "Generating initial migration..."
    
    # Check if there are any migration files
    if [ -z "$(ls -A migrations/versions/ 2>/dev/null)" ]; then
        print_status "Creating initial migration for existing models..."
        flask db migrate -m "Initial migration with User and Sponsor models"
        
        if [ $? -eq 0 ]; then
            print_status "✓ Initial migration created"
        else
            print_error "✗ Failed to create initial migration"
            exit 1
        fi
    else
        print_status "✓ Migrations already exist, skipping initial migration"
    fi
}

# Run database migrations
run_migrations() {
    print_status "Running database migrations..."
    
    flask db upgrade
    
    if [ $? -eq 0 ]; then
        print_status "✓ Database migrations completed successfully"
    else
        print_error "✗ Database migrations failed"
        exit 1
    fi
}

# Verify database schema
verify_schema() {
    print_status "Verifying database schema..."
    
    # Check if key tables exist
    TABLES=("users" "sponsors")
    
    for table in "${TABLES[@]}"; do
        if mysql -h "$DB_HOST" -P "$DB_PORT" -u "$DB_USER" -p"$DB_PASS" "$DB_NAME" -e "DESCRIBE $table;" > /dev/null 2>&1; then
            print_status "✓ Table '$table' exists"
        else
            print_warning "✗ Table '$table' not found"
        fi
    done
}

# Create database backup
backup_database() {
    print_status "Creating database backup..."
    
    BACKUP_DIR="$PROJECT_ROOT/backups"
    [ -d "$BACKUP_DIR" ] || mkdir -p "$BACKUP_DIR"
    
    BACKUP_FILE="$BACKUP_DIR/doi_db_backup_$(date +%Y%m%d_%H%M%S).sql"
    
    mysqldump -h "$DB_HOST" -P "$DB_PORT" -u "$DB_USER" -p"$DB_PASS" "$DB_NAME" > "$BACKUP_FILE"
    
    if [ $? -eq 0 ]; then
        print_status "✓ Database backup created: $BACKUP_FILE"
        
        # Compress backup
        gzip "$BACKUP_FILE"
        print_status "✓ Backup compressed: $BACKUP_FILE.gz"
    else
        print_error "✗ Failed to create database backup"
    fi
}

# Restore database from backup
restore_database() {
    if [ -z "$1" ]; then
        print_error "Usage: $0 restore <backup-file>"
        exit 1
    fi
    
    BACKUP_FILE="$1"
    
    if [ ! -f "$BACKUP_FILE" ]; then
        print_error "Backup file not found: $BACKUP_FILE"
        exit 1
    fi
    
    print_warning "This will restore database '$DB_NAME' from backup."
    print_warning "ALL CURRENT DATA WILL BE LOST!"
    print_question "Are you sure? (yes/no)"
    read -r confirm
    
    if [ "$confirm" != "yes" ]; then
        print_status "Restore cancelled"
        exit 0
    fi
    
    print_status "Restoring database from $BACKUP_FILE..."
    
    # Handle compressed backups
    if [[ "$BACKUP_FILE" == *.gz ]]; then
        zcat "$BACKUP_FILE" | mysql -h "$DB_HOST" -P "$DB_PORT" -u "$DB_USER" -p"$DB_PASS" "$DB_NAME"
    else
        mysql -h "$DB_HOST" -P "$DB_PORT" -u "$DB_USER" -p"$DB_PASS" "$DB_NAME" < "$BACKUP_FILE"
    fi
    
    if [ $? -eq 0 ]; then
        print_status "✓ Database restored successfully"
    else
        print_error "✗ Database restore failed"
        exit 1
    fi
}

# Show database status
show_status() {
    print_status "Database Status:"
    echo ""
    
    # Connection test
    if test_database_connection > /dev/null 2>&1; then
        echo "Connection: ✓ Connected"
    else
        echo "Connection: ✗ Failed"
        return 1
    fi
    
    # Database size
    DB_SIZE=$(mysql -h "$DB_HOST" -P "$DB_PORT" -u "$DB_USER" -p"$DB_PASS" -e "SELECT ROUND(SUM(data_length + index_length) / 1024 / 1024, 1) AS 'DB Size in MB' FROM information_schema.tables WHERE table_schema='$DB_NAME';" -s -N 2>/dev/null)
    if [ -n "$DB_SIZE" ]; then
        echo "Database Size: ${DB_SIZE} MB"
    fi
    
    # Table count
    TABLE_COUNT=$(mysql -h "$DB_HOST" -P "$DB_PORT" -u "$DB_USER" -p"$DB_PASS" -e "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='$DB_NAME';" -s -N 2>/dev/null)
    if [ -n "$TABLE_COUNT" ]; then
        echo "Tables: $TABLE_COUNT"
    fi
    
    # Migration status
    if [ -d "migrations/versions" ]; then
        MIGRATION_COUNT=$(ls -1 migrations/versions/*.py 2>/dev/null | wc -l)
        echo "Migrations: $MIGRATION_COUNT files"
    fi
}

# Main execution
main() {
    load_environment
    check_mysql_client
    parse_database_url
    
    case "${1:-setup}" in
        "setup"|"")
            test_database_connection || exit 1
            create_database
            initialize_migrations
            generate_initial_migration
            run_migrations
            verify_schema
            print_status "✅ Database setup completed successfully!"
            ;;
        "migrate")
            test_database_connection || exit 1
            run_migrations
            ;;
        "init")
            initialize_migrations
            ;;
        "backup")
            test_database_connection || exit 1
            backup_database
            ;;
        "restore")
            restore_database "$2"
            ;;
        "status")
            show_status
            ;;
        "test")
            test_database_connection
            ;;
        "help")
            echo "Usage: $0 [setup|migrate|init|backup|restore|status|test|help]"
            echo ""
            echo "Commands:"
            echo "  setup     - Complete database setup (default)"
            echo "  migrate   - Run database migrations only"
            echo "  init      - Initialize Flask-Migrate only"
            echo "  backup    - Create database backup"
            echo "  restore   - Restore from backup file"
            echo "  status    - Show database status"
            echo "  test      - Test database connection"
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