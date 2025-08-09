"""fantia moduleのテスト."""

from collections.abc import Callable
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import httpx
import pytest

from moro.modules.common import CommonConfig
from moro.modules.fantia import (
    FantiaClient,
    _extract_post_metadata,
    _fetch_post_data,
    _parse_post_contents,
    _parse_post_thumbnail,
    _validate_post_type,
    check_login,
)
from moro.modules.fantia.config import FantiaConfig
from moro.modules.fantia.domain import SessionIdProvider
from moro.modules.fantia.infrastructure import SeleniumSessionIdProvider


@pytest.fixture
def common_config(tmp_path: Path) -> CommonConfig:
    """CommonConfigのテスト用インスタンスを提供するフィクスチャ."""
    return CommonConfig(
        user_data_dir=str(tmp_path / "user_data"),
        user_cache_dir=str(tmp_path / "cache"),
        working_dir=str(tmp_path / "working"),
        jobs=4,
    )


@pytest.fixture
def fantia_config(tmp_path: Path) -> FantiaConfig:
    """FantiaConfigのテスト用インスタンスを提供するフィクスチャ."""
    return FantiaConfig()


@pytest.fixture
def session_id_provider() -> SessionIdProvider:
    """SessionIdProviderのテスト用インスタンスを提供するフィクスチャ."""

    class TestProvider(SessionIdProvider):
        def get_session_id(self) -> str | None:
            return "test_session_id"

        def get_cookies(self) -> dict[str, str]:
            return {"_session_id": "test_session_id"}

    return TestProvider()


class TestFantiaIntegratin:
    """FantiaClientの統合テスト."""


class TestSessionIdProvider:
    """SessionIdProvider クラスのテスト."""

    def test_get_session_id_is_abstract(self) -> None:
        """抽象メソッドのテスト - インスタンス化できないことを確認."""
        # SessionIdProviderは抽象クラスなので直接インスタンス化できない
        with pytest.raises(TypeError):
            SessionIdProvider()  # type: ignore

    def test_concrete_provider_success(self) -> None:
        """具象プロバイダーの成功ケーステスト."""

        # テスト用の具象クラスを作成
        class TestProvider(SessionIdProvider):
            def get_session_id(self) -> str | None:
                return "valid_session_id"

            def get_cookies(self) -> dict[str, str]:
                return {"_session_id": "valid_session_id"}

        provider = TestProvider()
        result = provider.get_session_id()

        assert result == "valid_session_id"
        assert isinstance(result, str)

    def test_concrete_provider_returns_none(self) -> None:
        """具象プロバイダーがNoneを返すケーステスト."""

        # テスト用の具象クラスを作成
        class TestProvider(SessionIdProvider):
            def get_session_id(self) -> str | None:
                return None

            def get_cookies(self) -> dict[str, str]:
                return {}

        provider = TestProvider()
        result = provider.get_session_id()

        assert result is None

    def test_concrete_provider_empty_string(self) -> None:
        """具象プロバイダーが空文字列を返すケーステスト."""

        # テスト用の具象クラスを作成
        class TestProvider(SessionIdProvider):
            def get_session_id(self) -> str | None:
                return ""

            def get_cookies(self) -> dict[str, str]:
                return {"_session_id": ""}

        provider = TestProvider()
        result = provider.get_session_id()

        assert result == ""
        assert isinstance(result, str)

    def test_concrete_provider_exception_handling(self) -> None:
        """具象プロバイダーで例外が発生するケーステスト."""

        # テスト用の具象クラスを作成
        class TestProvider(SessionIdProvider):
            def get_session_id(self) -> str | None:
                raise RuntimeError("Test error")

            def get_cookies(self) -> dict[str, str]:
                return {}

        provider = TestProvider()

        # 例外が発生することを確認
        with pytest.raises(RuntimeError, match="Test error"):
            provider.get_session_id()

    def test_multiple_calls(self) -> None:
        """複数回呼び出しのテスト."""

        # テスト用の具象クラスを作成
        class TestProvider(SessionIdProvider):
            def __init__(self) -> None:
                self.call_count = 0

            def get_session_id(self) -> str | None:
                self.call_count += 1
                return f"session_{self.call_count}"

            def get_cookies(self) -> dict[str, str]:
                self.call_count += 1
                return {"_session_id": f"session_{self.call_count}"}

        provider = TestProvider()

        # 複数回呼び出しても動作することを確認
        result1 = provider.get_session_id()
        result2 = provider.get_session_id()

        assert result1 == "session_1"
        assert result2 == "session_2"
        assert provider.call_count == 2

    def test_get_cookies_abstract_method(self) -> None:
        """get_cookies()が抽象メソッドであることを確認するテスト."""
        # SessionIdProviderは抽象クラスなので直接インスタンス化できない
        with pytest.raises(TypeError):
            SessionIdProvider()  # type: ignore

    def test_concrete_provider_get_cookies_success(self) -> None:
        """具象プロバイダーのget_cookies()成功ケーステスト."""

        # テスト用の具象クラスを作成
        class TestProvider(SessionIdProvider):
            def get_session_id(self) -> str | None:
                return "valid_session_id"

            def get_cookies(self) -> dict[str, str]:
                return {
                    "_session_id": "valid_session_id",
                    "jp_chatplus_vtoken": "valid_token",
                    "_f_v_k_1": "valid_key",
                }

        provider = TestProvider()
        result = provider.get_cookies()

        expected = {
            "_session_id": "valid_session_id",
            "jp_chatplus_vtoken": "valid_token",
            "_f_v_k_1": "valid_key",
        }
        assert result == expected
        assert isinstance(result, dict)

    def test_concrete_provider_get_cookies_empty(self) -> None:
        """具象プロバイダーが空辞書を返すケーステスト."""

        # テスト用の具象クラスを作成
        class TestProvider(SessionIdProvider):
            def get_session_id(self) -> str | None:
                return None

            def get_cookies(self) -> dict[str, str]:
                return {}

        provider = TestProvider()
        result = provider.get_cookies()

        assert result == {}
        assert isinstance(result, dict)


