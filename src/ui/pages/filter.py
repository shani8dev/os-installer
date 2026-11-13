# SPDX-License-Identifier: GPL-3.0-or-later

from enum import Enum
from gi.repository import Gtk

from .config import config
from .format_provider import format_provider
from .timezone_provider import timezone_provider
from .translations import translate_widgets


class FilterType(Enum):
    format = 0
    timezone = 1


@Gtk.Template(resource_path='/org/shani/os-installer/ui/pages/filter.ui')
class FilterPage(Gtk.Box):
    __gtype_name__ = __qualname__

    search_entry = Gtk.Template.Child()
    custom_filter = Gtk.Template.Child()
    filter_list_model = Gtk.Template.Child()
    list_model = Gtk.Template.Child()

    stack = Gtk.Template.Child()
    no_results_page = Gtk.Template.Child()

    def __init__(self, filter_type, **kwargs):
        super().__init__(**kwargs)

        translate_widgets(self.search_entry, self.no_results_page)

        self.type = filter_type
        match self.type:
            case FilterType.format:
                self.filter = self._format_filter
                self.list_model.splice(0, 0, format_provider.get_formats())
            case FilterType.timezone:
                self.filter = self._timezone_filter
                self.list_model.splice(0, 0, timezone_provider.get_timezones())

        self.search_entry.connect("search-changed", self._filter)

    def _filter(self, *args):
        self.search_text = self.search_entry.get_text().lower()
        self.custom_filter.set_filter_func(self.filter)

        if self.filter_list_model.get_n_items() > 0:
            self.stack.set_visible_child_name('list')
        else:
            self.stack.set_visible_child_name('none')

    def _format_filter(self, format):
        return self.search_text in format.search_string

    def _timezone_filter(self, timezone):
        return self.search_text in timezone.search_string

    ### callbacks ###

    @Gtk.Template.Callback('row_activated')
    def _row_activated(self, list_view, pos):
        item = self.filter_list_model.get_item(pos)
        match self.type:
            case FilterType.format:
                config.set('formats', (item.id, item.name))
            case FilterType.timezone:
                config.set('timezone', item.id)
        config.set_next_page(self)


FormatPage = lambda **args: FilterPage(FilterType.format, **args)
TimezonePage = lambda **args: FilterPage(FilterType.timezone, **args)
