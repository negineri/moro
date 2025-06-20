"""Tests for the __main__.py module."""

import sys
from unittest.mock import patch


class TestMainModule:
    """
    Test cases for the __main__.py module.

    This class contains tests to verify that the main module correctly
    initializes the CLI when executed as a module.
    """

    def test_cli_execution_when_main_module_imported(self) -> None:
        """
        Test that __main__.py executes the CLI entry point when imported.

        This test verifies that importing the __main__ module triggers
        the CLI execution, which is the expected behavior when running
        the package using `python -m moro`.

        Returns:
            None
        """
        # Mock sys.argv to prevent click from parsing test arguments
        with patch("sys.argv", ["moro"]):
            with patch("moro.cli.cli.cli") as mock_cli:
                # Import the module to trigger execution
                if "moro.__main__" in sys.modules:
                    del sys.modules["moro.__main__"]
                import moro.__main__  # noqa: F401

                # Verify that cli() was called
                mock_cli.assert_called_once()
