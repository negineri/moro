"""
Configuration module for managing application settings.

This module provides classes and methods to handle application configuration,
including reading environment variables and setting up logging.
"""

import logging
from dataclasses import dataclass, field, fields
from os import getenv
from os.path import dirname, expanduser, join
from pathlib import Path
from typing import Any, Optional, Union, get_type_hints

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
            self._merge_config_generic(self.app, config_data["app"], "app")
        if "fantia" in config_data:
            self._merge_config_generic(self.fantia, config_data["fantia"], "fantia")

    def _merge_config_generic(
        self, config_obj: Any, config_data: dict[str, Any], config_name: str
    ) -> None:
        """
        Generic configuration merging using type hints for automatic type conversion.

        Args:
            config_obj: Configuration object to update.
            config_data: Configuration data to merge.
            config_name: Name of the configuration section for logging.
        """
        type_hints = get_type_hints(type(config_obj))

        for key, value in config_data.items():
            if hasattr(config_obj, key):
                field_type = type_hints.get(key)
                try:
                    converted_value = self._convert_value(value, field_type)
                    setattr(config_obj, key, converted_value)
                except (ValueError, TypeError) as e:
                    logger.warning(f"Failed to convert {config_name}.{key} = {value}: {e}")
            else:
                logger.warning(f"Unknown {config_name} configuration key: {key}")

    def _convert_value(self, value: Any, target_type: Optional[type]) -> Any:
        """
        Convert a value to the specified type using type hints.

        Args:
            value: Value to convert.
            target_type: Target type for conversion.

        Returns:
            Converted value.

        Raises:
            ValueError: If conversion fails.
            TypeError: If type is not supported.
        """
        if target_type is None or value is None:
            return value

        # Handle Optional[T] (Union[T, None]) for Python 3.9
        if hasattr(target_type, '__origin__'):
            origin = target_type.__origin__
            if origin is Union:
                # Optional[T] is represented as Union[T, None]
                args = target_type.__args__  # type: ignore
                if len(args) == 2 and type(None) in args:
                    if value is None:
                        return None
                    # Get the non-None type
                    actual_type = args[0] if args[1] is type(None) else args[1]
                    return self._convert_value(value, actual_type)

        # Basic type conversions
        if target_type is bool:
            if isinstance(value, bool):
                return value
            return _parse_bool(str(value))

        if target_type is int:
            return int(value)

        if target_type is float:
            return float(value)

        if target_type is str:
            return str(value) if value is not None else None

        # If no specific conversion is needed, return as-is
        return value

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
            "app": self._get_object_summary(self.app),
            "fantia": self._get_object_summary(self.fantia, mask_fields={"session_id"}),
        }

    def _get_object_summary(
        self, config_obj: Any, mask_fields: Optional[set[str]] = None
    ) -> dict[str, Any]:
        """
        Get a summary of a configuration object using reflection.

        Args:
            config_obj: Configuration object to summarize.
            mask_fields: Set of field names to mask with "***".

        Returns:
            Dict[str, Any]: Object summary.
        """
        if mask_fields is None:
            mask_fields = set()

        summary = {}
        # Get all dataclass fields
        for field_obj in fields(config_obj):
            field_name = field_obj.name
            value = getattr(config_obj, field_name)
            # Mask sensitive fields
            if field_name in mask_fields and value is not None:
                summary[field_name] = "***"
            else:
                summary[field_name] = value

        return summary

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
