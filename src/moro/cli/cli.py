"""Entry point for the CLI."""

from logging import getLogger
from logging.config import dictConfig

import click

from moro.cli._utils import AliasedGroup
from moro.cli.config import config
from moro.cli.example import example
from moro.cli.fantia import fantia
from moro.cli.pixiv import pixiv
from moro.cli.tracklist import tracklist
from moro.cli.url_downloader import download
from moro.config.settings import ConfigRepository
from moro.dependencies.container import create_injector

logger = getLogger(__name__)


@click.group(cls=AliasedGroup)
@click.version_option()
def cli() -> None:
    """Entry point for the CLI."""
    # Create injector and store in context
    injector = create_injector()

    # Configure logging
    config = injector.get(ConfigRepository)
    config.load_all()
    dictConfig(config.app.logging_config)


cli.add_command(config)
cli.add_command(example)
cli.add_command(tracklist)
cli.add_command(download)
cli.add_command(pixiv)
cli.add_command(fantia)
