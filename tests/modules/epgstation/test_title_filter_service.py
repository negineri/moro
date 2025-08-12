"""TitleFilterService のテスト"""

import pytest

from moro.modules.epgstation.domain import (
    RecordingData,
    TitleFilterService,
    VideoFile,
    VideoFileType,
)


class TestTitleFilterService:
    """TitleFilterService のテストケース"""

    @pytest.fixture
    def sample_recordings(self) -> list[RecordingData]:
        """テスト用録画データ"""
        return [
            RecordingData(
                id=1,
                name="ニュース7",
                start_at=1700000000000,
                end_at=1700001800000,
                video_files=[
                    VideoFile(
                        id=1,
                        name="ニュース7.ts",
                        filename="news7.ts",
                        type=VideoFileType.TS,
                        size=1024 * 1024 * 100,
                    )
                ],
                is_recording=False,
                is_protected=False,
            ),
            RecordingData(
                id=2,
                name="朝のニュース",
                start_at=1700002000000,
                end_at=1700003800000,
                video_files=[
                    VideoFile(
                        id=2,
                        name="朝のニュース.ts",
                        filename="morning_news.ts",
                        type=VideoFileType.TS,
                        size=1024 * 1024 * 80,
                    )
                ],
                is_recording=False,
                is_protected=False,
            ),
            RecordingData(
                id=3,
                name="Drama Special",
                start_at=1700004000000,
                end_at=1700007600000,
                video_files=[
                    VideoFile(
                        id=3,
                        name="Drama Special.ts",
                        filename="drama_special.ts",
                        type=VideoFileType.ENCODED,
                        size=1024 * 1024 * 200,
                    )
                ],
                is_recording=True,
                is_protected=True,
            ),
        ]

    @pytest.fixture
    def filter_service(self) -> TitleFilterService:
        """TitleFilterService インスタンス"""
        return TitleFilterService()

    def test_apply_filter_with_no_filter_returns_all(
        self, filter_service: TitleFilterService, sample_recordings: list[RecordingData]
    ) -> None:
        """フィルター条件なしの場合、全データを返却"""
        result = filter_service.apply_filter(sample_recordings, title_filter=None)
        assert len(result) == 3
        assert result == sample_recordings

    def test_apply_filter_case_insensitive_basic(
        self, filter_service: TitleFilterService, sample_recordings: list[RecordingData]
    ) -> None:
        """大文字・小文字非区別の基本フィルタリング"""
        result = filter_service.apply_filter(sample_recordings, title_filter="ニュース")
        assert len(result) == 2
        assert all("ニュース" in rec.name for rec in result)

        # 大文字・小文字を区別しないテスト
        result_case = filter_service.apply_filter(sample_recordings, title_filter="drama")
        assert len(result_case) == 1

    def test_apply_filter_partial_match(
        self, filter_service: TitleFilterService, sample_recordings: list[RecordingData]
    ) -> None:
        """部分マッチのテスト"""
        result = filter_service.apply_filter(sample_recordings, title_filter="Special")
        assert len(result) == 1
        assert result[0].name == "Drama Special"

    def test_apply_filter_no_match(
        self, filter_service: TitleFilterService, sample_recordings: list[RecordingData]
    ) -> None:
        """マッチしない場合のテスト"""
        result = filter_service.apply_filter(sample_recordings, title_filter="バラエティ")
        assert len(result) == 0

    def test_apply_filter_regex_mode(
        self, filter_service: TitleFilterService, sample_recordings: list[RecordingData]
    ) -> None:
        """正規表現モードでのフィルタリング"""
        # "ニュース"で始まる番組を検索
        result = filter_service.apply_filter(
            sample_recordings, title_filter="^ニュース", regex=True
        )
        assert len(result) == 1
        assert result[0].name == "ニュース7"

        # "ニュース"を含む番組を検索
        result_contains = filter_service.apply_filter(
            sample_recordings, title_filter=".*ニュース.*", regex=True
        )
        assert len(result_contains) == 2

    def test_apply_filter_regex_case_sensitive(
        self, filter_service: TitleFilterService, sample_recordings: list[RecordingData]
    ) -> None:
        """正規表現モードでは大文字・小文字を区別する"""
        result = filter_service.apply_filter(sample_recordings, title_filter="drama", regex=True)
        assert len(result) == 0  # 大文字・小文字を区別するため（Drama != drama）

    def test_apply_filter_invalid_regex(
        self, filter_service: TitleFilterService, sample_recordings: list[RecordingData]
    ) -> None:
        """無効な正規表現のエラーハンドリング"""
        from moro.modules.epgstation.domain import RegexPatternError

        with pytest.raises(RegexPatternError, match="正規表現エラー"):
            filter_service.apply_filter(sample_recordings, title_filter="[", regex=True)

    def test_apply_filter_empty_list(self, filter_service: TitleFilterService) -> None:
        """空リストのフィルタリング"""
        result = filter_service.apply_filter([], title_filter="ニュース")
        assert len(result) == 0

    def test_apply_filter_empty_string_filter(
        self, filter_service: TitleFilterService, sample_recordings: list[RecordingData]
    ) -> None:
        """空文字フィルターの場合"""
        result = filter_service.apply_filter(sample_recordings, title_filter="")
        assert len(result) == 3  # 空文字は全マッチ

    def test_apply_filter_dangerous_regex_patterns(
        self, filter_service: TitleFilterService, sample_recordings: list[RecordingData]
    ) -> None:
        """危険な正規表現パターンの検出"""
        from moro.modules.epgstation.domain import RegexPatternError

        # ReDoS攻撃の可能性がある危険パターン
        dangerous_patterns = [
            "(a+)+$",  # 指数バックトラッキング
            "(a|a)*$",  # 代替重複
            "([a-zA-Z]+)*$",  # 文字クラス繰り返し
        ]

        for pattern in dangerous_patterns:
            with pytest.raises(RegexPatternError, match="危険な正規表現パターン"):
                filter_service.apply_filter(sample_recordings, title_filter=pattern, regex=True)

    def test_apply_filter_custom_exceptions(
        self, filter_service: TitleFilterService, sample_recordings: list[RecordingData]
    ) -> None:
        """カスタム例外クラスのテスト"""
        from moro.modules.epgstation.domain import FilterError, RegexPatternError

        # 基底例外クラスの継承確認
        try:
            filter_service.apply_filter(sample_recordings, title_filter="[", regex=True)
        except Exception as e:
            assert isinstance(e, FilterError)
            assert isinstance(e, RegexPatternError)
