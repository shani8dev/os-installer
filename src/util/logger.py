# SPDX-License-Identifier: GPL-3.0-or-later
"""Where the installer's output goes.

The app's own prints (config decisions, errors) and every script's output are
written to one file as well as to the terminal, so a failed install can be
reported without the user having to open the in-app terminal and copy it.
"""

import os
import sys

LOG_PATH = os.environ.get('OSI_LOG') or f'/tmp/os-installer-{os.getuid()}.log'


class _Tee:
    def __init__(self, stream, file):
        self.stream = stream
        self.file = file

    def write(self, data):
        try:
            self.file.write(data)
            self.file.flush()
        except Exception:
            pass
        return self.stream.write(data)

    def flush(self):
        try:
            self.file.flush()
        except Exception:
            pass
        return self.stream.flush()

    def isatty(self):
        return False


def install(path=None):
    """Send stdout/stderr to the terminal *and* the log file."""
    path = path or LOG_PATH
    try:
        os.makedirs(os.path.dirname(path) or '.', exist_ok=True)
        file = open(path, 'a', buffering=1)
    except OSError as error:
        print(f'Could not open the installer log {path}: {error}')
        return None
    sys.stdout = _Tee(sys.stdout, file)
    sys.stderr = _Tee(sys.stderr, file)
    try:
        from .config import config
        config.set('log_path', path)
    except Exception:
        pass
    print(f'Logging to {path}')
    return path