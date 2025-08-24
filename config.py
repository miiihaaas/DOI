import os
import logging
from datetime import timedelta
from dotenv import load_dotenv


class Config:
    """Base configuration class."""

    SECRET_KEY = os.environ.get("SECRET_KEY") or "dev-secret-key-change-in-production"
    SQLALCHEMY_DATABASE_URI = (
        os.environ.get("DATABASE_URL")
        or "mysql+pymysql://user:password@localhost/doi_db"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    def get_engine_options(self):
        """Get SQLAlchemy engine options - adapted for database type."""
        # Check instance attribute first, then class attribute, then environment/default
        db_uri = (
            getattr(self, 'SQLALCHEMY_DATABASE_URI', None) or
            getattr(self.__class__, 'SQLALCHEMY_DATABASE_URI', None) or
            os.environ.get("DATABASE_URL") or 
            "mysql+pymysql://user:password@localhost/doi_db"
        )
        
        # Use empty options for SQLite to avoid compatibility issues
        if 'sqlite' in db_uri.lower():
            return {}
        
        # MySQL/PostgreSQL specific options
        return {
            'pool_size': int(os.environ.get('SQLALCHEMY_ENGINE_OPTIONS_POOL_SIZE', 10)),
            'max_overflow': int(os.environ.get('SQLALCHEMY_ENGINE_OPTIONS_MAX_OVERFLOW', 20)),
            'pool_recycle': int(os.environ.get('SQLALCHEMY_ENGINE_OPTIONS_POOL_RECYCLE', 3600)),
            'pool_pre_ping': os.environ.get('SQLALCHEMY_ENGINE_OPTIONS_POOL_PRE_PING', 'True').lower() == 'true'
        }
    
    # Set default SQLALCHEMY_ENGINE_OPTIONS to empty dict, will be updated in init_app
    SQLALCHEMY_ENGINE_OPTIONS = {}
    
    # File upload settings
    UPLOAD_FOLDER = os.environ.get("UPLOAD_FOLDER") or "uploads"
    MAX_CONTENT_LENGTH = int(os.environ.get('MAX_CONTENT_LENGTH', 16 * 1024 * 1024))  # 16MB default
    ALLOWED_EXTENSIONS = set(os.environ.get('ALLOWED_EXTENSIONS', 'xml,pdf,doc,docx').split(','))

    # Flask-Caching configuration
    CACHE_TYPE = os.environ.get("CACHE_TYPE") or "simple"
    CACHE_DEFAULT_TIMEOUT = int(os.environ.get('CACHE_DEFAULT_TIMEOUT', 300))

    # WTF Forms configuration
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = None
    
    # Session configuration
    SESSION_COOKIE_SECURE = os.environ.get('SESSION_COOKIE_SECURE', 'False').lower() == 'true'
    SESSION_COOKIE_HTTPONLY = os.environ.get('SESSION_COOKIE_HTTPONLY', 'True').lower() == 'true'
    SESSION_COOKIE_SAMESITE = os.environ.get('SESSION_COOKIE_SAMESITE', 'Lax')
    PERMANENT_SESSION_LIFETIME = timedelta(seconds=int(os.environ.get('PERMANENT_SESSION_LIFETIME', 3600)))
    
    # Rate limiting configuration
    RATELIMIT_STORAGE_URL = os.environ.get('RATELIMIT_STORAGE_URL', 'memory://')
    RATELIMIT_DEFAULT = os.environ.get('RATELIMIT_DEFAULT', '200 per day')
    
    # Logging configuration
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_FILE = os.environ.get('LOG_FILE', 'logs/doi_app.log')
    LOG_MAX_BYTES = int(os.environ.get('LOG_MAX_BYTES', 10 * 1024 * 1024))  # 10MB
    LOG_BACKUP_COUNT = int(os.environ.get('LOG_BACKUP_COUNT', 10))
    
    # Health check configuration
    HEALTH_CHECK_DATABASE = os.environ.get('HEALTH_CHECK_DATABASE', 'True').lower() == 'true'
    HEALTH_CHECK_TIMEOUT = int(os.environ.get('HEALTH_CHECK_TIMEOUT', 5))
    
    # Monitoring and error tracking
    SENTRY_DSN = os.environ.get('SENTRY_DSN')
    SENTRY_ENVIRONMENT = os.environ.get('SENTRY_ENVIRONMENT', 'development')
    
    def __init__(self):
        """Initialize config with engine options."""
        # Set SQLALCHEMY_ENGINE_OPTIONS based on current environment
        self.SQLALCHEMY_ENGINE_OPTIONS = self.get_engine_options()
        
        # Re-read environment variables to ensure instance has latest values
        self.SECRET_KEY = os.environ.get("SECRET_KEY") or "dev-secret-key-change-in-production"
        self.SQLALCHEMY_DATABASE_URI = (
            os.environ.get("DATABASE_URL")
            or "mysql+pymysql://user:password@localhost/doi_db"
        )
        
        # File upload settings (re-read from environment)
        self.UPLOAD_FOLDER = os.environ.get("UPLOAD_FOLDER") or "uploads"
        self.MAX_CONTENT_LENGTH = int(os.environ.get('MAX_CONTENT_LENGTH', 16 * 1024 * 1024))
        self.ALLOWED_EXTENSIONS = set(os.environ.get('ALLOWED_EXTENSIONS', 'xml,pdf,doc,docx').split(','))
        
        # Flask-Caching configuration (re-read from environment)
        self.CACHE_TYPE = os.environ.get("CACHE_TYPE") or "simple"
        self.CACHE_DEFAULT_TIMEOUT = int(os.environ.get('CACHE_DEFAULT_TIMEOUT', 300))
        
        # Session configuration (re-read from environment)
        self.SESSION_COOKIE_SECURE = os.environ.get('SESSION_COOKIE_SECURE', 'False').lower() == 'true'
        self.SESSION_COOKIE_HTTPONLY = os.environ.get('SESSION_COOKIE_HTTPONLY', 'True').lower() == 'true'
        self.SESSION_COOKIE_SAMESITE = os.environ.get('SESSION_COOKIE_SAMESITE', 'Lax')
        self.PERMANENT_SESSION_LIFETIME = timedelta(seconds=int(os.environ.get('PERMANENT_SESSION_LIFETIME', 3600)))
        
        # Logging configuration (re-read from environment)
        self.LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
        self.LOG_FILE = os.environ.get('LOG_FILE', 'logs/doi_app.log')
        self.LOG_MAX_BYTES = int(os.environ.get('LOG_MAX_BYTES', 10 * 1024 * 1024))
        self.LOG_BACKUP_COUNT = int(os.environ.get('LOG_BACKUP_COUNT', 10))
        
        # Health check configuration (re-read from environment)
        self.HEALTH_CHECK_DATABASE = os.environ.get('HEALTH_CHECK_DATABASE', 'True').lower() == 'true'
        self.HEALTH_CHECK_TIMEOUT = int(os.environ.get('HEALTH_CHECK_TIMEOUT', 5))
        
        # Monitoring and error tracking (re-read from environment)
        self.SENTRY_DSN = os.environ.get('SENTRY_DSN')
        self.SENTRY_ENVIRONMENT = os.environ.get('SENTRY_ENVIRONMENT', 'development')
    
    @classmethod
    def init_app(cls, app):
        """Initialize base configuration."""
        # Engine options are already set in __init__
        pass


class DevelopmentConfig(Config):
    """Development configuration."""

    DEBUG = True
    TESTING = False
    
    def __init__(self):
        """Initialize development config."""
        # Load .env file for development
        load_dotenv()
        super().__init__()
        # Override database URI if provided in environment
        if os.environ.get("DATABASE_URL"):
            self.SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL")


class TestingConfig(Config):
    """Testing configuration."""

    TESTING = True
    DEBUG = False
    WTF_CSRF_ENABLED = False
    
    def __init__(self):
        """Initialize testing config."""
        super().__init__()
        # Override with SQLite for testing (after super().__init__)
        self.SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
        # Re-initialize ENGINE_OPTIONS after setting SQLite URI
        self.SQLALCHEMY_ENGINE_OPTIONS = self.get_engine_options()


class ProductionConfig(Config):
    """Production configuration with security and performance optimizations."""

    DEBUG = False
    TESTING = False
    
    # Secure session cookies for production (HTTPS required)
    SESSION_COOKIE_SECURE = True

    def __init__(self):
        """Initialize production config with validation."""
        super().__init__()
        
        # Override with environment variables in production
        self.SECRET_KEY = os.environ.get("SECRET_KEY")
        self.SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL")

        # Force secure cookies in production regardless of environment variable
        self.SESSION_COOKIE_SECURE = True

        if not self.SECRET_KEY:
            raise ValueError("SECRET_KEY environment variable must be set in production")
        if not self.SQLALCHEMY_DATABASE_URI:
            raise ValueError("DATABASE_URL environment variable must be set in production")
    
    @classmethod
    def init_app(cls, app):
        """Initialize production-specific configurations."""
        Config.init_app(app)
        
        # Use our enhanced logging infrastructure
        try:
            from app.utils.logging import setup_production_logging
            setup_production_logging(app)
        except ImportError:
            pass  # Gracefully handle if logging utils don't exist yet
        
        # Configure Sentry if DSN is provided
        sentry_dsn = os.environ.get('SENTRY_DSN')
        if sentry_dsn:
            try:
                import sentry_sdk
                from sentry_sdk.integrations.flask import FlaskIntegration
                from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
                from sentry_sdk.integrations.logging import LoggingIntegration
                
                # Integrate with our logging system
                sentry_logging = LoggingIntegration(
                    level=logging.INFO,  # Capture info and above as breadcrumbs
                    event_level=logging.ERROR  # Send errors as events
                )
                
                sentry_sdk.init(
                    dsn=sentry_dsn,
                    environment=os.environ.get('SENTRY_ENVIRONMENT', 'production'),
                    integrations=[
                        FlaskIntegration(),
                        SqlalchemyIntegration(),
                        sentry_logging
                    ],
                    traces_sample_rate=0.1,  # 10% of transactions
                    send_default_pii=False  # Don't send PII data
                )
                app.logger.info('Sentry error tracking initialized')
            except ImportError:
                app.logger.warning('Sentry SDK not installed, error tracking disabled')


config = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}
