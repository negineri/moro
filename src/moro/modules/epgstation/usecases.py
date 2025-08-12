"""EPGStation ユースケース実装"""

import logging

from injector import inject

from moro.modules.epgstation.domain import RecordingData, RecordingRepository, TitleFilterService

logger = logging.getLogger(__name__)


@inject
class ListRecordingsUseCase:
    """録画一覧取得ユースケース"""

    def __init__(
        self,
        recording_repository: "RecordingRepository",
        title_filter_service: "TitleFilterService",
    ) -> None:
        """初期化

        Args:
            recording_repository: 録画データリポジトリ
            title_filter_service: タイトルフィルターサービス
        """
        self._repository = recording_repository
        self._filter_service = title_filter_service

    def execute(
        self, limit: int = 100, title_filter: str | None = None, regex: bool = False
    ) -> list[RecordingData]:
        """録画一覧を取得・フィルタリング

        Args:
            limit: 表示する録画数の上限
            title_filter: タイトルフィルター条件
            regex: 正規表現モードフラグ

        Returns:
            フィルタリング後の録画データリスト
        """
        try:
            recordings = self._repository.get_all(limit=limit)
            return self._filter_service.apply_filter(recordings, title_filter, regex)
        except Exception as e:
            logger.error(f"Failed to get recordings: {e}")
            raise
