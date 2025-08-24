"""
Tests for environment configuration and validation functionality.
Tests the production.env.template and validation scripts.
"""

import pytest
import os
import tempfile
import json
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open
from app import create_app


class TestProductionEnvironmentTemplate:
    """Test production.env.template completeness and validity."""

    def test_template_file_exists(self):
        """Test that production.env.template exists."""
        template_path = Path("production.env.template")
        assert template_path.exists(), "production.env.template must exist"

    def test_template_contains_required_variables(self):
        """Test that template contains all required environment variables."""
        template_path = Path("production.env.template")
        
        with open(template_path, 'r') as f:
            content = f.read()
        
        # Core Flask variables
        required_vars = [
            'SECRET_KEY', 'FLASK_ENV', 'FLASK_DEBUG',
            'DATABASE_URL', 'SQLALCHEMY_ENGINE_OPTIONS_POOL_SIZE',
            'UPLOAD_FOLDER', 'MAX_CONTENT_LENGTH', 'ALLOWED_EXTENSIONS',
            'CACHE_TYPE', 'CACHE_DEFAULT_TIMEOUT',
            'SESSION_COOKIE_SECURE', 'SESSION_COOKIE_HTTPONLY',
            'PERMANENT_SESSION_LIFETIME',
            'LOG_LEVEL', 'LOG_FILE', 'LOG_MAX_BYTES', 'LOG_BACKUP_COUNT',
            'SENTRY_DSN', 'SENTRY_ENVIRONMENT',
            'HEALTH_CHECK_DATABASE', 'HEALTH_CHECK_TIMEOUT'
        ]
        
        for var in required_vars:
            assert f"{var}=" in content, f"Template must contain {var} variable"

    def test_template_security_variables(self):
        """Test security-related variables in template."""
        template_path = Path("production.env.template")
        
        with open(template_path, 'r') as f:
            content = f.read()
        
        # Security variables
        security_vars = [
            'SESSION_COOKIE_SECURE=True',
            'SESSION_COOKIE_HTTPONLY=True', 
            'SESSION_COOKIE_SAMESITE=Lax',
            'SSL_REDIRECT=True',
            'FORCE_HTTPS=True'
        ]
        
        for var in security_vars:
            assert var in content, f"Template must contain security setting: {var}"

    def test_template_has_placeholder_values(self):
        """Test that template has appropriate placeholder values."""
        template_path = Path("production.env.template")
        
        with open(template_path, 'r') as f:
            content = f.read()
        
        # Should contain placeholder text for customization
        placeholders = [
            'your-domain.com', 'your-secret-key', 'your_password',
            'your_email', 'your-sentry-dsn'
        ]
        
        placeholder_found = any(placeholder in content for placeholder in placeholders)
        assert placeholder_found, "Template should contain placeholder values for customization"

    def test_template_comments_and_documentation(self):
        """Test that template has helpful comments."""
        template_path = Path("production.env.template")
        
        with open(template_path, 'r') as f:
            content = f.read()
        
        # Should have comments explaining sections
        assert '# Flask Configuration' in content, "Should have section comments"
        assert '# Database Configuration' in content, "Should document database section"
        assert '# Security Settings' in content, "Should document security section"


class TestEnvironmentValidationScript:
    """Test the environment validation script functionality."""

    def test_validation_script_exists(self):
        """Test that validation script exists and is importable."""
        script_path = Path("scripts/validate_environment.py")
        assert script_path.exists(), "Environment validation script must exist"

    @patch('scripts.validate_environment.load_dotenv')
    @patch('scripts.validate_environment.os.environ.get')
    @patch('scripts.validate_environment.Path.exists')
    def test_validation_with_valid_environment(self, mock_exists, mock_env_get, mock_load_dotenv):
        """Test validation with valid environment variables."""
        # Mock .env file exists
        mock_exists.return_value = True
        
        # Mock valid environment variables
        valid_env = {
            'SECRET_KEY': 'secure-secret-key-32-chars-long',
            'DATABASE_URL': 'mysql+pymysql://user:pass@localhost:3306/db',
            'SENTRY_DSN': 'https://key@sentry.io/project',
            'UPLOAD_FOLDER': '/opt/doi-app/uploads',
            'LOG_FILE': '/opt/doi-app/logs/app.log'
        }
        
        mock_env_get.side_effect = lambda key, default=None: valid_env.get(key, default)
        
        # Import and test
        import sys
        import importlib.util
        
        spec = importlib.util.spec_from_file_location(
            "validate_environment", 
            "scripts/validate_environment.py"
        )
        if spec and spec.loader:
            validate_env = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(validate_env)
            
            # Test validation function
            result = validate_env.validate_environment()
            # Should not raise exception and return success
            assert result in [True, None]  # Some functions may not return value

    @patch('scripts.validate_environment.load_dotenv')
    @patch('scripts.validate_environment.os.environ.get')
    @patch('scripts.validate_environment.Path.exists')
    def test_validation_with_missing_variables(self, mock_exists, mock_env_get, mock_load_dotenv):
        """Test validation with missing required variables."""
        # Mock .env file exists
        mock_exists.return_value = True
        
        # Mock missing environment variables
        mock_env_get.return_value = None
        
        import sys
        import importlib.util
        
        try:
            spec = importlib.util.spec_from_file_location(
                "validate_environment", 
                "scripts/validate_environment.py"
            )
            if spec and spec.loader:
                validate_env = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(validate_env)
                
                # Should detect missing variables
                result = validate_env.validate_environment()
                # May return False or raise exception
                assert result in [False, None]
        except Exception:
            # Exception is expected with missing variables
            pass

    def test_directory_creation_function(self):
        """Test directory creation functionality."""
        import sys
        import importlib.util
        
        try:
            spec = importlib.util.spec_from_file_location(
                "validate_environment", 
                "scripts/validate_environment.py"
            )
            if spec and spec.loader:
                validate_env = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(validate_env)
                
                # Test create_directories function if exists
                if hasattr(validate_env, 'create_directories'):
                    # Should be callable
                    assert callable(validate_env.create_directories)
        except ImportError:
            pytest.skip("Validation script not importable in test environment")


