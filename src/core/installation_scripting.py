# SPDX-License-Identifier: GPL-3.0-or-later

from threading import Lock
import grp
import os
import pwd

from gi.repository import Gio, GLib, Vte

from .config import config
from .envvar_creator import create_envs
from .installation_step import InstallationStep
from .logger import LOG_PATH
from .recovery_key import generate as generate_recovery_key
from .terminal_provider import terminal_provider


def _admin_problem(policy, euid, user, groups):
    """None when this user may install, else the message to show them.

    The installer owns this decision now: prepare.sh used to exit 1 with a
    sentence printed into the terminal, which the user only saw if they
    opened it. The groups come from the config (default wheel/sudo); an empty
    list disables the check for distros that authorise installs another way.
    """
    if euid == 0:
        return None
    allowed = policy.get('admin_groups') or []
    if not allowed:
        return None
    if groups.intersection(allowed):
        return None
    return ('Installing needs an administrator: run the installer as root or '
            f'as a user in {", ".join(allowed)} (current user: {user}).')


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
        self._admin_checked = False
        self.admin_problem = None

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
            config.set('installation_step', '')
            # Translators: Notification text
            config.set('send_notification', _("Finished Installation"))
            GLib.idle_add(config.set_next_page, None)

        if self.finished_step.value >= self.ready_step.value:
            return

        next_step = InstallationStep(self.finished_step.value + 1)
        if next_step != InstallationStep.prepare:
            config.set('installation_running', True)

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
            config.set('installation_step', next_step.name)

            # The script's output goes to the terminal and to the log file, so
            # a failed install can be reported without the in-app terminal.
            if next_step is InstallationStep.configure:
                # The recovery key has to exist before the configure script
                # adds it to the LUKS header; shown once, on the done page.
                if (not config.get('recovery_key') and
                        config.get('disk_encryption')['recovery_key'] and
                        config.get('use_encryption')):
                    config.set('recovery_key', generate_recovery_key())

            envs = create_envs(next_step)
            envs.insert(len(envs) - 1, f'OSI_SCRIPT={script_path}')
            envs.insert(len(envs) - 1, f'OSI_LOG={LOG_PATH}')

            pty = Vte.Pty.new_sync(Vte.PtyFlags.NO_CTTY, self.cancel)
            # Run script through bash, tee'd into the log; pipefail keeps the
            # script's exit status instead of tee's.
            pty.spawn_async(
                '/',
                ['/bin/bash', '-c',
                 'set -o pipefail; /bin/bash "$OSI_SCRIPT" 2>&1 | tee -a "$OSI_LOG"',
                 'os-installer'],
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
            # One message, not two: the second used to overwrite the first, so
            # the terminal only ever said "Stopping installation" and never
            # which script was missing.
            config.set('logged-error',
                       f'Could not find configured script "{file_path}". '
                       'Stopping installation.')
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
        if not self._admin_checked:
            self._admin_checked = True
            self.admin_problem = self._check_admin()

        scripts = config.get('scripts')
        if not (scripts['prepare'] or scripts['install']):
            # Nothing to install: an info-only configuration must not be
            # blocked by a policy about running install scripts.
            self._set_ok_to_start_step(InstallationStep.prepare)
            return

        if self.admin_problem:
            config.set('logged-error', self.admin_problem)
            GLib.idle_add(self._fail_installation, None)
            return

        self._set_ok_to_start_step(InstallationStep.prepare)

    def _check_admin(self):
        try:
            euid = os.geteuid()
            user = pwd.getpwuid(euid).pw_name
            groups = {group.gr_name for group in grp.getgrall()
                      if user in group.gr_mem}
        except (KeyError, OSError):
            # No passwd/group database (a container, a minimal image): the
            # prepare script is the last word, as before.
            return None
        return _admin_problem(config.get('install_policy'), euid, user, groups)


installation_scripting = InstallationScripting()

