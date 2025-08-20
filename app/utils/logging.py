"""Logging utilities and configuration for DOI Application."""

import logging
import logging.handlers
import os
import gzip
import shutil
import glob
from datetime import datetime, timedelta
from flask import current_app, request, g
from functools import wraps


def setup_production_logging(app):
    """Setup production logging with rotation and compression.

    This function configures:
    - Rotating file handler with size-based rotation
    - Daily log compression
    - Log retention policy
    - Structured log formatting
    - Request ID correlation
    """

    # Create logs directory if it doesn't exist
    log_dir = os.path.dirname(app.config['LOG_FILE'])
    os.makedirs(log_dir, exist_ok=True)

    # Set up rotating file handler
    handler = logging.handlers.RotatingFileHandler(
        app.config['LOG_FILE'],
        maxBytes=app.config['LOG_MAX_BYTES'],
        backupCount=app.config['LOG_BACKUP_COUNT']
    )

    # Custom formatter with request correlation
    formatter = RequestCorrelationFormatter(
        '%(asctime)s [%(levelname)s] [%(request_id)s] %(name)s: %(message)s [in %(pathname)s:%(lineno)d]'
    )
    handler.setFormatter(formatter)

    # Set log level
    log_level = getattr(logging, app.config['LOG_LEVEL'].upper(), logging.INFO)
    handler.setLevel(log_level)
    app.logger.setLevel(log_level)

    # Add handler to app logger
    app.logger.addHandler(handler)

    # Also configure root logger for third-party libraries
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.addHandler(handler)

    # Set up log compression and cleanup
    setup_log_compression_cleanup(app)

    app.logger.info('Production logging initialized')


def setup_log_compression_cleanup(app):
    """Setup automated log compression and cleanup.

    This function:
    - Compresses old log files daily
    - Removes old compressed logs based on retention policy
    """

    def compress_old_logs():
        """Compress log files older than 1 day."""
        log_dir = os.path.dirname(app.config['LOG_FILE'])
        log_basename = os.path.basename(app.config['LOG_FILE'])

        # Find rotated log files (ending with .1, .2, etc.)
        pattern = os.path.join(log_dir, f"{log_basename}.*")
        log_files = glob.glob(pattern)

        for log_file in log_files:
            # Skip already compressed files
            if log_file.endswith('.gz'):
                continue

            # Check if file is older than 1 day
            file_age = datetime.now() - datetime.fromtimestamp(os.path.getmtime(log_file))
            if file_age > timedelta(days=1):
                try:
                    # Compress the file
                    with open(log_file, 'rb') as f_in:
                        with gzip.open(f"{log_file}.gz", 'wb') as f_out:
                            shutil.copyfileobj(f_in, f_out)

                    # Remove original file
                    os.remove(log_file)
                    app.logger.info(f'Compressed old log file: {log_file}')

                except Exception as e:
                    app.logger.error(f'Failed to compress log file {log_file}: {e}')

    def cleanup_old_logs():
        """Remove compressed log files older than retention period."""
        retention_days = app.config.get('BACKUP_RETENTION_DAYS', 30)
        log_dir = os.path.dirname(app.config['LOG_FILE'])

        # Find compressed log files
        pattern = os.path.join(log_dir, "*.gz")
        compressed_files = glob.glob(pattern)

        for compressed_file in compressed_files:
            file_age = datetime.now() - datetime.fromtimestamp(os.path.getmtime(compressed_file))
            if file_age > timedelta(days=retention_days):
                try:
                    os.remove(compressed_file)
                    app.logger.info(f'Removed old compressed log: {compressed_file}')
                except Exception as e:
                    app.logger.error(f'Failed to remove old log file {compressed_file}: {e}')

    # Store functions for potential cron job or scheduler
    app._log_compress_cleanup_functions = {
        'compress': compress_old_logs,
        'cleanup': cleanup_old_logs
    }


class RequestCorrelationFormatter(logging.Formatter):
    """Custom formatter that adds request ID for correlation."""

    def format(self, record):
        # Add request ID if available
        if hasattr(g, 'request_id'):
            record.request_id = g.request_id
        else:
            record.request_id = 'N/A'

        # Add request info if available
        if request:
            record.remote_addr = request.remote_addr
            record.method = request.method
            record.url = request.url
        else:
            record.remote_addr = 'N/A'
            record.method = 'N/A'
            record.url = 'N/A'

        return super().format(record)


def generate_request_id():
    """Generate a unique request ID for correlation."""
    import uuid
    return str(uuid.uuid4())[:8]


