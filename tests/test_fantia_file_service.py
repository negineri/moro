"""fantia file service のテスト."""

from typing import TYPE_CHECKING
from unittest.mock import MagicMock, mock_open, patch

import pytest

from moro.services.fantia_file import FantiaFileService

if TYPE_CHECKING:
    from conftest import FantiaPostDataFactory


class TestFantiaFileService:
    """FantiaFileService クラスのテスト."""

    def _create_file_service(self) -> FantiaFileService:
        """ファイルサービスのテスト用インスタンスを作成."""
        mock_config = MagicMock()
        mock_config.app.working_dir = "/test/working"
        return FantiaFileService(mock_config)

    @patch("moro.services.fantia_file.os.makedirs")
    @patch("moro.services.fantia_file.sanitize_filename")
    def test_create_post_directory(
        self,
        mock_sanitize: MagicMock,
        mock_makedirs: MagicMock,
        fantia_post_data_factory: "FantiaPostDataFactory",
    ) -> None:
        """投稿ディレクトリ作成テスト."""
        service = self._create_file_service()

        # モックの設定
        mock_sanitize.return_value = "12345_Test_Post_Title_202301011200"

        # テスト用投稿データ
        post_data = fantia_post_data_factory.build(
            id="12345",
            title="Test Post Title",
            creator_id="creator123",
            creator_name="Test Creator",
        )

        # 実行
        result = service.create_post_directory(post_data)

        # 検証
        # 結果のパス文字列に必要な要素が含まれることを確認
        assert "/test/working/downloads/fantia/creator123" in result
        assert "12345_Test_Post_Title_202301011200" in result

        # ディレクトリ作成が呼び出されたことを確認
        mock_makedirs.assert_called_once()
        created_path = mock_makedirs.call_args[0][0]
        assert "/test/working/downloads/fantia/creator123" in created_path

        # sanitize_filenameの呼び出しを検証
        mock_sanitize.assert_called_once()

    @patch("builtins.open", new_callable=mock_open)
    def test_file_operations(self, mock_file: MagicMock) -> None:
        """ファイル操作の統合テスト（コメント保存とディレクトリ取得）."""
        service = self._create_file_service()
        service.save_post_comment("/test/dir", "Test comment content")

        # ファイル書き込み呼び出しを検証
        write_calls = [str(call[0]) for call in mock_file.call_args_list]
        assert any("/test/dir" in call and "comment.txt" in call for call in write_calls)
        mock_file.return_value.write.assert_called_with("Test comment content")

        # ダウンロードディレクトリ取得のテスト
        result = service.get_download_directory()
        assert "/test/working/downloads/fantia" in result

    @patch("builtins.open", new_callable=mock_open)
    def test_create_content_directory(self, mock_file: MagicMock) -> None:
        """コンテンツディレクトリ作成テスト."""
        service = self._create_file_service()

        with patch("moro.services.fantia_file.os.makedirs") as mock_makedirs:
            with patch("moro.services.fantia_file.sanitize_filename") as mock_sanitize:
                mock_sanitize.return_value = "content123_Test_Content"

                result = service.create_content_directory(
                    "/test/post", "content123", "Test Content"
                )

                # 結果のパスに必要な要素が含まれることを確認
                assert "/test/post" in result
                assert "content123_Test_Content" in result

                # ディレクトリ作成が呼び出されたことを確認
                mock_makedirs.assert_called_once()
                created_path = mock_makedirs.call_args[0][0]
                assert "/test/post" in created_path and "content123_Test_Content" in created_path

    @patch("moro.services.fantia_file.os.makedirs")
    def test_create_directory_permission_error(self, mock_makedirs: MagicMock) -> None:
        """ディレクトリ作成権限エラーのテスト."""
        service = self._create_file_service()

        # 権限エラーをシミュレート
        mock_makedirs.side_effect = PermissionError("Permission denied")

        # 例外が発生することを検証
        with pytest.raises(PermissionError, match="Permission denied"):
            service.create_content_directory("/root/test", "content123", "Test Content")

    @patch("builtins.open", new_callable=mock_open)
    def test_save_file_permission_error(self, mock_file: MagicMock) -> None:
        """ファイル保存権限エラーのテスト."""
        service = self._create_file_service()

        # 権限エラーをシミュレート
        mock_file.side_effect = PermissionError("Permission denied")

        # 例外が発生することを検証
        with pytest.raises(PermissionError, match="Permission denied"):
            service.save_post_comment("/readonly/dir", "Test comment")
