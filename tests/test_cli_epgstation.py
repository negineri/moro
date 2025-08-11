"""EPGStation CLI コマンドのテスト

TDD Red Phase: CLIコマンドテスト作成
"""

from unittest.mock import Mock, patch

from click.testing import CliRunner

from moro.cli.epgstation import epgstation
from moro.modules.epgstation.domain import RecordingData


class TestEPGStationCLI:
    """EPGStation CLI コマンドのテスト"""

    def test_should_execute_list_command_successfully_when_valid_options(self) -> None:
        """Moro epgstation list コマンドの正常動作テスト"""
        runner = CliRunner()

        # ユースケースのモック
        mock_usecase = Mock()
        test_recordings = [
            RecordingData(
                id=123,
                name="テスト番組",
                start_at=1691683200000,
                end_at=1691686800000,
                video_files=[],
                is_recording=False,
                is_protected=False,
            )
        ]
        mock_usecase.execute.return_value = test_recordings

        # Injector のモック
        mock_injector = Mock()
        mock_injector.get.return_value = mock_usecase

        with patch("moro.cli.epgstation.create_injector", return_value=mock_injector):
            result = runner.invoke(epgstation, ["list", "--limit", "50"])

        # アサーション
        assert result.exit_code == 0
        assert "録画ID" in result.output  # テーブルヘッダー
        assert "テスト番組" in result.output  # データ内容
        mock_usecase.execute.assert_called_once_with(limit=50)

    def test_should_use_default_limit_when_no_option_provided(self) -> None:
        """オプションなしの場合にデフォルトlimitが使用されることをテスト"""
        runner = CliRunner()

        mock_usecase = Mock()
        test_recordings = [
            RecordingData(
                id=456,
                name="デフォルトテスト",
                start_at=1691683200000,
                end_at=1691686800000,
                video_files=[],
                is_recording=False,
                is_protected=False,
            )
        ]
        mock_usecase.execute.return_value = test_recordings

        mock_injector = Mock()
        mock_injector.get.return_value = mock_usecase

        with patch("moro.cli.epgstation.create_injector", return_value=mock_injector):
            result = runner.invoke(epgstation, ["list"])

        assert result.exit_code == 0
        assert "録画ID" in result.output  # テーブルヘッダー
        assert "デフォルトテスト" in result.output  # データ内容
        mock_usecase.execute.assert_called_once_with(limit=100)  # デフォルト値

    def test_should_handle_usecase_exception_gracefully(self) -> None:
        """ユースケース実行時の例外の適切な処理テスト"""
        runner = CliRunner()

        mock_usecase = Mock()
        mock_usecase.execute.side_effect = RuntimeError("認証エラー")

        mock_injector = Mock()
        mock_injector.get.return_value = mock_usecase

        with patch("moro.cli.epgstation.create_injector", return_value=mock_injector):
            result = runner.invoke(epgstation, ["list"])

        # 例外が適切に処理されることを確認
        assert result.exit_code == 1  # ClickException による終了コード
        assert "認証エラー" in result.output

    def test_should_handle_injector_creation_failure(self) -> None:
        """Injector 作成失敗時の例外処理テスト"""
        runner = CliRunner()

        with patch("moro.cli.epgstation.create_injector", side_effect=Exception("DI設定エラー")):
            result = runner.invoke(epgstation, ["list"])

        assert result.exit_code == 1
        assert "DI設定エラー" in result.output

    def test_should_accept_various_limit_values(self) -> None:
        """様々なlimit値の受け入れテスト"""
        runner = CliRunner()

        mock_usecase = Mock()
        test_recordings = [
            RecordingData(
                id=789,
                name="リミットテスト",
                start_at=1691683200000,
                end_at=1691686800000,
                video_files=[],
                is_recording=False,
                is_protected=False,
            )
        ]
        mock_usecase.execute.return_value = test_recordings

        mock_injector = Mock()
        mock_injector.get.return_value = mock_usecase

        test_limits = [1, 10, 100, 1000]

        for limit in test_limits:
            with patch("moro.cli.epgstation.create_injector", return_value=mock_injector):
                result = runner.invoke(epgstation, ["list", "--limit", str(limit)])

            assert result.exit_code == 0
            assert "録画ID" in result.output  # テーブルヘッダー
            mock_usecase.execute.assert_called_with(limit=limit)

    def test_should_show_help_message_when_help_requested(self) -> None:
        """ヘルプメッセージの表示テスト"""
        runner = CliRunner()

        # epgstation グループのヘルプ
        result = runner.invoke(epgstation, ["--help"])
        assert result.exit_code == 0
        assert "EPGStation 録画管理コマンド" in result.output

        # list サブコマンドのヘルプ
        result = runner.invoke(epgstation, ["list", "--help"])
        assert result.exit_code == 0
        assert "録画一覧を表示" in result.output
        assert "--limit" in result.output

    def test_should_handle_keyboard_interrupt_gracefully(self) -> None:
        """キーボード割り込みの適切な処理テスト"""
        runner = CliRunner()

        mock_usecase = Mock()
        mock_usecase.execute.side_effect = KeyboardInterrupt()

        mock_injector = Mock()
        mock_injector.get.return_value = mock_usecase

        with patch("moro.cli.epgstation.create_injector", return_value=mock_injector):
            result = runner.invoke(epgstation, ["list"])

        # キーボード割り込みが適切に処理されることを確認
        assert result.exit_code == 1
        # Click は KeyboardInterrupt を "Aborted!" として表示する
        assert "Aborted!" in result.output or "エラー:" in result.output

    def test_should_display_usecase_result_directly(self) -> None:
        """ユースケース結果の直接表示テスト"""
        runner = CliRunner()

        test_recordings = [
            RecordingData(
                id=123,
                name="テスト番組",
                start_at=1641020400000,  # 2022-01-01 00:00 JST
                end_at=1641024000000,
                video_files=[],
                is_recording=False,
                is_protected=False,
            )
        ]

        mock_usecase = Mock()
        mock_usecase.execute.return_value = test_recordings

        mock_injector = Mock()
        mock_injector.get.return_value = mock_usecase

        with patch("moro.cli.epgstation.create_injector", return_value=mock_injector):
            result = runner.invoke(epgstation, ["list"])

        assert result.exit_code == 0
        assert "録画ID" in result.output  # テーブルヘッダー
        assert "テスト番組" in result.output  # データ内容
        assert "123" in result.output  # 録画ID

    def test_should_pass_correct_parameters_to_usecase(self) -> None:
        """ユースケースに正しいパラメータが渡されることをテスト"""
        runner = CliRunner()

        mock_usecase = Mock()
        test_recordings = [
            RecordingData(
                id=250,
                name="パラメータテスト",
                start_at=1691683200000,
                end_at=1691686800000,
                video_files=[],
                is_recording=False,
                is_protected=False,
            )
        ]
        mock_usecase.execute.return_value = test_recordings

        mock_injector = Mock()
        mock_injector.get.return_value = mock_usecase

        with patch("moro.cli.epgstation.create_injector", return_value=mock_injector):
            result = runner.invoke(epgstation, ["list", "--limit", "250"])

        # パラメータが正確に渡されることを確認
        assert result.exit_code == 0
        mock_usecase.execute.assert_called_once_with(limit=250)

        # Injector から正しいクラスが取得されることを確認
        from moro.modules.epgstation.usecases import ListRecordingsUseCase

        mock_injector.get.assert_called_once_with(ListRecordingsUseCase)


