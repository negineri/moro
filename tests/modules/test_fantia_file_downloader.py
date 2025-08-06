"""Tests for FantiaFileDownloader."""

import os
from pathlib import Path
from unittest.mock import Mock, patch

from moro.modules.fantia.domain import (
    FantiaFile,
    FantiaFileDownloader,
    FantiaPhotoGallery,
    FantiaPostData,
    FantiaURL,
)


class TestFantiaFileDownloader:
    """FantiaFileDownloaderのテストクラス。"""

    def test_download_all_content_with_thumbnail(self, tmp_path: Path) -> None:
        """サムネイル付き投稿のダウンロードテスト。

        前提: サムネイルURLを含むFantiaPostData
        アクション: download_all_content実行
        期待結果: サムネイルファイルが正しくダウンロード・保存される
        """
        # Arrange
        downloader = FantiaFileDownloader()
        post_directory = str(tmp_path / "test_post")
        os.makedirs(post_directory, exist_ok=True)

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
            thumbnail=FantiaURL(url="https://example.com/thumb.jpg", ext="jpg"),
        )

        # Act & Assert: 現在のdownload_all_contentは常にTrueを返すため失敗するはず
        with patch("httpx.get") as mock_get:
            mock_response = Mock()
            mock_response.content = b"fake image data"
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response

            result = downloader.download_all_content(post_data, post_directory)

            # 現在の実装では実際のダウンロードが行われないため、Falseが返されるべき
            assert result is True  # この部分で失敗するはず（実装が不完全なため）

            # ダウンロードされたファイルが存在するかチェック
            thumbnail_path = Path(post_directory) / "0000_thumb.jpg"
            assert thumbnail_path.exists()  # この部分で失敗するはず

    def test_download_all_content_with_photo_gallery(self, tmp_path: Path) -> None:
        """写真ギャラリー付き投稿のダウンロードテスト。

        前提: FantiaPhotoGalleryを含むFantiaPostData
        アクション: download_all_content実行
        期待結果: 全写真が連番でダウンロード・保存される
        """
        # Arrange
        downloader = FantiaFileDownloader()
        post_directory = str(tmp_path / "test_post")
        os.makedirs(post_directory, exist_ok=True)

        gallery = FantiaPhotoGallery(
            id="gallery1",
            title="テストギャラリー",
            comment="ギャラリーコメント",
            photos=[
                FantiaURL(url="https://example.com/photo1.jpg", ext="jpg"),
                FantiaURL(url="https://example.com/photo2.png", ext="png"),
            ],
        )

        post_data = FantiaPostData(
            id="12345",
            title="テスト投稿",
            creator_name="テストクリエイター",
            creator_id="67890",
            contents=[],
            contents_photo_gallery=[gallery],
            contents_files=[],
            contents_text=[],
            contents_products=[],
            posted_at=1234567890,
            converted_at=1234567890,
            comment="テストコメント",
            thumbnail=None,
        )

        # Act & Assert
        with patch("httpx.get") as mock_get:
            mock_response = Mock()
            mock_response.content = b"fake image data"
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response

            result = downloader.download_all_content(post_data, post_directory)

            # 現在の実装では実際のダウンロードが行われないため、Falseが返されるべき
            assert result is True  # この部分で失敗するはず

            # ダウンロードされたファイルが存在するかチェック
            gallery_dir = Path(post_directory) / "gallery1_テストギャラリー"
            photo1_path = gallery_dir / "000.jpg"
            photo2_path = gallery_dir / "001.png"
            assert gallery_dir.exists()  # この部分で失敗するはず
            assert photo1_path.exists()  # この部分で失敗するはず
            assert photo2_path.exists()  # この部分で失敗するはず

    def test_download_all_content_with_files(self, tmp_path: Path) -> None:
        """ファイル付き投稿のダウンロードテスト。

        前提: FantiaFileを含むFantiaPostData
        アクション: download_all_content実行
        期待結果: ファイルが元のファイル名で保存される
        """
        # Arrange
        downloader = FantiaFileDownloader()
        post_directory = str(tmp_path / "test_post")
        os.makedirs(post_directory, exist_ok=True)

        file_data = FantiaFile(
            id="file1",
            title="テストファイル",
            comment="ファイルコメント",
            url="https://example.com/testfile.zip",
            name="testfile.zip",
        )

        post_data = FantiaPostData(
            id="12345",
            title="テスト投稿",
            creator_name="テストクリエイター",
            creator_id="67890",
            contents=[],
            contents_photo_gallery=[],
            contents_files=[file_data],
            contents_text=[],
            contents_products=[],
            posted_at=1234567890,
            converted_at=1234567890,
            comment="テストコメント",
            thumbnail=None,
        )

        # Act & Assert
        with patch("httpx.get") as mock_get:
            mock_response = Mock()
            mock_response.content = b"fake file data"
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response

            result = downloader.download_all_content(post_data, post_directory)

            # 現在の実装では実際のダウンロードが行われないため、Falseが返されるべき
            assert result is True  # この部分で失敗するはず

            # ダウンロードされたファイルが存在するかチェック
            file_dir = Path(post_directory) / "file1_テストファイル"
            downloaded_file = file_dir / "testfile.zip"
            assert file_dir.exists()  # この部分で失敗するはず
            assert downloaded_file.exists()  # この部分で失敗するはず

    def test_download_all_content_network_error(self, tmp_path: Path) -> None:
        """ネットワークエラー時のダウンロード失敗テスト。

        前提: ネットワーク接続エラーが発生
        アクション: download_all_content実行
        期待結果: Falseが返され、例外は発生しない（エラーハンドリング）
        """
        # Arrange
        downloader = FantiaFileDownloader()
        post_directory = str(tmp_path / "test_post")
        os.makedirs(post_directory, exist_ok=True)

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
            thumbnail=FantiaURL(url="https://invalid-url.com/thumb.jpg", ext="jpg"),
        )

        # Act & Assert
        with patch("httpx.get") as mock_get:
            mock_get.side_effect = Exception("Network error")

            result = downloader.download_all_content(post_data, post_directory)

            # ネットワークエラー時はFalseが返されるべき
            assert result is False
