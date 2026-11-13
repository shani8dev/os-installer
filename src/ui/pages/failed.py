# SPDX-License-Identifier: GPL-3.0-or-later

from gi.repository import Gtk

from .buttons import TerminalButton
from .config import config
from .translations import translate_widgets


@Gtk.Template(resource_path='/org/shani/os-installer/ui/pages/failed.ui')
class FailedPage(Gtk.Box):
    __gtype_name__ = __qualname__

    failure_page = Gtk.Template.Child()
    search_button = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        translate_widgets(self.failure_page, self.search_button)

        description = self.failure_page.get_description()
        formatted = description.format(config.get('distribution_name'))
        self.failure_page.set_description(formatted)
