# SPDX-License-Identifier: GPL-3.0-or-later

from gi.repository import Gtk

from .config import config
from .language_provider import language_provider
from .progress_row import ProgressRow


@Gtk.Template(resource_path='/org/shani/os-installer/ui/pages/language.ui')
class LanguagePage(Gtk.Box):
    __gtype_name__ = __qualname__

    list = Gtk.Template.Child()
    model = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        if languages := language_provider.get_available_languages():
            self.model.splice(0, 0, languages)
            self.list.bind_model(self.model, ProgressRow)
        else:
            self.list.set_visible(False)

    ### callbacks ###

    @Gtk.Template.Callback('row_activated')
    def _row_activated(self, list_box, row):
        config.set('language_chosen', row.info)
        config.set_next_page(self)
