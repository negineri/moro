"""Common utilities for the modules."""

from typing import Any

from platformdirs import PlatformDirs
from pydantic import BaseModel, Field

pfd = PlatformDirs(appname="moro", appauthor="negineri")


class CommonConfig(BaseModel):
    """
    Common configuration class for the application.

    This class holds global settings that can be accessed throughout the application.
    """

    jobs: int = Field(default=16, ge=1)  # Number of jobs for processing
    logging_config: dict[str, Any] = Field(default_factory=dict)  # Logging configuration
    user_data_dir: str = Field(default=pfd.user_data_dir)  # User data directory
    working_dir: str = Field(default=".")  # Working directory
