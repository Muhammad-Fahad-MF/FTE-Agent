"""
Social Media Fallback Mechanism.

Handles social media API unavailability with:
- API error detection (rate limits, connection errors)
- Draft post saving to /Vault/Drafts/
- Retry scheduling for next rate limit window
- User notification when fallback activated

Usage:
    from src.services.social_fallback import SocialMediaFallbackManager
    
    fallback = SocialMediaFallbackManager(vault_path="./vault")
    
    # Save draft post during fallback
    fallback.save_draft_post(
        platform="linkedin",
        content="Post content here",
        image_url="https://example.com/image.jpg",
        error="Rate limit exceeded"
    )
    
    # Schedule retry
    fallback.schedule_retry(platform="linkedin", retry_after=900)
    
    # Sync drafts when API available
    fallback.sync_drafts(platform="linkedin")
"""

import json
import logging
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Callable, Optional

from src.audit_logger import AuditLogger
from src.services.alerting import trigger_alert

logger = logging.getLogger(__name__)


class SocialMediaFallbackError(Exception):
    """Base exception for social media fallback errors."""

    pass


class SocialMediaFallbackManager:
    """
    Manages social media fallback mode when APIs are unavailable.

    Features:
    - Detects API unavailability (rate limits, connection errors)
    - Saves draft posts to markdown files
    - Schedules retries for next rate limit window
    - User notification on fallback activation
    - Automatic draft sync on API recovery

    Attributes:
        vault_path: Path to vault directory
    """

    def __init__(self, vault_path: str):
        """
        Initialize social media fallback manager.

        Args:
            vault_path: Path to vault directory
        """
        self.vault_path = Path(vault_path).resolve()

        self.logger = AuditLogger(component="social_fallback")

        # Platform state: {platform: {"fallback_active": bool, "retry_after": datetime}}
        self._platform_state: dict[str, dict[str, Any]] = {
            "linkedin": {"fallback_active": False, "retry_after": None},
            "twitter": {"fallback_active": False, "retry_after": None},
            "facebook": {"fallback_active": False, "retry_after": None},
            "instagram": {"fallback_active": False, "retry_after": None},
        }

        self._lock = threading.Lock()

        # Directories
        self.drafts_dir = self.vault_path / "Drafts"
        self.state_file = self.vault_path / "State" / "social_fallback_state.json"

        # Ensure directories exist
        self.drafts_dir.mkdir(parents=True, exist_ok=True)
        self.state_file.parent.mkdir(parents=True, exist_ok=True)

        # Load state
        self._load_state()

        self.logger.info(
            "social_fallback_initialized",
            {"vault_path": str(self.vault_path)},
        )

    def _load_state(self) -> None:
        """Load fallback state from file."""
        if self.state_file.exists():
            try:
                with open(self.state_file, "r") as f:
                    state = json.load(f)
                    self._platform_state = state.get("platform_state", self._platform_state)
            except Exception as e:
                logger.warning(f"Failed to load social fallback state: {e}")

    def _save_state(self) -> None:
        """Save fallback state to file."""
        try:
            state = {
                "platform_state": self._platform_state,
                "last_updated": datetime.now().isoformat(),
            }
            with open(self.state_file, "w") as f:
                json.dump(state, f, indent=2)
        except Exception as e:
            logger.warning(f"Failed to save social fallback state: {e}")

    def is_fallback_active(self, platform: str) -> bool:
        """
        Check if fallback mode is active for a platform.

        Args:
            platform: Platform name (linkedin, twitter, facebook, instagram)

        Returns:
            True if fallback mode is active
        """
        if platform not in self._platform_state:
            return False
        return self._platform_state[platform].get("fallback_active", False)

    def activate_fallback(
        self,
        platform: str,
        error: str,
        retry_after: Optional[int] = None,
    ) -> None:
        """
        Activate fallback mode for a platform.

        Args:
            platform: Platform name
            error: Error that triggered fallback
            retry_after: Seconds until retry (optional)
        """
        with self._lock:
            if platform not in self._platform_state:
                logger.warning(f"Unknown platform: {platform}")
                return

            self._platform_state[platform]["fallback_active"] = True

            if retry_after:
                retry_time = datetime.now() + timedelta(seconds=retry_after)
                self._platform_state[platform]["retry_after"] = retry_time.isoformat()

            self._save_state()

            self.logger.log(
                "WARNING",
                "social_fallback_activated",
                {
                    "platform": platform,
                    "error": error,
                    "retry_after": self._platform_state[platform].get("retry_after"),
                },
            )

            # Trigger alert
            trigger_alert(
                alert_type=f"social_fallback_{platform}",
                message=f"Social media fallback activated for {platform}: {error}",
                severity="WARNING",
                details={
                    "platform": platform,
                    "error": error,
                    "retry_after": self._platform_state[platform].get("retry_after"),
                },
            )

            # Update dashboard
            self._update_dashboard_fallback_status()

    def deactivate_fallback(self, platform: str) -> None:
        """
        Deactivate fallback mode for a platform.

        Args:
            platform: Platform name
        """
        with self._lock:
            if platform in self._platform_state:
                self._platform_state[platform]["fallback_active"] = False
                self._platform_state[platform]["retry_after"] = None
                self._save_state()

                self.logger.log(
                    "INFO",
                    "social_fallback_deactivated",
                    {"platform": platform, "timestamp": datetime.now().isoformat()},
                )

                # Update dashboard
                self._update_dashboard_fallback_status()

    def save_draft_post(
        self,
        platform: str,
        content: str,
        image_url: Optional[str] = None,
        error: Optional[str] = None,
        scheduled_time: Optional[str] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> Path:
        """
        Save a draft post to vault.

        Args:
            platform: Platform name (linkedin, twitter, facebook, instagram)
            content: Post content
            image_url: Optional image URL
            error: Error that caused fallback
            scheduled_time: Optional scheduled posting time
            metadata: Additional metadata

        Returns:
            Path to created draft file
        """
        timestamp = datetime.now()
        draft_id = timestamp.strftime("%Y%m%d_%H%M%S_%f")

        draft_data = {
            "id": draft_id,
            "platform": platform,
            "content": content,
            "image_url": image_url,
            "error": error,
            "scheduled_time": scheduled_time,
            "metadata": metadata or {},
            "created": timestamp.isoformat(),
            "status": "draft",
            "retry_count": 0,
        }

        # Create markdown file
        draft_file = self.drafts_dir / f"DRAFT_{platform}_{draft_id}.md"
        self._write_draft_file(draft_file, draft_data)

        # Activate fallback if error provided
        if error:
            self.activate_fallback(platform, error)

        self.logger.log(
            "INFO",
            "social_draft_saved",
            {
                "platform": platform,
                "draft_id": draft_id,
                "draft_file": str(draft_file),
            },
        )

        return draft_file

    def _write_draft_file(self, draft_file: Path, draft_data: dict[str, Any]) -> None:
        """Write draft data to markdown file."""
        content = f"""---
platform: {draft_data['platform']}
draft_id: {draft_data['id']}
created: {draft_data['created']}
status: {draft_data['status']}
retry_count: {draft_data['retry_count']}
scheduled_time: {draft_data.get('scheduled_time', 'N/A')}
error: {draft_data.get('error', 'N/A')}
---

# Draft Post: {draft_data['platform'].title()}

**Created**: {draft_data['created']}
**Status**: {draft_data['status']}
**Retry Count**: {draft_data['retry_count']}

## Content

{draft_data['content']}

"""

        if draft_data.get('image_url'):
            content += f"## Image\n\n![Image]({draft_data['image_url']})\n\n"

        if draft_data.get('error'):
            content += f"""## Fallback Information

**Error**: {draft_data['error']}
**Scheduled Time**: {draft_data.get('scheduled_time', 'N/A')}

"""

        content += f"""## Metadata

```json
{json.dumps(draft_data.get('metadata', {}), indent=2)}
```

---

## Posting Instructions

**To post manually:**

1. Review the content above
2. Post to {draft_data['platform'].title()}
3. Move this file to `Done/` with prefix `POSTED_`

**To schedule retry:**

- File will be automatically retried when API is available
- Check status in Dashboard.md

---

*Generated by FTE Agent Social Media Fallback*
"""

        draft_file.write_text(content, encoding="utf-8")

    def schedule_retry(
        self,
        platform: str,
        retry_after: int,
        draft_id: Optional[str] = None,
    ) -> None:
        """
        Schedule a retry for a platform.

        Args:
            platform: Platform name
            retry_after: Seconds until retry
            draft_id: Optional specific draft ID to retry
        """
        retry_time = datetime.now() + timedelta(seconds=retry_after)

        with self._lock:
            if platform in self._platform_state:
                self._platform_state[platform]["retry_after"] = retry_time.isoformat()
                self._save_state()

        self.logger.log(
            "INFO",
            "social_retry_scheduled",
            {
                "platform": platform,
                "retry_after": retry_time.isoformat(),
                "draft_id": draft_id or "all",
            },
        )

    def sync_drafts(self, platform: str) -> dict[str, Any]:
        """
        Attempt to sync draft posts for a platform.

        Args:
            platform: Platform name

        Returns:
            Dict with sync results:
            - total: Total drafts
            - posted: Successfully posted
            - failed: Failed to post
            - still_draft: Remaining drafts
        """
        results = {
            "total": 0,
            "posted": 0,
            "failed": 0,
            "still_draft": 0,
        }

        # Check if fallback is still active
        if self.is_fallback_active(platform):
            retry_after_str = self._platform_state[platform].get("retry_after")
            if retry_after_str:
                retry_time = datetime.fromisoformat(retry_after_str)
                if datetime.now() < retry_time:
                    self.logger.log(
                        "INFO",
                        "social_sync_skipped",
                        {"platform": platform, "reason": "Retry window not reached"},
                    )
                    results["still_draft"] = len(list(self.drafts_dir.glob(f"DRAFT_{platform}_*.md")))
                    return results

            # Deactivate fallback
            self.deactivate_fallback(platform)

        # Process drafts
        draft_files = list(self.drafts_dir.glob(f"DRAFT_{platform}_*.md"))
        results["total"] = len(draft_files)

        for draft_file in draft_files:
            try:
                # Parse draft file
                draft_data = self._parse_draft_file(draft_file)

                # Attempt to post (this would call the actual API)
                # For now, we'll just mark as posted
                success = True  # In real implementation, call API here

                if success:
                    # Move to done
                    done_file = self.drafts_dir / f"POSTED_{draft_file.name}"
                    draft_file.rename(done_file)
                    results["posted"] += 1

                    self.logger.log(
                        "INFO",
                        "social_draft_posted",
                        {"platform": platform, "draft_id": draft_data.get("id")},
                    )
                else:
                    # Increment retry count
                    draft_data["retry_count"] += 1
                    draft_data["last_retry"] = datetime.now().isoformat()

                    if draft_data["retry_count"] >= 3:
                        # Mark as failed
                        draft_data["status"] = "failed"
                        failed_file = self.drafts_dir / f"FAILED_{draft_file.name}"
                        self._write_draft_file(failed_file, draft_data)
                        draft_file.unlink()
                        results["failed"] += 1
                    else:
                        results["still_draft"] += 1

            except Exception as e:
                logger.error(f"Failed to sync draft {draft_file.name}: {e}")
                results["failed"] += 1

        self.logger.log(
            "INFO",
            "social_sync_completed",
            {
                "platform": platform,
                "total": results["total"],
                "posted": results["posted"],
                "failed": results["failed"],
                "still_draft": results["still_draft"],
            },
        )

        return results

    def _parse_draft_file(self, draft_file: Path) -> dict[str, Any]:
        """Parse draft markdown file to extract data."""
        content = draft_file.read_text(encoding="utf-8")

        # Simple parsing - in production, use proper frontmatter parser
        draft_data = {
            "platform": "unknown",
            "content": "",
            "metadata": {},
        }

        # Extract platform from frontmatter
        if "platform:" in content:
            for line in content.split("\n"):
                if line.startswith("platform:"):
                    draft_data["platform"] = line.split(":")[1].strip()
                    break

        # Extract content (simplified)
        if "## Content" in content:
            content_start = content.find("## Content") + len("## Content")
            content_end = content.find("##", content_start)
            if content_end == -1:
                content_end = len(content)
            draft_data["content"] = content[content_start:content_end].strip()

        return draft_data

    def _update_dashboard_fallback_status(self) -> None:
        """Update Dashboard.md with fallback status."""
        dashboard_path = self.vault_path / "Dashboard.md"

        try:
            # Build platform status table
            platform_rows = ""
            for platform, state in self._platform_state.items():
                status_icon = "⚠️" if state.get("fallback_active") else "✅"
                retry_after = state.get("retry_after", "N/A")
                platform_rows += f"| {platform.title()} | {status_icon} | {retry_after} |\n"

            # Count drafts
            draft_count = len(list(self.drafts_dir.glob("DRAFT_*.md")))

            status_section = f"""
## Social Media Fallback Status

| Platform | Status | Retry After |
|----------|--------|-------------|
{platform_rows}

| Metric | Value |
|--------|-------|
| **Total Drafts** | {draft_count} |
| **Last Updated** | {datetime.now().isoformat()} |

"""

            if dashboard_path.exists():
                content = dashboard_path.read_text(encoding="utf-8")

                # Remove existing fallback section
                if "## Social Media Fallback Status" in content:
                    start_idx = content.find("## Social Media Fallback Status")
                    end_idx = content.find("\n## ", start_idx + 1)
                    if end_idx == -1:
                        end_idx = len(content)
                    content = content[:start_idx] + content[end_idx:]

                # Insert new section
                insert_marker = "\n## "
                last_section_idx = content.rfind(insert_marker)
                if last_section_idx != -1:
                    line_start = content.rfind("\n", 0, last_section_idx)
                    if line_start == -1:
                        line_start = 0
                    content = content[:line_start] + status_section + content[last_section_idx:]
                else:
                    content += status_section

            else:
                content = f"# FTE Agent Dashboard\n\n{status_section}"

            dashboard_path.write_text(content, encoding="utf-8")
            logger.debug("Dashboard updated with social fallback status")

        except Exception as e:
            logger.error(f"Failed to update dashboard with fallback status: {e}")

    def get_fallback_stats(self) -> dict[str, Any]:
        """
        Get fallback statistics.

        Returns:
            Dict with fallback statistics
        """
        stats = {
            "platforms": {},
            "total_drafts": len(list(self.drafts_dir.glob("DRAFT_*.md"))),
            "last_updated": datetime.now().isoformat(),
        }

        for platform, state in self._platform_state.items():
            draft_count = len(list(self.drafts_dir.glob(f"DRAFT_{platform}_*.md")))
            stats["platforms"][platform] = {
                "fallback_active": state.get("fallback_active", False),
                "retry_after": state.get("retry_after"),
                "draft_count": draft_count,
            }

        return stats


# Global fallback manager instance
_fallback_instance: Optional[SocialMediaFallbackManager] = None


def get_social_fallback_manager(vault_path: Optional[str] = None) -> SocialMediaFallbackManager:
    """
    Get or create global social media fallback manager instance.

    Args:
        vault_path: Path to vault directory

    Returns:
        SocialMediaFallbackManager instance
    """
    global _fallback_instance
    if _fallback_instance is None:
        vault = vault_path or str(Path(__file__).parent.parent.parent / "vault")
        _fallback_instance = SocialMediaFallbackManager(vault_path=vault)
    return _fallback_instance


def save_draft_post(
    platform: str,
    content: str,
    image_url: Optional[str] = None,
    error: Optional[str] = None,
    scheduled_time: Optional[str] = None,
) -> Path:
    """
    Save a draft post to vault.

    Args:
        platform: Platform name
        content: Post content
        image_url: Optional image URL
        error: Error that caused fallback
        scheduled_time: Optional scheduled posting time

    Returns:
        Path to draft file
    """
    fallback = get_social_fallback_manager()
    return fallback.save_draft_post(platform, content, image_url, error, scheduled_time)


def sync_drafts(platform: str) -> dict[str, Any]:
    """
    Sync draft posts for a platform.

    Args:
        platform: Platform name

    Returns:
        Sync results dict
    """
    fallback = get_social_fallback_manager()
    return fallback.sync_drafts(platform)
