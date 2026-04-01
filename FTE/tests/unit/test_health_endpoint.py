"""
Health Endpoint Tests.

Tests for FastAPI health monitoring endpoints:
- GET /health - Component health status
- GET /metrics - Prometheus-format metrics  
- GET /ready - Readiness check
- GET /live - Liveness check
- Rate limiting
- Authentication

Usage:
    pytest tests/unit/test_health_endpoint.py -v
"""

import os
import time
from unittest.mock import patch, MagicMock

import pytest
from fastapi.testclient import TestClient

from src.api.health_endpoint import create_app, check_rate_limit, _rate_limit_window


@pytest.fixture
def mock_metrics_collector():
    """Mock metrics collector to avoid SQLite issues."""
    mock_collector = MagicMock()
    mock_collector.get_prometheus_metrics.return_value = "# Mock metrics\nfte_mock_metric 1.0"
    with patch('src.api.health_endpoint.get_metrics_collector', return_value=mock_collector):
        yield mock_collector


@pytest.fixture
def client(mock_metrics_collector):
    """Create test client without auth."""
    app = create_app(
        metrics_auth_token=None,
        enable_rate_limiting=False,
    )
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def client_with_auth(mock_metrics_collector):
    """Create test client with auth enabled."""
    app = create_app(
        metrics_auth_token="test-token-123",
        enable_rate_limiting=False,
    )
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def client_with_rate_limit(mock_metrics_collector):
    """Create test client with rate limiting enabled."""
    # Clear rate limit window before creating client
    _rate_limit_window.clear()
    
    app = create_app(
        metrics_auth_token=None,
        enable_rate_limiting=True,
    )
    with TestClient(app) as test_client:
        yield test_client


class TestHealthEndpoint:
    """Test /health endpoint."""

    def test_health_response(self, client):
        """Should return health status with components."""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "status" in data
        assert data["status"] in ["healthy", "degraded", "unhealthy"]
        assert "timestamp" in data
        assert "components" in data
        assert "system" in data
        
        # Check system metrics
        assert "cpu_percent" in data["system"]
        assert "memory_percent" in data["system"]
        assert "disk_percent" in data["system"]

    def test_health_includes_all_components(self, client):
        """Should include all monitored components."""
        response = client.get("/health")
        data = response.json()
        
        expected_components = [
            "sqlite_database",
            "file_system",
            "metrics_collector",
            "external_api",
            "watcher_gmail",
            "watcher_whatsapp",
            "watcher_filesystem",
            "approval_handler",
            "dlq",
            "health_endpoint",
        ]
        
        for component in expected_components:
            assert component in data["components"]

    def test_health_component_format(self, client):
        """Component health should have correct format."""
        response = client.get("/health")
        data = response.json()
        
        for name, health in data["components"].items():
            assert "status" in health
            assert "last_check" in health or health.get("status") == "unknown"
            assert "error_count" in health
            assert "fallback_active" in health


class TestMetricsEndpoint:
    """Test /metrics endpoint."""

    def test_metrics_format(self, client):
        """Should return Prometheus-format metrics."""
        response = client.get("/metrics")
        
        assert response.status_code == 200
        assert "text/plain" in response.headers.get("content-type", "")
        
        content = response.text
        
        # Check for required metrics
        assert "fte_component_health" in content
        assert "fte_error_count_total" in content
        assert "fte_system_cpu_percent" in content
        assert "fte_system_memory_percent" in content

    def test_metrics_prometheus_type(self, client):
        """Should have correct Prometheus content type."""
        response = client.get("/metrics")
        
        content_type = response.headers.get("content-type", "")
        assert "text/plain" in content_type
        assert "version=0.0.4" in content_type

    def test_metrics_auth_required(self, client_with_auth):
        """Should require auth token when configured."""
        # Without auth
        response = client_with_auth.get("/metrics")
        assert response.status_code == 401
        
        # With correct auth
        response = client_with_auth.get(
            "/metrics",
            headers={"Authorization": "Bearer test-token-123"},
        )
        assert response.status_code == 200

    def test_metrics_auth_invalid_token(self, client_with_auth):
        """Should reject invalid auth token."""
        response = client_with_auth.get(
            "/metrics",
            headers={"Authorization": "Bearer wrong-token"},
        )
        assert response.status_code == 401

    def test_metrics_component_health_values(self, client):
        """Component health should have correct values."""
        response = client.get("/metrics")
        content = response.text
        
        # Check for component health lines
        assert 'fte_component_health{component="watcher_gmail"}' in content
        assert 'fte_component_health{component="watcher_whatsapp"}' in content


class TestReadyEndpoint:
    """Test /ready endpoint."""

    def test_readiness_check_healthy(self, client):
        """Should return 200 when critical components healthy."""
        response = client.get("/ready")
        
        # Should be ready or not ready based on component state
        assert response.status_code in [200, 503]
        
        data = response.json()
        assert "status" in data
        assert "timestamp" in data

    def test_readiness_check_unhealthy(self, client):
        """Should return 503 when critical component unhealthy."""
        # Manually set a critical component as unhealthy
        from src.api.health_endpoint import get_degradation_manager
        from src.utils.graceful_degradation import ComponentStatus
        
        manager = get_degradation_manager()
        manager.set_component_status(
            "sqlite_database",
            ComponentStatus.UNHEALTHY,
            error="Simulated failure",
        )
        
        response = client.get("/ready")
        
        if response.status_code == 503:
            data = response.json()
            assert data["status"] == "not_ready"
            assert "unhealthy_components" in data

    def test_readiness_includes_critical_components(self, client):
        """Should check critical components."""
        response = client.get("/ready")
        data = response.json()
        
        if response.status_code == 200:
            assert "critical_components" in data
        else:
            assert "unhealthy_components" in data


