"""Unit tests for the CLI class in typetrace.backend.cli."""
import sqlite3
import sys
import types
import unittest
from unittest import mock

backend_mod = types.ModuleType("backend")
events_mod = types.ModuleType("backend.events")
windows_mod = types.ModuleType("backend.events.windows_darwin")

class DummyWinDarwin:
    def __init__(self, db_path, *args, **kwargs):
        pass
    def trace(self):
        pass
    def stop(self):
        pass

windows_mod.WindowsDarwinEventProcessor = DummyWinDarwin
sys.modules["backend"] = backend_mod
sys.modules["backend.events"] = events_mod
sys.modules["backend.events.windows_darwin"] = windows_mod

import pytest

from typetrace.backend.cli import CLI
from typetrace.config import ExitCodes


class TestCLI(unittest.TestCase):
    def setUp(self):
        self.cli = CLI()

    def tearDown(self):
        sys.modules.pop("grp", None)

    @mock.patch("typetrace.backend.cli.platform.system", return_value="AmigaOS")
    @mock.patch("typetrace.backend.cli.DatabaseManager.initialize_database")
    def test_unsupported_platform(self, mock_init_db, mock_platform):
        rc = self.cli.run()
        self.assertEqual(rc, ExitCodes.PLATFORM_ERROR)

    @mock.patch("typetrace.backend.cli.DatabaseManager.initialize_database", 
                side_effect=sqlite3.Error)
    def test_database_error(self, mock_init_db):
        rc = self.cli.run()
        self.assertEqual(rc, ExitCodes.DATABASE_ERROR)

    @mock.patch("typetrace.backend.cli.DatabaseManager.initialize_database", 
                side_effect=PermissionError)
    def test_permission_error(self, mock_init_db):
        rc = self.cli.run()
        self.assertEqual(rc, ExitCodes.PERMISSION_ERROR)

    @mock.patch("typetrace.backend.cli.DatabaseManager.initialize_database", 
                side_effect=RuntimeError)
    def test_runtime_error(self, mock_init_db):
        rc = self.cli.run()
        self.assertEqual(rc, ExitCodes.RUNTIME_ERROR)

    @mock.patch("typetrace.backend.cli.DatabaseManager.initialize_database", 
                side_effect=Exception("boom"))
    def test_unhandled_exception(self, mock_init_db):
        with pytest.raises(Exception, match="boom"):
            self.cli.run()

    @mock.patch("typetrace.backend.cli.platform.system", return_value="Windows")
    @mock.patch("typetrace.backend.cli.threading.Thread")
    @mock.patch("typetrace.backend.cli.DbusServiceManager")
    @mock.patch("typetrace.backend.cli.DatabaseManager.initialize_database")
    def test_run_windows_success(
        self, mock_init_db, mock_dbus_svc, mock_thread_cls, mock_platform
    ):
        win_mod = sys.modules["backend.events.windows_darwin"]
        win_mod.WindowsDarwinEventProcessor = mock.Mock(
            return_value=mock.Mock(trace=mock.Mock(), stop=mock.Mock())
        )

        dbus_inst = mock_dbus_svc.return_value
        dbus_inst.run.return_value = ExitCodes.SUCCESS

        thread_inst = mock_thread_cls.return_value
        thread_inst.is_alive.return_value = True

        rc = self.cli.run()
        self.assertEqual(rc, ExitCodes.SUCCESS)
        mock_init_db.assert_called_once_with(self.cli._CLI__db_path)


if __name__ == "__main__":
    unittest.main()