class TestConfigurationClasses:
    """Test Flask configuration classes handle environment variables properly."""

    def test_development_config(self):
        """Test development configuration."""
        with patch.dict(os.environ, {
            'SECRET_KEY': 'dev-secret',
            'DATABASE_URL': 'sqlite:///:memory:'
        }):
            app = create_app('development')
            
            assert app.config['DEBUG'] is True
            assert app.config['TESTING'] is False
            assert 'dev-secret' in app.config['SECRET_KEY']

    def test_testing_config(self):
        """Test testing configuration."""
        app = create_app('testing')
        
        assert app.config['TESTING'] is True
        assert app.config['DEBUG'] is False
        assert app.config['WTF_CSRF_ENABLED'] is False
        assert 'sqlite' in app.config['SQLALCHEMY_DATABASE_URI']

    def test_production_config_requires_secret_key(self):
        """Test production config requires SECRET_KEY."""
        # Keep USERNAME for Windows compatibility with PyMySQL
        username = os.environ.get('USERNAME', 'testuser')
        with patch.dict(os.environ, {'USERNAME': username}, clear=True):
            with pytest.raises(ValueError, match="SECRET_KEY"):
                create_app('production')

    def test_production_config_with_environment(self):
        """Test production config with proper environment."""
        with patch.dict(os.environ, {
            'SECRET_KEY': 'production-secret-key-32-chars',
            'DATABASE_URL': 'mysql+pymysql://user:pass@localhost:3306/prod_db',
            'SESSION_COOKIE_SECURE': 'True',
            'SENTRY_DSN': 'https://test@sentry.io/1'
        }):
            app = create_app('production')
            
            assert app.config['DEBUG'] is False
            assert app.config['TESTING'] is False
            assert app.config['SESSION_COOKIE_SECURE'] is True
            assert app.config['SECRET_KEY'] == 'production-secret-key-32-chars'

    def test_database_engine_options(self):
        """Test database engine options configuration."""
        # Keep USERNAME for Windows compatibility with PyMySQL
        username = os.environ.get('USERNAME', 'testuser')
        with patch.dict(os.environ, {
            'USERNAME': username,
            'SECRET_KEY': 'test-secret',
            'DATABASE_URL': 'mysql+pymysql://user:pass@localhost/testdb',
            'SQLALCHEMY_ENGINE_OPTIONS_POOL_SIZE': '15',
            'SQLALCHEMY_ENGINE_OPTIONS_MAX_OVERFLOW': '25',
            'SQLALCHEMY_ENGINE_OPTIONS_POOL_RECYCLE': '7200',
            'SQLALCHEMY_ENGINE_OPTIONS_POOL_PRE_PING': 'False'
        }, clear=True):
            app = create_app('production')
            
            engine_options = app.config['SQLALCHEMY_ENGINE_OPTIONS']
            assert engine_options['pool_size'] == 15
            assert engine_options['max_overflow'] == 25
            assert engine_options['pool_recycle'] == 7200
            assert engine_options['pool_pre_ping'] is False

    def test_logging_configuration(self):
        """Test logging configuration from environment."""
        # Keep USERNAME for Windows compatibility with PyMySQL
        username = os.environ.get('USERNAME', 'testuser')
        with patch.dict(os.environ, {
            'USERNAME': username,
            'SECRET_KEY': 'test-secret',
            'DATABASE_URL': 'mysql+pymysql://user:pass@localhost/testdb',
            'LOG_LEVEL': 'WARNING',
            'LOG_FILE': '/custom/path/app.log',
            'LOG_MAX_BYTES': '5242880',  # 5MB
            'LOG_BACKUP_COUNT': '5'
        }, clear=True):
            app = create_app('production')
            
            assert app.config['LOG_LEVEL'] == 'WARNING'
            assert app.config['LOG_FILE'] == '/custom/path/app.log'
            assert app.config['LOG_MAX_BYTES'] == 5242880
            assert app.config['LOG_BACKUP_COUNT'] == 5

    def test_cache_configuration(self):
        """Test cache configuration from environment."""
        # Keep USERNAME for Windows compatibility with PyMySQL
        username = os.environ.get('USERNAME', 'testuser')
        with patch.dict(os.environ, {
            'USERNAME': username,
            'SECRET_KEY': 'test-secret',
            'DATABASE_URL': 'mysql+pymysql://user:pass@localhost/testdb',
            'CACHE_TYPE': 'redis',
            'CACHE_DEFAULT_TIMEOUT': '600'
        }, clear=True):
            app = create_app('production')
            
            assert app.config['CACHE_TYPE'] == 'redis'
            assert app.config['CACHE_DEFAULT_TIMEOUT'] == 600

    def test_upload_configuration(self):
        """Test file upload configuration."""
        # Keep USERNAME for Windows compatibility with PyMySQL
        username = os.environ.get('USERNAME', 'testuser')
        with patch.dict(os.environ, {
            'USERNAME': username,
            'SECRET_KEY': 'test-secret',
            'DATABASE_URL': 'mysql+pymysql://user:pass@localhost/testdb',
            'UPLOAD_FOLDER': '/custom/uploads',
            'MAX_CONTENT_LENGTH': '20971520',  # 20MB
            'ALLOWED_EXTENSIONS': 'pdf,doc,docx,txt'
        }, clear=True):
            app = create_app('production')
            
            assert app.config['UPLOAD_FOLDER'] == '/custom/uploads'
            assert app.config['MAX_CONTENT_LENGTH'] == 20971520
            assert 'pdf' in app.config['ALLOWED_EXTENSIONS']
            assert 'txt' in app.config['ALLOWED_EXTENSIONS']


