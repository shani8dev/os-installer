# SPDX-License-Identifier: GPL-3.0-or-later
"""What the firmware and the TPM can do for this machine.

The Secure Boot and TPM pages show the state they will act on, instead of
asking the user to trust an option that the hardware cannot honour.
"""

import glob
import os


def secure_boot_state():
    """True/False, or None when this is not a UEFI machine."""
    if not os.path.isdir('/sys/firmware/efi/efivars'):
        return None
    for path in glob.glob('/sys/firmware/efi/efivars/SecureBoot-*'):
        try:
            with open(path, 'rb') as file:
                return file.read(5)[4] == 1
        except OSError:
            continue
    return None


def tpm_present():
    return bool(glob.glob('/dev/tpmrm*') or glob.glob('/sys/class/tpm/tpm[0-9]*'))