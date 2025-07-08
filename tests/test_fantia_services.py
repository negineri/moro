"""fantia services のテスト."""

from unittest.mock import MagicMock, mock_open, patch

from moro.modules.fantia import FantiaFile, FantiaPhotoGallery, FantiaPostData, FantiaURL
from moro.services.fantia_auth import FantiaAuthService
from moro.services.fantia_download import FantiaDownloadService
from moro.services.fantia_file import FantiaFileService


class TestFantiaAuthService:
    """FantiaAuthService クラスのテスト."""

    def test_init(self) -> None:
        """初期化テスト."""
        mock_config = MagicMock()
        mock_client = MagicMock()
        service = FantiaAuthService(mock_config, mock_client)
        assert service.config == mock_config
        assert service.client == mock_client

    @patch("moro.services.fantia_auth.check_login")
    def test_ensure_authenticated_already_logged_in(self, mock_check_login: MagicMock) -> None:
        """既にログイン済みの場合のテスト."""
        mock_config = MagicMock()
        mock_client = MagicMock()
        service = FantiaAuthService(mock_config, mock_client)

        # 既にログイン済み
        mock_check_login.return_value = True

        result = service.ensure_authenticated()

        assert result is True
        mock_check_login.assert_called_once_with(mock_client)

    @patch("moro.services.fantia_auth.check_login")
    @patch("moro.services.fantia_auth.webdriver.Chrome")
    @patch("moro.services.fantia_auth.os.makedirs")
    def test_ensure_authenticated_login_required(
        self, mock_makedirs: MagicMock, mock_chrome: MagicMock, mock_check_login: MagicMock
    ) -> None:
        """ログインが必要な場合のテスト."""
        mock_config = MagicMock()
        mock_config.app.user_data_dir = "/test/userdata"
        mock_client = MagicMock()
        service = FantiaAuthService(mock_config, mock_client)

        # 最初はログインしていない
        mock_check_login.return_value = False

        # WebDriverのモック
        mock_driver = MagicMock()
        mock_chrome.return_value.__enter__.return_value = mock_driver
        mock_driver.current_url = "https://fantia.jp/"

        # クッキーのモック
        mock_driver.get_cookies.return_value = [
            {"name": "_session_id", "value": "test_session", "domain": "fantia.jp"}
        ]

        result = service.ensure_authenticated()

        assert result is True
        mock_makedirs.assert_called_once_with("/test/userdata/chrome_userdata", exist_ok=True)

    @patch("moro.services.fantia_auth.check_login")
    def test_ensure_authenticated_login_failed(self, mock_check_login: MagicMock) -> None:
        """ログイン失敗のテスト."""
        mock_config = MagicMock()
        mock_config.app.user_data_dir = "/test/userdata"
        mock_client = MagicMock()
        service = FantiaAuthService(mock_config, mock_client)

        # ログインしていない
        mock_check_login.return_value = False

        # _login_with_seleniumが失敗するようにモック
        with patch.object(service, "_login_with_selenium") as mock_login_selenium:
            mock_login_selenium.return_value = False

            result = service.ensure_authenticated()

            assert result is False
            mock_login_selenium.assert_called_once()


