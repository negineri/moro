"""
Configuration module for managing application settings.

This module provides classes and methods to handle application configuration,
including reading environment variables and setting up logging.
"""

import logging
from os import getenv
from os.path import dirname, expanduser, join
from pathlib import Path
from typing import Any, Optional

import tomli
from dotenv import load_dotenv
from injector import inject, singleton
from platformdirs import PlatformDirs
from pydantic import BaseModel, Field, ValidationError
from yaml import safe_load

from moro.modules.fantia import FantiaConfig

logger = logging.getLogger(__name__)

ENV_PREFIX = "MORO_"
pfd = PlatformDirs(appname="moro", appauthor="negineri")
CONFIG_PATHS = [
    "./settings.toml",
    "/etc/moro/settings.toml",
    expanduser("~/.config/moro/settings.toml"),
]


def create_app_config(
    options: Optional[dict[str, Any]] = None, paths: list[str] = CONFIG_PATHS
) -> "AppConfig":
    """Factory method to create an instance of AppConfig with default values."""
    if options is None:
        options = {}

    etc_options = load_config_files(paths=paths)
    env_options = load_env_vars()
    etc_options.update(env_options)
    etc_options.update(options)

    return AppConfig(**etc_options.get("settings", {}))


def load_config_files(paths: list[str]) -> dict[str, Any]:
    """
    Load configuration from YAML files in the user's config directories.

    Returns:
        dict[str, Any]: Merged configuration data from all found files.
    """
    config_paths = [Path(path) for path in paths]

    config_data: dict[str, Any] = {}
    for path in config_paths:
        if path.exists():
            try:
                with open(path, "rb") as f:
                    data: dict[str, Any] = tomli.load(f) or {}
                    config_data.update(data)
            except Exception as e:
                logger.warning(f"Failed to load configuration file {path}: {e}")

    return config_data


def load_env_vars() -> dict[str, Any]:
    """
    Load environment variables with MORO_SETTINGS_ prefix.

    Supports both flat and nested configuration with arbitrary depth:
    - MORO_SETTINGS_JOBS=16 -> settings.jobs
    - MORO_SETTINGS_FANTIA__DOWNLOAD_THUMB=true -> settings.fantia.download_thumb
    - MORO_SETTINGS_TEMP__HOGEHOGE__EXAMPLE=false -> settings.temp.hogehoge.example

    Returns:
        dict[str, Any]: Configuration data from environment variables.
    """
    import os

    settings_prefix = f"{ENV_PREFIX}SETTINGS_"
    config_data: dict[str, Any] = {}

    def _ensure_settings_section() -> dict[str, Any]:
        """Ensure settings section exists in config_data."""
        if "settings" not in config_data:
            config_data["settings"] = {}
        return config_data["settings"]  # type: ignore[no-any-return]

    for key, value in os.environ.items():
        if not key.startswith(settings_prefix):
            continue

        # Remove the prefix and convert to lowercase
        setting_key = key[len(settings_prefix) :].lower()

        # Handle nested fields (e.g., FANTIA__DOWNLOAD_THUMB -> fantia.download_thumb)
        if "__" in setting_key:
            parts = setting_key.split("__")
            settings = _ensure_settings_section()

            # Navigate/create nested structure
            current_dict = settings
            for part in parts[:-1]:  # All parts except the last one
                if part not in current_dict:
                    current_dict[part] = {}
                current_dict = current_dict[part]

            # Set the final value
            current_dict[parts[-1]] = value
        else:
            # Handle top-level fields
            settings = _ensure_settings_section()
            settings[setting_key] = value

    return config_data


class AppConfig(BaseModel):
    """
    Global configuration class for the application.

    This class holds global settings that can be accessed throughout the application.
    """

    jobs: int = Field(default=16, ge=1)  # Number of jobs for processing
    logging_config: dict[str, Any] = Field(default_factory=dict)  # Logging configuration
    user_data_dir: str = Field(default=pfd.user_data_dir)  # User data directory
    working_dir: str = Field(default=".")  # Working directory

    fantia: FantiaConfig = Field(default_factory=FantiaConfig)  # Fantia-specific configuration


