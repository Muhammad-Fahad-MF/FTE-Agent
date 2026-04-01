"""Watchers package for FTE-Agent.

This package contains watcher implementations for various input sources:
- Gmail Watcher: Monitor Gmail for unread/important emails
- WhatsApp Watcher: Monitor WhatsApp Web for keyword messages
- FileSystem Watcher: Monitor filesystem for new files (in src/)
"""

from .gmail_watcher import GmailWatcher

__all__ = ["GmailWatcher"]
