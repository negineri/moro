"""EPGStation 録画管理コマンド"""

import click

from moro.dependencies import get_injector
from moro.modules.epgstation.usecases import ListRecordingsUseCase


@click.group()
def epgstation() -> None:
    """EPGStation 録画管理コマンド"""
    pass


@epgstation.command()
@click.option(
    "--limit",
    default=100,
    type=int,
    help="表示する録画数の上限（デフォルト: 100）",
)
def list_recordings(limit: int) -> None:
    """録画一覧を表示"""
    try:
        injector = get_injector()
        use_case = injector.get(ListRecordingsUseCase)
        result = use_case.execute(limit=limit)
        click.echo(result)
    except Exception as e:
        click.echo(f"エラー: {e}", err=True)
        raise click.ClickException(str(e)) from e


if __name__ == "__main__":
    epgstation()
