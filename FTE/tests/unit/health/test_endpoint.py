"""
Unit tests for FTE-Agent Health Endpoint
Coverage: HealthChecker, create_health_app
"""

import time
from pathlib import Path
from unittest.mock import patch

import pytest

from src.health.endpoint import HealthChecker, create_health_app


class TestHealthChecker:
    """Tests for HealthChecker class."""

    @pytest.fixture
    def health_checker(self):
        """Create HealthChecker instance."""
        return HealthChecker(vault_path=Path("/tmp/test-vault"))

    def test_get_uptime(self, health_checker):
        """Test uptime calculation."""
        # Wait a bit to ensure uptime > 0
        time.sleep(0.1)
        uptime = health_checker.get_uptime()
        assert uptime >= 0
        assert isinstance(uptime, int)

    def test_get_status_healthy(self, health_checker):
        """Test healthy status determination."""
        with patch.object(health_checker, "_get_cached_metrics") as mock_metrics:
            mock_metrics.return_value = {
                "cpu_percent": 40,
                "memory_percent": 50,
                "disk_percent": 60,
            }
            status = health_checker.get_status()
            assert status == "healthy"

    def test_get_status_degraded_cpu(self, health_checker):
        """Test degraded status due to high CPU."""
        with patch.object(health_checker, "_get_cached_metrics") as mock_metrics:
            mock_metrics.return_value = {
                "cpu_percent": 85,
                "memory_percent": 50,
                "disk_percent": 60,
            }
            status = health_checker.get_status()
            assert status == "degraded"

    def test_get_status_degraded_memory(self, health_checker):
        """Test degraded status due to high memory."""
        with patch.object(health_checker, "_get_cached_metrics") as mock_metrics:
            mock_metrics.return_value = {
                "cpu_percent": 40,
                "memory_percent": 85,
                "disk_percent": 60,
            }
            status = health_checker.get_status()
            assert status == "degraded"

    def test_get_status_unhealthy_disk(self, health_checker):
        """Test unhealthy status due to critical disk usage."""
        with patch.object(health_checker, "_get_cached_metrics") as mock_metrics:
            mock_metrics.return_value = {
                "cpu_percent": 40,
                "memory_percent": 50,
                "disk_percent": 95,
            }
            status = health_checker.get_status()
            assert status == "unhealthy"

    def test_get_health_data(self, health_checker):
        """Test complete health data structure."""
        with patch.object(health_checker, "_get_cached_metrics") as mock_metrics:
            mock_metrics.return_value = {
                "cpu_percent": 45.5,
                "memory_percent": 62.3,
                "disk_percent": 71.2,
                "disk_free_gb": 57.8,
            }

            health_data = health_checker.get_health_data()

            assert "status" in health_data
            assert "uptime_seconds" in health_data
            assert "timestamp" in health_data
            assert "resources" in health_data
            assert "watchers" in health_data
            assert "last_sync" in health_data

            assert health_data["resources"]["cpu_percent"] == 45.5
            assert health_data["resources"]["memory_percent"] == 62.3
            assert isinstance(health_data["watchers"], dict)

    def test_get_watcher_status(self, health_checker):
        """Test watcher status reporting."""
        watchers = health_checker._get_watcher_status()

        assert "gmail" in watchers
        assert "whatsapp" in watchers
        assert "filesystem" in watchers

    def test_get_prometheus_metrics(self, health_checker):
        """Test Prometheus metrics format."""
        with patch.object(health_checker, "_get_cached_metrics") as mock_metrics:
            mock_metrics.return_value = {
                "cpu_percent": 45.5,
                "memory_percent": 62.3,
                "disk_percent": 71.2,
                "disk_free_gb": 57.8,
            }

            metrics_text = health_checker.get_prometheus_metrics()

            # Check Prometheus format
            assert "# HELP" in metrics_text
            assert "# TYPE" in metrics_text
            assert "fte_agent_uptime_seconds" in metrics_text
            assert "fte_agent_cpu_percent" in metrics_text
            assert "fte_agent_memory_percent" in metrics_text
            assert "fte_agent_disk_percent" in metrics_text


class TestCreateHealthApp:
    """Tests for create_health_app function."""

    @pytest.fixture
    def app(self):
        """Create FastAPI app."""
        return create_health_app(vault_path=Path("/tmp/test-vault"))

    @pytest.fixture
    def client(self, app):
        """Create test client."""
        from fastapi.testclient import TestClient

        return TestClient(app)

    def test_health_endpoint(self, client):
        """Test /health endpoint response."""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()

        assert "status" in data
        assert "uptime_seconds" in data
        assert "resources" in data
        assert "watchers" in data

    def test_metrics_endpoint(self, client):
        """Test /metrics endpoint response."""
        response = client.get("/metrics")

        assert response.status_code == 200
        assert response.headers["content-type"] == "text/plain; charset=utf-8"

        metrics_text = response.text
        assert "# HELP" in metrics_text
        assert "fte_agent_" in metrics_text

    def test_readiness_probe_healthy(self, client):
        """Test /ready endpoint when healthy."""
        with patch("src.health.endpoint.HealthChecker.get_status") as mock_status:
            mock_status.return_value = "healthy"

            response = client.get("/ready")

            assert response.status_code == 200
            assert response.text == "Ready"

    def test_readiness_probe_unhealthy(self, client):
        """Test /ready endpoint when unhealthy."""
        with patch("src.health.endpoint.HealthChecker.get_status") as mock_status:
            mock_status.return_value = "unhealthy"

            response = client.get("/ready")

            assert response.status_code == 503
            assert response.text == "Service unhealthy"

    def test_root_endpoint(self, client):
        """Test root endpoint."""
        response = client.get("/")

        assert response.status_code == 200
        data = response.json()

        assert data["service"] == "FTE-Agent Health"
        assert data["version"] == "1.0.0"
        assert "endpoints" in data