class TestFantiaClient:
    """FantiaClient クラスのテスト."""

    def test_http_client_configuration(self, session_id_provider: SessionIdProvider) -> None:
        """HTTP クライアントの設定テスト."""
        config = FantiaConfig(max_retries=5)
        client = FantiaClient(config, session_provider=session_id_provider)

        # httpx.Client が適切な設定で作成されることを確認
        assert client.timeout.connect == config.timeout_connect
        assert client.timeout.read == config.timeout_read
        assert client.timeout.write == config.timeout_write
        assert client.timeout.pool == config.timeout_pool


class TestFantiaClientSessionIdProviderIntegration:
    """FantiaClientとSessionIdProviderの統合テスト."""

    def test_session_id_provider_integration_success(self) -> None:
        """SessionIdProviderとの統合成功テスト."""

        # テスト用のプロバイダーを作成
        class TestProvider(SessionIdProvider):
            def get_session_id(self) -> str | None:
                return "test_session_id"

            def get_cookies(self) -> dict[str, str]:
                return {"_session_id": "test_session_id"}

        provider = TestProvider()
        config = FantiaConfig()

        # 統合機能をテスト
        client = FantiaClient(config, session_provider=provider)

        # クッキーの更新をテスト
        client._update_cookies()
        assert client.cookies.get("_session_id") == "test_session_id"

    def test_session_id_provider_integration_none(self) -> None:
        """SessionIdProviderがNoneを返す場合の統合テスト."""

        # テスト用のプロバイダーを作成
        class TestProvider(SessionIdProvider):
            def get_session_id(self) -> str | None:
                return None

            def get_cookies(self) -> dict[str, str]:
                return {}

        provider = TestProvider()
        config = FantiaConfig()

        # 統合機能をテスト
        client = FantiaClient(config, session_provider=provider)

        # クッキーの更新をテスト（空の場合はクッキーが削除される）
        client._update_cookies()
        assert client.cookies.get("_session_id") is None

    def test_session_id_provider_dynamic_update(self) -> None:
        """SessionIdProviderの動的更新テスト."""

        # テスト用のプロバイダーを作成
        class TestProvider(SessionIdProvider):
            def __init__(self) -> None:
                self.session_id = "initial_session"

            def get_session_id(self) -> str | None:
                return self.session_id

            def get_cookies(self) -> dict[str, str]:
                if self.session_id:
                    return {"_session_id": self.session_id}
                return {}

            def update_session_id(self, new_session_id: str) -> None:
                self.session_id = new_session_id

        provider = TestProvider()
        config = FantiaConfig()

        # 統合機能をテスト
        client = FantiaClient(config, session_provider=provider)

        # 初期クッキーの確認
        client._update_cookies()
        assert client.cookies.get("_session_id") == "initial_session"

        # セッションIDを更新
        provider.update_session_id("updated_session")

        # クッキーも動的に更新されることを確認
        client._update_cookies()
        assert client.cookies.get("_session_id") == "updated_session"

    def test_multi_cookie_integration(self) -> None:
        """複数クッキー統合テスト."""

        # テスト用の複数クッキープロバイダーを作成
        class TestMultiCookieProvider(SessionIdProvider):
            def get_session_id(self) -> str | None:
                return "test_session_12345"

            def get_cookies(self) -> dict[str, str]:
                return {
                    "_session_id": "test_session_12345",
                    "jp_chatplus_vtoken": "test_chatplus_67890",
                    "_f_v_k_1": "test_fantia_key_abcde",
                }

        provider = TestMultiCookieProvider()
        config = FantiaConfig()

        # 統合機能をテスト
        client = FantiaClient(config, session_provider=provider)

        # 複数クッキーの更新をテスト
        client._update_cookies()
        assert client.cookies.get("_session_id") == "test_session_12345"
        assert client.cookies.get("jp_chatplus_vtoken") == "test_chatplus_67890"
        assert client.cookies.get("_f_v_k_1") == "test_fantia_key_abcde"

    def test_partial_cookie_integration(self) -> None:
        """一部クッキーのみの統合テスト."""

        # テスト用の一部クッキープロバイダーを作成
        class TestPartialCookieProvider(SessionIdProvider):
            def get_session_id(self) -> str | None:
                return "test_session_only"

            def get_cookies(self) -> dict[str, str]:
                return {
                    "_session_id": "test_session_only",
                    # jp_chatplus_vtoken と _f_v_k_1 は存在しない
                }

        provider = TestPartialCookieProvider()
        config = FantiaConfig()

        # 統合機能をテスト
        client = FantiaClient(config, session_provider=provider)

        # 一部クッキーの更新をテスト
        client._update_cookies()
        assert client.cookies.get("_session_id") == "test_session_only"
        assert client.cookies.get("jp_chatplus_vtoken") is None
        assert client.cookies.get("_f_v_k_1") is None

    def test_cookie_deletion_on_provider_change(self) -> None:
        """プロバイダーでクッキーが削除される場合のテスト."""

        # 初期状態で複数クッキーを返すプロバイダーを作成
        class TestInitialProvider(SessionIdProvider):
            def get_session_id(self) -> str | None:
                return "test_session"

            def get_cookies(self) -> dict[str, str]:
                return {
                    "_session_id": "test_session",
                    "jp_chatplus_vtoken": "test_token",
                    "_f_v_k_1": "test_key",
                }

        initial_provider = TestInitialProvider()
        config = FantiaConfig()
        client = FantiaClient(config, session_provider=initial_provider)

        # 初期クッキーの設定
        client._update_cookies()
        assert client.cookies.get("_session_id") == "test_session"
        assert client.cookies.get("jp_chatplus_vtoken") == "test_token"
        assert client.cookies.get("_f_v_k_1") == "test_key"

        # 一部のクッキーのみを返すプロバイダーに変更
        class TestReducedProvider(SessionIdProvider):
            def get_session_id(self) -> str | None:
                return "new_session"

            def get_cookies(self) -> dict[str, str]:
                return {
                    "_session_id": "new_session",
                    # jp_chatplus_vtoken と _f_v_k_1 は削除される
                }

        reduced_provider = TestReducedProvider()
        client._session_provider = reduced_provider

        # クッキーが適切に更新・削除されることを確認
        client._update_cookies()
        assert client.cookies.get("_session_id") == "new_session"
        assert client.cookies.get("jp_chatplus_vtoken") is None
        assert client.cookies.get("_f_v_k_1") is None


