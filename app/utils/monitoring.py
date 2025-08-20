"""Monitoring utilities for DOI Application."""

import time
import functools
from datetime import datetime
from flask import current_app, request, g
from flask_login import current_user
import sentry_sdk
from typing import Optional, Dict, Any


class BusinessMetrics:
    """Business metrics tracking for DOI application."""

    @staticmethod
    def track_metric(metric_name: str, value: float = 1, tags: Optional[Dict[str, str]] = None):
        """Track a business metric.

        Args:
            metric_name: Name of the metric (e.g., 'doi_generation', 'user_login')
            value: Metric value (default: 1 for counters)
            tags: Additional tags for the metric
        """
        timestamp = datetime.utcnow()

        # Log metric
        log_data = {
            'metric': metric_name,
            'value': value,
            'timestamp': timestamp.isoformat(),
            'tags': tags or {}
        }

        # Add request context if available
        if request:
            log_data['request_id'] = getattr(g, 'request_id', None)
            log_data['endpoint'] = request.endpoint
            log_data['method'] = request.method

        # Add user context if available
        if current_user and current_user.is_authenticated:
            log_data['user_id'] = current_user.id
            log_data['user_email'] = current_user.email

        current_app.logger.info(f'Business metric: {log_data}')

        # Send to Sentry as a custom metric
        with sentry_sdk.configure_scope() as scope:
            scope.set_tag("metric_type", "business")
            scope.set_context("business_metric", log_data)
            # Sentry doesn't have built-in metrics, but we can send as breadcrumb
            sentry_sdk.add_breadcrumb(
                message=f"Business metric: {metric_name}",
                category="metric",
                level="info",
                data=log_data
            )

    @staticmethod
    def track_doi_generation(draft_id: int, success: bool, generation_time: float = None):
        """Track DOI generation metrics.

        Args:
            draft_id: ID of the DOI draft
            success: Whether generation was successful
            generation_time: Time taken for generation in seconds
        """
        tags = {
            'draft_id': str(draft_id),
            'status': 'success' if success else 'failure'
        }

        # Track generation attempt
        BusinessMetrics.track_metric('doi_generation_attempt', tags=tags)

        # Track result
        if success:
            BusinessMetrics.track_metric('doi_generation_success', tags=tags)
        else:
            BusinessMetrics.track_metric('doi_generation_failure', tags=tags)

        # Track generation time if provided
        if generation_time is not None:
            BusinessMetrics.track_metric('doi_generation_time', generation_time, tags=tags)

    @staticmethod
    def track_user_activity(activity: str, details: Optional[Dict[str, Any]] = None):
        """Track user activity metrics.

        Args:
            activity: Type of activity (e.g., 'login', 'logout', 'create_draft')
            details: Additional activity details
        """
        tags = {
            'activity': activity,
            'user_id': str(current_user.id) if current_user.is_authenticated else 'anonymous'
        }

        if details:
            tags.update({k: str(v) for k, v in details.items()})

        BusinessMetrics.track_metric('user_activity', tags=tags)

    @staticmethod
    def track_api_usage(endpoint: str, method: str, status_code: int, response_time: float):
        """Track API usage metrics.

        Args:
            endpoint: API endpoint
            method: HTTP method
            status_code: HTTP status code
            response_time: Response time in seconds
        """
        tags = {
            'endpoint': endpoint,
            'method': method,
            'status_code': str(status_code),
            'status_class': f"{status_code // 100}xx"
        }

        # Track API call
        BusinessMetrics.track_metric('api_request', tags=tags)

        # Track response time
        BusinessMetrics.track_metric('api_response_time', response_time, tags=tags)

        # Track errors
        if status_code >= 400:
            BusinessMetrics.track_metric('api_error', tags=tags)


