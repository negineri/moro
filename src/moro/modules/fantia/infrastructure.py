"""Infrastructure for Fantia client."""

import json
from dataclasses import dataclass
from datetime import datetime as dt
from logging import getLogger
from os import makedirs, path
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import httpx
from selenium import webdriver

from moro.modules.common import CommonConfig
from moro.modules.fantia import FantiaClient
from moro.modules.fantia.config import DOMAIN, LOGIN_SIGNIN_URL, ME_API, FantiaConfig
from moro.modules.fantia.domain import (
    SessionIdProvider,
)

logger = getLogger(__name__)


class SeleniumSessionIdProvider(SessionIdProvider):
    """Selenium-based SessionId provider that uses Chrome WebDriver to login to Fantia."""

    def __init__(self, config: CommonConfig, fantia_config: FantiaConfig) -> None:
        """Initialize the Selenium session ID provider.

        Args:
            config: CommonConfig instance for configuration.
            fantia_config: FantiaConfig instance for cookie caching options.
        """
        self._chrome_user_data = path.join(config.user_cache_dir, fantia_config.chrome_data_dir)
        self._enable_cookie_cache = fantia_config.enable_cookie_cache
        self._cookie_cache_file = path.join(config.user_cache_dir, fantia_config.cookie_cache_file)

    def _load_cached_cookies(self) -> dict[str, str]:
        """Load cached cookies from file.

        Returns:
            Dictionary of cached cookies, empty dict if not found or invalid.
        """
        if not self._enable_cookie_cache:
            return {}

        try:
            cache_file = Path(self._cookie_cache_file)
            if not cache_file.exists():
                return {}

            with cache_file.open("r", encoding="utf-8") as f:
                data = json.load(f)

            # Validate the structure
            if isinstance(data, dict) and "cookies" in data and "timestamp" in data:
                return data["cookies"]  # type: ignore
        except Exception as e:
            logger.warning(f"Failed to load cached cookies: {e}")

        return {}

    def _save_cookies_to_cache(self, cookies: dict[str, str]) -> None:
        """Save cookies to cache file.

        Args:
            cookies: Dictionary of cookies to save.
        """
        if not self._enable_cookie_cache or not cookies:
            return

        try:
            cache_file = Path(self._cookie_cache_file)
            cache_file.parent.mkdir(parents=True, exist_ok=True)

            data: dict[str, Any] = {
                "cookies": cookies,
                "timestamp": dt.now().isoformat(),
            }

            with cache_file.open("w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)

            # Set file permissions to user read/write only for security
            cache_file.chmod(0o600)

            logger.info(f"Saved {len(cookies)} cookies to cache: {cache_file}")
        except Exception as e:
            logger.warning(f"Failed to save cookies to cache: {e}")

    def _is_session_valid(self, cookies: dict[str, str]) -> bool:
        """Check if cached session is still valid.

        Args:
            cookies: Dictionary of cookies to validate.

        Returns:
            True if session is valid, False otherwise.
        """
        if not cookies.get("_session_id"):
            return False

        try:
            # Create a temporary httpx client to test the session
            test_cookies = dict(cookies.items())

            with httpx.Client(cookies=test_cookies) as client:
                response = client.get(ME_API, timeout=10.0)
                return response.is_success or response.status_code == 304

        except Exception as e:
            logger.debug(f"Session validation failed: {e}")
            return False

    def get_cookies(self) -> dict[str, str]:
        """Get all Fantia-related cookies with caching support.

        First attempts to load cached cookies and validate them.
        If cached cookies are invalid or not found, performs Selenium-based login.

        Returns:
            Dictionary containing available cookies. May include:
            - _session_id: Main session identifier
            - jp_chatplus_vtoken: Chat plus token
            - _f_v_k_1: Fantia verification key
        """
        # Try to load cached cookies first
        cached_cookies = self._load_cached_cookies()
        if cached_cookies and self._is_session_valid(cached_cookies):
            logger.info(f"Using cached cookies: {list(cached_cookies.keys())}")
            return cached_cookies

        # Cached cookies not valid, perform fresh login
        logger.info("Cached cookies invalid or not found, performing fresh login")
        result = self._perform_selenium_login()

        # Save new cookies to cache
        if result:
            self._save_cookies_to_cache(result)

        return result

    def _perform_selenium_login(self) -> dict[str, str]:
        """Perform Selenium-based login to obtain fresh cookies.

        Returns:
            Dictionary containing fresh cookies from Selenium login.
        """
        target_cookies = ["_session_id", "jp_chatplus_vtoken", "_f_v_k_1"]
        result: dict[str, str] = {}

        try:
            options = self._create_chrome_options()

            with webdriver.Chrome(options=options) as driver:
                driver.get(LOGIN_SIGNIN_URL)

                # Wait for user to complete login manually
                while True:
                    parsed_url = urlparse(driver.current_url)
                    if parsed_url.path == "/" and parsed_url.netloc == DOMAIN:
                        # Successfully logged in, extract target cookies
                        cookies: list[dict[str, str]] = driver.get_cookies()  # pyright: ignore[reportUnknownVariableType, reportUnknownMemberType]

                        for cookie in cookies:
                            if cookie["name"] in target_cookies:
                                result[cookie["name"]] = str(cookie["value"])

                        if result:
                            cookie_names = list(result.keys())
                            count = len(result)
                            logger.info(f"Obtained {count} cookies via Selenium: {cookie_names}")
                        else:
                            logger.warning("Login successful but no target cookies found")
                        break

        except Exception as e:
            logger.error(f"Error during Selenium login: {e}")

        return result

    def _create_chrome_options(self) -> webdriver.ChromeOptions:
        """Create Chrome options for the WebDriver.

        Returns:
            Configured ChromeOptions instance.
        """
        options = webdriver.ChromeOptions()

        if self._chrome_user_data:
            makedirs(self._chrome_user_data, exist_ok=True)
            options.add_argument(f"--user-data-dir={self._chrome_user_data}")

        return options


# ===== Repository Implementations =====


@dataclass
class FantiaPostRepositoryImpl:
    """Repository implementation for Fantia posts."""

    _client: FantiaClient

    def get(self, post_id: str) -> Any:
        """Get a single post by ID.

        Args:
            post_id: The ID of the post to retrieve

        Returns:
            FantiaPostData if found, None otherwise
        """
        if not post_id or not post_id.strip():
            return None

        try:
            from moro.modules.fantia import parse_post

            return parse_post(self._client, post_id)
        except Exception:
            return None

    def get_many(self, post_ids: list[str]) -> list[Any]:
        """Get multiple posts by IDs.

        Args:
            post_ids: List of post IDs to retrieve

        Returns:
            List of FantiaPostData for found posts (excludes not found)
        """
        if not post_ids:
            return []

        results: list[Any] = []
        for post_id in post_ids:
            post = self.get(post_id)
            if post is not None:
                results.append(post)
        return results


@dataclass
class FantiaCreatorRepositoryImpl:
    """Repository implementation for Fantia creators."""

    _client: FantiaClient

    def get(self, creator_id: str) -> Any:
        """Get a creator by ID.

        Args:
            creator_id: The ID of the creator to retrieve

        Returns:
            FantiaCreator if found, None otherwise
        """
        if not creator_id or not creator_id.strip():
            return None

        try:
            from moro.modules.fantia import get_posts_by_user
            from moro.modules.fantia.domain import FantiaCreator

            # 投稿一覧を取得
            posts = get_posts_by_user(self._client, creator_id)

            # FantiaCreator エンティティを作成
            # NOTE: 現在は creator_id をそのまま name として使用（後で改善）
            return FantiaCreator(
                id=creator_id,
                name=f"Creator {creator_id}",  # プレースホルダー
                posts=posts,
            )
        except Exception:
            return None
