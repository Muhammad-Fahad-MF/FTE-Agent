"""Unit tests for approval workflow (request_approval skill and approval handler).

Tests cover:
- Approval request creation
- Expiry detection and flagging
- Approval/rejection detection
- Circuit breaker integration
- Metrics emission
"""

import os
import tempfile
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import yaml

from src.approval_handler import ApprovalHandler, get_approval_handler
from src.skills.request_approval import (
    ApprovalExpiredError,
    ApprovalRequiredError,
    RequestApprovalSkill,
)


@pytest.fixture(scope="module")
def temp_data_dir():
    """Create temporary data directory for SQLite databases."""
    with tempfile.TemporaryDirectory() as tmpdir:
        data_dir = Path(tmpdir) / "data"
        data_dir.mkdir(parents=True)
        yield data_dir


class TestRequestApprovalSkill:
    """Tests for RequestApprovalSkill."""

    @pytest.fixture
    def temp_vault(self):
        """Create temporary vault directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            vault = Path(tmpdir) / "vault"
            vault.mkdir(parents=True)
            (vault / "Pending_Approval").mkdir()
            (vault / "Approved").mkdir()
            (vault / "Rejected").mkdir()
            (vault / "Templates").mkdir()
            yield vault

    @pytest.fixture
    def skill(self, temp_vault, temp_data_dir):
        """Create RequestApprovalSkill instance with mocked dependencies."""
        # Create data directory for metrics DB
        (temp_data_dir).mkdir(parents=True, exist_ok=True)
        
        with patch("src.skills.base_skill.AuditLogger") as MockLogger:
            with patch("src.skills.base_skill.get_metrics_collector") as mock_get_metrics:
                mock_logger = MagicMock()
                MockLogger.return_value = mock_logger
                mock_metrics = MagicMock()
                mock_get_metrics.return_value = mock_metrics
                
                skill = RequestApprovalSkill(vault_dir=temp_vault)
                yield skill

    def test_create_approval_request_creates_file(self, skill):
        """Test approval request file creation."""
        action = {"type": "email", "to": "test@example.com", "subject": "Test"}
        reason = "New contact requires approval"

        approval_path = skill.create_approval_request(
            action=action, reason=reason, risk_level="medium"
        )

        assert approval_path.exists(), f"File not created: {approval_path}"
        assert "Pending_Approval" in str(approval_path.parent)
        assert approval_path.name.startswith("APPROVAL_EMAIL_")

    def test_create_approval_request_yaml_frontmatter(self, skill):
        """Test YAML frontmatter includes all 8 required fields."""
        action = {"type": "email", "to": "test@example.com"}
        reason = "Test reason"

        approval_path = skill.create_approval_request(
            action=action, reason=reason, risk_level="low"
        )

        # Read file and extract YAML frontmatter
        content = approval_path.read_text(encoding="utf-8", errors="replace")
        
        # Find YAML frontmatter between --- markers
        if not content.startswith("---"):
            pytest.fail("File does not start with YAML frontmatter delimiter")
            
        end_marker = content.find("\n---\n", 3)
        if end_marker < 0:
            pytest.fail("YAML frontmatter end marker not found")
            
        yaml_content = content[4:end_marker].strip()
        frontmatter = yaml.safe_load(yaml_content)

        # Check all 8 required fields
        assert frontmatter["type"] == "approval_request"
        assert frontmatter["action"] == "email"
        assert "action_details" in frontmatter
        assert "created" in frontmatter
        assert "expires" in frontmatter
        assert frontmatter["status"] == "pending"
        assert frontmatter["risk_level"] == "low"
        assert frontmatter["reason"] == "Test reason"

        # Verify expiry is 24 hours from creation
        created = datetime.fromisoformat(frontmatter["created"])
        expires = datetime.fromisoformat(frontmatter["expires"])
        assert expires - created >= timedelta(hours=23)
        assert expires - created <= timedelta(hours=25)

    def test_create_approval_request_invalid_risk_level(self, skill):
        """Test invalid risk level raises ValueError."""
        action = {"type": "email"}

        with pytest.raises(ValueError, match="Invalid risk_level"):
            skill.create_approval_request(action=action, reason="test", risk_level="invalid")

    def test_create_approval_request_dry_run(self, temp_vault, temp_data_dir):
        """Test dry run mode doesn't create file."""
        (temp_data_dir).mkdir(parents=True, exist_ok=True)
        
        with patch("src.skills.base_skill.AuditLogger") as MockLogger:
            with patch("src.skills.base_skill.get_metrics_collector") as mock_get_metrics:
                mock_logger = MagicMock()
                MockLogger.return_value = mock_logger
                mock_metrics = MagicMock()
                mock_get_metrics.return_value = mock_metrics
                
                skill = RequestApprovalSkill(vault_dir=temp_vault, dry_run=True)
                
                action = {"type": "email"}
                approval_path = skill.create_approval_request(
                    action=action, reason="test", risk_level="medium"
                )

                # In dry run, file should not be created
                assert not approval_path.exists()

    def test_check_expiry_returns_expired_files(self, skill):
        """Test check_expiry detects expired approvals."""
        # Create an expired approval file
        expired_time = datetime.now() - timedelta(hours=25)
        expires_time = expired_time + timedelta(hours=24)

        # Get the vault directory from the skill
        pending_dir = skill.pending_approval_dir
        
        approval_file = pending_dir / "APPROVAL_TEST_EXPIRED.md"
        # Use simple YAML without Unicode characters
        content = f"""---
type: approval_request
action: test
created: {expired_time.strftime('%Y-%m-%dT%H:%M:%S')}
expires: {expires_time.strftime('%Y-%m-%dT%H:%M:%S')}
status: pending
risk_level: low
reason: Test
---

# Test content
"""
        approval_file.write_text(content, encoding="utf-8")

        expired = skill.check_expiry()

        assert len(expired) >= 1, f"No expired files found. Files in dir: {list(pending_dir.glob('*.md'))}"
        assert any(f.name == "APPROVAL_TEST_EXPIRED.md" for f in expired)

    def test_check_expiry_returns_empty_for_valid(self, skill, temp_vault):
        """Test check_expiry returns empty for non-expired approvals."""
        created_time = datetime.now()
        expires_time = created_time + timedelta(hours=24)

        approval_file = temp_vault / "Pending_Approval" / "APPROVAL_TEST_VALID.md"
        content = f"""---
type: approval_request
action: test
created: {created_time.isoformat()}
expires: {expires_time.isoformat()}
status: pending
risk_level: low
reason: Test
---
# Test
"""
        approval_file.write_text(content, encoding="utf-8")

        expired = skill.check_expiry()
        assert len(expired) == 0

    def test_flag_expired_updates_status(self, skill, temp_vault):
        """Test flag_expired updates status to expired."""
        expired_time = datetime.now() - timedelta(hours=25)
        expires_time = expired_time + timedelta(hours=24)

        approval_file = temp_vault / "Pending_Approval" / "APPROVAL_TEST_FLAG.md"
        content = f"""---
type: approval_request
action: test
created: {expired_time.isoformat()}
expires: {expires_time.isoformat()}
status: pending
risk_level: low
reason: Test
---
# Test
"""
        approval_file.write_text(content, encoding="utf-8")

        skill.flag_expired([approval_file])

        updated_content = approval_file.read_text(encoding="utf-8")
        match = updated_content.split("---", 2)
        frontmatter = yaml.safe_load(match[1])
        assert frontmatter["status"] == "expired"

    def test_flag_expired_updates_dashboard(self, skill, temp_vault):
        """Test flag_expired updates Dashboard.md."""
        dashboard_path = temp_vault / "Dashboard.md"
        dashboard_path.write_text("# Dashboard\n", encoding="utf-8")

        expired_time = datetime.now() - timedelta(hours=25)
        expires_time = expired_time + timedelta(hours=24)

        approval_file = temp_vault / "Pending_Approval" / "APPROVAL_TEST_DASHBOARD.md"
        content = f"""---
type: approval_request
action: test
created: {expired_time.isoformat()}
expires: {expires_time.isoformat()}
status: pending
risk_level: low
reason: Test
---
# Test
"""
        approval_file.write_text(content, encoding="utf-8")

        skill.flag_expired([approval_file])

        dashboard_content = dashboard_path.read_text(encoding="utf-8")
        assert "EXPIRED APPROVALS ALERT" in dashboard_content
        assert "APPROVAL_TEST_DASHBOARD.md" in dashboard_content

    def test_get_approval_status_returns_status(self, skill, temp_vault):
        """Test get_approval_status reads status correctly."""
        approval_file = temp_vault / "Pending_Approval" / "APPROVAL_TEST_STATUS.md"
        content = """---
type: approval_request
action: test
status: approved
---
# Test
"""
        approval_file.write_text(content, encoding="utf-8")

        status = skill.get_approval_status(approval_file)
        assert status == "approved"

    def test_get_approval_status_nonexistent_file(self, skill):
        """Test get_approval_status returns None for nonexistent file."""
        status = skill.get_approval_status(Path("/nonexistent/file.md"))
        assert status is None


