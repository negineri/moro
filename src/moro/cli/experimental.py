"""Experimental command group."""

import asyncio
from logging import getLogger

import click
from injector import Injector

from moro.cli._utils import AliasedGroup, click_verbose_option, config_logging
from moro.config.settings import ConfigRepository
from moro.dependencies.container import async_injector
from moro.modules.common.infrastructure import PlaywrightProvider
from moro.modules.common.utils import PWScriptLoadError, iter_pwscript_classes

_logger = getLogger(__name__)


@click.group(cls=AliasedGroup)
def experimental() -> None:
    """Experimental commands."""
    pass


@experimental.command()
@click_verbose_option
def list_scripts(verbose: tuple[bool]) -> None:
    """List all available Playwright scripts."""
    config = ConfigRepository.create()
    config_logging(config, verbose)

    try:
        scripts = iter_pwscript_classes(config.common.plugin_dirs)
    except PWScriptLoadError as e:
        _logger.debug("Failed to load Playwright scripts", exc_info=True)
        raise click.ClickException(str(e)) from e

    if not scripts:
        click.echo("No Playwright scripts found.")
        return

    for script in sorted(scripts, key=lambda script: script.name):
        click.echo(f"{script.name}\t({script.__module__}.{script.__qualname__})")


@experimental.command()
@click_verbose_option
@click.argument("url", type=str)
@click.option(
    "--no-headless", is_flag=True, default=False, help="Run Playwright in non-headless mode"
)
@click.option("--login", is_flag=True, default=False, help="Login to the site before downloading")
def download(url: str, verbose: tuple[bool], no_headless: bool, login: bool) -> None:
    """Download content from a URL."""
    config = ConfigRepository.create()
    config.common.playwright_headless = not no_headless
    config_logging(config, verbose)

    try:
        scripts = iter_pwscript_classes(config.common.plugin_dirs)
    except PWScriptLoadError as e:
        _logger.debug("Failed to load Playwright scripts", exc_info=True)
        raise click.ClickException(str(e)) from e

    instance = None
    for script in scripts:
        if script.validate(url):
            click.echo(f"Using script: {script.name}")
            # Here you would call the script's download method or similar
            instance = script()
    if instance is None:
        raise click.ClickException("No suitable script found for the given URL.")

    @async_injector(config)
    async def run_async(injector: Injector) -> None:
        provider = injector.get(PlaywrightProvider)
        res = await provider.execute_script(
            instance, {"url": url, "login": login, "output_dir": config.common.working_dir}
        )
        click.echo(res)

    asyncio.run(run_async())
