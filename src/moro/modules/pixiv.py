"""
Pixiv artwork downloader module.

Uses pixivpy library to download artwork from Pixiv.
Supports downloading illustrations, manga, and ugoira (animated images).
"""

import logging
import os
import re
import tempfile
import zipfile
from typing import Any
from urllib.parse import urlparse

import httpx
from pixivpy3 import AppPixivAPI  # type: ignore[import-untyped]

from moro.modules.common import generate_number_prefix

logger = logging.getLogger(__name__)

__all__ = [
    "PixivDownloader",
    "PixivError",
    "download_pixiv_artwork",
    "extract_artwork_id",
]


class PixivError(Exception):
    """Exception raised when Pixiv operations fail."""

    pass


class PixivDownloader:
    """Pixiv artwork downloader using pixivpy API."""

    def __init__(self, refresh_token: str | None = None) -> None:
        """
        Initialize Pixiv downloader.

        Args:
            refresh_token: Pixiv API refresh token for authentication.
                         If None, will attempt anonymous access (limited functionality).
        """
        self.api = AppPixivAPI()
        self.refresh_token = refresh_token
        self._authenticated = False

        if refresh_token:
            try:
                self.api.auth(refresh_token=refresh_token)
                self._authenticated = True
                logger.info("Successfully authenticated with Pixiv API")
            except Exception as e:
                logger.warning(f"Failed to authenticate with Pixiv API: {e}")
                raise PixivError(f"Authentication failed: {e}") from e

    def get_artwork_detail(self, artwork_id: int) -> dict[str, Any]:
        """
        Get artwork details from Pixiv.

        Args:
            artwork_id: Pixiv artwork ID.

        Returns:
            Dict containing artwork information.

        Raises:
            PixivError: If artwork cannot be retrieved.
        """
        try:
            result = self.api.illust_detail(artwork_id)
            if "illust" not in result:
                raise PixivError(f"Artwork {artwork_id} not found or inaccessible")
            return result["illust"]  # type: ignore[no-any-return]
        except Exception as e:
            logger.error(f"Failed to get artwork details for {artwork_id}: {e}")
            raise PixivError(f"Failed to get artwork details: {e}") from e

    def get_artwork_urls(self, artwork_detail: dict[str, Any]) -> list[str]:
        """
        Extract download URLs from artwork detail.

        Args:
            artwork_detail: Artwork detail from Pixiv API.

        Returns:
            List of image URLs to download.
        """
        urls: list[str] = []
        artwork_type = artwork_detail["type"]

        if artwork_type == "illust":
            # Single illustration
            if artwork_detail["page_count"] == 1:
                # Single page
                urls.append(artwork_detail["meta_single_page"]["original_image_url"])
            else:
                # Multiple pages
                for page in artwork_detail["meta_pages"]:
                    urls.append(page["image_urls"]["original"])
        elif artwork_type == "manga":
            # Manga (multiple pages)
            for page in artwork_detail["meta_pages"]:
                urls.append(page["image_urls"]["original"])
        elif artwork_type == "ugoira":
            # Animated image - get ugoira metadata
            try:
                ugoira_meta = self.api.ugoira_metadata(artwork_detail["id"])
                if "ugoira_metadata" in ugoira_meta:
                    urls.append(ugoira_meta["ugoira_metadata"]["zip_urls"]["medium"])
            except Exception as e:
                logger.warning(f"Failed to get ugoira metadata: {e}")
                # Fallback to regular image
                urls.append(artwork_detail["image_urls"]["medium"])

        return urls

    def download_file(
        self, url: str, dest_path: str, referer: str = "https://www.pixiv.net/"
    ) -> str:
        """
        Download a file from Pixiv with proper headers.

        Args:
            url: URL to download.
            dest_path: Destination file path.
            referer: Referer header for the request.

        Returns:
            Path to the downloaded file.

        Raises:
            PixivError: If download fails.
        """
        try:
            headers = {
                "Referer": referer,
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            }

            with httpx.Client(timeout=30.0) as client:
                response = client.get(url, headers=headers)
                response.raise_for_status()

                os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                with open(dest_path, "wb") as f:
                    f.write(response.content)

                logger.info(f"Downloaded: {url} -> {dest_path}")
                return dest_path

        except Exception as e:
            logger.error(f"Failed to download {url}: {e}")
            raise PixivError(f"Download failed: {e}") from e

    def create_filename(
        self,
        artwork_detail: dict[str, Any],
        url: str,
        index: int = 0,
        total: int = 1,
        auto_prefix: bool = False,
    ) -> str:
        """
        Create filename for downloaded artwork.

        Args:
            artwork_detail: Artwork detail from Pixiv API.
            url: Download URL.
            index: Index for multiple files (0-based).
            total: Total number of files.
            auto_prefix: Whether to use automatic numbered prefixes.

        Returns:
            Generated filename.
        """
        # Extract extension from URL
        ext = os.path.splitext(urlparse(url).path)[-1] or ".jpg"

        # Clean title for filename
        title = re.sub(r'[<>:"/\\|?*]', "_", artwork_detail["title"])
        author = re.sub(r'[<>:"/\\|?*]', "_", artwork_detail["user"]["name"])
        artwork_id = artwork_detail["id"]

        if auto_prefix and total > 1:
            prefix = generate_number_prefix(total, index + 1)
            return f"{prefix}{artwork_id}_{title}_{author}{ext}"
        if total > 1:
            return f"{artwork_id}_{title}_{author}_p{index:02d}{ext}"
        return f"{artwork_id}_{title}_{author}{ext}"

    def save_metadata(self, artwork_detail: dict[str, Any], dest_dir: str) -> str:
        """
        Save artwork metadata as JSON file.

        Args:
            artwork_detail: Artwork detail from Pixiv API.
            dest_dir: Destination directory.

        Returns:
            Path to the saved metadata file.
        """
        import json

        artwork_id = artwork_detail["id"]
        metadata_path = os.path.join(dest_dir, f"{artwork_id}_metadata.json")

        # Extract relevant metadata
        metadata: dict[str, Any] = {
            "id": artwork_detail["id"],
            "title": artwork_detail["title"],
            "author": artwork_detail["user"]["name"],
            "author_id": artwork_detail["user"]["id"],
            "tags": [tag["name"] for tag in artwork_detail["tags"]],
            "create_date": artwork_detail["create_date"],
            "page_count": artwork_detail["page_count"],
            "type": artwork_detail["type"],
            "caption": artwork_detail["caption"],
            "total_bookmarks": artwork_detail["total_bookmarks"],
            "total_view": artwork_detail["total_view"],
            "url": f"https://www.pixiv.net/artworks/{artwork_detail['id']}",
        }

        os.makedirs(dest_dir, exist_ok=True)
        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)

        logger.info(f"Saved metadata: {metadata_path}")
        return metadata_path


