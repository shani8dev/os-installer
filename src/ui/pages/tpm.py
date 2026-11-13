# SPDX-License-Identifier: GPL-3.0-or-later

from gi.repository import Gtk

from .buttons import ContinueButton
from .config import config
from .translations import translate_widgets


@Gtk.Template(resource_path='/org/shani/os-installer/ui/pages/tpm.ui')
class TpmPage(Gtk.Box):
    __gtype_name__ = __qualname__

    switch_row = Gtk.Template.Child()
    hint_banner = Gtk.Template.Child()
    continue_button = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        translate_widgets(self.switch_row)

        self.active = config.get('use_tpm')
        self.switch_row.set_active(self.active)

    @Gtk.Template.Callback('switch_row_clicked')
    def _switch_row_clicked(self, row, state):
        self.active = self.switch_row.get_active()
        config.set('use_tpm', self.active)