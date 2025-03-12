"""The heatmap widget that displays a keyboard."""

from gi.repository import Gtk


@Gtk.Template(resource_path="/edu/ost/typetrace/view/heatmap.ui")
class Heatmap(Gtk.Box):
    """The heatmap widget that displays a keyboard."""

    __gtype_name__ = "Heatmap"

    def __init__(self, **kwargs) -> None:
        """Initialize the heatmap widget.

        Args:
            **kwargs: Keyword arguments passed to the parent constructor

        """
        super().__init__(**kwargs)
