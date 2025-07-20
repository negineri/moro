"""settings.pyのテスト"""

from pathlib import Path

import pytest

from moro.config.settings import create_app_config


def test_app_config_factory_method(tmp_path: Path) -> None:
    """AppConfigのFactoryメソッド"""
    text = """
[settings]
jobs = 4
"""

    tmp_path.mkdir(exist_ok=True)
    file = tmp_path / "settings.toml"
    file.write_text(text)

    app_config = create_app_config()
    assert app_config.jobs == 16

    app_config = create_app_config(paths=[str(file)])
    assert app_config.jobs == 4

    app_config = create_app_config(options={"settings": {"jobs": 1}}, paths=[str(file)])
    assert app_config.jobs == 1

    with pytest.raises(ValueError):
        app_config = create_app_config(options={"settings": {"jobs": 0}})


def test_load_config_files(tmp_path: Path) -> None:
    """設定ファイルの読み込み"""
    from moro.config.settings import load_config_files

    text = """
[settings]
jobs = 4
"""

    tmp_path.mkdir(exist_ok=True)
    file = tmp_path / "settings.toml"
    file.write_text(text)

    config = load_config_files(paths=[str(file)])
    assert isinstance(config, dict)
    assert config["settings"]["jobs"] == 4
