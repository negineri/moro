"""Configuration for BigComics module."""

from pathlib import Path

from pydantic import BaseModel, Field


class BigComicsConfig(BaseModel):
    """BigComics module configuration."""

    output_dir: Path = Field(default=Path("output/bigcomics"))
    user_data_dir: Path = Field(default=Path("chromium_profile"))
    timeout_ms: int = Field(default=10000, description="Timeout in milliseconds")
    viewport_width: int = Field(default=400)
    viewport_height: int = Field(default=800)
    user_agent: str = Field(
        default=(
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
            " (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36"
        )
    )
