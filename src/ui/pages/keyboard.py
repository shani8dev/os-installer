# SPDX-License-Identifier: GPL-3.0-or-later

from gi.repository import Gio, Gtk

from .buttons import ContinueButton
from .config import config
from .functions import reset_model
from .keyboard_layout_provider import get_default_layout, get_layouts_for
from .language_provider import language_provider
from .progress_row import ProgressRow
from .translations import translate_widgets


@Gtk.Template(resource_path='/org/shani/os-installer/ui/pages/keyboard_language.ui')
class KeyboardLanguagePage(Gtk.Box):
    __gtype_name__ = __qualname__

    list = Gtk.Template.Child()
    model = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.model.splice(0, 0, language_provider.get_all_languages())
        self.list.bind_model(self.model, ProgressRow)

    ### callbacks ###

    @Gtk.Template.Callback('language_row_activated')
    def _language_row_activated(self, list_box, row):
        info = row.info
        config.set('keyboard_language', (info.code, info.name))
        config.set_next_page(self)


@Gtk.Template(resource_path='/org/shani/os-installer/ui/pages/keyboard_layout.ui')
class KeyboardLayoutPage(Gtk.Box):
    __gtype_name__ = __qualname__

    language_row = Gtk.Template.Child()
    layout_list = Gtk.Template.Child()
    model = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        translate_widgets(self.language_row)

        self.layout_list.bind_model(self.model, ProgressRow)

        config.subscribe('keyboard_language', self._update_keyboard_language)

    ### callbacks ###

    def _update_keyboard_language(self, language):
        code, name = language
        reset_model(self.model, get_layouts_for(code, name))
        self.language_row.set_subtitle(name)

    @Gtk.Template.Callback('layout_row_activated')
    def _layout_row_activated(self, list_box, row):
        keyboard = row.info
        config.set('keyboard_layout', (keyboard.layout, keyboard.name))
        config.set_next_page(self)

    @Gtk.Template.Callback('show_language_selection')
    def _show_language_selection(self, row):
        config.set('displayed-page', 'keyboard-language')


@Gtk.Template(resource_path='/org/shani/os-installer/ui/pages/keyboard_overview.ui')
class KeyboardOverviewPage(Gtk.Box):
    __gtype_name__ = __qualname__

    primary_layout_row = Gtk.Template.Child()
    test_entry_row = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        translate_widgets(self.test_entry_row)

        if not config.has('keyboard_layout'):
            language = config.get('language_chosen')
            config.set('keyboard_language', (language.code, language.name))
            keyboard = get_default_layout(language.code)
            config.set('keyboard_layout', (keyboard.layout, keyboard.name))

        config.subscribe('keyboard_layout', self._update_primary_layout)

    ### callbacks ###

    def _update_primary_layout(self, keyboard_layout):
        _, name = keyboard_layout
        self.primary_layout_row.set_title(name)

    @Gtk.Template.Callback('continue')
    def _continue(self, data):
        config.set_next_page(self)

    @Gtk.Template.Callback('show_layout_selection')
    def _show_layout_selection(self, row):
        config.set('displayed-page', 'keyboard-layout')
