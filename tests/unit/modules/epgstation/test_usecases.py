"""EPGStationモジュール独立ユースケーステスト

他モジュールへの依存・参照は一切禁止
moro.modules.epgstation.* のみimport許可
"""

from unittest.mock import Mock

import pytest

from moro.modules.epgstation.domain import RecordingData, RecordingRepository
from moro.modules.epgstation.usecases import ListRecordingsUseCase
from tests.factories.epgstation_factories import RecordingDataFactory


@pytest.mark.unit
class TestListRecordingsUseCase:
    """ListRecordingsUseCase 単体テスト"""

    @pytest.fixture
    def mock_repository(self) -> Mock:
        """RepositoryのMock"""
        return Mock(spec=RecordingRepository)

    @pytest.fixture
    def usecase(self, mock_repository: Mock) -> ListRecordingsUseCase:
        """テスト対象UseCase"""
        return ListRecordingsUseCase(recording_repository=mock_repository)

    def test_execute_with_limit(
        self, usecase: ListRecordingsUseCase, mock_repository: Mock
    ) -> None:
        """制限数指定での録画一覧取得テスト"""
        # Given
        limit = 10
        test_recordings = [
            RecordingDataFactory.build(id=i, name=f"テスト番組{i}") for i in range(1, 6)
        ]
        mock_repository.get_all.return_value = test_recordings

        # When
        result = usecase.execute(limit=limit)

        # Then
        assert len(result) == 5
        assert all(isinstance(recording, RecordingData) for recording in result)
        assert result[0].name == "テスト番組1"
        assert result[4].name == "テスト番組5"
        mock_repository.get_all.assert_called_once_with(limit=limit)

    def test_execute_with_default_limit(
        self, usecase: ListRecordingsUseCase, mock_repository: Mock
    ) -> None:
        """デフォルト制限数での録画一覧取得テスト"""
        # Given
        test_recordings = [RecordingDataFactory.build(id=1)]
        mock_repository.get_all.return_value = test_recordings

        # When
        result = usecase.execute()

        # Then
        assert len(result) == 1
        mock_repository.get_all.assert_called_once_with(limit=100)

    def test_execute_empty_result(
        self, usecase: ListRecordingsUseCase, mock_repository: Mock
    ) -> None:
        """空の結果処理テスト"""
        # Given
        mock_repository.get_all.return_value = []

        # When
        result = usecase.execute(limit=50)

        # Then
        assert len(result) == 0
        mock_repository.get_all.assert_called_once_with(limit=50)

    def test_execute_large_limit(
        self, usecase: ListRecordingsUseCase, mock_repository: Mock
    ) -> None:
        """大きな制限数での処理テスト"""
        # Given
        limit = 1000
        test_recordings = [
            RecordingDataFactory.build(id=i)
            for i in range(1, 501)  # 500件
        ]
        mock_repository.get_all.return_value = test_recordings

        # When
        result = usecase.execute(limit=limit)

        # Then
        assert len(result) == 500
        mock_repository.get_all.assert_called_once_with(limit=limit)

    def test_execute_zero_limit(
        self, usecase: ListRecordingsUseCase, mock_repository: Mock
    ) -> None:
        """制限数0での処理テスト"""
        # Given
        limit = 0
        mock_repository.get_all.return_value = []

        # When
        result = usecase.execute(limit=limit)

        # Then
        assert len(result) == 0
        mock_repository.get_all.assert_called_once_with(limit=limit)

    def test_execute_repository_list_behavior(
        self, usecase: ListRecordingsUseCase, mock_repository: Mock
    ) -> None:
        """Repository List の動作確認テスト"""
        # Given
        test_recordings = [
            RecordingDataFactory.build(id=1, name="番組1"),
            RecordingDataFactory.build(id=2, name="番組2"),
            RecordingDataFactory.build(id=3, name="番組3"),
        ]

        mock_repository.get_all.return_value = test_recordings

        # When
        result = usecase.execute(limit=10)

        # Then
        assert len(result) == 3
        assert result[0].id == 1
        assert result[1].id == 2
        assert result[2].id == 3
        mock_repository.get_all.assert_called_once_with(limit=10)
