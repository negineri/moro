"""
Fantia CLI Module

Provides a command-line interface for interacting with Fantia, including login functionality.
"""

from logging import getLogger

import click

from moro.cli._utils import AliasedGroup, click_verbose_option, config_logging
from moro.config.settings import ConfigRepository
from moro.dependencies.container import create_injector
from moro.modules.fantia.usecases import FantiaGetFanclubUseCase, FantiaGetPostsUseCase

logger = getLogger(__name__)


@click.group(cls=AliasedGroup)
def fantia() -> None:
    """Fantia command group."""


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
