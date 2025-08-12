"""EPGStation CLI タイトルフィルター機能のテスト"""

from unittest.mock import Mock, patch

import pytest
from click.testing import CliRunner

from moro.cli.epgstation import epgstation
from moro.modules.epgstation.domain import (
    RecordingData,
    RegexPatternError,
    VideoFile,
    VideoFileType,
)


class TestEPGStationCLITitleFilter:
    """EPGStation CLI タイトルフィルター機能のテストケース"""

    @pytest.fixture
    def sample_recordings(self) -> list[RecordingData]:
        """テスト用録画データ"""
        return [
            RecordingData(
                id=1,
                name="ニュース7",
                start_at=1700000000000,
                end_at=1700001800000,
                video_files=[
                    VideoFile(
                        id=1,
                        name="ニュース7.ts",
                        filename="news7.ts",
                        type=VideoFileType.TS,
                        size=1024 * 1024 * 100,
                    )
                ],
                is_recording=False,
                is_protected=False,
            ),
            RecordingData(
                id=2,
                name="朝のニュース",
                start_at=1700002000000,
                end_at=1700003800000,
                video_files=[
                    VideoFile(
                        id=2,
                        name="朝のニュース.ts",
                        filename="morning_news.ts",
                        type=VideoFileType.TS,
                        size=1024 * 1024 * 80,
                    )
                ],
                is_recording=False,
                is_protected=False,
            ),
        ]

    @pytest.fixture
    def runner(self) -> CliRunner:
        """Click テストランナー"""
        return CliRunner()

    @patch("moro.cli.epgstation.create_injector")
    @patch("moro.config.settings.ConfigRepository.create")
    @patch("moro.cli.epgstation.config_logging")
    def test_list_with_title_filter(
        self,
        mock_config_logging: Mock,
        mock_config_create: Mock,
        mock_create_injector: Mock,
        runner: CliRunner,
        sample_recordings: list[RecordingData],
    ) -> None:
        """--title オプションのテスト"""
        # モック設定
        mock_config = Mock()
        # config に必要な属性やメソッドを追加
        mock_config.logging = Mock()
        mock_config_create.return_value = mock_config

        mock_injector = Mock()
        mock_create_injector.return_value = mock_injector

        mock_usecase = Mock()
        mock_injector.get.return_value = mock_usecase
        mock_usecase.execute.return_value = sample_recordings

        # コマンド実行
        with runner.isolated_filesystem():
            result = runner.invoke(epgstation, ["list", "--title", "ニュース"])

        # アサーション
        assert result.exit_code == 0
        mock_usecase.execute.assert_called_once_with(
            limit=100, title_filter="ニュース", regex=False
        )

    @patch("moro.cli.epgstation.create_injector")
    @patch("moro.config.settings.ConfigRepository.create")
    @patch("moro.cli.epgstation.config_logging")
    def test_list_with_regex_filter(
        self,
        mock_config_logging: Mock,
        mock_config_create: Mock,
        mock_create_injector: Mock,
        runner: CliRunner,
        sample_recordings: list[RecordingData],
    ) -> None:
        """--regex オプションのテスト"""
        # モック設定
        mock_config = Mock()
        mock_config_create.return_value = mock_config

        mock_injector = Mock()
        mock_create_injector.return_value = mock_injector

        mock_usecase = Mock()
        mock_injector.get.return_value = mock_usecase
        mock_usecase.execute.return_value = sample_recordings[:1]  # ニュース7のみ

        # モック設定
        mock_config.logging = Mock()

        # コマンド実行
        with runner.isolated_filesystem():
            result = runner.invoke(epgstation, ["list", "--title", "^ニュース", "--regex"])

        # アサーション
        assert result.exit_code == 0
        mock_usecase.execute.assert_called_once_with(
            limit=100, title_filter="^ニュース", regex=True
        )
        assert "ニュース7" in result.output

    @patch("moro.cli.epgstation.create_injector")
    @patch("moro.config.settings.ConfigRepository.create")
    @patch("moro.cli.epgstation.config_logging")
    def test_list_with_invalid_regex(
        self,
        mock_config_logging: Mock,
        mock_config_create: Mock,
        mock_create_injector: Mock,
        runner: CliRunner,
    ) -> None:
        """無効正規表現のエラーハンドリングテスト"""
        # モック設定
        mock_config = Mock()
        mock_config_create.return_value = mock_config

        mock_injector = Mock()
        mock_create_injector.return_value = mock_injector

        mock_usecase = Mock()
        mock_injector.get.return_value = mock_usecase
        mock_usecase.execute.side_effect = RegexPatternError("無効な正規表現パターンです")
        mock_config.logging = Mock()

        # コマンド実行
        with runner.isolated_filesystem():
            result = runner.invoke(epgstation, ["list", "--title", "[", "--regex"])

        # アサーション
        assert result.exit_code != 0
        assert "正規表現エラー" in result.output

    @patch("moro.cli.epgstation.create_injector")
    @patch("moro.config.settings.ConfigRepository.create")
    @patch("moro.cli.epgstation.config_logging")
    def test_list_without_filter_options(
        self,
        mock_config_logging: Mock,
        mock_config_create: Mock,
        mock_create_injector: Mock,
        runner: CliRunner,
        sample_recordings: list[RecordingData],
    ) -> None:
        """フィルターオプションなしのテスト（既存機能の継続動作確認）"""
        # モック設定
        mock_config = Mock()
        mock_config_create.return_value = mock_config

        mock_injector = Mock()
        mock_create_injector.return_value = mock_injector

        mock_usecase = Mock()
        mock_injector.get.return_value = mock_usecase
        mock_usecase.execute.return_value = sample_recordings
        mock_config.logging = Mock()

        # コマンド実行
        with runner.isolated_filesystem():
            result = runner.invoke(epgstation, ["list"])

        # アサーション
        assert result.exit_code == 0
        mock_usecase.execute.assert_called_once_with(limit=100, title_filter=None, regex=False)

    @patch("moro.cli.epgstation.create_injector")
    @patch("moro.config.settings.ConfigRepository.create")
    @patch("moro.cli.epgstation.config_logging")
    def test_list_with_filter_and_format_json(
        self,
        mock_config_logging: Mock,
        mock_config_create: Mock,
        mock_create_injector: Mock,
        runner: CliRunner,
        sample_recordings: list[RecordingData],
    ) -> None:
        """フィルターとJSONフォーマットの併用テスト"""
        # モック設定
        mock_config = Mock()
        mock_config_create.return_value = mock_config

        mock_injector = Mock()
        mock_create_injector.return_value = mock_injector

        mock_usecase = Mock()
        mock_injector.get.return_value = mock_usecase
        mock_usecase.execute.return_value = sample_recordings

        # コマンド実行
        with runner.isolated_filesystem():
            result = runner.invoke(epgstation, ["list", "--title", "ニュース", "--format", "json"])

        # アサーション
        assert result.exit_code == 0
        mock_usecase.execute.assert_called_once_with(
            limit=100, title_filter="ニュース", regex=False
        )
        # JSON出力の確認
        assert "ニュース7" in result.output
        assert "朝のニュース" in result.output

    def test_help_shows_new_options(self, runner: CliRunner) -> None:
        """ヘルプメッセージに新オプションが表示されることを確認"""
        result = runner.invoke(epgstation, ["list", "--help"])

        assert result.exit_code == 0
        assert "--title" in result.output
        assert "--regex" in result.output
        assert "番組タイトルでフィルタリング" in result.output
        assert "正規表現モード" in result.output
