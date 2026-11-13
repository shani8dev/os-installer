# SPDX-License-Identifier: GPL-3.0-or-later

from gi.repository import Adw, GObject, Gtk

from .config import config
from .state_machine import state_machine
from .translator import config_gettext


def _get_choices(choices):
    _ = config_gettext
    choice_texts = []
    for choice in choices:
        if choice.options:
            if choice.state.keyword:
                text = f"{_(choice.name)} – {_(choice.state.display)}"
                choice_texts.append(text)
        elif choice.state:
            choice_texts.append(_(choice.name))

    if choice_texts:
        return ", ".join(choice_texts)
    else:
        # Translators: Shown when list of selected software is empty.
        return _("None")


update_funcs = {
    "desktop": ("desktop_chosen", lambda desktop: desktop[1]),
    "feature": ("feature_choices", _get_choices),
    "format": ("formats", lambda formats: formats[1]),
    "keyboard-overview": ("keyboard_layout", lambda keyboard: keyboard[1]),
    "language": ("language_chosen", lambda language: language.name),
    "secure-boot": ("mok_enroll",
                    lambda enabled: _("Enabled") if enabled else _("Disabled")),
    "timezone": ("timezone", lambda timezone: timezone),
    "software": ("software_choices", _get_choices),
    "tpm": ("use_tpm",
            lambda enabled: _("Enabled") if enabled else _("Disabled")),
}

titles = {
    # Translators: Description of selected desktop.
    "desktop": _("Desktop"),
    # Translators: Description of selected additional features.
    "feature": _("Additional Features"),
    # Translators: Description of selected format.
    "format": _("Formats"),
    # Translators: Description of selected keyboard layout.
    "keyboard-overview": _("Keyboard Layout"),
    # Translators: Description of selected language.
    "language": _("Language"),
    # Translators: Description of the MOK enrollment choice.
    "secure-boot": _("Secure Boot"),
    # Translators: Description of selected timezone.
    "timezone": _("Timezone"),
    # Translators: Description of the TPM auto-unlock choice.
    "tpm": _("Automatic Unlock"),
    # Translators: Description of selected additional software.
    "software": _("Additional Software"),
}


@Gtk.Template(resource_path='/org/shani/os-installer/ui/row/summary_row.ui')
class SummaryRow(Adw.ActionRow):
    __gtype_name__ = __qualname__

    page_name = GObject.Property(type=str)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # page-name is not set yet, react when that happens
        self.connect("notify::page-name", self._set_update)

    def _set_update(self, row, value):
        page_name = self.get_property("page-name")

        if not state_machine.is_page_available(page_name):
            self.set_visible(False)
            return

        title = titles.get(page_name, " ")
        self.set_title(_(title))

        config_var, subtitle_func = update_funcs.get(page_name, ("", None))
        config.subscribe(config_var, lambda v: self.set_subtitle(subtitle_func(v)))
