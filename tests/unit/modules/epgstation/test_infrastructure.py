"""EPGStationモジュール独立インフラテスト

外部システム連携部分の単体テスト
Mock使用による外部依存分離
"""

from unittest.mock import Mock, patch

import pytest

from moro.modules.epgstation.domain import RecordingData
from moro.modules.epgstation.infrastructure import EPGStationRecordingRepository


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
        from moro.modules.epgstation.config import EPGStationConfig

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
