# SPDX-License-Identifier: GPL-3.0-or-later
"""Password strength: libpwquality's verdict plus a small meter.

`pam_pwquality` is what the system actually enforces, so its message is the
honest one ("the password is shorter than 8 characters"). Arch ships the C
library but no Python binding, so this talks to `libpwquality` with ctypes;
if the library is missing the heuristic below still gives a rough meter.

The distro's `user.min_password_length` remains the policy: this is a hint.
"""

import ctypes
import re

try:                      # the app installs gettext's _ into builtins
    _
except NameError:         # imported by the tests without it
    def _(text):
        return text

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

_library = None


def _pwquality():
    global _library
    if _library is not None:
        return _library or None
    lib = None
    for name in ('libpwquality.so.1', 'libpwquality.so'):
        try:
            lib = ctypes.CDLL(name)
            break
        except OSError:
            continue
    if lib is not None:
        lib.pwquality_default_settings.restype = ctypes.c_void_p
        lib.pwquality_free_settings.argtypes = [ctypes.c_void_p]
        lib.pwquality_check.argtypes = [
            ctypes.c_void_p, ctypes.c_char_p, ctypes.c_char_p,
            ctypes.c_char_p, ctypes.POINTER(ctypes.c_void_p)]
        lib.pwquality_check.restype = ctypes.c_int
        lib.pwquality_get_strerror.argtypes = [ctypes.c_int]
        lib.pwquality_get_strerror.restype = ctypes.c_char_p
    _library = lib or False
    return _library or None


def check(password):
    """(ok, message) from libpwquality; (None, '') when it is unavailable."""
    lib = _pwquality()
    if lib is None:
        return None, ''
    settings = lib.pwquality_default_settings()
    if not settings:
        return None, ''
    error = ctypes.c_void_p()
    try:
        code = lib.pwquality_check(
            settings, password.encode(), None, None, ctypes.byref(error))
    finally:
        lib.pwquality_free_settings(settings)
    if code == 0:
        return True, ''
    message = lib.pwquality_get_strerror(code)
    return False, (message.decode() if message else '')


def score(text):
    """0 (too short) .. 4 (strong) — the meter, not the policy."""
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


def hint(text):
    """The line to show under the field, with pwquality's reason when it has one."""
    if not text:
        return ''
    strength = label(text)
    ok, message = check(text)
    if ok is False and message:
        # Translators: Followed by the strength, then libpwquality's reason.
        return _("Password strength: {} — {}").format(strength, message)
    # Translators: Followed by the strength.
    return _("Password strength: {}").format(strength)