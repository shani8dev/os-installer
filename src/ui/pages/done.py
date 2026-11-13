# SPDX-License-Identifier: GPL-3.0-or-later

from gi.repository import Gdk, Gtk

from .buttons import TerminalButton
from .config import config
from .translations import translate_widgets

# configure.sh writes it after adding the keyslot; /run is a tmpfs, so a
# reboot removes it.
RECOVERY_KEY_FILE = '/run/os-installer/recovery-key'


@Gtk.Template(resource_path='/org/shani/os-installer/ui/pages/done.ui')
class DonePage(Gtk.Box):
    __gtype_name__ = __qualname__

    now_button = Gtk.Template.Child()
    later_button = Gtk.Template.Child()
    recovery_key_box = Gtk.Template.Child()
    recovery_key_label = Gtk.Template.Child()
    copy_button = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        translate_widgets(self.now_button, self.later_button,
                          self.recovery_key_label, self.copy_button)
        self._show_recovery_key()

    def _show_recovery_key(self):
        try:
            with open(RECOVERY_KEY_FILE) as file:
                key = file.read().strip()
        except OSError:
            return
        if not key:
            return
        self.recovery_key_label.set_label(key)
        self.recovery_key_box.set_visible(True)

    @Gtk.Template.Callback('copy_recovery_key')
    def _copy_recovery_key(self, _):
        display = Gdk.Display.get_default()
        if display is not None:
            display.get_clipboard().set(self.recovery_key_label.get_label())
        config.set('display-toast', _("Recovery key copied"))