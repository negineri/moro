"""pydanticのテスト"""

from typing import Any

from pydantic import BaseModel, Field


class Cls1(BaseModel):
    int_var: int = Field(default=0, description="An integer variable")
    str_var: str = Field(default="", description="A string variable")
    bool_var: bool = Field(default=False, description="A boolean variable")


def test_cls1() -> None:
    """pydanticのテスト"""
    data: dict[str, Any] = {"int_var": 16, "str_var": "test", "bool_var": True}
    cls1 = Cls1(**data)
    assert cls1.int_var == 16
    assert cls1.str_var == "test"
    assert cls1.bool_var is True

    data = {"int_var": "8", "str_var": "8", "bool_var": "false"}
    cls1 = Cls1(**data)
    assert cls1.int_var == 8
    assert cls1.str_var == "8"
    assert cls1.bool_var is False

    data = {"bool_var": "FALSE"}
    assert Cls1(**data).bool_var is False
    data = {"bool_var": "false"}
    assert Cls1(**data).bool_var is False
    data = {"bool_var": "0"}
    assert Cls1(**data).bool_var is False
    data = {"bool_var": "True"}
    assert Cls1(**data).bool_var is True
    data = {"bool_var": "true"}
    assert Cls1(**data).bool_var is True
    data = {"bool_var": "TRUE"}
    assert Cls1(**data).bool_var is True
    data = {"bool_var": "1"}
    assert Cls1(**data).bool_var is True
