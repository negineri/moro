"""URLダウンローダーモジュールの統合テスト（リファクタリング版）."""

import os
import zipfile
from pathlib import Path
from typing import TYPE_CHECKING
from unittest import mock
from unittest.mock import MagicMock

import pytest

if TYPE_CHECKING:
    from collections.abc import Callable
    from typing import Any

from moro.modules.url_downloader import (
    DownloadError,
    download_content,
    download_from_url_list,
    get_filename_with_prefix,
    is_zip_path,
    process_files_to_zip,
    read_url_list,
    save_content,
)


class TestReadUrlList:
    """URLリスト読み込み機能のテスト."""

    def test_read_url_list_empty_file(self, tmp_path: Path) -> None:
        """空のファイルを読み込んだ場合、空のリストを返すことを確認する."""
        test_file = tmp_path / "empty.txt"
        test_file.touch()
        assert read_url_list(str(test_file)) == []

    def test_read_url_list_with_urls(self, tmp_path: Path, sample_urls: list[str]) -> None:
        """URLが記載されたファイルを読み込んだ場合、URLのリストを返すことを確認する."""
        test_file = tmp_path / "urls.txt"
        test_file.write_text("\n".join(sample_urls))
        assert read_url_list(str(test_file)) == sample_urls

    def test_read_url_list_with_empty_lines(self, tmp_path: Path) -> None:
        """空行を含むファイルを読み込んだ場合、空行を除外したURLリストを返すことを確認する."""
        test_file = tmp_path / "urls_with_empty.txt"
        content = "https://example.com\n\nhttps://example.org\n\nhttps://example.net\n"
        test_file.write_text(content)
        expected = [
            "https://example.com",
            "https://example.org",
            "https://example.net",
        ]
        assert read_url_list(str(test_file)) == expected


class TestDownloadContent:
    """コンテンツダウンロード機能のテスト."""

    @mock.patch("moro.modules.url_downloader.httpx.Client")
    def test_download_content_success(self, mock_client: MagicMock) -> None:
        """正常な応答を受け取った場合、コンテンツが返されることを確認する."""
        mock_response = mock.MagicMock()
        mock_response.content = b"test content"
        mock_response.raise_for_status.return_value = None
        mock_client.return_value.__enter__.return_value.get.return_value = mock_response

        result = download_content("https://example.com")

        assert result == b"test content"
        mock_client.assert_called_once()
        mock_client.return_value.__enter__.return_value.get.assert_called_once_with(
            "https://example.com"
        )

    @mock.patch("moro.modules.url_downloader.httpx.Client")
    def test_download_content_http_error(self, mock_client: MagicMock) -> None:
        """HTTPエラーが発生した場合、DownloadErrorが発生することを確認する."""
        mock_response = mock.MagicMock()
        mock_response.raise_for_status.side_effect = Exception("HTTP Error")
        mock_client.return_value.__enter__.return_value.get.return_value = mock_response

        with pytest.raises(DownloadError):
            download_content("https://example.com")

    @mock.patch("moro.modules.url_downloader.httpx.Client")
    def test_download_content_connection_error(self, mock_client: MagicMock) -> None:
        """接続エラーが発生した場合、DownloadErrorが発生することを確認する."""
        mock_client.return_value.__enter__.return_value.get.side_effect = Exception(
            "Connection Error"
        )

        with pytest.raises(DownloadError):
            download_content("https://example.com")


class TestSaveContent:
    """コンテンツ保存機能のテスト."""

    def test_save_content_create_directory(self, tmp_path: Path) -> None:
        """指定されたディレクトリが存在しない場合、ディレクトリを作成することを確認する."""
        dest_dir = tmp_path / "new_dir"
        content = b"test content"
        filename = "test.txt"

        saved_path = save_content(content, str(dest_dir), filename)

        assert dest_dir.exists()
        assert Path(saved_path).is_file()
        assert Path(saved_path).read_bytes() == content

    def test_save_content_existing_directory(self, tmp_path: Path) -> None:
        """指定されたディレクトリが既に存在する場合、そこにファイルを保存することを確認する."""
        dest_dir = tmp_path / "existing_dir"
        dest_dir.mkdir()
        content = b"test content"
        filename = "test.txt"

        saved_path = save_content(content, str(dest_dir), filename)

        assert Path(saved_path).is_file()
        assert Path(saved_path).read_bytes() == content


class TestGetFilenameWithPrefix:
    """ファイル名プレフィックス生成機能のテスト."""

    def test_get_filename_with_prefix_basic(self) -> None:
        """基本的なプレフィックス付きファイル名生成をテスト."""
        url = "https://example.com/sample.txt"
        filename = get_filename_with_prefix(url, 10, 1)
        assert filename == "01_sample.txt"

    def test_get_filename_with_prefix_no_extension(self) -> None:
        """拡張子のないURLからのファイル名生成をテスト."""
        url = "https://example.com/sample"
        filename = get_filename_with_prefix(url, 10, 1)
        assert filename == "01_sample.bin"

    def test_get_filename_with_prefix_query_params(self) -> None:
        """クエリパラメータ付きURLからのファイル名生成をテスト."""
        url = "https://example.com/sample.jpg?size=large"
        filename = get_filename_with_prefix(url, 10, 1)
        assert filename == "01_sample.jpg"

    def test_get_filename_with_prefix_complex_url(self) -> None:
        """複雑なURLからのファイル名生成をテスト."""
        url = "https://example.com/path/to/resource/sample.zip"
        filename = get_filename_with_prefix(url, 100, 99)
        assert filename == "099_sample.zip"


