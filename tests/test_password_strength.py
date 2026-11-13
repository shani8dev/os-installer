# SPDX-License-Identifier: GPL-3.0-or-later
"""The password-strength hint (heuristic meter + libpwquality's reason)."""

from os_installer.password_strength import hint, score


def test_empty_has_no_hint():
    assert hint('') == ''
    assert score('') == 0


def test_score_follows_length_and_variety():
    assert score('123') == 0      # too short
    assert score('1234') == 1     # digits only
    assert score('abcdefgh') == 1
    assert score('abcdefgh1') == 2
    assert score('Abcdefgh1') == 3
    assert score('Abcdefgh1!') == 4
    assert score('Tr0ub4dor&3') == 4


def test_hint_names_the_strength():
    # libpwquality may or may not be present; the strength is always there.
    assert 'Weak' in hint('abcdefgh') or 'Okay' in hint('abcdefgh')