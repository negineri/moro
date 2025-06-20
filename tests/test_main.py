"""Tests for __main__.py module."""

import sys
from unittest.mock import patch


class TestMainModule:
    """Test cases for the __main__.py module."""

    def test_main_module_execution(self):
        """Test that __main__.py executes the CLI when run as a module."""
        # Mock sys.argv to prevent click from parsing test arguments
        with patch('sys.argv', ['moro']):
            with patch('moro.cli.cli.cli') as mock_cli:
                # Import the module to trigger execution
                if 'moro.__main__' in sys.modules:
                    del sys.modules['moro.__main__']
                import moro.__main__  # noqa: F401

                # Verify that cli() was called
                mock_cli.assert_called_once()