class TestIsZipPath:
    """ZIP保存先パス判定機能のテスト."""

    def test_is_zip_path_with_zip_extension(self) -> None:
        """ZIP拡張子を持つパスを正しく判定することを確認."""
        assert is_zip_path("output.zip") is True
        assert is_zip_path("/path/to/archive.zip") is True

    def test_is_zip_path_with_other_extension(self) -> None:
        """ZIP拡張子以外のパスを正しく判定することを確認."""
        assert is_zip_path("output.txt") is False
        assert is_zip_path("/path/to/dir") is False
        assert is_zip_path("archive.zip.txt") is False

    def test_is_zip_path_case_insensitive(self) -> None:
        """ZIP拡張子の大文字小文字を区別しないことを確認."""
        assert is_zip_path("output.ZIP") is True
        assert is_zip_path("archive.Zip") is True


class TestProcessFilesToZip:
    """ファイルをZIP圧縮する機能のテスト."""

    def test_process_files_to_zip_empty_list(self, tmp_path: Path) -> None:
        """空のファイルリストに対してZIPファイルを作成できることを確認."""
        zip_path = tmp_path / "empty.zip"
        source_files: list[str] = []

        result = process_files_to_zip(source_files, str(zip_path))

        assert result == str(zip_path)
        assert zip_path.exists()

        with zipfile.ZipFile(zip_path, "r") as zf:
            assert len(zf.namelist()) == 0

    def test_process_files_to_zip_error_handling(self, tmp_path: Path) -> None:
        """ZIP作成時の例外処理をテスト."""
        zip_path = tmp_path / "test.zip"
        test_files = ["nonexistent_file.txt"]

        with pytest.raises(OSError, match="Failed to create ZIP file"):
            process_files_to_zip(test_files, str(zip_path))

    def test_process_files_to_zip_with_files(
        self, tmp_path: Path, create_test_files: "Callable[[int, str], list[str]]"
    ) -> None:
        """テストファイルのリストを正しくZIP圧縮できることを確認."""
        test_files = create_test_files(3, "file")
        zip_path = tmp_path / "test.zip"

        result = process_files_to_zip(test_files, str(zip_path))

        assert result == str(zip_path)
        assert zip_path.exists()

        with zipfile.ZipFile(zip_path, "r") as zf:
            namelist = zf.namelist()
            assert len(namelist) == 3

            for i, orig_path in enumerate(test_files):
                filename = os.path.basename(orig_path)
                assert filename in namelist
                content = zf.read(filename).decode("utf-8")
                assert content == f"Test content {i}"


