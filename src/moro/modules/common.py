"""Common utilities for the modules."""

from typing import Any

from platformdirs import PlatformDirs
from pydantic import BaseModel, Field

pfd = PlatformDirs(appname="moro", appauthor="negineri")


def generate_number_prefix(total_count: int, current_index: int) -> str:
    """
    Generates a zero-padded sequential prefix based on the total number of URLs.

    Args:
        total_count (int): The total number of URLs.
        current_index (int): The current index being processed (starting from 1).

    Returns:
        str: Zero-padded sequential prefix (e.g., "01_", "001_").

    Raises:
        ValueError: If total_count is less than or equal to 0, or if current_index is less than 1
            or greater than total_count.
    """
    if total_count <= 0:
        raise ValueError("total_count must be greater than 0")

    if current_index <= 0 or current_index > total_count:
        raise ValueError(
            "current_index must be greater than or equal to 1 and less than or equal to total_count"
        )

    # 必要な桁数を計算
    width = len(str(total_count))

    # ゼロ埋めされたプレフィックスを生成
    return f"{current_index:0{width}d}_"


class CommonConfig(BaseModel):
    """
    Common configuration class for the application.

    This class holds global settings that can be accessed throughout the application.
    """

    jobs: int = Field(default=16, ge=1)  # Number of jobs for processing
    logging_config: dict[str, Any] = Field(default_factory=dict)  # Logging configuration
    user_data_dir: str = Field(default=pfd.user_data_dir)  # User data directory
    user_cache_dir: str = Field(default=pfd.user_cache_dir)  # User cache directory
    working_dir: str = Field(default=".")  # Working directory
