"""
Integration tests for FTE-Agent Auto-Restart
Coverage: Systemd service auto-restart functionality
"""

import pytest
import subprocess
import time
from pathlib import Path


class TestAutoRestart:
    """Tests for systemd auto-restart functionality."""
    
    @pytest.fixture
    def service_name(self):
        """Service name for testing."""
        return "fte-agent"
    
    def test_systemd_service_file_exists(self, service_name):
        """Test systemd service file exists."""
        service_file = Path("/etc/systemd/system") / f"{service_name}.service"
        
        # This test will only pass if run on Cloud VM with service installed
        # For local testing, we check if the source file exists
        source_file = Path(__file__).parent.parent.parent / "scripts" / "deploy" / "fte-agent.service"
        
        assert source_file.exists(), f"Service file not found: {source_file}"
    
    def test_systemd_restart_policy(self, service_name):
        """Test systemd restart policy configuration."""
        # Read service file
        source_file = Path(__file__).parent.parent.parent / "scripts" / "deploy" / "fte-agent.service"
        
        if not source_file.exists():
            pytest.skip("Service file not available for testing")
        
        content = source_file.read_text()
        
        # Check restart policy
        assert "Restart=always" in content, "Restart policy should be 'always'"
        assert "RestartSec=" in content, "RestartSec should be configured"
        
        # Extract RestartSec value
        for line in content.split("\n"):
            if line.startswith("RestartSec="):
                restart_sec = int(line.split("=")[1])
                assert restart_sec <= 10, f"RestartSec should be <= 10, got {restart_sec}"
                break
    
    @pytest.mark.skip(reason="Requires systemd (Cloud VM only)")
    def test_service_auto_restart(self, service_name):
        """
        Test actual auto-restart functionality.
        
        This test kills the service process and measures restart time.
        Only runs on Cloud VM with systemd.
        """
        # Get current PID
        result = subprocess.run(
            ["systemctl", "show", service_name, "--property=MainPID", "--value"],
            capture_output=True,
            text=True,
        )
        pid_before = int(result.stdout.strip())
        
        assert pid_before > 0, "Service should be running"
        
        # Kill the process
        subprocess.run(["sudo", "kill", str(pid_before)], check=True)
        
        # Wait for restart
        time.sleep(10)
        
        # Get new PID
        result = subprocess.run(
            ["systemctl", "show", service_name, "--property=MainPID", "--value"],
            capture_output=True,
            text=True,
        )
        pid_after = int(result.stdout.strip())
        
        # Verify restart
        assert pid_after > 0, "Service should have restarted"
        assert pid_after != pid_before, "PID should have changed"
    
    @pytest.mark.skip(reason="Requires systemd (Cloud VM only)")
    def test_service_start_on_boot(self, service_name):
        """Test service is enabled for startup on boot."""
        result = subprocess.run(
            ["systemctl", "is-enabled", service_name],
            capture_output=True,
            text=True,
        )
        
        assert result.stdout.strip() == "enabled", "Service should be enabled"
    
    @pytest.mark.skip(reason="Requires systemd (Cloud VM only)")
    def test_service_status(self, service_name):
        """Test service status."""
        result = subprocess.run(
            ["systemctl", "is-active", service_name],
            capture_output=True,
            text=True,
        )
        
        assert result.stdout.strip() == "active", "Service should be active"
    
    def test_service_resource_limits(self, service_name):
        """Test service resource limits configuration."""
        source_file = Path(__file__).parent.parent.parent / "scripts" / "deploy" / "fte-agent.service"
        
        if not source_file.exists():
            pytest.skip("Service file not available for testing")
        
        content = source_file.read_text()
        
        # Check resource limits
        assert "MemoryLimit=" in content, "Memory limit should be configured"
        assert "CPUQuota=" in content, "CPU quota should be configured"
        
        # Verify limits are reasonable
        for line in content.split("\n"):
            if line.startswith("MemoryLimit="):
                assert "500M" in line, "Memory limit should be 500M"
            if line.startswith("CPUQuota="):
                cpu_quota = int(line.split("=")[1].replace("%", ""))
                assert cpu_quota <= 100, f"CPU quota should be <= 100%, got {cpu_quota}%"
