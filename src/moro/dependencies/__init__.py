"""Dependency injection configuration."""

from injector import Injector

from moro.config.settings import ConfigRepository

from .container import create_injector


def get_injector() -> Injector:
    """Get configured injector instance.

    Returns:
        Configured injector instance.
    """
    config = ConfigRepository.create()
    return create_injector(config)
