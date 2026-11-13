# SPDX-License-Identifier: GPL-3.0-or-later
"""Is there already an install on this disk?

Repairing and "keep /data" only make sense if there is something to repair,
and the user should not have to know the distro's labels. `lsblk` is
read-only and needs no privileges, so it works from the live session.
"""

import json
import subprocess


def _device_path(name):
    if not name:
        return ''
    return name if name.startswith('/') else f'/dev/{name}'


def parse_lsblk(data):
    """{label: /dev/...} for the configured root/boot labels."""
    from .config import config
    policy = config.get('install_policy')
    wanted = {policy['root_label'], policy['boot_label']}
    found = {}

    def walk(node):
        label = node.get('label')
        if label in wanted:
            found[label] = _device_path(node.get('name'))
        for child in node.get('children') or []:
            walk(child)

    for device in data.get('blockdevices') or []:
        walk(device)
    return found or None


def find_existing(device_path):
    """The existing root/boot devices on a whole-disk target, or None."""
    if not device_path:
        return None
    try:
        result = subprocess.run(
            ['lsblk', '-J', '-b', '-o', 'NAME,LABEL,FSTYPE,TYPE,SIZE', device_path],
            capture_output=True, text=True, timeout=10)
    except (OSError, subprocess.SubprocessError):
        return None
    if result.returncode != 0 or not result.stdout.strip():
        return None
    try:
        return parse_lsblk(json.loads(result.stdout))
    except ValueError:
        return None