class TestApprovalHandler:
    """Tests for ApprovalHandler."""

    @pytest.fixture
    def temp_vault(self):
        """Create temporary vault directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            vault = Path(tmpdir) / "vault"
            vault.mkdir(parents=True)
            (vault / "Pending_Approval").mkdir()
            (vault / "Approved").mkdir()
            (vault / "Rejected").mkdir()
            yield vault

    @pytest.fixture
    def handler(self, temp_vault, temp_data_dir):
        """Create ApprovalHandler instance with mocked dependencies."""
        with patch("src.approval_handler.AuditLogger") as MockLogger:
            with patch("src.approval_handler.get_metrics_collector") as mock_get_metrics:
                with patch("src.approval_handler.PersistentCircuitBreaker") as MockCB:
                    mock_logger = MagicMock()
                    MockLogger.return_value = mock_logger
                    mock_metrics = MagicMock()
                    mock_get_metrics.return_value = mock_metrics
                    mock_cb = MagicMock()
                    MockCB.return_value = mock_cb
                    
                    handler = ApprovalHandler(vault_dir=temp_vault, check_interval=0.5)
                    handler.metrics = mock_metrics
                    handler.circuit_breaker = mock_cb
                    handler.logger = mock_logger
                    yield handler

    def test_handler_initialization(self, handler, temp_vault):
        """Test handler initializes with correct directories."""
        assert handler.pending_approval_dir.exists()
        assert handler.approved_dir.exists()
        assert handler.rejected_dir.exists()
        assert not handler.is_running()

    def test_register_approval_callback(self, handler):
        """Test callback registration."""
        def test_callback(f):
            pass
        
        handler.register_approval_callback(test_callback)
        assert test_callback in handler._approval_callbacks

    def test_register_rejection_callback(self, handler):
        """Test rejection callback registration."""
        def test_callback(f):
            pass
        
        handler.register_rejection_callback(test_callback)
        assert test_callback in handler._rejection_callbacks

    def test_detect_approved_file(self, handler, temp_vault):
        """Test detection of approved files."""
        approved_file = temp_vault / "Approved" / "APPROVAL_TEST_APPROVED.md"
        approved_file.write_text(
            "---\ntype: approval_request\nstatus: approved\n---\n",
            encoding="utf-8"
        )

        detected = handler._detect_approved_files()
        assert len(detected) == 1
        assert detected[0].name == "APPROVAL_TEST_APPROVED.md"

    def test_detect_rejected_file(self, handler, temp_vault):
        """Test detection of rejected files."""
        rejected_file = temp_vault / "Rejected" / "APPROVAL_TEST_REJECTED.md"
        rejected_file.write_text(
            "---\ntype: approval_request\nstatus: rejected\n---\n",
            encoding="utf-8"
        )

        detected = handler._detect_rejected_files()
        assert len(detected) == 1
        assert detected[0].name == "APPROVAL_TEST_REJECTED.md"

    def test_process_approval_calls_callbacks(self, handler, temp_vault):
        """Test processing approved file calls callbacks."""
        callback_called = []
        
        def test_callback(approval_file):
            callback_called.append(approval_file)

        handler.register_approval_callback(test_callback)

        approved_file = temp_vault / "Approved" / "APPROVAL_TEST_CALLBACK.md"
        approved_file.write_text("---\ntype: approval_request\n---\n", encoding="utf-8")

        handler._process_approval(approved_file)
        assert len(callback_called) == 1
        assert callback_called[0] == approved_file

    def test_process_rejection_calls_callbacks(self, handler, temp_vault):
        """Test processing rejected file calls callbacks."""
        callback_called = []
        
        def test_callback(rejection_file):
            callback_called.append(rejection_file)

        handler.register_rejection_callback(test_callback)

        rejected_file = temp_vault / "Rejected" / "APPROVAL_TEST_REJECT.md"
        rejected_file.write_text("---\ntype: approval_request\n---\n", encoding="utf-8")

        handler._process_rejection(rejected_file)
        assert len(callback_called) == 1
        assert callback_called[0] == rejected_file

    def test_start_stop_monitoring(self, handler):
        """Test starting and stopping monitoring."""
        handler.start()
        assert handler.is_running()

        time.sleep(1)

        handler.stop()
        assert not handler.is_running()

    def test_monitoring_detects_file_move(self, temp_vault, temp_data_dir):
        """Test monitoring detects file moves within timeout."""
        (temp_data_dir).mkdir(parents=True, exist_ok=True)
        
        with patch("src.approval_handler.AuditLogger") as MockLogger:
            with patch("src.approval_handler.get_metrics_collector") as mock_get_metrics:
                with patch("src.approval_handler.PersistentCircuitBreaker") as MockCB:
                    mock_logger = MagicMock()
                    MockLogger.return_value = mock_logger
                    mock_metrics = MagicMock()
                    mock_get_metrics.return_value = mock_metrics
                    mock_cb = MagicMock()
                    MockCB.return_value = mock_cb
                    
                    handler = ApprovalHandler(vault_dir=temp_vault, check_interval=0.3)
                    handler.metrics = mock_metrics
                    handler.circuit_breaker = mock_cb
                    handler.logger = mock_logger

                    approval_received = threading.Event()

                    def on_approval(approval_file):
                        approval_received.set()

                    handler.register_approval_callback(on_approval)
                    handler.start()

                    try:
                        approved_file = temp_vault / "Approved" / "APPROVAL_TEST_MOVE.md"
                        approved_file.write_text(
                            "---\ntype: approval_request\nstatus: approved\n---\n",
                            encoding="utf-8"
                        )

                        detected = approval_received.wait(timeout=5.0)
                        assert detected, "Approval not detected within 5 seconds"

                    finally:
                        handler.stop()

    def test_get_approval_details(self, handler, temp_vault):
        """Test reading approval details."""
        approval_file = temp_vault / "Pending_Approval" / "APPROVAL_TEST_DETAILS.md"
        content = """---
