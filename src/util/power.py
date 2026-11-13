# SPDX-License-Identifier: GPL-3.0-or-later
"""Is this machine running on battery?

A formatting install takes a while and a flat battery mid-write is a bad
day; the other installers warn before the first page.
"""

import glob
import os


def on_battery():
    for type_path in glob.glob('/sys/class/power_supply/*/type'):
        try:
            with open(type_path) as file:
                if file.read().strip() != 'Battery':
                    continue
            status_path = os.path.join(os.path.dirname(type_path), 'status')
            with open(status_path) as file:
                return file.read().strip() == 'Discharging'
        except OSError:
            continue
    return False