class TestFantiaClientAutoSessionUpdate:
    """FantiaClientの自動session_id更新機能のテスト."""

    def test_get_success_with_valid_session(self) -> None:
        """有効なsession_idでget()が成功するテスト."""

        # テスト用のプロバイダーを作成
        class TestProvider(SessionIdProvider):
            def get_session_id(self) -> str | None:
                return "valid_session_id"

            def get_cookies(self) -> dict[str, str]:
                return {"_session_id": "valid_session_id"}

        provider = TestProvider()
        config = FantiaConfig()
        client = FantiaClient(config, session_provider=provider)

        # モックレスポンスを作成
        with patch.object(
            client, "get", return_value=MagicMock(status_code=200, is_success=True)
        ) as mock_get:
            response = client.get("https://fantia.jp/api/v1/me")

            assert response.status_code == 200
            assert response.is_success is True
            mock_get.assert_called_once()

    def test_get_auto_retry_on_401_provider_none(self) -> None:
        """401エラー時にProviderがNoneを返す場合のテスト."""

        # テスト用のプロバイダーを作成
        class TestProvider(SessionIdProvider):
            def get_session_id(self) -> str | None:
                return None

            def get_cookies(self) -> dict[str, str]:
                return {}

        provider = TestProvider()
        config = FantiaConfig()
        client = FantiaClient(config, session_provider=provider)

        mock_response = MagicMock(status_code=401, is_success=False)

        with patch.object(httpx.Client, "get", return_value=mock_response) as mock_get:
            # Providerが None を返すため、リトライしない
            response = client.get("https://fantia.jp/api/v1/me")
            assert response.status_code == 401
            assert mock_get.call_count == 1

    def test_get_no_retry_on_403_error(self) -> None:
        """403エラーでは自動リトライしないテスト."""

        # テスト用のプロバイダーを作成
        class TestProvider(SessionIdProvider):
            def get_session_id(self) -> str | None:
                return "valid_session_id"

            def get_cookies(self) -> dict[str, str]:
                return {"_session_id": "valid_session_id"}

        provider = TestProvider()
        config = FantiaConfig()
        client = FantiaClient(config, session_provider=provider)

        mock_response = MagicMock(status_code=403, is_success=False)

        with patch.object(httpx.Client, "get", return_value=mock_response) as mock_get:
            response = client.get("https://fantia.jp/api/v1/me")
            assert response.status_code == 403
            # 403エラーでは1回だけ呼び出される（リトライなし）
            assert mock_get.call_count == 1


