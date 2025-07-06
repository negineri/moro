"""Use Case for Downloading a Post from Fantia"""

import os
from dataclasses import dataclass

from click import echo
from injector import inject

from moro.config.settings import AppConfig
from moro.modules.fantia import (
    FantiaClient,
    create_chrome_options,
    download_photo_gallery,
    login_fantia,
    parse_post,
)


@inject
@dataclass
class FantiaDownloadPostUseCase:
    """Use case for downloading a post from Fantia."""

    config: AppConfig
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

        post = parse_post(self.client, post_id, priorize_webp=self.config.fantia.priorize_webp)
        echo(f"Post ID: {post.id}")
        echo(f"Post Title: {post.title}")
        echo(f"Post Creator: {post.creator_name}")
        echo(f"Post Contents: {post.contents}")
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
