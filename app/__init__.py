from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_caching import Cache
from flask_wtf.csrf import CSRFProtect

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
cache = Cache()
csrf = CSRFProtect()


def create_app(config_name="default"):
    """Flask application factory."""
    app = Flask(__name__)

    # Load configuration
    from config import config

    app.config.from_object(config[config_name])

    # Initialize extensions with app
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    cache.init_app(app)
    csrf.init_app(app)

    # Configure Flask-Login
    login_manager.login_view = "auth.login"
    login_manager.login_message = "Molimo prijavite se da pristupite ovoj stranici."
    login_manager.login_message_category = "info"

    # Import models so Flask-Migrate can discover them
    from app.models import Sponsor, User

    # User loader for Flask-Login
    @login_manager.user_loader
    def load_user(user_id):
        return User.get_by_id(int(user_id))

    # Register blueprints
    from app.blueprints.main import main_bp
    from app.blueprints.auth import auth_bp
    from app.blueprints.members import members_bp
    from app.blueprints.publications import publications_bp
    from app.blueprints.drafts import drafts_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix="/auth")
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

    # Security headers
    @app.after_request
    def security_headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        return response

    return app
