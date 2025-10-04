"""injectorのテスト

コア機能の単体テスト - 依存性注入システム
"""

from collections.abc import Callable
from dataclasses import dataclass

from injector import Binder, Injector, inject


@inject
@dataclass
class Cls1:
    ins2: "Cls2"
    ins3: "Cls3"


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

    injector = Injector()
    ins1 = injector.get(Cls1)
    assert id(ins1.ins2) != id(ins2)

    injector = Injector(return_binder(ins2))
    ins1 = injector.get(Cls1)
    assert id(ins1.ins2) == id(ins2)
