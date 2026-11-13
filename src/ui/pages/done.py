# SPDX-License-Identifier: GPL-3.0-or-later

from gi.repository import Gtk

from .buttons import TerminalButton
from .config import config
from .translations import translate_widgets


@Gtk.Template(resource_path='/org/shani/os-installer/ui/pages/done.ui')
class DonePage(Gtk.Box):
    __gtype_name__ = __qualname__

    now_button = Gtk.Template.Child()
    later_button = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        translate_widgets(self.now_button, self.later_button)
