"""
Configuration module for managing application settings.

This module provides classes and methods to handle application configuration,
including reading environment variables and setting up logging.
"""

import logging
from dataclasses import dataclass, field
from os import getenv
from os.path import dirname, expanduser, join
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from injector import inject, singleton
from platformdirs import PlatformDirs
from yaml import safe_load

from moro.modules.fantia import FantiaConfig

logger = logging.getLogger(__name__)

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

    def load_all(self) -> None:
        """
        Load configuration from all sources.

        Loads configuration in the following priority order:
        1. Default values (already set in dataclass defaults)
        2. Configuration files
        3. Environment variables

        Raises:
            ValueError: If any configuration value is invalid.
        """
        self.load_config_files()
        self.load_env()
        self.validate_config()

    def load_config_files(self) -> None:
        """
        Load configuration from YAML configuration files.

        Searches for configuration files in the following order:
        1. ~/.config/moro/config.yml (XDG config directory)
        2. ~/.moro/config.yml (traditional config directory)
        3. ./moro.yml (project-local configuration)
        """
        config_paths = self.get_config_paths()

        for path in config_paths:
            if path.exists():
                try:
                    logger.info(f"Loading configuration from {path}")
                    config_data = self._load_yaml_file(path)
                    self.merge_config(config_data)
                except Exception as e:
                    logger.warning(f"Failed to load configuration file {path}: {e}")

    def get_config_paths(self) -> list[Path]:
        """
        Get list of configuration file paths in priority order.

        Returns:
            List[Path]: Configuration file paths in priority order.
        """
        return [
            Path(expanduser("~/.config/moro/config.yml")),
            Path(expanduser("~/.moro/config.yml")),
            Path("./moro.yml"),
        ]

    def _load_yaml_file(self, path: Path) -> dict[str, Any]:
        """
        Load YAML configuration file.

        Args:
            path: Path to the YAML file.

        Returns:
            Dict[str, Any]: Configuration data from the YAML file.
        """
        with open(path, encoding="utf-8") as f:
            return safe_load(f) or {}

    def merge_config(self, config_data: dict[str, Any]) -> None:
        """
        Merge configuration data into existing configuration.

        Args:
            config_data: Configuration data to merge.
        """
        if "app" in config_data:
            self._merge_app_config(config_data["app"])
        if "fantia" in config_data:
            self._merge_fantia_config(config_data["fantia"])

    def _merge_app_config(self, app_config: dict[str, Any]) -> None:
        """
        Merge app configuration data.

        Args:
            app_config: App configuration data to merge.
        """
        if "jobs" in app_config:
            self.app.jobs = int(app_config["jobs"])
        if "user_data_dir" in app_config:
            self.app.user_data_dir = str(app_config["user_data_dir"])
        if "working_dir" in app_config:
            self.app.working_dir = str(app_config["working_dir"])

    def _merge_fantia_config(self, fantia_config: dict[str, Any]) -> None:
        """
        Merge fantia configuration data.

        Args:
            fantia_config: Fantia configuration data to merge.
        """
        for key, value in fantia_config.items():
            if hasattr(self.fantia, key):
                # Type conversion for specific fields
                if key in ["max_retries", "concurrent_downloads"]:
                    value = int(value)
                elif key in ["timeout_connect", "timeout_read", "timeout_write", "timeout_pool"]:
                    value = float(value)
                elif key in ["download_thumb", "priorize_webp", "use_server_filenames"]:
                    value = bool(value) if isinstance(value, bool) else _parse_bool(str(value))
                elif key in ["session_id", "directory"]:
                    value = str(value) if value is not None else None

                setattr(self.fantia, key, value)
            else:
                logger.warning(f"Unknown fantia configuration key: {key}")

    def validate_config(self) -> None:
        """
        Validate all configuration values.

        Raises:
            ValueError: If any configuration value is invalid.
        """
        try:
            self.fantia.validate()
        except ValueError as e:
            raise ValueError(f"Invalid fantia configuration: {e}") from e

    def get_config_summary(self) -> dict[str, Any]:
        """
        Get a summary of current configuration.

        Returns:
            Dict[str, Any]: Configuration summary.
        """
        return {
            "app": {
                "jobs": self.app.jobs,
                "user_data_dir": self.app.user_data_dir,
                "working_dir": self.app.working_dir,
            },
            "fantia": {
                "session_id": "***" if self.fantia.session_id else None,
                "directory": self.fantia.directory,
                "download_thumb": self.fantia.download_thumb,
                "priorize_webp": self.fantia.priorize_webp,
                "use_server_filenames": self.fantia.use_server_filenames,
                "max_retries": self.fantia.max_retries,
                "timeout_connect": self.fantia.timeout_connect,
                "timeout_read": self.fantia.timeout_read,
                "timeout_write": self.fantia.timeout_write,
                "timeout_pool": self.fantia.timeout_pool,
                "concurrent_downloads": self.fantia.concurrent_downloads,
            },
        }

    def load_env(self) -> None:
        """
        Load environment variables into the configuration instances.

        This function loads environment variables from a .env file and updates the
        configuration instances with the loaded values. Environment variables
        have the highest priority and will override any configuration file values.
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
                f"{ENV_PREFIX}FANTIA_USE_SERVER_FILENAMES", str(self.fantia.use_server_filenames)
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
                f"{ENV_PREFIX}FANTIA_CONCURRENT_DOWNLOADS", str(self.fantia.concurrent_downloads)
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