def extract_artwork_id(url: str) -> int:
    """
    Extract artwork ID from Pixiv URL.

    Args:
        url: Pixiv artwork URL.

    Returns:
        Artwork ID as integer.

    Raises:
        PixivError: If URL format is invalid.
    """
    # Pattern for Pixiv artwork URLs
    patterns = [
        r"pixiv\.net/(?:en/)?artworks/(\d+)",
        r"pixiv\.net/(?:en/)?member_illust\.php\?.*illust_id=(\d+)",
        r"pixiv\.net/i/(\d+)",
    ]

    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return int(match.group(1))

    raise PixivError(f"Invalid Pixiv URL format: {url}")


def download_pixiv_artwork(
    url: str,
    dest_dir: str,
    refresh_token: str | None = None,
    auto_prefix: bool = False,
    save_metadata: bool = True,
) -> list[str]:
    """
    Download Pixiv artwork from URL.

    Args:
        url: Pixiv artwork URL.
        dest_dir: Destination directory or ZIP file path.
        refresh_token: Pixiv API refresh token.
        auto_prefix: Whether to use automatic numbered prefixes for multiple files.
        save_metadata: Whether to save artwork metadata.

    Returns:
        List of downloaded file paths.

    Raises:
        PixivError: If download fails.
    """
    downloader = PixivDownloader(refresh_token)
    artwork_id = extract_artwork_id(url)

    logger.info(f"Downloading Pixiv artwork {artwork_id}")

    # Get artwork details
    artwork_detail = downloader.get_artwork_detail(artwork_id)
    image_urls = downloader.get_artwork_urls(artwork_detail)
    logger.info(f"Found {len(image_urls)} images for artwork {artwork_id}")

    # Check if output should be ZIP
    is_zip = dest_dir.lower().endswith(".zip")
    temp_dir = None

    try:
        if is_zip:
            temp_dir = tempfile.mkdtemp()
            download_dest = temp_dir
        else:
            download_dest = dest_dir

        downloaded_files: list[str] = []

        # Download images
        for i, image_url in enumerate(image_urls):
            filename = downloader.create_filename(
                artwork_detail, image_url, i, len(image_urls), auto_prefix
            )
            file_path = os.path.join(download_dest, filename)

            downloaded_file = downloader.download_file(image_url, file_path)
            downloaded_files.append(downloaded_file)

        # Save metadata if requested
        if save_metadata:
            metadata_file = downloader.save_metadata(artwork_detail, download_dest)
            downloaded_files.append(metadata_file)

        # Create ZIP if needed
        if is_zip and temp_dir:
            logger.info(f"Creating ZIP archive: {dest_dir}")
            os.makedirs(os.path.dirname(os.path.abspath(dest_dir)), exist_ok=True)

            with zipfile.ZipFile(dest_dir, "w", zipfile.ZIP_DEFLATED) as zipf:
                for file_path in downloaded_files:
                    zipf.write(file_path, os.path.basename(file_path))

            logger.info(f"Created ZIP archive with {len(downloaded_files)} files")
            return [dest_dir]

        logger.info(f"Downloaded {len(downloaded_files)} files")
        return downloaded_files

    finally:
        if temp_dir:
            import shutil

            shutil.rmtree(temp_dir)
