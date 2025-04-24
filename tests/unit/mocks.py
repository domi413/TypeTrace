import sys
import types
from unittest.mock import MagicMock

gi_mock = types.ModuleType("gi")
gi_repository_mock = types.ModuleType("gi.repository")
gtk_mock = types.ModuleType("gi.repository.Gtk")
adw_mock = types.ModuleType("gi.repository.Adw")
gio_mock = types.ModuleType("gi.repository.Gio")
glib_mock = types.ModuleType("gi.repository.GLib")
gdk_mock = types.ModuleType("gi.repository.Gdk")
gobject_mock = types.ModuleType("gi.repository.GObject")

gi_mock.require_version = MagicMock()

gtk_mock.Template = lambda resource_path=None: (lambda cls: cls)
gtk_mock.Template.Child = MagicMock()
gtk_mock.Box = type("Box", (), {})
gtk_mock.SortListModel = type(
    "SortListModel",
    (),
    {"__init__": lambda self, model=None: None, "set_sorter": MagicMock()},
)
gtk_mock.SingleSelection = type(
    "SingleSelection", (), {"__init__": lambda self, model=None: None}
)
gtk_mock.ColumnView = type(
    "ColumnView",
    (),
    {
        "set_model": MagicMock(),
        "append_column": MagicMock(),
        "sort_by_column": MagicMock(),
        "get_sorter": MagicMock(),
    },
)
gtk_mock.SignalListItemFactory = type(
    "SignalListItemFactory", (), {"connect": MagicMock()}
)
gtk_mock.ListItem = type("ListItem", (), {"set_child": MagicMock()})
gtk_mock.ColumnViewColumn = type(
    "ColumnViewColumn",
    (),
    {
        "__init__": lambda self, title=None, factory=None, expand=None: None,
        "set_sorter": MagicMock(),
    },
)
gtk_mock.PropertyExpression = type(
    "PropertyExpression", (), {"new": MagicMock(return_value=MagicMock())}
)
gtk_mock.NumericSorter = type(
    "NumericSorter", (), {"__init__": lambda self, expression=None: None}
)
gtk_mock.StringSorter = type(
    "StringSorter", (), {"__init__": lambda self, expression=None: None}
)
gtk_mock.SortType = type("SortType", (), {"ASCENDING": 0})


gtk_mock.CssProvider = type("CssProvider", (), {})
gtk_mock.StyleContext = type(
    "StyleContext", (), {"add_provider_for_display": MagicMock()}
)
gtk_mock.STYLE_PROVIDER_PRIORITY_APPLICATION = 600
gtk_mock.Orientation = type("Orientation", (), {"HORIZONTAL": 0})
gtk_mock.StackSwitcher = MagicMock()
gtk_mock.Stack = MagicMock()


adw_mock.ApplicationWindow = type("ApplicationWindow", (), {})


class MockListStore:
    def __init__(self):
        self.items = []
        self.get_item_mocks = []

    def remove_all(self):
        self.items = []
        self.get_item_mocks = []

    def append(self, item):
        self.items.append(item)

    def get_n_items(self):
        return len(self.items)

    def get_item(self, index):
        return (
            self.get_item_mocks[index]
            if index < len(self.get_item_mocks)
            else self.items[index]
        )


gio_mock.ListStore = MockListStore
gio_mock.Settings = type("Settings", (), {})

gdk_mock.Display = type(
    "Display", (), {"get_default": MagicMock(return_value=MagicMock())}
)

glib_mock.idle_add = lambda func: func()

gobject_mock.Object = type("Object", (), {})
gobject_mock.Property = MagicMock()

sys.modules["gi"] = gi_mock
sys.modules["gi.repository"] = gi_repository_mock
sys.modules["gi.repository.Gtk"] = gtk_mock
sys.modules["gi.repository.Adw"] = adw_mock
sys.modules["gi.repository.Gio"] = gio_mock
sys.modules["gi.repository.GLib"] = glib_mock
sys.modules["gi.repository.Gdk"] = gdk_mock
sys.modules["gi.repository.GObject"] = gobject_mock
