from gi.repository import Adw
from gi.repository import Gtk


@Gtk.Template(resource_path="/edu/ost/typetrace/window.ui")
class TypetraceWindow(Adw.ApplicationWindow):
    __gtype_name__ = "TypetraceWindow"

    label = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
