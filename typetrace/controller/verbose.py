"""The verbose widget that displays keystroke data in text."""

from gi.repository import Gio, Gtk

from typetrace.model.keystrokes import Keystroke, KeystrokeStore


@Gtk.Template(resource_path="/edu/ost/typetrace/view/verbose.ui")
class Verbose(Gtk.Box):
    """The verbose widget that displays keystroke data in text."""

    __gtype_name__ = "Verbose"

    column_view = Gtk.Template.Child("column_view")

    def __init__(self, keystroke_store: KeystrokeStore, **kwargs) -> None:
        """Initialize the verbose widget with keystroke data.

        Args:
            keystroke_store: Access to keystrokes models
            **kwargs: Keyword arguments passed to the parent constructor

        """
        super().__init__(**kwargs)
        self.keystroke_store = keystroke_store
        self.list_store = Gio.ListStore()
        self.sort_model = Gtk.SortListModel(model=self.list_store)
        self.selection_model = Gtk.SingleSelection(model=self.sort_model)
        self.column_view.set_model(self.selection_model)

        self._populate_list_store()
        self._setup_column_view()

        # Set the sort_model's sorter to the column_view's sorter
        self.sort_model.set_sorter(self.column_view.get_sorter())

    def _populate_list_store(self) -> None:
        """Populate the list store with keystroke data."""
        for keystroke in self.keystroke_store.get_all_keystrokes():
            self.list_store.append(
                Keystroke(
                    scan_code=keystroke.scan_code,
                    count=keystroke.count,
                    key_name=keystroke.key_name,
                ),
            )

    def _setup_column_view(self) -> None:
        """Set up the ColumnView with columns, data binding, and sorting."""
        columns = [
            ("Scan Code", self._bind_scan_code, "scan_code", "numeric"),
            ("Count", self._bind_count, "count", "numeric"),
            ("Key Name", self._bind_key_name, "key_name", "string"),
        ]

        # Create and add all columns with sorters
        for title, bind_func, prop_name, sort_type in columns:
            # Set up the factory for rendering items
            factory = Gtk.SignalListItemFactory()
            factory.connect("setup", self._factory_setup)
            factory.connect("bind", bind_func)

            column = Gtk.ColumnViewColumn(title=title, factory=factory, expand=True)

            # Create and set the sorter based on the sort type
            expression = Gtk.PropertyExpression.new(Keystroke, None, prop_name)
            if sort_type == "numeric":
                sorter = Gtk.NumericSorter(expression=expression)
            elif sort_type == "string":
                sorter = Gtk.StringSorter(expression=expression)
            else:
                raise ValueError
            column.set_sorter(sorter)

            self.column_view.append_column(column)

        # Set an initial sort order
        self.column_view.sort_by_column(
            self.column_view.get_columns()[1],
            Gtk.SortType.DESCENDING,
        )

    def _factory_setup(
        self,
        factory: Gtk.SignalListItemFactory,
        list_item: Gtk.ListItem,
    ) -> None:
        """Set up a label widget for each list item."""
        label = Gtk.Label()
        label.set_halign(Gtk.Align.START)
        list_item.set_child(label)

    def _bind_scan_code(
        self,
        factory: Gtk.SignalListItemFactory,
        list_item: Gtk.ListItem,
    ) -> None:
        """Bind scan_code property to the label."""
        keystroke = list_item.get_item()
        list_item.get_child().set_text(str(keystroke.scan_code))

    def _bind_count(
        self,
        factory: Gtk.SignalListItemFactory,
        list_item: Gtk.ListItem,
    ) -> None:
        """Bind count property to the label."""
        keystroke = list_item.get_item()
        list_item.get_child().set_text(str(keystroke.count))

    def _bind_key_name(
        self,
        factory: Gtk.SignalListItemFactory,
        list_item: Gtk.ListItem,
    ) -> None:
        """Bind key_name property to the label."""
        keystroke = list_item.get_item()
        list_item.get_child().set_text(keystroke.key_name)
