"""injectorのテスト"""

from collections.abc import Callable
from dataclasses import dataclass
from os import getenv

from injector import Binder, Injector, inject
from tests.common import with_injection

from moro.config.settings import CommonConfig


@inject
@dataclass
class Cls1:
    ins2: "Cls2"
    ins3: "Cls3"

    def print(self) -> None:
        print(f"Cls1: ins2={id(self.ins2)}, ins3={id(self.ins3)}")  # noqa: T201


@dataclass
class Cls2:
    pass


@dataclass
class Cls3:
    pass


def return_binder(ins2: "Cls2") -> Callable[[Binder], None]:
    """
    Returns a function that accepts a Binder and returns None.

    This function can be used to inject dependencies into the Binder.
    """

    def binder(binder: Binder) -> None:
        binder.bind(Cls2, to=ins2)

    return binder


def test_injector() -> None:
    ins2 = Cls2()
    print(f"ins2: {id(ins2)}")  # noqa: T201
    # injector = Injector(return_binder(ins2))
    injector = Injector()
    ins1 = injector.get(Cls1)
    print(f"ins1: {id(ins1)}")  # noqa: T201
    ins1.print()


def test_evn() -> None:
    test = getenv("MORO_TEST", "default")
    print(f"MORO_TEST: {test}")  # noqa: T201


@with_injection
def test_with_injection(common_config: CommonConfig) -> None:
    assert isinstance(common_config, CommonConfig)
