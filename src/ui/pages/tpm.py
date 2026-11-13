# SPDX-License-Identifier: GPL-3.0-or-later

from gi.repository import Gtk

from .config import config
from .translations import translate_widgets


@Gtk.Template(resource_path='/org/shani/os-installer/ui/pages/tpm.ui')
class TpmPage(Gtk.Box):
    __gtype_name__ = __qualname__

    tpm_row = Gtk.Template.Child()
    pin_switch_row = Gtk.Template.Child()
    tpm_pin_row = Gtk.Template.Child()
    switch_row = Gtk.Template.Child()
    hint_banner = Gtk.Template.Child()
    continue_button = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        translate_widgets(self.pin_switch_row, self.switch_row)

        from .firmware import tpm_present
        # Translators: TPM state.
        self.tpm_row.set_subtitle(
            _("Found") if tpm_present() else _("Not found"))

        self.min_pin_length = max(4, config.get('user')['min_password_length'])

        self.active = config.get('use_tpm')
        self.switch_row.set_active(self.active)

        self.use_pin = config.get('use_tpm_pin')
        self.pin_switch_row.set_active(self.use_pin)
        self.tpm_pin_row.set_text(config.get('tpm_pin'))
        self._adjust_pin()

    @Gtk.Template.Callback('switch_row_clicked')
    def _switch_row_clicked(self, row, state):
        self.active = self.switch_row.get_active()
        config.set('use_tpm', self.active)
        self._adjust_pin()

    @Gtk.Template.Callback('pin_switch_clicked')
    def _pin_switch_clicked(self, row, state):
        self.use_pin = self.pin_switch_row.get_active()
        config.set('use_tpm_pin', self.use_pin)
        if self.use_pin:
            self.tpm_pin_row.grab_focus()
        else:
            config.set('tpm_pin', '')
        self._adjust_pin()

    @Gtk.Template.Callback('pin_changed')
    def _pin_changed(self, editable):
        pin = editable.get_text()
        if len(pin) >= self.min_pin_length:
            config.set('tpm_pin', pin)
        else:
            config.set('tpm_pin', '')

    def _adjust_pin(self):
        active = self.active and self.use_pin
        self.tpm_pin_row.set_visible(self.use_pin)
        self.tpm_pin_row.set_sensitive(active)