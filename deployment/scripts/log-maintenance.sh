#!/bin/bash

# Log Maintenance Script for DOI Application
# This script handles log compression and cleanup for the DOI application

set -e

APP_DIR="/opt/doi-app"
LOG_DIR="$APP_DIR/logs"
SCRIPT_LOG="$LOG_DIR/log-maintenance.log"

# Function to print timestamped messages
log_message() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$SCRIPT_LOG"
}

# Function to compress old log files
compress_logs() {
    log_message "Starting log compression..."
    
    # Find uncompressed log files older than 1 day
    find "$LOG_DIR" -name "*.log.*" -type f ! -name "*.gz" -mtime +1 | while read -r log_file; do
        if [ -f "$log_file" ]; then
            log_message "Compressing: $log_file"
            
            # Compress the file
            gzip "$log_file"
            
            if [ $? -eq 0 ]; then
                log_message "Successfully compressed: $log_file"
            else
                log_message "ERROR: Failed to compress: $log_file"
            fi
        fi
    done
    
    log_message "Log compression completed"
}

# Function to clean up old compressed logs
cleanup_old_logs() {
    # Default retention: 30 days
    RETENTION_DAYS=${1:-30}
    
    log_message "Starting cleanup of logs older than $RETENTION_DAYS days..."
    
    # Find and remove compressed log files older than retention period
    find "$LOG_DIR" -name "*.gz" -type f -mtime +$RETENTION_DAYS | while read -r old_file; do
        if [ -f "$old_file" ]; then
            log_message "Removing old log: $old_file"
            rm "$old_file"
            
            if [ $? -eq 0 ]; then
                log_message "Successfully removed: $old_file"
            else
                log_message "ERROR: Failed to remove: $old_file"
            fi
        fi
    done
    
    log_message "Old log cleanup completed"
}

# Function to get log statistics
log_stats() {
    log_message "Collecting log statistics..."
    
    if [ ! -d "$LOG_DIR" ]; then
        log_message "Log directory not found: $LOG_DIR"
        return 1
    fi
    
    # Count files
    total_files=$(find "$LOG_DIR" -name "*.log*" -type f | wc -l)
    compressed_files=$(find "$LOG_DIR" -name "*.gz" -type f | wc -l)
    active_files=$(find "$LOG_DIR" -name "*.log" -type f | wc -l)
    
    # Calculate sizes
    total_size=$(du -sh "$LOG_DIR" 2>/dev/null | cut -f1)
    
    # Find oldest and newest files
    if [ $total_files -gt 0 ]; then
        oldest_file=$(find "$LOG_DIR" -name "*.log*" -type f -printf '%T@ %p\n' 2>/dev/null | sort -n | head -1 | cut -d' ' -f2-)
        newest_file=$(find "$LOG_DIR" -name "*.log*" -type f -printf '%T@ %p\n' 2>/dev/null | sort -n | tail -1 | cut -d' ' -f2-)
    fi
    
    log_message "=== LOG STATISTICS ==="
    log_message "Total log files: $total_files"
    log_message "Active log files: $active_files"
    log_message "Compressed files: $compressed_files"
    log_message "Total directory size: $total_size"
    
    if [ -n "$oldest_file" ]; then
        log_message "Oldest file: $oldest_file"
    fi
    if [ -n "$newest_file" ]; then
        log_message "Newest file: $newest_file"
    fi
    
    log_message "======================"
}

# Function to verify log directory structure
verify_log_structure() {
    log_message "Verifying log directory structure..."
    
    # Create log directory if it doesn't exist
    if [ ! -d "$LOG_DIR" ]; then
        log_message "Creating log directory: $LOG_DIR"
        mkdir -p "$LOG_DIR"
        chown doi-app:doi-app "$LOG_DIR" 2>/dev/null || true
        chmod 755 "$LOG_DIR"
    fi
    
    # Check permissions
    if [ ! -w "$LOG_DIR" ]; then
        log_message "WARNING: Log directory is not writable: $LOG_DIR"
    fi
    
    # Check main application log
    APP_LOG="$LOG_DIR/doi_app.log"
    if [ ! -f "$APP_LOG" ]; then
        log_message "Main application log not found: $APP_LOG"
    else
        log_size=$(du -h "$APP_LOG" | cut -f1)
        log_message "Current application log size: $log_size"
    fi
}

