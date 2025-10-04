"""Unit tests for hypothesis examples."""

from random import Random
from typing import Any

import pytest
from hypothesis import HealthCheck, assume, example, given, note, settings
from hypothesis import strategies as st


def selection_sort(lst: list[float]) -> list[float]:
    result: list[float] = []
    while lst:
        smallest = min(lst)
        result.append(smallest)
        lst.remove(smallest)
    return result


@given(st.integers())
def test_is_integer(n: int) -> None:
    # print(f"called with {n}")
    assert isinstance(n, int)


@given(st.lists(st.integers() | st.floats(allow_nan=False)))
def test_sort_correct(lst: list[float]) -> None:
    # print(f"called with {lst}")
    assert selection_sort(lst.copy()) == sorted(lst)


@given(st.integers(), st.lists(st.floats()))
def test_multiple_arguments(n: int, lst: list[float]) -> None:
    assert isinstance(n, int)
    assert isinstance(lst, list)
    for f in lst:
        assert isinstance(f, float)


@given(st.integers(), st.integers().filter(lambda n: n != 0))
def test_remainder_magnitude(a: int, b: int) -> None:
    # the remainder after division is always less than
    # the divisor
    assert abs(a % b) < abs(b)


@settings(suppress_health_check=[HealthCheck.filter_too_much], max_examples=10)
@given(st.integers(), st.integers().filter(lambda n: n != 0))
def test_floor_division_lossless_when_b_divides_a(a: int, b: int) -> None:
    assume(a % b == 0)
    # we want to assume that:
    # * b is nonzero, and
    # * b divides a
    assert (a // b) * b == a


def json(*, finite_only: bool = True) -> st.SearchStrategy:
    """Helper function to describe JSON objects, with optional inf and nan."""
    numbers = st.floats(allow_infinity=not finite_only, allow_nan=not finite_only)
    return st.recursive(
        st.none() | st.booleans() | st.integers() | numbers | st.text(),
        extend=lambda xs: st.lists(xs) | st.dictionaries(st.text(), xs),
    )


@st.composite
def sums_to_one(draw: Any) -> list[float]:
    values = draw(st.lists(st.floats(0, 1, exclude_min=True), min_size=1))
    # print(f"Generated list: {values}")
    return [f / sum(values) for f in values]


@st.composite
def sums_to_n(draw: Any, *, n: float = 1) -> list[float]:
    lst = draw(st.lists(st.floats(0, 1), min_size=1))
    assume(sum(lst) > 0)
    return [f / sum(lst) * n for f in lst]


@given(sums_to_n(n=1))
def test(lst: list[float]) -> None:
    # ignore floating point errors
    assert sum(lst) == pytest.approx(1)


@st.composite
def ordered_pairs(draw: Any) -> tuple[int, int]:
    n1 = draw(st.integers())
    n2 = draw(st.integers(min_value=n1))
    return (n1, n2)


@given(ordered_pairs())
def test_pairs_are_ordered_a(pair: tuple[int, int]) -> None:
    n1, n2 = pair
    assert n1 <= n2


@given(st.tuples(st.integers(), st.integers()).map(sorted))
def test_pairs_are_ordered_b(pair: tuple[int, int]) -> None:
    n1, n2 = pair
    assert n1 <= n2


@example(2**17 - 1)
@given(st.integers())
def test_something_with_integers(n: int) -> None:
    assert n < 100


@given(st.lists(st.integers()), st.randoms())
def test_shuffle_is_noop(ls: list[int], r: Random) -> None:
    ls2 = list(ls)
    r.shuffle(ls2)
    note(f"Shuffle: {ls2!r}")
    assert ls == ls2
