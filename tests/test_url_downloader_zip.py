"""URLダウンローダーのZIP圧縮機能に関するテスト."""

import os
import tempfile
import zipfile
from pathlib import Path
from unittest import mock
from unittest.mock import MagicMock, patch

from moro.modules.url_downloader import (
    download_from_url_list,
    is_zip_path,
    process_files_to_zip,
)


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
        zip_path = os.path.join(tmp_path, "empty.zip")
        source_files: list[str] = []

        # 空のリストでもZIPファイルを作成できるか
        result = process_files_to_zip(source_files, zip_path)

        # ZIP作成成功の確認
        assert result == zip_path
        assert os.path.exists(zip_path)

        # 空のZIPファイルの確認
        with zipfile.ZipFile(zip_path, "r") as zf:
            assert len(zf.namelist()) == 0

    def test_process_files_to_zip_with_files(self, tmp_path: Path) -> None:
        """テストファイルのリストを正しくZIP圧縮できることを確認."""
        # テストファイルを作成
        test_files = []
        for i in range(3):
            file_path = os.path.join(tmp_path, f"file{i}.txt")
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(f"Test content {i}")
            test_files.append(file_path)

        # ZIPファイルを作成
        zip_path = os.path.join(tmp_path, "test.zip")
        result = process_files_to_zip(test_files, zip_path)

        # ZIP作成成功の確認
        assert result == zip_path
        assert os.path.exists(zip_path)

        # ZIPの内容を確認
        with zipfile.ZipFile(zip_path, "r") as zf:
            namelist = zf.namelist()
            assert len(namelist) == 3

            # 全ファイルが存在し内容が正しいことを確認
            for i, orig_path in enumerate(test_files):
                filename = os.path.basename(orig_path)
                assert filename in namelist

                # 内容の検証
                content = zf.read(filename).decode("utf-8")
                assert content == f"Test content {i}"


class TestDownloadFromUrlListZip:
    """ZIPモードでのURLリストからのダウンロード機能のテスト."""

    @mock.patch("moro.modules.url_downloader.download_content")
    @mock.patch("moro.modules.url_downloader.save_content")
    @mock.patch("moro.modules.url_downloader.read_url_list")
    @mock.patch("moro.modules.url_downloader.process_files_to_zip")
    @mock.patch("moro.modules.url_downloader.tempfile.mkdtemp")
    @mock.patch("moro.modules.url_downloader.shutil.rmtree")
    def test_download_to_zip_basic(
        self,
        mock_rmtree: MagicMock,
        mock_mkdtemp: MagicMock,
        mock_process_to_zip: MagicMock,
        mock_read: MagicMock,
        mock_save: MagicMock,
        mock_download: MagicMock,
    ) -> None:
        """基本的なZIPへのダウンロードが正しく動作することを確認."""
        # モックの設定
        urls = [
            "https://example.com/file1.txt",
            "https://example.org/file2.pdf",
        ]
        mock_read.return_value = urls
        mock_download.return_value = b"test content"

        # 一時ディレクトリのモック
        temp_dir = tempfile.mkdtemp()
        mock_mkdtemp.return_value = temp_dir

        # 保存されるファイルパスをキャプチャ
        _ = [os.path.join(temp_dir, "file_1.txt"), os.path.join(temp_dir, "file_2.pdf")]

        def _save_content_mock(content: bytes, dest_dir: str, filename: str) -> str:
            return os.path.join(dest_dir, filename)

        mock_save.side_effect = _save_content_mock
        mock_process_to_zip.return_value = "/path/to/output.zip"

        # テスト実行
        zip_path = "/path/to/output.zip"
        result = download_from_url_list("urls.txt", zip_path)

        # 検証
        assert result == ["/path/to/output.zip"]
        mock_process_to_zip.assert_called_once()
        mock_rmtree.assert_called_once_with(temp_dir)

    @mock.patch("moro.modules.url_downloader.download_content")
    @mock.patch("moro.modules.url_downloader.read_url_list")
    def test_download_to_zip_with_auto_prefix(
        self,
        mock_read: MagicMock,
        mock_download: MagicMock,
    ) -> None:
        """自動プレフィックス付きでZIPモードが正しく動作することを確認."""
        # 一時ディレクトリで実際にファイルを作成してテスト
        with tempfile.TemporaryDirectory() as temp_dir:
            # モックの設定
            urls = [
                "https://example.com/file1.txt",
                "https://example.org/file2.pdf",
            ]
            mock_read.return_value = urls
            mock_download.side_effect = [b"content1", b"content2"]

            # テスト実行
            zip_path = os.path.join(temp_dir, "output.zip")

            # 元の関数の代わりにパッチを当てる
            with patch(
                "moro.modules.url_downloader.process_files_to_zip", autospec=True
            ) as mock_zip:
                # ZIPファイル作成をモック
                mock_zip.return_value = zip_path
                download_from_url_list("urls.txt", zip_path, auto_prefix=True)

                # process_files_to_zipへの引数を検証
                args = mock_zip.call_args[0]
                temp_files = args[0]  # 最初の引数が一時ファイルリスト

                # ファイル名形式の確認
                assert len(temp_files) == 2
                assert os.path.basename(temp_files[0]).startswith("1_") or os.path.basename(
                    temp_files[0]
                ).startswith("01_")
                assert os.path.basename(temp_files[1]).startswith("2_") or os.path.basename(
                    temp_files[1]
                ).startswith("02_")
