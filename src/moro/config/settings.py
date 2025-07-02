"""
Configuration module for managing application settings.

This module provides classes and methods to handle application configuration,
including reading environment variables and setting up logging.
"""

from os import getenv
from os.path import dirname, join
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from injector import singleton
from yaml import safe_load

ENV_PREFIX = "MORO_"

# Domain Object


@singleton
class AppConfig:
    """
    Configuration class for the application.

    Attributes:
        jobs (int): Number of jobs for processing.
        logging_config_path (str): Path to the logging configuration file.
    """

    def __init__(self) -> None:
        """
        Initialize the AppConfig instance.

        This constructor loads environment variables and sets up the configuration
        attributes.
        """
        load_dotenv()

        self.jobs = int(getenv(f"{ENV_PREFIX}JOBS", "16"))  # Number of jobs for processing
        self.logging_config: dict[str, Any] = _load_logging_config()  # Logging configuration

    def __str__(self) -> str:
        """
        String representation of the AppConfig instance.

        Returns:
            str: String representation of the configuration.
        """
        return vars(self).__str__()


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