@inject
@singleton
class ConfigRepository(BaseModel):
    """
    Configuration repository for the application.

    This class holds the application configuration and provides methods to load
    environment variables into the configuration.
    """

    app: AppConfig = Field(default_factory=AppConfig)  # Global configuration instance
    fantia: FantiaConfig = Field(default_factory=FantiaConfig)  # Fantia-specific configuration

    model_config = {"extra": "forbid"}

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
        Merge configuration data into existing configuration using Pydantic.

        Args:
            config_data: Configuration data to merge.
        """
        try:
            if "app" in config_data:
                # Merge with existing app config
                current_app_data = self.app.model_dump()
                current_app_data.update(config_data["app"])
                self.app = AppConfig.model_validate(current_app_data)

            if "fantia" in config_data:
                # Merge with existing fantia config
                current_fantia_data = self.fantia.model_dump()
                current_fantia_data.update(config_data["fantia"])
                self.fantia = FantiaConfig.model_validate(current_fantia_data)
        except ValidationError as e:
            logger.error(f"Configuration validation failed: {e}")
            raise ValueError(f"Invalid configuration: {e}") from e

    def validate_config(self) -> None:
        """
        Validate all configuration values using Pydantic.

        Raises:
            ValueError: If any configuration value is invalid.
        """
        try:
            # Pydantic models are automatically validated on creation/update
            # Re-validate to ensure current state is valid
            AppConfig.model_validate(self.app.model_dump())
            FantiaConfig.model_validate(self.fantia.model_dump())
        except ValidationError as e:
            raise ValueError(f"Invalid configuration: {e}") from e

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
        self, config_obj: BaseModel, mask_fields: Optional[set[str]] = None
    ) -> dict[str, Any]:
        """
        Get a summary of a Pydantic configuration object.

        Args:
            config_obj: Pydantic configuration object to summarize.
            mask_fields: Set of field names to mask with "***".

        Returns:
            dict[str, Any]: Object summary.
        """
        if mask_fields is None:
            mask_fields = set()

        summary = config_obj.model_dump()

        # Mask sensitive fields
        for field_name in mask_fields:
            if field_name in summary and summary[field_name] is not None:
                summary[field_name] = "***"

        return summary

    def load_env(self) -> None:
        """
        Load environment variables into the configuration instances.

        This function loads environment variables from a .env file and updates the
        configuration instances with the loaded values. Environment variables
        have the highest priority and will override any configuration file values.
        """
        load_dotenv()

        # Build environment override data
        env_data: dict[str, Any] = {}

        # App設定
        app_env_data: dict[str, Any] = {}
        if jobs_env := getenv(f"{ENV_PREFIX}JOBS"):
            app_env_data["jobs"] = int(jobs_env)
        if user_data_dir_env := getenv(f"{ENV_PREFIX}USER_DATA_DIR"):
            app_env_data["user_data_dir"] = user_data_dir_env
        if working_dir_env := getenv(f"{ENV_PREFIX}WORKING_DIR"):
            app_env_data["working_dir"] = working_dir_env

        # Always load logging config
        app_env_data["logging_config"] = _load_logging_config()

        if app_env_data:
            env_data["app"] = app_env_data

        # Fantia設定
        fantia_env_data: dict[str, Any] = {}
        if session_id_env := getenv(f"{ENV_PREFIX}FANTIA_SESSION_ID"):
            fantia_env_data["session_id"] = session_id_env
        if directory_env := getenv(f"{ENV_PREFIX}FANTIA_DIRECTORY"):
            fantia_env_data["directory"] = directory_env
        if download_thumb_env := getenv(f"{ENV_PREFIX}FANTIA_DOWNLOAD_THUMB"):
            fantia_env_data["download_thumb"] = _parse_bool(download_thumb_env)
        if priorize_webp_env := getenv(f"{ENV_PREFIX}FANTIA_PRIORIZE_WEBP"):
            fantia_env_data["priorize_webp"] = _parse_bool(priorize_webp_env)
        if use_server_filenames_env := getenv(f"{ENV_PREFIX}FANTIA_USE_SERVER_FILENAMES"):
            fantia_env_data["use_server_filenames"] = _parse_bool(use_server_filenames_env)
        if max_retries_env := getenv(f"{ENV_PREFIX}FANTIA_MAX_RETRIES"):
            fantia_env_data["max_retries"] = int(max_retries_env)
        if timeout_connect_env := getenv(f"{ENV_PREFIX}FANTIA_TIMEOUT_CONNECT"):
            fantia_env_data["timeout_connect"] = float(timeout_connect_env)
        if timeout_read_env := getenv(f"{ENV_PREFIX}FANTIA_TIMEOUT_READ"):
            fantia_env_data["timeout_read"] = float(timeout_read_env)
        if timeout_write_env := getenv(f"{ENV_PREFIX}FANTIA_TIMEOUT_WRITE"):
            fantia_env_data["timeout_write"] = float(timeout_write_env)
        if timeout_pool_env := getenv(f"{ENV_PREFIX}FANTIA_TIMEOUT_POOL"):
            fantia_env_data["timeout_pool"] = float(timeout_pool_env)
        if concurrent_downloads_env := getenv(f"{ENV_PREFIX}FANTIA_CONCURRENT_DOWNLOADS"):
            fantia_env_data["concurrent_downloads"] = int(concurrent_downloads_env)

        if fantia_env_data:
            env_data["fantia"] = fantia_env_data

        # Apply environment overrides using merge_config
        if env_data:
            self.merge_config(env_data)


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
