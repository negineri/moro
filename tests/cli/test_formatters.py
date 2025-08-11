"""EPGStation フォーマッターテスト"""

import json
from unittest.mock import Mock, PropertyMock

from moro.cli.epgstation import JsonFormatter, TableFormatter
from moro.modules.epgstation.domain import RecordingData, VideoFile, VideoFileType


class TestTableFormatter:
    """TableFormatter のテストクラス"""

    def test_format_single_recording_with_video_files(self) -> None:
        """単一録画（ビデオファイルあり）の正確なテーブル出力"""
        # Given
        recordings = [
            RecordingData(
                id=12345,
                name="テスト番組",
                start_at=1691683200000,
                end_at=1691686800000,
                video_files=[
                    VideoFile(
                        id=1,
                        name="program.ts",
                        filename="program.ts",
                        type=VideoFileType.TS,
                        size=1234567890,
                    )
                ],
                is_recording=False,
                is_protected=False,
            )
        ]
        formatter = TableFormatter()

        # When
        result = formatter.format(recordings)

        # Then
        assert "録画ID" in result
        assert "タイトル" in result
        assert "開始時刻" in result
        assert "ファイル名" in result
        assert "種別" in result
        assert "サイズ" in result
        assert "│" in result  # テーブル区切り文字
        assert "12345" in result
        assert "テスト番組" in result
        assert "program.ts" in result
        assert "TS" in result
        assert "1.15GB" in result

    def test_format_recording_without_video_files(self) -> None:
        """ビデオファイルなし録画の N/A 表示確認"""
        # Given
        recordings = [
            RecordingData(
                id=99999,
                name="ビデオファイルなし番組",
                start_at=1691683200000,
                end_at=1691686800000,
                video_files=[],
                is_recording=True,
                is_protected=True,
            )
        ]
        formatter = TableFormatter()

        # When
        result = formatter.format(recordings)

        # Then
        assert "99999" in result
        assert "ビデオファイルなし番組" in result
        # N/A が3つ（ファイル名、種別、サイズ）
        n_a_count = result.count("N/A")
        assert n_a_count == 3

    def test_format_handles_long_titles(self) -> None:
        """長いタイトルの切り詰め動作確認"""
        # Given
        long_title = "非常に長いタイトルの番組名です" * 5  # 40文字を超える
        recordings = [
            RecordingData(
                id=1,
                name=long_title,
                start_at=1691683200000,
                end_at=1691686800000,
                video_files=[],
                is_recording=False,
                is_protected=False,
            )
        ]
        formatter = TableFormatter()

        # When
        result = formatter.format(recordings)

        # Then
        # 40文字で切り詰められて...が付く
        assert "..." in result
        # 元の長いタイトル全体は含まれない
        assert long_title not in result

    def test_format_empty_message(self) -> None:
        """空データでの適切なメッセージ表示"""
        # Given
        formatter = TableFormatter()

        # When
        result = formatter.format([])

        # Then
        assert result == "録画データが見つかりませんでした。"

    def test_format_empty_message_method(self) -> None:
        """format_empty_message メソッドの単体テスト"""
        # Given
        formatter = TableFormatter()

        # When
        result = formatter.format_empty_message()

        # Then
        assert result == "録画データが見つかりませんでした。"

    def test_format_multiple_video_files(self) -> None:
        """複数ビデオファイルを持つ録画の表示確認"""
        # Given
        recordings = [
            RecordingData(
                id=555,
                name="複数ファイル番組",
                start_at=1691683200000,
                end_at=1691686800000,
                video_files=[
                    VideoFile(
                        id=1,
                        name="original.ts",
                        filename="original.ts",
                        type=VideoFileType.TS,
                        size=2000000000,
                    ),
                    VideoFile(
                        id=2,
                        name="encoded.mp4",
                        filename="encoded.mp4",
                        type=VideoFileType.ENCODED,
                        size=500000000,
                    ),
                ],
                is_recording=False,
                is_protected=False,
            )
        ]
        formatter = TableFormatter()

        # When
        result = formatter.format(recordings)

        # Then
        # 同じ録画IDが2行に表示される
        recording_id_count = result.count("555")
        assert recording_id_count == 2
        assert "original.ts" in result
        assert "encoded.mp4" in result
        assert "TS" in result
        assert "ENCODED" in result


