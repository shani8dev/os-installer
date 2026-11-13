# SPDX-License-Identifier: GPL-3.0-or-later

import re

from gi.repository import Gtk

from .buttons import ContinueButton
from .config import config
from .entry_error_enhancer import EntryErrorEnhancer
from .password_strength import label as password_strength_label
from .translations import translate_widgets


@Gtk.Template(resource_path='/org/shani/os-installer/ui/pages/user.ui')
class UserPage(Gtk.Box):
    __gtype_name__ = __qualname__

    name_row = Gtk.Template.Child()
    username_row = Gtk.Template.Child()
    autologin_row = Gtk.Template.Child()
    password_row = Gtk.Template.Child()
    strength_label = Gtk.Template.Child()
    password_confirm_row = Gtk.Template.Child()
    continue_button = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        translate_widgets(self.name_row, self.username_row, self.autologin_row,
                          self.password_row, self.password_confirm_row)

        user_setting = config.get('user')
        self.min_password_length = user_setting['min_password_length']
        self.request_username = user_setting['request_username']
        self.use_confirmation = user_setting['password_confirmation']

        self.name_ok = False
        self.username = EntryErrorEnhancer(
            self.username_row, lambda text: bool(re.match('^[a-z][a-z0-9_-]*$', text)))
        self.password = EntryErrorEnhancer(
            self.password_row, lambda text: len(text) >= self.min_password_length)
        self.confirmation = EntryErrorEnhancer(
            self.password_confirm_row,
            lambda text: not self.use_confirmation or text == self.password_row.get_text())

        self.name_row.set_text(config.get('user_name'))
        self.username_row.set_visible(self.request_username)
        if self.request_username:
            self.username_row.set_text(config.get('user_username'))
        else:
            self.username = True

        if user_setting['provide_autologin']:
            self.autologin_row.set_visible(True)
            self.autologin_row.set_active(config.get('user_autologin'))
        else:
            self.autologin_row.set_visible(False)
            self.autologin_row.set_active(False)

        password = config.get('user_password')
        self.password_row.set_text(password)
        self.password_confirm_row.set_visible(self.use_confirmation)
        if self.use_confirmation:
            self.password_confirm_row.set_text(password)

    def _set_continue_button(self):
        self.continue_button.set_sensitive(
            self.name_ok and self.username and self.password and self.confirmation)

    ### callbacks ###

    @Gtk.Template.Callback('autologin_row_clicked')
    def _autologin_row_clicked(self, row, state):
        config.set('user_autologin', self.autologin_row.get_active())
        self._set_continue_button()

    @Gtk.Template.Callback('focus_password')
    def _focus_password(self, row):
        self.password_row.grab_focus()

    @Gtk.Template.Callback('focus_next_from_name')
    def _focus_next_from_name(self, row):
        if self.request_username:
            self.username_row.grab_focus()
        else:
            self.password_row.grab_focus()

    @Gtk.Template.Callback('name_changed')
    def _name_changed(self, editable):
        name = editable.get_text().strip()
        self.name_ok = len(name) > 0
        if self.name_ok:
            config.set('user_name', name)
        self._set_continue_button()

    @Gtk.Template.Callback('username_changed')
    def _username_changed(self, editable):
        username = editable.get_text().strip()
        if self.username.update_row(username):
            config.set('user_username', username)
        self._set_continue_button()

    @Gtk.Template.Callback('password_changed')
    def _password_changed(self, editable):
        password = editable.get_text()
        if self.password.update_row(password):
            config.set('user_password', password)
        self._update_strength(password)
        self._password_confirm_changed(self.password_confirm_row)

    def _update_strength(self, password):
        # Translators: Followed by the strength (Weak, Okay, ...).
        self.strength_label.set_label(
            _("Password strength: {}").format(password_strength_label(password))
            if password else '')

    @Gtk.Template.Callback('password_active')
    def _password_active(self, object):
        if self.continue_button.get_sensitive():
            config.set_next_page(self)

    @Gtk.Template.Callback('password_confirm_changed')
    def _password_confirm_changed(self, editable):
        password = editable.get_text()
        self.confirmation.update_row(password)
        self._set_continue_button()

    @Gtk.Template.Callback('continue')
    def _continue(self, object):
        if self.continue_button.get_sensitive():
            config.set_next_page(self)
