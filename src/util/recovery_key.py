# SPDX-License-Identifier: GPL-3.0-or-later
"""The LUKS recovery key.

A PIN is something the user remembers; the recovery key is what they write
down. It is generated here, added as a LUKS keyslot by configure.sh, and
shown once on the done page — the installer never stores it anywhere else.
"""

import secrets

# RFC 4648 base32 (no padding), the alphabet cryptsetup's own recovery keys
# use: no 0/O/1/I/L, so it can be read back off paper.
ALPHABET = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ234567'


def generate(groups=8, size=6):
    return '-'.join(
        ''.join(secrets.choice(ALPHABET) for _ in range(size))
        for _ in range(groups))