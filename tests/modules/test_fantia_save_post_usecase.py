"""Tests for FantiaSavePostUseCase."""

from pathlib import Path
from unittest.mock import Mock

import pytest

from moro.config.settings import ConfigRepository
from moro.modules.common import CommonConfig
from moro.modules.fantia.domain import FantiaFileDownloader, FantiaPostData
from moro.modules.fantia.usecases import FantiaSavePostUseCase


class TestFantiaSavePostUseCase:
    """FantiaSavePostUseCaseのテストクラス。"""

    def test_execute_basic_post_save(self, tmp_path: Path) -> None:
        """HP001: 基本的な投稿データ保存のテスト。

        前提: 有効なFantiaPostDataが存在
        アクション: execute(post_data)実行
        期待結果: 正常に保存完了、ディレクトリ構造が正しく作成される
        """
        # Arrange: テストデータとモックの準備
        config_repo = Mock(spec=ConfigRepository)
        config_repo.common = CommonConfig(working_dir=str(tmp_path))

        post_storage_repo = Mock()
        file_downloader = Mock(spec=FantiaFileDownloader)

        usecase = FantiaSavePostUseCase(
            config=config_repo,
            post_storage_repo=post_storage_repo,
            file_downloader=file_downloader,
        )

        post_data = FantiaPostData(
            id="12345",
            title="テスト投稿",
            creator_name="テストクリエイター",
            creator_id="67890",
            contents=[],
            contents_photo_gallery=[],
            contents_files=[],
            contents_text=[],
            contents_products=[],
            posted_at=1234567890,
            converted_at=1234567890,
            comment="テストコメント",
            thumbnail=None,
        )

        # モックの戻り値を設定
        file_downloader.download_all_content.return_value = True

        # Act: UseCase実行
        usecase.execute(post_data)

        # Assert: 適切なメソッドが呼ばれることを確認
        file_downloader.download_all_content.assert_called_once()
        post_storage_repo.save.assert_called_once()

    def test_execute_download_failure_rollback(self, tmp_path: Path) -> None:
        """EC001: ダウンロード失敗時の全体ロールバックのテスト。

        前提: 一部URLが404エラーを返す（download_all_content が False を返す）
        アクション: execute(post_data)実行
        期待結果: post全体の保存が失敗、IOErrorが発生、部分的保存データもクリーンアップ
        """
        # Arrange: テストデータとモックの準備
        config_repo = Mock(spec=ConfigRepository)
        config_repo.common = CommonConfig(working_dir=str(tmp_path))

        post_storage_repo = Mock()
        file_downloader = Mock(spec=FantiaFileDownloader)

        usecase = FantiaSavePostUseCase(
            config=config_repo,
            post_storage_repo=post_storage_repo,
            file_downloader=file_downloader,
        )

        post_data = FantiaPostData(
            id="12345",
            title="テスト投稿",
            creator_name="テストクリエイター",
            creator_id="67890",
            contents=[],
            contents_photo_gallery=[],
            contents_files=[],
            contents_text=[],
            contents_products=[],
            posted_at=1234567890,
            converted_at=1234567890,
            comment="テストコメント",
            thumbnail=None,
        )

        # モックの戻り値を設定: ダウンロード失敗
        file_downloader.download_all_content.return_value = False

        # Act & Assert: IOErrorが発生することを確認
        with pytest.raises(IOError, match="Failed to download all content for the post"):
            usecase.execute(post_data)

        # Assert: ダウンロードは試行されるが、保存は実行されない
        file_downloader.download_all_content.assert_called_once()
        post_storage_repo.save.assert_not_called()
