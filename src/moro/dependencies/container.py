"""Dependency injection container configuration."""

from typing import Callable, TypeVar

from injector import Binder, Injector, Module

_T = TypeVar("_T")


class RepositoryModule(Module):
    """Module for repository bindings."""


def create_injector() -> Injector:
    """
    Create and configure the dependency injection container.

    Returns:
        Injector: Configured injector instance.
    """
    return Injector([RepositoryModule])


def create_binder(cls: type[_T], ins: _T) -> Callable[[Binder], None]:
    """Create a binder function that binds a class to an instance."""

    def binder(binder: Binder) -> None:
        binder.bind(cls, to=ins)

    return binder
