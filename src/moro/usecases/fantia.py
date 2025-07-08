"""Use Case for Downloading a Post from Fantia"""

import os
from dataclasses import dataclass
from datetime import datetime as dt
from logging import getLogger
from time import sleep

from click import echo
from injector import inject
from pathvalidate import sanitize_filename

from moro.config.settings import ConfigRepository
from moro.modules.fantia import (
    FantiaClient,
    create_chrome_options,
    download_file,
    download_photo_gallery,
    download_thumbnail,
    get_posts_by_user,
    login_fantia,
    parse_post,
)

logger = getLogger(__name__)


@inject
@dataclass
class FantiaDownloadPostUseCase:
    """Use case for downloading a post from Fantia."""

    config: ConfigRepository
    client: FantiaClient

    def execute(self, post_id: str) -> None:
        """
        Execute the use case to download a post.

        :param post_id: The ID of the post to download.
        """
        chrome_userdata_dir = os.path.join(self.config.app.user_data_dir, "chrome_userdata")
        if not login_fantia(self.client, create_chrome_options(chrome_userdata_dir)):
            echo("Failed to login to Fantia. Please check your session ID.")
            return

        post = parse_post(self.client, post_id)
        echo(f"Post ID: {post.id}")
        echo(f"Post Title: {post.title}")
        echo(f"Post Creator: {post.creator_name}")
        echo(f"Post Contents: {len(post.contents)}")
        echo(f"Post Posted At: {post.posted_at}")
        echo(f"Post Converted At: {post.converted_at}")

        data_dir = os.path.join(
            self.config.app.working_dir,
            "downloads",
            "fantia",
            post.creator_id,
            f"{post.id}_{post.title}_{post.converted_at}",
        )
        os.makedirs(data_dir, exist_ok=True)
        if post.comment:
            with open(os.path.join(data_dir, "comment.txt"), mode="w") as f:
                f.write(post.comment)

        for photo_gallery in post.contents_photo_gallery:
            echo(f"Downloading photo gallery: {photo_gallery.title}")
            content_dir = os.path.join(data_dir, f"{photo_gallery.id}_{photo_gallery.title}")
            os.makedirs(content_dir, exist_ok=True)
            download_photo_gallery(self.client, content_dir, photo_gallery)


@inject
@dataclass
class FantiaDownloadPostsByUserUseCase:
    """Use case for downloading all posts by a user from Fantia."""

    config: ConfigRepository
    client: FantiaClient

    def execute(self, user_id: str) -> None:
        """
        Execute the use case to download all posts by a user.

        :param user_id: The ID of the user whose posts to download.
        """
        chrome_userdata_dir = os.path.join(self.config.app.user_data_dir, "chrome_userdata")
        if not login_fantia(self.client, create_chrome_options(chrome_userdata_dir)):
            echo("Failed to login to Fantia. Please check your session ID.")
            return

        post_ids = get_posts_by_user(self.client, user_id)
        for post_id in post_ids:
            echo(f"Downloading post ID: {post_id}")
            post = parse_post(self.client, post_id)

            data_dir = os.path.join(
                self.config.app.working_dir,
                "downloads",
                "fantia",
                post.creator_id,
                sanitize_filename(
                    f"{post.id}_{post.title}_{dt.fromtimestamp(post.converted_at).strftime('%Y%m%d%H%M')}"
                ),
            )
            os.makedirs(data_dir, exist_ok=True)
            if post.comment:
                with open(os.path.join(data_dir, "comment.txt"), mode="w") as f:
                    f.write(post.comment)
            if self.config.fantia.download_thumb and post.thumbnail:
                logger.info(f"Downloading thumbnail: {post.thumbnail}")
                download_thumbnail(self.client, data_dir, post)

            for photo_gallery in post.contents_photo_gallery:
                echo(f"Downloading photo gallery: {photo_gallery.title}")
                content_dir = os.path.join(
                    data_dir, sanitize_filename(f"{photo_gallery.id}_{photo_gallery.title}")
                )
                os.makedirs(content_dir, exist_ok=True)
                download_photo_gallery(self.client, content_dir, photo_gallery)

            for file in post.contents_files:
                echo(f"Downloading file: {file.title}")
                content_dir = os.path.join(data_dir, sanitize_filename(f"{file.id}_{file.title}"))
                os.makedirs(content_dir, exist_ok=True)
                download_file(self.client, content_dir, file)

            for text in post.contents_text:
                echo(f"Saving text content: {text.title}")
                if not text.comment:
                    logger.warning(f"Text content {text.id} has no comment.")
                    continue
                content_dir = os.path.join(data_dir, sanitize_filename(f"{text.id}_{text.title}"))
                os.makedirs(content_dir, exist_ok=True)
                with open(os.path.join(content_dir, "content.txt"), mode="w") as f:
                    f.write(text.comment)

            for product in post.contents_products:
                echo(f"Saving product content: {product.title}")
                if not product.comment:
                    logger.warning(f"Product content {product.id} has no comment.")
                    continue
                content_dir = os.path.join(
                    data_dir, sanitize_filename(f"{product.id}_{product.title}")
                )
                os.makedirs(content_dir, exist_ok=True)
                with open(os.path.join(content_dir, "content.txt"), mode="w") as f:
                    f.write(product.comment)
                with open(os.path.join(content_dir, "url.txt"), mode="w") as f:
                    f.write(product.url)

            sleep(1)
