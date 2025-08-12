"""EPGStation ドメインモデル"""

from enum import Enum
from re import Pattern
from typing import Annotated, Protocol

from pydantic import BaseModel, Field


class FilterError(Exception):
    """フィルター処理エラー基底クラス"""

    pass


class RegexPatternError(FilterError):
    """正規表現パターンエラー"""

    pass


class VideoFileType(str, Enum):
    """ビデオファイル種別"""

    TS = "ts"
    ENCODED = "encoded"


class VideoFile(BaseModel):
    """ビデオファイル値オブジェクト"""

    id: Annotated[int, Field(description="ビデオファイルID")]
    name: Annotated[str, Field(min_length=1, description="表示名")]
    filename: Annotated[str, Field(description="ファイル名")]
    type: Annotated[VideoFileType, Field(description="ファイル種別")]
    size: Annotated[int, Field(ge=1, description="ファイルサイズ（バイト）")]

    @property
    def formatted_size(self) -> str:
        """ファイルサイズを適切な単位で表示"""
        if self.size < 1024:
            return f"{self.size}B"
        if self.size < 1024**2:
            return f"{self.size / 1024:.1f}KB"
        if self.size < 1024**3:
            return f"{self.size / (1024**2):.1f}MB"
        return f"{self.size / (1024**3):.2f}GB"


class RecordingData(BaseModel):
    """録画データエンティティ"""

    id: int = Field(description="録画ID")
    name: str = Field(min_length=1, description="番組タイトル")
    start_at: int = Field(description="開始時刻（Unix timestamp ms）")
    end_at: int = Field(description="終了時刻（Unix timestamp ms）")
    video_files: list[VideoFile] = Field(description="ビデオファイル一覧")
    is_recording: bool = Field(description="録画中かどうか")
    is_protected: bool = Field(description="自動削除対象外か")

    def model_post_init(self, _: dict[str, object]) -> None:
        """Post-init validation"""
        if self.end_at <= self.start_at:
            raise ValueError("end_at must be greater than start_at")

    @property
    def formatted_start_time(self) -> str:
        """開始時刻の表示用フォーマット"""
        from datetime import datetime

        return datetime.fromtimestamp(self.start_at / 1000).strftime("%Y-%m-%d %H:%M")

    @property
    def duration_minutes(self) -> int:
        """録画時間（分）"""
        return (self.end_at - self.start_at) // (1000 * 60)


# Repository インターフェース定義
class EPGStationSessionProvider(Protocol):
    """EPGStation 認証セッション提供者"""

    def get_cookies(self) -> dict[str, str]:
        """認証済み Cookie を取得

        Returns:
            認証済み Cookie 辞書

        Raises:
            AuthenticationError: 認証に失敗した場合
        """
        ...


class RecordingRepository(Protocol):
    """録画データリポジトリ"""

    def get_all(self, limit: int = 1000, offset: int = 0) -> list[RecordingData]:
        """全録画データを取得

        Args:
            limit: 取得最大件数
            offset: 取得開始位置

        Returns:
            録画データリスト

        Raises:
            APIError: API アクセスに失敗した場合
        """
        ...


class TitleFilterService:
    """番組タイトルフィルタリングサービス"""

    def apply_filter(
        self,
        recordings: list[RecordingData],
        title_filter: str | None = None,
        regex: bool = False,
    ) -> list[RecordingData]:
        """録画データをタイトルでフィルタリング

        Args:
            recordings: フィルタリング対象の録画データ
            title_filter: フィルター条件（None の場合はフィルタリングしない）
            regex: 正規表現モードフラグ

        Returns:
            フィルタリング後の録画データリスト

        Raises:
            ValueError: 無効な正規表現パターンが指定された場合
        """
        if not title_filter:
            return recordings

        if regex:
            pattern = self._compile_regex_safely(title_filter)
            return [r for r in recordings if pattern.search(r.name)]
        title_lower = title_filter.lower()
        return [r for r in recordings if title_lower in r.name.lower()]

    def _compile_regex_safely(self, pattern: str) -> Pattern[str]:
        """安全な正規表現コンパイル"""
        import re

        try:
            # ReDoS対策: 危険なパターンの検出
            if self._is_dangerous_regex(pattern):
                raise RegexPatternError("危険な正規表現パターンです")

            return re.compile(pattern)
        except re.error as e:
            raise RegexPatternError(f"正規表現エラー: {e}") from e

    def _is_dangerous_regex(self, pattern: str) -> bool:
        """危険な正規表現パターンの検出"""
        import re

        dangerous_patterns = [
            r"\(.+\)\+",  # (any)+
            r"\(.+\)\*",  # (any)*
            r"\([a-zA-Z]+\)\+",  # (letters)+
            r"\([a-zA-Z]+\)\*",  # (letters)*
            r"\(\w\*\)\+",  # (\w*)+
            r"\(\w\+\)\*",  # (\w+)*
        ]

        try:
            return any(re.search(dp, pattern) for dp in dangerous_patterns)
        except re.error:
            # 危険パターンの検出中にエラーが起きた場合は安全側に倒して危険とみなす
            return False
