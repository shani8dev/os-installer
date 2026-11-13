# SPDX-License-Identifier: GPL-3.0-or-later

from gi.repository import Gtk

from .buttons import ContinueButton
from .config import config
from .translations import translate_widgets


@Gtk.Template(resource_path='/org/shani/os-installer/ui/pages/region.ui')
class RegionPage(Gtk.Box):
    __gtype_name__ = __qualname__

    format_hint_row = Gtk.Template.Child()
    formats_row = Gtk.Template.Child()
    timezone_row = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        translate_widgets(self.format_hint_row, self.formats_row, self.timezone_row)

        config.subscribe('formats', self._update_formats)
        config.subscribe('timezone', self._update_timezone)

    ### callbacks ###

    def _update_formats(self, formats):
        self.formats_row.set_subtitle(formats[1])

    def _update_timezone(self, timezone):
        self.timezone_row.set_subtitle(timezone)

    @Gtk.Template.Callback('row_activated')
    def _row_activated(self, row):
        config.set('displayed-page', row.get_name())
