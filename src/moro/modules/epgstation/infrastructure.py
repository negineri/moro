"""EPGStation インフラストラクチャ実装"""

import json
import logging
import os
import time
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from selenium.webdriver.chrome.options import Options

    from moro.modules.common import CommonConfig
    from moro.modules.epgstation.config import EPGStationConfig
    from moro.modules.epgstation.domain import EPGStationSessionProvider, RecordingData

logger = logging.getLogger(__name__)


class CookieCacheManager:
    """Cookie キャッシュ管理クラス"""

    def __init__(self, cache_file_path: str, ttl_seconds: int) -> None:
        """初期化

        Args:
            cache_file_path: キャッシュファイルのパス
            ttl_seconds: キャッシュの有効期限（秒）
        """
        self.cache_file_path = cache_file_path
        self.ttl_seconds = ttl_seconds

    def save_cookies(self, cookies: dict[str, str]) -> None:
        """Cookie を安全な権限でキャッシュファイルに保存

        Args:
            cookies: 保存する Cookie 辞書
        """
        # キャッシュディレクトリが存在しない場合は作成
        cache_dir = Path(self.cache_file_path).parent
        cache_dir.mkdir(parents=True, exist_ok=True)

        # タイムスタンプ付きでデータを保存
        cache_data = {"timestamp": time.time(), "cookies": cookies}

        # 一時ファイルに書き込んでから移動（アトミック操作）
        temp_file = self.cache_file_path + ".tmp"
        with open(temp_file, "w") as f:
            json.dump(cache_data, f)

        # ファイル権限を600に設定（オーナーのみ読み書き）
        os.chmod(temp_file, 0o600)

        # 一時ファイルを本来のファイルに移動
        os.rename(temp_file, self.cache_file_path)

    def load_cookies(self) -> dict[str, str] | None:
        """キャッシュから Cookie を読み込み

        Returns:
            有効な Cookie 辞書、または None（無効・存在しない場合）
        """
        try:
            if not os.path.exists(self.cache_file_path):
                return None

            with open(self.cache_file_path) as f:
                cache_data = json.load(f)

            # キャッシュの有効期限をチェック
            cached_time = cache_data.get("timestamp", 0)
            current_time = time.time()

            if current_time - cached_time > self.ttl_seconds:
                # 期限切れ
                return None

            cookies = cache_data.get("cookies")
            return cookies if isinstance(cookies, dict) else None

        except (json.JSONDecodeError, KeyError, OSError):
            # ファイルが破損している、または読み取りエラー
            return None


class SeleniumEPGStationSessionProvider:
    """Selenium ベースの EPGStation セッション認証"""

    def __init__(
        self,
        common_config: "CommonConfig",
        epgstation_config: "EPGStationConfig",
    ) -> None:
        """初期化

        Args:
            common_config: 共通設定
            epgstation_config: EPGStation 設定
        """
        self._common_config = common_config
        self._epgstation_config = epgstation_config
        self._chrome_user_data = (
            Path(common_config.user_cache_dir) / epgstation_config.chrome_data_dir
        )

        # Cookie キャッシュマネージャーを初期化
        cookie_cache_file = Path(common_config.user_cache_dir) / epgstation_config.cookie_cache_file
        self._cookie_cache = CookieCacheManager(
            cache_file_path=str(cookie_cache_file),
            ttl_seconds=epgstation_config.cookie_cache_ttl,
        )

    def get_cookies(self) -> dict[str, str]:
        """認証済み Cookie を取得（キャッシュ機能付き）

        Returns:
            認証済み Cookie 辞書

        Raises:
            RuntimeError: 認証に失敗した場合
        """
        if not self._epgstation_config.enable_cookie_cache:
            logger.info("Cookie cache disabled, performing fresh authentication")
            return self._perform_selenium_login()

        # キャッシュから読み込み
        cached_cookies = self._cookie_cache.load_cookies()
        if cached_cookies and self._is_session_valid(cached_cookies):
            logger.info("Using cached EPGStation cookies")
            return cached_cookies

        # 新規認証実行
        logger.info("Performing fresh EPGStation authentication")
        fresh_cookies = self._perform_selenium_login()

        # キャッシュに保存
        if fresh_cookies:
            self._cookie_cache.save_cookies(fresh_cookies)
            logger.info("Saved fresh cookies to cache")

        return fresh_cookies

    def _perform_selenium_login(self) -> dict[str, str]:
        """Selenium による認証実行

        Returns:
            認証済み Cookie 辞書

        Raises:
            RuntimeError: 認証に失敗した場合
        """
        from selenium import webdriver

        options = self._create_chrome_options()

        try:
            with webdriver.Chrome(options=options) as driver:
                # EPGStation トップページにアクセス
                logger.info(f"Navigating to EPGStation: {self._epgstation_config.base_url}")
                driver.get(self._epgstation_config.base_url)

                # 認証完了を待機（ユーザー操作）
                input("ブラウザで認証を完了してください。完了したら Enter キーを押してください...")

                # 認証完了後の Cookie を取得
                cookies = driver.get_cookies()
                result = {cookie["name"]: cookie["value"] for cookie in cookies}

                logger.info(f"Obtained {len(result)} cookies from browser")
                return result

        except Exception as e:
            logger.error(f"Selenium authentication failed: {e}")
            raise RuntimeError(f"認証に失敗しました: {e}") from e

    def _create_chrome_options(self) -> "Options":
        """Chrome WebDriver オプションを作成"""
        from selenium.webdriver.chrome.options import Options

        options = Options()
        options.add_argument(f"--user-data-dir={self._chrome_user_data}")
        options.add_argument("--no-first-run")
        options.add_argument("--disable-extensions")

        # CI環境での設定
        if os.getenv("CI") == "true":
            options.add_argument("--headless")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")

        return options

    def _is_session_valid(self, cookies: dict[str, str]) -> bool:
        """セッションが有効かチェック

        Args:
            cookies: チェックする Cookie 辞書

        Returns:
            セッションが有効な場合 True
        """
        # 簡単な validation - より複雑なチェックが必要な場合は後で実装
        required_cookies = ["session", "_oauth2_proxy"]
        return any(cookie_name in cookies for cookie_name in required_cookies)


