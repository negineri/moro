"""Dependency injection container configuration."""

from injector import Injector, Module


class RepositoryModule(Module):
    """Module for repository bindings."""


def create_injector() -> Injector:
    """
    Create and configure the dependency injection container.

    Returns:
        Injector: Configured injector instance.
    """
    return Injector([RepositoryModule])
