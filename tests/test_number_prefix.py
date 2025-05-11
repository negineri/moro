"""連番プレフィックス生成関数のテストモジュール."""

import pytest

from moro.modules.number_prefix import generate_number_prefix


class TestGenerateNumberPrefix:
    """連番プレフィックス生成関数のテスト."""

    def test_generate_number_prefix_single_digit(self) -> None:
        """単一桁の場合のプレフィックス生成をテスト."""
        # 9個のURLリストの場合、1桁のプレフィックスが生成される
        assert generate_number_prefix(9, 1) == "1_"
        assert generate_number_prefix(9, 9) == "9_"

    def test_generate_number_prefix_double_digit(self) -> None:
        """二桁の場合のプレフィックス生成をテスト."""
        # 10個のURLリストの場合、2桁のプレフィックスが生成される
        assert generate_number_prefix(10, 1) == "01_"
        assert generate_number_prefix(99, 9) == "09_"
        assert generate_number_prefix(99, 10) == "10_"
        assert generate_number_prefix(99, 99) == "99_"

    def test_generate_number_prefix_triple_digit(self) -> None:
        """三桁の場合のプレフィックス生成をテスト."""
        # 100個のURLリストの場合、3桁のプレフィックスが生成される
        assert generate_number_prefix(100, 1) == "001_"
        assert generate_number_prefix(999, 99) == "099_"
        assert generate_number_prefix(999, 100) == "100_"
        assert generate_number_prefix(999, 999) == "999_"

    def test_generate_number_prefix_edge_cases(self) -> None:
        """エッジケースのテスト."""
        # 0個のURLリストの場合(異常系)
        with pytest.raises(ValueError):
            generate_number_prefix(0, 1)

        # インデックスが0以下の場合(異常系)
        with pytest.raises(ValueError):
            generate_number_prefix(10, 0)

        with pytest.raises(ValueError):
            generate_number_prefix(10, -1)

        # インデックスがURL数より大きい場合(異常系)
        with pytest.raises(ValueError):
            generate_number_prefix(10, 11)
