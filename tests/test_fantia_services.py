"""fantia services のテスト."""

from unittest.mock import MagicMock, mock_open, patch

import pytest

from moro.services.fantia_auth import FantiaAuthService
from moro.services.fantia_download import FantiaDownloadService
from moro.services.fantia_file import FantiaFileService


class TestFantiaAuthService:
    """FantiaAuthService クラスのテスト."""

    @patch("moro.services.fantia_auth.check_login")
    def test_ensure_authenticated_already_logged_in(
        self, mock_check_login: MagicMock, mock_fantia_client, fantia_config
    ) -> None:
        """既にログイン済みの場合のテスト."""
        service = FantiaAuthService(fantia_config, mock_fantia_client)

        # 既にログイン済み
        mock_check_login.return_value = True

        result = service.ensure_authenticated()

        assert result is True
        mock_check_login.assert_called_once_with(mock_fantia_client)

    @patch("moro.services.fantia_auth.check_login")
    @patch("moro.services.fantia_auth.webdriver.Chrome")
    @patch("moro.services.fantia_auth.os.makedirs")
    def test_ensure_authenticated_login_required(
        self,
        mock_makedirs: MagicMock,
        mock_chrome: MagicMock,
        mock_check_login: MagicMock,
        mock_fantia_client,
        fantia_test_data,
    ) -> None:
        """ログインが必要な場合のテスト."""
        mock_config = MagicMock()
        mock_config.app.user_data_dir = "/test/userdata"
        service = FantiaAuthService(mock_config, mock_fantia_client)

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

        with patch.object(service, "_login_with_selenium") as mock_login_selenium:
            mock_login_selenium.return_value = True
            result = service.ensure_authenticated()

            assert result is True
            mock_login_selenium.assert_called_once()

    @patch("moro.services.fantia_auth.check_login")
    def test_ensure_authenticated_login_failed(
        self, mock_check_login: MagicMock, mock_fantia_client, fantia_config
    ) -> None:
        """ログイン失敗のテスト."""
        mock_config = MagicMock()
        mock_config.app.user_data_dir = "/test/userdata"
        service = FantiaAuthService(mock_config, mock_fantia_client)

        # ログインしていない
        mock_check_login.return_value = False

        # _login_with_seleniumが失敗するようにモック
        with patch.object(service, "_login_with_selenium") as mock_login_selenium:
            mock_login_selenium.return_value = False

            result = service.ensure_authenticated()

            assert result is False
            mock_login_selenium.assert_called_once()
            mock_check_login.assert_called_once_with(mock_fantia_client)