def setup_request_logging(app):
    """Setup request logging middleware."""

    @app.before_request
    def before_request():
        g.request_id = generate_request_id()
        g.start_time = datetime.utcnow()

        # Log request start (debug level to avoid noise)
        app.logger.debug(f'Request started: {request.method} {request.url}')

    @app.after_request
    def after_request(response):
        if hasattr(g, 'start_time'):
            duration = (datetime.utcnow() - g.start_time).total_seconds() * 1000

            # Log request completion
            app.logger.info(
                f'Request completed: {request.method} {request.url} '
                f'{response.status_code} {duration:.2f}ms'
            )

        return response

    @app.teardown_request
    def teardown_request(exception):
        if exception:
            app.logger.error(f'Request failed with exception: {exception}', exc_info=True)


def log_user_activity(action, details=None):
    """Log user activity for audit trail.

    Args:
        action (str): The action performed (e.g., 'login', 'create_draft', 'delete_user')
        details (dict): Additional details about the action
    """
    from flask_login import current_user

    user_id = current_user.id if current_user.is_authenticated else None
    user_email = current_user.email if current_user.is_authenticated else 'anonymous'

    log_data = {
        'user_id': user_id,
        'user_email': user_email,
        'action': action,
        'remote_addr': request.remote_addr if request else None,
        'user_agent': request.user_agent.string if request else None,
        'timestamp': datetime.utcnow().isoformat(),
    }

    if details:
        log_data.update(details)

    current_app.logger.info(f'User activity: {log_data}')


def audit_log(action):
    """Decorator for automatic audit logging of function calls.

    Usage:
        @audit_log('create_user')
        def create_user(user_data):
            # function implementation
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                result = func(*args, **kwargs)
                log_user_activity(action, {'status': 'success', 'function': func.__name__})
                return result
            except Exception as e:
                log_user_activity(action, {
                    'status': 'error',
                    'function': func.__name__,
                    'error': str(e)
                })
                raise
        return wrapper
    return decorator


def setup_security_logging(app):
    """Setup security event logging."""

    def log_security_event(event_type, details=None):
        """Log security-related events."""
        log_data = {
            'event_type': event_type,
            'timestamp': datetime.utcnow().isoformat(),
            'remote_addr': request.remote_addr if request else None,
            'user_agent': request.user_agent.string if request else None,
        }

        if details:
            log_data.update(details)

        app.logger.warning(f'Security event: {log_data}')

    # Store function for use in authentication/authorization code
    app.log_security_event = log_security_event


def get_log_stats():
    """Get statistics about application logs.

    Returns:
        dict: Log statistics including file sizes, counts, etc.
    """
    try:
        log_dir = os.path.dirname(current_app.config['LOG_FILE'])
        log_files = glob.glob(os.path.join(log_dir, "*.log*"))

        stats = {
            'log_files_count': len(log_files),
            'total_log_size_mb': 0,
            'current_log_size_mb': 0,
            'compressed_logs_count': 0,
            'oldest_log': None,
            'newest_log': None
        }

        file_times = []

        for log_file in log_files:
            size_mb = os.path.getsize(log_file) / (1024 * 1024)
            stats['total_log_size_mb'] += size_mb

            if log_file == current_app.config['LOG_FILE']:
                stats['current_log_size_mb'] = size_mb

            if log_file.endswith('.gz'):
                stats['compressed_logs_count'] += 1

            file_time = datetime.fromtimestamp(os.path.getmtime(log_file))
            file_times.append(file_time)

        if file_times:
            stats['oldest_log'] = min(file_times).isoformat()
            stats['newest_log'] = max(file_times).isoformat()

        stats['total_log_size_mb'] = round(stats['total_log_size_mb'], 2)
        stats['current_log_size_mb'] = round(stats['current_log_size_mb'], 2)

        return stats

    except Exception as e:
        current_app.logger.error(f'Failed to get log statistics: {e}')
        return {'error': str(e)}


# Convenience logging functions
def log_info(message, extra=None):
    """Log info message with request correlation."""
    current_app.logger.info(message, extra=extra)


def log_warning(message, extra=None):
    """Log warning message with request correlation."""
    current_app.logger.warning(message, extra=extra)


def log_error(message, exc_info=False, extra=None):
    """Log error message with request correlation."""
    current_app.logger.error(message, exc_info=exc_info, extra=extra)


def log_debug(message, extra=None):
    """Log debug message with request correlation."""
    current_app.logger.debug(message, extra=extra)
