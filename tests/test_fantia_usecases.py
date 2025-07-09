"""fantia usecases のテスト."""

from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

import pytest

if TYPE_CHECKING:
    from conftest import FantiaTestDataFactory

from moro.usecases.fantia import FantiaDownloadPostsByUserUseCase, FantiaDownloadPostUseCase


class TestFantiaDownloadPostUseCase:
    """FantiaDownloadPostUseCase クラスのテスト."""

    @patch("moro.usecases.fantia.parse_post")
    def test_execute_success(
        self, mock_parse_post: MagicMock, fantia_test_data: "FantiaTestDataFactory"
    ) -> None:
        """実行成功テスト."""
        # モックの設定
        mock_config = MagicMock()
        mock_client = MagicMock()
        mock_auth_service = MagicMock()
        mock_download_service = MagicMock()
        mock_file_service = MagicMock()

        use_case = FantiaDownloadPostUseCase(
            config=mock_config,
            client=mock_client,
            auth_service=mock_auth_service,
            download_service=mock_download_service,
            file_service=mock_file_service,
        )

        # 認証成功
        mock_auth_service.ensure_authenticated.return_value = True

        # 投稿データのモック
        mock_post_data = fantia_test_data.create_fantia_post_data()
        mock_parse_post.return_value = mock_post_data

        # ディレクトリ作成のモック
        mock_file_service.create_post_directory.return_value = "/test/directory"

        # 実行
        use_case.execute("12345")

        # 検証
        mock_auth_service.ensure_authenticated.assert_called_once()
        mock_parse_post.assert_called_once_with(mock_client, "12345")
        mock_file_service.create_post_directory.assert_called_once_with(mock_post_data)
        mock_file_service.save_post_comment.assert_called_once_with(
            "/test/directory", mock_post_data.comment
        )


    @patch("moro.usecases.fantia.parse_post")
    def test_execute_parse_error(self, mock_parse_post: MagicMock) -> None:
        """パースエラーのテスト."""
        mock_config = MagicMock()
        mock_client = MagicMock()
        mock_auth_service = MagicMock()
        mock_download_service = MagicMock()
        mock_file_service = MagicMock()

        use_case = FantiaDownloadPostUseCase(
            config=mock_config,
            client=mock_client,
            auth_service=mock_auth_service,
            download_service=mock_download_service,
            file_service=mock_file_service,
        )

        # 認証成功
        mock_auth_service.ensure_authenticated.return_value = True

        # パースエラー
        mock_parse_post.side_effect = Exception("Parse error")

        # 実行 - 例外が発生することを確認
        with pytest.raises(Exception, match="Parse error"):
            use_case.execute("12345")


class TestFantiaDownloadPostsByUserUseCase:
    """FantiaDownloadPostsByUserUseCase クラスのテスト."""

    @patch("moro.usecases.fantia.get_posts_by_user")
    def test_execute_success(self, mock_get_posts_by_user: MagicMock) -> None:
        """実行成功テスト."""
        # モックの設定
        mock_config = MagicMock()
        mock_client = MagicMock()
        mock_auth_service = MagicMock()
        mock_download_service = MagicMock()
        mock_file_service = MagicMock()

        use_case = FantiaDownloadPostsByUserUseCase(
            config=mock_config,
            client=mock_client,
            auth_service=mock_auth_service,
            download_service=mock_download_service,
            file_service=mock_file_service,
        )

        # 認証成功
        mock_auth_service.ensure_authenticated.return_value = True

        # ユーザーの投稿リスト
        mock_get_posts_by_user.return_value = ["12345", "67890"]

        # _download_single_postをモックして実際の処理を回避
        with patch.object(use_case, "_download_single_post") as mock_download:
            # 実行
            use_case.execute("test_user")

            # 検証
            mock_auth_service.ensure_authenticated.assert_called_once()
            mock_get_posts_by_user.assert_called_once_with(mock_client, "test_user")
            assert mock_download.call_count == 2  # 2つの投稿を処理
