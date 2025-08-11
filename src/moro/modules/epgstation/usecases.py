"""EPGStation ユースケース実装"""

import logging

from injector import inject

from moro.modules.epgstation.domain import RecordingData, RecordingRepository

logger = logging.getLogger(__name__)


@inject
class ListRecordingsUseCase:
    """録画一覧取得ユースケース"""

    def __init__(self, recording_repository: "RecordingRepository") -> None:
        """初期化

        Args:
            recording_repository: 録画データリポジトリ
        """
        self._repository = recording_repository

    def execute(self, limit: int = 100) -> list[RecordingData]:
        """録画一覧を取得（純粋ビジネスロジック）

        Args:
            limit: 表示する録画数の上限

        Returns:
            録画データリスト
        """
        try:
            return self._repository.get_all(limit=limit)
        except Exception as e:
            logger.error(f"Failed to get recordings: {e}")
            raise
