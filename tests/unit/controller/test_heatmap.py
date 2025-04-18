import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path
import gi
gi.require_version('Gdk', '4.0')
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, Gdk, GObject, Gio
import warnings  # Import warnings module to suppress DeprecationWarning

from typetrace.model.keystrokes import Keystroke, KeystrokeStore
from typetrace.model.layouts import KEYBOARD_LAYOUTS

# Custom mock for Gtk.Template to support Child
class MockTemplate:
    def __init__(self, *args, **kwargs):
        self.resource_path = kwargs.get('resource_path')
    def __call__(self, cls):
        return cls
    @staticmethod
    def Child():
        return MagicMock()  # Mock template child

# Mock Gtk.Template globally
with patch.object(Gtk, "Template", MockTemplate):
    from heatmap import Heatmap

# Register GResource programmatically
def register_gresource():
    resource_path = Path("~/TypeTrace/typetrace.gresource")
    if resource_path.exists():
        resource = Gio.Resource.load(str(resource_path))
        resource._register()

class TestHeatmap:
    """Test suite for Heatmap class."""

    @pytest.fixture(autouse=True)
    def setup_gresource(self):
        """Register GResource before each test and suppress DeprecationWarning."""
        # Suppress DeprecationWarning for Gdk.RGBA initialization
        warnings.filterwarnings("ignore", category=DeprecationWarning, module="heatmap")
        register_gresource()

    @pytest.fixture
    def mock_keystroke_store(self):
        """Provide a mocked KeystrokeStore."""
        store = MagicMock(spec=KeystrokeStore)
        keystroke1 = MagicMock(spec=Keystroke)
        keystroke1.scan_code = 1
        keystroke1.count = 10
        keystroke1.key_name = "A"
        keystroke1.get_property.side_effect = lambda prop: {
            "scan_code": 1,
            "count": 10,
            "key_name": "A"
        }[prop]
        
        keystroke2 = MagicMock(spec=Keystroke)
        keystroke2.scan_code = 2
        keystroke2.count = 5
        keystroke2.key_name = "B"
        keystroke2.get_property.side_effect = lambda prop: {
            "scan_code": 2,
            "count": 5,
            "key_name": "B"
        }[prop]
        
        store.get_all_keystrokes.return_value = [keystroke1, keystroke2]
        store.get_highest_count.return_value = 10
        return store

    @pytest.fixture
    def mock_keyboard_layouts(self):
        """Mock KEYBOARD_LAYOUTS for testing."""
        with patch("typetrace.model.layouts.KEYBOARD_LAYOUTS", {
            "en_US": [
                [(1, "A"), (2, "B")],  # Row 1
                [(3, "C"), (4, "Space")],  # Row 2
            ]
        }):
            yield

    @pytest.fixture
    def heatmap(self, mock_keystroke_store, mock_keyboard_layouts):
        """Provide a Heatmap instance with mocked dependencies."""
        with patch.object(Gtk, "Template", MockTemplate):
            with patch.object(Gtk, "CssProvider", autospec=True) as mock_css_provider, \
                 patch.object(Gtk.StyleContext, "add_provider_for_display"), \
                 patch.object(Gtk, "Box", autospec=True), \
                 patch.object(Gtk, "Label", autospec=True), \
                 patch.object(Gtk, "Button", autospec=True), \
                 patch.object(Gtk, "CenterBox", autospec=True):
                heatmap = Heatmap(
                    keystroke_store=mock_keystroke_store,
                    layout="en_US",
                    beg_color=(0.0, 0.0, 1.0),
                    end_color=(1.0, 0.0, 0.0)
                )
                yield heatmap

    def test_init(self, mock_keystroke_store, mock_keyboard_layouts):
        """Test Heatmap initialization."""
        with patch.object(Gtk, "Template", MockTemplate):
            with patch.object(Gtk, "CssProvider", autospec=True) as mock_css_provider, \
                 patch.object(Gtk.StyleContext, "add_provider_for_display") as mock_add_provider, \
                 patch.object(Gtk, "Box", autospec=True), \
                 patch.object(Gtk, "Button", autospec=True):
                heatmap = Heatmap(
                    keystroke_store=mock_keystroke_store,
                    layout="en_US",
                    beg_color=(0.0, 0.0, 1.0),
                    end_color=(1.0, 1.0, 0.0)
                )
                assert heatmap.keystroke_store == mock_keystroke_store
                assert heatmap.layout == "en_US"
                assert heatmap.beg_color == (0.0, 0.0, 1.0)
                assert heatmap.end_color == (1.0, 1.0, 0.0)
                assert isinstance(heatmap.key_widgets, dict)
                assert heatmap.css_provider == mock_css_provider.return_value
                mock_add_provider.assert_called_once()
                assert heatmap.refresh_button.connect.called

    def test_update_colors_zero_highest_count(self, heatmap, mock_keystroke_store):
        """Test updating colors when highest count is zero."""
        mock_keystroke_store.get_highest_count.return_value = 0
        with patch.object(heatmap, "css_provider") as mock_css_provider:
            heatmap._update_colors()
            mock_css_provider.load_from_string.assert_not_called()

    def test_update_colors_missing_scancode(self, heatmap, mock_keystroke_store):
        """Test updating colors with a scancode not in key_widgets."""
        mock_keystroke = MagicMock(spec=Keystroke)
        mock_keystroke.scan_code = 999
        mock_keystroke.count = 10
        mock_keystroke.key_name = "X"
        mock_keystroke.get_property.side_effect = lambda prop: {
            "scan_code": 999,
            "count": 10,
            "key_name": "X"
        }[prop]
        mock_keystroke_store.get_all_keystrokes.return_value = [mock_keystroke]
        with patch.object(heatmap, "css_provider") as mock_css_provider:
            heatmap._update_colors()
            mock_css_provider.load_from_string.assert_called_once()
            css_string = mock_css_provider.load_from_string.call_args[0][0]
            assert ".gradient-bar" in css_string
            assert "scancode-999" not in css_string  # Missing scancode ignored

    def test_invalid_layout(self, mock_keystroke_store):
        """Test initialization with invalid layout."""
        with patch("typetrace.model.layouts.KEYBOARD_LAYOUTS", {}):
            with patch.object(Gtk, "Template", MockTemplate):
                with pytest.raises(KeyError):
                    Heatmap(keystroke_store=mock_keystroke_store, layout="invalid")