"""共通テストユーティリティ - 依存性注入サポート"""

import functools
import inspect
from collections.abc import Callable
from tempfile import TemporaryDirectory
from typing import ParamSpec, TypeVar

from injector import Injector, inject
from src.moro.config.settings import ConfigRepository

from moro.dependencies.container import create_injector
from moro.modules.common import CommonConfig

_P = ParamSpec("_P")
_R = TypeVar("_R")

config = ConfigRepository.create()

injector = create_injector(config)


def with_injector(injector: Injector) -> Callable[[Callable[_P, _R]], Callable[..., _R]]:
    """依存性注入を使用して関数をラップするデコレータ。

    https://github.com/python-injector/injector/issues/114
    """

    def decorator(f: Callable[_P, _R]) -> Callable[..., _R]:
        f = inject(f)

        @functools.wraps(f)
        def wrapper(**kwargs) -> _R:  # This function is inspected and called by pytest
            user_data_dir = TemporaryDirectory()
            user_cache_dir = TemporaryDirectory()
            working_dir = TemporaryDirectory()
            injector.get(CommonConfig).user_data_dir = user_data_dir.name
            injector.get(CommonConfig).user_cache_dir = user_cache_dir.name
            injector.get(CommonConfig).working_dir = working_dir.name

            result = injector.call_with_injection(f, kwargs=kwargs)

            user_data_dir.cleanup()
            user_cache_dir.cleanup()
            working_dir.cleanup()
            return result

        # Remove parameters which will be provided by injector, so that pytest is not confused
        sig = inspect.signature(wrapper)
        not_injected_parameters = tuple(
            param
            for param in sig.parameters.values()
            if param.name not in f.__bindings__  # pyright: ignore[reportFunctionMemberAccess]
        )
        wrapper.__signature__ = sig.replace(parameters=not_injected_parameters)  # pyright: ignore[reportAttributeAccessIssue]

        return wrapper

    return decorator


with_injection = with_injector(injector)

__all__ = ["with_injection", "with_injector"]
