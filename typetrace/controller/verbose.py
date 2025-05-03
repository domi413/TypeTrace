"""The verbose widget that displays keystroke data in text."""

import logging
from typing import Self

from gi.repository import Gio, Gtk

from typetrace.model.keystrokes import Keystroke, KeystrokeStore

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@Gtk.Template(resource_path="/edu/ost/typetrace/view/verbose.ui")
class Verbose(Gtk.Box):
    """The verbose widget that displays keystroke data in text."""

    __gtype_name__ = "Verbose"

    column_view = Gtk.Template.Child()

    def __init__(self: Self, keystroke_store: KeystrokeStore, **kwargs: object) -> None:
        """Initialize the Verbose widget.

        Args:
        ----
            keystroke_store: The store containing keystroke data.
            **kwargs: Additional arguments passed to the parent class.

        """
        super().__init__(**kwargs)
        self.keystroke_store = keystroke_store
        self.list_store = Gio.ListStore()
        self.sort_model = Gtk.SortListModel(model=self.list_store)
        self.selection_model = Gtk.SingleSelection(model=self.sort_model)
        self.column_view.set_model(self.selection_model)

        self._populate_list_store()
        self._setup_column_view()
        self.sort_model.set_sorter(self.column_view.get_sorter())

    def update(self: Self) -> None:
        """Update the list to reflect current data."""
        self._populate_list_store()
        logger.debug("List store has %d items", self.list_store.get_n_items())
        self.queue_draw()  # Forces the widget to redraw itself.

    def _populate_list_store(self: Self) -> None:
        """Populate the list store with keystroke data."""
        self.list_store.remove_all()
        keystrokes = self.keystroke_store.get_all_keystrokes()
        logger.debug("Found %d keystrokes", len(keystrokes))
        for keystroke in keystrokes:
            self.list_store.append(
                Keystroke(
                    scan_code=keystroke.scan_code,
                    count=keystroke.count,
                    key_name=keystroke.key_name,
                    date=keystroke.date,
                ),
            )

    def _setup_column_view(self: Self) -> None:
        """Set up the ColumnView with columns, data binding, and sorting."""
        columns = [
            ("Scan Code", self._bind_scan_code, "scan_code", "numeric"),
            ("Count", self._bind_count, "count", "numeric"),
            ("Key Name", self._bind_key_name, "key_name", "string"),
        ]

        for title, bind_func, prop_name, sort_type in columns:
            factory = Gtk.SignalListItemFactory()
            factory.connect("setup", self._factory_setup)
            factory.connect("bind", bind_func)

            column = Gtk.ColumnViewColumn(title=title, factory=factory, expand=True)
            expression = Gtk.PropertyExpression.new(Keystroke, None, prop_name)

            if sort_type == "numeric":
                sorter = Gtk.NumericSorter(expression=expression)
            elif sort_type == "string":
                sorter = Gtk.StringSorter(expression=expression)
            else:
                error_msg = "Unknown sort type: " + sort_type
                raise ValueError(error_msg)

            column.set_sorter(sorter)
            self.column_view.append_column(column)

        self.column_view.sort_by_column(
            self.column_view.get_columns()[0],
            Gtk.SortType.ASCENDING,
        )

    def _factory_setup(
        self: Self, _: Gtk.SignalListItemFactory, list_item: Gtk.ListItem,
    ) -> None:
        label = Gtk.Label()
        label.set_halign(Gtk.Align.START)
        list_item.set_child(label)

    def _bind_scan_code(
        self: Self, _: Gtk.SignalListItemFactory, list_item: Gtk.ListItem,
    ) -> None:
        keystroke = list_item.get_item()
        list_item.get_child().set_text(str(keystroke.scan_code))

    def _bind_count(
        self: Self, _: Gtk.SignalListItemFactory, list_item: Gtk.ListItem,
    ) -> None:
        keystroke = list_item.get_item()
        list_item.get_child().set_text(str(keystroke.count))

    def _bind_key_name(
        self: Self, _: Gtk.SignalListItemFactory, list_item: Gtk.ListItem,
    ) -> None:
        keystroke = list_item.get_item()
        list_item.get_child().set_text(keystroke.key_name)
