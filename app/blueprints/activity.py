"""
Activity Blueprint - Routes for activity logging and management.
"""

from flask import Blueprint, render_template, request, jsonify, current_app, make_response, send_file
from flask_login import login_required, current_user
from datetime import datetime, timedelta
import csv
import io
from sqlalchemy import and_, or_

from app import db
from app.models.activity_log import ActivityLog
from app.models.user import User
from app.services.activity_logger import ActivityLogger

activity_bp = Blueprint('activity', __name__, url_prefix='/activity')


@activity_bp.route('/')
@activity_bp.route('/log')
@login_required
def activity_log():
    """
    Full activity log page with advanced filtering and pagination.
    """
    # Get filter parameters from request
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    user_id = request.args.get('user_id', type=int)
    action_type = request.args.get('action_type')
    search = request.args.get('search', '')
    ip_address = request.args.get('ip_address')
    
    # Build query
    query = ActivityLog.query
    
    # Filter by sponsor if not admin
    if not current_user.is_admin and hasattr(current_user, 'sponsor_id'):
        query = query.join(ActivityLog.user).filter(User.sponsor_id == current_user.sponsor_id)
    
    # Apply date filters
    if start_date:
        try:
            start_dt = datetime.strptime(start_date, '%Y-%m-%d')
            query = query.filter(ActivityLog.created_at >= start_dt)
        except ValueError:
            pass
    
    if end_date:
        try:
            end_dt = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
            query = query.filter(ActivityLog.created_at < end_dt)
        except ValueError:
            pass
    
    # Apply user filter
    if user_id:
        query = query.filter(ActivityLog.user_id == user_id)
    
    # Apply action type filter
    if action_type:
        query = query.filter(ActivityLog.action.like(f'{action_type}%'))
    
    # Apply search filter
    if search:
        search_term = f'%{search}%'
        query = query.filter(ActivityLog.description.like(search_term))
    
    # Apply IP address filter
    if ip_address:
        query = query.filter(ActivityLog.ip_address == ip_address)
    
    # Order by most recent first
    query = query.order_by(ActivityLog.created_at.desc())
    
    # Paginate
    pagination = query.paginate(
        page=page,
        per_page=min(per_page, 100),  # Max 100 per page
        error_out=False
    )
    
    activities = pagination.items
    
    # Get available users for filter dropdown
    available_users = User.query.all()
    if not current_user.is_admin and hasattr(current_user, 'sponsor_id'):
        available_users = User.query.filter_by(sponsor_id=current_user.sponsor_id).all()
    
    # Get activity statistics
    activity_stats = ActivityLog.get_activity_statistics(
        user_id=user_id if user_id else None,
        sponsor_id=current_user.sponsor_id if hasattr(current_user, 'sponsor_id') and not current_user.is_admin else None
    )
    
    # Handle AJAX requests for pagination
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({
            'html': render_template('activity/includes/activity_items.html', activities=activities),
            'has_next': pagination.has_next,
            'next_page': pagination.next_num if pagination.has_next else None
        })
    
    return render_template('activity/activity_log.html',
                           activities=activities,
                           pagination=pagination,
                           available_users=available_users,
                           activity_stats=activity_stats)


