"""Fantia file operations service."""

import os
from datetime import datetime as dt
from logging import getLogger

from injector import inject, singleton
from pathvalidate import sanitize_filename

from moro.config.settings import ConfigRepository
from moro.modules.fantia.domain import FantiaPostData, FantiaProduct, FantiaText

logger = getLogger(__name__)


@inject
@singleton
class FantiaFileService:
    """Service for handling Fantia file operations."""

    def __init__(self, config: ConfigRepository) -> None:
        self.config = config

    def create_post_directory(self, post_data: FantiaPostData) -> str:
        """
        Create directory for a post.

        Args:
            post_data: Post data containing directory information.

        Returns:
            str: Created directory path.
        """
        if post_data.converted_at == 1571632367.0:
            # Handle special case for posts with no converted_at timestamp
            date = dt.fromtimestamp(post_data.posted_at)
        else:
            date = dt.fromtimestamp(post_data.converted_at)
        formatted_date = date.strftime("%Y%m%d%H%M")
        dir_name = sanitize_filename(f"{post_data.id}_{post_data.title}_{formatted_date}")

        post_dir = os.path.join(
            self.config.common.working_dir, "downloads", "fantia", post_data.creator_id, dir_name
        )

        os.makedirs(post_dir, exist_ok=True)
        return post_dir

    def create_content_directory(self, post_dir: str, content_id: str, content_title: str) -> str:
        """
        Create directory for content within a post.

        Args:
            post_dir: Parent post directory.
            content_id: Content ID.
            content_title: Content title.

        Returns:
            str: Created content directory path.
        """
        dir_name = sanitize_filename(f"{content_id}_{content_title}")
        content_dir = os.path.join(post_dir, dir_name)
        os.makedirs(content_dir, exist_ok=True)
        return content_dir

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

    def save_text_content(self, post_dir: str, text_content: FantiaText) -> None:
        """
        Save text content to file.

        Args:
            post_dir: Post directory path.
            text_content: Text content data.
        """
        if not text_content.comment:
            logger.warning(f"Text content {text_content.id} has no comment.")
            return

        content_dir = self.create_content_directory(post_dir, text_content.id, text_content.title)

        content_path = os.path.join(content_dir, "content.txt")
        with open(content_path, "w", encoding="utf-8") as f:
            f.write(text_content.comment)

    def save_product_content(self, post_dir: str, product_content: FantiaProduct) -> None:
        """
        Save product content to files.

        Args:
            post_dir: Post directory path.
            product_content: Product content data.
        """
        if not product_content.comment:
            logger.warning(f"Product content {product_content.id} has no comment.")
            return

        content_dir = self.create_content_directory(
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

    def get_download_directory(self) -> str:
        """
        Get the base download directory.

        Returns:
            str: Base download directory path.
        """
        return os.path.join(self.config.common.working_dir, "downloads", "fantia")
