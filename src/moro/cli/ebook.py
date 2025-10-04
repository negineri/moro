"""Ebook CLI commands."""

import asyncio

import click

from moro.cli._utils import AliasedGroup, click_verbose_option, config_logging
from moro.config.settings import ConfigRepository
from moro.dependencies.container import create_injector
from moro.scenarios.ebook import EbookDownloadUseCase


@click.group(cls=AliasedGroup)
def ebook() -> None:
    """Ebook related commands."""
    pass


@ebook.command()
@click_verbose_option
@click.argument("url", type=str)
def download(url: str, verbose: tuple[bool, ...]) -> None:
    """Download ebook."""
    config = ConfigRepository.create()
    config_logging(config, verbose)

    async def run_async() -> None:
        injector = create_injector(config)
        ebook_download_usecase = injector.get(EbookDownloadUseCase)
        await ebook_download_usecase.execute(url)

    asyncio.run(run_async())
