from flask import Blueprint, render_template, redirect, url_for, jsonify, current_app, request, make_response
from flask_login import login_required, current_user
from app import db
import time
import psutil
import os
from datetime import datetime
from app.models.member import Member
from app.models.publication import Publication
from app.models.activity_log import ActivityLog
from app.models.sponsor import Sponsor
from app.services.dashboard_service import DashboardService
from app.services.export_service import ExportService

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
@login_required
def index():
    """Glavna stranica aplikacije - Dashboard."""
    # Get sponsor from singleton pattern
    sponsor = Sponsor.get_instance()
    
    if sponsor:
        # Use DashboardService to get comprehensive statistics
        dashboard_stats = DashboardService.get_sponsor_statistics(sponsor.id)
        
        # Format statistics for template compatibility
        statistics = {
            'total_members': dashboard_stats['members']['total'],
            'total_publications': dashboard_stats['publications']['total'],
            'total_drafts': dashboard_stats['drafts']['total'],
            'members': dashboard_stats['members'],
            'publications': dashboard_stats['publications'],
            'drafts': dashboard_stats['drafts'],
            'drafts_by_status': dashboard_stats['drafts']['by_status']
        }
        
        # Get recent activities using existing ActivityLog method
        recent_activities = ActivityLog.get_recent_activities(
            limit=10, 
            sponsor_id=sponsor.id
        )
    else:
        # Fallback for no sponsor (shouldn't happen in production)
        statistics = {
            'total_members': 0,
            'total_publications': 0,
            'total_drafts': 0,
            'members': {'total': 0, 'active': 0, 'inactive': 0, 'percentage_active': 0},
            'publications': {'total': 0, 'active': 0, 'inactive': 0, 'by_type': {}},
            'drafts': {'total': 0, 'by_status': {}},
            'drafts_by_status': {}
        }
        recent_activities = []

    return render_template("dashboard.html",
                           title="Dashboard",
                           user=current_user,
                           statistics=statistics,
                           recent_activities=recent_activities)


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


@main_bp.route("/export")
@login_required
def export_index():
    """Stranica za upravljanje izvozom podataka."""
    sponsor = Sponsor.get_instance()
    if not sponsor:
        return redirect(url_for('main.index'))
    
    # Dobij metadata za filtere
    filters_metadata = ExportService.get_export_filters_metadata(sponsor.id)
    
    return render_template('export/export_index.html',
                           title='Izvoz podataka',
                           filters_metadata=filters_metadata)


@main_bp.route("/export/members")
@login_required
def export_members():
    """Izvoz članova u CSV format."""
    sponsor = Sponsor.get_instance()
    if not sponsor:
        return redirect(url_for('main.index'))
    
    # Dobij filtere iz query parametara
    filters = {
        'active_only': request.args.get('active_only') == 'true',
        'search_query': request.args.get('search_query', '').strip() or None,
        'date_from': None,
        'date_to': None
    }
    
    # Parse date filters if provided
    if request.args.get('date_from'):
        try:
            filters['date_from'] = datetime.strptime(request.args.get('date_from'), '%Y-%m-%d')
        except ValueError:
            pass
    
    if request.args.get('date_to'):
        try:
            filters['date_to'] = datetime.strptime(request.args.get('date_to'), '%Y-%m-%d')
        except ValueError:
            pass
    
    # Generate CSV
    csv_content, filename = ExportService.export_members_csv(sponsor.id, filters)
    
    # Create response
    response = make_response(csv_content)
    response.headers['Content-Type'] = 'text/csv; charset=utf-8'
    response.headers['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    return response


@main_bp.route("/export/publications")
@login_required
def export_publications():
    """Izvoz publikacija u CSV format."""
    sponsor = Sponsor.get_instance()
    if not sponsor:
        return redirect(url_for('main.index'))
    
    # Dobij filtere iz query parametara
    filters = {
        'active_only': request.args.get('active_only') == 'true',
        'publication_type': request.args.get('publication_type') or None,
        'member_id': request.args.get('member_id', type=int),
        'search_query': request.args.get('search_query', '').strip() or None,
        'date_from': None,
        'date_to': None
    }
    
    # Parse date filters if provided
    if request.args.get('date_from'):
        try:
            filters['date_from'] = datetime.strptime(request.args.get('date_from'), '%Y-%m-%d')
        except ValueError:
            pass
    
    if request.args.get('date_to'):
        try:
            filters['date_to'] = datetime.strptime(request.args.get('date_to'), '%Y-%m-%d')
        except ValueError:
            pass
    
    # Generate CSV
    csv_content, filename = ExportService.export_publications_csv(sponsor.id, filters)
    
    # Create response
    response = make_response(csv_content)
    response.headers['Content-Type'] = 'text/csv; charset=utf-8'
    response.headers['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    return response


@main_bp.route("/export/drafts")
@login_required
def export_drafts():
    """Izvoz DOI draftova u CSV format."""
    sponsor = Sponsor.get_instance()
    if not sponsor:
        return redirect(url_for('main.index'))
    
    # Dobij filtere iz query parametara
    filters = {
        'status': request.args.get('status') or None,
        'publication_id': request.args.get('publication_id', type=int),
        'member_id': request.args.get('member_id', type=int),
        'search_query': request.args.get('search_query', '').strip() or None,
        'date_from': None,
        'date_to': None
    }
    
    # Parse date filters if provided
    if request.args.get('date_from'):
        try:
            filters['date_from'] = datetime.strptime(request.args.get('date_from'), '%Y-%m-%d')
        except ValueError:
            pass
    
    if request.args.get('date_to'):
        try:
            filters['date_to'] = datetime.strptime(request.args.get('date_to'), '%Y-%m-%d')
        except ValueError:
            pass
    
    # Generate CSV
    csv_content, filename = ExportService.export_doi_drafts_csv(sponsor.id, filters)
    
    # Create response
    response = make_response(csv_content)
    response.headers['Content-Type'] = 'text/csv; charset=utf-8'
    response.headers['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    return response
