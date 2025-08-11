"""VideoFile 値オブジェクトのテスト

TDD Red Phase: VideoFile のビジネスロジックをテスト
"""

import pytest
from pydantic import ValidationError

from moro.modules.epgstation.domain import VideoFile, VideoFileType


def test_should_format_file_size_in_appropriate_unit_when_large_size() -> None:
    """ファイルサイズの単位変換ロジックをテスト"""
    # Bytes
    video_file = VideoFile(
        id=1, name="test_file", filename="test.ts", type=VideoFileType.TS, size=512
    )
    assert video_file.formatted_size == "512B"

    # KB
    video_file = VideoFile(
        id=1,
        name="test_file",
        filename="test.ts",
        type=VideoFileType.TS,
        size=1536,  # 1.5KB
    )
    assert video_file.formatted_size == "1.5KB"

    # MB
    video_file = VideoFile(
        id=1,
        name="test_file",
        filename="test.ts",
        type=VideoFileType.TS,
        size=2621440,  # 2.5MB
    )
    assert video_file.formatted_size == "2.5MB"

    # GB
    video_file = VideoFile(
        id=1,
        name="test_file",
        filename="test.ts",
        type=VideoFileType.TS,
        size=3221225472,  # 3GB
    )
    assert video_file.formatted_size == "3.00GB"


def test_should_handle_zero_size_gracefully_when_empty_file() -> None:
    """ゼロバイトファイルの表示テスト"""
    with pytest.raises(ValidationError):
        video_file = VideoFile(
            id=1, name="empty_file", filename="empty.ts", type=VideoFileType.TS, size=0
        )
        assert video_file.formatted_size == "0B"


def test_should_create_video_file_with_all_required_fields() -> None:
    """VideoFile のインスタンス作成テスト"""
    video_file = VideoFile(
        id=123,
        name="録画テスト番組",
        filename="recording_123.ts",
        type=VideoFileType.TS,
        size=1073741824,  # 1GB
    )

    assert video_file.id == 123
    assert video_file.name == "録画テスト番組"
    assert video_file.filename == "recording_123.ts"
    assert video_file.type == VideoFileType.TS
    assert video_file.size == 1073741824


def test_should_support_different_video_file_types() -> None:
    """異なるビデオファイル種別をサポートすることをテスト"""
    ts_file = VideoFile(id=1, name="TS File", filename="test.ts", type=VideoFileType.TS, size=1000)
    assert ts_file.type == VideoFileType.TS

    encoded_file = VideoFile(
        id=2, name="Encoded File", filename="test.mp4", type=VideoFileType.ENCODED, size=1000
    )
    assert encoded_file.type == VideoFileType.ENCODED


def test_should_validate_required_fields_when_missing() -> None:
    """必須フィールドが不足している場合のバリデーションテスト"""
    with pytest.raises(ValidationError):
        VideoFile(
            id=1,
            name="test",
            filename="test.ts",
            type=VideoFileType.TS,
            size=-1,  # 負のサイズは無効
        )

    with pytest.raises(ValidationError):
        VideoFile(
            id=1,
            name="",  # 空文字は無効
            filename="test.ts",
            type=VideoFileType.TS,
            size=1000,
        )
