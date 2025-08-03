"""Fantia download service."""

import os
from logging import getLogger

from injector import inject, singleton

from moro.config.settings import ConfigRepository
from moro.modules.fantia import FantiaClient
from moro.modules.fantia.domain import FantiaFile, FantiaPhotoGallery, FantiaPostData

logger = getLogger(__name__)


@inject
@singleton
class FantiaDownloadService:
    """Service for downloading Fantia content."""

    def __init__(self, config: ConfigRepository, client: FantiaClient) -> None:
        self.config = config
        self.client = client

    def download_thumbnail(self, post_path: str, post_data: FantiaPostData) -> None:
        """
        Download the thumbnail of a post.

        Args:
            post_path: Directory path to save the thumbnail.
            post_data: Post data containing thumbnail information.
        """
        if not post_data.thumbnail:
            logger.info("No thumbnail found for this post. Skipping...")
            return

        thumb_url = post_data.thumbnail.url
        ext = post_data.thumbnail.ext
        file_path = os.path.join(post_path, f"0000_thumb{ext}")

        self._perform_download(thumb_url, file_path)

    def download_photo_gallery(self, post_path: str, photo_gallery: FantiaPhotoGallery) -> None:
        """
        Download a photo gallery.

        Args:
            post_path: Directory path to save the photos.
            photo_gallery: Photo gallery data.
        """
        if photo_gallery.comment:
            comment_path = os.path.join(post_path, "comment.txt")
            with open(comment_path, "w", encoding="utf-8") as f:
                f.write(photo_gallery.comment)

        for index, photo in enumerate(photo_gallery.photos):
            photo_path = os.path.join(post_path, f"{index:03d}{photo.ext}")
            self._perform_download(photo.url, photo_path)

    def download_file(self, post_path: str, file_data: FantiaFile) -> None:
        """
        Download a file.

        Args:
            post_path: Directory path to save the file.
            file_data: File data.
        """
        if file_data.comment:
            comment_path = os.path.join(post_path, "comment.txt")
            with open(comment_path, "w", encoding="utf-8") as f:
                f.write(file_data.comment)

        file_path = os.path.join(post_path, file_data.name)
        self._perform_download(file_data.url, file_path)

    def _perform_download(self, url: str, file_path: str) -> None:
        """
        Perform a download for the specified URL.

        Args:
            url: URL to download from.
            file_path: Local file path to save to.

        Raises:
            Exception: If download fails or file size mismatch occurs.
        """
        try:
            with self.client.stream("GET", url) as response:
                if response.status_code == 404:
                    logger.info(f"URL returned 404, skipping: {url}")
                    return

                response.raise_for_status()

                # Get expected file size
                content_length = response.headers.get("Content-Length")
                expected_size = int(content_length) if content_length else None

                # Download with progress tracking
                downloaded = 0
                with open(file_path, "wb") as f:
                    for chunk in response.iter_bytes():
                        downloaded += len(chunk)
                        f.write(chunk)

                # Verify file size if Content-Length was provided
                if expected_size and downloaded != expected_size:
                    raise Exception(
                        f"Downloaded file size mismatch: expected {expected_size}, got {downloaded}"
                    )

                logger.info(f"Downloaded: {file_path} ({downloaded} bytes)")

        except Exception as e:
            logger.error(f"Download failed for {url}: {e}")
            # Clean up partial file
            if os.path.exists(file_path):
                os.remove(file_path)
            raise