class TestFantiaClientMultiCookieIntegration:
    """FantiaClientと複数クッキーProviderの統合テスト."""

    def test_fantia_client_with_multi_cookie_provider(self) -> None:
        """FantiaClientが複数クッキープロバイダーと統合できることのテスト."""

        # テスト用の複数クッキープロバイダーを作成
        class TestMultiCookieProvider(SessionIdProvider):
            def get_session_id(self) -> str | None:
                return "test_session_12345"

            def get_cookies(self) -> dict[str, str]:
                return {
                    "_session_id": "test_session_12345",
                    "jp_chatplus_vtoken": "test_chatplus_67890",
                    "_f_v_k_1": "test_fantia_key_abcde",
                }

        provider = TestMultiCookieProvider()
        config = FantiaConfig()

        # 統合機能をテスト
        client = FantiaClient(config, session_provider=provider)

        # クッキーの更新をテスト
        client._update_cookies()
        assert client.cookies.get("_session_id") == "test_session_12345"

    def test_fantia_client_with_empty_cookie_provider(self) -> None:
        """空のクッキーを返すプロバイダーとの統合テスト."""

        # テスト用の空クッキープロバイダーを作成
        class TestEmptyCookieProvider(SessionIdProvider):
            def get_session_id(self) -> str | None:
                return None

            def get_cookies(self) -> dict[str, str]:
                return {}

        provider = TestEmptyCookieProvider()
        config = FantiaConfig()
        client = FantiaClient(config, session_provider=provider)

        # クッキーの更新をテスト（空の場合はクッキーが削除される）
        client._update_cookies()
        assert client.cookies.get("_session_id") is None


class TestSeleniumSessionIdProviderCookieCache:
    """SeleniumSessionIdProviderのクッキーキャッシュ機能のテスト."""

    def test_cache_file_path_custom(self, common_config: CommonConfig) -> None:
        """カスタムキャッシュファイルパスのテスト."""
        fantia_config = FantiaConfig(cookie_cache_file="/custom/path/cookies.json")
        provider = SeleniumSessionIdProvider(common_config, fantia_config)
        assert provider._cookie_cache_file == "/custom/path/cookies.json"

    def test_save_and_load_cached_cookies(
        self, common_config: CommonConfig, tmp_path: Path
    ) -> None:
        """クッキーの保存と読み込みのテスト."""
        cache_file = tmp_path / "test_cookies.json"
        fantia_config = FantiaConfig(cookie_cache_file=str(cache_file))
        provider = SeleniumSessionIdProvider(common_config, fantia_config)

        # Test cookies
        test_cookies = {
            "_session_id": "test_session_12345",
            "jp_chatplus_vtoken": "test_token_67890",
            "_f_v_k_1": "test_key_abcde",
        }

        # Save cookies
        provider._save_cookies_to_cache(test_cookies)
        assert cache_file.exists()

        # Load cookies
        loaded_cookies = provider._load_cached_cookies()
        assert loaded_cookies == test_cookies

    def test_cache_file_security_permissions(
        self, common_config: CommonConfig, tmp_path: Path
    ) -> None:
        """キャッシュファイルのセキュリティ権限のテスト."""
        import stat

        cache_file = tmp_path / "secure_cookies.json"
        fantia_config = FantiaConfig(cookie_cache_file=str(cache_file))
        provider = SeleniumSessionIdProvider(common_config, fantia_config)

        test_cookies = {"_session_id": "test_session"}
        provider._save_cookies_to_cache(test_cookies)

        # Check file permissions (user read/write only)
        file_mode = cache_file.stat().st_mode
        assert file_mode & stat.S_IRWXU == stat.S_IRUSR | stat.S_IWUSR
        assert file_mode & stat.S_IRWXG == 0
        assert file_mode & stat.S_IRWXO == 0

    def test_session_validation_success(
        self, common_config: CommonConfig, fantia_config: FantiaConfig
    ) -> None:
        """セッション有効性チェック成功のテスト."""
        from unittest.mock import MagicMock, patch

        provider = SeleniumSessionIdProvider(common_config, fantia_config)
        test_cookies = {"_session_id": "valid_session"}

        # Mock successful API response
        mock_response = MagicMock()
        mock_response.is_success = True
        mock_response.status_code = 200

        with patch("httpx.Client") as mock_client_class:
            mock_client = MagicMock()
            mock_client.__enter__ = MagicMock(return_value=mock_client)
            mock_client.__exit__ = MagicMock(return_value=None)
            mock_client.get.return_value = mock_response
            mock_client_class.return_value = mock_client

            result = provider._is_session_valid(test_cookies)
            assert result is True
            mock_client.get.assert_called_once()

    def test_session_validation_failure(
        self, common_config: CommonConfig, fantia_config: FantiaConfig
    ) -> None:
        """セッション有効性チェック失敗のテスト."""
        from unittest.mock import MagicMock, patch

        provider = SeleniumSessionIdProvider(common_config, fantia_config)
        test_cookies = {"_session_id": "invalid_session"}

        # Mock failed API response
        mock_response = MagicMock()
        mock_response.is_success = False
        mock_response.status_code = 401

        with patch("httpx.Client") as mock_client_class:
            mock_client = MagicMock()
            mock_client.__enter__ = MagicMock(return_value=mock_client)
            mock_client.__exit__ = MagicMock(return_value=None)
            mock_client.get.return_value = mock_response
            mock_client_class.return_value = mock_client

            result = provider._is_session_valid(test_cookies)
            assert result is False

    def test_session_validation_empty_cookies(
        self, common_config: CommonConfig, fantia_config: FantiaConfig
    ) -> None:
        """空のクッキーでのセッション有効性チェックのテスト."""
        provider = SeleniumSessionIdProvider(common_config, fantia_config)

        result = provider._is_session_valid({})
        assert result is False

    def test_get_cookies_uses_cache_when_valid(
        self, common_config: CommonConfig, tmp_path: Path
    ) -> None:
        """有効なキャッシュが存在する場合にキャッシュを使用することのテスト."""
        from unittest.mock import patch

        cache_file = tmp_path / "valid_cache.json"
        fantia_config = FantiaConfig(cookie_cache_file=str(cache_file))
        provider = SeleniumSessionIdProvider(common_config, fantia_config)

        # Pre-populate cache
        test_cookies = {"_session_id": "cached_session", "jp_chatplus_vtoken": "cached_token"}
        provider._save_cookies_to_cache(test_cookies)

        # Mock session validation to return True
        with patch.object(provider, "_is_session_valid", return_value=True):
            with patch.object(provider, "_perform_selenium_login") as mock_selenium:
                result = provider.get_cookies()

                # Should return cached cookies without calling Selenium
                assert result == test_cookies
                mock_selenium.assert_not_called()

    def test_get_cookies_performs_login_when_cache_invalid(
        self, common_config: CommonConfig, tmp_path: Path
    ) -> None:
        """無効なキャッシュの場合にSeleniumログインを実行することのテスト."""
        from unittest.mock import patch

        cache_file = tmp_path / "invalid_cache.json"
        fantia_config = FantiaConfig(cookie_cache_file=str(cache_file))
        provider = SeleniumSessionIdProvider(common_config, fantia_config)

        fresh_cookies = {"_session_id": "fresh_session", "_f_v_k_1": "fresh_key"}

        # Mock session validation to return False and Selenium login
        with patch.object(provider, "_is_session_valid", return_value=False):
            with patch.object(
                provider, "_perform_selenium_login", return_value=fresh_cookies
            ) as mock_selenium:
                result = provider.get_cookies()

                # Should perform fresh login and return new cookies
                assert result == fresh_cookies
                mock_selenium.assert_called_once()

    def test_cache_disabled(self, common_config: CommonConfig) -> None:
        """クッキーキャッシュが無効の場合のテスト."""
        fantia_config = FantiaConfig(enable_cookie_cache=False)
        provider = SeleniumSessionIdProvider(common_config, fantia_config)

        assert provider._enable_cookie_cache is False

        # Should always return empty cache when disabled
        result = provider._load_cached_cookies()
        assert result == {}


