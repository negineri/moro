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
    config = ConfigRepository.create()
    injector = create_injector(config)

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
    config = ConfigRepository.create()
    if verbose:
        config.common.logging_config["loggers"]["default"]["level"] = "INFO"
        dictConfig(config.common.logging_config)
    injector = create_injector(config)

    injector.get(FantiaDownloadPostsByUserUseCase).execute(user_id)
