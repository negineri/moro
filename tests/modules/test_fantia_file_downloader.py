"""Tests for FantiaFileDownloader."""

import os
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, Mock

import pytest

from moro.modules.fantia.domain import (
    FantiaFile,
    FantiaPhotoGallery,
    FantiaPostData,
    FantiaURL,
)
from moro.modules.fantia.infrastructure import FantiaFileDownloader


@pytest.fixture
def mock_client() -> MagicMock:
    """モックFantiaClientを作成。"""
    return MagicMock()


@pytest.fixture
def downloader(mock_client: MagicMock) -> FantiaFileDownloader:
    """モッククライアントで初期化したFantiaFileDownloader。"""
    return FantiaFileDownloader(mock_client)


@pytest.fixture
def post_directory(tmp_path: Path) -> str:
    """テスト用ポストディレクトリ。"""
    directory = str(tmp_path / "test_post")
    os.makedirs(directory, exist_ok=True)
    return directory


def _setup_mock_response(content: bytes) -> Mock:
    """共通のモックレスポンス設定。"""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.headers = {"Content-Length": str(len(content))}
    mock_response.iter_bytes.return_value = [content]
    mock_response.raise_for_status.return_value = None
    return mock_response


def _create_base_post_data(**overrides: Any) -> FantiaPostData:
    """基本的なFantiaPostDataを作成。"""
    defaults: dict[str, Any] = {
        "id": "12345",
        "title": "テスト投稿",
        "creator_name": "テストクリエイター",
        "creator_id": "67890",
        "contents": [],
        "contents_photo_gallery": [],
        "contents_files": [],
        "contents_text": [],
        "contents_products": [],
        "posted_at": 1234567890,
        "converted_at": 1234567890,
        "comment": "テストコメント",
        "thumbnail": None,
    }
    defaults.update(overrides)
    return FantiaPostData(**defaults)


class TestFantiaFileDownloader:
    """ファイルダウンローダーのテスト。"""

    def test_download_all_content_with_thumbnail(
        self, mock_client: MagicMock, downloader: FantiaFileDownloader, post_directory: str
    ) -> None:
        """サムネイル付き投稿のダウンロードテスト。

        前提: サムネイルURLを含むFantiaPostData
        アクション: download_all_content実行
        期待結果: サムネイルファイルが正しくダウンロード・保存される
        """
        # Arrange
        thumbnail = FantiaURL(url="https://example.com/thumb.jpg", ext=".jpg")
        post_data = _create_base_post_data(thumbnail=thumbnail)

        content = b"fake image data"
        mock_response = _setup_mock_response(content)
        mock_client.stream.return_value.__enter__.return_value = mock_response

        # Act
        result = downloader.download_all_content(post_data, post_directory)

        # Assert
        assert result is True
        mock_client.stream.assert_called_with("GET", "https://example.com/thumb.jpg")

        thumbnail_path = Path(post_directory) / "0000_thumb.jpg"
        assert thumbnail_path.exists()

        with open(thumbnail_path, "rb") as f:
            assert f.read() == content

    def test_download_all_content_with_photo_gallery(
        self, mock_client: MagicMock, downloader: FantiaFileDownloader, post_directory: str
    ) -> None:
        """写真ギャラリー付き投稿のダウンロードテスト。

        前提: FantiaPhotoGalleryを含むFantiaPostData
        アクション: download_all_content実行
        期待結果: 全写真が連番でダウンロード・保存される
        """
        # Arrange
        gallery = FantiaPhotoGallery(
            id="gallery1",
            title="テストギャラリー",
            comment="ギャラリーコメント",
            photos=[
                FantiaURL(url="https://example.com/photo1.jpg", ext=".jpg"),
                FantiaURL(url="https://example.com/photo2.png", ext=".png"),
            ],
        )
        post_data = _create_base_post_data(contents_photo_gallery=[gallery])

        content = b"fake image data"
        mock_response = _setup_mock_response(content)
        mock_client.stream.return_value.__enter__.return_value = mock_response

        # Act
        result = downloader.download_all_content(post_data, post_directory)

        # Assert
        assert result is True

        gallery_dir = Path(post_directory) / "gallery1_テストギャラリー"
        photo1_path = gallery_dir / "000.jpg"
        photo2_path = gallery_dir / "001.png"
        assert gallery_dir.exists()
        assert photo1_path.exists()
        assert photo2_path.exists()

    def test_download_all_content_with_files(
        self, mock_client: MagicMock, downloader: FantiaFileDownloader, post_directory: str
    ) -> None:
        """ファイル付き投稿のダウンロードテスト。

        前提: FantiaFileを含むFantiaPostData
        アクション: download_all_content実行
        期待結果: ファイルが元のファイル名で保存される
        """
        # Arrange
        file_data = FantiaFile(
            id="file1",
            title="テストファイル",
            comment="ファイルコメント",
            url="https://example.com/testfile.zip",
            name="testfile.zip",
        )
        post_data = _create_base_post_data(contents_files=[file_data])

        content = b"fake file data"
        mock_response = _setup_mock_response(content)
        mock_client.stream.return_value.__enter__.return_value = mock_response

        # Act
        result = downloader.download_all_content(post_data, post_directory)

        # Assert
        assert result is True

        file_dir = Path(post_directory) / "file1_テストファイル"
        downloaded_file = file_dir / "testfile.zip"
        assert file_dir.exists()
        assert downloaded_file.exists()

    def test_download_all_content_network_error(
        self, mock_client: MagicMock, downloader: FantiaFileDownloader, post_directory: str
    ) -> None:
        """ネットワークエラー時のダウンロード失敗テスト。

        前提: ネットワーク接続エラーが発生
        アクション: download_all_content実行
        期待結果: Falseが返され、例外は発生しない（エラーハンドリング）
        """
        # Arrange
        thumbnail = FantiaURL(url="https://invalid-url.com/thumb.jpg", ext=".jpg")
        post_data = _create_base_post_data(thumbnail=thumbnail)

        mock_client.stream.side_effect = Exception("Network error")

        # Act
        result = downloader.download_all_content(post_data, post_directory)

        # Assert
        assert result is False