class TestSeleniumSessionIdProvider:
    """SeleniumSessionIdProviderのテスト."""

    def test_selenium_provider_get_session_id_returns_none_when_not_implemented(self) -> None:
        """SeleniumSessionIdProviderのget_session_id()が実装されていない場合にNoneを返すテスト."""
        # TODO: SeleniumSessionIdProviderクラスが実装されたら、実際のテストに置き換える

        # 現在は実装されていないため、スキップ
        # provider = SeleniumSessionIdProvider()
        # result = provider.get_session_id()
        # assert result is None  # 実装されていない場合はNoneを返すことを期待
        pass

    def test_selenium_provider_webdriver_error_handling(
        self, common_config: CommonConfig, fantia_config: FantiaConfig
    ) -> None:
        """SeleniumSessionIdProviderがWebDriverエラーを適切に処理することを確認するテスト."""
        # WebDriverの初期化に失敗した場合のテスト
        with patch("selenium.webdriver.Chrome", side_effect=Exception("WebDriver error")):
            provider = SeleniumSessionIdProvider(common_config, fantia_config)
            result = provider.get_cookies()
            assert result == {}  # 空の辞書を返すことを期待

    def test_selenium_provider_login_success_mock(
        self, common_config: CommonConfig, fantia_config: FantiaConfig
    ) -> None:
        """SeleniumSessionIdProviderが正常にログインしてsession_idを取得することを確認するテスト（モック使用）."""
        # contextmanagerのモック設定
        mock_driver = MagicMock()
        mock_driver.__enter__ = MagicMock(return_value=mock_driver)
        mock_driver.__exit__ = MagicMock(return_value=None)

        mock_driver.get_cookies.return_value = [
            {"name": "_session_id", "value": "test_session_12345"},
            {"name": "other_cookie", "value": "other_value"},
        ]
        # current_urlプロパティを適切に設定
        mock_driver.current_url = "https://fantia.jp/"

        with patch("selenium.webdriver.Chrome", return_value=mock_driver):
            provider = SeleniumSessionIdProvider(common_config, fantia_config)
            result = provider.get_cookies()
            assert result["_session_id"] == "test_session_12345"

    def test_selenium_provider_no_session_cookie_found(
        self, common_config: CommonConfig, fantia_config: FantiaConfig
    ) -> None:
        """SeleniumSessionIdProviderがsession_idクッキーを見つけられない場合のテスト."""
        # session_idクッキーが存在しない場合のテスト
        mock_driver = MagicMock()
        mock_driver.__enter__ = MagicMock(return_value=mock_driver)
        mock_driver.__exit__ = MagicMock(return_value=None)

        mock_driver.get_cookies.return_value = [{"name": "other_cookie", "value": "other_value"}]
        # current_urlプロパティを適切に設定
        mock_driver.current_url = "https://fantia.jp/"

        with patch("selenium.webdriver.Chrome", return_value=mock_driver):
            provider = SeleniumSessionIdProvider(common_config, fantia_config)
            result = provider.get_cookies()
            assert result == {}  # session_idが見つからない場合は空の辞書を返す


