"""URLダウンローダーモジュールのユニットテスト."""

import os
from pathlib import Path
from unittest import mock
from unittest.mock import MagicMock

import pytest

from moro.modules.url_downloader import (
    DownloadError,
    download_content,
    download_from_url_list,
    read_url_list,
    save_content,
)


class TestReadUrlList:
    """URLリスト読み込み機能のテスト."""

    def test_read_url_list_empty_file(self, tmp_path: Path) -> None:
        """空のファイルを読み込んだ場合、空のリストを返すことを確認する."""
        test_file: Path = tmp_path / "empty.txt"
        test_file.touch()
        assert read_url_list(str(test_file)) == []

    def test_read_url_list_with_urls(self, tmp_path: Path) -> None:
        """URLが記載されたファイルを読み込んだ場合、URLのリストを返すことを確認する."""
        test_file: Path = tmp_path / "urls.txt"
        urls: list[str] = [
            "https://example.com",
            "https://example.org",
            "https://example.net",
        ]
        test_file.write_text("\n".join(urls))
        assert read_url_list(str(test_file)) == urls

    def test_read_url_list_with_empty_lines(self, tmp_path: Path) -> None:
        """空行を含むファイルを読み込んだ場合、空行を除外したURLリストを返すことを確認する."""
        test_file: Path = tmp_path / "urls_with_empty.txt"
        content: str = """https://example.com

https://example.org

https://example.net
"""
        test_file.write_text(content)
        expected: list[str] = [
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
        # モックの設定
        mock_response = mock.MagicMock()
        mock_response.content = b"test content"
        mock_response.raise_for_status.return_value = None
        mock_client.return_value.__enter__.return_value.get.return_value = mock_response

        # テスト実行
        result: bytes = download_content("https://example.com")

        # 検証
        assert result == b"test content"
        mock_client.assert_called_once()
        mock_client.return_value.__enter__.return_value.get.assert_called_once_with(
            "https://example.com"
        )

    @mock.patch("moro.modules.url_downloader.httpx.Client")
    def test_download_content_http_error(self, mock_client: MagicMock) -> None:
        """HTTPエラーが発生した場合、DownloadErrorが発生することを確認する."""
        # モックの設定
        mock_response = mock.MagicMock()
        mock_response.raise_for_status.side_effect = Exception("HTTP Error")
        mock_client.return_value.__enter__.return_value.get.return_value = mock_response

        # テスト実行と検証
        with pytest.raises(DownloadError):
            download_content("https://example.com")

    @mock.patch("moro.modules.url_downloader.httpx.Client")
    def test_download_content_connection_error(self, mock_client: MagicMock) -> None:
        """接続エラーが発生した場合、DownloadErrorが発生することを確認する."""
        # モックの設定
        mock_client.return_value.__enter__.return_value.get.side_effect = Exception(
            "Connection Error"
        )

        # テスト実行と検証
        with pytest.raises(DownloadError):
            download_content("https://example.com")


class TestSaveContent:
    """コンテンツ保存機能のテスト."""

    def test_save_content_create_directory(self, tmp_path: Path) -> None:
        """指定されたディレクトリが存在しない場合、ディレクトリを作成することを確認する."""
        dest_dir: Path = tmp_path / "new_dir"
        content: bytes = b"test content"
        filename: str = "test.txt"

        # テスト実行
        saved_path: str = save_content(content, str(dest_dir), filename)

        # 検証
        assert os.path.exists(dest_dir)
        assert os.path.isfile(saved_path)
        assert Path(saved_path).read_bytes() == content

    def test_save_content_existing_directory(self, tmp_path: Path) -> None:
        """指定されたディレクトリが既に存在する場合、そこにファイルを保存することを確認する."""
        dest_dir: Path = tmp_path / "existing_dir"
        dest_dir.mkdir()
        content: bytes = b"test content"
        filename: str = "test.txt"

        # テスト実行
        saved_path: str = save_content(content, str(dest_dir), filename)

        # 検証
        assert os.path.isfile(saved_path)
        assert Path(saved_path).read_bytes() == content


class TestDownloadFromUrlList:
    """URLリストからのダウンロード機能のテスト."""

    @mock.patch("moro.modules.url_downloader.download_content")
    @mock.patch("moro.modules.url_downloader.save_content")
    @mock.patch("moro.modules.url_downloader.read_url_list")
    def test_download_from_url_list_all_success(
        self, mock_read: MagicMock, mock_save: MagicMock, mock_download: MagicMock, tmp_path: Path
    ) -> None:
        """すべてのURLでダウンロードが成功した場合、保存されたファイルパスのリストを返すことを確認する."""
        # モックの設定
        urls: list[str] = ["https://example.com", "https://example.org"]
        mock_read.return_value = urls
        mock_download.return_value = b"test content"
        mock_save.side_effect = ["/path/to/file_1.bin", "/path/to/file_2.bin"]

        # テスト実行
        result: list[str] = download_from_url_list("urls.txt", "/path/to")

        # 検証
        assert result == ["/path/to/file_1.bin", "/path/to/file_2.bin"]
        assert mock_read.call_count == 1
        assert mock_download.call_count == 2
        assert mock_save.call_count == 2

    @mock.patch("moro.modules.url_downloader.download_content")
    @mock.patch("moro.modules.url_downloader.save_content")
    @mock.patch("moro.modules.url_downloader.read_url_list")
    def test_download_from_url_list_with_failure(
        self, mock_read: MagicMock, mock_save: MagicMock, mock_download: MagicMock, tmp_path: Path
    ) -> None:
        """一部のURLでダウンロードが失敗した場合、成功したURLのみ処理されることを確認する."""
        # モックの設定
        urls: list[str] = ["https://example.com", "https://example.org", "https://example.net"]
        mock_read.return_value = urls
        mock_download.side_effect = [
            b"test content",
            DownloadError("Download failed"),
            b"test content 2",
        ]
        mock_save.side_effect = ["/path/to/file_1.bin", "/path/to/file_3.bin"]

        # テスト実行
        result: list[str] = download_from_url_list("urls.txt", "/path/to")

        # 検証
        assert result == ["/path/to/file_1.bin", "/path/to/file_3.bin"]
        assert mock_read.call_count == 1
        assert mock_download.call_count == 3
        assert mock_save.call_count == 2

    @mock.patch("moro.modules.url_downloader.download_content")
    @mock.patch("moro.modules.url_downloader.save_content")
    @mock.patch("moro.modules.url_downloader.read_url_list")
    def test_download_from_url_list_with_prefix(
        self, mock_read: MagicMock, mock_save: MagicMock, mock_download: MagicMock, tmp_path: Path
    ) -> None:
        """プレフィックスが指定された場合、ファイル名にプレフィックスが付与されることを確認する."""
        # モックの設定
        urls: list[str] = ["https://example.com/file.txt"]
        mock_read.return_value = urls
        mock_download.return_value = b"test content"

        # ファイル名の検証のためにsave_contentの実装をキャプチャ
        def _save_content_mock(content: bytes, dest_dir: str, filename: str) -> str:
            assert filename == "custom_1.txt"  # プレフィックスが適用されていることを確認
            return os.path.join(dest_dir, filename)

        mock_save.side_effect = _save_content_mock

        # テスト実行
        _ = download_from_url_list("urls.txt", "/path/to", timeout=5.0, prefix="custom")

        # 検証
        mock_download.assert_called_once_with(urls[0], timeout=5.0)
