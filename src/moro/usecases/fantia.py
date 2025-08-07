"""Use Case for Downloading a Post from Fantia"""

from dataclasses import dataclass
from logging import getLogger
from time import sleep

from click import echo
from injector import inject

from moro.config.settings import ConfigRepository
from moro.modules.fantia import (
    FantiaClient,
    parse_post,
)
from moro.modules.fantia.infrastructure import get_posts_by_user
from moro.services.fantia_auth import FantiaAuthService
from moro.services.fantia_download import FantiaDownloadService
from moro.services.fantia_file import FantiaFileService

logger = getLogger(__name__)


@inject
@dataclass
class FantiaDownloadPostUseCase:
    """Use case for downloading a post from Fantia."""

    config: ConfigRepository
    client: FantiaClient
    auth_service: FantiaAuthService
    download_service: FantiaDownloadService
    file_service: FantiaFileService

    def execute(self, post_id: str) -> None:
        """
        Execute the use case to download a post.

        :param post_id: The ID of the post to download.
        """
        if not self.auth_service.ensure_authenticated():
            echo("Failed to login to Fantia. Please check your session ID.")
            return

        echo(f"Downloading post ID: {post_id}")
        self._download_single_post(post_id)

    def _download_single_post(self, post_id: str) -> None:
        """Download a single post with all its content."""
        post = parse_post(self.client, post_id)

        # Create post directory
        data_dir = self.file_service.create_post_directory(post)

        # Save post comment if exists
        if post.comment:
            self.file_service.save_post_comment(data_dir, post.comment)

        # Download thumbnail if enabled
        if self.config.fantia.download_thumb and post.thumbnail:
            logger.info(f"Downloading thumbnail: {post.thumbnail}")
            self.download_service.download_thumbnail(data_dir, post)

        # Download photo galleries
        for photo_gallery in post.contents_photo_gallery:
            echo(f"Downloading photo gallery: {photo_gallery.title}")
            content_dir = self.file_service.create_content_directory(
                data_dir, photo_gallery.id, photo_gallery.title
            )
            self.download_service.download_photo_gallery(content_dir, photo_gallery)

        # Download files
        for file in post.contents_files:
            echo(f"Downloading file: {file.title}")
            content_dir = self.file_service.create_content_directory(data_dir, file.id, file.title)
            self.download_service.download_file(content_dir, file)

        # Save text content
        for text in post.contents_text:
            echo(f"Saving text content: {text.title}")
            self.file_service.save_text_content(data_dir, text)

        # Save product content
        for product in post.contents_products:
            echo(f"Saving product content: {product.title}")
            self.file_service.save_product_content(data_dir, product)


@inject
@dataclass
class FantiaDownloadPostsByUserUseCase:
    """Use case for downloading all posts by a user from Fantia."""

    config: ConfigRepository
    client: FantiaClient
    auth_service: FantiaAuthService
    download_service: FantiaDownloadService
    file_service: FantiaFileService

    def execute(self, user_id: str) -> None:
        """
        Execute the use case to download all posts by a user.

        :param user_id: The ID of the user whose posts to download.
        """
        if not self.auth_service.ensure_authenticated():
            echo("Failed to login to Fantia. Please check your session ID.")
            return

        post_ids = get_posts_by_user(self.client, user_id)
        for post_id in post_ids:
            echo(f"Downloading post ID: {post_id}")
            self._download_single_post(post_id)
            sleep(1)

    def _download_single_post(self, post_id: str) -> None:
        """Download a single post with all its content."""
        post = parse_post(self.client, post_id)

        # Create post directory
        data_dir = self.file_service.create_post_directory(post)

        # Save post comment if exists
        if post.comment:
            self.file_service.save_post_comment(data_dir, post.comment)

        # Download thumbnail if enabled
        if self.config.fantia.download_thumb and post.thumbnail:
            logger.info(f"Downloading thumbnail: {post.thumbnail}")
            self.download_service.download_thumbnail(data_dir, post)

        # Download photo galleries
        for photo_gallery in post.contents_photo_gallery:
            echo(f"Downloading photo gallery: {photo_gallery.title}")
            content_dir = self.file_service.create_content_directory(
                data_dir, photo_gallery.id, photo_gallery.title
            )
            self.download_service.download_photo_gallery(content_dir, photo_gallery)

        # Download files
        for file in post.contents_files:
            echo(f"Downloading file: {file.title}")
            content_dir = self.file_service.create_content_directory(data_dir, file.id, file.title)
            self.download_service.download_file(content_dir, file)

        # Save text content
        for text in post.contents_text:
            echo(f"Saving text content: {text.title}")
            self.file_service.save_text_content(data_dir, text)

        # Save product content
        for product in post.contents_products:
            echo(f"Saving product content: {product.title}")
            self.file_service.save_product_content(data_dir, product)
