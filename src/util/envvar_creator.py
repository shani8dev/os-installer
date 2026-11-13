# SPDX-License-Identifier: GPL-3.0-or-later

import os
import re

from gi.repository import GLib

from .config import config
from .installation_step import InstallationStep


def _get(var):
    if not config.has(var) and not config.is_test():
        print(f'Required variable {var} not set, using empty string fallback. '
              'Please report this error.')
        return ''
    else:
        value = config.get(var)
        if isinstance(value, bool):
            return 1 if value else 0
        elif isinstance(value, tuple):
            return value[0]
        else:
            return value


def _get_device_path():
    if disk := config.get('chosen_device'):
        return disk.device_path
    else:
        print('Internal Error: No chosen disk set!')
        return ''


def _get_locale():
    if language := config.get('language_chosen'):
        return language.locale
    print('Internal Error: No language chosen, using the C locale.')
    return 'C.UTF-8'


def _get_username():
    if config.get('user')['request_username']:
        if username := config.get('user_username'):
            return username
    # This sticks to common linux username rules:
    # * starts with a lowercase letter
    # * only lowercase letters, numbers, underscore (_), and dash (-)
    # If the generation fails (including when the user page is skipped and
    # user_name is still ''), a fallback is used.
    asciified = GLib.str_to_ascii(config.get('user_name') or '').lower()
    filtered = re.sub(r'[^a-z0-9-_]+', '', asciified)
    if (position := re.search(r'[a-z]', filtered)) is None:
        return 'user'
    return filtered[position.start():]


def _parse_choices(choices_var):
    keywords = []
    for choice in _get(choices_var):
        if choice.options:
            keywords.append(choice.state.keyword)
        elif choice.state:
            keywords.append(choice.keyword)
    return ' '.join(keywords)


def _get_policy_vars():
    """The distro's install policy, as the scripts used to hardcode it.

    Everything here used to be a constant at the top of install.sh/configure.sh
    (labels, subvolumes, image paths, boot entries), which meant the installer
    could not know it, show it, or change it. The installer owns it now and
    exports it; a script reads OSI_* and keeps a fallback for an older
    installer.
    """
    policy = config.get('install_policy')

    layout = policy['partition_layout']
    if not os.path.isabs(layout):
        layout = str(config.base_path / layout)

    values = {
        'OSI_OS_NAME': policy['os_name'],
        'OSI_ROOT_LABEL': policy['root_label'],
        'OSI_BOOT_LABEL': policy['boot_label'],
        'OSI_PARTITION_LAYOUT': layout,
        'OSI_BTRFS_SUBVOLUMES': ' '.join(policy['btrfs_subvolumes']),
        'OSI_BTRFS_TOP_OPTS': policy['btrfs_top_options'],
        'OSI_SWAPFILE_PATH': policy['swapfile_path'],
        'OSI_IMAGE_DIR': policy['image_dir'],
        'OSI_ROOTFS_IMAGE': policy['rootfs_image'],
        'OSI_FLATPAK_IMAGE': policy['flatpak_image'],
        'OSI_SNAP_IMAGE': policy['snap_image'],
        'OSI_AI_MODELS_IMAGE': policy['ai_models_image'],
        'OSI_KERNEL_CMDLINE_CURRENT': policy['kernel_cmdline_current'],
        'OSI_KERNEL_CMDLINE_CANDIDATE': policy['kernel_cmdline_candidate'],
        'OSI_UKI_BOOT_ENTRIES': policy['uki_boot_entries'],
        'OSI_SKIP_USER': _get('skip_user'),
        'OSI_SKIP_REGION': _get('skip_region'),
        'OSI_MIN_PASSWORD_LENGTH': config.get('user')['min_password_length'],
    }
    return [f'{name}={value}' for name, value in values.items()]


def create_envs(installation_step: InstallationStep):
    with_configure_envs = installation_step is InstallationStep.configure
    with_install_envs = installation_step is InstallationStep.install or with_configure_envs

    envs = _get_policy_vars()
    if with_install_envs:
        envs += [
            f"OSI_DESKTOP={_get('desktop_chosen')}",
            f"OSI_LOCALE={_get_locale()}",
            f"OSI_KEYBOARD_LAYOUT={_get('keyboard_layout')}",
            f"OSI_DEVICE_PATH={_get_device_path()}",
            f"OSI_DEVICE_IS_PARTITION={_get('disk_is_partition')}",
            f"OSI_DEVICE_EFI_PARTITION={_get('disk_efi_partition')}",
            f"OSI_USE_ENCRYPTION={_get('use_encryption')}",
            f"OSI_ENCRYPTION_PIN={_get('encryption_pin')}",
            # Secure Boot: stage MOK enrollment (configure.sh does it in the
            # target chroot, where /etc/shadow is the installed one).
            f"OSI_MOK_ENROLL={_get('mok_enroll')}",
            f"OSI_MOK_PASSWORD={_get('mok_password')}",
            f"OSI_MOK_ROOT_PW={_get('mok_root_pw')}",
            # TPM auto-unlock: enrolled on the first boot of the installed
            # system (gen-efi enroll-tpm2 needs the booted LUKS mapper).
            f"OSI_USE_TPM={_get('use_tpm')}",
        ]

    if with_configure_envs:
        envs += [
            f"OSI_USER_NAME={_get('user_name')}",
            f"OSI_USER_USERNAME={_get_username()}",
            f"OSI_USER_AUTOLOGIN={_get('user_autologin')}",
            f"OSI_USER_GROUPS={' '.join(config.get('user').get('groups') or [])}",
            f"OSI_USER_PASSWORD={_get('user_password')}",
            f"OSI_ROOT_PASSWORD={_get('root_password')}",
            f"OSI_HOSTNAME={_get_hostname()}",
            f"OSI_FORMATS={_get('formats')}",
            f"OSI_TIMEZONE={_get('timezone')}",
            f"OSI_ADDITIONAL_SOFTWARE={_parse_choices('software_choices')}",
            f"OSI_ADDITIONAL_FEATURES={_parse_choices('feature_choices')}",
        ]
    return envs + [None]


def _get_hostname():
    """A fixed hostname from the config, else the one typed on the page."""
    if hostname := config.get('hostname'):
        return hostname
    return config.get('hostname_chosen') or 'shanios'
