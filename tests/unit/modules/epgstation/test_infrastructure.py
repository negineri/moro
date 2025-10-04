"""EPGStationモジュール独立インフラテスト

外部システム連携部分の単体テスト
Mock使用による外部依存分離
"""

from collections.abc import Generator
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from moro.modules.common import CommonConfig
from moro.modules.epgstation.config import EPGStationConfig
from moro.modules.epgstation.domain import RecordingData
from moro.modules.epgstation.infrastructure import (
    CookieCacheManager,
    EPGStationRecordingRepository,
    SeleniumEPGStationSessionProvider,
)


@pytest.fixture
def cookie_cache_manager(tmp_path: Path) -> CookieCacheManager:
    """CookieCacheManager テスト用インスタンス"""
    tmp_path.mkdir(parents=True, exist_ok=True)
    return CookieCacheManager(str(tmp_path / "cookie_cache.json"), ttl_seconds=3600)


@pytest.fixture
def selenium_session_provider(
    common_config: CommonConfig,
) -> Generator[SeleniumEPGStationSessionProvider, None, None]:
    """SeleniumEPGStationSessionProvider テスト用インスタンス"""
    with (
        patch("moro.modules.epgstation.infrastructure.webdriver") as mock_webdriver,
        patch("moro.modules.epgstation.infrastructure.httpx") as mock_httpx,
        patch("moro.modules.epgstation.infrastructure.input"),
    ):
        # Selenium WebDriver Mock設定
        mock_driver = MagicMock()
        mock_driver.get_cookies.return_value = [{"name": "session_id", "value": "test123"}]
        mock_webdriver.Chrome.return_value.__enter__.return_value = mock_driver
        mock_webdriver.Chrome.return_value.__exit__.return_value = None

        # httpx Mock設定
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_client = MagicMock()
        mock_client.post.return_value = mock_response
        mock_httpx.Client.return_value = mock_client

        epgstation_config = EPGStationConfig(base_url="http://example.com")

        yield SeleniumEPGStationSessionProvider(common_config, epgstation_config)


@pytest.mark.unit
class TestCookieCacheManager:
    """CookieCacheManager 単体テスト"""

    def test_get_cookies_returns_empty_dict_when_no_cookies_set(
        self,
        cookie_cache_manager: CookieCacheManager,
    ) -> None:
        """クッキー未設定時のNone返却テスト"""
        result = cookie_cache_manager.load_cookies()
        assert result is None

    def test_save_and_load_cookies(self, cookie_cache_manager: CookieCacheManager) -> None:
        """クッキーの保存と読み込みテスト"""
        cookie_cache_manager.save_cookies({"session_id": "test123"})
        result = cookie_cache_manager.load_cookies()
        assert result == {"session_id": "test123"}
        with open(cookie_cache_manager.cache_file_path) as f:
            data = f.read()
            assert '{"session_id": "test123"}' in data


@pytest.mark.unit
class TestSeleniumEPGStationSessionProvider:
    """SeleniumEPGStationSessionProvider 単体テスト"""

    def test_get_cookies_returns_valid_cookies(
        self, selenium_session_provider: SeleniumEPGStationSessionProvider
    ) -> None:
        """クッキー取得テスト"""
        result = selenium_session_provider.get_cookies()
        assert result == {"session_id": "test123"}


@pytest.mark.unit
class TestEPGStationRecordingRepository:
    """EPGStationRecordingRepository 単体テスト"""

    @pytest.fixture
    def mock_session_provider(self) -> Mock:
        """SessionProvider Mock"""
        provider = Mock()
        provider.get_cookies.return_value = {"session_id": "test123"}
        return provider

    @pytest.fixture
    def mock_config(self) -> Mock:
        """Config Mock"""
        config = Mock(spec=EPGStationConfig)
        config.base_url = "http://localhost:8888"
        config.max_recordings = 1000
        config.timeout = 30.0
        return config

    @pytest.fixture
    def repository(
        self, mock_session_provider: Mock, mock_config: Mock
    ) -> EPGStationRecordingRepository:
        """テスト対象Repository"""
        return EPGStationRecordingRepository(
            session_provider=mock_session_provider, epgstation_config=mock_config
        )

    @patch("httpx.Client")
    def test_get_all_success(
        self, mock_client_class: Mock, repository: EPGStationRecordingRepository
    ) -> None:
        """録画一覧取得成功テスト"""
        # Given
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "records": [
                {
                    "id": 123,
                    "name": "テスト番組",
                    "startAt": 1691683200000,
                    "endAt": 1691686800000,
                    "videoFiles": [],
                    "isRecording": False,
                    "isProtected": False,
                }
            ]
        }

        mock_client = Mock()
        mock_client.get.return_value = mock_response
        mock_client.__enter__ = Mock(return_value=mock_client)
        mock_client.__exit__ = Mock(return_value=None)
        mock_client_class.return_value = mock_client

        # When
        result = repository.get_all(limit=10)

        # Then
        assert len(result) == 1
        assert isinstance(result[0], RecordingData)
        assert result[0].id == 123
        assert result[0].name == "テスト番組"

    @patch("httpx.Client")
    def test_get_all_empty_result(
        self, mock_client_class: Mock, repository: EPGStationRecordingRepository
    ) -> None:
        """空の録画一覧取得テスト"""
        # Given
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"records": []}

        mock_client = Mock()
        mock_client.get.return_value = mock_response
        mock_client.__enter__ = Mock(return_value=mock_client)
        mock_client.__exit__ = Mock(return_value=None)
        mock_client_class.return_value = mock_client

        # When
        result = repository.get_all(limit=50)

        # Then
        assert len(result) == 0

    @patch("httpx.Client")
    def test_get_all_with_authentication(
        self, mock_client_class: Mock, repository: EPGStationRecordingRepository
    ) -> None:
        """認証情報付きHTTPリクエストテスト"""
        # Given
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"records": []}

        mock_client = Mock()
        mock_client.get.return_value = mock_response
        mock_client.__enter__ = Mock(return_value=mock_client)
        mock_client.__exit__ = Mock(return_value=None)
        mock_client_class.return_value = mock_client

        # When
        repository.get_all(limit=5)

        # Then
        mock_client.get.assert_called_once()
        call_args = mock_client.get.call_args
        # Cookie認証確認
        cookies = call_args[1]["cookies"]
        assert cookies == {"session_id": "test123"}
