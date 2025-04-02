import pytest
import sys
from unittest.mock import MagicMock, patch


# Fixture to mock gi.repository for all tests
@pytest.fixture(autouse=True)
def mock_gi(mocker):
    """Mock gi.repository to allow tests to run without PyGObject dependencies."""
    mock_repository = MagicMock()
    with patch.dict(sys.modules, {"gi.repository": mock_repository}):

        class MockGtkBox:
            def __init__(self, *args, **kwargs):
                pass

        mock_repository.Gtk = MagicMock()
        mock_repository.Gtk.Box = MockGtkBox
        mock_repository.Gtk.Label = MagicMock()
        mock_repository.Gtk.ColumnViewColumn = MagicMock()
        mock_repository.Gtk.SignalListItemFactory = MagicMock()
        mock_repository.Gtk.PropertyExpression = MagicMock()
        mock_repository.Gtk.NumericSorter = MagicMock()
        mock_repository.Gtk.StringSorter = MagicMock()
        mock_repository.Gtk.SortType = MagicMock(ASCENDING="ASCENDING")
        mock_repository.Gtk.Align = MagicMock(START="START")

        mock_repository.Gio = MagicMock()
        mock_repository.Gio.ListStore = MagicMock()

        class MockGObject:
            def __init__(self, *args, **kwargs):
                pass

        mock_repository.GObject = MagicMock()
        mock_repository.GObject.Object = MockGObject
        mock_repository.GObject.Property = lambda *args, **kwargs: lambda x: x

        class MockTemplate:
            def __init__(self, *args, **kwargs):
                pass

            def __call__(self, cls):
                return cls

            @staticmethod
            def Child(name):
                if name == "column_view":
                    mock_column_view = MagicMock()
                    mock_column_view.get_columns.return_value = [MagicMock()]
                    return mock_column_view
                return MagicMock()

        mock_repository.Gtk.Template = MockTemplate

        def create_sort_list_model(*args, **kwargs):
            model = kwargs.get("model", MagicMock())
            mock = MagicMock()
            mock.model = model
            return mock

        def create_single_selection(*args, **kwargs):
            model = kwargs.get("model", MagicMock())
            mock = MagicMock()
            mock.model = model
            return mock

        mock_repository.Gtk.SortListModel = create_sort_list_model
        mock_repository.Gtk.SingleSelection = create_single_selection

        yield mock_repository


def test_verbose_init(mocker, mock_gi):
    """Test the initialization of the Verbose widget."""
    from typetrace.model.keystrokes import KeystrokeStore
    from typetrace.controller.verbose import Verbose

    # Mock KeystrokeStore
    mock_store = mocker.Mock(spec=KeystrokeStore)
    mock_store.get_all_keystrokes.return_value = []

    # Create Verbose instance
    verbose = Verbose(keystroke_store=mock_store)

    # Verify attributes and setup
    assert verbose.keystroke_store == mock_store
    assert isinstance(verbose.list_store, mock_gi.Gio.ListStore.return_value.__class__)
    assert verbose.sort_model.model == verbose.list_store
    assert verbose.selection_model.model == verbose.sort_model
    verbose.column_view.set_model.assert_called_with(verbose.selection_model)
    verbose.sort_model.set_sorter.assert_called_with(
        verbose.column_view.get_sorter.return_value
    )


def test_populate_list_store(mocker, mock_gi):
    """Test populating the list store with keystroke data."""
    from typetrace.model.keystrokes import Keystroke, KeystrokeStore
    from typetrace.controller.verbose import Verbose

    # Mock KeystrokeStore with sample data
    mock_store = mocker.Mock(spec=KeystrokeStore)
    mock_keystroke1 = mocker.Mock(spec=Keystroke, scan_code=16, count=5, key_name="Q")
    mock_keystroke2 = mocker.Mock(spec=Keystroke, scan_code=17, count=10, key_name="W")
    mock_store.get_all_keystrokes.return_value = [mock_keystroke1, mock_keystroke2]

    # Create Verbose instance
    verbose = Verbose(keystroke_store=mock_store)

    # Reset list_store to clear any initial calls from __init__
    verbose.list_store = mocker.Mock()
    verbose._populate_list_store()

    # Verify the list store is populated with keystrokes
    assert verbose.list_store.append.call_count == 2
    calls = verbose.list_store.append.call_args_list
    assert calls[0][0][0].scan_code == 16
    assert calls[0][0][0].count == 5
    assert calls[0][0][0].key_name == "Q"
    assert calls[1][0][0].scan_code == 17
    assert calls[1][0][0].count == 10
    assert calls[1][0][0].key_name == "W"
