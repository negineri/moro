"""
Fantia CLI Module

Provides a command-line interface for interacting with Fantia, including login functionality.
"""

import click

from moro.config.settings import AppConfig
from moro.dependencies.container import create_injector
from moro.usecases.fantia import FantiaDownloadPostUseCase


@click.command()
@click.option(
    "-u",
    "--url",
    type=str,
    required=True,
    help="Fantia URL (e.g., https://fantia.jp/posts/123456)",
)
@click.option(
    "-s",
    "--session_id",
    type=str,
    help="Fantia _session_id value",
)
def fantia(url: str, session_id: str) -> None:
    """Interact with Fantia using the provided URL and session ID."""
    injector = create_injector()
    config = injector.get(AppConfig)
    config.fantia.download_thumb = True
    config.fantia.session_id = session_id

    injector.get(FantiaDownloadPostUseCase).execute(url)
