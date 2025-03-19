"""The verbose widget that displays keystroke data in text."""

from gi.repository import Gio, Gtk

from typetrace.model.keystrokes import Keystroke, KeystrokesModel


@Gtk.Template(resource_path="/edu/ost/typetrace/view/verbose.ui")
class Verbose(Gtk.Box):
    """The verbose widget that displays keystroke data in text."""

    __gtype_name__ = "Verbose"

    column_view = Gtk.Template.Child("column_view")

    def __init__(self, model : KeystrokesModel, **kwargs) -> None:
        """Initialize the verbose widget.

        Args:
            model: Access to keystrokes models
            **kwargs: Keyword arguments passed to the parent constructor

        """
        super().__init__(**kwargs)
        self.model = model
        self.list_store = Gio.ListStore()

        self.populate_list_store()
        self.setup_column_view()

    def populate_list_store(self) -> None:
        """Populate the list box with keystroke data."""
        keystrokes = self.model.get_all_keystrokes()

        for keystroke in keystrokes:
            self.list_store.append(
                Keystroke(
                    scan_code=keystroke.scan_code,
                    count=keystroke.count,
                    key_name=keystroke.key_name,
                ),
            )

    def setup_column_view(self) -> None:
        """Set up the ColumnView with columns and data binding."""
        # Create a selection model for the ColumnView
        selection_model = Gtk.SingleSelection(model=self.list_store)
        self.column_view.set_model(selection_model)

        # Define factories for rendering each column
        scan_code_factory = Gtk.SignalListItemFactory()
        count_factory = Gtk.SignalListItemFactory()
        key_name_factory = Gtk.SignalListItemFactory()

        # Connect the setup and bind signals for each factory
        scan_code_factory.connect("setup", self.on_factory_setup)
        scan_code_factory.connect("bind", self.on_scan_code_bind)
        count_factory.connect("setup", self.on_factory_setup)
        count_factory.connect("bind", self.on_count_bind)
        key_name_factory.connect("setup", self.on_factory_setup)
        key_name_factory.connect("bind", self.on_key_name_bind)

        # Create columns and assign factories
        scan_code_column = Gtk.ColumnViewColumn(
            title="Scan Code",
            factory=scan_code_factory,
            expand=True,
        )
        count_column = Gtk.ColumnViewColumn(
            title="Count",
            factory=count_factory,
            expand=True,
        )
        key_name_column = Gtk.ColumnViewColumn(
            title="Key Name",
            factory=key_name_factory,
            expand=True,
        )

        # Add columns to the ColumnView
        self.column_view.append_column(scan_code_column)
        self.column_view.append_column(count_column)
        self.column_view.append_column(key_name_column)

    def on_factory_setup(
        self, factory: Gtk.SignalListItemFactory, list_item: Gtk.ListItem,  # noqa: ARG002
    ) -> None:
        """Set up the widget for each list item (called once per row)."""
        label = Gtk.Label()
        label.set_halign(Gtk.Align.START)
        list_item.set_child(label)

    def on_scan_code_bind(
        self, factory: Gtk.SignalListItemFactory, list_item: Gtk.ListItem,  # noqa: ARG002
    ) -> None:
        """Bind the scan_code property to the label."""
        keystroke = list_item.get_item()
        label = list_item.get_child()
        label.set_text(str(keystroke.scan_code))

    def on_count_bind(
        self, factory: Gtk.SignalListItemFactory, list_item: Gtk.ListItem,  # noqa: ARG002
    ) -> None:
        """Bind the count property to the label."""
        keystroke = list_item.get_item()
        label = list_item.get_child()
        label.set_text(str(keystroke.count))

    def on_key_name_bind(
        self, factory: Gtk.SignalListItemFactory, list_item: Gtk.ListItem,  # noqa: ARG002
    ) -> None:
        """Bind the key_name property to the label."""
        keystroke = list_item.get_item()
        label = list_item.get_child()
        label.set_text(keystroke.key_name)
