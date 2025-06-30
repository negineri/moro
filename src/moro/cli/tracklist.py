"""曲目リスト抽出コマンド."""

from logging import getLogger
from pathlib import Path
from typing import Union

import click

from moro.modules.tracklist_extractor import extract_tracklist_from_url_to_csv

logger = getLogger(__name__)


@click.command()
@click.argument("url", type=str)
@click.option(
    "-o",
    "--output",
    type=click.Path(path_type=Path),
    help="出力CSVファイルパス(デフォルト: tracklist.csv)",
)
def tracklist(url: str, output: Union[Path, None]) -> None:
    """
    URLから曲目リストを抽出してCSVファイルに保存する.

    URL: 曲目リストが含まれるWebページのURL
    """
    if output is None:
        output = Path("tracklist.csv")

    try:
        track_count = extract_tracklist_from_url_to_csv(url, output)

        click.echo(f"✅ {track_count}曲の曲目リストを {output} に保存しました")
        logger.info(f"Extracted {track_count} tracks from {url} to {output}")

    except Exception as e:
        click.echo(f"❌ エラーが発生しました: {e}", err=True)
        logger.error(f"Failed to extract tracklist: {e}")
        raise click.ClickException(str(e)) from e
