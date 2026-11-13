# SPDX-License-Identifier: GPL-3.0-or-later

from gi.repository import Gtk

from .buttons import ConfirmButton
from .config import config
from .device_rows import DeviceSummaryRow
from .translations import translate_widgets


@Gtk.Template(resource_path='/org/shani/os-installer/ui/pages/confirm.ui')
class ConfirmPage(Gtk.Box):
    __gtype_name__ = __qualname__

    explanation_label = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        translate_widgets(self.explanation_label)

        if config.get('repair'):
            # Translators: Followed by a disk or partition name.
            self.explanation_label.set_label(
                _("This will repair the installation on"))

    ### callbacks ###
