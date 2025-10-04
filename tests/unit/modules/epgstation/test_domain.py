"""EPGStationモジュール独立ドメインテスト

他モジュールへの依存・参照は一切禁止
moro.modules.epgstation.* のみimport許可
"""

from datetime import datetime

import pytest
from hypothesis import assume, given, note
from hypothesis import strategies as st
from pydantic import ValidationError

from moro.modules.epgstation.domain import RecordingData, VideoFile, VideoFileType


@given(st.integers(min_value=0, max_value=9999999999999))
def test_should_format_start_time_when_timestamp_provided(timestamp_ms: int) -> None:
    """開始時刻のフォーマット表示をテスト"""
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


@given(
    st.tuples(
        st.integers(min_value=1, max_value=9999999999999),
        st.integers(min_value=1, max_value=9999999999999),
    ).map(sorted)
)
def test_should_calculate_duration_in_minutes(times: tuple[int, int]) -> None:
    """録画時間（分）の計算をテスト"""
    start_time, end_time = times
    assume(start_time < end_time)  # 開始時刻は終了時刻より前であること
    note(f"Testing duration from {start_time} to {end_time}")

    recording = RecordingData(
        id=1,
        name="テスト番組",
        start_at=start_time,
        end_at=end_time,
        video_files=[],
        is_recording=False,
        is_protected=False,
    )

    assert recording.duration_minutes == pytest.approx((end_time - start_time) // 60000)


@given(
    st.integers(min_value=1, max_value=999999),
    st.text(min_size=1, max_size=100),
    st.lists(
        st.builds(
            VideoFile,
            id=st.integers(min_value=1, max_value=999999),
            name=st.text(min_size=1, max_size=50),
            filename=st.text(min_size=1, max_size=100),
            type=st.sampled_from(VideoFileType),
            size=st.integers(min_value=1, max_value=10737418240),  # 10GB max
        ),
        min_size=1,
        max_size=5,
    ),
    st.booleans(),
)
def test_should_create_recording_with_video_files(
    recording_id: int, name: str, video_files: list[VideoFile], is_protected: bool
) -> None:
    """録画データにビデオファイルを含めて作成をテスト"""
    start_time = 1704105000000
    end_time = start_time + 1800000  # 30分後

    recording = RecordingData(
        id=recording_id,
        name=name,
        start_at=start_time,
        end_at=end_time,
        video_files=video_files,
        is_recording=False,
        is_protected=is_protected,
    )

    assert recording.id == recording_id
    assert recording.name == name
    assert len(recording.video_files) == len(video_files)
    assert recording.is_protected is is_protected


@given(
    st.integers(min_value=1, max_value=999999),
    st.text(min_size=1, max_size=100),
    st.booleans(),
)
def test_should_handle_empty_video_files_list(
    recording_id: int, name: str, is_recording: bool
) -> None:
    """ビデオファイルが空の場合の処理をテスト"""
    start_time = 1704105000000
    end_time = start_time + 1800000

    recording = RecordingData(
        id=recording_id,
        name=name,
        start_at=start_time,
        end_at=end_time,
        video_files=[],
        is_recording=is_recording,
        is_protected=False,
    )

    assert len(recording.video_files) == 0
    assert recording.is_recording is is_recording


@given(
    st.integers(min_value=1, max_value=999999),
    st.text(min_size=1, max_size=100),
    st.integers(min_value=1, max_value=9999999999999),
)
def test_should_validate_time_order(recording_id: int, name: str, start_time: int) -> None:
    """開始時刻が終了時刻より後の場合のバリデーションテスト"""
    end_time = start_time - 1  # 開始時刻より前の終了時刻

    with pytest.raises(ValidationError):
        RecordingData(
            id=recording_id,
            name=name,
            start_at=start_time,
            end_at=end_time,
            video_files=[],
            is_recording=False,
            is_protected=False,
        )


@given(st.integers(min_value=1, max_value=999999))
def test_should_validate_empty_name(recording_id: int) -> None:
    """空文字の名前の場合のバリデーションテスト"""
    with pytest.raises(ValidationError):
        RecordingData(
            id=recording_id,
            name="",  # 空文字は無効
            start_at=1704105000000,
            end_at=1704106800000,
            video_files=[],
            is_recording=False,
            is_protected=False,
        )
