"""url_downloader CLIコマンドのテスト。"""

import logging
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from moro.cli.url_downloader import download


class TestUrlDownloaderCLI:
    """url_downloader CLIコマンドのテストケース。

    このテストクラスは、url_downloaderコマンドラインインターフェースの機能（引数処理、エラー条件、基盤機能との統合）を検証します。

    テストではClickのCliRunnerを使ってコマンドライン呼び出しをシミュレートし、実際のダウンロード機能をモックしてCLIの挙動をネットワーク処理から分離します。
    """

    def setup_method(self) -> None:
        """テスト用フィクスチャのセットアップ。

        Clickコマンドのテスト用にCliRunnerインスタンスを作成します。
        """
        self.runner = CliRunner()

    def _create_test_files(self, temp_dir: str) -> tuple[Path, Path]:
        """ダウンロードコマンドテスト用のテストファイルを作成。

        サンプルの入力ファイル（URL入り）を作成し、出力ディレクトリのパスを用意します。

        引数:
            temp_dir: 一時ディレクトリのパス

        戻り値:
            入力ファイルパスと出力ディレクトリパスのタプル
        """
        input_file = Path(temp_dir) / "urls.txt"
        input_file.write_text("https://example.com/file1.txt\n")

        output_dir = Path(temp_dir) / "output"
        return input_file, output_dir

    def test_download_command_success(self) -> None:
        """ダウンロードコマンドの正常実行テスト。

        downloadコマンドが基本オプションで正常に実行され、download_from_url_list関数が期待通りのパラメータで呼ばれることを検証します。
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            # テストファイルの作成
            input_file, output_dir = self._create_test_files(temp_dir)

            with patch("moro.cli.url_downloader.download_from_url_list") as mock_download:
                mock_download.return_value = ["file1.txt"]

                result = self.runner.invoke(
                    download, ["--input", str(input_file), "--output", str(output_dir)]
                )

                assert result.exit_code == 0
                mock_download.assert_called_once_with(
                    str(input_file), str(output_dir), timeout=10.0, prefix=None, auto_prefix=False
                )

    def test_download_command_with_all_options(self) -> None:
        """すべてのオプションを指定したダウンロードコマンドのテスト。

        タイムアウト、プレフィックス、番号付き、詳細表示など、利用可能なすべてのオプションでdownloadコマンドが正常に実行され、
        これらのオプションが基盤となる関数に正しく渡されることを検証します。
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            input_file, _ = self._create_test_files(temp_dir)
            output_dir = Path(temp_dir) / "output.zip"

            with patch("moro.cli.url_downloader.download_from_url_list") as mock_download:
                mock_download.return_value = ["file1.txt", "file2.txt"]

                result = self.runner.invoke(
                    download,
                    [
                        "--input",
                        str(input_file),
                        "--output",
                        str(output_dir),
                        "--timeout",
                        "30.0",
                        "--prefix",
                        "test",
                        "--numbered",
                        "--verbose",
                    ],
                )

                assert result.exit_code == 0
                mock_download.assert_called_once_with(
                    str(input_file), str(output_dir), timeout=30.0, prefix="test", auto_prefix=True
                )

    def test_download_command_missing_input_file(self) -> None:
        """入力ファイルがない場合のダウンロードコマンドのテスト。

        指定された入力ファイルが存在しない場合に、downloadコマンドがどのように処理するかを検証します。
        非ゼロの終了コードを返し、エラーメッセージにファイル名が含まれることを確認します。
        """
        result = self.runner.invoke(download, ["--input", "nonexistent.txt", "--output", "output"])

        assert result.exit_code != 0
        assert "nonexistent.txt" in result.output

    def test_download_command_exception_handling(self) -> None:
        """例外処理のテスト。

        download_from_url_list関数によってスローされた例外をdownloadコマンドが適切に処理し、
        非ゼロの終了コードを返すことを検証します。
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            input_file, output_dir = self._create_test_files(temp_dir)

            with patch("moro.cli.url_downloader.download_from_url_list") as mock_download:
                mock_download.side_effect = Exception("Download failed")

                result = self.runner.invoke(
                    download, ["--input", str(input_file), "--output", str(output_dir)]
                )

                assert result.exit_code != 0

    def test_download_command_verbose_logging(self) -> None:
        """詳細ログ出力が有効な場合のダウンロードコマンドのテスト。

        詳細ログ出力が有効な状態でdownloadコマンドが正常に実行されることを検証します。
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            input_file, output_dir = self._create_test_files(temp_dir)

            with patch("moro.cli.url_downloader.download_from_url_list") as mock_download:
                mock_download.return_value = ["file1.txt"]

                # 詳細モードのテスト
                result = self.runner.invoke(
                    download, ["--input", str(input_file), "--output", str(output_dir), "--verbose"]
                )

                assert result.exit_code == 0

    def test_logging_setup_configuration(self) -> None:
        """ロギングの設定が正しいことをテスト。

        詳細フラグが使用されるときに、ロギングシステムが正しく設定されることを検証します。
        - ログレベルがDEBUGに設定される
        - ハンドラが存在しない場合は追加される
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            input_file, output_dir = self._create_test_files(temp_dir)

            with patch("moro.cli.url_downloader.download_from_url_list") as mock_download:
                mock_download.return_value = ["file1.txt"]

                # ロガーが設定されていることをテスト
                with patch("logging.getLogger") as mock_get_logger:
                    mock_logger = MagicMock()
                    mock_logger.handlers = []  # 既存のハンドラはなし
                    mock_get_logger.return_value = mock_logger

                    result = self.runner.invoke(
                        download,
                        ["--input", str(input_file), "--output", str(output_dir), "--verbose"],
                    )

                    assert result.exit_code == 0
                    mock_logger.setLevel.assert_called_with(logging.DEBUG)
                    mock_logger.addHandler.assert_called_once()

    def test_logging_with_existing_handler(self) -> None:
        """既存のハンドラがある場合のロギング設定のテスト。

        ロギングシステムが既にハンドラを持っているときに冗長なハンドラを追加しないことを検証します。
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            input_file, output_dir = self._create_test_files(temp_dir)

            with patch("moro.cli.url_downloader.download_from_url_list") as mock_download:
                mock_download.return_value = ["file1.txt"]

                # 既存のハンドラがある状態でテスト
                with patch("logging.getLogger") as mock_get_logger:
                    mock_logger = MagicMock()
                    mock_logger.handlers = [MagicMock()]  # 既存のハンドラ
                    mock_get_logger.return_value = mock_logger

                    result = self.runner.invoke(
                        download, ["--input", str(input_file), "--output", str(output_dir)]
                    )

                    assert result.exit_code == 0
                    mock_logger.addHandler.assert_not_called()

    def test_exception_with_verbose_mode(self) -> None:
        """詳細モードでの例外処理のテスト。

        例外が発生し、詳細モードが有効な場合に次のことを検証します。
        - コマンドが非ゼロの終了コードを返す
        - エラーがexc_info=Trueでログに記録され、完全なトレースバック情報が得られる
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            input_file, output_dir = self._create_test_files(temp_dir)

            with patch("moro.cli.url_downloader.download_from_url_list") as mock_download:
                mock_download.side_effect = Exception("Download failed")

                with patch("logging.getLogger") as mock_get_logger:
                    mock_logger = MagicMock()
                    mock_logger.handlers = []
                    mock_get_logger.return_value = mock_logger

                    result = self.runner.invoke(
                        download,
                        ["--input", str(input_file), "--output", str(output_dir), "--verbose"],
                    )

                    assert result.exit_code != 0
                    # Verify that error is logged with exc_info=True when verbose
                    mock_logger.error.assert_called_once()
                    args, kwargs = mock_logger.error.call_args
                    assert kwargs.get("exc_info") is True
                    # Verify the error message contains the exception info
                    assert "Download failed" in str(args[0]) or "Exception" in str(args[0])
                    # Verify logger level was set to DEBUG in verbose mode
                    mock_logger.setLevel.assert_called_with(logging.DEBUG)
