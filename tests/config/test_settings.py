"""settings.pyのテスト"""

import os
from pathlib import Path
from typing import Any

import pytest

from moro.config.settings import create_app_config, load_env_vars


def test_app_config() -> None:
    """AppConfigのテスト"""
    from moro.config.settings import AppConfig

    data: dict[str, Any] = {"jobs": 16}
    config = AppConfig(**data)
    assert config.jobs == 16

    data = {"jobs": "16"}
    config = AppConfig(**data)
    assert config.jobs == 16


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


# 環境変数読み込み機能のテスト - Red Phase (失敗テスト)
class TestCreateAppConfigEnvironmentVariables:
    """create_app_config() 環境変数読み込み機能のテスト"""

    def test_single_env_var_loading(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """HP-1: 単一環境変数の読み込み"""
        # 環境変数を設定
        monkeypatch.setenv("MORO_SETTINGS_JOBS", "8")

        # create_app_config()を呼び出し（実装前なので失敗するはず）
        app_config = create_app_config()

        # 期待結果: AppConfig.jobs が 8 になる
        assert app_config.jobs == 8

    def test_multiple_env_vars_loading(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """HP-2: 複数環境変数の読み込み"""
        # 環境変数を設定
        monkeypatch.setenv("MORO_SETTINGS_JOBS", "4")
        monkeypatch.setenv("MORO_SETTINGS_WORKING_DIR", "/tmp")  # noqa: S108

        # create_app_config()を呼び出し
        app_config = create_app_config()

        # 期待結果: jobs=4, working_dir="/tmp" になる
        assert app_config.jobs == 4
        assert app_config.working_dir == "/tmp"  # noqa: S108

    def test_nested_env_var_loading(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """階層構造の環境変数の読み込み"""
        # 環境変数を設定
        monkeypatch.setenv("MORO_SETTINGS_FANTIA__DOWNLOAD_THUMB", "true")
        monkeypatch.setenv("MORO_SETTINGS_TEMP__HOGEHOGE__EXAMPLE__TEST", "false")

        # create_app_config()を呼び出し
        app_config = create_app_config()

        # 期待結果: fantia.download_thumb=True になる
        assert app_config.fantia.download_thumb is True
        data = load_env_vars()
        assert data["settings"]["temp"]["hogehoge"]["example"]["test"] == "false"

    def test_string_type_env_var_loading(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """HP-3: 文字列型設定値の読み込み"""
        # 環境変数を設定
        monkeypatch.setenv("MORO_SETTINGS_USER_DATA_DIR", "/custom/data")

        # create_app_config()を呼び出し
        app_config = create_app_config()

        # 期待結果: user_data_dir="/custom/data" になる
        assert app_config.user_data_dir == "/custom/data"

    def test_numeric_env_var_as_string(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """HP-4: 数値型設定値の読み込み（文字列として）"""
        # 環境変数を設定
        monkeypatch.setenv("MORO_SETTINGS_JOBS", "32")

        # create_app_config()を呼び出し
        app_config = create_app_config()

        # 期待結果: Pydanticが "32" を 32 (int型) に変換
        assert app_config.jobs == 32
        assert isinstance(app_config.jobs, int)

    def test_invalid_numeric_value(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """EC-1: 無効な数値の処理"""
        # 環境変数を設定
        monkeypatch.setenv("MORO_SETTINGS_JOBS", "invalid")

        # create_app_config()を呼び出し、Pydantic ValidationErrorが発生するはず
        with pytest.raises(ValueError):  # Pydantic ValidationErrorがValueErrorとして伝播
            create_app_config()

    def test_unknown_field_ignored(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """EC-2: 存在しないフィールドの処理"""
        # 環境変数を設定
        monkeypatch.setenv("MORO_SETTINGS_UNKNOWN_FIELD", "value")

        # create_app_config()を呼び出し
        app_config = create_app_config()

        # 期待結果: エラーが発生せず、デフォルト値が使用される
        assert app_config.jobs == 16  # デフォルト値

    def test_no_env_vars_uses_defaults(self) -> None:
        """ED-1: 環境変数が設定されていない場合"""
        # MORO_SETTINGS_* 環境変数を明示的にクリア
        for key in list(os.environ.keys()):
            if key.startswith("MORO_SETTINGS_"):
                del os.environ[key]

        # create_app_config()を呼び出し
        app_config = create_app_config()

        # 期待結果: デフォルト値が使用される
        assert app_config.jobs == 16

    def test_empty_string_env_var(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """ED-2: 空文字列の環境変数"""
        # 環境変数を設定
        monkeypatch.setenv("MORO_SETTINGS_WORKING_DIR", "")

        # create_app_config()を呼び出し
        app_config = create_app_config()

        # 期待結果: 空文字列が設定値として使用される
        assert app_config.working_dir == ""

    def test_config_file_vs_env_var_priority(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """ED-3: 設定ファイルと環境変数の優先度"""
        # 設定ファイルを作成
        text = """
[settings]
jobs = 16
"""
        tmp_path.mkdir(exist_ok=True)
        file = tmp_path / "settings.toml"
        file.write_text(text)

        # 環境変数を設定
        monkeypatch.setenv("MORO_SETTINGS_JOBS", "8")

        # create_app_config()を呼び出し
        app_config = create_app_config(paths=[str(file)])

        # 期待結果: 環境変数が優先され jobs=8 になる
        assert app_config.jobs == 8

    def test_env_var_vs_options_priority(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """ED-4: 環境変数とoptions引数の優先度"""
        # 環境変数を設定
        monkeypatch.setenv("MORO_SETTINGS_JOBS", "8")

        # create_app_config()を呼び出し
        app_config = create_app_config(options={"settings": {"jobs": 4}})

        # 期待結果: options引数が優先され jobs=4 になる
        assert app_config.jobs == 4