class TestFantiaDownloadService:
    """FantiaDownloadService クラスのテスト."""

    def test_init(self) -> None:
        """初期化テスト."""
        mock_config = MagicMock()
        mock_client = MagicMock()
        service = FantiaDownloadService(mock_config, mock_client)
        assert service.config == mock_config
        assert service.client == mock_client

    @patch("builtins.open", new_callable=mock_open)
    @patch("moro.services.fantia_download.os.path.join")
    def test_download_thumbnail_success(self, mock_join: MagicMock, mock_file: MagicMock) -> None:
        """サムネイルダウンロード成功テスト."""
        mock_config = MagicMock()
        mock_client = MagicMock()
        service = FantiaDownloadService(mock_config, mock_client)

        # 投稿データのモック
        post_data = FantiaPostData(
            id="12345",
            title="Test Post",
            creator_id="creator123",
            creator_name="Test Creator",
            contents=[],
            contents_photo_gallery=[],
            contents_files=[],
            contents_text=[],
            contents_products=[],
            posted_at=1672531200,
            converted_at=1672531200,
            comment="Test comment",
            thumbnail=FantiaURL(url="https://example.com/thumb.jpg", ext=".jpg"),
        )

        # モックの設定
        mock_join.return_value = "/test/path/0000_thumb.jpg"
        mock_client.stream.return_value.__enter__.return_value = MagicMock(
            status_code=200,
            headers={"Content-Length": "1024"},
            iter_bytes=MagicMock(return_value=[b"test"]),
        )

        with patch.object(service, "_perform_download") as mock_perform:
            service.download_thumbnail("/test/path", post_data)
            mock_perform.assert_called_once_with(
                "https://example.com/thumb.jpg", "/test/path/0000_thumb.jpg"
            )

    def test_download_thumbnail_no_thumbnail(self) -> None:
        """サムネイルがない場合のテスト."""
        mock_config = MagicMock()
        mock_client = MagicMock()
        service = FantiaDownloadService(mock_config, mock_client)

        # サムネイルがない投稿データ
        post_data = FantiaPostData(
            id="12345",
            title="Test Post",
            creator_id="creator123",
            creator_name="Test Creator",
            contents=[],
            contents_photo_gallery=[],
            contents_files=[],
            contents_text=[],
            contents_products=[],
            posted_at=1672531200,
            converted_at=1672531200,
            comment="Test comment",
            thumbnail=None,
        )

        # 実行 - 例外が発生しないことを確認
        service.download_thumbnail("/test/path", post_data)

    @patch("builtins.open", new_callable=mock_open)
    @patch("moro.services.fantia_download.os.path.join")
    def test_download_photo_gallery(self, mock_join: MagicMock, mock_file: MagicMock) -> None:
        """フォトギャラリーダウンロードテスト."""
        mock_config = MagicMock()
        mock_client = MagicMock()
        service = FantiaDownloadService(mock_config, mock_client)

        # フォトギャラリーのモック
        photo_gallery = FantiaPhotoGallery(
            id="gallery123",
            title="Test Gallery",
            comment="Test comment",
            photos=[
                FantiaURL(url="https://example.com/photo1.jpg", ext=".jpg"),
                FantiaURL(url="https://example.com/photo2.jpg", ext=".jpg"),
            ],
        )

        mock_join.side_effect = ["/test/comment.txt", "/test/000.jpg", "/test/001.jpg"]

        with patch.object(service, "_perform_download") as mock_perform:
            service.download_photo_gallery("/test/path", photo_gallery)
            assert mock_perform.call_count == 2  # 2つの写真

    @patch("builtins.open", new_callable=mock_open)
    @patch("moro.services.fantia_download.os.path.join")
    def test_download_file(self, mock_join: MagicMock, mock_file: MagicMock) -> None:
        """ファイルダウンロードテスト."""
        mock_config = MagicMock()
        mock_client = MagicMock()
        service = FantiaDownloadService(mock_config, mock_client)

        # ファイルデータのモック
        file_data = FantiaFile(
            id="file123",
            title="Test File",
            comment="Test comment",
            url="https://example.com/test.pdf",
            name="test.pdf",
        )

        mock_join.side_effect = ["/test/comment.txt", "/test/test.pdf"]

        with patch.object(service, "_perform_download") as mock_perform:
            service.download_file("/test/path", file_data)
            mock_perform.assert_called_once_with("https://example.com/test.pdf", "/test/test.pdf")

    @patch("builtins.open", new_callable=mock_open)
    @patch("moro.services.fantia_download.os.remove")
    def test_perform_download_success(self, mock_remove: MagicMock, mock_file: MagicMock) -> None:
        """ダウンロード実行成功テスト."""
        mock_config = MagicMock()
        mock_client = MagicMock()
        service = FantiaDownloadService(mock_config, mock_client)

        # レスポンスのモック
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {"Content-Length": "4"}
        mock_response.iter_bytes.return_value = [b"test"]
        mock_client.stream.return_value.__enter__.return_value = mock_response

        # 実行
        service._perform_download("https://example.com/test.jpg", "/test/test.jpg")

        # 検証
        mock_client.stream.assert_called_once_with("GET", "https://example.com/test.jpg")
        mock_file.assert_called_once_with("/test/test.jpg", "wb")

    @patch("moro.services.fantia_download.os.remove")
    def test_perform_download_404(self, mock_remove: MagicMock) -> None:
        """404エラーのテスト."""
        mock_config = MagicMock()
        mock_client = MagicMock()
        service = FantiaDownloadService(mock_config, mock_client)

        # 404レスポンスのモック
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_client.stream.return_value.__enter__.return_value = mock_response

        # 実行 - 例外が発生しないことを確認
        service._perform_download("https://example.com/test.jpg", "/test/test.jpg")


