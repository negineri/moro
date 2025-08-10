"""Entry point for the CLI."""

from logging import getLogger

import click

from moro.cli._utils import AliasedGroup, config_logging
from moro.cli.config import config
from moro.cli.example import example
from moro.cli.fantia import fantia
from moro.cli.pixiv import pixiv
from moro.cli.todo import todo
from moro.cli.tracklist import tracklist
from moro.cli.url_downloader import download
from moro.config.settings import ConfigRepository

logger = getLogger(__name__)


@click.group(cls=AliasedGroup)
@click.version_option()
def cli() -> None:
    """Entry point for the CLI."""
    repo = ConfigRepository.create()

    # Configure logging
    config_logging(repo)


cli.add_command(config)
cli.add_command(example)
cli.add_command(tracklist)
cli.add_command(download)
cli.add_command(pixiv)
cli.add_command(fantia)
cli.add_command(todo)
