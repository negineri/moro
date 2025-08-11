"""EPGStation セッションプロバイダーのテスト

TDD Red Phase: 認証プロバイダーテスト作成
"""

import json
import os
import tempfile
import time
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from injector import Injector

from moro.modules.epgstation.infrastructure import (
    CookieCacheManager,
    SeleniumEPGStationSessionProvider,
)


class TestSessionProvider:
    """セッションプロバイダーのテスト"""

    def test_should_return_cached_cookies_when_session_valid(self) -> None:
        """有効なキャッシュがある場合の動作テスト"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # モック設定を作成
            mock_common_config = Mock()
            mock_common_config.user_cache_dir = temp_dir

            mock_epgstation_config = Mock()
            mock_epgstation_config.enable_cookie_cache = True
            mock_epgstation_config.chrome_data_dir = "test_chrome"
            mock_epgstation_config.cookie_cache_file = "test_cookies.json"
            mock_epgstation_config.cookie_cache_ttl = 3600

            provider = SeleniumEPGStationSessionProvider(
                common_config=mock_common_config, epgstation_config=mock_epgstation_config
            )

            # 有効なキャッシュを事前に作成
            cache_file = Path(temp_dir) / "test_cookies.json"
            cache_data = {
                "timestamp": time.time(),  # 現在時刻（有効）
                "cookies": {"session": "test_session", "_oauth2_proxy": "test_oauth"},
            }
            cache_file.write_text(json.dumps(cache_data))

            # テスト実行
            cookies = provider.get_cookies()

            # アサーション
            assert cookies == {"session": "test_session", "_oauth2_proxy": "test_oauth"}

    def test_should_perform_fresh_login_when_cache_expired(self) -> None:
        """キャッシュ期限切れ時の新規認証テスト（モック使用）"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # モック設定
            mock_common_config = Mock()
            mock_common_config.user_cache_dir = temp_dir

            mock_epgstation_config = Mock()
            mock_epgstation_config.enable_cookie_cache = True
            mock_epgstation_config.chrome_data_dir = "test_chrome"
            mock_epgstation_config.cookie_cache_file = "test_cookies.json"
            mock_epgstation_config.cookie_cache_ttl = 3600
            mock_epgstation_config.base_url = "https://test.example.com"

            provider = SeleniumEPGStationSessionProvider(
                common_config=mock_common_config, epgstation_config=mock_epgstation_config
            )

            # 期限切れキャッシュを作成
            cache_file = Path(temp_dir) / "test_cookies.json"
            cache_data = {
                "timestamp": time.time() - 7200,  # 2時間前（期限切れ）
                "cookies": {"old_session": "expired"},
            }
            cache_file.write_text(json.dumps(cache_data))

            # Selenium のモック
            mock_driver = Mock()
            mock_driver.get_cookies.return_value = [
                {"name": "session", "value": "new_session"},
                {"name": "_oauth2_proxy", "value": "new_oauth"},
            ]

            with patch("selenium.webdriver.Chrome") as mock_chrome:
                mock_chrome.return_value.__enter__.return_value = mock_driver
                with patch("builtins.input", return_value=""):  # Enter キー入力をモック
                    cookies = provider.get_cookies()

            # アサーション
            assert cookies == {"session": "new_session", "_oauth2_proxy": "new_oauth"}

            # 新しいキャッシュが保存されていることを確認
            assert cache_file.exists()
            cached_data = json.loads(cache_file.read_text())
            assert cached_data["cookies"] == {
                "session": "new_session",
                "_oauth2_proxy": "new_oauth",
            }

    def test_should_perform_fresh_login_when_cache_disabled(self) -> None:
        """キャッシュが無効な場合の認証テスト"""
        with tempfile.TemporaryDirectory() as temp_dir:
            mock_common_config = Mock()
            mock_common_config.user_cache_dir = temp_dir

            mock_epgstation_config = Mock()
            mock_epgstation_config.enable_cookie_cache = False  # キャッシュ無効
            mock_epgstation_config.chrome_data_dir = "test_chrome"
            mock_epgstation_config.cookie_cache_file = "test_cookies.json"
            mock_epgstation_config.cookie_cache_ttl = 3600
            mock_epgstation_config.base_url = "https://test.example.com"

            provider = SeleniumEPGStationSessionProvider(
                common_config=mock_common_config, epgstation_config=mock_epgstation_config
            )

            # Selenium のモック
            mock_driver = Mock()
            mock_driver.get_cookies.return_value = [{"name": "session", "value": "fresh_session"}]

            with patch("selenium.webdriver.Chrome") as mock_chrome:
                mock_chrome.return_value.__enter__.return_value = mock_driver
                with patch("builtins.input", return_value=""):
                    cookies = provider.get_cookies()

            assert cookies == {"session": "fresh_session"}

    def test_should_handle_selenium_authentication_failure(self) -> None:
        """Selenium 認証失敗時のエラーハンドリングテスト"""
        with tempfile.TemporaryDirectory() as temp_dir:
            mock_common_config = Mock()
            mock_common_config.user_cache_dir = temp_dir

            mock_epgstation_config = Mock()
            mock_epgstation_config.enable_cookie_cache = False
            mock_epgstation_config.chrome_data_dir = "test_chrome"
            mock_epgstation_config.cookie_cache_file = "test_cookies.json"
            mock_epgstation_config.cookie_cache_ttl = 3600
            mock_epgstation_config.base_url = "https://test.example.com"

            provider = SeleniumEPGStationSessionProvider(
                common_config=mock_common_config, epgstation_config=mock_epgstation_config
            )

            with patch("selenium.webdriver.Chrome", side_effect=Exception("WebDriver failed")):
                with pytest.raises(RuntimeError, match="認証に失敗しました"):
                    provider.get_cookies()


