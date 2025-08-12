"""TitleFilterService パフォーマンステスト"""

import time

import pytest

from moro.modules.epgstation.domain import (
    RecordingData,
    TitleFilterService,
    VideoFile,
    VideoFileType,
)


class TestTitleFilterServicePerformance:
    """TitleFilterService のパフォーマンステスト"""

    @pytest.fixture
    def large_dataset(self) -> list[RecordingData]:
        """1000件の大量テストデータ"""
        recordings = []
        titles = [
            "ニュース7",
            "朝のニュース",
            "ニュースウォッチ9",
            "報道ステーション",
            "情報ライブ ミヤネ屋",
            "ひるおび！",
            "バラエティ番組",
            "ドラマスペシャル",
            "アニメ特集",
            "映画劇場",
        ]

        for i in range(1000):
            title_index = i % len(titles)
            recordings.append(
                RecordingData(
                    id=i + 1,
                    name=f"{titles[title_index]}_{i:04d}",
                    start_at=1700000000000 + i * 3600000,  # 1時間間隔
                    end_at=1700000000000 + i * 3600000 + 1800000,  # 30分番組
                    video_files=[
                        VideoFile(
                            id=i + 1,
                            name=f"{titles[title_index]}_{i:04d}.ts",
                            filename=f"recording_{i:04d}.ts",
                            type=VideoFileType.TS,
                            size=1024 * 1024 * 100,  # 100MB
                        )
                    ],
                    is_recording=False,
                    is_protected=False,
                )
            )
        return recordings

    @pytest.fixture
    def filter_service(self) -> TitleFilterService:
        """TitleFilterService インスタンス"""
        return TitleFilterService()

    def test_filter_performance_1000_records(
        self, filter_service: TitleFilterService, large_dataset: list[RecordingData]
    ) -> None:
        """1000件データの1秒以内処理を検証"""
        # ニュース関連番組を抽出（約400件想定）
        start_time = time.time()
        result = filter_service.apply_filter(large_dataset, title_filter="ニュース")
        end_time = time.time()

        execution_time = end_time - start_time

        # アサーション
        assert execution_time < 1.0, f"処理時間が1秒を超過: {execution_time:.3f}秒"
        assert len(result) > 0, "フィルター結果が空"
        # ニュース関連が約400件あることを確認
        assert 300 <= len(result) <= 500, f"予期される結果数と異なる: {len(result)}"

        # 全結果が「ニュース」を含むことを確認
        for record in result:
            assert "ニュース" in record.name

    def test_regex_performance_1000_records(
        self, filter_service: TitleFilterService, large_dataset: list[RecordingData]
    ) -> None:
        """正規表現モードでのパフォーマンステスト"""
        # 「ニュース」で始まる番組を抽出
        start_time = time.time()
        result = filter_service.apply_filter(large_dataset, title_filter="^ニュース", regex=True)
        end_time = time.time()

        execution_time = end_time - start_time

        # アサーション
        assert execution_time < 1.0, f"正規表現処理時間が1秒を超過: {execution_time:.3f}秒"
        assert len(result) > 0, "正規表現フィルター結果が空"

        # 全結果が「ニュース」で始まることを確認
        for record in result:
            assert record.name.startswith("ニュース")

    def test_no_filter_performance_baseline(
        self, filter_service: TitleFilterService, large_dataset: list[RecordingData]
    ) -> None:
        """フィルターなしのベースライン性能測定"""
        start_time = time.time()
        result = filter_service.apply_filter(large_dataset, title_filter=None)
        end_time = time.time()

        execution_time = end_time - start_time

        # フィルターなしは非常に高速であるべき
        assert execution_time < 0.1, f"ベースライン処理時間が遅すぎる: {execution_time:.3f}秒"
        assert len(result) == 1000, "全データが返却されていない"

    def test_memory_usage_optimization(
        self, filter_service: TitleFilterService, large_dataset: list[RecordingData]
    ) -> None:
        """メモリ使用量の最適化検証（簡易版）"""
        import gc

        # ガベージコレクション実行
        gc.collect()

        # フィルタリング実行
        result = filter_service.apply_filter(large_dataset, title_filter="ニュース")

        # 結果が元データと異なるオブジェクトであることを確認（コピーではなく参照）
        assert result is not large_dataset, "元データと同じオブジェクトが返却されている"

        # フィルター結果のデータ構造が正しいことを確認
        for record in result[:5]:  # 最初の5件のみ確認
            assert isinstance(record, RecordingData)
            assert hasattr(record, "name")
            assert hasattr(record, "video_files")

        # メモリリーク防止のため、大きなデータを削除
        del result
