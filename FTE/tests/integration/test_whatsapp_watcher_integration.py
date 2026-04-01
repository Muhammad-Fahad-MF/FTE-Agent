"""Integration tests for WhatsAppWatcher class."""

import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.watchers.whatsapp_watcher import WhatsAppWatcher


class TestWhatsAppWatcherIntegration:
    """Integration tests for WhatsAppWatcher with real file system."""

    @pytest.fixture
    def tmp_vault(self, tmp_path):
        """Create temporary vault directory."""
        vault = tmp_path / "vault"
        vault.mkdir()
        (vault / "Needs_Action").mkdir()
        (vault / "Logs").mkdir()
        (vault / "Dashboard.md").write_text("# Dashboard\n", encoding="utf-8")
        return vault

    @pytest.fixture
    def mock_playwright(self):
        """Mock Playwright instance for integration tests."""
        mock_page = AsyncMock()
        mock_page.goto = AsyncMock()
        mock_page.wait_for_timeout = AsyncMock()
        mock_page.wait_for_selector = AsyncMock()
        mock_page.query_selector = AsyncMock()
        mock_page.query_selector_all = AsyncMock()

        mock_context = AsyncMock()
        mock_context.new_page = AsyncMock(return_value=mock_page)
        mock_context.set_viewport_size = AsyncMock()
        mock_context.storage_state = AsyncMock(
            return_value={"cookies": [], "origins": []}
        )
        mock_context.close = AsyncMock()

        mock_browser = AsyncMock()
        mock_browser.new_context = AsyncMock(return_value=mock_context)
        mock_browser.close = AsyncMock()

        mock_playwright = AsyncMock()
        mock_playwright.chromium.launch = AsyncMock(return_value=mock_browser)
        mock_playwright.stop = AsyncMock()

        return mock_playwright, mock_browser, mock_context, mock_page

    def test_watcher_creates_action_file_in_needs_action(
        self, tmp_vault, mock_playwright
    ):
        """Verify watcher creates action file in Needs_Action directory."""
        mock_pw, mock_browser, mock_context, mock_page = mock_playwright

        # Setup mock message extraction
        mock_contact_elem = AsyncMock()
        mock_contact_elem.inner_text = AsyncMock(return_value="Test User")
        mock_message_elem = AsyncMock()
        mock_message_elem.inner_text = AsyncMock(
            return_value="URGENT: Please help with payment"
        )
        mock_time_elem = AsyncMock()
        mock_time_elem.inner_text = AsyncMock(return_value="10:00 AM")

        mock_message_row = AsyncMock()
        mock_message_row.query_selector = AsyncMock(
            side_effect=lambda x: {
                'span[data-testid="meta-title"]': mock_contact_elem,
                'span[data-testid="message-preview"]': mock_message_elem,
                'span[data-testid="message-preview-time"]': mock_time_elem,
            }.get(x)
        )

        mock_page.query_selector_all = AsyncMock(return_value=[mock_message_row])
        mock_page.wait_for_selector = AsyncMock(return_value=MagicMock())

        # Create watcher (not dry run)
        watcher = WhatsAppWatcher(
            vault_path=str(tmp_vault),
            dry_run=False,
            interval=30,
        )
        watcher._playwright = mock_pw
        watcher._browser = mock_browser
        watcher._context = mock_context
        watcher._page = mock_page

        # Run check
        messages = watcher.check_for_updates()

        # Verify action file was created
        needs_action_dir = tmp_vault / "Needs_Action"
        action_files = list(needs_action_dir.glob("WHATSAPP_*.md"))

        assert len(action_files) == 1
        assert action_files[0].exists()

        # Verify file content
        content = action_files[0].read_text(encoding="utf-8")
        assert "type: whatsapp" in content
        assert "Test User" in content
        assert "URGENT: Please help with payment" in content
        assert "keywords: urgent, payment" in content

    def test_session_persists_across_restarts(self, tmp_vault, mock_playwright):
        """Verify session storage path is correct for persistence."""
        mock_pw, mock_browser, mock_context, mock_page = mock_playwright

        # Create watcher
        watcher = WhatsAppWatcher(
            vault_path=str(tmp_vault),
            dry_run=True,
            interval=30,
        )
        watcher._playwright = mock_pw
        watcher._browser = mock_browser
        watcher._context = mock_context
        watcher._page = mock_page

        # Save session
        asyncio.run(watcher._save_session())

        # Verify storage_state was called with correct path
        assert mock_context.storage_state.called
        call_args = mock_context.storage_state.call_args
        storage_path = call_args.kwargs["path"]

        # Verify path is in whatsapp_session directory
        assert "whatsapp_session" in storage_path
        assert "storage.json" in storage_path

        # Verify directory was created
        session_dir = tmp_vault / "whatsapp_session"
        assert session_dir.exists()

    def test_multiple_messages_create_multiple_action_files(
        self, tmp_vault, mock_playwright
    ):
        """Verify multiple matching messages create multiple action files."""
        mock_pw, mock_browser, mock_context, mock_page = mock_playwright

        # Create multiple mock message rows
        def create_message_row(contact, message, time):
            row = AsyncMock()
            contact_elem = AsyncMock()
            contact_elem.inner_text = AsyncMock(return_value=contact)
            message_elem = AsyncMock()
            message_elem.inner_text = AsyncMock(return_value=message)
            time_elem = AsyncMock()
            time_elem.inner_text = AsyncMock(return_value=time)

            row.query_selector = AsyncMock(
                side_effect=lambda x: {
                    'span[data-testid="meta-title"]': contact_elem,
                    'span[data-testid="message-preview"]': message_elem,
                    'span[data-testid="message-preview-time"]': time_elem,
                }.get(x)
            )
            return row

        message_rows = [
            create_message_row("User1", "URGENT: Help needed", "10:00 AM"),
            create_message_row("User2", "Payment reminder", "10:05 AM"),
            create_message_row("User3", "Regular message", "10:10 AM"),  # No keywords
        ]

        mock_page.query_selector_all = AsyncMock(return_value=message_rows)
        mock_page.wait_for_selector = AsyncMock(return_value=MagicMock())

        # Create watcher (not dry run)
        watcher = WhatsAppWatcher(
            vault_path=str(tmp_vault),
            dry_run=False,
            interval=30,
        )
        watcher._playwright = mock_pw
        watcher._browser = mock_browser
        watcher._context = mock_context
        watcher._page = mock_page

        # Run check
        messages = watcher.check_for_updates()

        # Should have 2 messages (User1 and User2 have keywords)
        assert len(messages) == 2

        # Verify action files created
        needs_action_dir = tmp_vault / "Needs_Action"
        action_files = list(needs_action_dir.glob("WHATSAPP_*.md"))
        assert len(action_files) == 2

    def test_watcher_handles_session_expiry_gracefully(
        self, tmp_vault, mock_playwright
    ):
        """Verify watcher handles session expiry without crashing."""
        mock_pw, mock_browser, mock_context, mock_page = mock_playwright

        # Mock session recovery to return False (expired)
        from playwright.async_api import TimeoutError as PlaywrightTimeoutError

        async def timeout_side_effect(*args, **kwargs):
            raise PlaywrightTimeoutError()

        mock_page.wait_for_selector = AsyncMock(side_effect=timeout_side_effect)
        mock_page.query_selector = AsyncMock(return_value=None)  # No QR code either

        watcher = WhatsAppWatcher(
            vault_path=str(tmp_vault),
            dry_run=True,
            interval=30,
        )
        watcher._playwright = mock_pw
        watcher._browser = mock_browser
        watcher._context = mock_context
        watcher._page = mock_page

        # Should return empty list, not raise
        result = watcher.check_for_updates()
        assert result == []

        # Verify Dashboard.md was updated
        dashboard_path = tmp_vault / "Dashboard.md"
        content = dashboard_path.read_text(encoding="utf-8")
        assert "Session Expired: WhatsApp" in content