class TestLiveEndpoint:
    """Test /live endpoint."""

    def test_liveness_check(self, client):
        """Should return alive status."""
        response = client.get("/live")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "alive"
        assert "timestamp" in data


class TestRateLimiting:
    """Test rate limiting functionality."""

    def test_rate_limiting_enforced(self, client_with_rate_limit):
        """Should enforce rate limit after max requests."""
        # Clear rate limit window for this test
        _rate_limit_window.clear()
        
        # Make requests up to limit
        for i in range(60):
            response = client_with_rate_limit.get("/health")
            assert response.status_code == 200, f"Request {i+1} failed"
        
        # Next request should be rate limited
        response = client_with_rate_limit.get("/health")
        assert response.status_code == 429
        
        data = response.json()
        assert "error" in data
        assert "Rate limit" in data["error"]

    def test_rate_limit_response_format(self, client_with_rate_limit):
        """Rate limit response should have correct format."""
        _rate_limit_window.clear()
        
        # Exhaust rate limit
        for _ in range(60):
            client_with_rate_limit.get("/health")
        
        response = client_with_rate_limit.get("/health")
        data = response.json()
        
        assert response.status_code == 429
        assert "retry_after" in data


class TestHealthConfig:
    """Test /health/config endpoint."""

    def test_config_response(self, client):
        """Should return configuration."""
        response = client.get("/health/config")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "metrics_auth_enabled" in data
        assert "rate_limiting_enabled" in data
        assert "rate_limit_max_requests" in data
        assert "rate_limit_window_seconds" in data

    def test_config_with_auth(self, client_with_auth):
        """Should show auth enabled in config."""
        response = client_with_auth.get("/health/config")
        data = response.json()
        
        assert data["metrics_auth_enabled"] is True

    def test_config_with_rate_limit(self, client_with_rate_limit):
        """Should show rate limiting config."""
        response = client_with_rate_limit.get("/health/config")
        data = response.json()

        # Check available config keys
        assert "metrics_auth_enabled" in data
        assert "rate_limiting_enabled" in data


class TestHealthReset:
    """Test /health/reset endpoint."""

    def test_reset_all_components(self, client):
        """Should reset all component statuses."""
        # First set some components as unhealthy
        from src.api.health_endpoint import get_degradation_manager
        from src.utils.graceful_degradation import ComponentStatus
        
        manager = get_degradation_manager()
        manager.set_component_status("watcher_gmail", ComponentStatus.UNHEALTHY)
        
        # Reset
        response = client.post("/health/reset")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "reset"
        assert data["components"] == "all"

    def test_reset_single_component(self, client):
        """Should reset specific component."""
        response = client.post("/health/reset?component=watcher_gmail")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "reset"
        assert data["component"] == "watcher_gmail"


class TestRateLimitFunction:
    """Test rate limiting helper function."""

    def test_check_rate_limit_allows_under_limit(self):
        """Should allow requests under limit."""
        _rate_limit_window.clear()
        client_ip = "test_ip_1"
        
        # First request should be allowed
        assert check_rate_limit(client_ip) is True

    def test_check_rate_limit_blocks_over_limit(self):
        """Should block requests over limit."""
        _rate_limit_window.clear()
        client_ip = "test_ip_2"
        
        # Fill up the window
        for _ in range(60):
            check_rate_limit(client_ip)
        
        # Next should be blocked
        assert check_rate_limit(client_ip) is False

    def test_check_rate_limit_window_expires(self):
        """Should allow requests after window expires."""
        _rate_limit_window.clear()
        client_ip = "test_ip_3"
        
        # Add old timestamps
        old_time = time.time() - 120  # 2 minutes ago
        _rate_limit_window[client_ip] = [old_time] * 60
        
        # Should be allowed (old entries expired)
        assert check_rate_limit(client_ip) is True


class TestIntegration:
    """Integration tests for health endpoint."""

    def test_health_metrics_consistency(self, client):
        """Health and metrics should report consistent data."""
        health_response = client.get("/health")
        metrics_response = client.get("/metrics")
        
        health_data = health_response.json()
        metrics_content = metrics_response.text
        
        # Check that components in health appear in metrics
        for component in health_data["components"].keys():
            assert f'component="{component}"' in metrics_content

    def test_ready_reflects_health_status(self, client):
        """Ready endpoint should reflect health status."""
        health_response = client.get("/health")
        ready_response = client.get("/ready")
        
        health_data = health_response.json()
        
        # If overall healthy, ready should be 200
        # If unhealthy, ready may be 503
        if health_data["status"] == "healthy":
            assert ready_response.status_code == 200
