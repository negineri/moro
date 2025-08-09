"""Infrastructure for Fantia client."""

import json
import os
import time
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import datetime as dt
from logging import getLogger
from os import makedirs, path
from pathlib import Path
from time import sleep
from typing import Any
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup
from injector import inject
from pathvalidate import sanitize_filename
from selenium import webdriver

from moro.modules.common import CommonConfig
from moro.modules.fantia import FantiaClient
from moro.modules.fantia.config import (
    DOMAIN,
    FANCLUB_POSTS_HTML,
    LOGIN_SIGNIN_URL,
    ME_API,
    FantiaConfig,
)
from moro.modules.fantia.domain import (
    FantiaFanclubRepository,
    FantiaFile,
    FantiaPhotoGallery,
    FantiaPostData,
    FantiaPostRepository,
    FantiaProduct,
    FantiaText,
    SessionIdProvider,
)

logger = getLogger(__name__)


@inject
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


def get_posts_by_user(client: FantiaClient, user_id: str, interval: float = 0) -> list[str]:
    """Get all post ids by a user."""
    logger.info(f"Fetching posts for user {user_id}...")

    posts: list[str] = []
    page = 1
    while True:
        logger.info(f"Fetching page {page}...")
        response = client.get(FANCLUB_POSTS_HTML.format(user_id, page))
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        post_elements = soup.select("div.post")
        if not post_elements:
            break

        for post_element in post_elements:
            post_title_ele = post_element.select_one(".post-title")
            if post_title_ele is None:
                logger.warning("Post title not found. Skipping post.")
                logger.debug(f"Post element: {post_element}")
                continue
            post_title = post_title_ele.string
            if post_title is None:
                logger.warning("Post title is None. Skipping post.")
                continue

            post_href_ele = post_element.select_one("a.link-block")
            if post_href_ele is None:
                logger.warning("Post link not found. Skipping post.")
                continue
            post_href = post_href_ele.get("href")
            if post_href is None:
                logger.warning("Post link is None. Skipping post.")
                continue

            post_id = Path(str(post_href)).name
            posts.append(post_id)

        page += 1
        time.sleep(interval)

    return posts


# ===== Repository Implementations =====


@inject
@dataclass
class FantiaPostRepositoryImpl(FantiaPostRepository):
    """Repository implementation for Fantia posts."""

    _client: FantiaClient
    _fantia_config: FantiaConfig

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

    def get_many(self, post_ids: list[str]) -> Iterator[FantiaPostData]:
        """Get multiple posts by IDs.

        Args:
            post_ids: List of post IDs to retrieve

        Returns:
            Iterator of FantiaPostData for found posts (excludes not found)
        """
        if not post_ids:
            return

        for post_id in post_ids:
            post = self.get(post_id)
            if post is not None:
                yield post
            sleep(self._fantia_config.interval_sec)


@inject
@dataclass
class FantiaFanclubRepositoryImpl(FantiaFanclubRepository):
    """Repository implementation for Fantia fanclubs."""

    _client: FantiaClient

    def get(self, fanclub_id: str) -> Any:
        """Get a fanclub by ID.

        Args:
            fanclub_id: The ID of the fanclub to retrieve

        Returns:
            FantiaFanclub if found, None otherwise
        """
        if not fanclub_id or not fanclub_id.strip():
            return None

        try:
            from moro.modules.fantia.domain import FantiaFanclub

            # 投稿一覧を取得
            posts = get_posts_by_user(self._client, fanclub_id)

            # FantiaFanclub エンティティを作成
            return FantiaFanclub(
                id=fanclub_id,
                posts=posts,
            )
        except Exception:
            return None


