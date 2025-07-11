"""fantia download service のテスト."""

from typing import TYPE_CHECKING
from unittest.mock import MagicMock, mock_open, patch

import pytest

from moro.services.fantia_download import FantiaDownloadService

if TYPE_CHECKING:
    from conftest import (
        FantiaFileFactory,
        FantiaPhotoGalleryFactory,
        FantiaPostDataFactory,
        FantiaURLFactory,
    )


class TestFantiaDownloadService:
    """FantiaDownloadService クラスのテスト."""

    def _create_download_service(self, mock_client: MagicMock) -> FantiaDownloadService:
        """ダウンロードサービスのテスト用インスタンスを作成."""
        mock_config = MagicMock()
        return FantiaDownloadService(mock_config, mock_client)

    @patch("builtins.open", new_callable=mock_open)
    def test_download_thumbnail_success(
        self,
        mock_file: MagicMock,
        mock_fantia_client: MagicMock,
        fantia_post_data_factory: "FantiaPostDataFactory",
        fantia_url_factory: "FantiaURLFactory",
    ) -> None:
        """サムネイルダウンロード成功テスト."""
        service = self._create_download_service(mock_fantia_client)

        # 投稿データのモック
        post_data = fantia_post_data_factory.build(
            thumbnail=fantia_url_factory.build(url="https://example.com/thumb.jpg", ext=".jpg")
        )

        # HTTPレスポンスのモック設定
        thumbnail_data = b"test_thumbnail_data"
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {"Content-Length": str(len(thumbnail_data))}
        mock_response.iter_bytes.return_value = [thumbnail_data]
        mock_fantia_client.stream.return_value.__enter__.return_value = mock_response

        # 実行
        service.download_thumbnail("/test/path", post_data)

        # 検証
        mock_fantia_client.stream.assert_called_once_with("GET", "https://example.com/thumb.jpg")
        mock_file.assert_called_once_with("/test/path/0000_thumb.jpg", "wb")
        mock_file.return_value.write.assert_called_once_with(thumbnail_data)

    @patch("builtins.open", new_callable=mock_open)
    def test_download_photo_gallery(
        self,
        mock_file: MagicMock,
        mock_fantia_client: MagicMock,
        fantia_photo_gallery_factory: "FantiaPhotoGalleryFactory",
        fantia_url_factory: "FantiaURLFactory",
    ) -> None:
        """フォトギャラリーダウンロードテスト."""
        service = self._create_download_service(mock_fantia_client)

        # フォトギャラリーのモック
        photo_gallery = fantia_photo_gallery_factory.build(
            photos=[
                fantia_url_factory.build(url="https://example.com/photo1.jpg", ext=".jpg"),
                fantia_url_factory.build(url="https://example.com/photo2.jpg", ext=".jpg"),
            ],
        )

        # HTTPレスポンスのモック設定
        photo_data = b"photo_data"
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {"Content-Length": str(len(photo_data))}
        mock_response.iter_bytes.return_value = [photo_data]
        mock_fantia_client.stream.return_value.__enter__.return_value = mock_response

        # 実行
        service.download_photo_gallery("/test/path", photo_gallery)

        # 検証 - HTTPリクエストが正しく行われたか
        assert mock_fantia_client.stream.call_count == 2
        expected_urls = ["https://example.com/photo1.jpg", "https://example.com/photo2.jpg"]
        actual_urls = [call[0][1] for call in mock_fantia_client.stream.call_args_list]
        assert actual_urls == expected_urls

        # ファイル書き込み呼び出しを検証
        write_calls = [call[0] for call in mock_file.call_args_list]

        # コメントファイルとギャラリー画像ファイルが作成されることを検証
        comment_files = [
            call for call in write_calls
            if "/test/path" in str(call) and "comment.txt" in str(call)
        ]
        jpg_files = [
            call for call in write_calls
            if "/test/path" in str(call) and ".jpg" in str(call)
        ]

        assert len(comment_files) > 0
        assert len(jpg_files) == 2

    @patch("builtins.open", new_callable=mock_open)
    def test_download_file(
        self,
        mock_file: MagicMock,
        mock_fantia_client: MagicMock,
        fantia_file_factory: "FantiaFileFactory",
    ) -> None:
        """ファイルダウンロードテスト."""
        service = self._create_download_service(mock_fantia_client)

        # ファイルデータのモック
        file_data = fantia_file_factory.build(
            url="https://example.com/test.pdf",
            name="test.pdf",
        )

        # HTTPレスポンスのモック設定
        pdf_data = b"pdf_file_data"
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {"Content-Length": str(len(pdf_data))}
        mock_response.iter_bytes.return_value = [pdf_data]
        mock_fantia_client.stream.return_value.__enter__.return_value = mock_response

        # 実行
        service.download_file("/test/path", file_data)

        # 検証
        mock_fantia_client.stream.assert_called_once_with("GET", "https://example.com/test.pdf")

        # ファイル書き込み呼び出しを検証
        write_calls = [str(call[0]) for call in mock_file.call_args_list]

        # コメントファイルとPDFファイルが作成されることを検証
        assert any("/test/path" in call and "comment.txt" in call for call in write_calls)
        assert any("/test/path" in call and "test.pdf" in call for call in write_calls)

    @patch("builtins.open", new_callable=mock_open)
    @patch("moro.services.fantia_download.os.remove")
    def test_perform_download_success(
        self,
        mock_remove: MagicMock,
        mock_file: MagicMock,
        mock_fantia_client: MagicMock,
    ) -> None:
        """ダウンロード実行成功テスト."""
        service = self._create_download_service(mock_fantia_client)

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
        self,
        mock_remove: MagicMock,
        mock_file: MagicMock,
        mock_fantia_client: MagicMock,
    ) -> None:
        """ダウンロード実行ネットワークエラーテスト."""
        service = self._create_download_service(mock_fantia_client)

        # ネットワークエラーをシミュレート
        mock_fantia_client.stream.side_effect = Exception("Network error")

        # 例外が発生することを検証
        with pytest.raises(Exception, match="Network error"):
            service._perform_download("https://example.com/test.jpg", "/test/test.jpg")

        # ファイルが作成されないことを検証
        mock_file.assert_not_called()
        mock_remove.assert_not_called()

    @patch("builtins.open", new_callable=mock_open)
    def test_perform_download_timeout_error(
        self,
        mock_file: MagicMock,
        mock_fantia_client: MagicMock,
    ) -> None:
        """ダウンロード実行タイムアウトエラーテスト."""
        import httpx

        service = self._create_download_service(mock_fantia_client)

        # タイムアウトエラーをシミュレート
        mock_fantia_client.stream.side_effect = httpx.TimeoutException("Request timeout")

        # 例外が発生することを検証
        with pytest.raises(httpx.TimeoutException, match="Request timeout"):
            service._perform_download("https://example.com/test.jpg", "/test/test.jpg")

        # ファイルが作成されないことを検証
        mock_file.assert_not_called()

    @patch("builtins.open", new_callable=mock_open)
    def test_perform_download_connection_error(
        self,
        mock_file: MagicMock,
        mock_fantia_client: MagicMock,
    ) -> None:
        """ダウンロード実行接続エラーテスト."""
        import httpx

        service = self._create_download_service(mock_fantia_client)

        # 接続エラーをシミュレート
        mock_fantia_client.stream.side_effect = httpx.ConnectError("Connection refused")

        # 例外が発生することを検証
        with pytest.raises(httpx.ConnectError, match="Connection refused"):
            service._perform_download("https://example.com/test.jpg", "/test/test.jpg")

        # ファイルが作成されないことを検証
        mock_file.assert_not_called()
