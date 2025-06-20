"""連番プレフィックス生成関数のテストモジュール."""

import pytest

from moro.modules.number_prefix import generate_number_prefix


class TestGenerateNumberPrefix:
    """連番プレフィックス生成関数のテスト."""

    @pytest.mark.parametrize(
        "total_count,index,expected",
        [
            (9, 1, "1_"),
            (9, 9, "9_"),
        ]
    )
    def test_generate_number_prefix_single_digit(
        self, total_count: int, index: int, expected: str
    ) -> None:
        """単一桁の場合のプレフィックス生成をテスト."""
        assert generate_number_prefix(total_count, index) == expected

    @pytest.mark.parametrize(
        "total_count,index,expected",
        [
            (10, 1, "01_"),
            (99, 9, "09_"),
            (99, 10, "10_"),
            (99, 99, "99_"),
        ]
    )
    def test_generate_number_prefix_double_digit(
        self, total_count: int, index: int, expected: str
    ) -> None:
        """二桁の場合のプレフィックス生成をテスト."""
        assert generate_number_prefix(total_count, index) == expected

    @pytest.mark.parametrize(
        "total_count,index,expected",
        [
            (100, 1, "001_"),
            (999, 99, "099_"),
            (999, 100, "100_"),
            (999, 999, "999_"),
        ]
    )
    def test_generate_number_prefix_triple_digit(
        self, total_count: int, index: int, expected: str
    ) -> None:
        """三桁の場合のプレフィックス生成をテスト."""
        assert generate_number_prefix(total_count, index) == expected

    @pytest.mark.parametrize(
        "total_count,index,expected_error",
        [
            (0, 1, ValueError),  # 0個のURLリストの場合
            (10, 0, ValueError),  # インデックスが0以下の場合
            (10, -1, ValueError),  # インデックスが負の場合
            (10, 11, ValueError),  # インデックスがURL数より大きい場合
        ]
    )
    def test_generate_number_prefix_edge_cases(
        self, total_count: int, index: int, expected_error: type[Exception]
    ) -> None:
        """エッジケースのテスト."""
        with pytest.raises(expected_error):
            generate_number_prefix(total_count, index)
