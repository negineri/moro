"""Configuration management commands."""

from pathlib import Path
from typing import Any, Optional

import click
import yaml

from moro.cli._utils import AliasedGroup
from moro.config.settings import ConfigRepository
from moro.dependencies.container import create_injector


@click.group(cls=AliasedGroup)
def config() -> None:
    """Configuration management commands."""
    pass


@config.command()
def show() -> None:
    """Show current configuration."""
    injector = create_injector()
    config_repo = injector.get(ConfigRepository)
    config_repo.load_all()

    config_summary = config_repo.get_config_summary()
    click.echo("Current configuration:")
    click.echo(yaml.dump(config_summary, default_flow_style=False))


@config.command()
@click.option(
    "--path",
    type=click.Path(),
    default="./moro.yml",
    help="Path to generate the configuration file (default: ./moro.yml)",
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
    default_config: dict[str, Any] = {
        "app": {
            "jobs": 16,
            "user_data_dir": "~/.local/share/moro",
            "working_dir": ".",
        },
        "fantia": {
            "session_id": None,
            "directory": "downloads/fantia",
            "download_thumb": False,
            "priorize_webp": False,
            "use_server_filenames": False,
            "max_retries": 5,
            "timeout_connect": 10.0,
            "timeout_read": 30.0,
            "timeout_write": 10.0,
            "timeout_pool": 5.0,
            "concurrent_downloads": 3,
        },
    }

    # Ensure directory exists
    config_path.parent.mkdir(parents=True, exist_ok=True)

    # Write configuration file
    with open(config_path, "w", encoding="utf-8") as f:
        yaml.dump(default_config, f, default_flow_style=False, allow_unicode=True)

    click.echo(f"Generated default configuration file: {config_path}")


@config.command()
@click.option(
    "--config-file",
    type=click.Path(exists=True),
    help="Path to configuration file to validate",
)
def validate(config_file: Optional[str]) -> None:
    """Validate configuration file or current configuration."""
    if config_file:
        # Validate specific configuration file
        try:
            config_path = Path(config_file)
            with open(config_path, encoding="utf-8") as f:
                config_data = yaml.safe_load(f)

            # Create temporary config repository to validate
            temp_config = ConfigRepository()
            temp_config.merge_config(config_data or {})
            temp_config.validate_config()

            click.echo(f"Configuration file {config_file} is valid.")
        except Exception as e:
            click.echo(f"Configuration file {config_file} is invalid: {e}")
            raise click.Abort() from e
    else:
        # Validate current configuration
        try:
            injector = create_injector()
            config_repo = injector.get(ConfigRepository)
            config_repo.load_all()

            click.echo("Current configuration is valid.")
        except Exception as e:
            click.echo(f"Current configuration is invalid: {e}")
            raise click.Abort() from e


@config.command()
def paths() -> None:
    """Show configuration file search paths."""
    injector = create_injector()
    config_repo = injector.get(ConfigRepository)

    click.echo("Configuration files are searched in the following order:")

    for i, path in enumerate(config_repo.get_config_paths(), 1):
        exists = path.exists()
        status = "✓" if exists else "✗"
        click.echo(f"{i}. {status} {path}")
