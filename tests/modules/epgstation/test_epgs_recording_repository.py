"""EPGStation 録画データリポジトリのテスト

TDD Red Phase: Repository テスト作成
"""

from typing import Any
from unittest.mock import Mock, patch

import httpx
import pytest

from moro.modules.epgstation.domain import VideoFileType
from moro.modules.epgstation.infrastructure import EPGStationRecordingRepository


class TestRecordingRepository:
    """録画データリポジトリのテスト"""

    def test_should_return_recordings_list_when_api_responds_successfully(self) -> None:
        """API成功時の録画データ取得テスト（モック使用）"""
        # モック設定
        mock_session_provider = Mock()
        mock_session_provider.get_cookies.return_value = {
            "session": "test_session",
            "_oauth2_proxy": "test_oauth",
        }

        mock_config = Mock()
        mock_config.base_url = "https://test.example.com"
        mock_config.timeout = 30.0
        mock_config.max_recordings = 1000

        repository = EPGStationRecordingRepository(
            session_provider=mock_session_provider, epgstation_config=mock_config
        )

        # API レスポンスのモックデータ
        mock_response_data = {
            "records": [
                {
                    "id": 123,
                    "name": "テスト番組",
                    "startAt": 1640995200000,  # 2022-01-01 00:00:00 JST
                    "endAt": 1640998800000,  # 2022-01-01 01:00:00 JST
                    "isRecording": False,
                    "isProtected": True,
                    "videoFiles": [
                        {
                            "id": 1,
                            "name": "テスト番組.ts",
                            "filename": "test_program.ts",
                            "type": "ts",
                            "size": 1073741824,  # 1GB
                        },
                        {
                            "id": 2,
                            "name": "テスト番組.mp4",
                            "filename": "test_program.mp4",
                            "type": "encoded",
                            "size": 536870912,  # 512MB
                        },
                    ],
                }
            ]
        }

        # HTTP クライアントのモック
        with patch("httpx.Client") as mock_client:
            mock_response = Mock()
            mock_response.json.return_value = mock_response_data
            mock_response.raise_for_status.return_value = None

            mock_client.return_value.__enter__.return_value.get.return_value = mock_response

            # テスト実行
            recordings = repository.get_all(limit=100)

        # アサーション
        assert len(recordings) == 1
        recording = recordings[0]

        assert recording.id == 123
        assert recording.name == "テスト番組"
        assert recording.start_at == 1640995200000
        assert recording.end_at == 1640998800000
        assert recording.is_recording is False
        assert recording.is_protected is True

        # ビデオファイルの検証
        assert len(recording.video_files) == 2

        ts_file = recording.video_files[0]
        assert ts_file.id == 1
        assert ts_file.name == "テスト番組.ts"
        assert ts_file.filename == "test_program.ts"
        assert ts_file.type == VideoFileType.TS
        assert ts_file.size == 1073741824

        encoded_file = recording.video_files[1]
        assert encoded_file.id == 2
        assert encoded_file.type == VideoFileType.ENCODED

    def test_should_handle_api_error_gracefully_when_server_unavailable(self) -> None:
        """APIエラー時の適切な例外処理テスト"""
        mock_session_provider = Mock()
        mock_session_provider.get_cookies.return_value = {"session": "test"}

        mock_config = Mock()
        mock_config.base_url = "https://test.example.com"
        mock_config.timeout = 30.0
        mock_config.max_recordings = 1000

        repository = EPGStationRecordingRepository(
            session_provider=mock_session_provider, epgstation_config=mock_config
        )

        # HTTP エラーのモック
        with patch("httpx.Client") as mock_client:
            mock_client.return_value.__enter__.return_value.get.side_effect = httpx.HTTPError(
                "Server error"
            )

            with pytest.raises(RuntimeError, match="EPGStation API アクセスエラー"):
                repository.get_all()

    def test_should_handle_empty_response_when_no_recordings(self) -> None:
        """録画データが0件の場合の処理テスト"""
        mock_session_provider = Mock()
        mock_session_provider.get_cookies.return_value = {"session": "test"}

        mock_config = Mock()
        mock_config.base_url = "https://test.example.com"
        mock_config.timeout = 30.0
        mock_config.max_recordings = 1000

        repository = EPGStationRecordingRepository(
            session_provider=mock_session_provider, epgstation_config=mock_config
        )

        # 空のレスポンス
        mock_response_data: dict[str, Any] = {"records": []}

        with patch("httpx.Client") as mock_client:
            mock_response = Mock()
            mock_response.json.return_value = mock_response_data
            mock_response.raise_for_status.return_value = None

            mock_client.return_value.__enter__.return_value.get.return_value = mock_response

            recordings = repository.get_all()

        assert recordings == []

    def test_should_handle_malformed_video_file_data(self) -> None:
        """不正なビデオファイルデータの処理テスト"""
        mock_session_provider = Mock()
        mock_session_provider.get_cookies.return_value = {"session": "test"}

        mock_config = Mock()
        mock_config.base_url = "https://test.example.com"
        mock_config.timeout = 30.0
        mock_config.max_recordings = 1000

        repository = EPGStationRecordingRepository(
            session_provider=mock_session_provider, epgstation_config=mock_config
        )

        # 不正なビデオファイルデータを含むレスポンス
        mock_response_data = {
            "records": [
                {
                    "id": 123,
                    "name": "テスト番組",
                    "startAt": 1640995200000,
                    "endAt": 1640998800000,
                    "isRecording": False,
                    "isProtected": False,
                    "videoFiles": [
                        {
                            "id": 1,
                            "name": "正常なファイル",
                            "filename": "normal.ts",
                            "type": "ts",
                            "size": 1024,
                        },
                        {
                            # 不正なデータ（必須フィールド不足）
                            "id": 2,
                            "name": "",  # 空文字列（無効）
                            "filename": "invalid.ts",
                            "type": "ts",
                            "size": 0,  # 0バイト（無効）
                        },
                        {
                            "id": 3,
                            "name": "別の正常なファイル",
                            "filename": "normal2.ts",
                            "type": "encoded",
                            "size": 2048,
                        },
                    ],
                }
            ]
        }

        with patch("httpx.Client") as mock_client:
            mock_response = Mock()
            mock_response.json.return_value = mock_response_data
            mock_response.raise_for_status.return_value = None

            mock_client.return_value.__enter__.return_value.get.return_value = mock_response

            recordings = repository.get_all()

        # 録画データは作成されるが、不正なビデオファイルは除外される
        assert len(recordings) == 1
        recording = recordings[0]

        # 正常なビデオファイル2個のみが含まれる（不正なものは除外）
        assert len(recording.video_files) == 2
        assert all(vf.size > 0 for vf in recording.video_files)  # 全て正常なサイズ

    def test_should_use_default_values_for_missing_fields(self) -> None:
        """必須フィールドが不足している場合のデフォルト値使用テスト"""
        mock_session_provider = Mock()
        mock_session_provider.get_cookies.return_value = {"session": "test"}

        mock_config = Mock()
        mock_config.base_url = "https://test.example.com"
        mock_config.timeout = 30.0
        mock_config.max_recordings = 1000

        repository = EPGStationRecordingRepository(
            session_provider=mock_session_provider, epgstation_config=mock_config
        )

        # 最小限のフィールドのみのレスポンス
        mock_response_data = {
            "records": [
                {
                    "id": 123,
                    # name, startAt, endAt, isRecording, isProtected が不足
                    "videoFiles": [],
                }
            ]
        }

        with patch("httpx.Client") as mock_client:
            mock_response = Mock()
            mock_response.json.return_value = mock_response_data
            mock_response.raise_for_status.return_value = None

            mock_client.return_value.__enter__.return_value.get.return_value = mock_response

            recordings = repository.get_all()

        # デフォルト値が使用されることを確認
        assert len(recordings) == 1
        recording = recordings[0]

        assert recording.id == 123
        assert recording.name == "不明な番組"
        assert recording.start_at == 0
        assert recording.end_at == 1  # start_at より大きい値
        assert recording.is_recording is False
        assert recording.is_protected is False
        assert recording.video_files == []

    def test_should_respect_limit_parameter(self) -> None:
        """Limit パラメータが適切に適用されることをテスト"""
        mock_session_provider = Mock()
        mock_session_provider.get_cookies.return_value = {"session": "test"}

        mock_config = Mock()
        mock_config.base_url = "https://test.example.com"
        mock_config.timeout = 30.0
        mock_config.max_recordings = 500  # 最大制限

        repository = EPGStationRecordingRepository(
            session_provider=mock_session_provider, epgstation_config=mock_config
        )

        with patch("httpx.Client") as mock_client:
            mock_response = Mock()
            mock_response.json.return_value = {"records": []}
            mock_response.raise_for_status.return_value = None

            mock_client_instance = mock_client.return_value.__enter__.return_value
            mock_client_instance.get.return_value = mock_response

            # 制限を超える値でテスト
            repository.get_all(limit=1000, offset=10)

            # get メソッドの呼び出し引数を検証
            mock_client_instance.get.assert_called_once()
            call_args = mock_client_instance.get.call_args

            # params の内容を確認
            params = call_args.kwargs["params"]
            assert params["limit"] == 500  # max_recordings で制限される
            assert params["offset"] == 10
            assert params["isHalfWidth"] is True

    def test_should_call_session_provider_for_authentication(self) -> None:
        """認証用にセッションプロバイダーが呼ばれることをテスト"""
        mock_session_provider = Mock()
        mock_session_provider.get_cookies.return_value = {
            "custom_session": "custom_value",
            "custom_csrf": "csrf_value",
        }

        mock_config = Mock()
        mock_config.base_url = "https://test.example.com"
        mock_config.timeout = 30.0
        mock_config.max_recordings = 1000

        repository = EPGStationRecordingRepository(
            session_provider=mock_session_provider, epgstation_config=mock_config
        )

        with patch("httpx.Client") as mock_client:
            mock_response = Mock()
            mock_response.json.return_value = {"records": []}
            mock_response.raise_for_status.return_value = None

            mock_client_instance = mock_client.return_value.__enter__.return_value
            mock_client_instance.get.return_value = mock_response

            repository.get_all()

        # セッションプロバイダーが呼ばれたことを確認
        mock_session_provider.get_cookies.assert_called_once()

        # Cookie が正しく渡されたことを確認
        call_args = mock_client_instance.get.call_args
        cookies = call_args.kwargs["cookies"]
        assert cookies == {"custom_session": "custom_value", "custom_csrf": "csrf_value"}