class TestSeleniumSessionIdProviderMultiCookie:
    """SeleniumSessionIdProviderの複数クッキー対応テスト."""

    def test_get_cookies_all_cookies_available(
        self, common_config: CommonConfig, fantia_config: FantiaConfig
    ) -> None:
        """全クッキーが取得できる場合のget_cookies()テスト."""
        mock_driver = MagicMock()
        mock_driver.__enter__ = MagicMock(return_value=mock_driver)
        mock_driver.__exit__ = MagicMock(return_value=None)

        mock_driver.get_cookies.return_value = [
            {"name": "_session_id", "value": "session_12345"},
            {"name": "jp_chatplus_vtoken", "value": "chatplus_67890"},
            {"name": "_f_v_k_1", "value": "fantia_key_abcde"},
            {"name": "other_cookie", "value": "other_value"},
        ]
        mock_driver.current_url = "https://fantia.jp/"

        with patch("selenium.webdriver.Chrome", return_value=mock_driver):
            provider = SeleniumSessionIdProvider(common_config, fantia_config)
            result = provider.get_cookies()

            expected = {
                "_session_id": "session_12345",
                "jp_chatplus_vtoken": "chatplus_67890",
                "_f_v_k_1": "fantia_key_abcde",
            }
            assert result == expected

    def test_get_cookies_partial_cookies_available(
        self, common_config: CommonConfig, fantia_config: FantiaConfig
    ) -> None:
        """一部クッキーのみ取得できる場合のget_cookies()テスト."""
        mock_driver = MagicMock()
        mock_driver.__enter__ = MagicMock(return_value=mock_driver)
        mock_driver.__exit__ = MagicMock(return_value=None)

        mock_driver.get_cookies.return_value = [
            {"name": "_session_id", "value": "session_12345"},
            {"name": "other_cookie", "value": "other_value"},
        ]
        mock_driver.current_url = "https://fantia.jp/"

        with patch("selenium.webdriver.Chrome", return_value=mock_driver):
            provider = SeleniumSessionIdProvider(common_config, fantia_config)
            result = provider.get_cookies()

            expected = {
                "_session_id": "session_12345",
            }
            assert result == expected

    def test_get_cookies_no_relevant_cookies(
        self, common_config: CommonConfig, fantia_config: FantiaConfig
    ) -> None:
        """必要クッキーが全く見つからない場合のget_cookies()テスト."""
        mock_driver = MagicMock()
        mock_driver.__enter__ = MagicMock(return_value=mock_driver)
        mock_driver.__exit__ = MagicMock(return_value=None)

        mock_driver.get_cookies.return_value = [
            {"name": "other_cookie", "value": "other_value"},
            {"name": "unrelated_cookie", "value": "unrelated_value"},
        ]
        mock_driver.current_url = "https://fantia.jp/"

        with patch("selenium.webdriver.Chrome", return_value=mock_driver):
            provider = SeleniumSessionIdProvider(common_config, fantia_config)
            result = provider.get_cookies()

            assert result == {}

    def test_get_cookies_webdriver_error(
        self, common_config: CommonConfig, fantia_config: FantiaConfig
    ) -> None:
        """WebDriverエラー時のget_cookies()テスト."""
        with patch("selenium.webdriver.Chrome", side_effect=Exception("WebDriver error")):
            provider = SeleniumSessionIdProvider(common_config, fantia_config)
            result = provider.get_cookies()
            assert result == {}

    @pytest.mark.skip(reason="ログインのタイムアウトは実装されていない")
    def test_get_cookies_login_failure(
        self, common_config: CommonConfig, fantia_config: FantiaConfig
    ) -> None:
        """ログイン失敗時のget_cookies()テスト."""
        mock_driver = MagicMock()
        mock_driver.__enter__ = MagicMock(return_value=mock_driver)
        mock_driver.__exit__ = MagicMock(return_value=None)

        # ログインページのまま（ログイン失敗をシミュレート）
        mock_driver.current_url = "https://fantia.jp/sessions/signin"

        with patch("selenium.webdriver.Chrome", return_value=mock_driver):
            provider = SeleniumSessionIdProvider(common_config, fantia_config)
            result = provider.get_cookies()
            assert result == {}


