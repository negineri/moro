"""settings.pyのテスト"""

from typing import Any

import pytest
from injector import Injector

from moro.config.settings import ConfigRepository
from moro.modules.common import CommonConfig


class TestConfigRepository:
    """ConfigRepositoryのテスト"""

    def test_create_config_repository(self) -> None:
        """ConfigRepositoryのFactoryメソッド"""
        config_repo = ConfigRepository.create()

        assert isinstance(config_repo, ConfigRepository)
        assert config_repo.common.jobs == 16

    def test_config_repository_with_custom_options(self) -> None:
        """ConfigRepositoryのカスタムオプション"""
        options: dict[str, Any] = {"common": {"jobs": 8, "working_dir": "/custom/dir"}}
        config_repo = ConfigRepository.create(options=options)

        assert config_repo.common.jobs == 8
        assert config_repo.common.working_dir == "/custom/dir"

    def test_config_repository_with_invalid_options(self) -> None:
        """ConfigRepositoryの無効なオプション"""
        options: dict[str, Any] = {"common": {"jobs": 0}}
        with pytest.raises(ValueError):
            ConfigRepository.create(options=options)

    def test_config_repository_with_env_vars(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """ConfigRepositoryの環境変数読み込み"""
        monkeypatch.setenv("MORO_COMMON__JOBS", "8")
        monkeypatch.setenv("MORO_COMMON__WORKING_DIR", "/env/dir")

        config_repo = ConfigRepository.create()

        assert config_repo.common.jobs == 8
        assert config_repo.common.working_dir == "/env/dir"
        assert "version" in config_repo.common.logging_config
        assert "handlers" in config_repo.common.logging_config

    def test_create_injector_builder(self) -> None:
        """Injectorビルダーの作成"""
        config_repo = ConfigRepository.create()
        builder = config_repo.create_injector_builder()

        assert callable(builder)

        injector = Injector(builder)
        assert injector.get(ConfigRepository) is config_repo
        assert injector.get(CommonConfig) is config_repo.common
