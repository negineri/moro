"""Test suite for the tracklist module."""

from pathlib import Path
from unittest.mock import Mock, patch

import httpx
from click.testing import CliRunner

from moro.cli.cli import cli
from moro.modules.tracklist_extractor import Track, extract_tracks, save_tracks_to_csv


class TestTracklistExtractor:
    """Test class for tracklist extractor functions."""

    def test_extract_tracks_empty_html(self) -> None:
        """Test extract_tracks with empty HTML."""
        tracks = extract_tracks("", "example.com")
        assert tracks == []

    def test_extract_tracks_no_table(self) -> None:
        """Test extract_tracks with HTML that has no table."""
        html = "<html><body><p>No table here</p></body></html>"
        tracks = extract_tracks(html, "example.com")
        assert tracks == []

    def test_save_to_csv(self, tmp_path: Path) -> None:
        """Test save_to_csv functionality."""
        tracks = [
            Track(
                disc=1,
                track=1,
                title="Song 1",
                duration="3:45",
                track_url="http://example.com/song1.flac",
            ),
            Track(
                disc=1,
                track=2,
                title="Song 2",
                duration="4:12",
                track_url="http://example.com/song2.flac",
            ),
        ]

        output_file = tmp_path / "test_tracklist.csv"
        save_tracks_to_csv(tracks, output_file)

        # Check if file was created and has correct content
        assert output_file.exists()
        content = output_file.read_text(encoding="utf-8")

        assert "Disc,Track,Title,Duration,Track URL" in content
        assert "1,1,Song 1,3:45,http://example.com/song1.flac" in content
        assert "1,2,Song 2,4:12,http://example.com/song2.flac" in content


class TestTracklistCommand:
    """Test class for tracklist CLI command."""

    @patch("moro.cli.tracklist.extract_tracklist_from_url_to_csv")
    def test_tracklist_command_success(self, mock_extract: Mock, tmp_path: Path) -> None:
        """Test tracklist command with successful extraction."""
        # Mock successful extraction returning 1 track
        mock_extract.return_value = 1

        runner = CliRunner()
        output_file = tmp_path / "test_output.csv"

        result = runner.invoke(
            cli, ["tracklist", "http://example.com/tracklist", "-o", str(output_file)]
        )

        assert result.exit_code == 0
        assert "1曲の曲目リストを" in result.output
        assert "保存しました" in result.output
        mock_extract.assert_called_once()

    @patch("moro.cli.tracklist.extract_tracklist_from_url_to_csv")
    def test_tracklist_command_http_error(self, mock_extract: Mock) -> None:
        """Test tracklist command with HTTP error."""
        # Mock extraction that raises HTTPError
        mock_extract.side_effect = httpx.HTTPError("Connection failed")

        runner = CliRunner()
        result = runner.invoke(cli, ["tracklist", "http://example.com/invalid"])

        assert result.exit_code != 0
        assert "エラーが発生しました" in result.output

    @patch("moro.cli.tracklist.extract_tracklist_from_url_to_csv")
    def test_tracklist_command_default_output(self, mock_extract: Mock, tmp_path: Path) -> None:
        """Test tracklist command with default output filename."""
        # Mock successful extraction
        mock_extract.return_value = 0

        runner = CliRunner()

        # Change to temp directory to avoid creating files in project root
        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(cli, ["tracklist", "http://example.com/tracklist"])

            assert result.exit_code == 0
            assert "tracklist.csv" in result.output
