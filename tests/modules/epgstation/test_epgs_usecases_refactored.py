"""EPGStation ユースケース層テスト（リファクタリング後）"""

import logging
from unittest.mock import Mock

import pytest

from moro.modules.epgstation.domain import (
    RecordingData,
    RecordingRepository,
    VideoFile,
    VideoFileType,
)
from moro.modules.epgstation.usecases import ListRecordingsUseCase


class TestListRecordingsUseCase:
    """ListRecordingsUseCase のテストクラス"""

    def test_execute_returns_recordings_from_repository(self) -> None:
        """正常系：リポジトリからの録画データ取得"""
        # Given
        mock_repo = Mock(spec=RecordingRepository)
        expected_recordings = [
            RecordingData(
                id=1,
                name="テスト番組",
                start_at=1691683200000,
                end_at=1691686800000,
                video_files=[],
                is_recording=False,
                is_protected=False,
            )
        ]
        mock_repo.get_all.return_value = expected_recordings

        mock_filter_service = Mock()
        mock_filter_service.apply_filter.return_value = expected_recordings
        use_case = ListRecordingsUseCase(mock_repo, mock_filter_service)

        # When
        result = use_case.execute()

        # Then
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0].id == 1
        assert result[0].name == "テスト番組"
        mock_repo.get_all.assert_called_once_with(limit=100)

    def test_execute_forwards_limit_parameter(self) -> None:
        """パラメータ転送：limit値がリポジトリに正しく渡される"""
        # Given
        mock_repo = Mock(spec=RecordingRepository)
        mock_repo.get_all.return_value = []

        mock_filter_service = Mock()
        mock_filter_service.apply_filter.return_value = []
        use_case = ListRecordingsUseCase(mock_repo, mock_filter_service)

        # When
        result = use_case.execute(limit=50)

        # Then
        assert result == []
        mock_repo.get_all.assert_called_once_with(limit=50)

    def test_execute_raises_exception_on_repository_failure(self) -> None:
        """異常系：リポジトリ例外の適切な委譲"""
        # Given
        mock_repo = Mock(spec=RecordingRepository)
        original_error = Exception("Connection timeout")
        mock_repo.get_all.side_effect = original_error

        mock_filter_service = Mock()
        use_case = ListRecordingsUseCase(mock_repo, mock_filter_service)

        # When & Then
        with pytest.raises(Exception, match="Connection timeout") as exc_info:
            use_case.execute()

        assert exc_info.value is original_error

    def test_execute_logs_errors_appropriately(self, caplog: pytest.LogCaptureFixture) -> None:
        """ログ出力：エラー時の適切なログレベル・メッセージ"""
        # Given
        mock_repo = Mock(spec=RecordingRepository)
        error_message = "Database connection failed"
        mock_repo.get_all.side_effect = Exception(error_message)

        mock_filter_service = Mock()
        use_case = ListRecordingsUseCase(mock_repo, mock_filter_service)

        # When
        with (
            pytest.raises(Exception, match="Database connection failed"),
            caplog.at_level(logging.ERROR),
        ):
            use_case.execute()

        # Then
        assert len(caplog.records) == 1
        assert caplog.records[0].levelname == "ERROR"
        assert "Failed to get recordings" in caplog.records[0].message
        assert error_message in caplog.records[0].message

    def test_execute_returns_multiple_recordings(self) -> None:
        """複数録画データの取得確認"""
        # Given
        mock_repo = Mock(spec=RecordingRepository)
        expected_recordings = [
            RecordingData(
                id=1,
                name="番組1",
                start_at=1691683200000,
                end_at=1691686800000,
                video_files=[
                    VideoFile(
                        id=1,
                        name="video1.ts",
                        filename="video1.ts",
                        type=VideoFileType.TS,
                        size=1234567890,
                    )
                ],
                is_recording=False,
                is_protected=True,
            ),
            RecordingData(
                id=2,
                name="番組2",
                start_at=1691690000000,
                end_at=1691693600000,
                video_files=[],
                is_recording=True,
                is_protected=False,
            ),
        ]
        mock_repo.get_all.return_value = expected_recordings

        mock_filter_service = Mock()
        mock_filter_service.apply_filter.return_value = expected_recordings
        use_case = ListRecordingsUseCase(mock_repo, mock_filter_service)

        # When
        result = use_case.execute()

        # Then
        assert len(result) == 2
        assert result[0].id == 1
        assert result[0].name == "番組1"
        assert len(result[0].video_files) == 1
        assert result[1].id == 2
        assert result[1].name == "番組2"
        assert len(result[1].video_files) == 0
