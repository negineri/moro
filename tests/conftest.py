"""共通のテスト設定とfixture."""

import os
import tempfile
from collections.abc import Callable, Generator
from pathlib import Path
from unittest.mock import MagicMock

import pytest


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
def temp_dir() -> Generator[str, None, None]:
    """一時ディレクトリを作成・削除するfixture."""
    temp_dir_path = tempfile.mkdtemp()
    try:
        yield temp_dir_path
    finally:
        import shutil

        shutil.rmtree(temp_dir_path, ignore_errors=True)