class TestFantiaDownloadService:
    """FantiaDownloadService クラスのテスト."""

    @patch("builtins.open", new_callable=mock_open)
    @patch("moro.services.fantia_download.os.path.join")
    def test_download_thumbnail_success(
        self,
        mock_join: MagicMock,
        mock_file: MagicMock,
        mock_fantia_client,
        fantia_config,
        fantia_test_data,
    ) -> None:
        """サムネイルダウンロード成功テスト."""
        service = FantiaDownloadService(fantia_config, mock_fantia_client)

        # 投稿データのモック
        post_data = fantia_test_data.create_fantia_post_data(
            thumbnail=fantia_test_data.create_fantia_url(
                url="https://example.com/thumb.jpg", ext=".jpg"
            )
        )

        # モックの設定
        mock_join.return_value = "/test/path/0000_thumb.jpg"
        mock_fantia_client.stream.return_value.__enter__.return_value = MagicMock(
            status_code=200,
            headers={"Content-Length": "1024"},
            iter_bytes=MagicMock(return_value=[b"test"]),
        )

        with patch.object(service, "_perform_download") as mock_perform:
            service.download_thumbnail("/test/path", post_data)
            mock_perform.assert_called_once_with(
                "https://example.com/thumb.jpg", "/test/path/0000_thumb.jpg"
            )
            mock_join.assert_called_once_with("/test/path", "0000_thumb.jpg")

    @patch("builtins.open", new_callable=mock_open)
    @patch("moro.services.fantia_download.os.path.join")
    def test_download_photo_gallery(
        self,
        mock_join: MagicMock,
        mock_file: MagicMock,
        mock_fantia_client,
        fantia_config,
        fantia_test_data,
    ) -> None:
        """フォトギャラリーダウンロードテスト."""
        service = FantiaDownloadService(fantia_config, mock_fantia_client)

        # フォトギャラリーのモック
        photo_gallery = fantia_test_data.create_fantia_photo_gallery(
            photos=[
                fantia_test_data.create_fantia_url(
                    url="https://example.com/photo1.jpg", ext=".jpg"
                ),
                fantia_test_data.create_fantia_url(
                    url="https://example.com/photo2.jpg", ext=".jpg"
                ),
            ],
        )

        mock_join.side_effect = ["/test/comment.txt", "/test/000.jpg", "/test/001.jpg"]

        with patch.object(service, "_perform_download") as mock_perform:
            service.download_photo_gallery("/test/path", photo_gallery)

            # 具体的な呼び出しを検証
            expected_calls = [
                (("https://example.com/photo1.jpg", "/test/000.jpg"),),
                (("https://example.com/photo2.jpg", "/test/001.jpg"),),
            ]
            assert mock_perform.call_count == 2
            assert mock_perform.call_args_list == expected_calls

            # コメントファイルが書き込みされたことを検証
            mock_file.assert_called_with("/test/comment.txt", "w", encoding="utf-8")
            mock_file.return_value.write.assert_called_once_with("Test gallery comment")

    @patch("builtins.open", new_callable=mock_open)
    @patch("moro.services.fantia_download.os.path.join")
    def test_download_file(
        self,
        mock_join: MagicMock,
        mock_file: MagicMock,
        mock_fantia_client,
        fantia_config,
        fantia_test_data,
    ) -> None:
        """ファイルダウンロードテスト."""
        service = FantiaDownloadService(fantia_config, mock_fantia_client)

        # ファイルデータのモック
        file_data = fantia_test_data.create_fantia_file(
            url="https://example.com/test.pdf",
            name="test.pdf",
        )

        mock_join.side_effect = ["/test/comment.txt", "/test/test.pdf"]

        with patch.object(service, "_perform_download") as mock_perform:
            service.download_file("/test/path", file_data)

            # 具体的な呼び出しを検証
            mock_perform.assert_called_once_with("https://example.com/test.pdf", "/test/test.pdf")

            # コメントファイルが書き込みされたことを検証
            mock_file.assert_called_with("/test/comment.txt", "w", encoding="utf-8")
            mock_file.return_value.write.assert_called_once_with("Test file comment")

    @patch("builtins.open", new_callable=mock_open)
    @patch("moro.services.fantia_download.os.remove")
    def test_perform_download_success(
        self, mock_remove: MagicMock, mock_file: MagicMock, mock_fantia_client, fantia_config
    ) -> None:
        """ダウンロード実行成功テスト."""
        service = FantiaDownloadService(fantia_config, mock_fantia_client)

        # レスポンスのモック
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {"Content-Length": "4"}
        mock_response.iter_bytes.return_value = [b"test"]
        mock_fantia_client.stream.return_value.__enter__.return_value = mock_response

        # 実行
        service._perform_download("https://example.com/test.jpg", "/test/test.jpg")

        # 検証
        mock_fantia_client.stream.assert_called_once_with("GET", "https://example.com/test.jpg")
        mock_file.assert_called_once_with("/test/test.jpg", "wb")

        # ファイルの書き込みを検証
        mock_file.return_value.write.assert_called_once_with(b"test")

        # 一時ファイルが削除されていないことを検証
        mock_remove.assert_not_called()

    @patch("builtins.open", new_callable=mock_open)
    @patch("moro.services.fantia_download.os.remove")
    def test_perform_download_network_error(
        self, mock_remove: MagicMock, mock_file: MagicMock, mock_fantia_client, fantia_config
    ) -> None:
        """ダウンロード実行ネットワークエラーテスト."""
        service = FantiaDownloadService(fantia_config, mock_fantia_client)

        # ネットワークエラーをシミュレート
        mock_fantia_client.stream.side_effect = Exception("Network error")

        # 例外が発生することを検証
        with pytest.raises(Exception, match="Network error"):
            service._perform_download("https://example.com/test.jpg", "/test/test.jpg")

        # ファイルが作成されないことを検証
        mock_file.assert_not_called()
        mock_remove.assert_not_called()


class TestFantiaFileService:
    """FantiaFileService クラスのテスト."""

    @patch("moro.services.fantia_file.os.makedirs")
    @patch("moro.services.fantia_file.os.path.join")
    @patch("moro.services.fantia_file.sanitize_filename")
    def test_create_post_directory(
        self, mock_sanitize: MagicMock, mock_join: MagicMock, mock_makedirs: MagicMock,
        fantia_config, fantia_test_data
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
        post_data = fantia_test_data.create_fantia_post_data(
            id="12345",
            title="Test Post Title",
            creator_id="creator123",
            creator_name="Test Creator",
        )

        # 実行
        result = service.create_post_directory(post_data)

        # 検証
        expected_path = (
            "/test/working/downloads/fantia/creator123/12345_Test_Post_Title_202301011200"
        )
        assert result == expected_path
        mock_makedirs.assert_called_once_with(expected_path, exist_ok=True)
        # sanitize_filenameの呼び出しを検証（実際のフォーマットは実装依存）
        mock_sanitize.assert_called_once()

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