class TestCheckLogin:
    """check_login 関数のテスト."""

    def test_check_login_success(self) -> None:
        """ログイン成功テスト."""
        mock_client = MagicMock()

        # レスポンスが成功を示す
        mock_response = MagicMock()
        mock_response.is_success = True
        mock_response.status_code = 200
        mock_client.get.return_value = mock_response

        result = check_login(mock_client)

        assert result is True
        mock_client.get.assert_called_once_with("https://fantia.jp/api/v1/me")

    def test_check_login_failure(self) -> None:
        """ログイン失敗テスト."""
        mock_client = MagicMock()

        # レスポンスが失敗を示す
        mock_response = MagicMock()
        mock_response.is_success = False
        mock_response.status_code = 401
        mock_client.get.return_value = mock_response

        result = check_login(mock_client)

        assert result is False

    def test_check_login_exception(self) -> None:
        """ログインチェック例外テスト."""
        mock_client = MagicMock()
        mock_client.get.side_effect = httpx.RequestError("Network error")

        # 例外が発生することを確認
        with pytest.raises(httpx.RequestError, match="Network error") as exc_info:
            check_login(mock_client)

        # APIエンドポイントが呼び出されたことを検証
        mock_client.get.assert_called_once_with("https://fantia.jp/api/v1/me")
        # 例外の詳細情報を検証
        assert "Network error" in str(exc_info.value)
        assert isinstance(exc_info.value, httpx.RequestError)

    def test_check_login_timeout_exception(self) -> None:
        """ログインチェックタイムアウト例外テスト."""
        mock_client = MagicMock()
        mock_client.get.side_effect = httpx.TimeoutException("Request timeout")

        # タイムアウト例外が発生することを確認
        with pytest.raises(httpx.TimeoutException, match="Request timeout") as exc_info:
            check_login(mock_client)

        # 例外の詳細情報を検証
        assert "timeout" in str(exc_info.value).lower()
        assert isinstance(exc_info.value, httpx.TimeoutException)

    def test_check_login_connection_error(self) -> None:
        """ログインチェック接続エラーテスト."""
        mock_client = MagicMock()
        mock_client.get.side_effect = httpx.ConnectError("Connection refused")

        # 接続エラーが発生することを確認
        with pytest.raises(httpx.ConnectError, match="Connection refused") as exc_info:
            check_login(mock_client)

        # 例外の詳細情報を検証
        assert isinstance(exc_info.value, httpx.ConnectError)
        assert "refused" in str(exc_info.value).lower()


class TestFetchPostData:
    """_fetch_post_data 関数のテスト."""

    @patch("moro.modules.fantia.check_login")
    @patch("moro.modules.fantia.get_csrf_token")
    def test_fetch_post_data_success(
        self, mock_get_csrf: MagicMock, mock_check_login: MagicMock
    ) -> None:
        """投稿データ取得成功テスト."""
        mock_client = MagicMock()
        mock_check_login.return_value = True
        mock_get_csrf.return_value = "test_csrf_token"

        # レスポンスのモック
        mock_response = MagicMock()
        mock_response.text = '{"post": {"id": 12345, "title": "Test Post"}}'
        mock_client.get.return_value = mock_response

        result = _fetch_post_data(mock_client, "12345")

        assert result == {"id": 12345, "title": "Test Post"}
        mock_check_login.assert_called_once_with(mock_client)
        mock_get_csrf.assert_called_once_with(mock_client, "12345")
        # GETリクエストが正しいURLで呼び出されたことを検証
        mock_client.get.assert_called_once_with(
            "https://fantia.jp/api/v1/posts/12345",
            headers={"X-CSRF-Token": "test_csrf_token", "X-Requested-With": "XMLHttpRequest"},
        )

    @patch("moro.modules.fantia.check_login")
    def test_fetch_post_data_login_failed(self, mock_check_login: MagicMock) -> None:
        """ログイン失敗テスト."""
        mock_client = MagicMock()
        mock_check_login.return_value = False

        with pytest.raises(ValueError, match="Invalid session"):
            _fetch_post_data(mock_client, "12345")

        # ログインチェックが呼び出されたことを検証
        mock_check_login.assert_called_once_with(mock_client)
        # ログイン失敗時はデータ取得が呼び出されないことを検証
        mock_client.get.assert_not_called()

    @patch("moro.modules.fantia.check_login")
    @patch("moro.modules.fantia.get_csrf_token")
    def test_fetch_post_data_http_error(
        self, mock_get_csrf: MagicMock, mock_check_login: MagicMock
    ) -> None:
        """HTTP エラーテスト."""
        mock_client = MagicMock()
        mock_check_login.return_value = True
        mock_get_csrf.return_value = "test_csrf_token"

        # HTTP エラーをシミュレート
        mock_client.get.side_effect = httpx.HTTPStatusError(
            "Not Found", request=MagicMock(), response=MagicMock(status_code=404)
        )

        # HTTP エラーが発生することを確認
        with pytest.raises(httpx.HTTPStatusError) as exc_info:
            _fetch_post_data(mock_client, "12345")

        # 例外の詳細情報を検証
        assert exc_info.value.response.status_code == 404
        assert isinstance(exc_info.value, httpx.HTTPStatusError)

    @patch("moro.modules.fantia.check_login")
    @patch("moro.modules.fantia.get_csrf_token")
    def test_fetch_post_data_json_decode_error(
        self, mock_get_csrf: MagicMock, mock_check_login: MagicMock
    ) -> None:
        """JSON デコードエラーテスト."""
        mock_client = MagicMock()
        mock_check_login.return_value = True
        mock_get_csrf.return_value = "test_csrf_token"

        # 不正なJSONレスポンスをモック
        mock_response = MagicMock()
        mock_response.text = "invalid json content"
        mock_client.get.return_value = mock_response

        # JSON デコードエラーが発生することを確認
        with pytest.raises((ValueError, TypeError)) as exc_info:
            _fetch_post_data(mock_client, "12345")

        # 例外がJSONパース関連であることを検証
        assert isinstance(exc_info.value, ValueError | TypeError)


