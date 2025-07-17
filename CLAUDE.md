# CLAUDE.md

必ず日本語で回答してください。
This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Installation

- `pip install git+ssh://git@github.com/negineri/moro.git` - Install from GitHub

## Commands

### Development Setup

- `uv run moro` - Run the CLI tool directly without installation
- `pre-commit install` - Install pre-commit hooks for code quality
- `uv sync --group dev` - Install development dependencies

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
- **Configuration**: YAML-based logging configuration loaded via ConfigRepository
- **Main Commands**:
  - `example` - Example/template command
  - `download` - URL downloader with ZIP compression and numbered prefix support
  - `tracklist` - HTML tracklist extractor with CSV export functionality

### Code Standards

- Type annotations required for all functions/methods (mypy strict mode)
- Google-style docstrings for all public functions/classes/modules
- Ruff for linting and formatting (line length: 100)
- Japanese comments supported (RUF002/RUF003 ignored)
- 90%+ test coverage target with pytest-cov

### Entry Point

- CLI entry point: `moro.cli.cli:cli`
- Module can be run directly: `python -m moro`

## Development Flow

### Test-Driven Development (TDD)

**MANDATORY**: All implementations must strictly follow TDD principles.

#### TDD Cycle
1. **Red**: Write a failing test first
2. **Green**: Write minimal code to make the test pass
3. **Refactor**: Improve the code while keeping tests green

#### TODO List-Based Implementation

Always create a TODO list before implementation and follow these steps:

1. **Requirements Analysis**: Generate TODO list from initial requirements
2. **Gradual Specification**: Clarify details for each TODO item
3. **Test Category Classification**:
   - `[ ] Happy Path`: Basic functionality verification
   - `[ ] Error Cases`: Error handling scenarios
   - `[ ] Edge Cases`: Boundary conditions
   - `[ ] Integration`: Inter-component interactions

#### Implementation Flow
```
Requirements → TODO List → Failing Test → Minimal Implementation → Refactor → Next TODO
```

#### Consultation Phase Dialogue

For complex implementations or unclear requirements, use this gradual specification approach:

1. **Requirements Analysis Dialogue**: Ask "What kind of...?" to clarify details
2. **Existing Code Analysis**: Learn existing patterns before implementation
3. **Scenario Expansion**: Consider happy path → error cases → edge cases
4. **Gradual Detailing**: Purpose → Preconditions → Actions → Expected Results

## Implementation Best Practices

### Type Safety

- Use modern Python type hints (`list[T]` instead of `List[T]`)
- Cast when necessary but prefer type guards (`isinstance`)
- Handle optional types explicitly with Union or None checks
- Use NamedTuple for structured data with immutability
- Use Union types for Python 3.9 compatibility instead of `|` syntax
