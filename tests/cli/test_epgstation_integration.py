"""EPGStation CLI統合テスト"""

import json
from unittest.mock import Mock, patch

import pytest
from click.testing import CliRunner

from moro.cli.epgstation import list_recordings
from moro.modules.epgstation.domain import RecordingData, VideoFile, VideoFileType


class TestEPGStationCLIIntegration:
    """EPGStation CLI統合テストクラス"""

    def setup_method(self) -> None:
        """テスト前の準備"""
        self.runner = CliRunner()

    def test_table_format_backward_compatibility(self) -> None:
        """既存CLIコマンドとの出力互換性確認"""
        # Given
        test_recordings = [
            RecordingData(
                id=12345,
                name="互換性テスト番組",
                start_at=1691683200000,
                end_at=1691686800000,
                video_files=[
                    VideoFile(
                        id=1,
                        name="compat.ts",
                        filename="compat.ts",
                        type=VideoFileType.TS,
                        size=1500000000,
                    )
                ],
                is_recording=False,
                is_protected=False,
            )
        ]

        # When
        with patch("moro.cli.epgstation.create_injector") as mock_injector_factory:
            with patch("moro.cli.epgstation.ConfigRepository.create"):
                with patch("moro.cli.epgstation.config_logging"):
                    mock_injector = Mock()
                    mock_injector_factory.return_value = mock_injector
                    mock_use_case = Mock()
                    mock_injector.get.return_value = mock_use_case
                    mock_use_case.execute.return_value = test_recordings

                    result = self.runner.invoke(list_recordings, ["--limit", "10"])

        # Then
        assert result.exit_code == 0
        output = result.output

        # 既存テーブル形式の要素確認
        assert "録画ID" in output
        assert "タイトル" in output
        assert "開始時刻" in output
        assert "ファイル名" in output
        assert "種別" in output
        assert "サイズ" in output
        assert "│" in output  # テーブル区切り
        assert "12345" in output
        assert "互換性テスト番組" in output

    def test_json_format_new_functionality(self) -> None:
        """JSON形式での新機能動作確認"""
        # Given
        test_recordings = [
            RecordingData(
                id=67890,
                name="JSON テスト番組",
                start_at=1691683200000,
                end_at=1691686800000,
                video_files=[
                    VideoFile(
                        id=2,
                        name="json_test.ts",
                        filename="json_test.ts",
                        type=VideoFileType.TS,
                        size=2000000000,
                    )
                ],
                is_recording=True,
                is_protected=True,
            )
        ]

        # When
        with patch("moro.cli.epgstation.create_injector") as mock_injector_factory:
            with patch("moro.cli.epgstation.ConfigRepository.create"):
                with patch("moro.cli.epgstation.config_logging"):
                    mock_injector = Mock()
                    mock_injector_factory.return_value = mock_injector
                    mock_use_case = Mock()
                    mock_injector.get.return_value = mock_use_case
                    mock_use_case.execute.return_value = test_recordings

                    result = self.runner.invoke(
                        list_recordings, ["--format", "json", "--limit", "5"]
                    )

        # Then
        assert result.exit_code == 0

        # JSON形式出力の検証
        parsed = json.loads(result.output)
        assert isinstance(parsed, list)
        assert len(parsed) == 1

        recording = parsed[0]
        assert recording["id"] == 67890
        assert recording["name"] == "JSON テスト番組"
        assert recording["is_recording"] is True
        assert recording["is_protected"] is True
        assert len(recording["video_files"]) == 1

    def test_default_format_is_table(self) -> None:
        """デフォルトフォーマットがTableであることを確認"""
        # Given
        test_recordings = [
            RecordingData(
                id=111,
                name="デフォルトテスト",
                start_at=1691683200000,
                end_at=1691686800000,
                video_files=[],
                is_recording=False,
                is_protected=False,
            )
        ]

        # When（--format オプションなし）
        with patch("moro.cli.epgstation.create_injector") as mock_injector_factory:
            with patch("moro.cli.epgstation.ConfigRepository.create"):
                with patch("moro.cli.epgstation.config_logging"):
                    mock_injector = Mock()
                    mock_injector_factory.return_value = mock_injector
                    mock_use_case = Mock()
                    mock_injector.get.return_value = mock_use_case
                    mock_use_case.execute.return_value = test_recordings

                    result = self.runner.invoke(list_recordings)

        # Then
        assert result.exit_code == 0
        # テーブル形式の確認（JSONではない）
        assert "録画ID" in result.output
        assert "│" in result.output
        # JSON形式ではないことを確認
        with pytest.raises(json.JSONDecodeError):
            json.loads(result.output)

    def test_invalid_format_option(self) -> None:
        """無効なフォーマット指定時のエラーメッセージ確認"""
        # When
        result = self.runner.invoke(list_recordings, ["--format", "xml"])

        # Then
        assert result.exit_code != 0
        assert "Invalid value for '--format'" in result.output
        assert "not one of 'table', 'json'" in result.output

    def test_error_handling_across_layers(self) -> None:
        """レイヤー間エラーハンドリングの統合確認"""
        # Given
        error_message = "Database connection failed"

        # When
        with patch("moro.cli.epgstation.create_injector") as mock_injector_factory:
            with patch("moro.cli.epgstation.ConfigRepository.create"):
                with patch("moro.cli.epgstation.config_logging"):
                    mock_injector = Mock()
                    mock_injector_factory.return_value = mock_injector
                    mock_use_case = Mock()
                    mock_injector.get.return_value = mock_use_case
                    mock_use_case.execute.side_effect = Exception(error_message)

                    result = self.runner.invoke(list_recordings, ["--format", "table"])

        # Then
        assert result.exit_code != 0
        assert error_message in str(result.output)

    def test_empty_recordings_table_format(self) -> None:
        """空の録画リストでのTable形式出力確認"""
        # Given
        empty_recordings: list[RecordingData] = []

        # When
        with patch("moro.cli.epgstation.create_injector") as mock_injector_factory:
            with patch("moro.cli.epgstation.ConfigRepository.create"):
                with patch("moro.cli.epgstation.config_logging"):
                    mock_injector = Mock()
                    mock_injector_factory.return_value = mock_injector
                    mock_use_case = Mock()
                    mock_injector.get.return_value = mock_use_case
                    mock_use_case.execute.return_value = empty_recordings

                    result = self.runner.invoke(list_recordings, ["--format", "table"])

        # Then
        assert result.exit_code == 0
        assert result.output.strip() == "録画データが見つかりませんでした。"

    def test_empty_recordings_json_format(self) -> None:
        """空の録画リストでのJSON形式出力確認"""
        # Given
        empty_recordings: list[RecordingData] = []

        # When
        with patch("moro.cli.epgstation.create_injector") as mock_injector_factory:
            with patch("moro.cli.epgstation.ConfigRepository.create"):
                with patch("moro.cli.epgstation.config_logging"):
                    mock_injector = Mock()
                    mock_injector_factory.return_value = mock_injector
                    mock_use_case = Mock()
                    mock_injector.get.return_value = mock_use_case
                    mock_use_case.execute.return_value = empty_recordings

                    result = self.runner.invoke(list_recordings, ["--format", "json"])

        # Then
        assert result.exit_code == 0
        parsed = json.loads(result.output)
        assert parsed["recordings"] == []
        assert parsed["message"] == "録画データが見つかりませんでした。"

    def test_verbose_option_compatibility(self) -> None:
        """--verbose オプションとの組み合わせ動作確認"""
        # Given
        test_recordings = [
            RecordingData(
                id=999,
                name="Verbose テスト",
                start_at=1691683200000,
                end_at=1691686800000,
                video_files=[],
                is_recording=False,
                is_protected=False,
            )
        ]

        # When
        with patch("moro.cli.epgstation.create_injector") as mock_injector_factory:
            with patch("moro.cli.epgstation.ConfigRepository.create"):
                with patch("moro.cli.epgstation.config_logging") as mock_config_logging:
                    mock_injector = Mock()
                    mock_injector_factory.return_value = mock_injector
                    mock_use_case = Mock()
                    mock_injector.get.return_value = mock_use_case
                    mock_use_case.execute.return_value = test_recordings

                    result = self.runner.invoke(
                        list_recordings, ["--format", "json", "--limit", "20", "--verbose"]
                    )

        # Then
        assert result.exit_code == 0
        # config_logging が verbose オプションと共に呼ばれることを確認
        mock_config_logging.assert_called_once()
        call_args = mock_config_logging.call_args[0]
        verbose_arg = call_args[1]  # 第2引数がverbose
        assert verbose_arg == (True,)

    def test_limit_parameter_forwarding(self) -> None:
        """Limit パラメータの正しい転送確認"""
        # Given
        test_recordings: list[RecordingData] = []

        # When
        with patch("moro.cli.epgstation.create_injector") as mock_injector_factory:
            with patch("moro.cli.epgstation.ConfigRepository.create"):
                with patch("moro.cli.epgstation.config_logging"):
                    mock_injector = Mock()
                    mock_injector_factory.return_value = mock_injector
                    mock_use_case = Mock()
                    mock_injector.get.return_value = mock_use_case
                    mock_use_case.execute.return_value = test_recordings

                    result = self.runner.invoke(
                        list_recordings, ["--limit", "75", "--format", "table"]
                    )

        # Then
        assert result.exit_code == 0
        mock_use_case.execute.assert_called_once_with(limit=75)

    def test_all_format_option_combinations(self) -> None:
        """全フォーマットオプションの組み合わせテスト"""
        test_recordings = [
            RecordingData(
                id=1,
                name="組み合わせテスト",
                start_at=1691683200000,
                end_at=1691686800000,
                video_files=[],
                is_recording=False,
                is_protected=False,
            )
        ]

        format_combinations = [
            (["--format", "table"], "録画ID"),  # Table形式の期待文字列
            (["--format", "json"], '"id": 1'),  # JSON形式の期待文字列
        ]

        for args, expected_content in format_combinations:
            with patch("moro.cli.epgstation.create_injector") as mock_injector_factory:
                with patch("moro.cli.epgstation.ConfigRepository.create"):
                    with patch("moro.cli.epgstation.config_logging"):
                        mock_injector = Mock()
                        mock_injector_factory.return_value = mock_injector
                        mock_use_case = Mock()
                        mock_injector.get.return_value = mock_use_case
                        mock_use_case.execute.return_value = test_recordings

                        result = self.runner.invoke(list_recordings, args)

            assert result.exit_code == 0
            assert expected_content in result.output
