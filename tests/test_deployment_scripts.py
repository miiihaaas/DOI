"""
Tests for deployment scripts functionality.
Tests deployment automation scripts without requiring actual deployment.
"""

import pytest
import os
import tempfile
import subprocess
from pathlib import Path
from unittest.mock import patch, MagicMock, call


class TestDeploymentScriptExistence:
    """Test that all deployment scripts exist and have proper structure."""

    def test_main_deployment_script_exists(self):
        """Test main deployment script exists."""
        script_path = Path("deployment/scripts/deploy.sh")
        assert script_path.exists(), "deploy.sh must exist"
        assert script_path.is_file(), "deploy.sh must be a file"

    def test_service_management_scripts_exist(self):
        """Test service management scripts exist."""
        scripts = [
            "deployment/scripts/start.sh",
            "deployment/scripts/stop.sh", 
            "deployment/scripts/restart.sh"
        ]
        
        for script_path in scripts:
            path = Path(script_path)
            assert path.exists(), f"{script_path} must exist"
            assert path.is_file(), f"{script_path} must be a file"

    def test_database_scripts_exist(self):
        """Test database-related scripts exist."""
        scripts = [
            "deployment/scripts/setup-database.sh",
            "deployment/scripts/backup-cron.sh"
        ]
        
        for script_path in scripts:
            path = Path(script_path)
            assert path.exists(), f"{script_path} must exist"

    def test_infrastructure_scripts_exist(self):
        """Test infrastructure setup scripts exist."""
        scripts = [
            "deployment/scripts/setup-nginx.sh",
            "deployment/scripts/setup-ssl.sh",
            "deployment/scripts/ssl-monitor.sh",
            "deployment/scripts/deployment-test.sh"
        ]
        
        for script_path in scripts:
            path = Path(script_path)
            assert path.exists(), f"{script_path} must exist"

    def test_script_has_bash_shebang(self):
        """Test that bash scripts have proper shebang."""
        bash_scripts = [
            "deployment/scripts/deploy.sh",
            "deployment/scripts/start.sh",
            "deployment/scripts/setup-database.sh",
            "deployment/scripts/setup-nginx.sh"
        ]
        
        for script_path in bash_scripts:
            path = Path(script_path)
            if path.exists():
                with open(path, 'r') as f:
                    first_line = f.readline().strip()
                assert first_line == "#!/bin/bash", f"{script_path} must have bash shebang"


class TestDeploymentScriptContent:
    """Test deployment script content and structure."""

    def test_deploy_script_functions(self):
        """Test deploy.sh contains required functions."""
        script_path = Path("deployment/scripts/deploy.sh")
        
        with open(script_path, 'r') as f:
            content = f.read()
        
        # Key functions that should be present
        required_functions = [
            "create_app_user",
            "create_directories", 
            "install_system_dependencies",
            "setup_python_environment",
            "deploy_application",
            "setup_systemd_service",
            "run_database_migrations",
            "start_services",
            "verify_deployment"
        ]
        
        for func in required_functions:
            assert func in content, f"deploy.sh must contain {func} function"

    def test_deploy_script_error_handling(self):
        """Test deploy.sh has proper error handling."""
        script_path = Path("deployment/scripts/deploy.sh")
        
        with open(script_path, 'r') as f:
            content = f.read()
        
        # Should have error handling
        assert "set -e" in content, "Should exit on error"
        assert "print_error" in content, "Should have error printing function"

    def test_deploy_script_configuration(self):
        """Test deploy.sh has proper configuration variables."""
        script_path = Path("deployment/scripts/deploy.sh")
        
        with open(script_path, 'r') as f:
            content = f.read()
        
        # Should have configuration variables
        config_vars = [
            "APP_NAME", "APP_DIR", "USER", "GROUP", "SERVICE_NAME"
        ]
        
        for var in config_vars:
            assert var in content, f"deploy.sh should define {var} variable"

    def test_service_start_script_content(self):
        """Test start.sh script content."""
        script_path = Path("deployment/scripts/start.sh")
        
        with open(script_path, 'r') as f:
            content = f.read()
        
        # Should contain systemctl commands
        assert "systemctl start" in content, "Should start services"
        assert "systemctl status" in content, "Should check service status"

    def test_database_setup_script_commands(self):
        """Test setup-database.sh contains required commands."""
        script_path = Path("deployment/scripts/setup-database.sh")
        
        with open(script_path, 'r') as f:
            content = f.read()
        
        # Should have database operations
        db_commands = [
            "mysql", "flask db", "mysqldump", "backup", "restore"
        ]
        
        for cmd in db_commands:
            assert cmd in content, f"Database script should contain {cmd} functionality"