class EPGStationRecordingRepository:
    """EPGStation 録画データリポジトリ実装"""

    def __init__(
        self,
        session_provider: "EPGStationSessionProvider",
        epgstation_config: "EPGStationConfig",
    ) -> None:
        """初期化

        Args:
            session_provider: セッションプロバイダー
            epgstation_config: EPGStation 設定
        """
        self._session_provider = session_provider
        self._config = epgstation_config

    def get_all(self, limit: int = 1000, offset: int = 0) -> list["RecordingData"]:
        """録画データ一覧を取得

        Args:
            limit: 取得最大件数
            offset: 取得開始位置

        Returns:
            録画データリスト

        Raises:
            RuntimeError: API アクセスに失敗した場合
        """
        import httpx

        from moro.modules.epgstation.domain import RecordingData, VideoFile, VideoFileType

        cookies = self._session_provider.get_cookies()

        params = {
            "limit": min(limit, self._config.max_recordings),
            "offset": offset,
            "isHalfWidth": True,  # 半角文字で取得
        }

        try:
            with httpx.Client(
                base_url=self._config.base_url,
                timeout=self._config.timeout,
            ) as client:
                response = client.get(
                    "/api/recorded",
                    cookies=cookies,
                    params=params,
                )
                response.raise_for_status()

                data = response.json()
                recordings = []

                for item in data.get("records", []):
                    video_files = []

                    for vf in item.get("videoFiles", []):
                        try:
                            video_file = VideoFile(
                                id=vf["id"],
                                name=vf.get("name", ""),
                                filename=vf.get("filename", ""),
                                type=VideoFileType(vf.get("type", "ts")),
                                size=vf.get("size", 1),  # 0 bytes は無効なので 1 をデフォルト
                            )
                            video_files.append(video_file)
                        except Exception as e:
                            logger.warning(f"Failed to parse video file {vf}: {e}")
                            continue

                    recording = RecordingData(
                        id=item["id"],
                        name=item.get("name", "不明な番組"),
                        start_at=item.get("startAt", 0),
                        end_at=item.get("endAt", 1),  # start_at より大きくする必要がある
                        video_files=video_files,
                        is_recording=item.get("isRecording", False),
                        is_protected=item.get("isProtected", False),
                    )
                    recordings.append(recording)

                logger.info(f"Retrieved {len(recordings)} recordings from EPGStation")
                return recordings

        except httpx.HTTPError as e:
            logger.error(f"HTTP error accessing EPGStation API: {e}")
            raise RuntimeError(f"EPGStation API アクセスエラー: {e}") from e
        except Exception as e:
            logger.error(f"Failed to get recordings: {e}")
            raise RuntimeError(f"録画データの取得に失敗しました: {e}") from e
