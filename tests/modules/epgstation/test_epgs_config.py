"""EPGStation 設定管理のテスト

TDD Red Phase: 設定値検証のテストを作成
"""

import pytest
from pydantic import ValidationError

from moro.modules.epgstation.config import EPGStationConfig


def test_should_validate_base_url_format_when_invalid_url_provided() -> None:
    """不正なURL形式でValidationErrorが発生することをテスト"""
    with pytest.raises(ValidationError):
        EPGStationConfig(base_url="invalid-url")

    with pytest.raises(ValidationError):
        EPGStationConfig(base_url="not-a-url")


def test_should_set_default_values_when_optional_fields_omitted() -> None:
    """デフォルト値が正しく設定されることをテスト"""
    config = EPGStationConfig(base_url="https://epgstation.example.com")

    assert config.chrome_data_dir == "epgstation_chrome_userdata"
    assert config.enable_cookie_cache is True
    assert config.cookie_cache_file == "epgstation_cookies.json"
    assert config.cookie_cache_ttl == 3600
    assert config.timeout == 30.0
    assert config.max_retries == 3
    assert config.max_recordings == 1000


def test_should_normalize_base_url_when_trailing_slash_provided() -> None:
    """末尾のスラッシュが正規化されることをテスト"""
    config = EPGStationConfig(base_url="https://epgstation.example.com/")
    assert config.base_url == "https://epgstation.example.com"


def test_should_accept_valid_base_url_when_proper_format_provided() -> None:
    """有効なURL形式が受け入れられることをテスト"""
    valid_urls = [
        "https://epgstation.example.com",
        "http://localhost:8888",
        "https://epg.domain.co.jp:8080",
    ]

    for url in valid_urls:
        config = EPGStationConfig(base_url=url)
        assert config.base_url == url


def test_should_validate_numeric_constraints_when_invalid_values_provided() -> None:
    """数値制約の検証をテスト"""
    with pytest.raises(ValidationError):
        EPGStationConfig(
            base_url="https://example.com",
            timeout=-1.0,  # 負の値
        )

    with pytest.raises(ValidationError):
        EPGStationConfig(
            base_url="https://example.com",
            max_retries=-1,  # 負の値
        )

    with pytest.raises(ValidationError):
        EPGStationConfig(
            base_url="https://example.com",
            max_recordings=0,  # 最小値未満
        )
