"""
Fantia CLI Module

Provides a command-line interface for interacting with Fantia, including login functionality.
"""

import logging

import click

from moro.modules.fantia import FantiaClient, FantiaConfig, download_post, login
from moro.modules.pixiv import PixivError


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
    required=True,
    help="Fantia _session_id value",
)
def fantia(url: str, session_id: str) -> None:
    """Interact with Fantia using the provided URL and session ID."""
    config = FantiaConfig()
    config.download_thumb = True
    with FantiaClient(session_id=session_id) as client:
        try:
            login(client)
            download_post(client, url, config)
        except Exception as e:
            logging.error(f"An error occurred: {e}")
            raise PixivError("Failed to interact with FantiaClient") from e
