# SPDX-License-Identifier: GPL-3.0-or-later

from threading import Lock
import os

from gi.repository import Gio, GLib, Vte

from .config import config
from .envvar_creator import create_envs
from .installation_step import InstallationStep
from .terminal_provider import terminal_provider


class InstallationScripting():
    '''
    Handles all calls to scripts for installation. The installation process consists of 3 steps:
    * Preparation. Used e.g. for updating mirrors.
    * Installation. Installs an OS onto a disk.
    * Configuration. Configures an OS according to user's choices.
    '''

    def __init__(self):
        self.cancel = Gio.Cancellable()

        self.lock = Lock()
        self.ready_step = InstallationStep.none
        self.running_step = InstallationStep.none
        self.finished_step = InstallationStep.none

    def _fail_installation(self, __):
        config.set('installation_running', False)
        config.set('displayed-page', 'failed')
        # Translators: Notification text
        config.set('send_notification', _("Installation Failed"))

    def _try_start_next_script(self):
        if self.running_step != InstallationStep.none:
            return

        if self.finished_step is InstallationStep.configure:
            config.set('installation_running', False)
            # Translators: Notification text
            config.set('send_notification', _("Finished Installation"))
            GLib.idle_add(config.set_next_page, None)

        if self.finished_step.value >= self.ready_step.value:
            return

        next_step = InstallationStep(self.finished_step.value + 1)
        if next_step != InstallationStep.prepare:
            config.set('installation_running', True)

        envs = create_envs(next_step)

        # start script
        file_name = config.get('scripts')[next_step.name]
        if not file_name:
            print(f'Skipping step "{next_step.name}"')
            self.finished_step = next_step
            self._try_start_next_script()
            return

        file_path = config.base_path / file_name
        if file_path.exists():
            print(f'Starting step "{next_step.name}"...')

            # Determine proper path for execution
            script_path = str(file_path)
            if not file_path.is_absolute():
                script_path = f"./{script_path}"

            print(f"Executing script: {script_path}")

            pty = Vte.Pty.new_sync(Vte.PtyFlags.NO_CTTY, self.cancel)
            # Run script through bash
            pty.spawn_async(
                '/',
                ['/bin/bash', script_path],
                envs,
                GLib.SpawnFlags.DEFAULT,
                None,
                None,
                -1,
                self.cancel,
                self._on_child_spawned,
                (None,),
            )
            terminal_provider.set_pty(pty)
            self.running_step = next_step
        else:
            config.set('logged-error', f'Could not find configured script "{file_path}"')
            config.set('logged-error', 'Stopping installation')
            GLib.idle_add(self._fail_installation, None)

    ### callbacks ###

    def _on_child_spawned(self, pty, task, data):
        success, pid = pty.spawn_finish(task)
        if success:
            GLib.child_watch_add(pid, self._on_child_exited, None)
        else:
            config.set('logged-error', f'Error starting {self.running_step}')
            GLib.idle_add(self._fail_installation, None)

    def _on_child_exited(self, pid, status, data):
        with self.lock:
            self.finished_step = self.running_step
            self.running_step = InstallationStep.none

            if not status == 0:
                config.set('logged-error', f'Failure during step "{self.finished_step.name}"')
                GLib.idle_add(self._fail_installation, None)
                return

            config.set('logged-error', f'Finished step "{self.finished_step.name}".')

            self._try_start_next_script()

    def _set_ok_to_start_step(self, step: InstallationStep):
        with self.lock:
            if self.ready_step.value < step.value:
                self.ready_step = step
                self._try_start_next_script()

    ### public methods ###

    def can_run_configure(self):
        self._set_ok_to_start_step(InstallationStep.configure)

    def can_run_install(self):
        self._set_ok_to_start_step(InstallationStep.install)

    def can_run_prepare(self):
        self._set_ok_to_start_step(InstallationStep.prepare)


installation_scripting = InstallationScripting()

