"""Fantiaモジュール独立インフラテスト

外部システム連携部分の単体テスト
Mock使用による外部依存分離
"""

import os
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, Mock

import pytest

from moro.modules.fantia import FantiaClient
from moro.modules.fantia.config import FantiaConfig
from moro.modules.fantia.domain import FantiaPostData, FantiaURL
from moro.modules.fantia.infrastructure import (
    FantiaFileDownloader,
    FantiaPostRepositoryImpl,
)


def _setup_mock_response(content: bytes) -> Mock:
    """共通のモックレスポンス設定"""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.headers = {"Content-Length": str(len(content))}
    mock_response.iter_bytes.return_value = [content]
    mock_response.raise_for_status.return_value = None
    return mock_response


def _create_base_post_data(**overrides: Any) -> FantiaPostData:
    """基本的なFantiaPostDataを作成"""
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


@pytest.mark.unit
class TestFantiaPostRepositoryImpl:
    """FantiaPostRepositoryImpl 単体テスト"""

    @pytest.fixture
    def mock_fantia_client(self) -> MagicMock:
        """FantiaClient のモックオブジェクト"""
        return MagicMock(spec=FantiaClient)

    @pytest.fixture
    def mock_fantia_config(self) -> FantiaConfig:
        """FantiaConfig のインスタンス"""
        return FantiaConfig()

    @pytest.fixture
    def repository(
        self,
        mock_fantia_client: MagicMock,
        mock_fantia_config: FantiaConfig,
    ) -> FantiaPostRepositoryImpl:
        """テスト対象Repository"""
        return FantiaPostRepositoryImpl(mock_fantia_client, mock_fantia_config)

    def test_instantiation_and_basic_methods(
        self, mock_fantia_client: MagicMock, mock_fantia_config: FantiaConfig
    ) -> None:
        """Repository のインスタンス化と基本メソッドの存在確認"""
        repo = FantiaPostRepositoryImpl(mock_fantia_client, mock_fantia_config)

        assert repo is not None
        assert hasattr(repo, "get")
        assert hasattr(repo, "get_many")

    def test_edge_cases(
        self, mock_fantia_client: MagicMock, mock_fantia_config: FantiaConfig
    ) -> None:
        """エッジケースのテスト"""
        repo = FantiaPostRepositoryImpl(mock_fantia_client, mock_fantia_config)

        # 空のIDでは None が返される
        assert repo.get("") is None

        # 空のリストでは空のイテレーターが返される
        assert list(repo.get_many([])) == []

    def test_exception_handling(
        self, mock_fantia_client: MagicMock, mock_fantia_config: FantiaConfig
    ) -> None:
        """例外発生時のエラーハンドリングテスト"""
        # Mock で例外を発生させる
        mock_fantia_client.get.side_effect = Exception("Test error")
        repo = FantiaPostRepositoryImpl(mock_fantia_client, mock_fantia_config)

        result = repo.get("test_post_id")
        assert result is None


# FantiaFanclubRepositoryImpl テストは実装の詳細が不明のため一旦スキップ


@pytest.mark.unit
class TestFantiaFileDownloader:
    """FantiaFileDownloader 単体テスト"""

    @pytest.fixture
    def mock_client(self) -> MagicMock:
        """モックFantiaClientを作成"""
        return MagicMock()

    @pytest.fixture
    def downloader(self, mock_client: MagicMock) -> FantiaFileDownloader:
        """モッククライアントで初期化したFantiaFileDownloader"""
        return FantiaFileDownloader(mock_client)

    @pytest.fixture
    def post_directory(self, tmp_path: Path) -> str:
        """テスト用ポストディレクトリ"""
        directory = str(tmp_path / "test_post")
        os.makedirs(directory, exist_ok=True)
        return directory

    def test_download_all_content_with_thumbnail(
        self, mock_client: MagicMock, downloader: FantiaFileDownloader, post_directory: str
    ) -> None:
        """サムネイル付き投稿のダウンロードテスト"""
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

    def test_download_all_content_empty_content(
        self, downloader: FantiaFileDownloader, post_directory: str
    ) -> None:
        """空コンテンツでもTrueを返すテスト"""
        # Arrange
        post_data = _create_base_post_data(
            contents_photo_gallery=[],
            contents_files=[],
            contents_text=[],
            contents_products=[],
            thumbnail=None,
        )

        # Act
        result = downloader.download_all_content(post_data, post_directory)

        # Assert
        assert result is True

    def test_instantiation(self, mock_client: MagicMock) -> None:
        """ファイルダウンローダーのインスタンス化テスト"""
        downloader = FantiaFileDownloader(mock_client)
        assert downloader is not None
        assert hasattr(downloader, "download_all_content")
