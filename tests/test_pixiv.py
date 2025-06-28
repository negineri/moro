"""Pixivモジュールの機能テスト。

このモジュールには以下のユニットテストが含まれています：
1. URL解析と作品IDの抽出
2. PixivDownloaderクラスのメソッド
3. 高レベルのdownload_pixiv_artwork関数
"""

from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from moro.modules.pixiv import (
    PixivDownloader,
    PixivError,
    download_pixiv_artwork,
    extract_artwork_id,
)


# テスト用の共通フィクスチャ
@pytest.fixture
def sample_artwork_detail() -> dict[str, Any]:
    """テスト用のサンプルイラスト詳細データ。"""
    return {
        "id": 123456,
        "title": "Test Artwork",
        "user": {"name": "Test Author"},
        "type": "illust",
        "page_count": 1,
        "meta_single_page": {"original_image_url": "https://i.pximg.net/img-original/test.jpg"},
    }


@pytest.fixture
def sample_multi_page_artwork() -> dict[str, Any]:
    """テスト用の複数ページのサンプルイラスト詳細データ。"""
    return {
        "id": 123456,
        "title": "Test Artwork",
        "user": {"name": "Test Author"},
        "type": "illust",
        "page_count": 2,
        "meta_pages": [
            {"image_urls": {"original": "https://i.pximg.net/img-original/test1.jpg"}},
            {"image_urls": {"original": "https://i.pximg.net/img-original/test2.jpg"}},
        ],
    }


class TestExtractArtworkId:
    """URLからの作品ID抽出をテストするクラス。"""

    def test_extract_artwork_id_standard_url(self) -> None:
        """標準的なPixiv URLからの抽出をテスト。"""
        url = "https://www.pixiv.net/artworks/123456"
        assert extract_artwork_id(url) == 123456

    def test_extract_artwork_id_en_url(self) -> None:
        """英語版Pixiv URLからの抽出をテスト。"""
        url = "https://www.pixiv.net/en/artworks/789012"
        assert extract_artwork_id(url) == 789012

    def test_extract_artwork_id_member_illust_url(self) -> None:
        """member_illust.php URLからの抽出をテスト。"""
        url = "https://www.pixiv.net/member_illust.php?mode=medium&illust_id=345678"
        assert extract_artwork_id(url) == 345678

    def test_extract_artwork_id_short_url(self) -> None:
        """短縮Pixiv URLからの抽出をテスト。"""
        url = "https://www.pixiv.net/i/901234"
        assert extract_artwork_id(url) == 901234

    def test_extract_artwork_id_invalid_url(self) -> None:
        """無効なURLからの抽出をテスト。"""
        with pytest.raises(PixivError, match="Invalid Pixiv URL format"):
            extract_artwork_id("https://example.com/invalid")


class TestPixivDownloader:
    """PixivDownloaderクラスの機能をテスト。"""

    def test_init_without_token(self) -> None:
        """リフレッシュトークンなしでの初期化をテスト。"""
        downloader = PixivDownloader()
        assert downloader.refresh_token is None
        assert not downloader._authenticated

    @patch("moro.modules.pixiv.AppPixivAPI")
    def test_init_with_token_success(self, mock_api_class: MagicMock) -> None:
        """有効なリフレッシュトークンでの初期化をテスト。"""
        # Arrange
        mock_api = MagicMock()
        mock_api_class.return_value = mock_api
        test_token = "valid_token"  # noqa: S105

        # Act
        downloader = PixivDownloader(test_token)

        # Assert
        assert downloader.refresh_token == test_token
        assert downloader._authenticated
        mock_api.auth.assert_called_once_with(refresh_token=test_token)

    @patch("moro.modules.pixiv.AppPixivAPI")
    def test_init_with_token_failure(self, mock_api_class: MagicMock) -> None:
        """無効なリフレッシュトークンでの初期化をテスト。"""
        # Arrange
        mock_api = MagicMock()
        mock_api.auth.side_effect = Exception("Auth failed")
        mock_api_class.return_value = mock_api

        # Act & Assert
        with pytest.raises(PixivError, match="Authentication failed"):
            PixivDownloader("invalid_token")


class TestPixivDownloaderArtworkDetail:
    """PixivDownloaderの作品取得メソッドをテスト。"""

    @patch("moro.modules.pixiv.AppPixivAPI")
    def test_get_artwork_detail_success(self, mock_api_class: MagicMock) -> None:
        """作品詳細の取得が成功するケースをテスト。"""
        # Arrange
        mock_api = MagicMock()
        mock_api.illust_detail.return_value = {
            "illust": {"id": 123456, "title": "Test Artwork", "type": "illust"}
        }
        mock_api_class.return_value = mock_api
        downloader = PixivDownloader()

        # Act
        result = downloader.get_artwork_detail(123456)

        # Assert
        assert result["id"] == 123456
        assert result["title"] == "Test Artwork"
        mock_api.illust_detail.assert_called_once_with(123456)

    @patch("moro.modules.pixiv.AppPixivAPI")
    def test_get_artwork_detail_not_found(self, mock_api_class: MagicMock) -> None:
        """作品が見つからない場合の作品詳細取得をテスト。"""
        # Arrange
        mock_api = MagicMock()
        mock_api.illust_detail.return_value = {}
        mock_api_class.return_value = mock_api
        downloader = PixivDownloader()

        # Act & Assert
        with pytest.raises(PixivError, match="Artwork 123456 not found"):
            downloader.get_artwork_detail(123456)


