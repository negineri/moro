"""
Configuration module for managing application settings.

This module provides classes and methods to handle application configuration,
including reading environment variables and setting up logging.
"""

from dataclasses import dataclass, field
from os import getenv
from os.path import dirname, join
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from injector import inject, singleton
from platformdirs import PlatformDirs
from yaml import safe_load

from moro.modules.fantia import FantiaConfig

ENV_PREFIX = "MORO_"
pfd = PlatformDirs(appname="moro", appauthor="negineri")


@singleton
@dataclass
class AppConfig:
    """
    Global configuration class for the application.

    This class holds global settings that can be accessed throughout the application.
    """

    jobs = 16  # Number of jobs for processing
    logging_config: dict[str, Any] = field(default_factory=dict[str, Any])  # Logging configuration
    user_data_dir = pfd.user_data_dir  # User data directory
    working_dir = "."  # Working directory


@inject
@singleton
@dataclass
class ConfigRepository:
    """
    Configuration repository for the application.

    This class holds the application configuration and provides methods to load
    environment variables into the configuration.
    """

    app: AppConfig = field(default_factory=AppConfig)  # Global configuration instance
    fantia: FantiaConfig = field(default_factory=FantiaConfig)  # Fantia-specific configuration

    def load_env(self) -> None:
        """
        Load environment variables into the configuration instances.

        This function loads environment variables from a .env file and updates the
        configuration instances with the loaded values.
        """
        load_dotenv()

        # App設定
        self.app.jobs = int(getenv(f"{ENV_PREFIX}JOBS", self.app.jobs))
        self.app.logging_config = _load_logging_config()
        self.app.user_data_dir = getenv(f"{ENV_PREFIX}USER_DATA_DIR", self.app.user_data_dir)
        self.app.working_dir = getenv(f"{ENV_PREFIX}WORKING_DIR", self.app.working_dir)

        # Fantia設定
        self.fantia.session_id = getenv(f"{ENV_PREFIX}FANTIA_SESSION_ID", self.fantia.session_id)
        self.fantia.directory = getenv(f"{ENV_PREFIX}FANTIA_DIRECTORY", self.fantia.directory)
        self.fantia.download_thumb = _parse_bool(
            getenv(f"{ENV_PREFIX}FANTIA_DOWNLOAD_THUMB", str(self.fantia.download_thumb))
        )
        self.fantia.priorize_webp = _parse_bool(
            getenv(f"{ENV_PREFIX}FANTIA_PRIORIZE_WEBP", str(self.fantia.priorize_webp))
        )
        self.fantia.use_server_filenames = _parse_bool(
            getenv(
                f"{ENV_PREFIX}FANTIA_USE_SERVER_FILENAMES",
                str(self.fantia.use_server_filenames)
            )
        )

        # HTTP設定
        self.fantia.max_retries = int(
            getenv(f"{ENV_PREFIX}FANTIA_MAX_RETRIES", str(self.fantia.max_retries))
        )
        self.fantia.timeout_connect = float(
            getenv(f"{ENV_PREFIX}FANTIA_TIMEOUT_CONNECT", str(self.fantia.timeout_connect))
        )
        self.fantia.timeout_read = float(
            getenv(f"{ENV_PREFIX}FANTIA_TIMEOUT_READ", str(self.fantia.timeout_read))
        )
        self.fantia.timeout_write = float(
            getenv(f"{ENV_PREFIX}FANTIA_TIMEOUT_WRITE", str(self.fantia.timeout_write))
        )
        self.fantia.timeout_pool = float(
            getenv(f"{ENV_PREFIX}FANTIA_TIMEOUT_POOL", str(self.fantia.timeout_pool))
        )

        # 並列処理設定
        self.fantia.concurrent_downloads = int(
            getenv(
                f"{ENV_PREFIX}FANTIA_CONCURRENT_DOWNLOADS",
                str(self.fantia.concurrent_downloads)
            )
        )


def _parse_bool(value: str) -> bool:
    """Parse string to boolean."""
    return value.lower() in ("true", "1", "yes", "on")


def _load_logging_config() -> Any:
    """
    Load the logging configuration from the environment variable or default path.

    Returns:
        dict[str, Any]: Logging configuration dictionary.

    Raises:
        FileNotFoundError: If the logging configuration file does not exist.
    """
    logging_config_path = Path(
        getenv(f"{ENV_PREFIX}LOGGING_CONFIG_PATH", join(dirname(__file__), "logging.yml"))
    )
    if logging_config_path.exists():
        with open(logging_config_path) as f:
            return safe_load(f)
    else:
        raise FileNotFoundError(f"Logging configuration file not found: {logging_config_path}")
