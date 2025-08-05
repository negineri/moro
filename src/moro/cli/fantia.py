"""
Fantia CLI Module

Provides a command-line interface for interacting with Fantia, including login functionality.
"""

from logging import getLogger
from logging.config import dictConfig

import click

from moro.cli._utils import AliasedGroup, click_verbose_option, config_logging
from moro.config.settings import ConfigRepository
from moro.dependencies.container import create_injector
from moro.modules.fantia.usecases import FantiaGetFanclubUseCase, FantiaGetPostsUseCase
from moro.usecases.fantia import FantiaDownloadPostsByUserUseCase, FantiaDownloadPostUseCase

logger = getLogger(__name__)


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
    "--post-id",
    type=str,
    multiple=True,
    help="Fantia post ID to download.",
)
@click.option(
    "-f",
    "--fanclub-id",
    type=str,
    help="Fantia fanclub ID to filter posts.",
)
@click_verbose_option
def posts(post_id: tuple[str], fanclub_id: str, verbose: tuple[bool]) -> None:
    """Download posts by their IDs."""
    config = ConfigRepository.create()
    config_logging(verbose, config)
    injector = create_injector(config)

    post_ids = list(post_id)
    if fanclub_id:
        fanclub = injector.get(FantiaGetFanclubUseCase).execute(fanclub_id)
        if not fanclub:
            click.echo(f"Fanclub with ID {fanclub_id} not found.")
        else:
            post_ids.extend(post for post in fanclub.posts)

    posts = injector.get(FantiaGetPostsUseCase).execute(post_ids)
    for post in posts:
        click.echo(f"Downloaded post: {post.id} - {post.title}")


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
        dictConfig(config.common.logging_config)
    injector = create_injector(config)

    injector.get(FantiaDownloadPostsByUserUseCase).execute(user_id)


@fantia.command()
@click.option(
    "-i",
    "--fanclub-id",
    type=str,
    required=True,
    help="Fantia fanclub ID to download posts from.",
)
@click_verbose_option
def fanclub(fanclub_id: str, verbose: tuple[bool]) -> None:
    """Download posts by fanclub ID."""
    config = ConfigRepository.create()
    config_logging(verbose, config)

    injector = create_injector(config)

    fanclub = injector.get(FantiaGetFanclubUseCase).execute(fanclub_id)
    if not fanclub:
        click.echo(f"Fanclub with ID {fanclub_id} not found.")
        return

    click.echo(f"{fanclub.id} has {len(fanclub.posts)} posts.")
