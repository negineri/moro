"""EPGStation モジュールのインポートテスト

TDD Red Phase: モジュールが存在せず失敗することを確認
"""


def test_should_import_epgstation_config_when_module_exists() -> None:
    """EPGStationConfig がインポート可能であることをテスト"""
    from moro.modules.epgstation.config import EPGStationConfig  # noqa: F401


def test_should_import_epgstation_domain_when_module_exists() -> None:
    """EPGStation ドメインクラスがインポート可能であることをテスト"""
    from moro.modules.epgstation.domain import RecordingData, VideoFile  # noqa: F401


def test_should_import_epgstation_infrastructure_when_module_exists() -> None:
    """EPGStation インフラクラスがインポート可能であることをテスト"""
    from moro.modules.epgstation.infrastructure import (  # noqa: F401
        EPGStationRecordingRepository,
        SeleniumEPGStationSessionProvider,
    )


def test_should_import_epgstation_usecases_when_module_exists() -> None:
    """EPGStation ユースケースがインポート可能であることをテスト"""
    from moro.modules.epgstation.usecases import ListRecordingsUseCase  # noqa: F401


def test_should_import_epgstation_module_when_public_interface_exists() -> None:
    """EPGStation モジュールの公開インターフェースがインポート可能であることをテスト"""
    from moro.modules.epgstation import (  # noqa: F401
        EPGStationConfig,
        ListRecordingsUseCase,
        RecordingData,
        VideoFile,
    )
