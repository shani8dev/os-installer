# SPDX-License-Identifier: GPL-3.0-or-later

from gi.repository import Adw, GObject, Gtk


@Gtk.Template(resource_path='/org/shani/os-installer/ui/row/progress_row.ui')
class ProgressRow(Adw.ActionRow):
    __gtype_name__ = __qualname__

    def __init__(self, info, **kwargs):
        self.info = info
        super().__init__(**kwargs)

    @GObject.Property(type=str)
    def name(self):
        return self.info.name
