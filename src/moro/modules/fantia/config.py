"""Configuration for the Fantia client."""

import logging
import re
from typing import Optional

from pydantic import BaseModel, Field, field_validator

logger = logging.getLogger(__name__)

FANTIA_URL_RE = re.compile(r"(?:https?://(?:(?:www\.)?(?:fantia\.jp/(fanclubs|posts)/)))([0-9]+)")
EXTERNAL_LINKS_RE = re.compile(
    r"(?:[\s]+)?((?:(?:https?://)?(?:(?:www\.)?(?:mega\.nz|mediafire\.com|(?:drive|docs)\.google\.com|youtube.com|dropbox.com)\/))[^\s]+)"
)

DOMAIN = "fantia.jp"
BASE_URL = "https://fantia.jp/"

LOGIN_SIGNIN_URL = "https://fantia.jp/sessions/signin"
LOGIN_SESSION_URL = "https://fantia.jp/sessions"

ME_API = "https://fantia.jp/api/v1/me"

FANCLUB_API = "https://fantia.jp/api/v1/fanclubs/{}"
FANCLUBS_FOLLOWING_API = "https://fantia.jp/api/v1/me/fanclubs"
FANCLUBS_PAID_HTML = "https://fantia.jp/mypage/users/plans?type=not_free&page={}"
FANCLUB_POSTS_HTML = "https://fantia.jp/fanclubs/{}/posts?page={}"

POST_API = "https://fantia.jp/api/v1/posts/{}"
POST_URL = "https://fantia.jp/posts/{}"
POSTS_URL = "https://fantia.jp/posts"
POST_RELATIVE_URL = "/posts/"

TIMELINES_API = "https://fantia.jp/api/v1/me/timelines/posts?page={}&per=24"

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/137.0.0.0 Safari/537.36"
)

CRAWLJOB_FILENAME = "external_links.crawljob"

MIMETYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/gif": ".gif",
    "video/mp4": ".mp4",
    "video/webm": ".webm",
}

UNICODE_CONTROL_MAP = dict.fromkeys(range(32))


class FantiaConfig(BaseModel):
    """Configuration for the Fantia client."""

    # 認証設定
    session_id: Optional[str] = Field(default=None, min_length=1)

    # selenium設定
    chrome_data_dir: str = Field(
        default="chrome_userdata", description="Directory for Selenium user data"
    )

    # ダウンロード設定
    directory: str = Field(default="downloads/fantia")
    download_thumb: bool = Field(default=False)
    priorize_webp: bool = Field(default=False)
    use_server_filenames: bool = Field(default=False)

    # HTTP設定
    max_retries: int = Field(default=5, ge=0)
    timeout_connect: float = Field(default=10.0, ge=0)
    timeout_read: float = Field(default=30.0, ge=0)
    timeout_write: float = Field(default=10.0, ge=0)
    timeout_pool: float = Field(default=5.0, ge=0)

    # 並列処理設定
    concurrent_downloads: int = Field(default=3, ge=1)

    # クッキーキャッシュ設定
    enable_cookie_cache: bool = Field(default=True, description="Enable cookie caching")
    cookie_cache_file: str = Field(
        default="fantia_cookies.json", description="Cookie cache file path"
    )

    @field_validator("session_id")
    @classmethod
    def validate_session_id(cls, v: Optional[str]) -> Optional[str]:
        """Validate session_id is not empty string."""
        if v is not None and not v.strip():
            raise ValueError("session_id cannot be empty string")
        return v