class TestEPGStationCommandGroup:
    """EPGStation コマンドグループのテスト"""

    def test_should_provide_epgstation_command_group(self) -> None:
        """Epgstation コマンドグループが提供されることをテスト"""
        runner = CliRunner()
        result = runner.invoke(epgstation, ["--help"])

        # ヘルプが適切に表示されることを確認
        assert result.exit_code == 0
        assert "Commands:" in result.output or "Usage:" in result.output

    def test_should_list_available_subcommands(self) -> None:
        """利用可能なサブコマンドの一覧表示テスト"""
        runner = CliRunner()
        result = runner.invoke(epgstation, ["--help"])

        assert result.exit_code == 0
        assert "list" in result.output

    def test_should_handle_unknown_subcommand(self) -> None:
        """不明なサブコマンドの処理テスト"""
        runner = CliRunner()
        result = runner.invoke(epgstation, ["unknown-command"])

        assert result.exit_code != 0
        assert "No such command" in result.output or "Usage:" in result.output


class TestIntegrationWithMainCLI:
    """メインCLIとの統合テスト"""

    def test_should_be_importable_from_main_cli(self) -> None:
        """メインCLIからインポート可能であることをテスト"""
        # モジュールがインポート可能であることを確認
        from moro.cli.epgstation import epgstation

        assert epgstation is not None

    def test_should_have_correct_command_structure(self) -> None:
        """コマンド構造の正確性テスト"""
        runner = CliRunner()

        # epgstation グループの存在確認
        result = runner.invoke(epgstation, ["--help"])
        assert result.exit_code == 0

        # list サブコマンドの存在確認
        result = runner.invoke(epgstation, ["list", "--help"])
        assert result.exit_code == 0
