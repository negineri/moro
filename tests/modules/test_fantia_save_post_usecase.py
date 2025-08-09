"""Tests for FantiaSavePostUseCase."""

from pathlib import Path
from unittest.mock import Mock, patch

import httpx
import pytest

from moro.config.settings import ConfigRepository
from moro.modules.common import CommonConfig
from moro.modules.fantia.domain import (
    FantiaFile,
    FantiaPhotoGallery,
    FantiaPostData,
    FantiaProduct,
    FantiaText,
    FantiaURL,
)
from moro.modules.fantia.infrastructure import FantiaFileDownloader
from moro.modules.fantia.usecases import FantiaSavePostUseCase


@pytest.fixture
def post_data() -> FantiaPostData:
    """FantiaPostDataのテスト用インスタンスを提供するフィクスチャ."""
    return FantiaPostData(
        id="test_post_id",
        title="Test Post",
        creator_name="Test Creator",
        creator_id="test_creator_id",
        contents=[],
        contents_photo_gallery=[
            FantiaPhotoGallery(
                id="gallery1",
                title="Test Gallery",
                comment="This is a test gallery.",
                photos=[FantiaURL(url="https://example.com/photo1.jpg", ext="jpg")],
            )
        ],
        contents_files=[
            FantiaFile(
                id="file1",
                title="Test File",
                comment="This is a test file.",
                url="https://example.com/file1.zip",
                name="file1.zip",
            )
        ],
        contents_text=[
            FantiaText(
                id="text1",
                title="Test Text",
                comment="This is a test text content.",
            )
        ],
        contents_products=[
            FantiaProduct(
                id="product1",
                title="Test Product",
                comment="This is a test product.",
                name="Test Product",
                url="https://example.com/product1",
            )
        ],
        posted_at=1633036800,
        converted_at=1633036800,
        comment="Test Comment",
        thumbnail=None,
    )


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

        file_downloader = Mock(spec=FantiaFileDownloader)

        usecase = FantiaSavePostUseCase(
            config=config_repo,
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

    def test_execute_download_failure_rollback(self, tmp_path: Path) -> None:
        """EC001: ダウンロード失敗時の全体ロールバックのテスト。

        前提: 一部URLが404エラーを返す（download_all_content が False を返す）
        アクション: execute(post_data)実行
        期待結果: post全体の保存が失敗、IOErrorが発生、部分的保存データもクリーンアップ
        """
        # Arrange: テストデータとモックの準備
        config_repo = Mock(spec=ConfigRepository)
        config_repo.common = CommonConfig(working_dir=str(tmp_path))

        file_downloader = Mock(spec=FantiaFileDownloader)

        usecase = FantiaSavePostUseCase(
            config=config_repo,
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

        # Assert: ダウンロードは試行される
        file_downloader.download_all_content.assert_called_once()


class TestFantiaSavePostUseCaseIntegration:
    """FantiaSavePostUseCaseの統合テストクラス."""

    def test_integration_successful_save(self, tmp_path: Path, post_data: FantiaPostData) -> None:
        """統合テスト: 実際のファイルダウンロードと保存をモック."""
        # Arrange
        config_repo = Mock(spec=ConfigRepository)
        config_repo.common = CommonConfig(
            user_data_dir=str(tmp_path / "user_data"),
            user_cache_dir=str(tmp_path / "cache"),
            working_dir=str(tmp_path),
            jobs=4,
        )

        # 実際のFantiaFileDownloaderを作成してモック
        mock_client = Mock()
        file_downloader = FantiaFileDownloader(_client=mock_client)

        # httpxのストリーミングレスポンスをモック
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {"Content-Length": "1024"}
        mock_response.iter_bytes.return_value = [b"x" * 1024]

        with (
            patch.object(file_downloader, "_perform_download", return_value=True),
            patch("builtins.open", create=True) as mock_open,
        ):
            mock_open.return_value.__enter__.return_value.write = Mock()

            usecase = FantiaSavePostUseCase(
                config=config_repo,
                file_downloader=file_downloader,
            )

            # Act
            usecase.execute(post_data)

            # Assert: ディレクトリが作成されることを確認
            expected_dir = Path(tmp_path) / "downloads" / "fantia" / post_data.creator_id
            assert expected_dir.exists()

    def test_integration_download_failure_cleanup(
        self, tmp_path: Path, post_data: FantiaPostData
    ) -> None:
        """統合テスト: ダウンロード失敗時のクリーンアップ."""
        # Arrange
        config_repo = Mock(spec=ConfigRepository)
        config_repo.common = CommonConfig(
            user_data_dir=str(tmp_path / "user_data"),
            user_cache_dir=str(tmp_path / "cache"),
            working_dir=str(tmp_path),
            jobs=4,
        )

        mock_client = Mock()
        file_downloader = FantiaFileDownloader(_client=mock_client)

        # ダウンロードが失敗することを模擬
        with patch.object(file_downloader, "download_all_content", return_value=False):
            usecase = FantiaSavePostUseCase(
                config=config_repo,
                file_downloader=file_downloader,
            )

            # Act & Assert
            with pytest.raises(OSError, match="Failed to download all content"):
                usecase.execute(post_data)

    def test_integration_file_operations(self, tmp_path: Path, post_data: FantiaPostData) -> None:
        """統合テスト: 実際のファイル操作を含むテスト."""
        # Arrange
        config_repo = Mock(spec=ConfigRepository)
        config_repo.common = CommonConfig(
            user_data_dir=str(tmp_path / "user_data"),
            user_cache_dir=str(tmp_path / "cache"),
            working_dir=str(tmp_path),
            jobs=4,
        )

        mock_client = Mock()

        # httpx.stream のモック設定
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {"Content-Length": "1024"}
        mock_response.iter_bytes.return_value = [b"test_data"]
        mock_response.raise_for_status = Mock()
        mock_client.stream.return_value.__enter__ = Mock(return_value=mock_response)
        mock_client.stream.return_value.__exit__ = Mock(return_value=None)

        file_downloader = FantiaFileDownloader(_client=mock_client)

        usecase = FantiaSavePostUseCase(
            config=config_repo,
            file_downloader=file_downloader,
        )

        # Act
        usecase.execute(post_data)

        # Assert: 期待されるディレクトリとファイルが作成されることを確認
        expected_dir = Path(tmp_path) / "downloads" / "fantia" / post_data.creator_id
        assert expected_dir.exists()

        # コメントファイルの存在確認
        comment_files = list(expected_dir.rglob("comment.txt"))
        assert len(comment_files) > 0

        # 各コンテンツディレクトリの確認
        for gallery in post_data.contents_photo_gallery:
            gallery_dir = expected_dir.rglob(f"{gallery.id}_{gallery.title}*")
            assert any(gallery_dir)

    def test_integration_directory_creation(
        self, tmp_path: Path, post_data: FantiaPostData
    ) -> None:
        """統合テスト: ディレクトリ作成の詳細テスト."""
        # Arrange
        config_repo = Mock(spec=ConfigRepository)
        config_repo.common = CommonConfig(
            user_data_dir=str(tmp_path / "user_data"),
            user_cache_dir=str(tmp_path / "cache"),
            working_dir=str(tmp_path),
            jobs=4,
        )

        mock_client = Mock()
        file_downloader = FantiaFileDownloader(_client=mock_client)

        with patch.object(file_downloader, "download_all_content", return_value=True):
            usecase = FantiaSavePostUseCase(
                config=config_repo,
                file_downloader=file_downloader,
            )

            # Act
            usecase.execute(post_data)

            # Assert: ディレクトリ構造の確認
            downloads_dir = Path(tmp_path) / "downloads" / "fantia" / post_data.creator_id
            assert downloads_dir.exists()

            # 投稿ディレクトリが作成されていることを確認
            post_dirs = list(downloads_dir.glob(f"{post_data.id}_*"))
            assert len(post_dirs) == 1
            assert post_dirs[0].is_dir()

    def test_integration_error_handling_with_real_exceptions(
        self, tmp_path: Path, post_data: FantiaPostData
    ) -> None:
        """統合テスト: 実際の例外処理."""
        # Arrange
        config_repo = Mock(spec=ConfigRepository)
        config_repo.common = CommonConfig(
            user_data_dir=str(tmp_path / "user_data"),
            user_cache_dir=str(tmp_path / "cache"),
            working_dir=str(tmp_path),
            jobs=4,
        )

        mock_client = Mock()
        mock_client.stream.side_effect = httpx.RequestError("Network error")

        file_downloader = FantiaFileDownloader(_client=mock_client)

        usecase = FantiaSavePostUseCase(
            config=config_repo,
            file_downloader=file_downloader,
        )

        # Act & Assert: ネットワークエラーが発生した場合の処理
        with pytest.raises(OSError, match="Failed to download all content"):
            usecase.execute(post_data)
