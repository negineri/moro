#!/usr/bin/env python3
"""Extract version from pyproject.toml file."""

import sys
from pathlib import Path

try:
    import tomllib
except ImportError:
    # Python < 3.11 fallback
    import tomli as tomllib


def main() -> None:
    """Extract and print version from pyproject.toml."""
    if len(sys.argv) != 2:
        print("Usage: python get_version.py <pyproject.toml>")
        sys.exit(1)

    file_path = Path(sys.argv[1])

    try:
        with open(file_path, "rb") as f:
            data = tomllib.load(f)
        version = data["project"]["version"]
        print(version)
    except FileNotFoundError:
        print(f"ERROR: {file_path} not found", file=sys.stderr)
        sys.exit(1)
    except KeyError as e:
        print(f"ERROR: Missing key {e} in {file_path}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: Failed to parse {file_path}: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
