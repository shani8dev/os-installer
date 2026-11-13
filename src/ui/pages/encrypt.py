# SPDX-License-Identifier: GPL-3.0-or-later

from gi.repository import Gtk

from .buttons import ContinueButton
from .config import config
from .entry_error_enhancer import EntryErrorEnhancer
from .password_strength import hint as password_strength_hint
from .translations import translate_widgets


@Gtk.Template(resource_path='/org/shani/os-installer/ui/pages/encrypt.ui')
class EncryptPage(Gtk.Box):
    __gtype_name__ = __qualname__

    switch_row = Gtk.Template.Child()
    pin_row = Gtk.Template.Child()
    pin_confirm_row = Gtk.Template.Child()
    info_revealer = Gtk.Template.Child()
    info_label = Gtk.Template.Child()
    root_strength_label = Gtk.Template.Child()
    layout_hint = Gtk.Template.Child()

    root_password_switch_row = Gtk.Template.Child()
    root_password_row = Gtk.Template.Child()
    root_password_confirm_row = Gtk.Template.Child()

    continue_button = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        translate_widgets(self.switch_row, self.pin_row, self.pin_confirm_row,
                          self.info_label, self.root_password_switch_row,
                          self.root_password_row, self.root_password_confirm_row)

        ### Encryption PIN ###

        encryption_setting = config.get('disk_encryption')
        self.min_pin_length = encryption_setting['min_length']
        self.use_confirmation = encryption_setting['confirmation']

        if encryption_setting['forced']:
            self.switch_row.set_visible(False)
            self.active = True
        else:
            self.active = config.get('use_encryption')
            self.switch_row.set_active(self.active)

        self.generated = encryption_setting['generated']
        if self.generated:
            self.pin_row.set_visible(False)
            self.pin_confirm_row.set_visible(False)
            self.info_revealer.set_visible(False)

        self.pin = EntryErrorEnhancer(
            self.pin_row, lambda text: len(text) >= self.min_pin_length)
        self.pin_row.set_text(config.get('encryption_pin'))

        self.pin_confirm_row.set_visible(self.use_confirmation)
        if self.use_confirmation:
            self.confirmation = EntryErrorEnhancer(
                self.pin_confirm_row, lambda text: text == self.pin_row.get_text())
            self.pin_confirm_row.set_text(config.get('encryption_pin'))
        else:
            self.confirmation = True

        self._adjust_pin_state()

        ### Root Password ###

        self.root_password_active = config.get('root_password') != ''
        self.root_password_switch_row.set_active(self.root_password_active)

        # Match the same minimum-length policy the distro configures for the
        # primary user account, rather than a hardcoded "just non-empty" — so
        # raising min_password_length later covers root too, not just the user.
        self.min_root_password_length = config.get('user')['min_password_length']
        self.root_password = EntryErrorEnhancer(
            self.root_password_row,
            lambda text: len(text) >= self.min_root_password_length)
        self.root_password_row.set_text(config.get('root_password') or '')
        self.root_password_confirm = EntryErrorEnhancer(
            self.root_password_confirm_row,
            lambda text: text == self.root_password_row.get_text())
        self.root_password_confirm_row.set_text(config.get('root_password') or '')

        self._adjust_root_password_state()

        # The PIN is typed at the boot prompt, with the console keymap the
        # installed system gets from the keyboard page (rd.vconsole.keymap).
        layout_name = config.get('keyboard_layout')[1]
        # Translators: Followed by the keyboard layout name.
        self.layout_hint.set_label(
            _("At boot, type this PIN with the {} layout.").format(layout_name))

    def _adjust_pin_state(self):
        self.pin_row.set_sensitive(self.active)
        self.pin_confirm_row.set_sensitive(self.active)
        self.info_revealer.set_reveal_child(self.active)
        self._set_continue_button()

    def _adjust_root_password_state(self):
        self.root_password_row.set_sensitive(self.root_password_active)
        self.root_password_confirm_row.set_sensitive(self.root_password_active)
        self._set_continue_button()

    def _set_continue_button(self):
        pin_ok = (not self.active or self.generated or
                  (self.pin and self.confirmation))
        root_active = getattr(self, 'root_password_active', False)
        root_ok = (not root_active or
                   (getattr(self, 'root_password', None) and
                    getattr(self, 'root_password_confirm', None)))
        self.continue_button.set_sensitive(pin_ok and root_ok)

    ### callbacks ###

    @Gtk.Template.Callback('switch_row_clicked')
    def _switch_row_clicked(self, row, state):
        self.active = self.switch_row.get_active()
        config.set('use_encryption', self.active)
        self._adjust_pin_state()

        if self.active:
            self.pin_row.grab_focus()
        else:
            config.set('encryption_pin', '')

    @Gtk.Template.Callback('pin_changed')
    def _pin_changed(self, editable):
        pin = editable.get_text()
        if self.pin.update_row(pin):
            config.set('encryption_pin', pin)
        self._pin_confirm_changed(self.pin_confirm_row)

    @Gtk.Template.Callback('pin_confirm_changed')
    def _pin_confirm_changed(self, editable):
        pin = editable.get_text()
        if self.use_confirmation:
            self.confirmation.update_row(pin)
        self._set_continue_button()

    @Gtk.Template.Callback('pin_activated')
    def _pin_activated(self, object):
        if self.use_confirmation:
            self.pin_confirm_row.grab_focus()
        elif self.root_password_active:
            self.root_password_row.grab_focus()
        else:
            self._continue(None)

    @Gtk.Template.Callback('pin_confirm_activated')
    def _pin_confirm_activated(self, object):
        if self.root_password_active:
            self.root_password_row.grab_focus()
        else:
            self._continue(None)

    @Gtk.Template.Callback('root_password_switch_row_clicked')
    def _root_password_switch_row_clicked(self, row, state):
        self.root_password_active = self.root_password_switch_row.get_active()
        self._adjust_root_password_state()

        if self.root_password_active:
            self.root_password_row.grab_focus()
        else:
            config.set('root_password', '')
            # Clear the visible fields too — otherwise re-enabling the switch
            # later shows the old password text even though it was discarded,
            # which reads as if the "off" toggle never took effect.
            self.root_password_row.set_text('')
            self.root_password_confirm_row.set_text('')

    @Gtk.Template.Callback('root_password_changed')
    def _root_password_changed(self, editable):
        password = editable.get_text()
        self.root_strength_label.set_label(
            password_strength_hint(password))
        if self.root_password.update_row(password):
            config.set('root_password', password)
        self._root_password_confirm_changed(self.root_password_confirm_row)

    @Gtk.Template.Callback('root_password_confirm_changed')
    def _root_password_confirm_changed(self, editable):
        password = editable.get_text()
        self.root_password_confirm.update_row(password)
        self._set_continue_button()

    @Gtk.Template.Callback('root_password_activated')
    def _root_password_activated(self, object):
        self.root_password_confirm_row.grab_focus()

    @Gtk.Template.Callback('root_password_confirm_activated')
    def _root_password_confirm_activated(self, object):
        self._continue(None)

    @Gtk.Template.Callback('continue')
    def _continue(self, object):
        if self.continue_button.is_sensitive():
            config.set_next_page(self)