class TestSystemdServiceConfiguration:
    """Test systemd service file configuration."""

    def test_systemd_service_file_exists(self):
        """Test systemd service file exists."""
        service_path = Path("deployment/systemd/doi-app.service")
        assert service_path.exists(), "Systemd service file must exist"

    def test_systemd_service_structure(self):
        """Test systemd service file has proper structure."""
        service_path = Path("deployment/systemd/doi-app.service")
        
        with open(service_path, 'r') as f:
            content = f.read()
        
        # Should have required sections
        required_sections = ["[Unit]", "[Service]", "[Install]"]
        for section in required_sections:
            assert section in content, f"Service file must have {section} section"

    def test_systemd_service_security(self):
        """Test systemd service has security settings."""
        service_path = Path("deployment/systemd/doi-app.service")
        
        with open(service_path, 'r') as f:
            content = f.read()
        
        # Should have security settings
        security_settings = [
            "NoNewPrivileges=yes",
            "ProtectSystem=strict", 
            "ProtectHome=yes",
            "PrivateTmp=true"
        ]
        
        for setting in security_settings:
            assert setting in content, f"Service file should have {setting}"

    def test_systemd_service_dependencies(self):
        """Test systemd service dependencies."""
        service_path = Path("deployment/systemd/doi-app.service")
        
        with open(service_path, 'r') as f:
            content = f.read()
        
        # Should have proper dependencies
        assert "After=network.target" in content, "Should start after network"
        assert "mysql.service" in content, "Should depend on MySQL"


class TestNginxConfiguration:
    """Test Nginx configuration script and file."""

    def test_nginx_config_file_exists(self):
        """Test Nginx configuration file exists."""
        config_path = Path("deployment/nginx/doi-app.conf")
        assert config_path.exists(), "Nginx config file must exist"

    def test_nginx_setup_script_functions(self):
        """Test setup-nginx.sh contains required functions."""
        script_path = Path("deployment/scripts/setup-nginx.sh")
        
        with open(script_path, 'r') as f:
            content = f.read()
        
        # Should have required functions
        functions = [
            "check_prerequisites",
            "create_error_pages",
            "nginx -t"  # Config test
        ]
        
        for func in functions:
            assert func in content, f"Nginx setup should contain {func}"

    def test_nginx_config_content(self):
        """Test Nginx configuration content."""
        config_path = Path("deployment/nginx/doi-app.conf")
        
        with open(config_path, 'r') as f:
            content = f.read()
        
        # Should have upstream configuration
        assert "upstream doi_app" in content, "Should have upstream definition"
        assert "server 127.0.0.1:5000" in content, "Should proxy to Gunicorn"
        
        # Should have SSL configuration
        assert "ssl_certificate" in content, "Should have SSL certificate config"
        assert "ssl_protocols TLSv1.2 TLSv1.3" in content, "Should use secure protocols"
        
        # Should have security headers
        assert "add_header Strict-Transport-Security" in content, "Should have HSTS"
        assert "add_header X-Frame-Options" in content, "Should have frame protection"


class TestSSLScripts:
    """Test SSL setup and monitoring scripts."""

    def test_ssl_setup_script_exists(self):
        """Test SSL setup script exists."""
        script_path = Path("deployment/scripts/setup-ssl.sh")
        assert script_path.exists(), "SSL setup script must exist"

    def test_ssl_monitor_script_exists(self):
        """Test SSL monitoring script exists."""
        script_path = Path("deployment/scripts/ssl-monitor.sh")
        assert script_path.exists(), "SSL monitor script must exist"

    def test_ssl_setup_script_functions(self):
        """Test SSL setup script functions."""
        script_path = Path("deployment/scripts/setup-ssl.sh")
        
        with open(script_path, 'r') as f:
            content = f.read()
        
        # Should have SSL-related functions
        ssl_functions = [
            "check_prerequisites",
            "install_certbot",
            "generate_certificate",
            "setup_renewal"
        ]
        
        for func in ssl_functions:
            assert func in content, f"SSL setup should contain {func} function"

    def test_ssl_monitor_script_functions(self):
        """Test SSL monitoring script functions."""
        script_path = Path("deployment/scripts/ssl-monitor.sh")
        
        with open(script_path, 'r') as f:
            content = f.read()
        
        # Should have monitoring functions
        monitor_functions = [
            "get_cert_expiry",
            "check_ssl_certificate",
            "check_cert_chain"
        ]
        
        for func in monitor_functions:
            assert func in content, f"SSL monitor should contain {func} function"