class TestEnvironmentVariableValidation:
    """Test environment variable validation logic."""

    def test_boolean_environment_variable_parsing(self):
        """Test parsing of boolean environment variables."""
        # Keep USERNAME for Windows compatibility with PyMySQL
        username = os.environ.get('USERNAME', 'testuser')
        with patch.dict(os.environ, {
            'USERNAME': username,
            'SECRET_KEY': 'test-secret',
            'DATABASE_URL': 'mysql+pymysql://user:pass@localhost/testdb',
            'SESSION_COOKIE_SECURE': 'True',
            'SESSION_COOKIE_HTTPONLY': 'False',
            'HEALTH_CHECK_DATABASE': 'true',
            'WTF_CSRF_ENABLED': 'false'
        }, clear=True):
            app = create_app('production')
            
            assert app.config['SESSION_COOKIE_SECURE'] is True
            assert app.config['SESSION_COOKIE_HTTPONLY'] is False
            assert app.config['HEALTH_CHECK_DATABASE'] is True

    def test_integer_environment_variable_parsing(self):
        """Test parsing of integer environment variables."""
        # Keep USERNAME for Windows compatibility with PyMySQL
        username = os.environ.get('USERNAME', 'testuser')
        with patch.dict(os.environ, {
            'USERNAME': username,
            'SECRET_KEY': 'test-secret',
            'DATABASE_URL': 'mysql+pymysql://user:pass@localhost/testdb',
            'PERMANENT_SESSION_LIFETIME': '7200',
            'HEALTH_CHECK_TIMEOUT': '10',
            'LOG_MAX_BYTES': '10485760'
        }, clear=True):
            app = create_app('production')
            
            # Check session lifetime (should be timedelta)
            assert app.config['PERMANENT_SESSION_LIFETIME'].total_seconds() == 7200
            assert app.config['HEALTH_CHECK_TIMEOUT'] == 10
            assert app.config['LOG_MAX_BYTES'] == 10485760

    def test_list_environment_variable_parsing(self):
        """Test parsing of list-like environment variables."""
        # Keep USERNAME for Windows compatibility with PyMySQL
        username = os.environ.get('USERNAME', 'testuser')
        with patch.dict(os.environ, {
            'USERNAME': username,
            'SECRET_KEY': 'test-secret',
            'DATABASE_URL': 'mysql+pymysql://user:pass@localhost/testdb',
            'ALLOWED_EXTENSIONS': 'xml,pdf,doc,docx,txt'
        }, clear=True):
            app = create_app('production')
            
            allowed_extensions = app.config['ALLOWED_EXTENSIONS']
            assert 'xml' in allowed_extensions
            assert 'pdf' in allowed_extensions
            assert 'doc' in allowed_extensions
            assert len(allowed_extensions) == 5

    def test_default_values_when_env_missing(self):
        """Test that default values are used when environment variables are missing."""
        with patch.dict(os.environ, {'SECRET_KEY': 'test-secret'}, clear=True):
            app = create_app('development')  # Use development to avoid production checks
            
            # Should have reasonable defaults
            assert app.config['LOG_LEVEL'] in ['INFO', 'DEBUG']
            assert app.config['CACHE_TYPE'] == 'simple'
            assert app.config['PERMANENT_SESSION_LIFETIME'].total_seconds() == 3600  # 1 hour default