class TestCookieCacheManager:
    """Cookie キャッシュマネージャーのテスト"""

    def test_should_save_and_load_cookies_successfully(self) -> None:
        """Cookie の保存と読み込みが正常に動作することをテスト"""
        with tempfile.TemporaryDirectory() as temp_dir:
            cache_file = os.path.join(temp_dir, "test_cache.json")
            manager = CookieCacheManager(cache_file, 3600)

            test_cookies = {"session": "test123", "csrf": "abc456"}

            # 保存
            manager.save_cookies(test_cookies)

            # 読み込み
            loaded_cookies = manager.load_cookies()

            assert loaded_cookies == test_cookies

    def test_should_return_none_when_cache_file_not_exists(self) -> None:
        """キャッシュファイルが存在しない場合にNoneを返すことをテスト"""
        with tempfile.TemporaryDirectory() as temp_dir:
            non_existent_file = os.path.join(temp_dir, "non_existent_cache.json")
            manager = CookieCacheManager(non_existent_file, 3600)

            result = manager.load_cookies()
            assert result is None

    def test_should_return_none_when_cache_expired(self) -> None:
        """キャッシュが期限切れの場合にNoneを返すことをテスト"""
        with tempfile.TemporaryDirectory() as temp_dir:
            cache_file = os.path.join(temp_dir, "expired_cache.json")
            manager = CookieCacheManager(cache_file, 1)  # 1秒のTTL

            # 過去のタイムスタンプでキャッシュを作成
            cache_data = {
                "timestamp": time.time() - 10,  # 10秒前
                "cookies": {"session": "expired"},
            }
            with open(cache_file, "w") as f:
                json.dump(cache_data, f)

            result = manager.load_cookies()
            assert result is None

    def test_should_return_none_when_cache_file_corrupted(self) -> None:
        """破損したキャッシュファイルの場合にNoneを返すことをテスト"""
        with tempfile.TemporaryDirectory() as temp_dir:
            cache_file = os.path.join(temp_dir, "corrupted_cache.json")

            # 不正なJSONファイルを作成
            with open(cache_file, "w") as f:
                f.write("invalid json content")

            manager = CookieCacheManager(cache_file, 3600)
            result = manager.load_cookies()
            assert result is None

    def test_should_create_cache_directory_when_not_exists(self) -> None:
        """キャッシュディレクトリが存在しない場合に作成することをテスト"""
        with tempfile.TemporaryDirectory() as temp_dir:
            nested_cache_file = os.path.join(temp_dir, "subdir", "cache.json")
            manager = CookieCacheManager(nested_cache_file, 3600)

            test_cookies = {"test": "value"}
            manager.save_cookies(test_cookies)

            # ディレクトリとファイルが作成されていることを確認
            assert os.path.exists(nested_cache_file)
            assert os.path.isdir(os.path.dirname(nested_cache_file))

    def test_should_set_secure_file_permissions_when_saving(self) -> None:
        """Cookie 保存時にファイル権限が600に設定されることをテスト"""
        with tempfile.TemporaryDirectory() as temp_dir:
            cache_file = os.path.join(temp_dir, "secure_cache.json")
            manager = CookieCacheManager(cache_file, 3600)

            test_cookies = {"secure": "cookie"}
            manager.save_cookies(test_cookies)

            # ファイル権限を確認（600 = オーナーのみ読み書き）
            file_mode = os.stat(cache_file).st_mode
            expected_permissions = 0o600
            assert (file_mode & 0o777) == expected_permissions


