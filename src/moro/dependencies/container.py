"""Dependency injection container configuration."""

from collections.abc import Callable
from typing import TypeVar

from injector import Binder, Injector, singleton

from moro.config.settings import ConfigRepository
from moro.modules.fantia.domain import (
    FantiaFanclubRepository,
    FantiaPostRepository,
    SessionIdProvider,
)
from moro.modules.fantia.infrastructure import (
    FantiaFanclubRepositoryImpl,
    FantiaPostRepositoryImpl,
    SeleniumSessionIdProvider,
)
from moro.modules.todo.domain import TodoRepository
from moro.modules.todo.infrastructure import InMemoryTodoRepository

_T = TypeVar("_T")


def configure(binder: Binder) -> None:
    """Configure the dependency injection container."""
    # EPGStation module bindings
    from moro.modules.epgstation.domain import EPGStationSessionProvider, RecordingRepository
    from moro.modules.epgstation.infrastructure import (
        EPGStationRecordingRepository,
        SeleniumEPGStationSessionProvider,
    )

    binder.bind(EPGStationSessionProvider, to=SeleniumEPGStationSessionProvider)  # type: ignore[type-abstract]
    binder.bind(RecordingRepository, to=EPGStationRecordingRepository)  # type: ignore[type-abstract]

    # Fantia module bindings
    binder.bind(SessionIdProvider, to=SeleniumSessionIdProvider)  # type: ignore[type-abstract]
    binder.bind(FantiaPostRepository, to=FantiaPostRepositoryImpl)  # type: ignore[type-abstract]
    binder.bind(FantiaFanclubRepository, to=FantiaFanclubRepositoryImpl)  # type: ignore[type-abstract]

    # Todo module bindings
    binder.bind(TodoRepository, to=InMemoryTodoRepository, scope=singleton)  # type: ignore[type-abstract]


def create_injector(config: ConfigRepository) -> Injector:
    """
    Create and configure the dependency injection container.

    Returns:
        Injector: Configured injector instance.
    """
    return Injector([config.create_injector_builder(), configure])


def create_binder(cls: type[_T], ins: _T) -> Callable[[Binder], None]:
    """Create a binder function that binds a class to an instance."""

    def binder(binder: Binder) -> None:
        binder.bind(cls, to=ins)

    return binder
