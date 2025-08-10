"""
Fantia CLI Module

Provides a command-line interface for interacting with Fantia, including login functionality.
"""

from logging import getLogger

import click

from moro.cli._progress import PostsProgressManager
from moro.cli._utils import AliasedGroup, click_verbose_option, config_logging
from moro.config.settings import ConfigRepository
from moro.dependencies.container import create_injector
from moro.modules.fantia.usecases import (
    FantiaGetFanclubUseCase,
    FantiaGetPostsUseCase,
    FantiaSavePostUseCase,
)

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
    """Download posts by their IDs with progress bar."""
    config = ConfigRepository.create()
    config_logging(config, verbose)
    injector = create_injector(config)

    post_ids = list(post_id)
    if fanclub_id:
        fanclub = injector.get(FantiaGetFanclubUseCase).execute(fanclub_id)
        if not fanclub:
            click.echo(f"Fanclub with ID {fanclub_id} not found.")
            return
        post_ids.extend(post for post in fanclub.posts)

    with PostsProgressManager(total_posts=len(post_ids)) as progress_manager:
        try:
            save_usecase = injector.get(FantiaSavePostUseCase)
            posts_iterator = injector.get(FantiaGetPostsUseCase).execute(post_ids)

            for post in posts_iterator:
                progress_manager.start_post(post.id, post.title)
                save_usecase.execute(post)
                progress_manager.finish_post()

        except KeyboardInterrupt:
            click.echo("\nOperation cancelled by user")
        except Exception as e:
            click.echo(f"Error during processing: {e}")
            raise


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
    config_logging(config, verbose)

    injector = create_injector(config)

    fanclub = injector.get(FantiaGetFanclubUseCase).execute(fanclub_id)
    if not fanclub:
        click.echo(f"Fanclub with ID {fanclub_id} not found.")
        return

    click.echo(f"{fanclub.id} has {len(fanclub.posts)} posts.")
