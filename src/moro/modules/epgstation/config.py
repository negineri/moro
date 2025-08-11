"""EPGStation 設定管理"""

import re

from pydantic import BaseModel, Field, field_validator


class EPGStationConfig(BaseModel):
    """EPGStation設定"""

    # 基本設定
    base_url: str = Field(
        ..., description="EPGStation ベースURL（例: https://epgstation.example.com）"
    )

    # Selenium設定
    chrome_data_dir: str = Field(
        default="epgstation_chrome_userdata", description="Chrome ユーザーデータディレクトリ"
    )

    # Cookie キャッシュ設定
    enable_cookie_cache: bool = Field(default=True, description="Cookie キャッシュを有効にするか")
    cookie_cache_file: str = Field(
        default="epgstation_cookies.json", description="Cookie キャッシュファイル名"
    )
    cookie_cache_ttl: int = Field(default=3600, description="Cookie キャッシュ有効期限（秒）")

    # HTTP設定
    timeout: float = Field(default=30.0, ge=1.0, description="HTTP タイムアウト（秒）")
    max_retries: int = Field(default=3, ge=0, description="最大リトライ回数")

    # 表示設定
    max_recordings: int = Field(default=1000, ge=1, le=10000, description="最大表示録画数")

    @field_validator("base_url")
    @classmethod
    def validate_base_url(cls, v: str) -> str:
        """ベースURL の検証と正規化

        Args:
            v: 検証するURL文字列

        Returns:
            正規化されたURL（末尾スラッシュを除去）

        Raises:
            ValueError: URL形式が不正な場合
        """
        # URL形式の基本検証
        url_pattern = r"^https?://[^\s/$.?#].[^\s]*$"
        if not re.match(url_pattern, v):
            raise ValueError("有効なURL形式ではありません（例: https://example.com）")

        # 末尾スラッシュの除去
        return v.rstrip("/")