class TestFantiaFileService:
    """FantiaFileService クラスのテスト."""

    def test_init(self) -> None:
        """初期化テスト."""
        mock_config = MagicMock()
        service = FantiaFileService(mock_config)
        assert service.config == mock_config

    @patch("moro.services.fantia_file.os.makedirs")
    @patch("moro.services.fantia_file.os.path.join")
    @patch("moro.services.fantia_file.sanitize_filename")
    def test_create_post_directory(
        self, mock_sanitize: MagicMock, mock_join: MagicMock, mock_makedirs: MagicMock
    ) -> None:
        """投稿ディレクトリ作成テスト."""
        mock_config = MagicMock()
        mock_config.app.working_dir = "/test/working"
        service = FantiaFileService(mock_config)

        # モックの設定
        mock_sanitize.return_value = "12345_Test_Post_Title_202301011200"
        mock_join.return_value = (
            "/test/working/downloads/fantia/creator123/12345_Test_Post_Title_202301011200"
        )

        # テスト用投稿データ
        post_data = FantiaPostData(
            id="12345",
            title="Test Post Title",
            creator_id="creator123",
            creator_name="Test Creator",
            contents=[],
            contents_photo_gallery=[],
            contents_files=[],
            contents_text=[],
            contents_products=[],
            posted_at=1672531200,
            converted_at=1672531200,
            comment="Test comment",
            thumbnail=None,
        )

        # 実行
        result = service.create_post_directory(post_data)

        # 検証
        expected_path = (
            "/test/working/downloads/fantia/creator123/12345_Test_Post_Title_202301011200"
        )
        assert result == expected_path
        mock_makedirs.assert_called_once_with(expected_path, exist_ok=True)

    @patch("builtins.open", new_callable=mock_open)
    @patch("moro.services.fantia_file.os.path.join")
    def test_save_post_comment(self, mock_join: MagicMock, mock_file: MagicMock) -> None:
        """投稿コメント保存テスト."""
        mock_config = MagicMock()
        service = FantiaFileService(mock_config)

        mock_join.return_value = "/test/dir/comment.txt"

        # 実行
        service.save_post_comment("/test/dir", "Test comment content")

        # 検証
        mock_file.assert_called_once_with("/test/dir/comment.txt", "w", encoding="utf-8")
        mock_file.return_value.write.assert_called_once_with("Test comment content")

    @patch("builtins.open", new_callable=mock_open)
    @patch("moro.services.fantia_file.os.path.join")
    def test_create_content_directory(self, mock_join: MagicMock, mock_file: MagicMock) -> None:
        """コンテンツディレクトリ作成テスト."""
        mock_config = MagicMock()
        service = FantiaFileService(mock_config)

        with patch("moro.services.fantia_file.os.makedirs") as mock_makedirs:
            with patch("moro.services.fantia_file.sanitize_filename") as mock_sanitize:
                mock_sanitize.return_value = "content123_Test_Content"
                mock_join.return_value = "/test/post/content123_Test_Content"

                result = service.create_content_directory(
                    "/test/post", "content123", "Test Content"
                )

                assert result == "/test/post/content123_Test_Content"
                mock_makedirs.assert_called_once_with(
                    "/test/post/content123_Test_Content", exist_ok=True
                )

    @patch("builtins.open", new_callable=mock_open)
    @patch("moro.services.fantia_file.os.path.join")
    def test_get_download_directory(self, mock_join: MagicMock, mock_file: MagicMock) -> None:
        """ダウンロードディレクトリ取得テスト."""
        mock_config = MagicMock()
        mock_config.app.working_dir = "/test/working"
        service = FantiaFileService(mock_config)

        mock_join.return_value = "/test/working/downloads/fantia"

        result = service.get_download_directory()

        assert result == "/test/working/downloads/fantia"
        mock_join.assert_called_once_with("/test/working", "downloads", "fantia")
