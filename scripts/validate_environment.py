#!/usr/bin/env python3
"""
Environment validation script for DOI Management System.
Validates that all required environment variables are set for production.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

def validate_environment():
    """Validate production environment variables."""
    
    # Required environment variables for production
    required_vars = [
        'SECRET_KEY',
        'DATABASE_URL',
        'SENTRY_DSN',  # Optional but recommended
    ]
    
    # Recommended environment variables
    recommended_vars = [
        'UPLOAD_FOLDER',
        'LOG_FILE',
        'HEALTH_CHECK_DATABASE',
        'SESSION_COOKIE_SECURE',
        'SQLALCHEMY_ENGINE_OPTIONS_POOL_SIZE',
    ]
    
    # Check if .env file exists
    env_file = Path('.env')
    if not env_file.exists():
        print("❌ ERROR: .env file not found!")
        print("   Copy production.env.template to .env and configure values.")
        return False
    
    print("🔍 Validating environment configuration...")
    print(f"   .env file: {env_file.absolute()}")
    
    # Load .env file
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        print("❌ ERROR: python-dotenv not installed!")
        print("   Install with: pip install python-dotenv")
        return False
    
    errors = []
    warnings = []
    
    # Check required variables
    for var in required_vars:
        value = os.environ.get(var)
        if not value:
            errors.append(f"Missing required variable: {var}")
        elif value.startswith('your-') or 'change-this' in value:
            errors.append(f"Default placeholder value for: {var}")
        else:
            print(f"✅ {var}: configured")
    
    # Check recommended variables  
    for var in recommended_vars:
        value = os.environ.get(var)
        if not value:
            warnings.append(f"Missing recommended variable: {var}")
        else:
            print(f"✅ {var}: {value}")
    
    # Validate specific values
    database_url = os.environ.get('DATABASE_URL')
    if database_url and 'sqlite' in database_url:
        warnings.append("Using SQLite database - consider MySQL for production")
    
    secret_key = os.environ.get('SECRET_KEY')
    if secret_key and len(secret_key) < 32:
        warnings.append("SECRET_KEY should be at least 32 characters long")
    
    # Validate directories
    upload_folder = os.environ.get('UPLOAD_FOLDER', 'uploads')
    log_file = os.environ.get('LOG_FILE', 'logs/doi_app.log')
    log_dir = Path(log_file).parent
    
    if not Path(upload_folder).exists():
        warnings.append(f"Upload directory does not exist: {upload_folder}")
    
    if not log_dir.exists():
        warnings.append(f"Log directory does not exist: {log_dir}")
    
    # Print results
    print("\n" + "="*50)
    
    if errors:
        print("❌ ERRORS FOUND:")
        for error in errors:
            print(f"   - {error}")
    
    if warnings:
        print("⚠️  WARNINGS:")
        for warning in warnings:
            print(f"   - {warning}")
    
    if not errors and not warnings:
        print("✅ Environment validation passed!")
        return True
    elif not errors:
        print("⚠️  Environment validation passed with warnings")
        return True
    else:
        print("❌ Environment validation failed!")
        return False

def create_directories():
    """Create required directories if they don't exist."""
    
    upload_folder = os.environ.get('UPLOAD_FOLDER', 'uploads')
    log_file = os.environ.get('LOG_FILE', 'logs/doi_app.log')
    log_dir = Path(log_file).parent
    
    print("\n🗂️  Creating required directories...")
    
    # Create upload directory
    Path(upload_folder).mkdir(parents=True, exist_ok=True)
    print(f"✅ Upload directory: {upload_folder}")
    
    # Create log directory
    log_dir.mkdir(parents=True, exist_ok=True)
    print(f"✅ Log directory: {log_dir}")
    
    print("✅ Directory setup complete!")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--create-dirs":
        create_directories()
    
    success = validate_environment()
    
    if not success:
        sys.exit(1)
    
    print("\n🚀 Ready for production deployment!")