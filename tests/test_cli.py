"""Test suite for the CLI module."""

from unittest.mock import patch

import click
from click.testing import CliRunner

from moro.cli._utils import AliasedGroup
from moro.cli.cli import cli


def test_example_command() -> None:
    """Test the example command."""
    runner = CliRunner()
    result = runner.invoke(cli, ["example", "echo"])
    assert result.exit_code == 0
    assert "Current configuration: app=AppConfig" in result.output
    assert "fantia=FantiaConfig" in result.output


def test_main_entry_point() -> None:
    """Test the CLI entry point in __main__.py."""
    runner = CliRunner()
    result = runner.invoke(cli)
    assert result.exit_code == 0


def test_aliased_group() -> None:
    """Test the AliasedGroup."""
    group = AliasedGroup()

    @group.command("hello")
    def hello() -> None:
        click.echo("Hello, World!")

    ctx = click.Context(group)
    command = group.get_command(ctx, "he")
    assert command is not None
    assert command.name == "hello"
    command = group.get_command(ctx, "a")
    assert command is None


def test_config_repo_read_file_not_found() -> None:
    """Test _load_logging_config raises FileNotFoundError when logging config is missing."""
    from moro.config.settings import _load_logging_config

    with patch("pathlib.Path.exists", return_value=False):
        try:
            _load_logging_config()
        except FileNotFoundError as e:
            assert "Logging configuration file not found" in str(e)


def test_aliased_group_multiple_matches() -> None:
    """Test AliasedGroup handling of multiple matches."""
    group = AliasedGroup()

    @group.command("hello")
    def hello() -> None:
        click.echo("Hello!")

    @group.command("help")
    def help_cmd() -> None:
        click.echo("Help!")

    ctx = click.Context(group)

    # Test multiple matches - should fail
    ctx.fail = lambda msg: (_ for _ in ()).throw(click.BadParameter(msg))
    try:
        group.get_command(ctx, "he")
        raise AssertionError("Should have raised an exception")
    except click.BadParameter as e:
        assert "Too many matches" in str(e)


def test_resolve_command_with_none_command() -> None:
    """Test resolve_command when command is None."""
    group = AliasedGroup()
    ctx = click.Context(group)

    # Mock the parent resolve_command to return None
    with patch.object(click.Group, "resolve_command", return_value=("", None, ["nonexistent"])):
        try:
            group.resolve_command(ctx, ["nonexistent"])
            raise AssertionError("Should have raised an exception")
        except click.BadParameter as e:
            assert "Command 'nonexistent' not found" in str(e)
