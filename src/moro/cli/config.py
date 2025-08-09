"""Configuration management commands."""

from pathlib import Path

import click
import tomli_w

from moro.cli._utils import AliasedGroup
from moro.config.settings import CONFIG_PATHS, ConfigRepository


@click.group(cls=AliasedGroup)
def config() -> None:
    """Configuration management commands."""
    pass


@config.command()
def show() -> None:
    """Show current configuration."""
    repo = ConfigRepository.create()

    click.echo("Current configuration:")
    click.echo(repo.model_dump_json(indent=2))


@config.command()
@click.option(
    "--path",
    type=click.Path(),
    default="./settings.toml",
    help="Path to generate the configuration file (default: ./settings.toml)",
)
@click.option(
    "--force",
    is_flag=True,
    help="Overwrite existing configuration file",
)
def init(path: str, force: bool) -> None:
    """Generate a default configuration file."""
    config_path = Path(path)

    if config_path.exists() and not force:
        click.echo(f"Configuration file already exists: {config_path}")
        click.echo("Use --force to overwrite.")
        return

    # Create default configuration
    repo = ConfigRepository.create()
    default_config = repo.model_dump(exclude_unset=True)

    # Ensure directory exists
    config_path.parent.mkdir(parents=True, exist_ok=True)

    # Write configuration file
    with open(config_path, "wb") as f:
        tomli_w.dump(default_config, f)

    click.echo(f"Generated default configuration file: {config_path}")


@config.command()
@click.option(
    "--config-file",
    type=click.Path(exists=True),
    help="Path to configuration file to validate",
)
def validate(config_file: str | None) -> None:
    """Validate configuration file or current configuration."""
    if config_file:
        # Validate specific configuration file
        try:
            _ = ConfigRepository.create(paths=[config_file])

            click.echo(f"Configuration file {config_file} is valid.")
        except Exception as e:
            click.echo(f"Configuration file {config_file} is invalid: {e}")
            raise click.Abort() from e
    else:
        # Validate current configuration
        try:
            _ = ConfigRepository.create()

            click.echo("Current configuration is valid.")
        except Exception as e:
            click.echo(f"Current configuration is invalid: {e}")
            raise click.Abort() from e


@config.command()
def paths() -> None:
    """Show configuration file search paths."""
    click.echo("Configuration files are searched in the following order:")
    for i, path in enumerate(CONFIG_PATHS, 1):
        click.echo(f"{i}. {path}")
