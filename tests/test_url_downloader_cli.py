"""Tests for url_downloader CLI command."""

import logging
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from moro.cli.url_downloader import download


class TestUrlDownloaderCLI:
    """Test cases for the url_downloader CLI command.

    This test class verifies the functionality of the url_downloader command-line interface,
    including argument handling, error conditions, and integration with the underlying
    functionality.

    The tests use Click's CliRunner to simulate command-line invocations and mock the actual
    download functionality to isolate the CLI behavior from network operations.
    """

    def setup_method(self) -> None:
        """Set up test fixtures.

        Creates a CliRunner instance for testing Click commands.
        """
        self.runner = CliRunner()

    def _create_test_files(self, temp_dir: str) -> tuple[Path, Path]:
        """Create test files for download command tests.

        Creates a sample input file with a URL and prepares an output directory path.

        Args:
            temp_dir: Temporary directory path

        Returns:
            Tuple containing input file path and output directory path
        """
        input_file = Path(temp_dir) / "urls.txt"
        input_file.write_text("https://example.com/file1.txt\n")

        output_dir = Path(temp_dir) / "output"
        return input_file, output_dir

    def test_download_command_success(self) -> None:
        """Test successful download command execution.

        Verifies that the download command executes successfully with basic options
        and correctly calls the download_from_url_list function with expected parameters.
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test files
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
        """Test download command with all options specified.

        Verifies that the download command executes successfully with all available options
        (timeout, prefix, numbered, verbose) and passes these options correctly to the
        underlying function.
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
        """Test download command with missing input file.

        Verifies that the download command correctly handles the case when the specified
        input file does not exist by returning a non-zero exit code and including
        the file name in the error message.
        """
        result = self.runner.invoke(download, ["--input", "nonexistent.txt", "--output", "output"])

        assert result.exit_code != 0
        assert "nonexistent.txt" in result.output

    def test_download_command_exception_handling(self) -> None:
        """Test download command handles exceptions properly.

        Verifies that the download command correctly handles exceptions thrown by
        the download_from_url_list function by returning a non-zero exit code.
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
        """Test download command with verbose logging enabled.

        Verifies that the download command executes successfully when verbose logging
        is enabled.
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            input_file, output_dir = self._create_test_files(temp_dir)

            with patch("moro.cli.url_downloader.download_from_url_list") as mock_download:
                mock_download.return_value = ["file1.txt"]

                # Test verbose mode
                result = self.runner.invoke(
                    download, ["--input", str(input_file), "--output", str(output_dir), "--verbose"]
                )

                assert result.exit_code == 0

    def test_download_command_logging_setup(self) -> None:
        """Test that logging is properly configured.

        Verifies that the logging system is correctly configured when the verbose flag
        is used, including:
        - Setting the log level to DEBUG
        - Adding a handler if none exists
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            input_file, output_dir = self._create_test_files(temp_dir)

            with patch("moro.cli.url_downloader.download_from_url_list") as mock_download:
                mock_download.return_value = ["file1.txt"]

                # Test that logger is configured
                with patch("logging.getLogger") as mock_get_logger:
                    mock_logger = MagicMock()
                    mock_logger.handlers = []  # No existing handlers
                    mock_get_logger.return_value = mock_logger

                    result = self.runner.invoke(
                        download,
                        ["--input", str(input_file), "--output", str(output_dir), "--verbose"],
                    )

                    assert result.exit_code == 0
                    mock_logger.setLevel.assert_called_with(logging.DEBUG)
                    mock_logger.addHandler.assert_called_once()

    def test_download_command_logging_with_existing_handler(self) -> None:
        """Test logging setup when handler already exists.

        Verifies that the logging system doesn't add a redundant handler when
        a handler already exists.
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            input_file, output_dir = self._create_test_files(temp_dir)

            with patch("moro.cli.url_downloader.download_from_url_list") as mock_download:
                mock_download.return_value = ["file1.txt"]

                # Test with existing handler
                with patch("logging.getLogger") as mock_get_logger:
                    mock_logger = MagicMock()
                    mock_logger.handlers = [MagicMock()]  # Existing handler
                    mock_get_logger.return_value = mock_logger

                    result = self.runner.invoke(
                        download, ["--input", str(input_file), "--output", str(output_dir)]
                    )

                    assert result.exit_code == 0
                    mock_logger.addHandler.assert_not_called()

    def test_download_command_exception_with_verbose(self) -> None:
        """Test exception handling with verbose mode.

        Verifies that when an exception occurs and verbose mode is enabled:
        - The command returns a non-zero exit code
        - The error is logged with exc_info=True for full traceback information
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
