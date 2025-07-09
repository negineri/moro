"""fantia auth service のテスト."""

from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

if TYPE_CHECKING:
    from conftest import FantiaTestDataFactory

from moro.modules.fantia import FantiaConfig
from moro.services.fantia_auth import FantiaAuthService


class TestFantiaAuthService:
    """FantiaAuthService クラスのテスト."""

    def _create_auth_service(self, mock_client: MagicMock) -> FantiaAuthService:
        """認証サービスのテスト用インスタンスを作成."""
        mock_config = MagicMock()
        mock_config.app.user_data_dir = "/test/userdata"
        return FantiaAuthService(mock_config, mock_client)

    @patch("moro.services.fantia_auth.check_login")
    def test_ensure_authenticated_already_logged_in(
        self,
        mock_check_login: MagicMock,
        mock_fantia_client: MagicMock,
    ) -> None:
        """既にログイン済みの場合のテスト."""
        service = self._create_auth_service(mock_fantia_client)

        # 既にログイン済み
        mock_check_login.return_value = True

        result = service.ensure_authenticated()

        assert result is True
        mock_check_login.assert_called_once_with(mock_fantia_client)

    @patch("moro.services.fantia_auth.check_login")
    def test_ensure_authenticated_login_required(
        self,
        mock_check_login: MagicMock,
        mock_fantia_client: MagicMock,
        fantia_test_data: "FantiaTestDataFactory",
    ) -> None:
        """ログインが必要な場合のテスト."""
        service = self._create_auth_service(mock_fantia_client)

        # 最初はログインしていない
        mock_check_login.return_value = False

        # _login_with_seleniumをモック化して成功させる
        with patch.object(service, "_login_with_selenium", return_value=True) as mock_login:
            result = service.ensure_authenticated()

            assert result is True
            mock_login.assert_called_once()

    @patch("moro.services.fantia_auth.check_login")
    def test_ensure_authenticated_login_failed(
        self,
        mock_check_login: MagicMock,
        mock_fantia_client: MagicMock,
        fantia_config: FantiaConfig,
    ) -> None:
        """ログイン失敗のテスト."""
        service = self._create_auth_service(mock_fantia_client)

        # ログインしていない
        mock_check_login.return_value = False

        # _login_with_seleniumが失敗するようにモック
        with patch.object(service, "_login_with_selenium", return_value=False) as mock_login:
            result = service.ensure_authenticated()

            assert result is False
            mock_login.assert_called_once()
            mock_check_login.assert_called_once_with(mock_fantia_client)
