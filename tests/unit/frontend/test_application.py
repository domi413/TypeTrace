"""Unit tests for typetrace.frontend.application."""

from unittest.mock import MagicMock, patch

import gi
import pytest

gi.require_version("Adw", "1")
gi.require_version("Gtk", "4.0")

from gi.repository import Gtk  # noqa: E402


@pytest.fixture(autouse=True)
def _mock_resources() -> None:
    """Fixture to mock GTK resource loading for all tests."""
    with patch("gi.repository.Gio.resources_lookup_data") as mock_lookup:
        mock_lookup.return_value = b'<?xml version="1.0"?><interface></interface>'
        yield


@pytest.fixture(autouse=True)
def mock_dbus() -> None:
    """Fixture to mock the dbus module to avoid ModuleNotFoundError."""
    dbus_mock = MagicMock()
    dbus_mock.mainloop = MagicMock()
    dbus_mock.mainloop.glib = MagicMock()
    dbus_mock.mainloop.glib.DBusGMainLoop = MagicMock()
    with patch.dict(
        "sys.modules",
        {
            "dbus": dbus_mock,
            "dbus.mainloop": dbus_mock.mainloop,
            "dbus.mainloop.glib": dbus_mock.mainloop.glib,
        },
    ):
        yield


@pytest.fixture(autouse=True)
def mock_gtk_environment() -> None:
    """Fixture to mock GTK environment and prevent GObject type registration issues."""
    with patch("gi.repository.Adw.PreferencesDialog", new=MagicMock()), patch(
        "gi._gi.type_register", return_value=None,
    ), patch("gi.repository.Gtk.Template", return_value=lambda x: x):
        yield


@pytest.fixture
def mock_settings() -> MagicMock:
    """Fixture to mock GSettings."""
    with patch("gi.repository.Gio.Settings.new") as mock_settings_func:
        mock_settings_func.return_value = MagicMock()
        yield mock_settings_func


@pytest.fixture
def mock_db_connection() -> MagicMock:
    """Fixture to mock database connection."""
    with patch("sqlite3.connect") as mock_connect:
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn
        yield mock_conn


@pytest.fixture
def mock_template() -> None:
    """Fixture to mock GTK template loading."""
    with patch.object(Gtk.Widget, "init_template"):
        yield


@pytest.mark.usefixtures("mock_settings", "mock_db_connection")
def test_application_initialization() -> None:
    """Test application initialization with mocked dependencies."""
    from typetrace.frontend.application import Application

    app = Application("edu.ost.typetrace", "1.0")
    assert app.version == "1.0"
    assert app.settings is not None
    assert app.db_conn is not None


@pytest.mark.usefixtures("mock_settings", "mock_db_connection", "mock_template")
def test_application_do_activate() -> None:
    """Test application activation with various scenarios."""
    from typetrace.frontend.application import Application

    app = Application("edu.ost.typetrace", "1.0")
    with patch("typetrace.frontend.application.TypetraceWindow") as mock_window:
        app.do_activate()
        mock_window.assert_called_once()


@pytest.mark.usefixtures("mock_settings", "mock_db_connection")
def test_application_shutdown() -> None:
    """Test application shutdown behavior."""
    from typetrace.frontend.application import Application

    app = Application("edu.ost.typetrace", "1.0")
    app.do_shutdown()
    app.db_conn.close.assert_called_once()


@pytest.mark.usefixtures("mock_settings", "mock_db_connection")
def test_application_about_action() -> None:
    """Test about action of the application."""
    from typetrace.frontend.application import Application

    app = Application("edu.ost.typetrace", "1.0")
    with patch("typetrace.frontend.application.Adw.AboutDialog") as mock_about:
        app.on_about_action()
        mock_about.assert_called_once()