type: approval_request
action: email
action_details:
  to: test@example.com
  subject: Test
---
# Test
"""
        approval_file.write_text(content, encoding="utf-8")

        details = handler.get_approval_details(approval_file)
        assert details["to"] == "test@example.com"
        assert details["subject"] == "Test"

    def test_get_approval_handler_singleton(self, temp_vault, temp_data_dir):
        """Test get_approval_handler returns singleton."""
        (temp_data_dir).mkdir(parents=True, exist_ok=True)
        
        with patch("src.approval_handler.AuditLogger") as MockLogger:
            with patch("src.approval_handler.get_metrics_collector") as mock_get_metrics:
                with patch("src.approval_handler.PersistentCircuitBreaker") as MockCB:
                    mock_logger = MagicMock()
                    MockLogger.return_value = mock_logger
                    mock_metrics = MagicMock()
                    mock_get_metrics.return_value = mock_metrics
                    mock_cb = MagicMock()
                    MockCB.return_value = mock_cb
                    
                    handler1 = get_approval_handler(vault_dir=temp_vault)
                    handler2 = get_approval_handler(vault_dir=temp_vault)

                    assert handler1 is handler2


class TestApprovalWorkflowIntegration:
    """Integration tests for approval workflow."""

    @pytest.fixture
    def temp_vault(self, temp_data_dir):
        """Create temporary vault directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            vault = Path(tmpdir) / "vault"
            vault.mkdir(parents=True)
            (vault / "Pending_Approval").mkdir()
            (vault / "Approved").mkdir()
            (vault / "Rejected").mkdir()
            (vault / "Templates").mkdir()
            yield vault

    def test_end_to_end_approval_workflow(self, temp_vault, temp_data_dir):
        """Test complete approval workflow from creation to approval."""
        (temp_data_dir).mkdir(parents=True, exist_ok=True)
        
        with patch("src.skills.base_skill.AuditLogger") as MockLogger1:
            with patch("src.skills.base_skill.get_metrics_collector") as mock_get_metrics1:
                with patch("src.approval_handler.AuditLogger") as MockLogger2:
                    with patch("src.approval_handler.get_metrics_collector") as mock_get_metrics2:
                        with patch("src.approval_handler.PersistentCircuitBreaker") as MockCB:
                            mock_logger1 = MagicMock()
                            MockLogger1.return_value = mock_logger1
                            mock_metrics1 = MagicMock()
                            mock_get_metrics1.return_value = mock_metrics1
                            
                            mock_logger2 = MagicMock()
                            MockLogger2.return_value = mock_logger2
                            mock_metrics2 = MagicMock()
                            mock_get_metrics2.return_value = mock_metrics2
                            
                            mock_cb = MagicMock()
                            MockCB.return_value = mock_cb
                            
                            skill = RequestApprovalSkill(vault_dir=temp_vault)

                            handler = ApprovalHandler(vault_dir=temp_vault, check_interval=0.3)
                            handler.metrics = mock_metrics2
                            handler.circuit_breaker = mock_cb
                            handler.logger = mock_logger2

                            approval_completed = threading.Event()
                            captured_file = None

                            def on_approval(approval_file):
                                nonlocal captured_file
                                captured_file = approval_file
                                approval_completed.set()

                            handler.register_approval_callback(on_approval)
                            handler.start()

                            try:
                                action = {"type": "email", "to": "test@example.com", "subject": "Test Email"}
                                approval_path = skill.create_approval_request(
                                    action=action, reason="Integration test", risk_level="medium"
                                )

                                assert approval_path.exists()

                                approved_path = temp_vault / "Approved" / approval_path.name
                                content = approval_path.read_text(encoding="utf-8", errors="replace")
                                content = content.replace("status: pending", "status: approved")
                                approved_path.write_text(content, encoding="utf-8")
                                approval_path.unlink()

                                detected = approval_completed.wait(timeout=5.0)
                                assert detected, "Approval not detected within 5 seconds"
                                assert captured_file is not None
                                assert captured_file.name == approved_path.name

                            finally:
                                handler.stop()

    def test_concurrent_approval_requests(self, temp_vault, temp_data_dir):
        """Test handling multiple concurrent approval requests."""
        (temp_data_dir).mkdir(parents=True, exist_ok=True)
        
        with patch("src.skills.base_skill.AuditLogger") as MockLogger:
            with patch("src.skills.base_skill.get_metrics_collector") as mock_get_metrics:
                mock_logger = MagicMock()
                MockLogger.return_value = mock_logger
                mock_metrics = MagicMock()
                mock_get_metrics.return_value = mock_metrics
                
                skill = RequestApprovalSkill(vault_dir=temp_vault)

                approval_paths = []
                for i in range(5):
                    action = {"type": "email", "to": f"user{i}@example.com"}
                    path = skill.create_approval_request(
                        action=action, reason=f"Concurrent test {i}", risk_level="low"
                    )
                    approval_paths.append(path)

                for path in approval_paths:
                    assert path.exists(), f"File not created: {path}"
                    assert "Pending_Approval" in str(path.parent)

                filenames = [p.name for p in approval_paths]
                assert len(set(filenames)) == 5, f"Duplicate filenames: {filenames}"


