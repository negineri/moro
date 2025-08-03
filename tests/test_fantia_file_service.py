"""fantia file service のテスト."""

from typing import TYPE_CHECKING
from unittest.mock import MagicMock, mock_open, patch

import pytest

from moro.services.fantia_file import FantiaFileService

if TYPE_CHECKING:
    pass


class TestFantiaFileService:
    """FantiaFileService クラスのテスト."""

    def _create_file_service(self) -> FantiaFileService:
        """ファイルサービスのテスト用インスタンスを作成."""
        mock_config = MagicMock()
        mock_config.app.working_dir = "/test/working"
        return FantiaFileService(mock_config)

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
