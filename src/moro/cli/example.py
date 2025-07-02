"""Example command group."""

from logging import getLogger

import click

from moro.cli._utils import AliasedGroup
from moro.config.settings import AppConfig
from moro.dependencies.container import create_injector

logger = getLogger(__name__)


@click.group(cls=AliasedGroup)
def example() -> None:
    """Example command group."""
    pass


@example.command()
def echo() -> None:
    """Echo command."""
    # Example of accessing injector from context
    injector = create_injector()
    config = injector.get(AppConfig)
    click.echo(f"Current configuration: {config}")