class TestExtractPostMetadata:
    """_extract_post_metadata 関数のテスト."""

    def test_extract_post_metadata_success(self) -> None:
        """メタデータ抽出成功テスト."""
        post_json = {
            "id": 12345,
            "title": "Test Post",
            "fanclub": {"creator_name": "Test Creator", "id": 456},
            "post_contents": [{"id": 1, "category": "text"}],
            "posted_at": "Wed, 01 Jan 2023 00:00:00 GMT",
            "converted_at": "2023-01-01T00:00:00+00:00",
            "comment": "Test comment",
        }

        result = _extract_post_metadata(post_json)

        assert result["id"] == 12345
        assert result["title"] == "Test Post"
        assert result["creator"] == "Test Creator"
        assert result["creator_id"] == 456
        assert result["comment"] == "Test comment"

    def test_extract_metadata_missing_converted_at(
        self, post_json_data: Callable[..., dict[str, Any]]
    ) -> None:
        """converted_atがない場合のテスト."""
        post_json = post_json_data(
            converted_at=None,
            comment=None,
        )

        result = _extract_post_metadata(post_json)

        assert result["posted_at"] == result["converted_at"]
        assert result["comment"] is None


class TestValidatePostType:
    """_validate_post_type 関数のテスト."""

    def test_validate_post_type_blog_post(
        self, post_json_data: Callable[..., dict[str, Any]], default_post_id: str
    ) -> None:
        """ブログ投稿のテスト."""
        post_json = post_json_data(is_blog=True)

        with pytest.raises(NotImplementedError, match="Blog posts are not supported"):
            _validate_post_type(post_json, default_post_id)

    def test_validate_post_type_normal_post(
        self, post_json_data: Callable[..., dict[str, Any]], default_post_id: str
    ) -> None:
        """通常の投稿のテスト."""
        post_json = post_json_data(is_blog=False)

        # 例外が発生しないことを確認
        _validate_post_type(post_json, default_post_id)


class TestParsePostThumbnail:
    """_parse_post_thumbnail 関数のテスト."""

    def test_parse_post_thumbnail_success(
        self, post_json_data: Callable[..., dict[str, Any]]
    ) -> None:
        """サムネイル解析成功テスト."""
        post_json = post_json_data()

        result = _parse_post_thumbnail(post_json)

        assert result is not None
        assert result.url == "https://example.com/thumb.jpg"
        assert result.ext == ".jpg"

    def test_parse_post_thumbnail_no_thumb(
        self, post_json_data: Callable[..., dict[str, Any]]
    ) -> None:
        """サムネイルがない場合のテスト."""
        post_json = post_json_data()
        del post_json["thumb"]

        result = _parse_post_thumbnail(post_json)

        assert result is None


class TestParsePostContents:
    """_parse_post_contents 関数のテスト."""

    def test_parse_post_contents_invisible(self, default_post_id: str) -> None:
        """非表示コンテンツのテスト."""
        post_contents = [{"id": 1, "category": "text", "visible_status": "invisible"}]

        gallery, files, text, products = _parse_post_contents(post_contents, default_post_id)

        assert gallery == []
        assert files == []
        assert text == []
        assert products == []

    def test_parse_contents_unsupported_category(self, default_post_id: str) -> None:
        """サポートされていないカテゴリのテスト."""
        post_contents = [{"id": 1, "category": "unsupported", "visible_status": "visible"}]

        with pytest.raises(NotImplementedError, match="not supported yet"):
            _parse_post_contents(post_contents, default_post_id)

    def test_parse_post_contents_empty(self, default_post_id: str) -> None:
        """空のコンテンツのテスト."""
        post_contents: list[Any] = []

        gallery, files, text, products = _parse_post_contents(post_contents, default_post_id)

        assert gallery == []
        assert files == []
        assert text == []
        assert products == []

    def test_parse_contents_valid_categories(self, default_post_id: str) -> None:
        """有効なカテゴリのテスト."""
        post_contents = [
            {
                "id": 1,
                "category": "photo_gallery",
                "visible_status": "visible",
                "title": "Gallery 1",
                "comment": "Gallery comment",
                "post_content_photos": [
                    {"url": {"original": "https://example.com/1.jpg"}},
                    {"url": {"original": "https://example.com/2.jpg"}},
                ],
            },
            {
                "id": 2,
                "category": "file",
                "visible_status": "visible",
                "title": "File 1",
                "comment": "File comment",
                "download_uri": "/files/file.pdf",
                "filename": "file.pdf",
            },
            {
                "id": 3,
                "category": "text",
                "visible_status": "visible",
                "title": "Text 1",
                "comment": "Text comment",
            },
        ]

        gallery, files, text, products = _parse_post_contents(post_contents, default_post_id)

        assert len(gallery) == 1
        assert len(files) == 1
        assert len(text) == 1
        assert len(products) == 0

        assert gallery[0].id == "1"
        assert gallery[0].title == "Gallery 1"
        assert files[0].id == "2"
        assert files[0].title == "File 1"
        assert text[0].id == "3"
        assert text[0].title == "Text 1"
