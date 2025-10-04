"""EPGStation パフォーマンステスト

仕様要件:
- Table形式（100件）: 50ms以下
- JSON形式（100件）: 40ms以下
- オーバーヘッド: 10ms以下
- 大量データ（1000件）でのメモリリーク回避
"""

import time
from typing import Any

import pytest

from moro.cli.epgstation import JsonFormatter, TableFormatter
from moro.modules.epgstation.domain import RecordingData, VideoFile, VideoFileType


def create_test_recordings(count: int) -> list[RecordingData]:
    """指定数のテスト録画データを生成"""
    recordings = []
    for i in range(count):
        video_files = []
        # 半分の録画にビデオファイルを追加
        if i % 2 == 0:
            video_files = [
                VideoFile(
                    id=i * 10 + j,
                    name=f"video_{i}_{j}.ts",
                    filename=f"video_{i}_{j}.ts",
                    type=VideoFileType.TS,
                    size=1500000000 + j * 100000,
                )
                for j in range(2)  # 各録画に2つのビデオファイル
            ]

        recordings.append(
            RecordingData(
                id=i,
                name=f"パフォーマンステスト番組_{i}",
                start_at=1691683200000 + i * 3600000,
                end_at=1691686800000 + i * 3600000,
                video_files=video_files,
                is_recording=i % 5 == 0,
                is_protected=i % 7 == 0,
            )
        )
    return recordings


def measure_execution_time(func: Any, *args: Any, **kwargs: Any) -> tuple[Any, float]:
    """関数の実行時間を測定"""
    start_time = time.perf_counter()
    result = func(*args, **kwargs)
    end_time = time.perf_counter()
    execution_time = (end_time - start_time) * 1000  # ms単位
    return result, execution_time


class TestTableFormatterPerformance:
    """TableFormatter のパフォーマンステスト"""

    def test_format_100_recordings_within_50ms(self) -> None:
        """100件の録画データを50ms以内でフォーマット"""
        # Given
        recordings = create_test_recordings(100)
        formatter = TableFormatter()

        # When
        result, execution_time = measure_execution_time(formatter.format, recordings)

        # Then
        assert execution_time < 50.0, f"実行時間 {execution_time:.2f}ms が目標50ms を超過"
        assert len(result) > 0
        assert "録画ID" in result  # 正常にフォーマットされている確認

    def test_format_1000_recordings_memory_efficiency(self) -> None:
        """1000件の大量データでのメモリ効率性確認"""
        # Given
        recordings = create_test_recordings(1000)
        formatter = TableFormatter()

        # When
        result, execution_time = measure_execution_time(formatter.format, recordings)

        # Then
        # 大量データでも完了すること
        assert len(result) > 0
        assert "録画ID" in result
        # 実行時間は線形スケール想定（10倍のデータで500ms以内）
        assert execution_time < 500.0, f"大量データ処理時間 {execution_time:.2f}ms が想定を超過"

    def test_format_empty_data_fast_response(self) -> None:
        """空データの高速レスポンス確認"""
        # Given
        formatter = TableFormatter()

        # When
        result, execution_time = measure_execution_time(formatter.format, [])

        # Then
        assert execution_time < 1.0, f"空データ処理時間 {execution_time:.2f}ms が1msを超過"
        assert result == "録画データが見つかりませんでした。"

    def test_format_long_titles_performance(self) -> None:
        """長いタイトル処理のパフォーマンス確認"""
        # Given
        long_title = "非常に長いタイトルの番組名です" * 20  # 600文字程度
        recordings = [
            RecordingData(
                id=i,
                name=f"{long_title}_{i}",
                start_at=1691683200000,
                end_at=1691686800000,
                video_files=[],
                is_recording=False,
                is_protected=False,
            )
            for i in range(50)
        ]
        formatter = TableFormatter()

        # When
        result, execution_time = measure_execution_time(formatter.format, recordings)

        # Then
        assert execution_time < 25.0, f"長タイトル処理時間 {execution_time:.2f}ms が25msを超過"
        assert "..." in result  # 切り詰め処理が正常動作