class TestDatabaseScripts:
    """Test database setup and backup scripts."""

    def test_database_setup_script_commands(self):
        """Test database setup script has required commands."""
        script_path = Path("deployment/scripts/setup-database.sh")
        
        with open(script_path, 'r') as f:
            content = f.read()
        
        # Should have database commands
        db_operations = [
            "mysql", "mysqldump", "flask db init", "flask db upgrade",
            "backup", "restore", "test_database_connection"
        ]
        
        for operation in db_operations:
            assert operation in content, f"Database setup should support {operation}"

    def test_backup_cron_script_functions(self):
        """Test backup cron script functions."""
        script_path = Path("deployment/scripts/backup-cron.sh")
        
        with open(script_path, 'r') as f:
            content = f.read()
        
        # Should have backup operations
        assert "backup" in content, "Should perform backup operations"
        assert "log_message" in content, "Should have logging"
        assert "BACKUP_RETENTION_DAYS" in content, "Should handle retention"

    def test_database_script_error_handling(self):
        """Test database script error handling."""
        script_path = Path("deployment/scripts/setup-database.sh")
        
        with open(script_path, 'r') as f:
            content = f.read()
        
        # Should have error handling
        assert "set -e" in content, "Should exit on error"
        assert "print_error" in content, "Should have error handling functions"


class TestDeploymentTestingScript:
    """Test the deployment testing script."""

    def test_deployment_test_script_exists(self):
        """Test deployment testing script exists."""
        script_path = Path("deployment/scripts/deployment-test.sh")
        assert script_path.exists(), "Deployment test script must exist"

    def test_deployment_test_functions(self):
        """Test deployment testing script functions."""
        script_path = Path("deployment/scripts/deployment-test.sh")
        
        with open(script_path, 'r') as f:
            content = f.read()
        
        # Should have test functions
        test_functions = [
            "test_environment",
            "test_services", 
            "test_database",
            "test_health_check",
            "test_web_server",
            "test_application",
            "test_logging",
            "test_monitoring"
        ]
        
        for func in test_functions:
            assert func in content, f"Deployment test should have {func} function"

    def test_deployment_test_reporting(self):
        """Test deployment testing script has reporting."""
        script_path = Path("deployment/scripts/deployment-test.sh")
        
        with open(script_path, 'r') as f:
            content = f.read()
        
        # Should have reporting functionality
        assert "generate_report" in content, "Should generate test reports"
        assert "RESULTS_FILE" in content, "Should save results to file"


class TestScriptUtilities:
    """Test utility functions in scripts."""

    def test_scripts_have_usage_functions(self):
        """Test that scripts have usage/help functions."""
        scripts_with_help = [
            "deployment/scripts/setup-ssl.sh",
            "deployment/scripts/ssl-monitor.sh", 
            "deployment/scripts/deployment-test.sh"
        ]
        
        for script_path in scripts_with_help:
            path = Path(script_path)
            if path.exists():
                with open(path, 'r') as f:
                    content = f.read()
                
                # Should have help functionality
                assert "show_usage" in content or "--help" in content, f"{script_path} should have help"

    def test_scripts_have_logging_functions(self):
        """Test that scripts have logging functions."""
        scripts_with_logging = [
            "deployment/scripts/deploy.sh",
            "deployment/scripts/setup-database.sh",
            "deployment/scripts/setup-ssl.sh"
        ]
        
        for script_path in scripts_with_logging:
            path = Path(script_path)
            if path.exists():
                with open(path, 'r') as f:
                    content = f.read()
                
                # Should have logging functions
                logging_functions = ["print_status", "print_error", "print_warning"]
                has_logging = any(func in content for func in logging_functions)
                assert has_logging, f"{script_path} should have logging functions"


class TestPythonScripts:
    """Test Python utility scripts."""

    def test_environment_validation_script_syntax(self):
        """Test environment validation script has valid Python syntax."""
        script_path = Path("scripts/validate_environment.py")
        
        if script_path.exists():
            # Test that Python can parse the file
            with open(script_path, 'r') as f:
                content = f.read()
            
            # Compile to check syntax
            try:
                compile(content, str(script_path), 'exec')
            except SyntaxError as e:
                pytest.fail(f"Syntax error in {script_path}: {e}")

    def test_environment_validation_imports(self):
        """Test environment validation script imports."""
        script_path = Path("scripts/validate_environment.py")
        
        if script_path.exists():
            with open(script_path, 'r') as f:
                content = f.read()
            
            # Should have necessary imports
            assert "import os" in content, "Should import os"
            assert "import sys" in content, "Should import sys"
            assert "from pathlib import Path" in content or "import pathlib" in content, "Should handle paths"