class TestDownloadFromUrlList:
    """URLリストからのダウンロード機能の統合テスト."""

    @mock.patch("moro.modules.url_downloader.download_content")
    @mock.patch("moro.modules.url_downloader.save_content")
    @mock.patch("moro.modules.url_downloader.read_url_list")
    def test_download_from_url_list_success(
        self, mock_read: MagicMock, mock_save: MagicMock, mock_download: MagicMock,
        sample_urls: list[str]
    ) -> None:
        """すべてのURLでダウンロードが成功した場合の動作確認."""
        mock_read.return_value = sample_urls
        mock_download.return_value = b"test content"
        mock_save.side_effect = [
            "/path/to/file_1.txt",
            "/path/to/file_2.pdf",
            "/path/to/file_3.jpg"
        ]

        result = download_from_url_list("urls.txt", "/path/to")

        assert result == ["/path/to/file_1.txt", "/path/to/file_2.pdf", "/path/to/file_3.jpg"]
        assert mock_download.call_count == 3
        assert mock_save.call_count == 3

    @mock.patch("moro.modules.url_downloader.download_content")
    @mock.patch("moro.modules.url_downloader.save_content")
    @mock.patch("moro.modules.url_downloader.read_url_list")
    def test_download_from_url_list_with_failure(
        self, mock_read: MagicMock, mock_save: MagicMock, mock_download: MagicMock,
        sample_urls: list[str]
    ) -> None:
        """一部のURLでダウンロードが失敗した場合の動作確認."""
        mock_read.return_value = sample_urls
        mock_download.side_effect = [
            b"test content",
            DownloadError("Download failed"),
            b"test content 2",
        ]
        mock_save.side_effect = ["/path/to/file_1.txt", "/path/to/file_3.jpg"]

        result = download_from_url_list("urls.txt", "/path/to")

        assert result == ["/path/to/file_1.txt", "/path/to/file_3.jpg"]
        assert mock_download.call_count == 3
        assert mock_save.call_count == 2

    @mock.patch("moro.modules.url_downloader.download_content")
    @mock.patch("moro.modules.url_downloader.read_url_list")
    def test_download_from_url_list_with_prefix(
        self, mock_read: MagicMock, mock_download: MagicMock,
        mock_save_content: "Any"
    ) -> None:
        """プレフィックスが指定された場合の動作確認."""
        urls = ["https://example.com/file.txt"]
        mock_read.return_value = urls
        mock_download.return_value = b"test content"

        with mock.patch("moro.modules.url_downloader.save_content", mock_save_content):
            download_from_url_list("urls.txt", "/path/to", timeout=5.0, prefix="custom")

        assert mock_save_content.saved_filenames == ["custom_1.txt"]
        mock_download.assert_called_once_with(urls[0], timeout=5.0)

    @mock.patch("moro.modules.url_downloader.download_content")
    @mock.patch("moro.modules.url_downloader.read_url_list")
    def test_download_with_auto_prefix(
        self, mock_read: MagicMock, mock_download: MagicMock,
        mock_save_content: "Any", sample_urls: list[str]
    ) -> None:
        """自動プレフィックスが正しく適用されることを確認."""
        mock_read.return_value = sample_urls
        mock_download.return_value = b"test content"

        with mock.patch("moro.modules.url_downloader.save_content", mock_save_content):
            download_from_url_list("urls.txt", "/path/to", auto_prefix=True)

        expected_filenames = ["1_file1.txt", "2_file2.pdf", "3_file3.jpg"]
        assert mock_save_content.saved_filenames == expected_filenames

    @mock.patch("moro.modules.url_downloader.download_content")
    @mock.patch("moro.modules.url_downloader.read_url_list")
    def test_download_with_auto_prefix_double_digit(
        self, mock_read: MagicMock, mock_download: MagicMock,
        mock_save_content: "Any", large_url_list: list[str]
    ) -> None:
        """10個以上のURLで自動プレフィックスが正しく適用されることを確認."""
        mock_read.return_value = large_url_list
        mock_download.return_value = b"test content"

        with mock.patch("moro.modules.url_downloader.save_content", mock_save_content):
            download_from_url_list("urls.txt", "/path/to", auto_prefix=True)

        assert mock_save_content.saved_filenames[0] == "01_file1.txt"
        assert mock_save_content.saved_filenames[10] == "11_file11.txt"
        assert len(mock_save_content.saved_filenames) == 11


class TestDownloadFromUrlListZip:
    """ZIPモードでのURLリストからのダウンロード機能のテスト."""

    @mock.patch("moro.modules.url_downloader.download_content")
    def test_download_to_zip_basic(
        self, mock_download: MagicMock, tmp_path: Path,
        create_url_file: "Callable[[list[str], str], str]", sample_urls: list[str]
    ) -> None:
        """基本的なZIPへのダウンロードが正しく動作することを確認."""
        url_file = create_url_file(sample_urls, "urls.txt")
        mock_download.side_effect = [b"content1", b"content2", b"content3"]
        zip_path = tmp_path / "output.zip"

        result = download_from_url_list(url_file, str(zip_path))

        assert result == [str(zip_path)]
        assert zip_path.exists()

        # ZIPファイルの内容を検証し、適切にクリーンアップ
        try:
            with zipfile.ZipFile(zip_path, "r") as zf:
                namelist = zf.namelist()
                assert len(namelist) == 3
                assert "file1.txt" in namelist
                assert "file2.pdf" in namelist
                assert "file3.jpg" in namelist
        finally:
            # テスト終了時に一時ファイルが確実に削除されることを確認
            if zip_path.exists():
                zip_path.unlink()

    @mock.patch("moro.modules.url_downloader.download_content")
    def test_download_to_zip_with_auto_prefix(
        self, mock_download: MagicMock, tmp_path: Path,
        create_url_file: "Callable[[list[str], str], str]", sample_urls: list[str]
    ) -> None:
        """自動プレフィックス付きでZIPモードが正しく動作することを確認."""
        url_file = create_url_file(sample_urls, "urls.txt")
        mock_download.side_effect = [b"content1", b"content2", b"content3"]
        zip_path = tmp_path / "output.zip"

        result = download_from_url_list(url_file, str(zip_path), auto_prefix=True)

        assert result == [str(zip_path)]
        assert zip_path.exists()

        try:
            with zipfile.ZipFile(zip_path, "r") as zf:
                namelist = zf.namelist()
                assert len(namelist) == 3
                # プレフィックス形式の確認
                assert any(name.startswith(("1_", "01_")) for name in namelist)
                assert any(name.startswith(("2_", "02_")) for name in namelist)
                assert any(name.startswith(("3_", "03_")) for name in namelist)
        finally:
            # テスト終了時に一時ファイルが確実に削除されることを確認
            if zip_path.exists():
                zip_path.unlink()
