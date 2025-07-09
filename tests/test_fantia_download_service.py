"""fantia download service のテスト."""

from typing import TYPE_CHECKING
from unittest.mock import MagicMock, mock_open, patch

import pytest

if TYPE_CHECKING:
    from conftest import FantiaTestDataFactory

from moro.config.settings import ConfigRepository
from moro.services.fantia_download import FantiaDownloadService


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
        config_repository: ConfigRepository,
        fantia_test_data: "FantiaTestDataFactory",
    ) -> None:
        """サムネイルダウンロード成功テスト."""
        service = self._create_download_service(mock_fantia_client)

        # 投稿データのモック
        post_data = fantia_test_data.create_fantia_post_data(
            thumbnail=fantia_test_data.create_fantia_url(
                url="https://example.com/thumb.jpg", ext=".jpg"
            )
        )

        # モックの設定
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

    @patch("builtins.open", new_callable=mock_open)
    @patch("moro.services.fantia_download.os.path.join")
    def test_download_photo_gallery(
        self,
        mock_join: MagicMock,
        mock_file: MagicMock,
        mock_fantia_client: MagicMock,
        config_repository: ConfigRepository,
        fantia_test_data: "FantiaTestDataFactory",
    ) -> None:
        """フォトギャラリーダウンロードテスト."""
        service = self._create_download_service(mock_fantia_client)

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
        mock_fantia_client: MagicMock,
        config_repository: ConfigRepository,
        fantia_test_data: "FantiaTestDataFactory",
    ) -> None:
        """ファイルダウンロードテスト."""
        service = self._create_download_service(mock_fantia_client)

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
        self,
        mock_remove: MagicMock,
        mock_file: MagicMock,
        mock_fantia_client: MagicMock,
        config_repository: ConfigRepository,
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
        config_repository: ConfigRepository,
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
