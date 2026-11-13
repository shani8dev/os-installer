# SPDX-License-Identifier: GPL-3.0-or-later

from gi.repository import Gdk, Gtk

from .buttons import TerminalButton
from .config import config
from .translations import translate_widgets


@Gtk.Template(resource_path='/org/shani/os-installer/ui/pages/failed.ui')
class FailedPage(Gtk.Box):
    __gtype_name__ = __qualname__

    failure_page = Gtk.Template.Child()
    search_button = Gtk.Template.Child()
    log_label = Gtk.Template.Child()
    copy_log_button = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        translate_widgets(self.failure_page, self.search_button)

        description = self.failure_page.get_description()
        formatted = description.format(config.get('distribution_name'))
        self.failure_page.set_description(formatted)

        log_path = config.get('log_path')
        if log_path:
            # Translators: Followed by a file path.
            self.log_label.set_label(
                _("The full log is in {}.").format(log_path))
        else:
            self.log_label.set_visible(False)
            self.copy_log_button.set_visible(False)

    @Gtk.Template.Callback('copy_log')
    def _copy_log(self, _):
        path = config.get('log_path')
        if not path:
            return
        try:
            with open(path) as file:
                text = file.read()
        except OSError:
            return
        display = Gdk.Display.get_default()
        if display is not None:
            display.get_clipboard().set(text)
        config.set('display-toast', _("Log copied"))
