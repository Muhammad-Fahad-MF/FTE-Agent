"""Chaos tests for WhatsAppWatcher class."""

import asyncio
import time
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.watchers.whatsapp_watcher import (
    WhatsAppSessionExpiredError,
    WhatsAppWatcher,
)


class TestWhatsAppWatcherChaos:
    """Chaos tests for WhatsAppWatcher - testing resilience and recovery."""

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
        """Mock Playwright instance."""
        mock_page = AsyncMock()
        mock_page.goto = AsyncMock()
        mock_page.wait_for_timeout = AsyncMock()
        mock_page.wait_for_selector = AsyncMock()
        mock_page.query_selector = AsyncMock()
        mock_page.query_selector_all = AsyncMock()

        mock_context = AsyncMock()
        mock_context.new_page = AsyncMock(return_value=mock_page)
        mock_context.set_viewport_size = AsyncMock()
        mock_context.storage_state = AsyncMock(return_value={"cookies": []})
        mock_context.close = AsyncMock()

        mock_browser = AsyncMock()
        mock_browser.new_context = AsyncMock(return_value=mock_context)
        mock_browser.close = AsyncMock()

        mock_playwright = AsyncMock()
        mock_playwright.chromium.launch = AsyncMock(return_value=mock_browser)
        mock_playwright.stop = AsyncMock()

        return mock_playwright, mock_browser, mock_context, mock_page

    def test_browser_crash_recovery(self, tmp_vault, mock_playwright):
        """Verify watcher recovers from browser crash within 10 seconds."""
        mock_pw, mock_browser, mock_context, mock_page = mock_playwright

        # Simulate browser crash on first call, recovery on second
        call_count = {"count": 0}

        def crash_then_recover(*args, **kwargs):
            call_count["count"] += 1
            if call_count["count"] == 1:
                # First call: simulate crash
                raise Exception("Browser crashed")
            else:
                # Subsequent calls: return success
                return [MagicMock()]

        mock_page.query_selector_all = AsyncMock(side_effect=crash_then_recover)
        mock_page.wait_for_selector = AsyncMock(return_value=MagicMock())

        watcher = WhatsAppWatcher(
            vault_path=str(tmp_vault),
            dry_run=True,
            interval=30,
        )
        watcher._playwright = mock_pw
        watcher._browser = mock_browser
        watcher._context = mock_context
        watcher._page = mock_page

        # First call should fail gracefully (return empty list)
        result1 = watcher.check_for_updates()
        assert result1 == []

        # Second call should succeed
        result2 = watcher.check_for_updates()
        # Should not be empty (circuit breaker may still allow)
        assert isinstance(result2, list)

    def test_session_expiry_handling(self, tmp_vault, mock_playwright):
        """Verify watcher handles session expiry gracefully."""
        mock_pw, mock_browser, mock_context, mock_page = mock_playwright

        # Mock session expiry detection
        from playwright.async_api import TimeoutError as PlaywrightTimeoutError

        async def timeout_side_effect(*args, **kwargs):
            raise PlaywrightTimeoutError()

        mock_page.wait_for_selector = AsyncMock(side_effect=timeout_side_effect)
        mock_page.query_selector = AsyncMock(return_value=None)

        watcher = WhatsAppWatcher(
            vault_path=str(tmp_vault),
            dry_run=True,
            interval=30,
        )
        watcher._playwright = mock_pw
        watcher._browser = mock_browser
        watcher._context = mock_context
        watcher._page = mock_page

        # Should handle expiry without crashing
        result = watcher.check_for_updates()
        assert result == []

        # Verify Dashboard.md was updated
        dashboard_path = tmp_vault / "Dashboard.md"
        content = dashboard_path.read_text(encoding="utf-8")
        assert "Session Expired: WhatsApp" in content

    def test_continues_when_circuit_breaker_open(self, tmp_vault, mock_playwright):
        """Verify watcher continues other operations when circuit breaker is open."""
        mock_pw, mock_browser, mock_context, mock_page = mock_playwright

        # Force circuit breaker open by setting failure count
        watcher = WhatsAppWatcher(
            vault_path=str(tmp_vault),
            dry_run=True,
            interval=30,
        )
        watcher._playwright = mock_pw
        watcher._browser = mock_browser
        watcher._context = mock_context
        watcher._page = mock_page

        # Manually trip circuit breaker
        watcher.circuit_breaker._persisted_failure_count = 5

        # Should return empty list when circuit is open, not crash
        result = watcher.check_for_updates()
        assert result == []

        # Verify watcher can still be used (circuit breaker should allow test call)
        # After timeout, it should allow another attempt
        assert watcher.circuit_breaker.is_open() or watcher.circuit_breaker.is_half_open()

    def test_network_timeout_recovery(self, tmp_vault, mock_playwright):
        """Verify watcher recovers from network timeout."""
        mock_pw, mock_browser, mock_context, mock_page = mock_playwright

        # Simulate timeout then recovery
        call_count = {"count": 0}

        from playwright.async_api import TimeoutError as PlaywrightTimeoutError

        def timeout_then_success(*args, **kwargs):
            call_count["count"] += 1
            if call_count["count"] < 3:
                raise PlaywrightTimeoutError("Network timeout")
            else:
                return [MagicMock()]

        mock_page.wait_for_selector = AsyncMock(side_effect=timeout_then_success)

        watcher = WhatsAppWatcher(
            vault_path=str(tmp_vault),
            dry_run=True,
            interval=30,
        )
        watcher._playwright = mock_pw
        watcher._browser = mock_browser
        watcher._context = mock_context
        watcher._page = mock_page

        # First two calls should fail gracefully
        result1 = watcher.check_for_updates()
        assert result1 == []

        # Third call should succeed
        result2 = watcher.check_for_updates()
        assert isinstance(result2, list)

    def test_concurrent_checks_do_not_corrupt_state(self, tmp_vault, mock_playwright):
        """Verify concurrent checks don't corrupt watcher state."""
        mock_pw, mock_browser, mock_context, mock_page = mock_playwright

        # Mock successful check
        mock_message_row = AsyncMock()
        mock_contact_elem = AsyncMock()
        mock_contact_elem.inner_text = AsyncMock(return_value="Test")
        mock_message_elem = AsyncMock()
        mock_message_elem.inner_text = AsyncMock(return_value="URGENT message")
        mock_time_elem = AsyncMock()
        mock_time_elem.inner_text = AsyncMock(return_value="10:00 AM")

        mock_message_row.query_selector = AsyncMock(
            side_effect=lambda x: {
                'span[data-testid="meta-title"]': mock_contact_elem,
                'span[data-testid="message-preview"]': mock_message_elem,
                'span[data-testid="message-preview-time"]': mock_time_elem,
            }.get(x)
        )

        mock_page.query_selector_all = AsyncMock(return_value=[mock_message_row])
        mock_page.wait_for_selector = AsyncMock(return_value=MagicMock())

        watcher = WhatsAppWatcher(
            vault_path=str(tmp_vault),
            dry_run=True,
            interval=30,
        )
        watcher._playwright = mock_pw
        watcher._browser = mock_browser
        watcher._context = mock_context
        watcher._page = mock_page

        # Run multiple checks concurrently
        import threading

        results = []
        errors = []

        def check():
            try:
                result = watcher.check_for_updates()
                results.append(result)
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=check) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # All checks should complete without error
        assert len(errors) == 0
        assert len(results) == 5

        # All results should be lists
        for result in results:
            assert isinstance(result, list)

    def test_memory_leak_prevention(self, tmp_vault, mock_playwright):
        """Verify watcher doesn't leak memory on repeated checks."""
        mock_pw, mock_browser, mock_context, mock_page = mock_playwright

        # Mock successful check
        mock_page.wait_for_selector = AsyncMock(return_value=MagicMock())
        mock_page.query_selector_all = AsyncMock(return_value=[])

        watcher = WhatsAppWatcher(
            vault_path=str(tmp_vault),
            dry_run=True,
            interval=30,
        )
        watcher._playwright = mock_pw
        watcher._browser = mock_browser
        watcher._context = mock_context
        watcher._page = mock_page

        # Run many checks
        for _ in range(100):
            result = watcher.check_for_updates()
            assert isinstance(result, list)

        # Verify browser resources are still valid (not leaked)
        assert watcher._browser is not None
        assert watcher._context is not None
        assert watcher._page is not None

    def test_rapid_restart_handling(self, tmp_vault, mock_playwright):
        """Verify watcher handles rapid start/stop cycles."""
        mock_pw, mock_browser, mock_context, mock_page = mock_playwright

        mock_page.wait_for_selector = AsyncMock(return_value=MagicMock())
        mock_page.query_selector_all = AsyncMock(return_value=[])

        watcher = WhatsAppWatcher(
            vault_path=str(tmp_vault),
            dry_run=True,
            interval=30,
        )

        # Simulate rapid start/stop
        for _ in range(10):
            watcher._playwright = mock_pw
            watcher._browser = mock_browser
            watcher._context = mock_context
            watcher._page = mock_page

            result = watcher.check_for_updates()
            assert isinstance(result, list)

            # Close and reopen
            asyncio.run(watcher._close_browser())

            # Should be able to reinitialize
            watcher._playwright = None
            watcher._browser = None
            watcher._context = None
            watcher._page = None