@inject
@dataclass
class FantiaFileDownloader:
    """Domain service for downloading Fantia post content."""

    _client: FantiaClient

    def download_all_content(self, post_data: FantiaPostData, post_directory: str) -> bool:
        """Download all content for a post to the specified directory.

        Args:
            post_data: The post data containing URLs to download
            post_directory: The directory to save downloaded content

        Returns:
            True if all downloads succeeded, False otherwise
        """
        try:
            # サムネイルのダウンロード
            self.download_thumbnail(post_directory, post_data)
            # コメントの保存
            if post_data.comment:
                self.save_post_comment(post_directory, post_data.comment)
            # コンテンツメタデータの保存
            self.save_post_contents_meta(post_directory, post_data.contents)

            # 写真ギャラリーのダウンロード
            for gallery in post_data.contents_photo_gallery:
                gallery_dir = self._create_content_directory(
                    post_directory, gallery.id, gallery.title
                )
                self.download_photo_gallery(gallery_dir, gallery)
            # ファイルのダウンロード
            for file_data in post_data.contents_files:
                content_dir = self._create_content_directory(
                    post_directory, file_data.id, file_data.title
                )
                self.download_file(content_dir, file_data)

            # テキストコンテンツの保存
            for text_content in post_data.contents_text:
                self.save_text_content(post_directory, text_content)

            # 商品コンテンツの保存
            for product_content in post_data.contents_products:
                self.save_product_content(post_directory, product_content)

            logger.info(f"All content downloaded successfully for post {post_data.id}")

            return True

        except Exception as e:
            logger.error(f"Error during content download: {e}")
            return False

    def save_post_contents_meta(self, post_dir: str, contents: list[Any]) -> None:
        """Save post contents metadata to file."""
        meta_path = os.path.join(post_dir, "contents.json")
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(contents, f, ensure_ascii=False, indent=4)

    def save_post_comment(self, post_dir: str, comment: str) -> None:
        """
        Save post comment to file.

        Args:
            post_dir: Post directory path.
            comment: Comment text to save.
        """
        comment_path = os.path.join(post_dir, "comment.txt")
        with open(comment_path, "w", encoding="utf-8") as f:
            f.write(comment)

    def download_thumbnail(self, post_path: str, post_content: FantiaPostData) -> None:
        """Download the thumbnail of a post to the specified directory."""
        if post_content.thumbnail is not None:
            thumb_url = post_content.thumbnail.url
            ext = post_content.thumbnail.ext
            file_path = os.path.join(post_path, "0000_thumb" + ext)
            self._perform_download(thumb_url, file_path)
        else:
            logger.info("No thumbnail found for this post. Skipping...\n")

    def download_file(self, post_path: str, post_content: FantiaFile) -> None:
        """Download a file to the specified directory."""
        if post_content.comment is not None:
            file_path = os.path.join(post_path, "comment.txt")
            with open(file_path, mode="w") as f:
                f.write(post_content.comment)

        download_url = post_content.url
        file_name = post_content.name
        file_path = os.path.join(post_path, file_name)
        self._perform_download(download_url, file_path)

    def download_photo_gallery(self, post_path: str, post_content: FantiaPhotoGallery) -> None:
        """Download a photo gallery to the specified directory."""
        if post_content.comment is not None:
            file_path = os.path.join(post_path, "comment.txt")
            with open(file_path, mode="w") as f:
                f.write(post_content.comment)
        for index, photo in enumerate(post_content.photos):
            self._perform_download(photo.url, os.path.join(post_path, f"{index:03d}{photo.ext}"))

    def save_text_content(self, post_dir: str, text_content: FantiaText) -> None:
        """Save text content to file."""
        if not text_content.comment:
            logger.warning(f"Text content {text_content.id} has no comment.")
            return

        content_dir = self._create_content_directory(post_dir, text_content.id, text_content.title)

        content_path = os.path.join(content_dir, "content.txt")
        with open(content_path, "w", encoding="utf-8") as f:
            f.write(text_content.comment)

    def save_product_content(self, post_dir: str, product_content: FantiaProduct) -> None:
        """Save product content to files."""
        if not product_content.comment:
            logger.warning(f"Product content {product_content.id} has no comment.")
            return

        content_dir = self._create_content_directory(
            post_dir, product_content.id, product_content.title
        )

        # Save comment
        content_path = os.path.join(content_dir, "content.txt")
        with open(content_path, "w", encoding="utf-8") as f:
            f.write(product_content.comment)

        # Save URL
        url_path = os.path.join(content_dir, "url.txt")
        with open(url_path, "w", encoding="utf-8") as f:
            f.write(product_content.url)

    def _create_content_directory(self, post_dir: str, content_id: str, content_title: str) -> str:
        """Create directory for content within a post."""
        dir_name = sanitize_filename(f"{content_id}_{content_title}")
        content_dir = os.path.join(post_dir, dir_name)
        os.makedirs(content_dir, exist_ok=True)
        return content_dir

    def _perform_download(self, url: str, path: str) -> bool:
        """Perform a download for the specified URL while showing progress."""
        with self._client.stream("GET", url) as response:
            if response.status_code == 404:
                logger.info("URL returned 404. Skipping...\n")
                return False
            response.raise_for_status()

            file_size = int(response.headers["Content-Length"])
            downloaded = 0
            with open(path, mode="wb") as f:
                for chunk in response.iter_bytes():
                    downloaded += len(chunk)
                    f.write(chunk)

        if downloaded != file_size:
            logger.error(f"Downloaded file size mismatch (expected {file_size}, got {downloaded})")

        return True
