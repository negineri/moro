"""Fantia API実統合テスト - 最小限

実際のAPI呼び出しによる統合テスト
本当に必要な統合テストのみ実装
"""

from pathlib import Path

import pytest

from moro.config.settings import ConfigRepository
from moro.modules.fantia.infrastructure import SeleniumSessionIdProvider


@pytest.mark.integration
@pytest.mark.slow
class TestFantiaAPIIntegration:
    """Fantia API統合テスト"""

    @pytest.fixture
    def config(self, tmp_path: Path) -> ConfigRepository:
        """テスト用ConfigRepository"""
        from moro.modules.common import CommonConfig
        from moro.modules.fantia.config import FantiaConfig

        config = ConfigRepository()
        config.common = CommonConfig(
            user_data_dir=str(tmp_path / "user_data"),
            user_cache_dir=str(tmp_path / "cache"),
            working_dir=str(tmp_path / "working"),
            jobs=2,
        )
        config.fantia = FantiaConfig()
        return config

    def test_session_provider_initialization(self, config: ConfigRepository) -> None:
        """SessionProvider初期化統合テスト"""
        # Given & When
        try:
            provider = SeleniumSessionIdProvider(config=config.common, fantia_config=config.fantia)
            # Then
            assert provider is not None
            assert hasattr(provider, "get_cookies")
        except ImportError:
            pytest.skip("Selenium not available in test environment")

    @pytest.mark.skip_in_ci
    def test_real_api_connection_health(self, config: ConfigRepository) -> None:
        """実API接続ヘルスチェック

        Note: CIでは実行しない（環境依存）
        """
        import httpx

        try:
            # 実際のFantiaサイトへの接続確認
            response = httpx.get("https://fantia.jp", timeout=10.0)
            assert response.status_code in [200, 302, 403]  # 403はログイン要求
        except httpx.RequestError:
            pytest.skip("Network connection not available")

    @pytest.mark.skip_in_ci
    def test_selenium_webdriver_availability(self, config: ConfigRepository) -> None:
        """WebDriverの利用可能性確認テスト

        Note: CIでは実行しない（WebDriver環境依存）
        """
        try:
            from selenium import webdriver
            from selenium.webdriver.chrome.options import Options

            # ヘッドレスモードでの起動確認のみ
            options = Options()
            options.add_argument("--headless")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")

            with webdriver.Chrome(options=options) as driver:
                # 基本動作確認のみ（Fantiaサイトにはアクセスしない）
                driver.get("about:blank")
                assert driver.current_url == "about:blank"

        except ImportError:
            pytest.skip("Selenium WebDriver not available")
        except Exception as e:
            pytest.skip(f"WebDriver initialization failed: {e}")


@pytest.mark.integration
class TestFantiaConfigIntegration:
    """Fantia設定統合テスト"""

    def test_config_integration_with_file_downloader(self, tmp_path: Path) -> None:
        """設定とFileDownloaderの統合テスト"""
        # Given
        from moro.config.settings import ConfigRepository
        from moro.modules.common import CommonConfig
        from moro.modules.fantia.config import FantiaConfig
        from moro.modules.fantia.infrastructure import FantiaFileDownloader

        config = ConfigRepository()
        config.common = CommonConfig(
            user_data_dir=str(tmp_path / "user_data"),
            user_cache_dir=str(tmp_path / "cache"),
            working_dir=str(tmp_path / "working"),
            jobs=2,
        )
        config.fantia = FantiaConfig()

        # When
        from unittest.mock import Mock

        from moro.modules.fantia import FantiaClient

        # SessionIdProviderをモック
        mock_session_provider = Mock()
        mock_session_provider.get_session_id.return_value = "test_session_id"

        # FantiaClientを作成
        client = FantiaClient(config=config.fantia, session_provider=mock_session_provider)
        downloader = FantiaFileDownloader(client)

        # Then
        assert downloader is not None
        assert hasattr(downloader, "download_file")
        assert hasattr(downloader, "download_all_content")
