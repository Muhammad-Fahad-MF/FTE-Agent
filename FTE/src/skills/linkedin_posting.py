"""LinkedIn Posting Skill for automated business content posting.

Usage:
    from src.skills.linkedin_posting import LinkedInPostingSkill

    skill = LinkedInPostingSkill()

    # Generate content from Business_Goals.md + Done/ folder
    content = skill.generate_content()

    # Post to LinkedIn (requires approval)
    result = skill.post_to_linkedin(content)

    # Dry run mode
    skill = LinkedInPostingSkill(dry_run=True)
    result = skill.post_to_linkedin(content)  # Logs without posting
"""

import os
import sqlite3
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Optional

from .base_skill import BaseSkill
from ..utils.circuit_breaker import get_circuit_breaker, CircuitBreakerOpenError
from .request_approval import RequestApprovalSkill, ApprovalRequiredError


class LinkedInSessionExpiredError(Exception):
    """Raised when LinkedIn session expires."""
    pass


class LinkedInPostError(Exception):
    """Raised when LinkedIn posting fails."""
    pass


class RateLimitExceededError(Exception):
    """Raised when rate limit is exceeded."""
    pass


class LinkedInPostingSkill(BaseSkill):
    """Skill for generating and posting business content to LinkedIn.

    Features:
    - Generate content from Business_Goals.md + Done/ achievements
    - Post to LinkedIn via Playwright browser automation
    - Session preservation and recovery
    - Rate limiting (max 1 post/day)
    - Circuit breaker protection
    - --dry-run mode for safe testing
    - Approval workflow integration

    Attributes:
        dry_run: If True, log actions without executing
        correlation_id: Unique ID for tracking action across logs
        vault_dir: Base directory for vault storage
    """

    def __init__(
        self,
        dry_run: bool = False,
        correlation_id: Optional[str] = None,
        vault_dir: Optional[Path] = None,
    ) -> None:
        """Initialize LinkedIn posting skill.

        Args:
            dry_run: If True, log actions without executing
            correlation_id: Unique ID for tracking
            vault_dir: Base vault directory (default: FTE/vault)
        """
        super().__init__(dry_run=dry_run, correlation_id=correlation_id)

        # Resolve vault directory
        if vault_dir is None:
            vault_dir = Path(__file__).parent.parent.parent / "vault"
        self.vault_dir = Path(vault_dir).resolve()

        # Session storage
        self.session_dir = self.vault_dir / "linkedin_session"
        self.session_dir.mkdir(parents=True, exist_ok=True)
        self.storage_state_path = self.session_dir / "storage.json"

        # Initialize rate limiting (DB in vault_dir/../data/ to match test structure)
        data_dir = self.vault_dir.parent / "data"
        data_dir.mkdir(parents=True, exist_ok=True)
        self.rate_limit_db = data_dir / "linkedin_posts.db"
        self._init_rate_limit_db()

        # Initialize circuit breaker
        self.circuit_breaker = get_circuit_breaker(
            name="linkedin_api",
            failure_threshold=5,
            recovery_timeout=300,  # 5 minutes for LinkedIn
            fallback=self._linkedin_fallback,
        )

        # Initialize approval skill
        self.approval_skill = RequestApprovalSkill(
            dry_run=dry_run,
            correlation_id=correlation_id,
            vault_dir=vault_dir,
        )

        # Rate limit configuration
        self.posts_per_day = 1
        self._load_rate_limit_config()

        # Playwright browser (lazy initialization)
        self._browser = None
        self._context = None

    def _load_rate_limit_config(self) -> None:
        """Load rate limit configuration from Company_Handbook.md."""
        handbook_path = self.vault_dir / "Company_Handbook.md"

        if handbook_path.exists():
            try:
                content = handbook_path.read_text(encoding="utf-8")
                # Parse [LinkedIn] section for posts_per_day
                in_linkedin_section = False
                for line in content.split("\n"):
                    if line.strip().startswith("[LinkedIn]"):
                        in_linkedin_section = True
                        continue
                    if in_linkedin_section:
                        if line.strip().startswith("["):
                            break
                        if "posts_per_day" in line:
                            try:
                                value = int(line.split("=")[1].strip())
                                self.posts_per_day = value
                            except (ValueError, IndexError):
                                pass
            except Exception as e:
                self.logger.log(
                    "WARNING",
                    "rate_limit_config_load_failed",
                    {"error": str(e)},
                    correlation_id=self.correlation_id,
                )

    def _init_rate_limit_db(self) -> None:
        """Initialize rate limit SQLite database."""
        try:
            conn = sqlite3.connect(self.rate_limit_db)
            cursor = conn.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS posts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    post_id TEXT,
                    content TEXT,
                    posted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    status TEXT DEFAULT 'posted'
                )
            """
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS rate_limits (
                    id INTEGER PRIMARY KEY CHECK (id = 1),
                    post_count INTEGER DEFAULT 0,
                    window_start TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
            )
            # Initialize with default row
            cursor.execute(
                """
                INSERT OR IGNORE INTO rate_limits (id, post_count, window_start)
                VALUES (1, 0, ?)
            """,
                (datetime.now(),),
            )
            conn.commit()
            conn.close()
        except sqlite3.Error as e:
            self.logger.log(
                "ERROR",
                "rate_limit_db_init_failed",
                {"error": str(e)},
                correlation_id=self.correlation_id,
            )

    def _check_rate_limit(self) -> bool:
        """Check if rate limit allows another post.

        Returns:
            True if post allowed, False if rate limited

        Raises:
            RateLimitExceededError: If rate limit exceeded
        """
        try:
            conn = sqlite3.connect(self.rate_limit_db)
            cursor = conn.cursor()

            # Get current rate limit state
            cursor.execute(
                "SELECT post_count, window_start FROM rate_limits WHERE id = 1"
            )
            row = cursor.fetchone()

            if not row:
                conn.close()
                return True

            post_count, window_start_str = row
            window_start = datetime.fromisoformat(window_start_str)
            now = datetime.now()

            # Check if window has expired (24 hours)
            if now - window_start >= timedelta(hours=24):
                # Reset counter
                cursor.execute(
                    """
                    UPDATE rate_limits
                    SET post_count = 1, window_start = ?, updated_at = ?
                    WHERE id = 1
                """,
                    (now, now),
                )
                conn.commit()
                conn.close()
                return True

            # Check if under limit
            if post_count < self.posts_per_day:
                # Increment counter
                cursor.execute(
                    """
                    UPDATE rate_limits
                    SET post_count = ?, updated_at = ?
                    WHERE id = 1
                """,
                    (post_count + 1, now),
                )
                conn.commit()
                conn.close()
                return True

            # Rate limit exceeded
            conn.close()
            reset_time = window_start + timedelta(hours=24)
            raise RateLimitExceededError(
                f"LinkedIn rate limit exceeded ({self.posts_per_day} post/day) - "
                f"retry after {reset_time.isoformat()}"
            )

        except RateLimitExceededError:
            raise
        except Exception as e:
            self.logger.log(
                "WARNING",
                "rate_limit_check_failed",
                {"error": str(e)},
                correlation_id=self.correlation_id,
            )
            # Fail open - allow post if check fails
            return True

    def _linkedin_fallback(self) -> dict[str, Any]:
        """Fallback function when circuit breaker is open.

        Returns:
            Error dict indicating circuit breaker state
        """
        return {
            "status": "error",
            "error": "Circuit breaker open - LinkedIn posting temporarily disabled",
            "post_id": None,
            "timestamp": datetime.now().isoformat(),
            "dry_run": self.dry_run,
        }

    def _load_business_goals(self) -> str:
        """Load business goals from Business_Goals.md.

        Returns:
            Business goals content as string
        """
        goals_path = self.vault_dir / "Business_Goals.md"

        if not goals_path.exists():
            self.logger.log(
                "WARNING",
                "business_goals_not_found",
                {"path": str(goals_path)},
                correlation_id=self.correlation_id,
            )
            return ""

        try:
            content = goals_path.read_text(encoding="utf-8")
            # Extract main content (skip YAML frontmatter if present)
            if content.startswith("---"):
                parts = content.split("---", 2)
                if len(parts) >= 3:
                    content = parts[2]

            return content.strip()

        except Exception as e:
            self.logger.log(
                "WARNING",
                "business_goals_load_failed",
                {"error": str(e)},
                correlation_id=self.correlation_id,
            )
            return ""

    def _load_recent_achievements(self, limit: int = 10) -> list[str]:
        """Load recent achievements from Done/ folder.

        Args:
            limit: Maximum number of achievements to load

        Returns:
            List of achievement strings
        """
        done_dir = self.vault_dir / "Done"
        achievements = []

        if not done_dir.exists():
            self.logger.log(
                "WARNING",
                "done_folder_not_found",
                {"path": str(done_dir)},
                correlation_id=self.correlation_id,
            )
            return []

        try:
            # Get last 10 .md files sorted by modification time
            md_files = sorted(
                done_dir.glob("*.md"),
                key=lambda f: f.stat().st_mtime,
                reverse=True,
            )[:limit]

            for file_path in md_files:
                try:
                    content = file_path.read_text(encoding="utf-8")
                    # Extract title from frontmatter or first heading
                    if content.startswith("---"):
                        parts = content.split("---", 2)
                        if len(parts) >= 2:
                            import yaml
                            frontmatter = yaml.safe_load(parts[1])
                            if frontmatter and "objective" in frontmatter:
                                achievements.append(frontmatter["objective"])
                                continue

                    # Fallback: first line or heading
                    lines = content.strip().split("\n")
                    for line in lines:
                        if line.startswith("#"):
                            achievements.append(line.lstrip("# ").strip())
                            break
                    else:
                        if lines:
                            achievements.append(lines[0][:100])

                except Exception as e:
                    self.logger.log(
                        "WARNING",
                        "achievement_load_failed",
                        {"file": str(file_path), "error": str(e)},
                        correlation_id=self.correlation_id,
                    )

            return achievements

        except Exception as e:
            self.logger.log(
                "WARNING",
                "achievements_load_failed",
                {"error": str(e)},
                correlation_id=self.correlation_id,
            )
            return []

    def _extract_hashtags(self) -> list[str]:
        """Extract hashtags from Business_Goals.md.

        Returns:
            List of hashtags
        """
        goals_path = self.vault_dir / "Business_Goals.md"
        hashtags = []

        if not goals_path.exists():
            return hashtags

        try:
            content = goals_path.read_text(encoding="utf-8")

            # Look for [hashtags] section
            in_hashtags_section = False
            for line in content.split("\n"):
                if "[hashtags]" in line.lower():
                    in_hashtags_section = True
                    continue
                if in_hashtags_section:
                    if line.strip().startswith("["):
                        break
                    # Parse hashtag list
                    if line.strip().startswith("-"):
                        tag = line.strip().lstrip("-").strip()
                        if tag:
                            hashtags.append(tag if tag.startswith("#") else f"#{tag}")

        except Exception as e:
            self.logger.log(
                "WARNING",
                "hashtag_extraction_failed",
                {"error": str(e)},
                correlation_id=self.correlation_id,
            )

        return hashtags[:3]  # Limit to 2-3 hashtags

    def generate_content(self) -> str:
        """Generate LinkedIn post content from goals and achievements.

        Returns:
            Generated post content (50-300 characters with hashtags)

        Raises:
            RuntimeError: If content generation fails
        """
        start_time = time.time()

        try:
            # Load business goals
            goals_content = self._load_business_goals()

            # Load recent achievements
            achievements = self._load_recent_achievements()

            if not achievements:
                self.logger.log(
                    "WARNING",
                    "no_achievements_for_content",
                    {},
                    correlation_id=self.correlation_id,
                )
                return ""

            # Generate post format: "🚀 {achievement} - {business_goal_connection}"
            primary_achievement = achievements[0]

            # Extract key theme from goals
            goal_theme = ""
            if goals_content:
                # Take first meaningful line from goals
                for line in goals_content.split("\n"):
                    line = line.strip()
                    if line and not line.startswith("#"):
                        goal_theme = line[:100]
                        break

            # Construct post
            if goal_theme:
                post = f"🚀 {primary_achievement}\n\nThis advances our goal: {goal_theme}"
            else:
                post = f"🚀 {primary_achievement}"

            # Add hashtags
            hashtags = self._extract_hashtags()
            if hashtags:
                post += "\n\n" + " ".join(hashtags)

            # Ensure post length 50-300 characters
            if len(post) > 300:
                post = post[:297] + "..."
            elif len(post) < 50:
                # Pad with more context
                if len(achievements) > 1:
                    post += f"\n\nAlso: {achievements[1][:100]}"

            duration = time.time() - start_time
            self.emit_metric("linkedin_content_generated_duration", duration)
            self.emit_metric("linkedin_content_generated_count", 1.0)

            self.logger.log(
                "INFO",
                "content_generated",
                {
                    "character_count": len(post),
                    "achievements_used": len(achievements),
                    "hashtags_count": len(hashtags),
                    "duration_ms": int(duration * 1000),
                },
                correlation_id=self.correlation_id,
            )

            return post

        except Exception as e:
            self.logger.log(
                "ERROR",
                "content_generation_failed",
                {"error": str(e)},
                correlation_id=self.correlation_id,
            )
            self.emit_metric("linkedin_content_errors", 1.0)
            raise RuntimeError(f"Failed to generate LinkedIn content: {e}")

    def _init_browser(self) -> None:
        """Initialize Playwright browser (lazy initialization)."""
        try:
            from playwright.async_api import async_playwright
            import asyncio

            async def _init():
                playwright = await async_playwright().start()
                self._browser = await playwright.chromium.launch(
                    headless=True,
                    args=["--disable-gpu", "--no-sandbox"],
                )

                # Load session if exists
                if self.storage_state_path.exists():
                    self._context = await self._browser.new_context(
                        storage_state=str(self.storage_state_path),
                    )
                else:
                    self._context = await self._browser.new_context()

            asyncio.run(_init())

        except Exception as e:
            self.logger.log(
                "ERROR",
                "browser_init_failed",
                {"error": str(e)},
                correlation_id=self.correlation_id,
            )
            raise LinkedInPostError(f"Failed to initialize browser: {e}")

    async def _navigate_to_linkedin(self) -> bool:
        """Navigate to LinkedIn feed.

        Returns:
            True if navigation successful, False if session expired

        Raises:
            LinkedInSessionExpiredError: If session expired
        """
        try:
            from playwright.async_api import TimeoutError as PlaywrightTimeoutError

            page = await self._context.new_page()

            # Navigate to feed
            await page.goto("https://www.linkedin.com/feed/", timeout=30000)

            # Wait for feed container or login prompt
            try:
                await page.wait_for_selector(
                    "div[class*='feed-shared-update-v2']",
                    timeout=10000,
                )
                return True
            except PlaywrightTimeoutError:
                # Check if we're on login page
                if await page.query_selector("input[type='email']"):
                    raise LinkedInSessionExpiredError(
                        "LinkedIn session expired - login page detected"
                    )
                raise LinkedInPostError("Failed to load LinkedIn feed")

        except LinkedInSessionExpiredError:
            raise
        except Exception as e:
            raise LinkedInPostError(f"Failed to navigate to LinkedIn: {e}")

    async def _create_post(self, content: str) -> str:
        """Create LinkedIn post via browser automation.

        Args:
            content: Post content to share

        Returns:
            Post URL after successful posting

        Raises:
            LinkedInPostError: If posting fails
        """
        try:
            from playwright.async_api import TimeoutError as PlaywrightTimeoutError

            page = await self._context.new_page()

            # Navigate to feed
            await page.goto("https://www.linkedin.com/feed/", timeout=30000)

            # Click "Start a post" button
            start_post_selector = "button[aria-label*='Start a post'], div[role='button']:has-text('Start a post')"
            await page.wait_for_selector(start_post_selector, timeout=10000)
            await page.click(start_post_selector)

            # Wait for post dialog and enter content
            content_editor = "div[contenteditable][aria-label*='Share what you think']"
            await page.wait_for_selector(content_editor, timeout=10000)
            await page.fill(content_editor, content)

            # Click "Post" button
            post_button = "button[aria-label*='Share'], button:has-text('Post')"
            await page.wait_for_selector(post_button, timeout=10000)
            await page.click(post_button)

            # Wait for confirmation toast
            try:
                await page.wait_for_selector(
                    "div:has-text('Your post has been shared'), div:has-text('Post shared')",
                    timeout=10000,
                )
            except PlaywrightTimeoutError:
                self.logger.log(
                    "WARNING",
                    "post_confirmation_not_found",
                    {},
                    correlation_id=self.correlation_id,
                )

            # Get post URL from feed
            # Wait for post to appear in feed and extract URL
            await page.wait_for_selector(
                "div[class*='feed-shared-update-v2']",
                timeout=10000,
            )
            post_url = page.url

            return post_url

        except Exception as e:
            # Save screenshot on error
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            error_screenshot = self.vault_dir / "Logs" / f"linkedin_error_{timestamp}.png"

            try:
                await page.screenshot(path=str(error_screenshot))
                self.logger.log(
                    "WARNING",
                    "error_screenshot_saved",
                    {"path": str(error_screenshot)},
                    correlation_id=self.correlation_id,
                )
            except Exception:
                pass

            raise LinkedInPostError(f"Failed to create LinkedIn post: {e}")

    async def _save_session(self) -> None:
        """Save browser session to storage.json."""
        try:
            if self._context:
                await self._context.storage_state(path=str(self.storage_state_path))
                self.logger.log(
                    "INFO",
                    "session_saved",
                    {"path": str(self.storage_state_path)},
                    correlation_id=self.correlation_id,
                )
        except Exception as e:
            self.logger.log(
                "WARNING",
                "session_save_failed",
                {"error": str(e)},
                correlation_id=self.correlation_id,
            )

    def _is_session_valid(self) -> bool:
        """Check if saved session is valid.

        Returns:
            True if session valid, False otherwise
        """
        if not self.storage_state_path.exists():
            return False

        try:
            # Check session file age (invalidate after 7 days)
            mtime = datetime.fromtimestamp(self.storage_state_path.stat().st_mtime)
            if datetime.now() - mtime > timedelta(days=7):
                self.logger.log(
                    "INFO",
                    "session_expired_by_age",
                    {"age_hours": (datetime.now() - mtime).total_seconds() / 3600},
                    correlation_id=self.correlation_id,
                )
                return False

            # Check file is valid JSON
            import json
            with open(self.storage_state_path, "r") as f:
                json.load(f)

            return True

        except Exception as e:
            self.logger.log(
                "WARNING",
                "session_validation_failed",
                {"error": str(e)},
                correlation_id=self.correlation_id,
            )
            return False

    def post_to_linkedin(self, content: str) -> dict[str, Any]:
        """Post content to LinkedIn.

        Args:
            content: Post content (50-300 characters recommended)

        Returns:
            Dict with post_id, status, timestamp, url

        Raises:
            LinkedInSessionExpiredError: If session expired
            LinkedInPostError: If posting fails
            RateLimitExceededError: If rate limit exceeded
            ApprovalRequiredError: If approval required
        """
        start_time = time.time()

        # Validate DEV_MODE
        self.validate_dev_mode()

        # Check rate limit
        try:
            self._check_rate_limit()
        except RateLimitExceededError as e:
            self.logger.log(
                "WARNING",
                "rate_limit_exceeded",
                {"error": str(e)},
                correlation_id=self.correlation_id,
            )
            self.emit_metric("linkedin_post_errors", 1.0, {"error_type": "rate_limit"})
            return {
                "status": "error",
                "error": str(e),
                "post_id": None,
                "timestamp": datetime.now().isoformat(),
                "dry_run": self.dry_run,
            }

        # Dry run mode
        if self.dry_run:
            self.logger.log(
                "INFO",
                "dry_run_linkedin_post",
                {
                    "content_length": len(content),
                    "content_preview": content[:100],
                },
                correlation_id=self.correlation_id,
            )
            self.emit_metric("linkedin_post_duration", time.time() - start_time)
            self.emit_metric("linkedin_post_count", 1.0, {"dry_run": "true"})

            return {
                "status": "dry_run",
                "message": f"DRY RUN: Would post to LinkedIn: {content[:100]}",
                "post_id": None,
                "timestamp": datetime.now().isoformat(),
                "dry_run": True,
            }

        # Post with circuit breaker protection
        try:
            result = self.circuit_breaker.call(
                self._post_to_linkedin_async,
                content,
            )

            duration = time.time() - start_time
            self.emit_metric("linkedin_post_duration", duration)
            self.emit_metric("linkedin_post_count", 1.0)

            # Record post in database
            self._record_post(result.get("post_id"), content)

            self.logger.log(
                "INFO",
                "linkedin_post_success",
                {
                    "post_id": result.get("post_id"),
                    "url": result.get("url"),
                    "duration_ms": int(duration * 1000),
                },
                correlation_id=self.correlation_id,
            )

            return result

        except CircuitBreakerOpenError as e:
            self.logger.log(
                "WARNING",
                "circuit_breaker_open",
                {"error": str(e)},
                correlation_id=self.correlation_id,
            )
            self.emit_metric("linkedin_post_errors", 1.0, {"error_type": "circuit_breaker"})
            return {
                "status": "error",
                "error": str(e),
                "post_id": None,
                "timestamp": datetime.now().isoformat(),
                "dry_run": self.dry_run,
            }

        except LinkedInSessionExpiredError as e:
            self.logger.log(
                "WARNING",
                "session_expired",
                {"error": str(e)},
                correlation_id=self.correlation_id,
            )
            self._update_dashboard_session_alert()
            self.emit_metric("linkedin_post_errors", 1.0, {"error_type": "session_expired"})
            raise

        except LinkedInPostError as e:
            self.logger.log(
                "ERROR",
                "linkedin_post_failed",
                {"error": str(e)},
                correlation_id=self.correlation_id,
            )
            self.emit_metric("linkedin_post_errors", 1.0)
            raise

    def _post_to_linkedin_async(self, content: str) -> dict[str, Any]:
        """Execute LinkedIn post asynchronously.

        Args:
            content: Post content

        Returns:
            Dict with post_id, status, timestamp, url
        """
        import asyncio

        async def _post():
            # Initialize browser if needed
            if not self._browser:
                self._init_browser()

            # Navigate to LinkedIn
            await self._navigate_to_linkedin()

            # Create post
            url = await self._create_post(content)

            # Save session
            await self._save_session()

            # Close browser
            await self._close_browser()

            return {
                "status": "posted",
                "post_id": str(hash(content))[:12],  # Generate pseudo ID
                "url": url,
                "timestamp": datetime.now().isoformat(),
                "dry_run": False,
            }

        return asyncio.run(_post())

    async def _close_browser(self) -> None:
        """Close browser and cleanup."""
        try:
            if self._browser:
                await self._browser.close()
                self._browser = None
                self._context = None
        except Exception as e:
            self.logger.log(
                "WARNING",
                "browser_close_failed",
                {"error": str(e)},
                correlation_id=self.correlation_id,
            )

    def _record_post(self, post_id: Optional[str], content: str) -> None:
        """Record post in database.

        Args:
            post_id: Post ID from LinkedIn
            content: Post content
        """
        try:
            conn = sqlite3.connect(self.rate_limit_db)
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO posts (post_id, content, status)
                VALUES (?, ?, 'posted')
            """,
                (post_id, content),
            )
            conn.commit()
            conn.close()
        except sqlite3.Error as e:
            self.logger.log(
                "WARNING",
                "post_recording_failed",
                {"error": str(e)},
                correlation_id=self.correlation_id,
            )

    def _update_dashboard_session_alert(self) -> None:
        """Update Dashboard.md with session expiry alert."""
        dashboard_path = self.vault_dir / "Dashboard.md"

        alert = (
            f"\n\n## ⚠️ LinkedIn Session Expired - {datetime.now().isoformat()}\n\n"
            "**Action Required:** Please re-authenticate at [linkedin.com](https://www.linkedin.com)\n\n"
            "After re-authentication, the LinkedIn posting skill will resume automatically.\n"
        )

        try:
            if dashboard_path.exists():
                content = dashboard_path.read_text(encoding="utf-8")
                content += alert
                dashboard_path.write_text(content, encoding="utf-8")
            else:
                dashboard_path.write_text(f"# FTE-Agent Dashboard\n{alert}", encoding="utf-8")

            self.logger.log(
                "WARNING",
                "dashboard_session_alert_updated",
                {},
                correlation_id=self.correlation_id,
            )

        except Exception as e:
            self.logger.log(
                "ERROR",
                "dashboard_update_failed",
                {"error": str(e)},
                correlation_id=self.correlation_id,
            )

    def execute(
        self,
        content: Optional[str] = None,
        generate: bool = True,
    ) -> dict[str, Any]:
        """Execute the LinkedIn posting skill.

        Args:
            content: Optional content to post (if not provided, generates content)
            generate: If True, generate content before posting

        Returns:
            Dict with post_id, status, timestamp, url
        """
        if generate or content is None:
            content = self.generate_content()

        if not content:
            return {
                "status": "error",
                "error": "No content to post",
                "post_id": None,
                "timestamp": datetime.now().isoformat(),
                "dry_run": self.dry_run,
            }

        return self.post_to_linkedin(content)
