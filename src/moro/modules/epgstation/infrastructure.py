"""EPGStation インフラストラクチャ実装"""

import json
import os
import time
from pathlib import Path


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
    """Selenium ベースの EPGStation セッション認証 - 最小実装"""

    pass


class EPGStationRecordingRepository:
    """EPGStation 録画データリポジトリ実装 - 最小実装"""

    pass
