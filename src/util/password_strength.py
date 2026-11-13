# SPDX-License-Identifier: GPL-3.0-or-later
"""A small, honest password-strength hint.

Not a replacement for a policy (the distro's min_password_length still
decides what is accepted): this only tells the user how much better a longer
or more varied password would be, the way the other installers do.
"""

import re

LABELS = [
    # Translators: Password strength.
    _("Too short"),
    # Translators: Password strength.
    _("Weak"),
    # Translators: Password strength.
    _("Okay"),
    # Translators: Password strength.
    _("Good"),
    # Translators: Password strength.
    _("Strong"),
]


def score(text):
    """0 (too short) .. 4 (strong)."""
    if len(text) < 4:
        return 0
    points = 0
    if len(text) >= 8:
        points += 1
    if len(text) >= 12:
        points += 1
    if re.search(r'[a-z]', text) and re.search(r'[A-Z]', text):
        points += 1
    if re.search(r'[0-9]', text):
        points += 1
    if re.search(r'[^A-Za-z0-9]', text):
        points += 1
    return min(points, 4)


def label(text):
    return LABELS[score(text)]