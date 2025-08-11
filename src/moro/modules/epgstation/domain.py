"""EPGStation ドメインモデル"""

from enum import Enum
from typing import Annotated, Protocol

from pydantic import BaseModel, Field


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
