"""共通のテスト設定とfixture."""

import os
import tempfile
from collections.abc import Callable, Generator
from pathlib import Path
from typing import Union
from unittest.mock import MagicMock

import pytest

from moro.modules.fantia import (
    FantiaConfig,
    FantiaFile,
    FantiaPhotoGallery,
    FantiaPostData,
    FantiaURL,
)


@pytest.fixture
def sample_urls() -> list[str]:
    """テスト用のサンプルURLリスト."""
    return [
        "https://example.com/file1.txt",
        "https://example.org/file2.pdf",
        "https://example.net/file3.jpg",
    ]


@pytest.fixture
def large_url_list() -> list[str]:
    """多数のURLを含むテスト用リスト."""
    return [f"https://example.com/file{i}.txt" for i in range(1, 12)]


@pytest.fixture
def create_url_file(tmp_path: Path) -> Callable[[list[str], str], str]:
    """URLリストファイルを作成するヘルパー."""

    def _create_file(urls: list[str], filename: str = "urls.txt") -> str:
        file_path = tmp_path / filename
        file_path.write_text("\n".join(urls))
        return str(file_path)

    return _create_file


@pytest.fixture
def mock_download_content() -> Callable[[bytes], MagicMock]:
    """download_content関数のモック."""

    def _create_mock(content: bytes = b"test content") -> MagicMock:
        mock = MagicMock()
        mock.return_value = content
        return mock

    return _create_mock


@pytest.fixture
def create_test_files(tmp_path: Path) -> Callable[[int, str], list[str]]:
    """テスト用ファイルを作成するヘルパー."""

    def _create_files(count: int = 3, prefix: str = "file") -> list[str]:
        files: list[str] = []
        for i in range(count):
            file_path = tmp_path / f"{prefix}{i}.txt"
            file_path.write_text(f"Test content {i}")
            files.append(str(file_path))
        return files

    return _create_files


class MockSaveContent:
    """save_content関数のモッククラス."""

    def __init__(self) -> None:
        self.saved_filenames: list[str] = []
        self.saved_paths: list[str] = []

    def __call__(self, _content: bytes, dest_dir: str, filename: str) -> str:
        self.saved_filenames.append(filename)
        path = os.path.join(dest_dir, filename)
        self.saved_paths.append(path)
        return path


@pytest.fixture
def mock_save_content() -> MockSaveContent:
    """save_content関数のモック."""
    return MockSaveContent()


@pytest.fixture
def mock_fantia_client() -> MagicMock:
    """FantiaClientのモック."""
    mock = MagicMock()
    mock.cookies = {}
    mock.timeout = MagicMock()
    mock.timeout.connect = 10.0
    mock.timeout.read = 30.0
    mock.timeout.write = 10.0
    mock.timeout.pool = 5.0
    return mock


@pytest.fixture
def temp_dir() -> Generator[str, None, None]:
    """一時ディレクトリを作成・削除するfixture."""
    temp_dir_path = tempfile.mkdtemp()
    try:
        yield temp_dir_path
    finally:
        import shutil

        shutil.rmtree(temp_dir_path, ignore_errors=True)


