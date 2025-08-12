"""ListRecordingsUseCase のテスト"""

from unittest.mock import Mock

import pytest

from moro.modules.epgstation.domain import (
    RecordingData,
    TitleFilterService,
    VideoFile,
    VideoFileType,
)
from moro.modules.epgstation.usecases import ListRecordingsUseCase


class TestListRecordingsUseCase:
    """ListRecordingsUseCase のテストケース"""

    @pytest.fixture
    def sample_recordings(self) -> list[RecordingData]:
        """テスト用録画データ"""
        return [
            RecordingData(
                id=1,
                name="ニュース7",
                start_at=1700000000000,
                end_at=1700001800000,
                video_files=[
                    VideoFile(
                        id=1,
                        name="ニュース7.ts",
                        filename="news7.ts",
                        type=VideoFileType.TS,
                        size=1024 * 1024 * 100,
                    )
                ],
                is_recording=False,
                is_protected=False,
            ),
            RecordingData(
                id=2,
                name="朝のニュース",
                start_at=1700002000000,
                end_at=1700003800000,
                video_files=[
                    VideoFile(
                        id=2,
                        name="朝のニュース.ts",
                        filename="morning_news.ts",
                        type=VideoFileType.TS,
                        size=1024 * 1024 * 80,
                    )
                ],
                is_recording=False,
                is_protected=False,
            ),
            RecordingData(
                id=3,
                name="Drama Special",
                start_at=1700004000000,
                end_at=1700007600000,
                video_files=[
                    VideoFile(
                        id=3,
                        name="Drama Special.ts",
                        filename="drama_special.ts",
                        type=VideoFileType.ENCODED,
                        size=1024 * 1024 * 200,
                    )
                ],
                is_recording=True,
                is_protected=True,
            ),
        ]

    @pytest.fixture
    def mock_repository(self, sample_recordings: list[RecordingData]) -> Mock:
        """モックリポジトリ"""
        repo = Mock()
        repo.get_all.return_value = sample_recordings
        return repo

    @pytest.fixture
    def mock_filter_service(self) -> Mock:
        """モックフィルターサービス"""
        return Mock(spec=TitleFilterService)

    @pytest.fixture
    def usecase(self, mock_repository: Mock, mock_filter_service: Mock) -> ListRecordingsUseCase:
        """ListRecordingsUseCase インスタンス"""
        # 新しいコンストラクタシグネチャを想定
        return ListRecordingsUseCase(mock_repository, mock_filter_service)

    def test_execute_without_filter(
        self,
        usecase: ListRecordingsUseCase,
        mock_repository: Mock,
        mock_filter_service: Mock,
        sample_recordings: list[RecordingData],
    ) -> None:
        """フィルターなしでの実行テスト"""
        mock_filter_service.apply_filter.return_value = sample_recordings

        result = usecase.execute(limit=100)

        mock_repository.get_all.assert_called_once_with(limit=100)
        mock_filter_service.apply_filter.assert_called_once_with(sample_recordings, None, False)
        assert len(result) == 3

    def test_execute_with_title_filter(
        self,
        usecase: ListRecordingsUseCase,
        mock_repository: Mock,
        mock_filter_service: Mock,
        sample_recordings: list[RecordingData],
    ) -> None:
        """タイトルフィルター付きの実行テスト"""
        filtered_recordings = [sample_recordings[0], sample_recordings[1]]  # ニュース2件
        mock_filter_service.apply_filter.return_value = filtered_recordings

        result = usecase.execute(limit=100, title_filter="ニュース")

        mock_repository.get_all.assert_called_once_with(limit=100)
        mock_filter_service.apply_filter.assert_called_once_with(
            sample_recordings, "ニュース", False
        )
        assert len(result) == 2

    def test_execute_with_regex_filter(
        self,
        usecase: ListRecordingsUseCase,
        mock_repository: Mock,
        mock_filter_service: Mock,
        sample_recordings: list[RecordingData],
    ) -> None:
        """正規表現フィルター付きの実行テスト"""
        filtered_recordings = [sample_recordings[0]]  # ニュース7のみ
        mock_filter_service.apply_filter.return_value = filtered_recordings

        result = usecase.execute(limit=100, title_filter="^ニュース", regex=True)

        mock_repository.get_all.assert_called_once_with(limit=100)
        mock_filter_service.apply_filter.assert_called_once_with(
            sample_recordings, "^ニュース", True
        )
        assert len(result) == 1

    def test_execute_with_empty_filter_result(
        self, usecase: ListRecordingsUseCase, mock_repository: Mock, mock_filter_service: Mock
    ) -> None:
        """フィルター結果が空の場合のテスト"""
        mock_filter_service.apply_filter.return_value = []

        result = usecase.execute(limit=100, title_filter="存在しない番組")

        mock_filter_service.apply_filter.assert_called_once()
        assert len(result) == 0

    def test_execute_filter_error_propagation(
        self,
        usecase: ListRecordingsUseCase,
        mock_repository: Mock,
        mock_filter_service: Mock,
        sample_recordings: list[RecordingData],
    ) -> None:
        """フィルターエラーの伝搬テスト"""
        from moro.modules.epgstation.domain import RegexPatternError

        mock_filter_service.apply_filter.side_effect = RegexPatternError("無効な正規表現")

        with pytest.raises(RegexPatternError, match="無効な正規表現"):
            usecase.execute(limit=100, title_filter="[", regex=True)
