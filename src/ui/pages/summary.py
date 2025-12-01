# SPDX-License-Identifier: GPL-3.0-or-later

from gi.repository import Gtk

from .buttons import ConfirmButton
from .config import config
from .device_rows import DeviceSummaryRow
from .summary_row import SummaryRow
from .state_machine import state_machine
from .translator import config_gettext
from .translations import translate_widgets


@Gtk.Template(resource_path='/com/github/p3732/os-installer/ui/pages/summary.ui')
class SummaryPage(Gtk.Box):
    __gtype_name__ = __qualname__

    # rows
    language_row = Gtk.Template.Child()
    desktop_row = Gtk.Template.Child()
    user_row = Gtk.Template.Child()

    # user row specific
    user_autologin = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        translate_widgets(self.user_row, self.user_autologin)

        if state_machine.is_page_available('user'):
            self.user_row.set_visible(True)
            config.subscribe('user_autologin', self._update_user_autologin)
            config.subscribe('user_name', self._update_user_name)

        self.has_install = config.get('scripts')['install'] is not None
        if self.has_install:
            # These values can only be edited if install step has not already
            # been started with them
            self.language_row.set_activatable(False)
            self.desktop_row.set_activatable(False)

    ### callbacks ###

    def _update_user_autologin(self, autologin):
        self.user_autologin.set_visible(autologin)

    def _update_user_name(self, user_name):
        self.user_row.set_subtitle(user_name)

    @Gtk.Template.Callback('summary_row_activated')
    def _summary_row_activated(self, list_box, row):
        config.set('displayed-page', row.page_name)
