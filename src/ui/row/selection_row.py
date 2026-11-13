# SPDX-License-Identifier: GPL-3.0-or-later

from gi.repository import Adw, Gtk

from .translator import config_gettext as _


@Gtk.Template(resource_path='/org/shani/os-installer/ui/row/multi_selection_row.ui')
class MultiSelectionRow(Adw.ComboRow):
    __gtype_name__ = __qualname__

    icon = Gtk.Template.Child()
    list = Gtk.Template.Child()

    def __init__(self, choice, **kwargs):
        super().__init__(**kwargs)

        self.choice = choice

        self.set_title(_(choice.name))
        if choice.description:
            self.set_subtitle(_(choice.description))
        if choice.icon_path:
            self.icon.set_from_file(str(choice.icon_path))
        else:
            self.icon.set_from_icon_name(choice.icon_name)
            self.icon.set_icon_size(Gtk.IconSize.LARGE)

        self.list.splice(0, 0, [_(option.display) for option in choice.options])
        self.set_model(self.list)
        self.set_selected(self.choice.options.index(self.choice.state))

    def get_chosen_option(self):
        return self.choice.options[self.get_selected()]

    def update_choice(self):
        self.choice.state = self.choice.options[self.get_selected()]


@Gtk.Template(resource_path='/org/shani/os-installer/ui/row/selection_row.ui')
class SelectionRow(Adw.ActionRow):
    __gtype_name__ = __qualname__

    icon = Gtk.Template.Child()
    switch = Gtk.Template.Child()

    def __init__(self, choice, **kwargs):
        super().__init__(**kwargs)

        self.choice = choice

        self.set_title(_(choice.name))
        if choice.description:
            self.set_subtitle(_(choice.description))
        self.switch.set_active(choice.state)
        if choice.icon_path:
            self.icon.set_from_file(str(choice.icon_path))
        else:
            self.icon.set_from_icon_name(choice.icon_name)
            self.icon.set_icon_size(Gtk.IconSize.LARGE)

    def is_activated(self):
        return self.switch.get_active()

    def flip_switch(self):
        new_state = not self.switch.get_active()
        self.switch.set_active(new_state)
        self.choice.state = new_state