@activity_bp.route('/export', methods=['POST'])
@login_required
def export_activities():
    """
    Export activity log to CSV or Excel format.
    """
    export_format = request.form.get('format', 'csv')
    date_range = request.form.get('date_range', 'all')
    start_date = request.form.get('start_date')
    end_date = request.form.get('end_date')
    include_ip = request.form.get('include_ip') == 'on'
    include_entity_refs = request.form.get('include_entity_refs') == 'on'
    
    # Build query
    query = ActivityLog.query.join(ActivityLog.user)
    
    # Filter by sponsor if not admin
    if not current_user.is_admin and hasattr(current_user, 'sponsor_id'):
        query = query.filter(User.sponsor_id == current_user.sponsor_id)
    
    # Apply date range filter
    if date_range == 'today':
        today = datetime.now().date()
        query = query.filter(ActivityLog.created_at >= today)
    elif date_range == 'week':
        week_ago = datetime.now() - timedelta(days=7)
        query = query.filter(ActivityLog.created_at >= week_ago)
    elif date_range == 'month':
        month_ago = datetime.now() - timedelta(days=30)
        query = query.filter(ActivityLog.created_at >= month_ago)
    elif date_range == 'quarter':
        quarter_ago = datetime.now() - timedelta(days=90)
        query = query.filter(ActivityLog.created_at >= quarter_ago)
    elif date_range == 'year':
        year_ago = datetime.now() - timedelta(days=365)
        query = query.filter(ActivityLog.created_at >= year_ago)
    elif date_range == 'custom':
        if start_date:
            try:
                start_dt = datetime.strptime(start_date, '%Y-%m-%d')
                query = query.filter(ActivityLog.created_at >= start_dt)
            except ValueError:
                pass
        if end_date:
            try:
                end_dt = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
                query = query.filter(ActivityLog.created_at < end_dt)
            except ValueError:
                pass
    
    # Order by most recent first and limit to prevent memory issues
    activities = query.order_by(ActivityLog.created_at.desc()).limit(10000).all()
    
    # Prepare CSV data
    output = io.StringIO()
    
    # Define headers
    headers = ['ID', 'Timestamp', 'User', 'Action', 'Description']
    if include_ip:
        headers.append('IP Address')
    if include_entity_refs:
        headers.extend(['Member ID', 'Publication ID'])
    
    writer = csv.writer(output)
    writer.writerow(headers)
    
    # Write data rows
    for activity in activities:
        row = [
            activity.id,
            activity.created_at.strftime('%Y-%m-%d %H:%M:%S') if activity.created_at else '',
            activity.user.full_name if activity.user else 'Unknown User',
            activity.action,
            activity.description
        ]
        
        if include_ip:
            row.append(activity.ip_address)
        
        if include_entity_refs:
            row.extend([
                activity.member_id or '',
                activity.publication_id or ''
            ])
        
        writer.writerow(row)
    
    # Prepare response
    output.seek(0)
    
    if export_format == 'csv':
        # Create CSV response
        response = make_response(output.getvalue())
        response.headers['Content-Type'] = 'text/csv'
        response.headers['Content-Disposition'] = f'attachment; filename=activity_log_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        return response
    
    else:
        # For now, return CSV even if Excel was requested
        # TODO: Implement Excel export with openpyxl
        current_app.logger.warning(f"Excel export requested but not implemented, returning CSV")
        response = make_response(output.getvalue())
        response.headers['Content-Type'] = 'text/csv'
        response.headers['Content-Disposition'] = f'attachment; filename=activity_log_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        return response


@activity_bp.route('/entity/<entity_type>/<int:entity_id>')
@login_required
def entity_activities(entity_type, entity_id):
    """
    Get activities for a specific entity (member, publication).
    """
    if entity_type not in ['member', 'publication']:
        return jsonify({'error': 'Invalid entity type'}), 400
    
    # Get activities for the entity
    activities = ActivityLogger.get_activities_for_entity(entity_type, entity_id, limit=50)
    
    # Security check - ensure user can access this entity
    if not current_user.is_admin and hasattr(current_user, 'sponsor_id'):
        # Filter activities to only show those from the same sponsor
        filtered_activities = []
        for activity in activities:
            if activity.user and activity.user.sponsor_id == current_user.sponsor_id:
                filtered_activities.append(activity)
        activities = filtered_activities
    
    # Handle AJAX requests
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({
            'activities': [activity.to_dict() for activity in activities],
            'count': len(activities)
        })
    
    return render_template('activity/entity_activities.html',
                           activities=activities,
                           entity_type=entity_type,
                           entity_id=entity_id)


@activity_bp.route('/stats')
@login_required
def activity_statistics():
    """
    Get activity statistics for dashboard widgets.
    """
    sponsor_id = None
    if not current_user.is_admin and hasattr(current_user, 'sponsor_id'):
        sponsor_id = current_user.sponsor_id
    
    # Get statistics for different time periods
    stats = {
        'today': ActivityLogger.get_activity_statistics(sponsor_id=sponsor_id, days=1),
        'week': ActivityLogger.get_activity_statistics(sponsor_id=sponsor_id, days=7),
        'month': ActivityLogger.get_activity_statistics(sponsor_id=sponsor_id, days=30)
    }
    
    return jsonify(stats)


@activity_bp.route('/cleanup', methods=['POST'])
@login_required
def cleanup_old_activities():
    """
    Manually trigger cleanup of old activity logs.
    Admin only functionality.
    """
    if not current_user.is_admin:
        return jsonify({'error': 'Admin access required'}), 403
    
    retention_days = request.json.get('retention_days', 365)
    
    try:
        # Validate retention days
        if not isinstance(retention_days, int) or retention_days < 30:
            return jsonify({'error': 'Retention days must be at least 30'}), 400
        
        # Perform cleanup
        deleted_count = ActivityLogger.cleanup_old_activities(retention_days=retention_days)
        
        # Log the cleanup action
        ActivityLogger.log_activity(
            user_id=current_user.id,
            action='system_cleanup',
            description=f'Manually cleaned up {deleted_count} activity log entries older than {retention_days} days'
        )
        
        return jsonify({
            'success': True,
            'deleted_count': deleted_count,
            'message': f'Successfully deleted {deleted_count} old activity log entries'
        })
    
    except Exception as e:
        current_app.logger.error(f"Manual cleanup failed: {str(e)}")
        return jsonify({'error': 'Cleanup failed'}), 500