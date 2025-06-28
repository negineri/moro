"""Test suite for the tracklist module."""

from pathlib import Path
from unittest.mock import Mock, patch

import httpx
from click.testing import CliRunner

from moro.cli.cli import cli
from moro.modules.tracklist_extractor import Track, TracklistExtractor


class TestTracklistExtractor:
    """Test class for TracklistExtractor."""

    def test_extract_tracks_empty_html(self) -> None:
        """Test extract_tracks with empty HTML."""
        extractor = TracklistExtractor("")
        tracks = extractor.extract_tracks()
        assert tracks == []

    def test_extract_tracks_no_table(self) -> None:
        """Test extract_tracks with HTML that has no table."""
        html = "<html><body><p>No table here</p></body></html>"
        extractor = TracklistExtractor(html)
        tracks = extractor.extract_tracks()
        assert tracks == []

    def test_extract_tracks_valid_html(self) -> None:
        """Test extract_tracks with valid HTML structure."""
        html = """
        <html>
        <body>
        <table>
        <tr>
            <td>Header</td>
            <td align="center">1</td>
            <td align="right">1.</td>
            <td class="clickable-row"><a>Test Song</a></td>
            <td class="clickable-row"><a>3:45</a></td>
            <td class="clickable-row"><a>4.5MB</a></td>
        </tr>
        </table>
        </body>
        </html>
        """
        extractor = TracklistExtractor(html)
        tracks = extractor.extract_tracks()

        assert len(tracks) == 1
        assert tracks[0].disc == 1
        assert tracks[0].track == 1
        assert tracks[0].title == "Test Song"
        assert tracks[0].duration == "3:45"
        assert tracks[0].file_size == "4.5MB"

    def test_save_to_csv(self, tmp_path: Path) -> None:
        """Test save_to_csv functionality."""
        extractor = TracklistExtractor("")
        tracks = [
            Track(disc=1, track=1, title="Song 1", duration="3:45", file_size="4.5MB"),
            Track(disc=1, track=2, title="Song 2", duration="4:12", file_size="5.2MB"),
        ]

        output_file = tmp_path / "test_tracklist.csv"
        extractor.save_to_csv(tracks, output_file)

        # Check if file was created and has correct content
        assert output_file.exists()
        content = output_file.read_text(encoding="utf-8")

        assert "Disc,Track,Title,Duration,File Size" in content
        assert "1,1,Song 1,3:45,4.5MB" in content
        assert "1,2,Song 2,4:12,5.2MB" in content


class TestTracklistCommand:
    """Test class for tracklist CLI command."""

    @patch("moro.cli.tracklist_extractor.httpx.Client")
    def test_tracklist_command_success(self, mock_client_class: Mock, tmp_path: Path) -> None:
        """Test tracklist command with successful URL fetch."""
        # Mock HTTP response
        mock_response = Mock()
        mock_response.text = """
        <html>
        <body>
        <table>
        <tr>
            <td>Header</td>
            <td align="center">1</td>
            <td align="right">1.</td>
            <td class="clickable-row"><a>Test Song</a></td>
            <td class="clickable-row"><a>3:45</a></td>
            <td class="clickable-row"><a>4.5MB</a></td>
        </tr>
        </table>
        </body>
        </html>
        """
        mock_response.raise_for_status.return_value = None

        # Mock client instance as context manager
        mock_client = Mock()
        mock_client.get.return_value = mock_response
        mock_client.__enter__ = Mock(return_value=mock_client)
        mock_client.__exit__ = Mock(return_value=None)
        mock_client_class.return_value = mock_client

        runner = CliRunner()
        output_file = tmp_path / "test_output.csv"

        result = runner.invoke(
            cli, ["tracklist", "http://example.com/tracklist", "-o", str(output_file)]
        )

        assert result.exit_code == 0
        assert "1曲の曲目リストを" in result.output
        assert "保存しました" in result.output
        assert output_file.exists()

    @patch("moro.cli.tracklist_extractor.httpx.Client")
    def test_tracklist_command_http_error(self, mock_client_class: Mock) -> None:
        """Test tracklist command with HTTP error."""
        # Mock client that raises HTTPError
        mock_client = Mock()
        mock_client.get.side_effect = httpx.HTTPError("Connection failed")
        mock_client.__enter__ = Mock(return_value=mock_client)
        mock_client.__exit__ = Mock(return_value=None)
        mock_client_class.return_value = mock_client

        runner = CliRunner()
        result = runner.invoke(cli, ["tracklist", "http://example.com/invalid"])

        assert result.exit_code != 0
        assert "エラーが発生しました" in result.output

    @patch("moro.cli.tracklist_extractor.httpx.Client")
    def test_tracklist_command_default_output(
        self, mock_client_class: Mock, tmp_path: Path
    ) -> None:
        """Test tracklist command with default output filename."""
        # Mock HTTP response
        mock_response = Mock()
        mock_response.text = "<html><body></body></html>"
        mock_response.raise_for_status.return_value = None

        # Mock client instance as context manager
        mock_client = Mock()
        mock_client.get.return_value = mock_response
        mock_client.__enter__ = Mock(return_value=mock_client)
        mock_client.__exit__ = Mock(return_value=None)
        mock_client_class.return_value = mock_client

        runner = CliRunner()

        # Change to temp directory to avoid creating files in project root
        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(cli, ["tracklist", "http://example.com/tracklist"])

            assert result.exit_code == 0
            assert "tracklist.csv" in result.output
            assert Path("tracklist.csv").exists()
