"""This extension provides a template context menu for nautilus"""
import gettext
from pathlib import Path
import gi

from gi.repository import Gtk
from gi.repository.Gdk import WindowTypeHint
from gi.repository import Nautilus, GObject
import locale
from odf import style
from odf.opendocument import (
    OpenDocumentText,
    OpenDocumentPresentation,
    OpenDocumentSpreadsheet,
)


gi.require_version("Gtk", "3.0")
t = gettext.translation("nautilus-templates", fallback=True)
_ = t.gettext


class TemplateMenuProvider(GObject.GObject, Nautilus.MenuProvider):
    """This class provides the menu entry for nautilus"""

    window = None

    def __init__(self):
        pass

    def get_file_items(self, window, files):
        pass

    def get_background_items(self, window, file):
        self.window = window
        menuitem = Nautilus.MenuItem(
            name="TemplateMenuProvider::Templates",
            label=_("Templates"),
            tip="",
            icon="",
        )

        submenu = Nautilus.Menu()
        item_odt = Nautilus.MenuItem(
            name="TemplateMenuProvider::ODT", label=_("New Document"), tip="", icon=""
        )
        item_odt.connect("activate", self.create_odt, file)

        item_ods = Nautilus.MenuItem(
            name="TemplateMenuProvider::ODS",
            label=_("New Spreadsheet"),
            tip="",
            icon="",
        )
        item_ods.connect("activate", self.create_ods, file)

        item_odp = Nautilus.MenuItem(
            name="TemplateMenuProvider::ODP",
            label=_("New Presentation"),
            tip="",
            icon="",
        )
        item_odp.connect("activate", self.create_odp, file)

        item_txt = Nautilus.MenuItem(
            name="TemplateMenuProvider::TXT", label=_("New Textfile"), tip="", icon=""
        )
        item_txt.connect("activate", self.create_txt, file)

        submenu.append_item(item_odt)
        submenu.append_item(item_ods)
        submenu.append_item(item_odp)
        submenu.append_item(item_txt)
        menuitem.set_submenu(submenu)

        return (menuitem,)

    def create_odt(self, menu, file):
        """Handler for creating new odt files."""
        default_name = _("New Document")
        base_path = file.get_location().get_path()
        ext = "odt"
        name = find_empty_name(base_path, default_name, ext)

        def create_function(full_path):
            textdoc = OpenDocumentText()
            textdoc.styles.addElement(self.build_default_style())
            textdoc.save(full_path)

        CreateWindow(default_name, base_path, name, ext, create_function, self.window)
        return True

    def create_ods(self, menu, file):
        """Handler for creating new ods files."""
        default_name = _("New Spreadsheet")
        base_path = file.get_location().get_path()
        ext = "ods"
        name = find_empty_name(base_path, default_name, ext)

        def create_function(full_path):
            textdoc = OpenDocumentSpreadsheet()
            textdoc.styles.addElement(self.build_default_style())
            textdoc.save(full_path)

        CreateWindow(default_name, base_path, name, ext, create_function, self.window)
        return True

    def create_odp(self, menu, file):
        """Handler for creating new odp files."""
        default_name = _("New Presentation")
        base_path = file.get_location().get_path()
        ext = "odp"
        name = find_empty_name(base_path, default_name, ext)

        def create_function(full_path):
            textdoc = OpenDocumentPresentation()
            textdoc.styles.addElement(self.build_default_style())
            textdoc.save(full_path)

        CreateWindow(default_name, base_path, name, ext, create_function, self.window)
        return True

    def create_txt(self, menu, file):
        """Handler for creating new txt files."""
        base_path = file.get_location().get_path()
        ext = "txt"
        name = find_empty_name(base_path, _("New Textfile"), ext)

        def create_function(full_path):
            Path(full_path).touch()

        CreateWindow(
            _("New Textfile"), base_path, name, ext, create_function, self.window
        )
        return True

    def build_default_style(self):
        """Creates default style for Libreoffice Documents"""
        # Add the right language to the template
        language_code = locale.getlocale()[0][:2]
        country_code = locale.getlocale()[0][-2:]
        default_style = style.DefaultStyle(family="paragraph")
        default_style.addElement(
            style.TextProperties(language=language_code, country=country_code)
        )
        return default_style


