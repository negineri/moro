"""Dependency injection container configuration."""

from collections.abc import Awaitable, Callable, Coroutine
from logging import getLogger
from typing import Any, Concatenate, ParamSpec, TypeVar

from aiohttp import ClientSession
from injector import Binder, Injector, singleton

from moro.config.settings import ConfigRepository
from moro.modules.epgstation.domain import EPGStationSessionProvider, RecordingRepository
from moro.modules.epgstation.infrastructure import (
    EPGStationRecordingRepository,
    SeleniumEPGStationSessionProvider,
)
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
Param = ParamSpec("Param")
RetType = TypeVar("RetType")

_logger = getLogger(__name__)


def configure(binder: Binder) -> None:
    """Configure the dependency injection container."""
    # EPGStation module bindings
    binder.bind(EPGStationSessionProvider, to=SeleniumEPGStationSessionProvider)  # type: ignore[type-abstract]
    binder.bind(RecordingRepository, to=EPGStationRecordingRepository)  # type: ignore[type-abstract]

    # Fantia module bindings
    binder.bind(SessionIdProvider, to=SeleniumSessionIdProvider)  # type: ignore[type-abstract]
    binder.bind(FantiaPostRepository, to=FantiaPostRepositoryImpl)  # type: ignore[type-abstract]
    binder.bind(FantiaFanclubRepository, to=FantiaFanclubRepositoryImpl)  # type: ignore[type-abstract]

    # Todo module bindings
    binder.bind(TodoRepository, to=InMemoryTodoRepository, scope=singleton)  # type: ignore[type-abstract]

    binder.bind(ClientSession, to=ClientSession(), scope=singleton)


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


def async_injector(
    config: ConfigRepository,
) -> Callable[
    [Callable[Concatenate[Injector, Param], Awaitable[RetType]]],
    Callable[Param, Coroutine[Any, Any, RetType]],
]:
    """Create a binder function that binds a class to an instance for async usage."""

    def decorator(
        func: Callable[Concatenate[Injector, Param], Awaitable[RetType]],
    ) -> Callable[Param, Coroutine[Any, Any, RetType]]:
        async def wrapper(*args: Param.args, **kwargs: Param.kwargs) -> RetType:
            injector = create_injector(config)

            result = await func(injector, *args, **kwargs)

            _logger.debug("Closing aiohttp ClientSession")
            await injector.get(ClientSession).close()
            return result

        return wrapper

    return decorator
