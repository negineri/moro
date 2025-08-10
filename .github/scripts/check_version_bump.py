#!/usr/bin/env python3
"""Check if version in pyproject.toml has been bumped compared to main branch."""

import sys
from pathlib import Path

try:
    import tomllib
except ImportError:
    # Python < 3.11 fallback
    import tomli as tomllib

try:
    from packaging import version
except ImportError:
    print("ERROR: packaging library is required. Install with: pip install packaging")
    sys.exit(1)


def get_version_from_pyproject(file_path: Path) -> str:
    """Extract version from pyproject.toml file."""
    try:
        with open(file_path, "rb") as f:
            data = tomllib.load(f)
        return data["project"]["version"]
    except FileNotFoundError:
        print(f"ERROR: {file_path} not found")
        sys.exit(1)
    except KeyError as e:
        print(f"ERROR: Missing key {e} in {file_path}")
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: Failed to parse {file_path}: {e}")
        sys.exit(1)


def compare_versions(current_version: str, main_version: str) -> bool:
    """Compare two semantic versions."""
    try:
        current_ver = version.parse(current_version)
        main_ver = version.parse(main_version)
        return current_ver > main_ver
    except Exception as e:
        print(f"ERROR: Failed to parse versions: {e}")
        sys.exit(1)


def main() -> None:
    """Main function to check version bump."""
    if len(sys.argv) != 3:
        print("Usage: python check_version_bump.py <current_version> <main_version>")
        sys.exit(1)

    current_version = sys.argv[1]
    main_version = sys.argv[2]

    print(f"Main branch version: {main_version}")
    print(f"Current PR version: {current_version}")

    if compare_versions(current_version, main_version):
        print(f"SUCCESS: Version properly bumped from {main_version} to {current_version}")
        sys.exit(0)
    else:
        print(f"ERROR: Version must be bumped. Current: {current_version}, Main: {main_version}")
        sys.exit(1)


if __name__ == "__main__":
    main()
