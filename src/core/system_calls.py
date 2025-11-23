# SPDX-License-Identifier: GPL-3.0-or-later

''' All calls to other programs are encapsulated here. '''

import locale
import os
from subprocess import Popen, run

from gi.repository import Gio, GLib

from .config import config


def _execute(args):
    if not config.is_demo() and not config.is_test():
        run(args)


def _run_program(args):
    env = os.environ.copy()
    env["LANG"] = config.get('language_chosen').locale
    try:
        Popen(args, env=env)
    except Exception as e:
        print(f"Error running {args}: {e}")


class SystemCaller:
    def __init__(self, app_window):
        self.action_group = Gio.SimpleActionGroup()

        self._add_syscall_action('error-search', self._open_internet_search)
        self._add_syscall_action('manage-disks', self._open_disks)
        self._add_syscall_action('reboot', self._reboot)
        self._add_syscall_action('wifi-settings', self._open_wifi_settings)

        app_window.insert_action_group('external', self.action_group)

        config.subscribe('formats', self._set_system_formats, delayed=True)
        config.subscribe('keyboard_layout',
                         self._set_system_keyboard_layout, delayed=True)
        config.subscribe('language_chosen', self._set_system_language)
        config.subscribe('timezone', self._set_system_timezone, delayed=True)

    def _add_syscall_action(self, action_name, callback):
        action = Gio.SimpleAction.new(action_name, None)
        action.connect('activate', callback)
        self.action_group.add_action(action)

    def _open_disks(self, _, __):
        _run_program(config.get('commands')['disks'].split())

    def _open_internet_search(self, _, __):
        browser_cmd = config.get('commands')['browser'].split()
        failure_help_url = config.get('failure_help_url')
        version = config.get('version')
        browser_cmd.append(failure_help_url.format(version))
        _run_program(browser_cmd)

    def _open_wifi_settings(self, _, __):
        _run_program(config.get('commands')['wifi'].split())

    def _reboot(self, _, __):
        _execute(config.get('commands')['reboot'].split())
        GLib.idle_add(config.set_next_page, None)

    def _set_system_formats(self, formats):
        locale, _ = formats
        _execute(['gsettings', 'set', 'org.gnome.system.locale', 'region',
                  f"'{locale}'"])

    def _set_system_keyboard_layout(self, keyboard):
        keyboard_layout, _ = keyboard
        _execute(['gsettings', 'set', 'org.gnome.desktop.input-sources', 'sources',
                  f"[('xkb','{keyboard_layout}')]"])

    def _set_system_language(self, language_info):
        if language_info.available:
            try:
                locale.setlocale(locale.LC_MESSAGES, language_info.locale)
                print(f'Set locale to "{language_info.locale}".')
            except locale.Error:
                print(f'Failed setting locale "{language_info.locale}", not available in system.')

        # TODO find correct way to set system locale without user authentication
        _execute(['localectl', '--no-ask-password', 'set-locale',
                  f'LANG={language_info.locale}'])

        _execute(['gsettings', 'set', 'org.gnome.system.locale',
                  'region', language_info.locale])

    def _set_system_timezone(self, timezone):
        # TODO find correct way to set timezone without user authentication
        _execute(['timedatectl', '--no-ask-password', 'set-timezone', timezone])


def start_system_timesync():
    # TODO find correct way to set enable time sync without user authentication
    _execute(['timedatectl', '--no-ask-password', 'set-ntp', 'true'])
    _execute(['gsettings', 'set', 'org.gnome.desktop.datetime',
             'automatic-timezone', 'true'])
