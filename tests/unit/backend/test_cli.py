import logging
import platform
import sqlite3
import unittest
from unittest import mock

from typetrace.backend.cli import CLI
from typetrace.config import ExitCodes

logging.disable(logging.CRITICAL)


class TestCLI(unittest.TestCase):
    """Test suite for the CLI class."""

    def setUp(self) -> None:
        """Initialize a fresh CLI instance before each test."""
        self.cli = CLI()

    def test_run_unsupported_platform(self) -> None:
        """Return PLATFORM_ERROR when running on unsupported platform."""
        with mock.patch.object(platform, "system", return_value="UnknownOS"):
            code = self.cli.run()
        self.assertEqual(code, ExitCodes.PLATFORM_ERROR)

    def test_run_database_error(self) -> None:
        """Return DATABASE_ERROR when initialize_database raises sqlite3.Error."""
        with mock.patch.object(platform, "system", return_value="Linux"), \
             mock.patch.object(self.cli._CLI__db_manager,
                              "initialize_database",
                              side_effect=sqlite3.Error):
            code = self.cli.run()
        self.assertEqual(code, ExitCodes.DATABASE_ERROR)

    def test_run_permission_error(self) -> None:
        """Return PERMISSION_ERROR if user is not in 'input' group."""
        with mock.patch.object(platform, "system", return_value="Linux"), \
             mock.patch.object(self.cli._CLI__db_manager,
                              "initialize_database",
                              return_value=None), \
             mock.patch.object(self.cli,
                              "_check_input_group",
                              side_effect=PermissionError):
            code = self.cli.run()
        self.assertEqual(code, ExitCodes.PERMISSION_ERROR)

    def test_check_input_group_member(self) -> None:
        """Not raise PermissionError if user is in the 'input' group."""
        with mock.patch("os.getlogin", return_value="user1"), \
             mock.patch("grp.getgrnam", return_value=mock.MagicMock(gr_mem=["user1"])):
            try:
                self.cli._check_input_group()
            except PermissionError:
                self.fail("_check_input_group() raised PermissionError unexpectedly")

if __name__ == "__main__":
    unittest.main()
