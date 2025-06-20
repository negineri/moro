"""Tests for url_downloader CLI command."""

import logging
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from moro.cli.url_downloader import download


class TestUrlDownloaderCLI:
    """Test cases for the url_downloader CLI command."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    def test_download_command_success(self):
        """Test successful download command execution."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test input file
            input_file = Path(temp_dir) / "urls.txt"
            input_file.write_text("https://example.com/file1.txt\n")

            output_dir = Path(temp_dir) / "output"

            with patch('moro.cli.url_downloader.download_from_url_list') as mock_download:
                mock_download.return_value = ["file1.txt"]

                result = self.runner.invoke(download, [
                    '--input', str(input_file),
                    '--output', str(output_dir)
                ])

                assert result.exit_code == 0
                mock_download.assert_called_once_with(
                    str(input_file),
                    str(output_dir),
                    timeout=10.0,
                    prefix=None,
                    auto_prefix=False
                )

    def test_download_command_with_all_options(self):
        """Test download command with all options specified."""
        with tempfile.TemporaryDirectory() as temp_dir:
            input_file = Path(temp_dir) / "urls.txt"
            input_file.write_text("https://example.com/file1.txt\n")

            output_dir = Path(temp_dir) / "output.zip"

            with patch('moro.cli.url_downloader.download_from_url_list') as mock_download:
                mock_download.return_value = ["file1.txt", "file2.txt"]

                result = self.runner.invoke(download, [
                    '--input', str(input_file),
                    '--output', str(output_dir),
                    '--timeout', '30.0',
                    '--prefix', 'test',
                    '--numbered',
                    '--verbose'
                ])

                assert result.exit_code == 0
                mock_download.assert_called_once_with(
                    str(input_file),
                    str(output_dir),
                    timeout=30.0,
                    prefix='test',
                    auto_prefix=True
                )

    def test_download_command_missing_input_file(self):
        """Test download command with missing input file."""
        result = self.runner.invoke(download, [
            '--input', 'nonexistent.txt',
            '--output', 'output'
        ])

        assert result.exit_code != 0
        assert "nonexistent.txt" in result.output

    def test_download_command_exception_handling(self):
        """Test download command handles exceptions properly."""
        with tempfile.TemporaryDirectory() as temp_dir:
            input_file = Path(temp_dir) / "urls.txt"
            input_file.write_text("https://example.com/file1.txt\n")

            output_dir = Path(temp_dir) / "output"

            with patch('moro.cli.url_downloader.download_from_url_list') as mock_download:
                mock_download.side_effect = Exception("Download failed")

                result = self.runner.invoke(download, [
                    '--input', str(input_file),
                    '--output', str(output_dir)
                ])

                assert result.exit_code != 0

    def test_download_command_verbose_logging(self):
        """Test download command with verbose logging enabled."""
        with tempfile.TemporaryDirectory() as temp_dir:
            input_file = Path(temp_dir) / "urls.txt"
            input_file.write_text("https://example.com/file1.txt\n")

            output_dir = Path(temp_dir) / "output"

            with patch('moro.cli.url_downloader.download_from_url_list') as mock_download:
                mock_download.return_value = ["file1.txt"]

                # Test verbose mode
                result = self.runner.invoke(download, [
                    '--input', str(input_file),
                    '--output', str(output_dir),
                    '--verbose'
                ])

                assert result.exit_code == 0

    def test_download_command_logging_setup(self):
        """Test that logging is properly configured."""
        with tempfile.TemporaryDirectory() as temp_dir:
            input_file = Path(temp_dir) / "urls.txt"
            input_file.write_text("https://example.com/file1.txt\n")

            output_dir = Path(temp_dir) / "output"

            with patch('moro.cli.url_downloader.download_from_url_list') as mock_download:
                mock_download.return_value = ["file1.txt"]

                # Test that logger is configured
                with patch('logging.getLogger') as mock_get_logger:
                    mock_logger = MagicMock()
                    mock_logger.handlers = []  # No existing handlers
                    mock_get_logger.return_value = mock_logger

                    result = self.runner.invoke(download, [
                        '--input', str(input_file),
                        '--output', str(output_dir),
                        '--verbose'
                    ])

                    assert result.exit_code == 0
                    mock_logger.setLevel.assert_called_with(logging.DEBUG)
                    mock_logger.addHandler.assert_called_once()

    def test_download_command_logging_with_existing_handler(self):
        """Test logging setup when handler already exists."""
        with tempfile.TemporaryDirectory() as temp_dir:
            input_file = Path(temp_dir) / "urls.txt"
            input_file.write_text("https://example.com/file1.txt\n")

            output_dir = Path(temp_dir) / "output"

            with patch('moro.cli.url_downloader.download_from_url_list') as mock_download:
                mock_download.return_value = ["file1.txt"]

                # Test with existing handler
                with patch('logging.getLogger') as mock_get_logger:
                    mock_logger = MagicMock()
                    mock_logger.handlers = [MagicMock()]  # Existing handler
                    mock_get_logger.return_value = mock_logger

                    result = self.runner.invoke(download, [
                        '--input', str(input_file),
                        '--output', str(output_dir)
                    ])

                    assert result.exit_code == 0
                    mock_logger.addHandler.assert_not_called()

    def test_download_command_exception_with_verbose(self):
        """Test exception handling with verbose mode."""
        with tempfile.TemporaryDirectory() as temp_dir:
            input_file = Path(temp_dir) / "urls.txt"
            input_file.write_text("https://example.com/file1.txt\n")

            output_dir = Path(temp_dir) / "output"

            with patch('moro.cli.url_downloader.download_from_url_list') as mock_download:
                mock_download.side_effect = Exception("Download failed")

                with patch('logging.getLogger') as mock_get_logger:
                    mock_logger = MagicMock()
                    mock_logger.handlers = []
                    mock_get_logger.return_value = mock_logger

                    result = self.runner.invoke(download, [
                        '--input', str(input_file),
                        '--output', str(output_dir),
                        '--verbose'
                    ])

                    assert result.exit_code != 0
                    # Verify that error is logged with exc_info=True when verbose
                    mock_logger.error.assert_called_once()
                    args, kwargs = mock_logger.error.call_args
                    assert kwargs.get('exc_info') is True
