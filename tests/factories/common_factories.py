"""共通Factory定義"""

from polyfactory.factories.pydantic_factory import ModelFactory

from moro.modules.common import CommonConfig


class CommonConfigFactory(ModelFactory[CommonConfig]):
    """CommonConfig用Factory - テスト用設定値を生成"""

    __model__ = CommonConfig
    __check_model__ = True

    @classmethod
    def user_data_dir(cls) -> str:
        return "/tmp/test_user_data"  # noqa: S108  # TODO: Replace with tmp_path fixture

    @classmethod
    def user_cache_dir(cls) -> str:
        return "/tmp/test_cache"  # noqa: S108  # TODO: Replace with tmp_path fixture

    @classmethod
    def working_dir(cls) -> str:
        return "/tmp/test_working"  # noqa: S108  # TODO: Replace with tmp_path fixture

    @classmethod
    def jobs(cls) -> int:
        return 2
