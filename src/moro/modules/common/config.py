"""Configuration for the common module."""

import os
from pathlib import Path
from typing import Any

from platformdirs import PlatformDirs
from pydantic import BaseModel, Field, field_validator

from moro.env import APP_AUTHOR, APP_NAME

_pfd = PlatformDirs(appname=APP_NAME, appauthor=APP_AUTHOR)


class CommonConfig(BaseModel):
    """
    Common configuration class for the application.

    This class holds global settings that can be accessed throughout the application.
    """

    jobs: int = Field(default=16, ge=1)  # Number of jobs for processing
    logging_config: dict[str, Any] = Field(default_factory=dict)  # Logging configuration
    user_data_dir: str = Field(default=_pfd.user_data_dir)  # User data directory
    user_cache_dir: str = Field(default=_pfd.user_cache_dir)  # User cache directory
    working_dir: str = Field(default=".")  # Working directory
    playwright_user_data_dir: Path = Field(default=Path(_pfd.user_data_dir) / "chromium_profile")
    playwright_headless: bool = Field(default=True, description="Run Playwright in headless mode")
    user_agent: str = Field(
        default=(
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
            " (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36"
        )
    )
    timeout_ms: int = Field(default=10000, description="Timeout in milliseconds")
    httpx_magnitude: int = Field(default=3, description="HTTPX requests per second")
    retry_count: int = Field(default=3, description="Number of retries for failed requests")
    plugin_dirs: list[Path] = Field(
        default_factory=list,
        description="Additional directories to load user defined Playwright scripts from",
    )

    @field_validator("plugin_dirs", mode="before")
    @classmethod
    def _split_plugin_dirs(cls, value: Any) -> Any:
        """Allow plugin_dirs to be given as an os.pathsep separated string (env vars)."""
        if isinstance(value, str):
            return [part for part in value.split(os.pathsep) if part]
        return value
