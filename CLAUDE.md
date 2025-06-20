# CLAUDE.md

必ず日本語で回答してください。
This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

### Development Setup

- `uv run moro` - Run the CLI tool directly without installation
- `pre-commit install` - Install pre-commit hooks for code quality

### Code Quality and Testing

- `uv run ruff check` - Run linting checks
- `uv run ruff format` - Format code automatically
- `uv run mypy src/` - Run type checking
- `uv run pytest` - Run all tests
- `uv run pytest tests/test_<specific>.py` - Run specific test file
- `uv run pytest --cov=src --cov-report=html` - Run tests with coverage report
- `tox` - Run tests across multiple Python versions (3.9, 3.10, 3.11)

### Documentation

- `mkdocs build` - Build documentation
- `mkdocs serve` - Serve documentation locally

### Version Management

- `bump-my-version bump patch/minor/major` - Bump version using bump-my-version

## Architecture

### Project Structure

This is a personal toolbox project (`moro`) that aggregates miscellaneous scripts as CLI subcommands:

- `src/moro/cli/` - CLI interface using Click framework with AliasedGroup support
- `src/moro/modules/` - Core functionality modules
- `src/moro/config/` - Configuration management with YAML logging config
- `tests/` - Test suite with pytest

### Key Components

- **CLI Framework**: Uses Click with custom AliasedGroup for command shortcuts
- **Dependency Injection**: Uses injector library for configuration management
- **Configuration**: YAML-based logging configuration loaded via ConfigRepo
- **Main Commands**:
  - `example` - Example/template command
  - `download` - URL downloader with ZIP compression and numbered prefix support

### Code Standards

- Type annotations required for all functions/methods (mypy strict mode)
- Google-style docstrings for all public functions/classes/modules
- Ruff for linting and formatting (line length: 100)
- Japanese comments supported (RUF002/RUF003 ignored)
- 90%+ test coverage target with pytest-cov

### Entry Point

- CLI entry point: `moro.cli.cli:cli`
- Module can be run directly: `python -m moro`
