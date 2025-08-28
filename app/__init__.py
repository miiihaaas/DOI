from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_caching import Cache
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
cache = Cache()
csrf = CSRFProtect()
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)


def create_app(config_name="default"):
    """Flask application factory."""
    app = Flask(__name__)

    # Load configuration
    from config import config
    config_class = config[config_name]
    config_instance = config_class()
    
    # Set configuration - instance attributes have priority
    # First set defaults from class
    app.config.from_object(config_class)
    # Then override with instance attributes (this handles environment variables)
    # But skip certain attributes that shouldn't be copied to Flask config
    skip_attrs = {'get_engine_options'}  # Skip methods that shouldn't be copied
    
    for attr in dir(config_instance):
        if (not attr.startswith('_') and 
            not callable(getattr(config_instance, attr)) and
            attr not in skip_attrs and
            hasattr(config_instance, attr)):
            # Special handling for SQLALCHEMY_ENGINE_OPTIONS
            if attr == 'SQLALCHEMY_ENGINE_OPTIONS':
                # Only set if not empty (SQLite returns empty dict)
                engine_options = getattr(config_instance, attr)
                if engine_options:
                    app.config[attr] = engine_options
            else:
                app.config[attr] = getattr(config_instance, attr)

    # Initialize configuration-specific setup (includes logging)
    config_class.init_app(app)

    # Initialize extensions with app
    # Special handling for SQLAlchemy to avoid pool parameter issues with SQLite
    if app.config.get('SQLALCHEMY_DATABASE_URI', '').startswith('sqlite'):
        # Ensure no pool parameters are set for SQLite
        app.config.pop('SQLALCHEMY_ENGINE_OPTIONS', None)
    
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    cache.init_app(app)
    csrf.init_app(app)
    limiter.init_app(app)

    # Configure Flask-Login
    login_manager.login_view = "auth.login"
    login_manager.login_message = "Molimo prijavite se da pristupite ovoj stranici."
    login_manager.login_message_category = "info"

    # Import models so Flask-Migrate can discover them
    from app.models import User

    # User loader for Flask-Login
    @login_manager.user_loader
    def load_user(user_id):
        return User.get_by_id(int(user_id))

    # Register blueprints
    from app.blueprints.main import main_bp
    from app.blueprints.auth import auth_bp
    from app.blueprints.admin import admin_bp
    from app.blueprints.members import members_bp
    from app.blueprints.publications import publications_bp
    from app.blueprints.drafts import drafts_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(admin_bp, url_prefix="/admin")
    app.register_blueprint(members_bp, url_prefix="/members")
    app.register_blueprint(publications_bp, url_prefix="/publications")
    app.register_blueprint(drafts_bp, url_prefix="/drafts")

    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        """404 error handler."""
        from flask import render_template
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def internal_error(error):
        """500 error handler."""
        from flask import render_template
        return render_template("errors/500.html"), 500

    # Setup production logging and request tracking
    if config_name == 'production':
        from app.utils.logging import setup_request_logging, setup_security_logging
        setup_request_logging(app)
        setup_security_logging(app)

    # Security headers
    @app.after_request
    def security_headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        return response
    
    # Add custom Jinja2 filters
    @app.template_filter('nl2br')
    def nl2br_filter(text):
        """Convert newlines to HTML line breaks."""
        from markupsafe import Markup
        if text is None:
            return ''
        return Markup(text.replace('\n', '<br>'))

    return app
