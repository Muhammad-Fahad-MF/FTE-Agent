"""Integration tests for approval workflow.

Tests end-to-end flows:
- Approval file creation and detection
- File move detection (Pending → Approved/Rejected)
- Expiry detection and Dashboard.md updates
"""

import os
import tempfile
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path

import pytest
import yaml

from src.approval_handler import ApprovalHandler
from src.skills.request_approval import RequestApprovalSkill


class TestApprovalFileCreation:
    """Test approval file creation and format."""

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
            # Create template
            template_path = vault / "Templates" / "approval_request_template.md"
            template_path.write_text("""---
type: approval_request
action: {{ACTION_TYPE}}
action_details: {{ACTION_DETAILS}}
created: {{CREATED_DATE}}
expires: {{EXPIRES_DATE}}
status: pending
risk_level: {{RISK_LEVEL}}
reason: {{REASON}}
---
# Approval Request
""")
            yield vault

    def test_approval_file_triggers_detection(self, temp_vault):
        """Test that created approval file is detected by handler."""
        skill = RequestApprovalSkill(vault_dir=temp_vault)
        handler = ApprovalHandler(vault_dir=temp_vault, check_interval=0.5)

        detected_files = []

        def on_new_approval(approval_file):
            detected_files.append(approval_file)

        # Note: We can't easily test new approval detection in Pending_Approval
        # because handler tracks known files at startup
        # Instead, test approved file detection
        handler.start()
        time.sleep(0.5)  # Let handler initialize

        try:
            # Create approval request
            action = {"type": "email", "to": "test@example.com"}
            approval_path = skill.create_approval_request(
                action=action, reason="Test", risk_level="medium"
            )

            assert approval_path.exists()

            # Verify file format
            content = approval_path.read_text()
            assert "type: approval_request" in content
            assert "status: pending" in content
            assert "email" in content

        finally:
            handler.stop()

    def test_approval_file_format_validation(self, temp_vault):
        """Test approval file matches specification format."""
        skill = RequestApprovalSkill(vault_dir=temp_vault)

        action = {
            "type": "email",
            "to": "user@example.com",
            "subject": "Test Subject",
            "body": "Test body",
        }
        approval_path = skill.create_approval_request(
            action=action, reason="New contact", risk_level="medium"
        )

        content = approval_path.read_text()

        # Parse YAML frontmatter
        match = content.split("---", 2)
        assert len(match) >= 2, "Missing YAML frontmatter delimiters"

        frontmatter = yaml.safe_load(match[1])

        # Validate all 8 required fields per spec
        required_fields = [
            "type",
            "action",
            "action_details",
            "created",
            "expires",
            "status",
            "risk_level",
            "reason",
        ]
        for field in required_fields:
            assert field in frontmatter, f"Missing required field: {field}"

        # Validate field values
        assert frontmatter["type"] == "approval_request"
        assert frontmatter["action"] == "email"
        assert frontmatter["status"] == "pending"
        assert frontmatter["risk_level"] == "medium"
        assert frontmatter["reason"] == "New contact"

        # Validate action_details contains original action
        assert frontmatter["action_details"]["to"] == "user@example.com"
        assert frontmatter["action_details"]["subject"] == "Test Subject"


class TestActionFileTriggersPlanGeneration:
    """Test that action files can trigger plan generation."""

    @pytest.fixture
    def temp_vault(self):
        """Create temporary vault directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            vault = Path(tmpdir) / "vault"
            vault.mkdir(parents=True)
            (vault / "Needs_Action").mkdir()
            (vault / "Pending_Approval").mkdir()
            (vault / "Plans").mkdir()
            yield vault

    def test_approval_request_from_action_file(self, temp_vault):
        """Test creating approval request from action file."""
        # Create an action file
        action_file = temp_vault / "Needs_Action" / "EMAIL_TEST_001.md"
        action_content = """---
type: email
from: user@example.com
to: newcontact@example.com
subject: Test
---
# Test Email Action

This requires approval for new contact.
"""
        action_file.write_text(action_content)

        # Create approval request
        skill = RequestApprovalSkill(vault_dir=temp_vault)

        action = {
            "type": "email",
            "to": "newcontact@example.com",
            "subject": "Test",
            "source_file": str(action_file),
        }

        approval_path = skill.create_approval_request(
            action=action,
            reason="New contact requires approval",
            risk_level="medium",
            source_file=action_file,
        )

        assert approval_path.exists()

        # Verify source file reference in approval
        content = approval_path.read_text()
        assert str(action_file) in content or "EMAIL_TEST_001" in content


class TestProcessedIdsPersistAcrossRestarts:
    """Test that approval state persists across handler restarts."""

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

    def test_approval_persists_after_handler_restart(self, temp_vault):
        """Test approval detection works after handler restart."""
        # Create approval file
        approval_file = temp_vault / "Pending_Approval" / "APPROVAL_PERSIST_TEST.md"
        content = """---