class TestDocumentationConsistency:
    """Test that documentation matches script implementation."""

    def test_backup_restore_doc_matches_scripts(self):
        """Test backup/restore documentation matches script functionality."""
        doc_path = Path("deployment/DATABASE_BACKUP_RESTORE.md")
        script_path = Path("deployment/scripts/setup-database.sh")
        
        if doc_path.exists() and script_path.exists():
            with open(doc_path, 'r', encoding='utf-8') as f:
                doc_content = f.read()
            
            with open(script_path, 'r') as f:
                script_content = f.read()
            
            # Documentation should mention script commands
            assert "setup-database.sh" in doc_content, "Doc should reference the script"
            assert "backup" in doc_content.lower(), "Doc should cover backup procedures"
            assert "restore" in doc_content.lower(), "Doc should cover restore procedures"

    def test_ssl_doc_matches_scripts(self):
        """Test SSL documentation matches script functionality."""
        doc_path = Path("deployment/SSL_HTTPS_SETUP.md")
        script_path = Path("deployment/scripts/setup-ssl.sh")
        
        if doc_path.exists() and script_path.exists():
            with open(doc_path, 'r', encoding='utf-8') as f:
                doc_content = f.read()
            
            # Documentation should reference SSL scripts
            assert "setup-ssl.sh" in doc_content, "Doc should reference SSL setup script"
            assert "certbot" in doc_content.lower(), "Doc should mention certbot"
            assert "let's encrypt" in doc_content.lower(), "Doc should mention Let's Encrypt"

    def test_deployment_checklist_matches_test_script(self):
        """Test deployment checklist matches testing script."""
        doc_path = Path("deployment/DEPLOYMENT_TESTING_CHECKLIST.md")
        script_path = Path("deployment/scripts/deployment-test.sh")
        
        if doc_path.exists() and script_path.exists():
            with open(doc_path, 'r', encoding='utf-8') as f:
                doc_content = f.read()
            
            with open(script_path, 'r') as f:
                script_content = f.read()
            
            # Should have corresponding test functions
            test_categories = [
                "environment", "services", "database", "health", "ssl", "application"
            ]
            
            for category in test_categories:
                assert category in doc_content.lower(), f"Doc should cover {category} testing"
                assert f"test_{category}" in script_content, f"Script should test {category}"


class TestScriptPermissions:
    """Test script file permissions (Unix-like systems only)."""

    @pytest.mark.skipif(os.name == 'nt', reason="Unix permissions not applicable on Windows")
    def test_bash_scripts_are_executable(self):
        """Test that bash scripts have executable permissions."""
        bash_scripts = [
            "deployment/scripts/deploy.sh",
            "deployment/scripts/start.sh",
            "deployment/scripts/stop.sh",
            "deployment/scripts/restart.sh",
            "deployment/scripts/setup-database.sh",
            "deployment/scripts/setup-nginx.sh",
            "deployment/scripts/setup-ssl.sh"
        ]
        
        for script_path in bash_scripts:
            path = Path(script_path)
            if path.exists():
                # Check if file is executable
                assert os.access(path, os.X_OK), f"{script_path} should be executable"

    @pytest.mark.skipif(os.name == 'nt', reason="Unix permissions not applicable on Windows")
    def test_python_scripts_permissions(self):
        """Test Python script permissions."""
        python_scripts = [
            "scripts/validate_environment.py"
        ]
        
        for script_path in python_scripts:
            path = Path(script_path)
            if path.exists():
                # Python scripts should be readable (executable not required)
                assert os.access(path, os.R_OK), f"{script_path} should be readable"


class TestScriptConfiguration:
    """Test script configuration and customization."""

    def test_scripts_use_configuration_variables(self):
        """Test that scripts use configuration variables properly."""
        script_path = Path("deployment/scripts/deploy.sh")
        
        with open(script_path, 'r') as f:
            content = f.read()
        
        # Should use variables instead of hardcoded values
        config_vars = ["$APP_DIR", "$USER", "$GROUP", "$SERVICE_NAME"]
        
        for var in config_vars:
            assert var in content, f"Deploy script should use {var} variable"

    def test_scripts_have_customizable_parameters(self):
        """Test that scripts have customizable parameters."""
        configurable_scripts = [
            ("deployment/scripts/setup-ssl.sh", ["DOMAIN", "EMAIL"]),
            ("deployment/scripts/ssl-monitor.sh", ["WARN_DAYS", "CRITICAL_DAYS"]),
            ("deployment/scripts/deployment-test.sh", ["DOMAIN", "VERBOSE"])
        ]
        
        for script_path, expected_params in configurable_scripts:
            path = Path(script_path)
            if path.exists():
                with open(path, 'r') as f:
                    content = f.read()
                
                for param in expected_params:
                    assert param in content, f"{script_path} should have {param} parameter"