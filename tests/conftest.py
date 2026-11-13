# SPDX-License-Identifier: GPL-3.0-or-later
"""Shared fixtures for the installer's unit tests.

The source tree keeps the modules in folders (src/core, src/util), but the
*installed* package is flat: meson installs every .py into
/usr/share/os-installer/os_installer/, so a module does `from .config import
config`, not `from ..core.config import config`. The tests reproduce that
layout once, in a temp dir, and import `os_installer.<module>` — the same
modules, in the same shape, the installed app uses.
"""

import gi

gi.require_version("Vte", "3.91")

import shutil
import sys
import tempfile
from pathlib import Path

import pytest

SRC = Path(__file__).resolve().parents[1] / 'src'
PKG = Path(tempfile.mkdtemp(prefix='os-installer-tests-')) / 'os_installer'
PKG.mkdir(parents=True)
for source in SRC.rglob('*.py'):
    shutil.copy2(source, PKG / source.name)
sys.path.insert(0, str(PKG.parent))


@pytest.fixture
def fresh_config():
    """A Config() that never touches the module-level singleton."""
    from os_installer.config import Config
    return Config()


@pytest.fixture
def config_file(tmp_path):
    """Write a minimal, valid distro config and return its path."""
    import textwrap

    path = tmp_path / 'config.yaml'
    path.write_text(textwrap.dedent("""\
        distribution_name: 'Test OS'

        scripts:
          prepare: prepare.sh
          install: install.sh
          configure: configure.sh

        internet:
          connection_required: no
          checker_url: 'http://nmcheck.gnome.org/check_network_status.txt'

        fixed_language: en_US
        skip_region: yes
        skip_user: yes

        disk:
          partition_ok: no
          min_size: 1
        """))
    return path