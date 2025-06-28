"""曲目リスト抽出コマンド."""

from logging import getLogger
from pathlib import Path
from typing import Union

import click

from moro.cli.tracklist_extractor import extract_tracklist_to_csv

logger = getLogger(__name__)


@click.command()
@click.argument('html_file', type=click.Path(exists=True, path_type=Path))
@click.option(
    '-o', '--output',
    type=click.Path(path_type=Path),
    help='出力CSVファイルパス(デフォルト: tracklist.csv)'
)
def tracklist(html_file: Path, output: Union[Path, None]) -> None:
    """
    HTMLファイルから曲目リストを抽出してCSVファイルに保存する.

    HTML_FILE: 曲目リストが含まれるHTMLファイルのパス
    """
    if output is None:
        output = Path('tracklist.csv')

    try:
        track_count = extract_tracklist_to_csv(html_file, output)

        click.echo(f"✅ {track_count}曲の曲目リストを {output} に保存しました")
        logger.info(f"Extracted {track_count} tracks from {html_file} to {output}")

    except Exception as e:
        click.echo(f"❌ エラーが発生しました: {e}", err=True)
        logger.error(f"Failed to extract tracklist: {e}")
        raise click.ClickException(str(e)) from e