# Function to rotate logs manually (emergency use)
force_rotate() {
    log_message "Force rotating application logs..."
    
    APP_LOG="$LOG_DIR/doi_app.log"
    if [ -f "$APP_LOG" ]; then
        timestamp=$(date '+%Y%m%d_%H%M%S')
        rotated_name="$LOG_DIR/doi_app.log.$timestamp"
        
        log_message "Moving $APP_LOG to $rotated_name"
        mv "$APP_LOG" "$rotated_name"
        
        # Send HUP signal to application to reopen log files
        if pgrep -f "doi-app" > /dev/null; then
            log_message "Sending HUP signal to application processes..."
            pkill -HUP -f "doi-app" || true
        fi
        
        # Wait a moment and check if new log file was created
        sleep 2
        if [ -f "$APP_LOG" ]; then
            log_message "New log file created successfully"
        else
            log_message "WARNING: New log file was not created"
        fi
    else
        log_message "No application log file found to rotate"
    fi
}

# Function to check log health
check_log_health() {
    log_message "Checking log health..."
    
    # Check if logs are being written
    APP_LOG="$LOG_DIR/doi_app.log"
    if [ -f "$APP_LOG" ]; then
        # Check if log was modified in the last hour
        if find "$APP_LOG" -mmin -60 | grep -q .; then
            log_message "✓ Application log is being actively written"
        else
            log_message "⚠ WARNING: Application log hasn't been updated in the last hour"
        fi
        
        # Check log file size
        log_size_bytes=$(stat -f%z "$APP_LOG" 2>/dev/null || stat -c%s "$APP_LOG" 2>/dev/null)
        log_size_mb=$((log_size_bytes / 1024 / 1024))
        
        if [ $log_size_mb -gt 50 ]; then
            log_message "⚠ WARNING: Log file is large ($log_size_mb MB), consider rotation"
        else
            log_message "✓ Log file size is reasonable ($log_size_mb MB)"
        fi
    else
        log_message "⚠ WARNING: Main application log file not found"
    fi
    
    # Check for error patterns in recent logs
    if [ -f "$APP_LOG" ]; then
        error_count=$(tail -1000 "$APP_LOG" | grep -c "ERROR" || echo "0")
        warning_count=$(tail -1000 "$APP_LOG" | grep -c "WARNING" || echo "0")
        
        log_message "Recent log analysis (last 1000 lines):"
        log_message "  Errors: $error_count"
        log_message "  Warnings: $warning_count"
        
        if [ $error_count -gt 10 ]; then
            log_message "⚠ HIGH ERROR COUNT detected in recent logs"
        fi
    fi
}

# Main execution
main() {
    # Ensure log directory exists for script logging
    mkdir -p "$LOG_DIR"
    
    log_message "=== DOI Application Log Maintenance Started ==="
    log_message "Command: $0 $*"
    
    case "${1:-compress}" in
        "compress")
            verify_log_structure
            compress_logs
            ;;
        "cleanup")
            retention_days=${2:-30}
            cleanup_old_logs $retention_days
            ;;
        "stats")
            log_stats
            ;;
        "health")
            check_log_health
            ;;
        "rotate")
            force_rotate
            ;;
        "full")
            verify_log_structure
            compress_logs
            cleanup_old_logs 30
            log_stats
            check_log_health
            ;;
        "help")
            echo "Usage: $0 [compress|cleanup|stats|health|rotate|full|help]"
            echo ""
            echo "Commands:"
            echo "  compress  - Compress log files older than 1 day (default)"
            echo "  cleanup   - Remove compressed logs older than retention period"
            echo "            Usage: $0 cleanup [days] (default: 30 days)"
            echo "  stats     - Show log directory statistics"
            echo "  health    - Check log system health"
            echo "  rotate    - Force rotate current log files"
            echo "  full      - Run compress, cleanup, stats, and health checks"
            echo "  help      - Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0                    # Compress old logs"
            echo "  $0 cleanup 45        # Remove logs older than 45 days"
            echo "  $0 full              # Full maintenance cycle"
            ;;
        *)
            log_message "ERROR: Unknown command: $1"
            echo "Use '$0 help' for usage information"
            exit 1
            ;;
    esac
    
    log_message "=== DOI Application Log Maintenance Completed ==="
}

# Run main function with all arguments
main "$@"