# Fantia関連のテストデータファクトリ
class FantiaTestDataFactory:
    """Fantia関連のテストデータを生成するファクトリクラス."""

    # 定数定義
    DEFAULT_POST_ID = "123456"
    DEFAULT_CREATOR_ID = "789"
    DEFAULT_CREATOR_NAME = "Test Creator"
    DEFAULT_POSTED_AT = 1672531200  # 2023-01-01T00:00:00Z
    DEFAULT_CONVERTED_AT = 1672531200

    @staticmethod
    def create_fantia_config(**kwargs) -> FantiaConfig:
        """FantiaConfigのテストデータを作成."""
        defaults = {
            "session_id": "test_session_id",
            "directory": "test/downloads",
            "download_thumb": False,
            "max_retries": 3,
            "timeout_connect": 5.0,
            "concurrent_downloads": 2,
        }
        defaults.update(kwargs)
        return FantiaConfig(**defaults)

    @staticmethod
    def create_fantia_post_data(**kwargs) -> FantiaPostData:
        """FantiaPostDataのテストデータを作成."""
        defaults = {
            "id": FantiaTestDataFactory.DEFAULT_POST_ID,
            "title": "Test Post Title",
            "creator_id": FantiaTestDataFactory.DEFAULT_CREATOR_ID,
            "creator_name": FantiaTestDataFactory.DEFAULT_CREATOR_NAME,
            "contents": [],
            "contents_photo_gallery": [],
            "contents_files": [],
            "contents_text": [],
            "contents_products": [],
            "posted_at": FantiaTestDataFactory.DEFAULT_POSTED_AT,
            "converted_at": FantiaTestDataFactory.DEFAULT_CONVERTED_AT,
            "comment": "Test comment",
            "thumbnail": None,
        }
        defaults.update(kwargs)
        return FantiaPostData(**defaults)

    @staticmethod
    def create_fantia_file(**kwargs) -> FantiaFile:
        """FantiaFileのテストデータを作成."""
        defaults = {
            "id": "file_001",
            "title": "Test File",
            "comment": "Test file comment",
            "url": "https://example.com/test.pdf",
            "name": "test.pdf",
        }
        defaults.update(kwargs)
        return FantiaFile(**defaults)

    @staticmethod
    def create_fantia_photo_gallery(**kwargs) -> FantiaPhotoGallery:
        """FantiaPhotoGalleryのテストデータを作成."""
        defaults = {
            "id": "gallery_001",
            "title": "Test Gallery",
            "comment": "Test gallery comment",
            "photos": [
                FantiaURL(url="https://example.com/image1.jpg", ext=".jpg"),
                FantiaURL(url="https://example.com/image2.png", ext=".png"),
            ],
        }
        defaults.update(kwargs)
        return FantiaPhotoGallery(**defaults)

    @staticmethod
    def create_fantia_url(**kwargs) -> FantiaURL:
        """FantiaURLのテストデータを作成."""
        defaults = {
            "url": "https://example.com/image.jpg",
            "ext": ".jpg",
        }
        defaults.update(kwargs)
        return FantiaURL(**defaults)

    @staticmethod
    def create_post_json_data(**kwargs) -> dict:
        """投稿JSONデータのテストデータを作成."""
        defaults = {
            "id": 123456,
            "title": "Test Post Title",
            "fanclub": {
                "creator_name": FantiaTestDataFactory.DEFAULT_CREATOR_NAME,
                "id": int(FantiaTestDataFactory.DEFAULT_CREATOR_ID),
            },
            "post_contents": [],
            "posted_at": "Sun, 01 Jan 2023 00:00:00 GMT",
            "converted_at": "2023-01-01T00:00:00+00:00",
            "comment": "Test comment",
            "is_blog": False,
            "thumb": {"original": "https://example.com/thumb.jpg"},
        }
        defaults.update(kwargs)
        return defaults


@pytest.fixture
def fantia_test_data() -> FantiaTestDataFactory:
    """Fantiaテストデータファクトリのfixture."""
    return FantiaTestDataFactory()


@pytest.fixture
def fantia_config() -> FantiaConfig:
    """標準的なFantiaConfigのfixture."""
    return FantiaTestDataFactory.create_fantia_config()


@pytest.fixture
def fantia_post_data() -> FantiaPostData:
    """標準的なFantiaPostDataのfixture."""
    return FantiaTestDataFactory.create_fantia_post_data()


# ヘルパー関数
def create_mock_response(
    status_code: int = 200, json_data: Union[dict, None] = None, text: Union[str, None] = None
) -> MagicMock:
    """HTTPレスポンスのモックを作成するヘルパー関数."""
    mock_response = MagicMock()
    mock_response.status_code = status_code
    mock_response.is_success = status_code < 400

    if json_data:
        mock_response.json.return_value = json_data
    if text:
        mock_response.text = text

    return mock_response


def create_mock_stream_response(content: bytes, status_code: int = 200) -> MagicMock:
    """ストリーミングレスポンスのモックを作成するヘルパー関数."""
    mock_response = MagicMock()
    mock_response.status_code = status_code
    mock_response.headers = {"Content-Length": str(len(content))}
    mock_response.iter_bytes.return_value = [content]

    return mock_response


@pytest.fixture
def mock_http_response() -> Callable[[int, Union[dict, None], Union[str, None]], MagicMock]:
    """HTTPレスポンスモック作成のfixture."""
    return create_mock_response


@pytest.fixture
def mock_stream_response() -> Callable[[bytes, int], MagicMock]:
    """ストリーミングレスポンスモック作成のfixture."""
    return create_mock_stream_response