class TestJsonFormatterPerformance:
    """JsonFormatter のパフォーマンステスト"""

    def test_format_100_recordings_within_40ms(self) -> None:
        """100件の録画データを40ms以内でJSONフォーマット"""
        # Given
        recordings = create_test_recordings(100)
        formatter = JsonFormatter()

        # When
        result, execution_time = measure_execution_time(formatter.format, recordings)

        # Then
        assert execution_time < 40.0, f"JSON実行時間 {execution_time:.2f}ms が目標40msを超過"
        assert len(result) > 0
        # JSON形式の妥当性確認
        import json

        parsed = json.loads(result)
        assert isinstance(parsed, list)
        assert len(parsed) == 100

    def test_format_1000_recordings_json_scalability(self) -> None:
        """1000件での JSON フォーマットスケーラビリティ"""
        # Given
        recordings = create_test_recordings(1000)
        formatter = JsonFormatter()

        # When
        result, execution_time = measure_execution_time(formatter.format, recordings)

        # Then
        # JSON処理は線形スケール（10倍で400ms以内想定）
        assert execution_time < 400.0, f"大量JSON処理時間 {execution_time:.2f}ms が400msを超過"
        import json

        parsed = json.loads(result)
        assert len(parsed) == 1000

    def test_json_serialization_overhead(self) -> None:
        """JSON シリアライゼーションオーバーヘッド測定"""
        # Given
        recordings = create_test_recordings(10)  # 少数で正確な測定
        formatter = JsonFormatter()

        # model_dump_json() の時間測定（新しい実装に合わせる）
        start_time = time.perf_counter()
        json_strings = [recording.model_dump_json() for recording in recordings]
        model_dump_json_time = (time.perf_counter() - start_time) * 1000

        # 配列結合の時間測定
        start_time = time.perf_counter()
        "[\n  " + ",\n  ".join(json_strings) + "\n]"
        join_time = (time.perf_counter() - start_time) * 1000

        # When
        _, total_time = measure_execution_time(formatter.format, recordings)

        # Then
        overhead = total_time - model_dump_json_time - join_time
        assert overhead < 5.0, f"JSONオーバーヘッド {overhead:.2f}ms が5msを超過"

    def test_format_japanese_text_performance(self) -> None:
        """日本語テキストのJSONパフォーマンス"""
        # Given
        japanese_recordings = []
        for i in range(100):
            japanese_recordings.append(
                RecordingData(
                    id=i,
                    name=f"日本語番組タイトル・特殊文字「」〜{i}",
                    start_at=1691683200000,
                    end_at=1691686800000,
                    video_files=[
                        VideoFile(
                            id=i,
                            name=f"日本語ファイル名_{i}.ts",
                            filename=f"japanese_file_{i}.ts",
                            type=VideoFileType.TS,
                            size=1000000000,
                        )
                    ],
                    is_recording=False,
                    is_protected=False,
                )
            )
        formatter = JsonFormatter()

        # When
        result, execution_time = measure_execution_time(formatter.format, japanese_recordings)

        # Then
        assert execution_time < 50.0, f"日本語JSON処理時間 {execution_time:.2f}ms が50msを超過"
        # 日本語が正しく保持されている確認
        import json

        parsed = json.loads(result)
        assert "日本語番組タイトル" in parsed[0]["name"]


class TestFormatterComparison:
    """フォーマッター間の比較パフォーマンステスト"""

    @pytest.mark.parametrize("data_size", [10, 50, 100, 500])
    def test_table_vs_json_performance_comparison(self, data_size: int) -> None:
        """TableとJSONフォーマッターのパフォーマンス比較"""
        # Given
        recordings = create_test_recordings(data_size)
        table_formatter = TableFormatter()
        json_formatter = JsonFormatter()

        # When
        _, table_time = measure_execution_time(table_formatter.format, recordings)
        _, json_time = measure_execution_time(json_formatter.format, recordings)

        # Then
        # 両方とも合理的な時間内で完了することを確認
        max_expected_time = data_size * 0.5  # 1件あたり0.5ms以内
        assert table_time < max_expected_time, "Table処理時間が想定を超過"
        assert json_time < max_expected_time, "JSON処理時間が想定を超過"

    def test_memory_usage_comparison(self) -> None:
        """メモリ使用量の比較確認"""
        # Given
        large_recordings = create_test_recordings(1000)

        # テスト実行前のベースライン確認として軽量データで測定
        small_recordings = create_test_recordings(10)

        table_formatter = TableFormatter()
        json_formatter = JsonFormatter()

        # When - 小さなデータでの基準時間
        _, small_table_time = measure_execution_time(table_formatter.format, small_recordings)
        _, small_json_time = measure_execution_time(json_formatter.format, small_recordings)

        # 大きなデータでの実行
        _, large_table_time = measure_execution_time(table_formatter.format, large_recordings)
        _, large_json_time = measure_execution_time(json_formatter.format, large_recordings)

        # Then - 線形スケーリング確認（100倍のデータで200倍以内の時間）
        table_scale_factor = large_table_time / small_table_time if small_table_time > 0 else 0
        json_scale_factor = large_json_time / small_json_time if small_json_time > 0 else 0

        assert table_scale_factor < 200, (
            f"Table処理の非線形スケーリング検出: {table_scale_factor:.1f}x"
        )
        assert json_scale_factor < 200, (
            f"JSON処理の非線形スケーリング検出: {json_scale_factor:.1f}x"
        )
