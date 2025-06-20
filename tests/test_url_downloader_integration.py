"""URLダウンローダーの統合テスト（ZIP機能含む）."""

import os
import zipfile
from pathlib import Path
from unittest import mock
from unittest.mock import MagicMock

from moro.modules.url_downloader import download_from_url_list


class TestUrlDownloaderIntegration:
    """URLダウンローダー統合テスト."""

    @mock.patch("moro.modules.url_downloader.download_content")
    def test_download_to_directory(self, mock_download: MagicMock, tmp_path: Path) -> None:
        """ディレクトリへのダウンロードを確認するテスト."""
        # URLリストファイルを作成
        url_list_path = os.path.join(tmp_path, "urls.txt")
        urls = [
            "https://example.com/file1.txt",
            "https://example.org/file2.pdf",
        ]
        with open(url_list_path, "w", encoding="utf-8") as f:
            f.write("\n".join(urls))

        # ダウンロードコンテンツをモック
        mock_download.side_effect = [b"content1", b"content2"]

        # 出力ディレクトリ
        output_dir = os.path.join(tmp_path, "downloads")

        # テスト実行
        result = download_from_url_list(url_list_path, output_dir)

        # 検証
        assert len(result) == 2
        assert all(os.path.exists(path) for path in result)
        assert os.path.exists(os.path.join(output_dir, "file_1.txt"))
        assert os.path.exists(os.path.join(output_dir, "file_2.pdf"))

    @mock.patch("moro.modules.url_downloader.download_content")
    def test_download_to_zip(self, mock_download: MagicMock, tmp_path: Path) -> None:
        """ZIPファイルへのダウンロードを確認するテスト."""
        # URLリストファイルを作成
        url_list_path = os.path.join(tmp_path, "urls.txt")
        urls = [
            "https://example.com/file1.txt",
            "https://example.org/file2.pdf",
        ]
        with open(url_list_path, "w", encoding="utf-8") as f:
            f.write("\n".join(urls))

        # ダウンロードコンテンツをモック
        mock_download.side_effect = [b"content1", b"content2"]

        # 出力ZIPファイル
        output_zip = os.path.join(tmp_path, "output.zip")

        # テスト実行
        result = download_from_url_list(url_list_path, output_zip)

        # 検証
        assert len(result) == 1
        assert result[0] == output_zip
        assert os.path.exists(output_zip)

        # ZIP内容の検証
        with zipfile.ZipFile(output_zip, "r") as zf:
            namelist = zf.namelist()
            assert len(namelist) == 2
            assert "file_1.txt" in namelist
            assert "file_2.pdf" in namelist
            assert zf.read("file_1.txt") == b"content1"
            assert zf.read("file_2.pdf") == b"content2"

    @mock.patch("moro.modules.url_downloader.download_content")
    def test_download_to_zip_with_prefix(self, mock_download: MagicMock, tmp_path: Path) -> None:
        """自動プレフィックス付きZIPファイルへのダウンロードを確認するテスト."""
        # URLリストファイルを作成
        url_list_path = os.path.join(tmp_path, "urls.txt")
        urls = [
            "https://example.com/file1.txt",
            "https://example.org/file2.pdf",
        ]
        with open(url_list_path, "w", encoding="utf-8") as f:
            f.write("\n".join(urls))

        # ダウンロードコンテンツをモック
        mock_download.side_effect = [b"content1", b"content2"]

        # 出力ZIPファイル
        output_zip = os.path.join(tmp_path, "output.zip")

        # テスト実行 - 自動プレフィックスあり
        _ = download_from_url_list(url_list_path, output_zip, auto_prefix=True)

        # 検証
        assert os.path.exists(output_zip)

        # ZIP内容の検証
        with zipfile.ZipFile(output_zip, "r") as zf:
            namelist = zf.namelist()
            assert len(namelist) == 2

            # プレフィックス形式の確認（数字で始まるファイルがある）
            assert any(name.startswith(("1_", "01_")) for name in namelist)
            assert any(name.startswith(("2_", "02_")) for name in namelist)