class TestPixivDownloaderUrlExtraction:
    """PixivDownloaderのURL抽出メソッドをテスト。"""

    def test_get_artwork_urls_single_illust(self, sample_artwork_detail: dict[str, Any]) -> None:
        """単一イラストのURL抽出をテスト。"""
        # Arrange
        downloader = PixivDownloader()

        # Act
        urls = downloader.get_artwork_urls(sample_artwork_detail)

        # Assert
        assert len(urls) == 1
        assert urls[0] == "https://i.pximg.net/img-original/test.jpg"

    def test_get_artwork_urls_multiple_pages(
        self, sample_multi_page_artwork: dict[str, Any]
    ) -> None:
        """複数ページの作品のURL抽出をテスト。"""
        # Arrange
        downloader = PixivDownloader()

        # Act
        urls = downloader.get_artwork_urls(sample_multi_page_artwork)

        # Assert
        assert len(urls) == 2
        assert urls[0] == "https://i.pximg.net/img-original/test1.jpg"
        assert urls[1] == "https://i.pximg.net/img-original/test2.jpg"


class TestPixivDownloaderFileHandling:
    """PixivDownloaderのファイル処理メソッドをテスト。"""

    @pytest.fixture
    def downloader(self) -> PixivDownloader:
        """テスト用のPixivDownloaderインスタンスを作成。"""
        return PixivDownloader()

    @pytest.fixture
    def test_url(self) -> str:
        """テスト用のサンプルURL。"""
        return "https://i.pximg.net/img-original/test.jpg"

    def test_create_filename_single_file(
        self, downloader: PixivDownloader, sample_artwork_detail: dict[str, Any], test_url: str
    ) -> None:
        """単一ファイルのファイル名生成をテスト。"""
        # Act
        filename = downloader.create_filename(sample_artwork_detail, test_url, 0, 1, False)

        # Assert
        assert filename == "123456_Test Artwork_Test Author.jpg"

    def test_create_filename_multiple_files_with_prefix(
        self, downloader: PixivDownloader, sample_artwork_detail: dict[str, Any], test_url: str
    ) -> None:
        """自動プレフィックスを持つ複数ファイルのファイル名生成をテスト。"""
        # Act
        filename = downloader.create_filename(sample_artwork_detail, test_url, 0, 3, True)

        # Assert
        # インデックスは0からスタート、数字は1からのため、0番目は "1_" となる
        assert filename.startswith("1_123456_Test Artwork_Test Author.jpg")

    def test_create_filename_sanitization(self, downloader: PixivDownloader, test_url: str) -> None:
        """無効な文字のファイル名サニタイズをテスト。"""
        # Arrange
        artwork_detail = {"id": 123456, "title": "Test<>Artwork", "user": {"name": "Test/Author"}}

        # Act
        filename = downloader.create_filename(artwork_detail, test_url, 0, 1, False)

        # Assert
        assert filename == "123456_Test__Artwork_Test_Author.jpg"


class TestDownloadPixivArtwork:
    """download_pixiv_artwork関数をテスト。"""

    @pytest.fixture
    def mock_downloader(self) -> MagicMock:
        """モックのPixivDownloaderインスタンスを作成。"""
        mock = MagicMock()
        mock.get_artwork_detail.return_value = {
            "id": 123456,
            "title": "Test",
            "user": {"name": "Author"},
            "type": "illust",
            "page_count": 1,
            "meta_single_page": {"original_image_url": "https://test.jpg"},
        }
        mock.get_artwork_urls.return_value = ["https://test.jpg"]
        mock.create_filename.return_value = "test.jpg"
        mock.download_file.return_value = "/path/to/test.jpg"
        mock.save_metadata.return_value = "/path/to/metadata.json"
        return mock

    @patch("moro.modules.pixiv.PixivDownloader")
    def test_download_pixiv_artwork_success(
        self, mock_downloader_class: MagicMock, mock_downloader: MagicMock
    ) -> None:
        """作品ダウンロードの成功をテスト。"""
        # Arrange
        mock_downloader_class.return_value = mock_downloader
        test_url = "https://www.pixiv.net/artworks/123456"

        # Act
        with patch("moro.modules.pixiv.extract_artwork_id", return_value=123456):
            result = download_pixiv_artwork(
                url=test_url, dest_dir="/output/dir", auto_prefix=False, save_metadata=True
            )

        # Assert
        assert len(result) == 2, "Expected two files (image + metadata)"
        assert "/path/to/test.jpg" in result, "Expected image file in result"
        assert "/path/to/metadata.json" in result, "Expected metadata file in result"
        mock_downloader.get_artwork_detail.assert_called_once_with(123456)
        mock_downloader.download_file.assert_called_once()
        mock_downloader.save_metadata.assert_called_once()

    @patch("moro.modules.pixiv.PixivDownloader")
    def test_download_pixiv_artwork_invalid_url(self, mock_downloader_class: MagicMock) -> None:
        """無効なURLでのダウンロードをテスト。"""
        # Arrange
        error_message = "Invalid URL"

        # Act & Assert
        with patch("moro.modules.pixiv.extract_artwork_id", side_effect=PixivError(error_message)):
            with pytest.raises(PixivError, match=error_message):
                download_pixiv_artwork(url="invalid_url", dest_dir="/output/dir")
