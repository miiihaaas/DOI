"""
Admin blueprint for user management functionality.
"""

from flask import Blueprint, render_template, redirect, url_for, request, flash, abort
from flask_login import login_required, current_user
from functools import wraps
from app import db
from app.models.user import User

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


@admin_bp.errorhandler(403)
def forbidden(error):
    """Handle 403 Forbidden errors for admin routes."""
    flash('Nemate dozvolu za pristup ovoj stranici. Potrebni su admin privilegije.', 'error')
    return redirect(url_for('main.dashboard'))