class CreateWindow(Gtk.Window):
    """This class provides a window to enter a file name and create that file"""

    base_path = None  # Path of the directory
    default_name = None  # Default Name of the file (already translated)
    ext = None  # Extension of the file
    create_button = None  # Holds the create button in HeaderBar
    input = None  # Holds input field
    create_function = None  # This function is called to create the new file

    def __init__(
        self, title, base_path, default_name, ext, create_function, parent=None
    ):
        # Init window
        Gtk.Window.__init__(self, title=title + " (." + ext + ")")
        self.set_border_width(10)
        self.set_default_size(400, 1)
        self.set_deletable(False)
        self.set_resizable(False)
        self.set_type_hint(WindowTypeHint.DIALOG)
        self.set_modal(True)
        self.set_transient_for(parent)
        self.set_position(Gtk.WindowPosition.CENTER_ON_PARENT)

        self.base_path = base_path
        self.default_name = default_name
        self.ext = ext
        self.create_function = create_function

        # Create top bar
        hb = Gtk.HeaderBar()
        hb.set_show_close_button(False)
        hb.props.title = title + " (." + ext + ")"
        self.set_titlebar(hb)

        cancel_button = Gtk.Button()
        cancel_button.set_label(_("Cancel"))
        cancel_button.connect("clicked", self.cancel_clicked)
        hb.pack_start(cancel_button)

        create_button = Gtk.Button()
        self.create_button = create_button
        create_button.set_label(_("Create"))
        create_button.connect("clicked", self.create_clicked)

        hb.pack_end(create_button)

        # Create text input
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)

        file_name = Gtk.Label.new(_("Filename"))
        file_name_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        file_name_box.add(file_name)

        name_input = Gtk.Entry()
        name_input.connect("changed", self.toggle_create_button)
        name_input.connect("activate", self.input_enter)
        name_input.set_text(default_name)
        self.input = name_input

        box.add(file_name_box)
        box.add(name_input)
        self.add(box)

        self.show_all()

    def toggle_create_button(self, data):
        """Enable or disable create_button based on the current name."""
        file_name = data.get_text()
        file_not_exists = not file_exists(self.base_path, file_name, self.ext)
        self.create_button.set_sensitive(file_not_exists)
        if data.get_text_length() == 0:
            self.create_button.set_sensitive(False)
        return True

    def input_enter(self, data):
        """Handle if enter is pressed in input field."""
        file_name = data.get_text()
        if (
            not file_exists(self.base_path, file_name, self.ext)
            and data.get_text_length() != 0
        ):
            self.create_function(
                self.base_path + "/" + self.input.get_text() + "." + self.ext
            )
            self.destroy()
        return True

    def cancel_clicked(self, button):
        """Handler for cancel_button."""
        self.destroy()
        return True

    def create_clicked(self, button):
        """Handler for create_button."""
        self.create_function(
            self.base_path + "/" + self.input.get_text() + "." + self.ext
        )
        self.destroy()
        return True


def file_exists(path, filename, ext):
    """Check if a file exists"""
    path = Path(path + "/" + filename + "." + ext)
    return path.exists()


def find_empty_name(path, default_name, ext):
    """Finds the next empty name. If the default is used we add (1) etc. to the name"""
    real_path = Path(path + "/" + default_name + "." + ext)
    name = default_name
    counter = 1
    while real_path.exists():
        name = default_name + " (" + str(counter) + ")"
        real_path = Path(path + "/" + name + "." + ext)
        counter = counter + 1
    return name
