"""Usecases for Fantia module."""

import os
import shutil
from dataclasses import dataclass
from datetime import datetime as dt

from injector import inject
from pathvalidate import sanitize_filename

from moro.config.settings import ConfigRepository
from moro.modules.fantia.domain import (
    FantiaFanclub,
    FantiaFanclubRepository,
    FantiaPostData,
    FantiaPostRepository,
)
from moro.modules.fantia.infrastructure import FantiaFileDownloader


@inject
@dataclass
class FantiaGetFanclubUseCase:
    """Use case for getting a Fantia fanclub by ID."""

    fanclub_repo: FantiaFanclubRepository

    def execute(self, fanclub_id: str) -> FantiaFanclub | None:
        """Execute the use case to get a fanclub by ID."""
        return self.fanclub_repo.get(fanclub_id)


@inject
@dataclass
class FantiaGetPostsUseCase:
    """Use case for getting posts by a Fantia fanclub ID."""

    post_repo: FantiaPostRepository

    def execute(self, post_ids: list[str]) -> list[FantiaPostData]:
        """Execute the use case to get posts by fanclub ID."""
        return self.post_repo.get_many(post_ids)


@inject
@dataclass
class FantiaSavePostUseCase:
    """Use case for saving a Fantia post with all its content."""

    config: ConfigRepository
    file_downloader: FantiaFileDownloader

    def execute(self, post_data: FantiaPostData) -> None:
        """Execute the use case to save a post with all its content.

        Args:
            post_data: The post data to save

        Raises:
            IOError: If saving fails
        """
        post_directory = self._create_post_directory(post_data)

        # 原子性を担保: 全てのダウンロードが成功した場合のみ保存
        download_success = self.file_downloader.download_all_content(post_data, post_directory)
        if not download_success:
            # 部分的に作成されたファイルをクリーンアップ
            self._cleanup_partial_download(post_directory)
            raise OSError("Failed to download all content for the post")

    def _create_post_directory(self, post_data: FantiaPostData) -> str:
        """Create directory for a post.

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

    def _cleanup_partial_download(self, post_directory: str) -> None:
        """Clean up partially downloaded content.

        Args:
            post_directory: Directory path to clean up.
        """
        if os.path.exists(post_directory):
            shutil.rmtree(post_directory)
