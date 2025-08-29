"""
Admin blueprint for user management functionality.
"""

from flask import Blueprint, render_template, redirect, url_for, request, flash, abort, jsonify
from flask_login import login_required, current_user
from functools import wraps
from datetime import datetime, timedelta
from app import db
from app.models.user import User
from app.models.activity_log import ActivityLog
from app.services.activity_logger import ActivityLogger

admin_bp = Blueprint('admin', __name__, template_folder='templates')


def admin_required(f):
    """
    Decorator to require admin role for accessing a route.
    Must be used after @login_required decorator.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin():
            abort(403)  # Forbidden
        return f(*args, **kwargs)
    return decorated_function


@admin_bp.route('/users')
@login_required
@admin_required
def users_list():
    """Display list of all users with pagination."""
    page = request.args.get('page', 1, type=int)
    per_page = 20  # Users per page

    users_pagination = User.query.paginate(
        page=page,
        per_page=per_page,
        error_out=False
    )

    return render_template('admin/users/list.html',
                           users=users_pagination.items,
                           pagination=users_pagination)


@admin_bp.route('/users/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create_user():
    """Create a new user account."""
    if request.method == 'POST':
        try:
            # Get form data
            email = request.form.get('email', '').strip()
            full_name = request.form.get('full_name', '').strip()
            password = request.form.get('password', '')
            role = request.form.get('role', 'operator')

            # Validate required fields
            if not email or not full_name or not password:
                flash('Sva polja su obavezna.', 'error')
                return render_template('admin/users/create.html')

            # Check if user already exists
            if User.get_by_email(email):
                flash('Korisnik sa ovom email adresom već postoji.', 'error')
                return render_template('admin/users/create.html')

            # Create new user
            user = User.create_user(
                email=email,
                password=password,
                full_name=full_name,
                role=role
            )

            flash(f'Korisnik {user.full_name} je uspešno kreiran.', 'success')
            return redirect(url_for('admin.users_list'))

        except ValueError as e:
            flash(f'Greška: {str(e)}', 'error')
            return render_template('admin/users/create.html')
        except Exception:
            db.session.rollback()
            flash('Došlo je do greške prilikom kreiranja korisnika.', 'error')
            return render_template('admin/users/create.html')

    return render_template('admin/users/create.html')


@admin_bp.route('/users/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_user(user_id):
    """Edit an existing user account."""
    user = User.query.get_or_404(user_id)

    if request.method == 'POST':
        try:
            # Get form data
            email = request.form.get('email', '').strip()
            full_name = request.form.get('full_name', '').strip()
            role = request.form.get('role', user.role)

            # Validate required fields
            if not email or not full_name:
                flash('Email i puno ime su obavezni.', 'error')
                return render_template('admin/users/edit.html', user=user)

            # Check email uniqueness (excluding current user)
            existing_user = User.get_by_email(email)
            if existing_user and existing_user.id != user.id:
                flash('Korisnik sa ovom email adresom već postoji.', 'error')
                return render_template('admin/users/edit.html', user=user)

            # Update user profile
            user.update_profile(full_name=full_name, email=email)

            # Update role if changed
            if role != user.role:
                user.change_role(role)

            flash(f'Podaci korisnika {user.full_name} su uspešno ažurirani.', 'success')
            return redirect(url_for('admin.users_list'))

        except ValueError as e:
            flash(f'Greška: {str(e)}', 'error')
            return render_template('admin/users/edit.html', user=user)
        except Exception:
            db.session.rollback()
            flash('Došlo je do greške prilikom ažuriranja korisnika.', 'error')
            return render_template('admin/users/edit.html', user=user)

    return render_template('admin/users/edit.html', user=user)


@admin_bp.route('/users/<int:user_id>/reset-password', methods=['POST'])
@login_required
@admin_required
def reset_password(user_id):
    """Reset user password."""
    user = User.query.get_or_404(user_id)

    try:
        new_password = request.form.get('new_password', '')

        if not new_password:
            flash('Nova lozinka je obavezna.', 'error')
            return redirect(url_for('admin.edit_user', user_id=user.id))

        user.change_password(new_password)
        flash(f'Lozinka korisnika {user.full_name} je uspešno resetovana.', 'success')

    except ValueError as e:
        flash(f'Greška: {str(e)}', 'error')
    except Exception:
        db.session.rollback()
        flash('Došlo je do greške prilikom resetovanja lozinke.', 'error')

    return redirect(url_for('admin.edit_user', user_id=user.id))


@admin_bp.route('/activity-log')
@login_required
@admin_required
def activity_management():
    """
    Administrative interface for activity log management.
    Shows comprehensive activity statistics, filters, and cleanup options.
    """
    # Get filter parameters
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 25, type=int)
    user_filter = request.args.get('user_id', type=int)
    action_filter = request.args.get('action_type')
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    ip_filter = request.args.get('ip_address')
    
    # Build query
    query = ActivityLog.query.join(ActivityLog.user)
    
    # Apply filters
    if user_filter:
        query = query.filter(ActivityLog.user_id == user_filter)
    
    if action_filter:
        query = query.filter(ActivityLog.action.like(f'{action_filter}%'))
    
    if date_from:
        try:
            date_from_obj = datetime.strptime(date_from, '%Y-%m-%d')
            query = query.filter(ActivityLog.created_at >= date_from_obj)
        except ValueError:
            flash('Invalid start date format', 'error')
    
    if date_to:
        try:
            date_to_obj = datetime.strptime(date_to, '%Y-%m-%d') + timedelta(days=1)
            query = query.filter(ActivityLog.created_at < date_to_obj)
        except ValueError:
            flash('Invalid end date format', 'error')
    
    if ip_filter:
        query = query.filter(ActivityLog.ip_address.like(f'%{ip_filter}%'))
    
    # Order by most recent first
    query = query.order_by(ActivityLog.created_at.desc())
    
    # Paginate results
    pagination = query.paginate(
        page=page,
        per_page=min(per_page, 100),
        error_out=False
    )
    
    activities = pagination.items
    
    # Get comprehensive statistics
    total_activities = ActivityLog.query.count()
    
    # Activity counts by action type - database-aware implementation
    from sqlalchemy import func
    
    # Check database type for appropriate function usage
    db_url = str(db.engine.url)
    if 'sqlite' in db_url:
        # SQLite-compatible approach: use SUBSTR and CASE for action prefix extraction
        from sqlalchemy import case
        action_prefix_expr = case(
            (ActivityLog.action.like('%_%'), 
             func.substr(ActivityLog.action, 1, func.instr(ActivityLog.action, '_') - 1)),
            else_=ActivityLog.action
        )
        action_stats = db.session.query(
            action_prefix_expr.label('action_prefix'),
            func.count(ActivityLog.id).label('count')
        ).group_by(action_prefix_expr).all()
    else:
        # MySQL-compatible approach using substring_index
        action_stats = db.session.query(
            func.substring_index(ActivityLog.action, '_', 1).label('action_prefix'),
            func.count(ActivityLog.id).label('count')
        ).group_by(
            func.substring_index(ActivityLog.action, '_', 1)
        ).all()
    
    # Recent activity trends (last 30 days)
    thirty_days_ago = datetime.now() - timedelta(days=30)
    recent_activity_trend = db.session.query(
        func.date(ActivityLog.created_at).label('date'),
        func.count(ActivityLog.id).label('count')
    ).filter(
        ActivityLog.created_at >= thirty_days_ago
    ).group_by(
        func.date(ActivityLog.created_at)
    ).order_by('date').all()
    
    # Most active users (last 30 days)
    most_active_users = db.session.query(
        User.full_name,
        User.id,
        func.count(ActivityLog.id).label('activity_count')
    ).join(
        ActivityLog, ActivityLog.user_id == User.id
    ).filter(
        ActivityLog.created_at >= thirty_days_ago
    ).group_by(
        User.id, User.full_name
    ).order_by(
        func.count(ActivityLog.id).desc()
    ).limit(10).all()
    
    # Most common IP addresses
    common_ips = db.session.query(
        ActivityLog.ip_address,
        func.count(ActivityLog.id).label('count')
    ).filter(
        ActivityLog.created_at >= thirty_days_ago,
        ActivityLog.ip_address != '0.0.0.0'
    ).group_by(
        ActivityLog.ip_address
    ).order_by(
        func.count(ActivityLog.id).desc()
    ).limit(10).all()
    
    # Database size information
    try:
        # Get table size information (MySQL specific)
        table_info = db.session.execute(
            db.text("""
                SELECT 
                    table_name,
                    ROUND(((data_length + index_length) / 1024 / 1024), 2) AS size_mb,
                    table_rows
                FROM information_schema.TABLES 
                WHERE table_schema = DATABASE() 
                AND table_name = 'activity_logs'
            """)
        ).fetchone()
        
        database_stats = {
            'table_size_mb': table_info[1] if table_info else 0,
            'row_count': table_info[2] if table_info else total_activities
        }
    except Exception:
        # Fallback for non-MySQL databases
        database_stats = {
            'table_size_mb': 0,
            'row_count': total_activities
        }
    
    # All users for filter dropdown
    all_users = User.query.order_by(User.full_name).all()
    
    statistics = {
        'total_activities': total_activities,
        'action_stats': dict(action_stats),
        'recent_trend': recent_activity_trend,
        'most_active_users': most_active_users,
        'common_ips': common_ips,
        'database_stats': database_stats
    }
    
    return render_template('admin/activity_management.html',
                           activities=activities,
                           pagination=pagination,
                           statistics=statistics,
                           all_users=all_users)


@admin_bp.route('/activity-log/cleanup', methods=['POST'])
@login_required
@admin_required
def cleanup_activities():
    """
    Manual cleanup of old activity logs.
    """
    retention_days = request.json.get('retention_days', 365)
    
    try:
        # Validate input
        if not isinstance(retention_days, int) or retention_days < 30:
            return jsonify({
                'success': False,
                'error': 'Retention period must be at least 30 days'
            }), 400
        
        # Perform cleanup
        deleted_count = ActivityLogger.cleanup_old_activities(retention_days)
        
        # Log the admin action
        ActivityLogger.log_activity(
            user_id=current_user.id,
            action='admin_cleanup',
            description=f'Admin cleanup: removed {deleted_count} activity log entries older than {retention_days} days'
        )
        
        return jsonify({
            'success': True,
            'deleted_count': deleted_count,
            'message': f'Successfully deleted {deleted_count} old activity log entries'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Cleanup failed: {str(e)}'
        }), 500


@admin_bp.route('/activity-log/export', methods=['POST'])
@login_required
@admin_required
def export_all_activities():
    """
    Export all activity logs for administrative purposes.
    Enhanced version of regular export with additional admin-only fields.
    """
    export_format = request.form.get('format', 'csv')
    include_system_info = request.form.get('include_system_info') == 'on'
    include_user_details = request.form.get('include_user_details') == 'on'
    
    # Get all activities (with reasonable limit for performance)
    activities = ActivityLog.query.join(ActivityLog.user).order_by(
        ActivityLog.created_at.desc()
    ).limit(50000).all()  # Max 50k records to prevent memory issues
    
    # Prepare CSV data with admin-specific fields
    import csv
    import io
    
    output = io.StringIO()
    
    # Enhanced headers for admin export
    headers = [
        'ID', 'Timestamp', 'User ID', 'User Name', 'User Email', 
        'Action', 'Description', 'IP Address'
    ]
    
    if include_system_info:
        headers.extend(['Member ID', 'Publication ID', 'Created At (UTC)'])
    
    if include_user_details:
        headers.extend(['User Role', 'User Sponsor'])
    
    writer = csv.writer(output)
    writer.writerow(headers)
    
    # Write data rows with enhanced information
    for activity in activities:
        row = [
            activity.id,
            activity.created_at.strftime('%Y-%m-%d %H:%M:%S') if activity.created_at else '',
            activity.user_id,
            activity.user.full_name if activity.user else 'Unknown User',
            activity.user.email if activity.user else 'unknown@domain.com',
            activity.action,
            activity.description,
            activity.ip_address
        ]
        
        if include_system_info:
            row.extend([
                activity.member_id or '',
                activity.publication_id or '',
                activity.created_at.isoformat() if activity.created_at else ''
            ])
        
        if include_user_details and activity.user:
            row.extend([
                getattr(activity.user, 'role', 'unknown'),
                getattr(activity.user.sponsor, 'name', 'No Sponsor') if hasattr(activity.user, 'sponsor') and activity.user.sponsor else 'No Sponsor'
            ])
        
        writer.writerow(row)
    
    # Log the export action
    ActivityLogger.log_activity(
        user_id=current_user.id,
        action='admin_export',
        description=f'Admin exported {len(activities)} activity log entries in {export_format} format'
    )
    
    # Return CSV response
    output.seek(0)
    from flask import make_response
    response = make_response(output.getvalue())
    response.headers['Content-Type'] = 'text/csv'
    response.headers['Content-Disposition'] = f'attachment; filename=admin_activity_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
    return response


@admin_bp.route('/activity-log/stats')
@login_required
@admin_required
def activity_statistics_api():
    """
    API endpoint for activity statistics dashboard widgets.
    """
    period = request.args.get('period', 'week')
    
    if period == 'today':
        days = 1
    elif period == 'week':
        days = 7
    elif period == 'month':
        days = 30
    elif period == 'quarter':
        days = 90
    else:
        days = 7
    
    stats = ActivityLog.get_activity_statistics(days=days)
    
    return jsonify(stats)


@admin_bp.errorhandler(403)
def forbidden(error):
    """Handle 403 Forbidden errors for admin routes."""
    flash('Nemate dozvolu za pristup ovoj stranici. Potrebni su admin privilegije.', 'error')
    return redirect(url_for('main.dashboard'))
