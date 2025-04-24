import pytest
from unittest.mock import MagicMock

# Import mocks (ensures sys.modules is correctly set)
import tests.unit.mocks  # noqa: F401

# Import project modules
from typetrace.model.keystrokes import Keystroke, KeystrokeStore
from typetrace.controller.verbose import Verbose


# Fixtures
@pytest.fixture
def keystroke_store():
    store = MagicMock(spec=KeystrokeStore)
    store.get_all_keystrokes.return_value = []
    return store


@pytest.fixture
def verbose_widget(keystroke_store):
    return Verbose(keystroke_store=keystroke_store)


# Tests
class TestVerbose:
    def test_populate_list_store_empty(self, verbose_widget, keystroke_store):
        verbose_widget.list_store.remove_all()
        keystroke_store.get_all_keystrokes.return_value = []
        verbose_widget._populate_list_store()
        assert verbose_widget.list_store.get_n_items() == 0

    def test_populate_list_store_with_data(self, verbose_widget, keystroke_store):
        mock_keystrokes = [
            Keystroke(scan_code=30, count=5, key_name="KEY_A", date=""),
            Keystroke(scan_code=48, count=3, key_name="KEY_B", date=""),
        ]
        keystroke_store.get_all_keystrokes.return_value = mock_keystrokes
        verbose_widget.list_store.remove_all()
        verbose_widget.list_store.get_item_mocks = [
            MagicMock(scan_code=30, count=5, key_name="A"),
            MagicMock(scan_code=48, count=3, key_name="B"),
        ]
        verbose_widget._populate_list_store()
        assert verbose_widget.list_store.get_n_items() == 2

    def test_populate_list_store_with_invalid_data(
        self, verbose_widget, keystroke_store
    ):
        mock_keystrokes = [Keystroke(scan_code=-1, count=-5, key_name="", date="")]
        keystroke_store.get_all_keystrokes.return_value = mock_keystrokes
        verbose_widget.list_store.remove_all()
        verbose_widget.list_store.get_item_mocks = [
            MagicMock(scan_code=-1, count=-5, key_name="")
        ]
        verbose_widget._populate_list_store()
        assert verbose_widget.list_store.get_n_items() == 1

    def test_populate_list_store_with_none_values(
        self, verbose_widget, keystroke_store
    ):
        mock_keystrokes = [Keystroke(scan_code=0, count=0, key_name="", date="")]
        keystroke_store.get_all_keystrokes.return_value = mock_keystrokes
        verbose_widget.list_store.remove_all()
        verbose_widget.list_store.get_item_mocks = [
            MagicMock(scan_code=0, count=0, key_name="")
        ]
        verbose_widget._populate_list_store()
        assert verbose_widget.list_store.get_n_items() == 1
