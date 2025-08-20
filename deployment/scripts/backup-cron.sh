#!/bin/bash

# Automated Database Backup Script for Cron Job
# This script is designed to be run as a daily cron job

set -e

# Configuration
APP_DIR="/opt/doi-app"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="$APP_DIR/logs/backup.log"
BACKUP_RETENTION_DAYS=30

# Ensure log directory exists
mkdir -p "$APP_DIR/logs"

# Function to log messages
log_message() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') [BACKUP] $1" | tee -a "$LOG_FILE"
}

# Change to application directory
cd "$APP_DIR"

log_message "Starting automated database backup"

# Run the backup
if "$SCRIPT_DIR/setup-database.sh" backup >> "$LOG_FILE" 2>&1; then
    log_message "Database backup completed successfully"
    
    # Clean up old backups
    if [ -n "$BACKUP_RETENTION_DAYS" ] && [ "$BACKUP_RETENTION_DAYS" -gt 0 ]; then
        log_message "Cleaning up backups older than $BACKUP_RETENTION_DAYS days"
        find "$APP_DIR/backups" -name "*.sql.gz" -mtime +"$BACKUP_RETENTION_DAYS" -delete 2>/dev/null || true
        
        deleted_count=$(find "$APP_DIR/backups" -name "*.sql.gz" -mtime +"$BACKUP_RETENTION_DAYS" 2>/dev/null | wc -l || echo "0")
        if [ "$deleted_count" -gt 0 ]; then
            log_message "Deleted $deleted_count old backup files"
        fi
    fi
    
    # Log backup statistics
    backup_count=$(find "$APP_DIR/backups" -name "*.sql.gz" 2>/dev/null | wc -l || echo "0")
    backup_size=$(du -sh "$APP_DIR/backups" 2>/dev/null | cut -f1 || echo "unknown")
    
    log_message "Backup statistics: $backup_count files, total size: $backup_size"
    log_message "Automated backup process completed successfully"
    
else
    log_message "ERROR: Database backup failed"
    
    # Send notification email if mail is configured
    if command -v mail >/dev/null 2>&1; then
        echo "Database backup failed on $(hostname) at $(date)" | mail -s "DOI App Backup Failed" root@localhost 2>/dev/null || true
    fi
    
    exit 1
fi