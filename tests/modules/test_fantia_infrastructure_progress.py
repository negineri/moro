"""Tests for FantiaFileDownloader progress callback functionality."""

from unittest.mock import MagicMock, mock_open, patch

import pytest

from moro.modules.fantia.domain import (
    FantiaFile,
    FantiaPhotoGallery,
    FantiaPostData,
    FantiaURL,
)
from moro.modules.fantia.infrastructure import FantiaFileDownloader


class TestFantiaFileDownloaderProgress:
    """FantiaFileDownloaderの進捗コールバック機能のテスト."""

    @pytest.fixture
    def mock_downloader(self) -> FantiaFileDownloader:
        """FantiaFileDownloaderのモックを作成."""
        mock_client = MagicMock()
        return FantiaFileDownloader(mock_client)

    @pytest.fixture
    def mock_post_data(self) -> FantiaPostData:
        """テスト用のFantiaPostDataを作成."""
        # サムネイル
        thumbnail = FantiaURL(
            url="https://example.com/thumb.jpg",
            ext=".jpg"
        )

        # 写真ギャラリー
        photos = [
            FantiaURL(url="https://example.com/photo1.jpg", ext=".jpg"),
            FantiaURL(url="https://example.com/photo2.jpg", ext=".jpg"),
        ]
        gallery = FantiaPhotoGallery(
            id="gallery1",
            title="Test Gallery",
            comment="Test gallery comment",
            photos=photos
        )

        # ファイル
        file_content = FantiaFile(
            id="file1",
            title="Test File",
            url="https://example.com/file.pdf",
            name="document.pdf",
            comment="Test file comment"
        )

        return FantiaPostData(
            id="123",
            title="Test Post",
            creator_name="Test Creator",
            creator_id="creator123",
            contents=[gallery, file_content],
            contents_photo_gallery=[gallery],
            contents_files=[file_content],
            contents_text=[],
            contents_products=[],
            posted_at=1609459200,  # 2021-01-01
            converted_at=1609459200,
            comment="Test post comment",
            thumbnail=thumbnail
        )

    @patch('moro.modules.fantia.infrastructure.FantiaFileDownloader.save_post_contents_meta')
    @patch('moro.modules.fantia.infrastructure.FantiaFileDownloader.save_post_comment')
    @patch('moro.modules.fantia.infrastructure.FantiaFileDownloader._perform_download')
    @patch('builtins.open', new_callable=mock_open)
    @patch('os.makedirs')
    def test_download_all_content_with_progress_callback(
        self,
        mock_makedirs: MagicMock,
        mock_file_open: MagicMock,
        mock_perform_download: MagicMock,
        mock_save_comment: MagicMock,
        mock_save_meta: MagicMock,
        mock_downloader: FantiaFileDownloader,
        mock_post_data: FantiaPostData
    ) -> None:
        """進捗コールバック付きでのdownload_all_content動作テスト."""
        downloaded_files: list[str] = []

        def progress_callback(filename: str) -> None:
            downloaded_files.append(filename)

        # _perform_downloadが成功するようにモック
        mock_perform_download.return_value = None

        # テスト実行
        import tempfile
        with tempfile.TemporaryDirectory() as temp_dir:
            result = mock_downloader.download_all_content(
                mock_post_data,
                temp_dir,
                progress_callback
            )

        # 結果検証
        assert result is True

        # 期待されるファイルがコールバックされたか確認
        expected_files = [
            "0000_thumb.jpg",  # サムネイル
            "000.jpg",         # 写真1
            "001.jpg",         # 写真2
            "document.pdf"     # ファイル
        ]

        assert len(downloaded_files) == len(expected_files)
        for expected_file in expected_files:
            assert expected_file in downloaded_files

    @patch('moro.modules.fantia.infrastructure.FantiaFileDownloader._perform_download')
    def test_download_thumbnail_with_progress_callback(
        self,
        mock_perform_download: MagicMock,
        mock_downloader: FantiaFileDownloader,
        mock_post_data: FantiaPostData
    ) -> None:
        """サムネイルダウンロードの進捗コールバックテスト."""
        downloaded_files: list[str] = []

        def progress_callback(filename: str) -> None:
            downloaded_files.append(filename)

        mock_perform_download.return_value = None

        import tempfile
        with tempfile.TemporaryDirectory() as temp_dir:
            mock_downloader.download_thumbnail(temp_dir, mock_post_data, progress_callback)

        assert len(downloaded_files) == 1
        assert downloaded_files[0] == "0000_thumb.jpg"

    @patch('moro.modules.fantia.infrastructure.FantiaFileDownloader._perform_download')
    def test_download_thumbnail_no_callback(
        self,
        mock_perform_download: MagicMock,
        mock_downloader: FantiaFileDownloader,
        mock_post_data: FantiaPostData
    ) -> None:
        """サムネイルダウンロード（コールバックなし）のテスト."""
        mock_perform_download.return_value = None

        # コールバックなしで実行（エラーが起きないことを確認）
        import tempfile
        with tempfile.TemporaryDirectory() as temp_dir:
            mock_downloader.download_thumbnail(temp_dir, mock_post_data, None)

        # _perform_downloadが呼ばれたことを確認
        mock_perform_download.assert_called_once()

    @patch('moro.modules.fantia.infrastructure.FantiaFileDownloader._perform_download')
    @patch('builtins.open', new_callable=mock_open)
    def test_download_file_with_progress_callback(
        self,
        mock_file_open: MagicMock,
        mock_perform_download: MagicMock,
        mock_downloader: FantiaFileDownloader
    ) -> None:
        """ファイルダウンロードの進捗コールバックテスト."""
        downloaded_files: list[str] = []

        def progress_callback(filename: str) -> None:
            downloaded_files.append(filename)

        mock_perform_download.return_value = None

        file_content = FantiaFile(
            id="file1",
            title="Test File",
            url="https://example.com/test.pdf",
            name="test.pdf",
            comment="Test comment"
        )

        import tempfile
        with tempfile.TemporaryDirectory() as temp_dir:
            mock_downloader.download_file(temp_dir, file_content, progress_callback)

        assert len(downloaded_files) == 1
        assert downloaded_files[0] == "test.pdf"

    @patch('moro.modules.fantia.infrastructure.FantiaFileDownloader._perform_download')
    @patch('builtins.open', new_callable=mock_open)
    def test_download_photo_gallery_with_progress_callback(
        self,
        mock_file_open: MagicMock,
        mock_perform_download: MagicMock,
        mock_downloader: FantiaFileDownloader
    ) -> None:
        """写真ギャラリーダウンロードの進捗コールバックテスト."""
        downloaded_files: list[str] = []

        def progress_callback(filename: str) -> None:
            downloaded_files.append(filename)

        mock_perform_download.return_value = None

        photos = [
            FantiaURL(url="https://example.com/photo1.jpg", ext=".jpg"),
            FantiaURL(url="https://example.com/photo2.png", ext=".png"),
            FantiaURL(url="https://example.com/photo3.gif", ext=".gif"),
        ]
        gallery = FantiaPhotoGallery(
            id="gallery1",
            title="Test Gallery",
            comment="Test comment",
            photos=photos
        )

        import tempfile
        with tempfile.TemporaryDirectory() as temp_dir:
            mock_downloader.download_photo_gallery(temp_dir, gallery, progress_callback)

        assert len(downloaded_files) == 3
        assert downloaded_files[0] == "000.jpg"
        assert downloaded_files[1] == "001.png"
        assert downloaded_files[2] == "002.gif"

    def test_no_thumbnail_no_callback(
        self,
        mock_downloader: FantiaFileDownloader
    ) -> None:
        """サムネイルなし時の動作テスト."""
        downloaded_files: list[str] = []

        def progress_callback(filename: str) -> None:
            downloaded_files.append(filename)

        post_data_no_thumb = FantiaPostData(
            id="123",
            title="Test Post",
            creator_name="Test Creator",
            creator_id="creator123",
            contents=[],
            contents_photo_gallery=[],
            contents_files=[],
            contents_text=[],
            contents_products=[],
            posted_at=1609459200,
            converted_at=1609459200,
            comment="Test post comment",
            thumbnail=None  # サムネイルなし
        )

        import tempfile
        with tempfile.TemporaryDirectory() as temp_dir:
            mock_downloader.download_thumbnail(temp_dir, post_data_no_thumb, progress_callback)

        # サムネイルがないのでコールバックは呼ばれない
        assert len(downloaded_files) == 0