def track_business_metric(metric_name: str):
    """Decorator for tracking business metrics on function calls.

    Args:
        metric_name: Base name of the metric

    Usage:
        @track_business_metric('doi_generation')
        def generate_doi(draft_id):
            # Function implementation
            pass
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            success = False

            try:
                result = func(*args, **kwargs)
                success = True
                return result
            except Exception as e:
                # Track the error
                with sentry_sdk.configure_scope() as scope:
                    scope.set_tag("function", func.__name__)
                    scope.set_context("function_args", {
                        'args': str(args),
                        'kwargs': str(kwargs)
                    })
                sentry_sdk.capture_exception(e)
                raise
            finally:
                execution_time = time.time() - start_time

                # Track metrics
                tags = {
                    'function': func.__name__,
                    'status': 'success' if success else 'failure'
                }

                BusinessMetrics.track_metric(f'{metric_name}_attempt', tags=tags)
                BusinessMetrics.track_metric(f'{metric_name}_time', execution_time, tags=tags)

                if success:
                    BusinessMetrics.track_metric(f'{metric_name}_success', tags=tags)
                else:
                    BusinessMetrics.track_metric(f'{metric_name}_failure', tags=tags)

        return wrapper
    return decorator


def track_performance(threshold_seconds: float = 1.0):
    """Decorator for tracking performance and slow operations.

    Args:
        threshold_seconds: Threshold for considering operation as slow

    Usage:
        @track_performance(threshold_seconds=2.0)
        def slow_operation():
            # Implementation
            pass
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()

            try:
                result = func(*args, **kwargs)
                return result
            finally:
                execution_time = time.time() - start_time

                # Log slow operations
                if execution_time > threshold_seconds:
                    current_app.logger.warning(
                        f"Slow operation detected: {func.__name__} took {execution_time:.2f}s"
                    )

                    # Send to Sentry
                    with sentry_sdk.configure_scope() as scope:
                        scope.set_tag("performance_issue", "slow_operation")
                        scope.set_context("performance", {
                            'function': func.__name__,
                            'execution_time': execution_time,
                            'threshold': threshold_seconds
                        })

                    sentry_sdk.add_breadcrumb(
                        message=f"Slow operation: {func.__name__}",
                        category="performance",
                        level="warning",
                        data={
                            'execution_time': execution_time,
                            'threshold': threshold_seconds
                        }
                    )

        return wrapper
    return decorator


class PerformanceMonitor:
    """Performance monitoring utilities."""

    @staticmethod
    def get_system_metrics() -> Dict[str, Any]:
        """Get current system performance metrics."""
        try:
            import psutil

            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=0.1)
            cpu_count = psutil.cpu_count()

            # Memory metrics
            memory = psutil.virtual_memory()

            # Disk metrics
            disk = psutil.disk_usage('/')

            # Process metrics
            process = psutil.Process()
            process_info = process.as_dict(attrs=['pid', 'name', 'create_time', 'memory_info', 'cpu_percent'])

            return {
                'cpu': {
                    'percent': cpu_percent,
                    'count': cpu_count
                },
                'memory': {
                    'total_gb': round(memory.total / (1024**3), 2),
                    'available_gb': round(memory.available / (1024**3), 2),
                    'percent': memory.percent
                },
                'disk': {
                    'total_gb': round(disk.total / (1024**3), 2),
                    'free_gb': round(disk.free / (1024**3), 2),
                    'percent': round(disk.used / disk.total * 100, 1)
                },
                'process': {
                    'pid': process_info['pid'],
                    'memory_mb': round(process_info['memory_info'].rss / (1024**2), 1),
                    'cpu_percent': process_info['cpu_percent'],
                    'uptime_seconds': int(time.time() - process_info['create_time'])
                }
            }
        except ImportError:
            current_app.logger.warning("psutil not available, system metrics disabled")
            return {'error': 'psutil not available'}
        except Exception as e:
            current_app.logger.error(f"Failed to get system metrics: {e}")
            return {'error': str(e)}

    @staticmethod
    def check_resource_thresholds() -> Dict[str, Any]:
        """Check if system resources exceed warning thresholds."""
        metrics = PerformanceMonitor.get_system_metrics()

        if 'error' in metrics:
            return {'status': 'unknown', 'error': metrics['error']}

        warnings = []
        alerts = []

        # CPU thresholds
        cpu_percent = metrics['cpu']['percent']
        if cpu_percent > 90:
            alerts.append(f"Critical CPU usage: {cpu_percent}%")
        elif cpu_percent > 75:
            warnings.append(f"High CPU usage: {cpu_percent}%")

        # Memory thresholds
        memory_percent = metrics['memory']['percent']
        if memory_percent > 90:
            alerts.append(f"Critical memory usage: {memory_percent}%")
        elif memory_percent > 75:
            warnings.append(f"High memory usage: {memory_percent}%")

        # Disk thresholds
        disk_percent = metrics['disk']['percent']
        if disk_percent > 95:
            alerts.append(f"Critical disk usage: {disk_percent}%")
        elif disk_percent > 85:
            warnings.append(f"High disk usage: {disk_percent}%")

        # Determine overall status
        if alerts:
            status = 'critical'
        elif warnings:
            status = 'warning'
        else:
            status = 'healthy'

        return {
            'status': status,
            'warnings': warnings,
            'alerts': alerts,
            'metrics': metrics
        }


