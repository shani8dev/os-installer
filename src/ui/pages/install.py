# SPDX-License-Identifier: GPL-3.0-or-later

from threading import Condition, Lock, Thread

from gi.repository import GLib, Gtk

from .buttons import TerminalButton
from .config import config
from .slideshow_provider import slideshow_provider


@Gtk.Template(resource_path='/org/shani/os-installer/ui/pages/install.ui')
class InstallPage(Gtk.Box):
    __gtype_name__ = __qualname__

    stack = Gtk.Template.Child()
    carousel = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        if self._setup_slideshow():
            self.stack.set_visible_child_name('slideshow')
        else:
            self.stack.set_visible_child_name('spinner')

    def _setup_slideshow(self):
        slideshow = slideshow_provider.get_slideshow()

        if not slideshow:
            return False

        self.durations = []
        self.slideshow_position = 0

        for slide in slideshow:
            picture = Gtk.Picture.new_for_paintable(slide.image)
            picture.add_css_class('card')
            picture.set_valign(Gtk.Align.CENTER)
            self.carousel.append(picture)
            self.durations.append(slide.duration)

        if self.carousel.get_n_pages() == 0:
            return False

        self.lock = Lock()
        self.cv = Condition(self.lock)

        self.stop_slideshow = False
        self.reset_timeout = False
        # Add extra time when manually navigating to a page
        self.extra_timeout = 0
        self.current_pos = 0

        self.thread = Thread(target=self._run_slideshow, daemon=True)
        self.thread.start()
        config.subscribe('displayed-page', self._stop_slideshow, delayed=True)

        return True

    def _run_slideshow(self):
        num_slides = self.carousel.get_n_pages()
        with self.cv:
            while True:
                timeout = self.durations[self.current_pos] + self.extra_timeout
                self.extra_timeout = 0
                self.cv.wait(timeout=timeout)

                if self.stop_slideshow:
                    break
                elif self.reset_timeout:
                    self.reset_timeout = False
                    continue

                self.current_pos = (self.current_pos + 1) % num_slides
                GLib.idle_add(self._ui_change_slide, self.current_pos)

    def _stop_slideshow(self, value):
        _, page = value
        # Relevant page change comes from scripting where page is None
        if page is None:
            self.stop_slideshow = True
            with self.cv:
                self.cv.notify_all()
            self.thread.join()

    def _ui_change_slide(self, position):
        slide = self.carousel.get_nth_page(position)
        self.carousel.scroll_to(slide, True)
        return False

    ### callbacks ###

    @Gtk.Template.Callback('page_changed')
    def _page_changed(self, page, position):
        if position == self.current_pos:
            return

        with self.cv:
            self.current_pos = max(0, int(self.carousel.get_position()))
            self.reset_timeout = True
            self.extra_timeout = 5
            self.cv.notify_all()
