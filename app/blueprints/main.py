from flask import Blueprint, render_template, redirect, url_for, jsonify, current_app
from flask_login import login_required, current_user
from app import db
import time
import psutil
import os
from datetime import datetime
from app.models.member import Member
from app.models.publication import Publication

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
@login_required
def index():
    """Glavna stranica aplikacije - Dashboard."""
    # Gather statistics data (placeholder until models are implemented)
    statistics = {
        'total_members': Member.query.count(),  # Member.query.count() kada bude implementiran
        'total_publications': Publication.query.count(),  # Publication.query.count() kada bude implementiran
        'total_drafts': 0,  # DOIDraft.query.count() kada bude implementiran
        'drafts_by_status': {
            'draft': 0,  # DOIDraft.query.filter_by(status='draft').count()
            'xml_generated': 0,  # DOIDraft.query.filter_by(status='xml_generated').count()
            'xml_sent': 0,  # DOIDraft.query.filter_by(status='xml_sent').count()
            'confirmed': 0  # DOIDraft.query.filter_by(status='confirmed').count()
        }
    }

    return render_template("dashboard.html",
                           title="Dashboard",
                           user=current_user,
                           statistics=statistics)


@main_bp.route("/dashboard")
@login_required
def dashboard():
    """Dashboard stranica - redirektuje na root za konzistentnost."""
    return redirect(url_for('main.index'))


@main_bp.route("/health")
def health_check():
    """Health check endpoint that returns application status and metrics.

    Returns JSON with:
    - Application status (healthy/unhealthy)
    - Database connection status
    - Response time metrics
    - System status (CPU, memory)
    - Uptime information

    AC: 5, 9 - Basic health check endpoint with database connection check
    and response time metrics.
    """
    start_time = time.time()
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "version": "1.0.0",  # Could be read from environment or package
        "environment": current_app.config.get('FLASK_ENV', 'unknown'),
        "checks": {},
        "metrics": {}
    }

    # Database connection check (AC: 5, 9)
    if current_app.config.get('HEALTH_CHECK_DATABASE', True):
        try:
            # Simple database connectivity test with timeout
            db_start = time.time()
            with db.engine.connect() as connection:
                result = connection.execute(db.text("SELECT 1"))
                result.fetchone()
            db_time = (time.time() - db_start) * 1000

            health_status["checks"]["database"] = {
                "status": "healthy",
                "response_time_ms": round(db_time, 2),
                "message": "Database connection successful"
            }
        except Exception as e:
            health_status["status"] = "unhealthy"
            health_status["checks"]["database"] = {
                "status": "unhealthy",
                "error": str(e),
                "message": "Database connection failed"
            }

    # System metrics (AC: 9)
    try:
        # CPU usage
        cpu_percent = psutil.cpu_percent(interval=0.1)

        # Memory usage
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        memory_available_mb = round(memory.available / (1024 * 1024), 1)

        # Disk usage for application directory
        disk_usage = psutil.disk_usage('/')
        disk_percent = (disk_usage.used / disk_usage.total) * 100
        disk_free_gb = round(disk_usage.free / (1024 ** 3), 1)

        health_status["metrics"]["system"] = {
            "cpu_percent": round(cpu_percent, 1),
            "memory_percent": round(memory_percent, 1),
            "memory_available_mb": memory_available_mb,
            "disk_percent": round(disk_percent, 1),
            "disk_free_gb": disk_free_gb
        }

        # Check for critical system resources
        if cpu_percent > 90:
            health_status["status"] = "degraded"
            health_status["checks"]["cpu"] = {
                "status": "warning",
                "message": f"High CPU usage: {cpu_percent}%"
            }

        if memory_percent > 90:
            health_status["status"] = "degraded"
            health_status["checks"]["memory"] = {
                "status": "warning",
                "message": f"High memory usage: {memory_percent}%"
            }

        if disk_percent > 90:
            health_status["status"] = "degraded"
            health_status["checks"]["disk"] = {
                "status": "warning",
                "message": f"High disk usage: {disk_percent}%"
            }

    except Exception as e:
        # System metrics are nice-to-have, don't fail health check for them
        health_status["checks"]["system_metrics"] = {
            "status": "warning",
            "message": f"Could not gather system metrics: {str(e)}"
        }

    # Application uptime (AC: 9)
    try:
        # Get process start time
        process = psutil.Process(os.getpid())
        start_time_obj = datetime.fromtimestamp(process.create_time())
        uptime = datetime.now() - start_time_obj

        health_status["metrics"]["uptime"] = {
            "started_at": start_time_obj.isoformat(),
            "uptime_seconds": int(uptime.total_seconds()),
            "uptime_human": str(uptime).split('.')[0]  # Remove microseconds
        }
    except Exception as e:
        health_status["checks"]["uptime"] = {
            "status": "warning",
            "message": f"Could not determine uptime: {str(e)}"
        }

    # Response time calculation (AC: 9)
    response_time = (time.time() - start_time) * 1000
    health_status["metrics"]["response_time_ms"] = round(response_time, 2)

    # Overall health determination
    failed_checks = [check for check in health_status["checks"].values()
                     if check.get("status") == "unhealthy"]

    if failed_checks:
        health_status["status"] = "unhealthy"
        http_status = 503  # Service Unavailable
    elif health_status["status"] == "degraded":
        http_status = 200  # OK but with warnings
    else:
        http_status = 200  # OK

    # Log health check if there are issues
    if health_status["status"] != "healthy":
        current_app.logger.warning(f"Health check status: {health_status['status']}")

    return jsonify(health_status), http_status


@main_bp.route("/health/logs")
def health_logs():
    """Extended health check endpoint with log statistics.

    Returns detailed information about application logs:
    - Log file statistics
    - Log health status
    - Recent error counts

    Useful for monitoring and debugging log-related issues.
    """
    try:
        from app.utils.logging import get_log_stats

        log_stats = get_log_stats()

        health_info = {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "log_statistics": log_stats
        }

        # Add warnings based on log stats
        warnings = []

        if log_stats.get('current_log_size_mb', 0) > 50:
            warnings.append("Current log file is large (>50MB)")

        if log_stats.get('total_log_size_mb', 0) > 500:
            warnings.append("Total log directory size is large (>500MB)")

        if log_stats.get('log_files_count', 0) > 50:
            warnings.append("Many log files present (>50 files)")

        if warnings:
            health_info["warnings"] = warnings
            health_info["status"] = "warning"

        return jsonify(health_info), 200

    except Exception as e:
        current_app.logger.error(f"Failed to get log health info: {e}")
        return jsonify({
            "status": "error",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "error": "Failed to retrieve log statistics"
        }), 500