class AlertManager:
    """Alert management and notification utilities."""

    @staticmethod
    def send_alert(message: str, severity: str = 'info', context: Optional[Dict[str, Any]] = None):
        """Send alert through configured channels.

        Args:
            message: Alert message
            severity: Alert severity (info, warning, error, critical)
            context: Additional context data
        """
        # Log the alert
        log_level = getattr(current_app.logger, severity, current_app.logger.info)
        log_level(f"Alert [{severity}]: {message}")

        # Send to Sentry for error and critical alerts
        if severity in ['error', 'critical']:
            with sentry_sdk.configure_scope() as scope:
                scope.set_tag("alert_severity", severity)
                scope.set_level(severity)
                if context:
                    scope.set_context("alert_context", context)

            if severity == 'critical':
                sentry_sdk.capture_message(message, level='error')
            else:
                sentry_sdk.add_breadcrumb(
                    message=message,
                    category="alert",
                    level=severity,
                    data=context or {}
                )

        # Track alert as business metric
        BusinessMetrics.track_metric('alert_sent', tags={
            'severity': severity,
            'type': 'system'
        })

    @staticmethod
    def check_and_alert_on_thresholds():
        """Check system thresholds and send alerts if necessary."""
        resource_check = PerformanceMonitor.check_resource_thresholds()

        # Send alerts for warnings and critical issues
        for warning in resource_check.get('warnings', []):
            AlertManager.send_alert(warning, 'warning', {
                'type': 'resource_usage',
                'metrics': resource_check['metrics']
            })

        for alert in resource_check.get('alerts', []):
            AlertManager.send_alert(alert, 'critical', {
                'type': 'resource_usage',
                'metrics': resource_check['metrics']
            })


def setup_error_handlers(app):
    """Setup custom error handlers with monitoring integration."""

    @app.errorhandler(Exception)
    def handle_exception(e):
        """Handle all unhandled exceptions."""
        # Track the error
        BusinessMetrics.track_metric('unhandled_exception', tags={
            'exception_type': type(e).__name__,
            'endpoint': request.endpoint if request else 'unknown'
        })

        # Let Sentry handle the exception (already configured)
        # Re-raise to let Flask's default error handling take over
        raise e

    @app.errorhandler(404)
    def handle_404(e):
        """Handle 404 errors."""
        BusinessMetrics.track_metric('http_404', tags={
            'path': request.path if request else 'unknown'
        })

        from flask import render_template
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def handle_500(e):
        """Handle 500 errors."""
        BusinessMetrics.track_metric('http_500', tags={
            'endpoint': request.endpoint if request else 'unknown'
        })

        from flask import render_template
        return render_template('errors/500.html'), 500


def setup_request_monitoring(app):
    """Setup request-level monitoring."""

    @app.before_request
    def before_request_monitoring():
        """Set up monitoring context for the request."""
        g.request_start_time = time.time()

        # Set Sentry context
        with sentry_sdk.configure_scope() as scope:
            scope.set_tag("endpoint", request.endpoint)
            scope.set_tag("method", request.method)
            scope.set_context("request", {
                "url": request.url,
                "method": request.method,
                "endpoint": request.endpoint,
                "remote_addr": request.remote_addr
            })

            # Add user context if authenticated
            if current_user and current_user.is_authenticated:
                scope.set_user({
                    "id": current_user.id,
                    "email": current_user.email,
                    "username": current_user.full_name
                })

    @app.after_request
    def after_request_monitoring(response):
        """Track request metrics after processing."""
        if hasattr(g, 'request_start_time'):
            request_time = time.time() - g.request_start_time

            # Track API usage metrics
            if request.endpoint:
                BusinessMetrics.track_api_usage(
                    endpoint=request.endpoint,
                    method=request.method,
                    status_code=response.status_code,
                    response_time=request_time
                )

        return response


# Convenience functions for common monitoring operations
def log_user_activity(activity: str, details: Optional[Dict[str, Any]] = None):
    """Log user activity with monitoring integration."""
    from app.utils.logging import log_user_activity as log_activity

    # Use existing logging function
    log_activity(activity, details)

    # Track as business metric
    BusinessMetrics.track_user_activity(activity, details)


def monitor_doi_generation(func):
    """Decorator specifically for DOI generation monitoring."""
    @functools.wraps(func)
    def wrapper(draft_id, *args, **kwargs):
        start_time = time.time()
        success = False

        try:
            result = func(draft_id, *args, **kwargs)
            success = True
            return result
        finally:
            generation_time = time.time() - start_time
            BusinessMetrics.track_doi_generation(
                draft_id=draft_id,
                success=success,
                generation_time=generation_time
            )

    return wrapper
