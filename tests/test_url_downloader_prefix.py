"""連番プレフィックス対応したURLダウンローダーのテスト."""

import os
from unittest import mock
from unittest.mock import MagicMock

from moro.modules.url_downloader import (
    download_from_url_list,
    get_filename_with_prefix,
)


class TestGetFilenameWithPrefix:
    """ファイル名プレフィックス生成機能のテスト."""

    def test_get_filename_with_prefix_basic(self) -> None:
        """基本的なプレフィックス付きファイル名生成をテスト."""
        # URLからファイル名を生成し、プレフィックスを付与
        url = "https://example.com/sample.txt"
        filename = get_filename_with_prefix(url, 10, 1)
        assert filename == "01_sample.txt"

    def test_get_filename_with_prefix_no_extension(self) -> None:
        """拡張子のないURLからのファイル名生成をテスト."""
        # 拡張子のないURLからファイル名を生成
        url = "https://example.com/sample"
        filename = get_filename_with_prefix(url, 10, 1)
        assert filename == "01_sample.bin"

    def test_get_filename_with_prefix_query_params(self) -> None:
        """クエリパラメータ付きURLからのファイル名生成をテスト."""
        # クエリパラメータを含むURLからファイル名を生成
        url = "https://example.com/sample.jpg?size=large"
        filename = get_filename_with_prefix(url, 10, 1)
        assert filename == "01_sample.jpg"

    def test_get_filename_with_prefix_hash(self) -> None:
        """ハッシュ付きURLからのファイル名生成をテスト."""
        # ハッシュを含むURLからファイル名を生成
        url = "https://example.com/sample.pdf#page=1"
        filename = get_filename_with_prefix(url, 10, 1)
        assert filename == "01_sample.pdf"

    def test_get_filename_with_prefix_complex_url(self) -> None:
        """複雑なURLからのファイル名生成をテスト."""
        # 複雑なパス構造を持つURLからファイル名を生成
        url = "https://example.com/path/to/resource/sample.zip"
        filename = get_filename_with_prefix(url, 100, 99)
        assert filename == "099_sample.zip"


class TestDownloadFromUrlListWithPrefix:
    """プレフィックス対応版URLリストダウンロード機能のテスト."""

    @mock.patch("moro.modules.url_downloader.download_content")
    @mock.patch("moro.modules.url_downloader.save_content")
    @mock.patch("moro.modules.url_downloader.read_url_list")
    def test_download_with_auto_prefix(
        self, mock_read: MagicMock, mock_save: MagicMock, mock_download: MagicMock
    ) -> None:
        """自動プレフィックスが正しく適用されることを確認."""
        # モックの設定
        urls = [
            "https://example.com/file1.txt",
            "https://example.org/file2.pdf",
            "https://example.net/file3.jpg",
        ]
        mock_read.return_value = urls
        mock_download.return_value = b"test content"

        # 保存されるファイル名をキャプチャ
        saved_filenames = []

        def _save_content_mock(content: bytes, dest_dir: str, filename: str) -> str:
            saved_filenames.append(filename)
            return os.path.join(dest_dir, filename)

        mock_save.side_effect = _save_content_mock

        # テスト実行（自動プレフィックス）
        _ = download_from_url_list("urls.txt", "/path/to", auto_prefix=True)

        # 検証
        assert saved_filenames == ["1_file1.txt", "2_file2.pdf", "3_file3.jpg"]

    @mock.patch("moro.modules.url_downloader.download_content")
    @mock.patch("moro.modules.url_downloader.save_content")
    @mock.patch("moro.modules.url_downloader.read_url_list")
    def test_download_with_auto_prefix_double_digit(
        self, mock_read: MagicMock, mock_save: MagicMock, mock_download: MagicMock
    ) -> None:
        """10個以上のURLで自動プレフィックスが正しく適用されることを確認."""
        # モックの設定
        urls = [f"https://example.com/file{i}.txt" for i in range(1, 12)]
        mock_read.return_value = urls
        mock_download.return_value = b"test content"

        # 保存されるファイル名をキャプチャ
        saved_filenames = []

        def _save_content_mock(content: bytes, dest_dir: str, filename: str) -> str:
            saved_filenames.append(filename)
            return os.path.join(dest_dir, filename)

        mock_save.side_effect = _save_content_mock

        # テスト実行（自動プレフィックス）
        _ = download_from_url_list("urls.txt", "/path/to", auto_prefix=True)

        # 検証 - 01_file1.txt から 11_file11.txt まで
        assert saved_filenames[0] == "01_file1.txt"
        assert saved_filenames[10] == "11_file11.txt"
        assert len(saved_filenames) == 11
