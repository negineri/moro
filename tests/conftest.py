"""共通のテスト設定とfixture."""

import os
from collections.abc import Callable, Generator
from pathlib import Path
from typing import Any, Union
from unittest.mock import MagicMock

import pytest

from moro.config.settings import ConfigRepository
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
    def create_fantia_config(**kwargs: Any) -> FantiaConfig:
        """FantiaConfigのテストデータを作成."""
        defaults: dict[str, Any] = {
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
    def create_fantia_post_data(**kwargs: Any) -> FantiaPostData:
        """FantiaPostDataのテストデータを作成."""
        defaults: dict[str, Any] = {
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
    def create_fantia_file(**kwargs: Any) -> FantiaFile:
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
    def create_fantia_photo_gallery(**kwargs: Any) -> FantiaPhotoGallery:
        """FantiaPhotoGalleryのテストデータを作成."""
        defaults: dict[str, Any] = {
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
    def create_fantia_url(**kwargs: Any) -> FantiaURL:
        """FantiaURLのテストデータを作成."""
        defaults = {
            "url": "https://example.com/image.jpg",
            "ext": ".jpg",
        }
        defaults.update(kwargs)
        return FantiaURL(**defaults)

    @staticmethod
    def create_post_json_data(**kwargs: Any) -> dict[str, Any]:
        """投稿JSONデータのテストデータを作成."""
        defaults: dict[str, Any] = {
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
def config_repository() -> ConfigRepository:
    """ConfigRepositoryのテスト用fixture."""
    return ConfigRepository()


class FileCleanupManager:
    """ファイルクリーンアップを管理するクラス.

    このクラスは、テスト中に作成されたファイルやディレクトリを
    追跡し、テスト終了後に自動的にクリーンアップします。

    主な機能:
    - ファイルとディレクトリの両方をサポート
    - 複数のファイル/ディレクトリを一括管理
    - クリーンアップ失敗時もテストを継続（警告のみ）
    - 存在しないファイルの削除要求を安全に処理

    使用方法:
        manager = FileCleanupManager()
        manager.register("/tmp/test_file.txt")  # ファイルを登録
        manager.register("/tmp/test_dir")       # ディレクトリを登録
        manager.cleanup()                       # 一括クリーンアップ
    """

    def __init__(self) -> None:
        """クリーンアップマネージャーを初期化."""
        self.files_to_cleanup: list[Path] = []

    def register(self, file_path: Union[str, Path]) -> None:
        """クリーンアップ対象ファイルまたはディレクトリを登録.

        Args:
            file_path: 削除対象のファイルまたはディレクトリパス
                      文字列またはPathオブジェクトを受け付ける

        Note:
            - 同じパスを複数回登録しても問題ありません
            - 存在しないパスを登録しても問題ありません
            - ファイルとディレクトリの両方を登録可能
        """
        self.files_to_cleanup.append(Path(file_path))

    def cleanup(self) -> None:
        """登録されたファイルとディレクトリをクリーンアップ.

        以下の順序で処理されます:
        1. 登録されたパスの存在確認
        2. ファイルの場合: unlink() で削除
        3. ディレクトリの場合: shutil.rmtree() で再帰削除
        4. 削除失敗時: OSError をキャッチして継続

        Note:
            - クリーンアップ失敗はテストの失敗にはなりません
            - 権限エラーや使用中ファイルでも安全に処理されます
            - 存在しないファイルの削除要求は無視されます
        """
        for file_path in self.files_to_cleanup:
            try:
                if file_path.exists():
                    if file_path.is_file():
                        file_path.unlink()
                    elif file_path.is_dir():
                        import shutil
                        shutil.rmtree(file_path)
            except OSError:
                # クリーンアップ失敗は警告のみ（テスト失敗にはしない）
                # 権限エラー、使用中ファイル、ネットワークエラーなどを想定
                pass


@pytest.fixture
def cleanup_files() -> Generator[FileCleanupManager, None, None]:
    """テスト終了時にファイルをクリーンアップするfixture.

    このfixtureは、テスト中に作成されたファイルやディレクトリを
    テスト終了後に自動的にクリーンアップします。

    注意: 通常のテストでは pytest の tmp_path fixture を使用してください。
    このfixtureは、以下のような特殊な場合にのみ使用してください：

    使用例1: 手動でファイルを作成する場合
    ----------------------------------------
    def test_manual_file_creation(cleanup_files):
        # 手動でファイルを作成
        manual_file = Path("/tmp/manual_test_file.txt")
        manual_file.write_text("manual content")

        # クリーンアップ対象に登録
        cleanup_files.register(manual_file)

        # テスト実行
        assert manual_file.exists()
        # テスト終了後、自動的にファイルが削除される

    使用例2: システム全体の一時ディレクトリにファイル作成
    ------------------------------------------------
    def test_system_wide_file(cleanup_files):
        # システム全体の一時ディレクトリにファイル作成
        system_file = Path("/tmp/system_test_file.txt")
        system_file.write_text("system content")

        # クリーンアップ対象に登録
        cleanup_files.register(system_file)

        # テスト実行...

    使用例3: 外部ツールが作成するファイルの場合
    ----------------------------------------
    def test_external_tool_output(cleanup_files):
        # 外部ツールが予期しないファイルを作成する場合
        output_file = Path("unexpected_output.log")

        # 事前にクリーンアップ対象に登録
        cleanup_files.register(output_file)

        # 外部ツール実行（ファイルが作成される）
        subprocess.run(["external_tool", "--output", str(output_file)])

        # テスト検証
        assert output_file.exists()
        # テスト終了後、自動的にファイルが削除される

    使用例4: ディレクトリのクリーンアップ
    ----------------------------------
    def test_directory_cleanup(cleanup_files):
        # テストディレクトリを作成
        test_dir = Path("/tmp/test_directory")
        test_dir.mkdir(exist_ok=True)

        # ディレクトリ内にファイルを作成
        (test_dir / "file1.txt").write_text("content1")
        (test_dir / "file2.txt").write_text("content2")

        # ディレクトリをクリーンアップ対象に登録
        cleanup_files.register(test_dir)

        # テスト実行
        assert test_dir.exists()
        assert len(list(test_dir.iterdir())) == 2
        # テスト終了後、ディレクトリとその中身が削除される

    使用例5: 複数ファイルの一括クリーンアップ
    ------------------------------------
    def test_multiple_files(cleanup_files):
        # 複数のファイルを作成
        files = []
        for i in range(3):
            file_path = Path(f"/tmp/test_file_{i}.txt")
            file_path.write_text(f"content {i}")
            files.append(file_path)

            # 各ファイルをクリーンアップ対象に登録
            cleanup_files.register(file_path)

        # テスト実行
        for file_path in files:
            assert file_path.exists()
        # テスト終了後、全てのファイルが削除される

    現在のコードベースでは、このfixtureは実際には使用されていません。
    ほとんどのテストでは pytest の tmp_path fixture で十分です。
    """
    manager = FileCleanupManager()
    yield manager
    manager.cleanup()
