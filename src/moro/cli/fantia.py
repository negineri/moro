"""
Fantia CLI Module

Provides a command-line interface for interacting with Fantia, including login functionality.
"""

from logging.config import dictConfig

import click

from moro.cli._utils import AliasedGroup
from moro.config.settings import ConfigRepository
from moro.dependencies.container import create_injector
from moro.usecases.fantia import FantiaDownloadPostsByUserUseCase, FantiaDownloadPostUseCase


@click.group(cls=AliasedGroup)
def fantia() -> None:
    """Fantia command group."""


@fantia.command()
@click.option(
    "-i",
    "--post-id",
    type=str,
    required=True,
    help="Fantia post ID to download.",
)
def post(post_id: str) -> None:
    """Download a post by its ID."""
    injector = create_injector()
    config = injector.get(ConfigRepository)
    config.load_env()

    injector.get(FantiaDownloadPostUseCase).execute(post_id)


@fantia.command()
@click.option(
    "-i",
    "--user-id",
    type=str,
    required=True,
    help="Fantia user ID to download posts from.",
)
@click.option(
    "-v",
    "--verbose",
    is_flag=True,
    help="Enable verbose output.",
)
def user(user_id: str, verbose: bool) -> None:
    """Download posts by user ID."""
    injector = create_injector()
    config = injector.get(ConfigRepository)
    config.load_env()
    if verbose:
        config.app.logging_config["loggers"][""]["level"] = "INFO"
        dictConfig(config.app.logging_config)

    injector.get(FantiaDownloadPostsByUserUseCase).execute(user_id)