class TestJsonFormatter:
    """JsonFormatter のテストクラス"""

    def test_format_produces_valid_json_structure(self) -> None:
        """有効なJSON構造の出力確認"""
        # Given
        recordings = [
            RecordingData(
                id=123,
                name="JSON テスト番組",
                start_at=1691683200000,
                end_at=1691686800000,
                video_files=[],
                is_recording=False,
                is_protected=True,
            )
        ]
        formatter = JsonFormatter()

        # When
        result = formatter.format(recordings)

        # Then
        parsed = json.loads(result)  # JSON妥当性検証
        assert isinstance(parsed, list)
        assert len(parsed) == 1
        assert parsed[0]["id"] == 123
        assert parsed[0]["name"] == "JSON テスト番組"

    def test_format_includes_all_recording_fields(self) -> None:
        """全録画フィールドの完全出力確認"""
        # Given
        recordings = [
            RecordingData(
                id=456,
                name="完全フィールド番組",
                start_at=1691683200000,
                end_at=1691686800000,
                video_files=[
                    VideoFile(
                        id=10,
                        name="complete.ts",
                        filename="complete.ts",
                        type=VideoFileType.TS,
                        size=1500000000,
                    )
                ],
                is_recording=True,
                is_protected=False,
            )
        ]
        formatter = JsonFormatter()

        # When
        result = formatter.format(recordings)

        # Then
        parsed = json.loads(result)
        recording = parsed[0]

        # 全フィールドの存在確認
        assert "id" in recording
        assert "name" in recording
        assert "start_at" in recording
        assert "end_at" in recording
        assert "video_files" in recording
        assert "is_recording" in recording
        assert "is_protected" in recording

        # 値の正確性確認
        assert recording["id"] == 456
        assert recording["name"] == "完全フィールド番組"
        assert recording["is_recording"] is True
        assert recording["is_protected"] is False
        assert len(recording["video_files"]) == 1

    def test_format_handles_japanese_characters(self) -> None:
        """日本語文字列の適切なエンコーディング"""
        # Given
        recordings = [
            RecordingData(
                id=789,
                name="日本語タイトル・特殊文字「」",
                start_at=1691683200000,
                end_at=1691686800000,
                video_files=[],
                is_recording=False,
                is_protected=False,
            )
        ]
        formatter = JsonFormatter()

        # When
        result = formatter.format(recordings)

        # Then
        parsed = json.loads(result)
        assert parsed[0]["name"] == "日本語タイトル・特殊文字「」"
        # ensure_ascii=False が適用されている確認
        assert "日本語タイトル・特殊文字「」" in result

    def test_format_fallback_on_serialization_error(self) -> None:
        """シリアライゼーション失敗時のフォールバック動作"""
        # Given
        # model_dump() が失敗するような録画データをモック
        mock_recording = Mock(spec=RecordingData)
        mock_recording.model_dump.side_effect = Exception("Serialization error")
        mock_recording.id = 999
        mock_recording.name = "エラーテスト番組"
        mock_recording.formatted_start_time = "2023-08-11 10:00"
        mock_recording.duration_minutes = 60

        formatter = JsonFormatter()

        # When
        result = formatter.format([mock_recording])

        # Then
        parsed = json.loads(result)
        assert isinstance(parsed, list)
        assert len(parsed) == 1
        fallback_data = parsed[0]

        # フォールバックフィールドの確認
        assert fallback_data["id"] == 999
        assert fallback_data["name"] == "エラーテスト番組"
        assert fallback_data["start_time"] == "2023-08-11 10:00"
        assert fallback_data["duration_minutes"] == 60
        assert fallback_data["error"] == "詳細情報の取得に失敗"

    def test_format_empty_message(self) -> None:
        """空データでの適切なJSONメッセージ"""
        # Given
        formatter = JsonFormatter()

        # When
        result = formatter.format([])

        # Then
        parsed = json.loads(result)
        assert "recordings" in parsed
        assert "message" in parsed
        assert parsed["recordings"] == []
        assert parsed["message"] == "録画データが見つかりませんでした。"

    def test_format_empty_message_method(self) -> None:
        """format_empty_message メソッドの単体テスト"""
        # Given
        formatter = JsonFormatter()

        # When
        result = formatter.format_empty_message()

        # Then
        parsed = json.loads(result)
        assert parsed["recordings"] == []
        assert parsed["message"] == "録画データが見つかりませんでした。"

    def test_format_extreme_fallback_on_complete_failure(self) -> None:
        """完全失敗時の極端なフォールバック動作確認"""
        # Given
        # すべてのアクセスが失敗するモック
        mock_recording = Mock()
        # id アクセスも失敗する状況
        type(mock_recording).id = PropertyMock(side_effect=Exception("Complete failure"))
        mock_recording.model_dump.side_effect = Exception("Serialization error")

        formatter = JsonFormatter()

        # When
        result = formatter.format([mock_recording])

        # Then
        parsed = json.loads(result)
        assert isinstance(parsed, list)
        assert len(parsed) == 1
        extreme_fallback = parsed[0]

        assert extreme_fallback["error"] == "データ取得エラー"
        assert extreme_fallback["id"] == "unknown"  # getattr fallback


# テスト用ヘルパー関数
def create_test_recording(
    recording_id: int = 1, name: str = "テスト番組", with_video_files: bool = True
) -> RecordingData:
    """テスト用の録画データを作成"""
    video_files = []
    if with_video_files:
        video_files = [
            VideoFile(
                id=1,
                name="test.ts",
                filename="test.ts",
                type=VideoFileType.TS,
                size=1000000000,
            )
        ]

    return RecordingData(
        id=recording_id,
        name=name,
        start_at=1691683200000,
        end_at=1691686800000,
        video_files=video_files,
        is_recording=False,
        is_protected=False,
    )
