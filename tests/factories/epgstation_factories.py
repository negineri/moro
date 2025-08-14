"""EPGStationモジュール専用Factory - type hints完全対応"""

from polyfactory.factories.pydantic_factory import ModelFactory

from moro.modules.epgstation.domain import RecordingData, VideoFile, VideoFileType


class VideoFileFactory(ModelFactory[VideoFile]):
    """VideoFile用Factory"""

    __model__ = VideoFile
    __check_model__ = True

    @classmethod
    def id(cls) -> int:
        return 1

    @classmethod
    def name(cls) -> str:
        return "test_video.ts"

    @classmethod
    def filename(cls) -> str:
        return "test_recording_20240101_1230.ts"

    @classmethod
    def size(cls) -> int:
        return 1000000000  # 1GB

    @classmethod
    def type(cls) -> VideoFileType:
        return VideoFileType.TS


class RecordingDataFactory(ModelFactory[RecordingData]):
    """RecordingData用Factory"""

    __model__ = RecordingData
    __check_model__ = True

    @classmethod
    def id(cls) -> int:
        return 1

    @classmethod
    def name(cls) -> str:
        return "テスト録画番組"

    @classmethod
    def start_at(cls) -> int:
        return 1704105000000  # 2024-01-01 12:30

    @classmethod
    def end_at(cls) -> int:
        return 1704106800000  # 2024-01-01 13:00 (30分後)

    @classmethod
    def video_files(cls) -> list[VideoFile]:
        return [VideoFileFactory.build()]

    @classmethod
    def is_recording(cls) -> bool:
        return False

    @classmethod
    def is_protected(cls) -> bool:
        return False