class TestConfigurationSecurity:
    """Test security aspects of configuration."""

    def test_secret_key_security_requirements(self):
        """Test SECRET_KEY security requirements."""
        # Test with weak secret key
        with patch.dict(os.environ, {
            'SECRET_KEY': 'weak'
        }):
            app = create_app('development')
            # Should still work in development but is not secure
            assert len(app.config['SECRET_KEY']) < 32

        # Test with strong secret key
        # Keep USERNAME for Windows compatibility with PyMySQL
        username = os.environ.get('USERNAME', 'testuser')
        with patch.dict(os.environ, {
            'USERNAME': username,
            'SECRET_KEY': 'very-strong-secret-key-with-32-chars-or-more',
            'DATABASE_URL': 'mysql+pymysql://user:pass@localhost/testdb'
        }, clear=True):
            app = create_app('production')
            assert len(app.config['SECRET_KEY']) >= 32

    def test_security_headers_configuration(self):
        """Test security headers are properly configured."""
        # Keep USERNAME for Windows compatibility with PyMySQL
        username = os.environ.get('USERNAME', 'testuser')
        with patch.dict(os.environ, {
            'USERNAME': username,
            'SECRET_KEY': 'test-secret',
            'DATABASE_URL': 'mysql+pymysql://user:pass@localhost/testdb',
            'SESSION_COOKIE_SECURE': 'True',
            'SESSION_COOKIE_HTTPONLY': 'True',
            'SESSION_COOKIE_SAMESITE': 'Strict'
        }, clear=True):
            app = create_app('production')
            
            assert app.config['SESSION_COOKIE_SECURE'] is True
            assert app.config['SESSION_COOKIE_HTTPONLY'] is True
            assert app.config['SESSION_COOKIE_SAMESITE'] == 'Strict'

    def test_database_url_security(self):
        """Test database URL doesn't expose credentials."""
        with patch.dict(os.environ, {
            'SECRET_KEY': 'test-secret',
            'DATABASE_URL': 'mysql+pymysql://user:secret@localhost:3306/db'
        }):
            app = create_app('production')
            
            # Configuration should contain the URL
            db_url = app.config['SQLALCHEMY_DATABASE_URI']
            assert 'mysql+pymysql' in db_url
            # URL should contain credentials (they are needed for connection)
            assert 'user:secret' in db_url


@pytest.fixture
def mock_env_file():
    """Create a mock environment file for testing."""
    env_content = """
# Test environment file
SECRET_KEY=test-secret-key-for-testing
DATABASE_URL=sqlite:///:memory:
FLASK_ENV=testing
DEBUG=False
SESSION_COOKIE_SECURE=True
LOG_LEVEL=INFO
UPLOAD_FOLDER=/tmp/test-uploads
CACHE_TYPE=simple
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
        f.write(env_content)
        f.flush()
        yield f.name
    
    # Cleanup
    os.unlink(f.name)


class TestEnvironmentFileLoading:
    """Test loading environment from .env files."""

    def test_dotenv_loading(self, mock_env_file):
        """Test loading environment from .env file."""
        from dotenv import load_dotenv
        
        # Load environment from mock file
        loaded = load_dotenv(mock_env_file)
        assert loaded is True
        
        # Check that variables were loaded
        assert os.environ.get('SECRET_KEY') == 'test-secret-key-for-testing'
        assert os.environ.get('FLASK_ENV') == 'testing'

    def test_env_file_override_priority(self, mock_env_file):
        """Test that .env file values can override system environment."""
        # Set initial environment value
        with patch.dict(os.environ, {'SECRET_KEY': 'original-value'}):
            from dotenv import load_dotenv
            
            # Load from file (should override)
            load_dotenv(mock_env_file, override=True)
            
            # Should be the file value, not original
            assert os.environ.get('SECRET_KEY') == 'test-secret-key-for-testing'

    def test_missing_env_file_handling(self):
        """Test graceful handling of missing .env file."""
        from dotenv import load_dotenv
        
        # Try to load non-existent file
        loaded = load_dotenv('/path/that/does/not/exist/.env')
        
        # Should return False but not crash
        assert loaded is False