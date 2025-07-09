"""fantia file service のテスト."""

from typing import TYPE_CHECKING
from unittest.mock import MagicMock, mock_open, patch

if TYPE_CHECKING:
    from conftest import FantiaTestDataFactory

from moro.services.fantia_file import FantiaFileService


class TestFantiaFileService:
    """FantiaFileService クラスのテスト."""

    def _create_file_service(self) -> FantiaFileService:
        """ファイルサービスのテスト用インスタンスを作成."""
        mock_config = MagicMock()
        mock_config.app.working_dir = "/test/working"
        return FantiaFileService(mock_config)

    @patch("moro.services.fantia_file.os.makedirs")
    @patch("moro.services.fantia_file.os.path.join")
    @patch("moro.services.fantia_file.sanitize_filename")
    def test_create_post_directory(
        self,
        mock_sanitize: MagicMock,
        mock_join: MagicMock,
        mock_makedirs: MagicMock,
        fantia_test_data: "FantiaTestDataFactory",
    ) -> None:
        """投稿ディレクトリ作成テスト."""
        service = self._create_file_service()

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
    def test_file_operations(self, mock_join: MagicMock, mock_file: MagicMock) -> None:
        """ファイル操作の統合テスト（コメント保存とディレクトリ取得）."""
        service = self._create_file_service()

        # コメント保存のテスト
        mock_join.return_value = "/test/dir/comment.txt"
        service.save_post_comment("/test/dir", "Test comment content")
        mock_file.assert_called_with("/test/dir/comment.txt", "w", encoding="utf-8")
        mock_file.return_value.write.assert_called_with("Test comment content")

        # ダウンロードディレクトリ取得のテスト
        mock_join.return_value = "/test/working/downloads/fantia"
        result = service.get_download_directory()
        assert result == "/test/working/downloads/fantia"

    @patch("builtins.open", new_callable=mock_open)
    @patch("moro.services.fantia_file.os.path.join")
    def test_create_content_directory(self, mock_join: MagicMock, mock_file: MagicMock) -> None:
        """コンテンツディレクトリ作成テスト."""
        service = self._create_file_service()

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
