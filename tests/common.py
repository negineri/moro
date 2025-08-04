"""共通テストユーティリティ - 依存性注入サポート"""

from collections.abc import Callable
from typing import ParamSpec, TypeVar

from injector import Injector, inject
from src.moro.config.settings import ConfigRepository

from moro.dependencies.container import create_injector

_P = ParamSpec("_P")
_R = TypeVar("_R")

config = ConfigRepository.create()

injector = create_injector(config)


def with_injector(injector: Injector) -> Callable[[Callable[_P, _R]], Callable[[], _R]]:
    """依存性注入を使用して関数をラップするデコレータ。

    https://github.com/python-injector/injector/issues/114
    """

    def decorator(f: Callable[_P, _R]) -> Callable[[], _R]:
        f = inject(f)

        def wrapper() -> _R:
            return injector.call_with_injection(f)

        return wrapper

    return decorator


with_injection = with_injector(injector)

__all__ = ["with_injection", "with_injector"]
