from logging import getLogger
from logging.config import dictConfig

import click

from moro.config.settings import ConfigRepository

logger = getLogger(__name__)


class AliasedGroup(click.Group):
    """
    Group class that allows commands to be aliased.

    http://click.pocoo.org/5/advanced/
    """

    def get_command(self, ctx: click.Context, cmd_name: str) -> click.Command | None:
        """Get a command by its name or alias."""
        rv = click.Group.get_command(self, ctx, cmd_name)
        if rv is not None:
            return rv
        matches = [x for x in self.list_commands(ctx) if x.startswith(cmd_name)]
        if not matches:
            return None
        if len(matches) == 1:
            return click.Group.get_command(self, ctx, matches[0])
        return ctx.fail(f"Too many matches: {', '.join(sorted(matches))}")

    def resolve_command(
        self, ctx: click.Context, args: list[str]
    ) -> tuple[str, click.Command, list[str]]:
        """Resolve a command and its arguments."""
        # always return the full command name
        _, cmd, args = super().resolve_command(ctx, args)
        if cmd is None or cmd.name is None:
            raise click.BadParameter(
                f"Command '{args[0]}' not found. Use 'moro --help' for a list of commands."
            )
        return cmd.name, cmd, args


click_verbose_option = click.option(
    "-v",
    "--verbose",
    is_flag=True,
    multiple=True,
    help="Enable verbose output.",
)


def config_logging(verbose: tuple[bool], config: ConfigRepository) -> None:
    """Configure logging based on verbosity."""
    if len(verbose) == 1:
        config.common.logging_config["root"]["level"] = "INFO"
        dictConfig(config.common.logging_config)
        logger.info("Setting log level to INFO")
        return

    if len(verbose) > 1:
        config.common.logging_config["root"]["level"] = "DEBUG"
        dictConfig(config.common.logging_config)
        logger.info("Setting log level to DEBUG")
        return


__all__ = ["AliasedGroup", "click_verbose_option", "config_logging"]
