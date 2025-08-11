"""EPGStation 録画データ管理クライアント機能

EPGStation の録画データを管理するクライアント機能。
OAuth2-Proxy（Keycloak 認証）の背後にある EPGStation に対して、
Selenium を使用した認証と Cookie キャッシュによる効率的なアクセスを提供する。

主な機能:
- Keycloak + OAuth2-Proxy 認証対応
- 録画データ一覧取得
- Cookie キャッシュによる認証効率化
- CLI インターフェース (moro epgstation list)
"""

# 公開インターフェース（順次実装予定）
from .config import EPGStationConfig
from .domain import RecordingData, VideoFile
from .infrastructure import EPGStationRecordingRepository, SeleniumEPGStationSessionProvider
from .usecases import ListRecordingsUseCase

__all__ = [
    "EPGStationConfig",
    "EPGStationRecordingRepository",
    "ListRecordingsUseCase",
    "RecordingData",
    "SeleniumEPGStationSessionProvider",
    "VideoFile",
]
