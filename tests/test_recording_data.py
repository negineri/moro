"""RecordingData エンティティのテスト

TDD Red Phase: RecordingData のビジネスロジックをテスト
"""

import pytest
from pydantic import ValidationError

from moro.modules.epgstation.domain import RecordingData, VideoFile, VideoFileType


def test_should_format_start_time_when_timestamp_provided() -> None:
    """開始時刻のフォーマット表示をテスト"""
    from datetime import datetime

    # 2024-01-01 12:30 のタイムスタンプ (ms)
    timestamp_ms = 1704105000000

    recording = RecordingData(
        id=1,
        name="テスト番組",
        start_at=timestamp_ms,
        end_at=timestamp_ms + 1800000,  # 30分後
        video_files=[],
        is_recording=False,
        is_protected=False,
    )

    # システムのローカル時間帯で期待値を生成
    expected_time = datetime.fromtimestamp(timestamp_ms / 1000).strftime("%Y-%m-%d %H:%M")
    assert recording.formatted_start_time == expected_time


def test_should_calculate_duration_in_minutes() -> None:
    """録画時間（分）の計算をテスト"""
    start_time = 1704105000000  # 2024-01-01 12:30
    end_time = start_time + 1800000  # 30分後

    recording = RecordingData(
        id=1,
        name="テスト番組",
        start_at=start_time,
        end_at=end_time,
        video_files=[],
        is_recording=False,
        is_protected=False,
    )

    assert recording.duration_minutes == 30


def test_should_create_recording_with_video_files() -> None:
    """録画データにビデオファイルを含めて作成をテスト"""
    video_files = [
        VideoFile(
            id=1, name="TSファイル", filename="recording.ts", type=VideoFileType.TS, size=1073741824
        ),
        VideoFile(
            id=2,
            name="エンコード済み",
            filename="recording.mp4",
            type=VideoFileType.ENCODED,
            size=536870912,
        ),
    ]

    recording = RecordingData(
        id=123,
        name="録画番組タイトル",
        start_at=1704105000000,
        end_at=1704106800000,
        video_files=video_files,
        is_recording=False,
        is_protected=True,
    )

    assert recording.id == 123
    assert recording.name == "録画番組タイトル"
    assert len(recording.video_files) == 2
    assert recording.is_protected is True


def test_should_handle_empty_video_files_list() -> None:
    """ビデオファイルが空の場合の処理をテスト"""
    recording = RecordingData(
        id=1,
        name="ファイルなし番組",
        start_at=1704105000000,
        end_at=1704106800000,
        video_files=[],
        is_recording=True,
        is_protected=False,
    )

    assert len(recording.video_files) == 0
    assert recording.is_recording is True


def test_should_validate_required_fields_when_missing() -> None:
    """必須フィールドが不足している場合のバリデーションテスト"""
    with pytest.raises(ValidationError):
        RecordingData(
            id=1,
            name="テスト",
            start_at=1704105000000,
            end_at=1704104000000,  # end_at < start_at は無効
            video_files=[],
            is_recording=False,
            is_protected=False,
        )

    with pytest.raises(ValidationError):
        RecordingData(
            id=1,
            name="",  # 空文字は無効
            start_at=1704105000000,
            end_at=1704106800000,
            video_files=[],
            is_recording=False,
            is_protected=False,
        )
