# SPDX-License-Identifier: GPL-3.0-or-later

import re

from gi.repository import Gtk

from .buttons import ContinueButton
from .config import config
from .entry_error_enhancer import EntryErrorEnhancer
from .translations import translate_widgets

# RFC 1123: letters, digits and hyphens, not at the ends, at most 63.
HOSTNAME_RE = re.compile(r'^[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?$')


@Gtk.Template(resource_path='/org/shani/os-installer/ui/pages/hostname.ui')
class HostnamePage(Gtk.Box):
    __gtype_name__ = __qualname__

    hostname_row = Gtk.Template.Child()
    hint_label = Gtk.Template.Child()
    continue_button = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        translate_widgets(self.hostname_row, self.hint_label)

        self.check = EntryErrorEnhancer(
            self.hostname_row, lambda text: bool(HOSTNAME_RE.match(text)))
        self.hostname_row.set_text(config.get('hostname_chosen'))
        self._update(self.hostname_row.get_text())

    ### callbacks ###

    @Gtk.Template.Callback('hostname_changed')
    def _hostname_changed(self, row):
        text = row.get_text()
        if self.check.update_row(text):
            config.set('hostname_chosen', text)
        self._update(text)

    @Gtk.Template.Callback('hostname_activated')
    def _hostname_activated(self, row):
        self._continue(None)

    def _update(self, text):
        if not text:
            # Translators: Hint under the hostname field.
            hint = _("This is the name other computers see on the network.")
        elif HOSTNAME_RE.match(text):
            # Translators: Hint under the hostname field, followed by the name.
            hint = _("Other computers will reach this one as {}.").format(text)
        else:
            hint = _("Use letters, digits and hyphens, not at the start or end, up to 63 characters.")
        self.hint_label.set_label(hint)
        self.continue_button.set_sensitive(bool(HOSTNAME_RE.match(text)))

    def _continue(self, _):
        if self.continue_button.is_sensitive():
            config.set_next_page(self)