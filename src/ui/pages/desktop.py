# SPDX-License-Identifier: GPL-3.0-or-later

from gi.repository import Gdk, GObject, Gtk

from .config import config
from .desktop_provider import desktop_provider
from .translator import config_gettext as _
from .translations import translate_widgets


@Gtk.Template(resource_path='/org/shani/os-installer/ui/widgets/desktop_entry.ui')
class DesktopEntry(Gtk.Button):
    __gtype_name__ = __qualname__

    is_selected = GObject.Property(type=bool, default=False)

    def __init__(self, desktop, **kwargs):
        self.desktop = desktop
        self._name = _(self.desktop.name)
        super().__init__(**kwargs)

    @GObject.Property(type=Gdk.Texture)
    def texture(self):
        return self.desktop.texture

    @GObject.Property(type=bool, default=False)
    def with_texture(self):
        return self.desktop.texture != None

    @GObject.Property(type=str)
    def name(self):
        return self._name


@Gtk.Template(resource_path='/org/shani/os-installer/ui/pages/desktop.ui')
class DesktopPage(Gtk.Box):
    __gtype_name__ = __qualname__

    grid = Gtk.Template.Child()
    continue_button = Gtk.Template.Child()
    selected_description = Gtk.Template.Child()
    selected_image = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        translate_widgets(self.continue_button)

        self.button_label = self.continue_button.get_label()
        self.selected_entry = None

        number = 0
        for desktop in desktop_provider.get_desktops():
            entry = DesktopEntry(desktop)
            entry.connect('clicked', self._desktop_activated)
            if number == 0:
                self._set_selected_desktop(entry)
            self.grid.attach(entry, number % 3, int(number/3), 1, 1)
            number += 1

    def _set_selected_desktop(self, entry):
        desktop = entry.desktop
        self.continue_button.set_label(self.button_label.format(desktop.name))
        if desktop.texture:
            self.selected_image.set_visible(True)
            self.selected_image.set_paintable(desktop.texture)
        else:
            self.selected_image.set_visible(False)

        description = _(desktop.description) if desktop.description else ''
        self.selected_description.set_label(description)

        if self.selected_entry:
            self.selected_entry.remove_css_class('selected-card')
            self.selected_entry.set_property("is_selected", False)
            self.selected_entry.remove_css_class('suggested-action')
        entry.set_property("is_selected", True)
        entry.add_css_class('selected-card')
        entry.add_css_class('suggested-action')
        self.selected_entry = entry

        config.set('desktop_chosen', (desktop.keyword, desktop.name))

    ### callbacks ###

    def _desktop_activated(self, button):
        self._set_selected_desktop(button)
