"""Cookie キャッシュ機能のテスト

TDD Red Phase: Cookie キャッシュの読み書きテスト
"""

import os
import tempfile
from unittest.mock import patch

from moro.modules.epgstation.infrastructure import CookieCacheManager


def test_should_save_cookies_with_secure_permissions_when_caching() -> None:
    """Cookie ファイルが 600 権限で保存されることをテスト"""
    with tempfile.TemporaryDirectory() as temp_dir:
        cache_file = os.path.join(temp_dir, "test_cookies.json")
        cache_manager = CookieCacheManager(cache_file_path=cache_file, ttl_seconds=3600)

        test_cookies = {"session_id": "test_session_123", "auth_token": "abc123"}
        cache_manager.save_cookies(test_cookies)

        # ファイルの権限をチェック
        file_stat = os.stat(cache_file)
        file_mode = oct(file_stat.st_mode)[-3:]
        assert file_mode == "600"  # オーナーのみ読み書き可能


def test_should_return_cached_cookies_when_cache_valid() -> None:
    """有効なキャッシュがある場合の Cookie 読み込みをテスト"""
    with tempfile.TemporaryDirectory() as temp_dir:
        cache_file = os.path.join(temp_dir, "test_cookies.json")
        cache_manager = CookieCacheManager(cache_file_path=cache_file, ttl_seconds=3600)

        test_cookies = {"session_id": "test_session_123"}
        cache_manager.save_cookies(test_cookies)

        # 保存直後なので有効なはず
        loaded_cookies = cache_manager.load_cookies()
        assert loaded_cookies == test_cookies


def test_should_return_none_when_cache_file_corrupted() -> None:
    """破損したキャッシュファイルの処理をテスト"""
    with tempfile.TemporaryDirectory() as temp_dir:
        cache_file = os.path.join(temp_dir, "corrupted_cookies.json")

        # 破損したJSONファイルを作成
        with open(cache_file, "w") as f:
            f.write("invalid json content")

        cache_manager = CookieCacheManager(cache_file_path=cache_file, ttl_seconds=3600)
        loaded_cookies = cache_manager.load_cookies()

        assert loaded_cookies is None


def test_should_return_none_when_cache_expired() -> None:
    """期限切れキャッシュの処理をテスト"""
    with tempfile.TemporaryDirectory() as temp_dir:
        cache_file = os.path.join(temp_dir, "expired_cookies.json")
        cache_manager = CookieCacheManager(cache_file_path=cache_file, ttl_seconds=1)  # 1秒TTL

        test_cookies = {"session_id": "test_session_123"}
        cache_manager.save_cookies(test_cookies)

        # 時刻を進めて期限切れにする
        import time

        with patch("time.time", return_value=time.time() + 2):  # 2秒後
            loaded_cookies = cache_manager.load_cookies()
            assert loaded_cookies is None


def test_should_return_none_when_cache_file_not_exists() -> None:
    """キャッシュファイルが存在しない場合のテスト"""
    cache_file = "/nonexistent/path/cookies.json"
    cache_manager = CookieCacheManager(cache_file_path=cache_file, ttl_seconds=3600)

    loaded_cookies = cache_manager.load_cookies()
    assert loaded_cookies is None


def test_should_create_cache_directory_when_not_exists() -> None:
    """キャッシュディレクトリが存在しない場合の自動作成をテスト"""
    with tempfile.TemporaryDirectory() as temp_dir:
        cache_dir = os.path.join(temp_dir, "nested", "cache", "dir")
        cache_file = os.path.join(cache_dir, "cookies.json")
        cache_manager = CookieCacheManager(cache_file_path=cache_file, ttl_seconds=3600)

        test_cookies = {"session_id": "test_session_123"}
        cache_manager.save_cookies(test_cookies)

        # ディレクトリとファイルが作成されていることを確認
        assert os.path.exists(cache_dir)
        assert os.path.exists(cache_file)

        # 読み込みできることを確認
        loaded_cookies = cache_manager.load_cookies()
        assert loaded_cookies == test_cookies


def test_should_handle_empty_cookies_dict() -> None:
    """空の Cookie 辞書の処理をテスト"""
    with tempfile.TemporaryDirectory() as temp_dir:
        cache_file = os.path.join(temp_dir, "empty_cookies.json")
        cache_manager = CookieCacheManager(cache_file_path=cache_file, ttl_seconds=3600)

        empty_cookies: dict[str, str] = {}
        cache_manager.save_cookies(empty_cookies)

        loaded_cookies = cache_manager.load_cookies()
        assert loaded_cookies == empty_cookies
