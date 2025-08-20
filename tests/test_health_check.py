import pytest
import json
from datetime import datetime


class TestHealthCheckEndpoint:
    """Test suite for health check endpoint functionality."""

    def test_health_endpoint_exists(self, client):
        """Test that health check endpoint is accessible."""
        response = client.get('/health')
        assert response.status_code in [200, 503]  # 200 healthy, 503 unhealthy

    def test_health_endpoint_returns_json(self, client):
        """Test that health check returns valid JSON."""
        response = client.get('/health')
        assert response.content_type == 'application/json'
        
        # Should be valid JSON
        data = response.get_json()
        assert data is not None

    def test_health_response_structure(self, client):
        """Test the structure of health check response."""
        response = client.get('/health')
        data = response.get_json()
        
        # Required fields
        required_fields = ['status', 'timestamp', 'version', 'environment', 'checks', 'metrics']
        for field in required_fields:
            assert field in data, f"Missing required field: {field}"
        
        # Status should be one of the valid values
        assert data['status'] in ['healthy', 'degraded', 'unhealthy']
        
        # Timestamp should be ISO format
        timestamp = data['timestamp']
        assert timestamp.endswith('Z')
        # Should be parseable as datetime
        datetime.fromisoformat(timestamp.replace('Z', '+00:00'))

    def test_health_database_check(self, client):
        """Test database connectivity check in health endpoint."""
        response = client.get('/health')
        data = response.get_json()
        
        # Database check should be present if HEALTH_CHECK_DATABASE is True
        if 'database' in data['checks']:
            db_check = data['checks']['database']
            assert 'status' in db_check
            assert db_check['status'] in ['healthy', 'unhealthy']
            
            if db_check['status'] == 'healthy':
                assert 'response_time_ms' in db_check
                assert isinstance(db_check['response_time_ms'], (int, float))
                assert db_check['response_time_ms'] >= 0
            else:
                assert 'error' in db_check

    def test_health_response_time_metrics(self, client):
        """Test that response time is included in health metrics."""
        response = client.get('/health')
        data = response.get_json()
        
        assert 'metrics' in data
        assert 'response_time_ms' in data['metrics']
        
        response_time = data['metrics']['response_time_ms']
        assert isinstance(response_time, (int, float))
        assert response_time >= 0
        # Health check should be fast (under 5 seconds)
        assert response_time < 5000

    def test_health_system_metrics(self, client):
        """Test system metrics in health check response."""
        response = client.get('/health')
        data = response.get_json()
        
        # System metrics might be present
        if 'system' in data['metrics']:
            system_metrics = data['metrics']['system']
            
            # Check CPU metrics
            if 'cpu_percent' in system_metrics:
                assert isinstance(system_metrics['cpu_percent'], (int, float))
                assert 0 <= system_metrics['cpu_percent'] <= 100
            
            # Check memory metrics  
            if 'memory_percent' in system_metrics:
                assert isinstance(system_metrics['memory_percent'], (int, float))
                assert 0 <= system_metrics['memory_percent'] <= 100
            
            # Check disk metrics
            if 'disk_percent' in system_metrics:
                assert isinstance(system_metrics['disk_percent'], (int, float))
                assert 0 <= system_metrics['disk_percent'] <= 100

    def test_health_uptime_metrics(self, client):
        """Test uptime metrics in health check response."""
        response = client.get('/health')
        data = response.get_json()
        
        if 'uptime' in data['metrics']:
            uptime_metrics = data['metrics']['uptime']
            
            assert 'uptime_seconds' in uptime_metrics
            assert isinstance(uptime_metrics['uptime_seconds'], int)
            assert uptime_metrics['uptime_seconds'] >= 0
            
            if 'started_at' in uptime_metrics:
                # Should be parseable as datetime
                datetime.fromisoformat(uptime_metrics['started_at'])

    def test_health_check_no_authentication_required(self, client):
        """Test that health check doesn't require authentication."""
        response = client.get('/health')
        
        # Should not redirect to login
        assert response.status_code != 302
        # Should return data, not login page
        assert response.content_type == 'application/json'

    def test_health_check_status_codes(self, client):
        """Test appropriate HTTP status codes for health check."""
        response = client.get('/health')
        data = response.get_json()
        
        if data['status'] == 'healthy':
            assert response.status_code == 200
        elif data['status'] == 'degraded':
            assert response.status_code == 200
        elif data['status'] == 'unhealthy':
            assert response.status_code == 503

    def test_health_check_environment_info(self, client, app):
        """Test that environment information is included."""
        response = client.get('/health')
        data = response.get_json()
        
        assert 'environment' in data
        assert 'version' in data
        
        # Environment should match Flask configuration
        assert data['environment'] == app.config.get('FLASK_ENV', 'unknown')

    def test_health_check_logging_on_issues(self, client, caplog):
        """Test that health issues are logged."""
        # This test would need to mock database failure or high resource usage
        # to trigger logging. For now, just ensure no errors in normal operation.
        
        with caplog.at_level('WARNING'):
            response = client.get('/health')
            data = response.get_json()
            
            # If status is not healthy, should have logged something
            if data['status'] != 'healthy':
                assert len(caplog.records) > 0
                assert any('Health check status' in record.message for record in caplog.records)

    def test_health_check_performance(self, client):
        """Test that health check endpoint is performant."""
        import time
        
        start_time = time.time()
        response = client.get('/health')
        end_time = time.time()
        
        # Health check should complete quickly (under 1 second normally)
        response_time = end_time - start_time
        assert response_time < 1.0, f"Health check took {response_time} seconds, should be under 1 second"
        
        # Should return valid response
        assert response.status_code in [200, 503]

    def test_health_check_multiple_calls(self, client):
        """Test multiple health check calls don't interfere with each other."""
        responses = []
        
        # Make multiple rapid calls
        for _ in range(3):
            response = client.get('/health')
            responses.append(response)
        
        # All should be successful
        for response in responses:
            assert response.status_code in [200, 503]
            assert response.content_type == 'application/json'
            
            data = response.get_json()
            assert data is not None
            assert 'status' in data

    def test_health_check_content_headers(self, client):
        """Test that health check returns appropriate headers."""
        response = client.get('/health')
        
        # Should have no-cache headers for monitoring tools
        cache_control = response.headers.get('Cache-Control', '')
        if 'no-cache' in cache_control:
            # If cache control is set, it should prevent caching
            assert 'no-store' in cache_control or 'must-revalidate' in cache_control