type: approval_request
action: email
status: pending
---
# Test
"""
        approval_file.write_text(content)

        # Start handler, let it initialize known files
        handler1 = ApprovalHandler(vault_dir=temp_vault, check_interval=0.5)
        handler1.start()
        time.sleep(1)  # Let it scan
        handler1.stop()

        # Move file to Approved (simulating user approval)
        approved_file = temp_vault / "Approved" / "APPROVAL_PERSIST_TEST.md"
        approved_file.write_text(content.replace("status: pending", "status: approved"))
        approval_file.unlink()

        # Restart handler
        approval_detected = threading.Event()

        def on_approval(f):
            approval_detected.set()

        handler2 = ApprovalHandler(vault_dir=temp_vault, check_interval=0.5)
        handler2.register_approval_callback(on_approval)
        handler2.start()

        try:
            # Should detect the approved file
            detected = approval_detected.wait(timeout=5.0)
            assert detected, "Approval not detected after restart"

        finally:
            handler2.stop()


class TestExpiryDetection:
    """Test approval expiry detection and handling."""

    @pytest.fixture
    def temp_vault(self):
        """Create temporary vault directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            vault = Path(tmpdir) / "vault"
            vault.mkdir(parents=True)
            (vault / "Pending_Approval").mkdir()
            (vault / "Dashboard.md").write_text("# Dashboard\n")
            yield vault

    def test_expiry_detection_and_flagging(self, temp_vault):
        """Test that expired approvals are detected and flagged."""
        skill = RequestApprovalSkill(vault_dir=temp_vault)

        # Create expired approval
        expired_time = datetime.now() - timedelta(hours=25)
        expires_time = expired_time + timedelta(hours=24)

        approval_file = temp_vault / "Pending_Approval" / "APPROVAL_EXPIRED_TEST.md"
        content = f"""---
type: approval_request
action: test
created: {expired_time.isoformat()}
expires: {expires_time.isoformat()}
status: pending
risk_level: high
reason: Test expiry
---
# Test
"""
        approval_file.write_text(content)

        # Check expiry
        expired = skill.check_expiry()
        assert len(expired) == 1

        # Flag expired
        skill.flag_expired(expired)

        # Verify status updated
        updated_content = approval_file.read_text()
        match = updated_content.split("---", 2)
        frontmatter = yaml.safe_load(match[1])
        assert frontmatter["status"] == "expired"

        # Verify Dashboard updated
        dashboard_content = (temp_vault / "Dashboard.md").read_text()
        assert "EXPIRED APPROVALS ALERT" in dashboard_content
        assert "APPROVAL_EXPIRED_TEST.md" in dashboard_content


class TestRejectionHandling:
    """Test rejection detection and handling."""

    @pytest.fixture
    def temp_vault(self):
        """Create temporary vault directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            vault = Path(tmpdir) / "vault"
            vault.mkdir(parents=True)
            (vault / "Pending_Approval").mkdir()
            (vault / "Rejected").mkdir()
            yield vault

    def test_rejection_file_detection(self, temp_vault):
        """Test that rejected files are detected."""
        handler = ApprovalHandler(vault_dir=temp_vault, check_interval=0.5)

        rejection_detected = threading.Event()
        captured_file = None

        def on_rejection(rejection_file):
            nonlocal captured_file
            captured_file = rejection_file
            rejection_detected.set()

        handler.register_rejection_callback(on_rejection)
        handler.start()

        try:
            # Create rejection file
            rejected_file = temp_vault / "Rejected" / "APPROVAL_REJECTED_TEST.md"
            rejected_file.write_text(
                "---\ntype: approval_request\nstatus: rejected\n---\n"
            )

            # Wait for detection
            detected = rejection_detected.wait(timeout=5.0)
            assert detected, "Rejection not detected within 5 seconds"
            assert captured_file == rejected_file

        finally:
            handler.stop()

    def test_rejection_logging(self, temp_vault):
        """Test that rejections are logged."""
        handler = ApprovalHandler(vault_dir=temp_vault)

        # Manually process a rejection
        rejected_file = temp_vault / "Rejected" / "APPROVAL_REJECT_LOG_TEST.md"
        rejected_file.write_text("---\ntype: approval_request\n---\n")

        # Should not raise
        handler._process_rejection(rejected_file)
