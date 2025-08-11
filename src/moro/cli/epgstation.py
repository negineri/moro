"""EPGStation 録画管理コマンド"""

import click

from moro.cli._utils import click_verbose_option, config_logging
from moro.config.settings import ConfigRepository
from moro.dependencies.container import create_injector
from moro.modules.epgstation.usecases import ListRecordingsUseCase


@click.group()
def epgstation() -> None:
    """EPGStation 録画管理コマンド"""
    pass


@epgstation.command(name="list")
@click.option(
    "--limit",
    default=100,
    type=int,
    help="表示する録画数の上限（デフォルト: 100）",
)
@click_verbose_option
def list_recordings(limit: int, verbose: tuple[bool]) -> None:
    """録画一覧を表示"""
    config = ConfigRepository.create()
    config_logging(config, verbose)
    try:
        injector = create_injector(config)
        use_case = injector.get(ListRecordingsUseCase)
        result = use_case.execute(limit=limit)
        click.echo(result)
    except Exception as e:
        raise click.ClickException(str(e)) from e


if __name__ == "__main__":
    epgstation()
