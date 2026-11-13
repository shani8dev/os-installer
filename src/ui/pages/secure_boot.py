# SPDX-License-Identifier: GPL-3.0-or-later

from gi.repository import Gtk

from .buttons import ContinueButton
from .config import config
from .entry_error_enhancer import EntryErrorEnhancer
from .translations import translate_widgets


@Gtk.Template(resource_path='/org/shani/os-installer/ui/pages/secure_boot.ui')
class SecureBootPage(Gtk.Box):
    __gtype_name__ = __qualname__

    switch_row = Gtk.Template.Child()
    root_pw_row = Gtk.Template.Child()
    password_row = Gtk.Template.Child()
    confirm_row = Gtk.Template.Child()
    hint_banner = Gtk.Template.Child()
    root_pw_banner = Gtk.Template.Child()
    continue_button = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self._ready = False

        translate_widgets(self.switch_row, self.root_pw_row, self.password_row,
                          self.confirm_row)

        self.min_length = config.get('secure_boot')['mok_password_min_length']

        # mokutil --root-pw takes the password hash from /etc/shadow: there
        # must be a root password for it to use.
        self.has_root_password = bool(config.get('root_password'))
        self.use_root_pw = config.get('mok_root_pw') and self.has_root_password

        # Set before the switches: set_active() emits notify::active, which
        # reads both of these.
        self.active = config.get('mok_enroll')
        self.switch_row.set_active(self.active)
        self.root_pw_row.set_active(self.use_root_pw)

        password = config.get('mok_password')
        self.password = EntryErrorEnhancer(
            self.password_row, lambda text: len(text) >= self.min_length)
        self.confirmation = EntryErrorEnhancer(
            self.confirm_row, lambda text: text == self.password_row.get_text())
        self.password_row.set_text(password)
        self.confirm_row.set_text(password)

        self._ready = True
        self._adjust()

    ### callbacks ###

    @Gtk.Template.Callback('switch_row_clicked')
    def _switch_row_clicked(self, row, state):
        self.active = self.switch_row.get_active()
        config.set('mok_enroll', self.active)
        self._adjust()

    @Gtk.Template.Callback('root_pw_clicked')
    def _root_pw_clicked(self, row, state):
        self.use_root_pw = self.root_pw_row.get_active()
        config.set('mok_root_pw', self.use_root_pw)
        self._adjust()

    @Gtk.Template.Callback('password_changed')
    def _password_changed(self, editable):
        password = editable.get_text()
        if self.password.update_row(password):
            config.set('mok_password', password)
        self._confirm_changed(self.confirm_row)

    @Gtk.Template.Callback('password_activated')
    def _password_activated(self, row):
        self.confirm_row.grab_focus()

    @Gtk.Template.Callback('confirm_changed')
    def _confirm_changed(self, editable):
        self.confirmation.update_row(editable.get_text())
        self._adjust()

    @Gtk.Template.Callback('confirm_activated')
    def _confirm_activated(self, row):
        self._continue(None)

    def _adjust(self):
        # Called from the switches' notify::active while the template is still
        # being built, before the entries exist.
        if not getattr(self, '_ready', False):
            return
        using_root_pw = self.active and getattr(self, 'use_root_pw', False)
        self.password_row.set_sensitive(self.active and not self.use_root_pw)
        self.confirm_row.set_sensitive(self.active and not self.use_root_pw)
        self.password_row.set_visible(not self.use_root_pw)
        self.confirm_row.set_visible(not self.use_root_pw)
        self.hint_banner.set_revealed(not self.use_root_pw)
        self.root_pw_banner.set_revealed(using_root_pw and not self.has_root_password)
        self.continue_button.set_sensitive(
            not self.active or using_root_pw or
            (self.password and self.confirmation))

    def _continue(self, _):
        if self.continue_button.is_sensitive():
            config.set_next_page(self)