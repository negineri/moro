from logging import getLogger
from logging.config import dictConfig
from pathlib import Path

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


def config_logging(config: ConfigRepository, verbose: tuple[bool] | None = None) -> None:
    """Configure logging based on verbosity."""
    # Create logs directory if file handler is configured
    if "file" in config.common.logging_config.get("handlers", {}):
        log_file_path = config.common.logging_config["handlers"]["file"]["filename"]
        # Replace %(user_data_dir)s with actual user data directory
        log_file_path = log_file_path.replace("%(user_data_dir)s", config.common.user_data_dir)
        config.common.logging_config["handlers"]["file"]["filename"] = log_file_path

        # Ensure log directory exists
        Path(log_file_path).parent.mkdir(parents=True, exist_ok=True)

    if verbose and len(verbose) == 1:
        config.common.logging_config["handlers"]["console"]["level"] = "INFO"
        dictConfig(config.common.logging_config)
        logger.info("Setting log level to INFO")
        return

    if verbose and len(verbose) > 1:
        config.common.logging_config["handlers"]["console"]["level"] = "DEBUG"
        dictConfig(config.common.logging_config)
        logger.info("Setting log level to DEBUG")
        return

    # Default case: apply configuration as-is
    dictConfig(config.common.logging_config)


__all__ = ["AliasedGroup", "click_verbose_option", "config_logging"]