class TestSessionValidation:
    """セッション有効性検証のテスト"""

    def test_should_validate_session_with_required_cookies(self) -> None:
        """必要な Cookie が存在する場合にセッションが有効と判定されることをテスト"""
        with tempfile.TemporaryDirectory() as temp_dir:
            mock_common_config = Mock()
            mock_common_config.user_cache_dir = temp_dir

            mock_epgstation_config = Mock()
            mock_epgstation_config.enable_cookie_cache = True
            mock_epgstation_config.chrome_data_dir = "test_chrome"
            mock_epgstation_config.cookie_cache_file = "test_cookies.json"
            mock_epgstation_config.cookie_cache_ttl = 3600

            provider = SeleniumEPGStationSessionProvider(
                common_config=mock_common_config, epgstation_config=mock_epgstation_config
            )

        # 必要な Cookie を含む辞書
        valid_cookies = {"session": "valid_session", "_oauth2_proxy": "valid_oauth"}
        assert provider._is_session_valid(valid_cookies) is True

        # session のみ
        session_only = {"session": "valid_session"}
        assert provider._is_session_valid(session_only) is True

        # _oauth2_proxy のみ
        oauth_only = {"_oauth2_proxy": "valid_oauth"}
        assert provider._is_session_valid(oauth_only) is True

    def test_should_invalidate_session_without_required_cookies(self) -> None:
        """必要な Cookie が存在しない場合にセッションが無効と判定されることをテスト"""
        with tempfile.TemporaryDirectory() as temp_dir:
            mock_common_config = Mock()
            mock_common_config.user_cache_dir = temp_dir

            mock_epgstation_config = Mock()
            mock_epgstation_config.enable_cookie_cache = True
            mock_epgstation_config.chrome_data_dir = "test_chrome"
            mock_epgstation_config.cookie_cache_file = "test_cookies.json"
            mock_epgstation_config.cookie_cache_ttl = 3600

            provider = SeleniumEPGStationSessionProvider(
                common_config=mock_common_config, epgstation_config=mock_epgstation_config
            )

        # 空の Cookie 辞書
        empty_cookies: dict[str, str] = {}
        assert provider._is_session_valid(empty_cookies) is False

        # 不要な Cookie のみ
        irrelevant_cookies: dict[str, str] = {"some_other_cookie": "value"}
        assert provider._is_session_valid(irrelevant_cookies) is False

    def test_should_handle_invalid_json_response(self, injector: Injector) -> None:
        """Version エンドポイントの呼び出しで無効な JSON が返された場合のハンドリング"""
        provider = injector.get(SeleniumEPGStationSessionProvider)

        with patch("moro.modules.epgstation.infrastructure.httpx.get") as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = {"version": "1.0.0"}
            assert provider._is_session_valid({}) is True

            mock_get.return_value.json.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)
            assert provider._is_session_valid({}) is False