class TestCircuitBreakerIntegration:
    """Tests for circuit breaker integration in approval workflow."""

    @pytest.fixture
    def temp_vault(self, temp_data_dir):
        """Create temporary vault directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            vault = Path(tmpdir) / "vault"
            vault.mkdir(parents=True)
            (vault / "Pending_Approval").mkdir()
            (vault / "Approved").mkdir()
            (vault / "Rejected").mkdir()
            yield vault

    def test_approval_handler_has_circuit_breaker(self, temp_vault, temp_data_dir):
        """Test approval handler has circuit breaker."""
        (temp_data_dir).mkdir(parents=True, exist_ok=True)
        
        with patch("src.approval_handler.AuditLogger") as MockLogger:
            with patch("src.approval_handler.get_metrics_collector") as mock_get_metrics:
                with patch("src.approval_handler.PersistentCircuitBreaker") as MockCB:
                    mock_logger = MagicMock()
                    MockLogger.return_value = mock_logger
                    mock_metrics = MagicMock()
                    mock_get_metrics.return_value = mock_metrics
                    mock_cb = MagicMock()
                    mock_cb.name = "approval_handler"
                    MockCB.return_value = mock_cb
                    
                    handler = ApprovalHandler(vault_dir=temp_vault)

                    assert hasattr(handler, "circuit_breaker")
                    assert handler.circuit_breaker is not None

    def test_approval_handler_circuit_breaker_name(self, temp_vault, temp_data_dir):
        """Test circuit breaker has correct name."""
        (temp_data_dir).mkdir(parents=True, exist_ok=True)
        
        with patch("src.approval_handler.AuditLogger") as MockLogger:
            with patch("src.approval_handler.get_metrics_collector") as mock_get_metrics:
                with patch("src.approval_handler.PersistentCircuitBreaker") as MockCB:
                    mock_logger = MagicMock()
                    MockLogger.return_value = mock_logger
                    mock_metrics = MagicMock()
                    mock_get_metrics.return_value = mock_metrics
                    mock_cb = MagicMock()
                    mock_cb.name = "approval_handler"
                    MockCB.return_value = mock_cb
                    
                    handler = ApprovalHandler(vault_dir=temp_vault)

                    assert handler.circuit_breaker.name == "approval_handler"
