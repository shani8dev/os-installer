# SPDX-License-Identifier: GPL-3.0-or-later
"""The OSI_* environment handed to the distro's scripts.

This is the entire contract between the installer GUI and os-installer-config,
and a wrong or missing value here fails on the target system, not on screen.
"""


import pytest

from os_installer.config import RunMode, config
from os_installer import envvar_creator
from os_installer.installation_step import InstallationStep
from os_installer.config import default_config
from os_installer.installation_scripting import _admin_problem


class Language:
    def __init__(self, locale):
        self.locale = locale


class Disk:
    def __init__(self, path):
        self.device_path = path


class Choice:
    """A choice row: either an expander (options) or a plain toggle."""

    def __init__(self, keyword, state=True, options=()):
        self.keyword = keyword
        self.state = state
        self.options = list(options)


class Option:
    """The selected entry of an expander row (choices_provider.Option)."""

    def __init__(self, keyword):
        self.keyword = keyword


@pytest.fixture(autouse=True)
def clean_config():
    from copy import deepcopy
    from pathlib import Path
    config.base_path = Path('/etc/os-installer')
    config.variables = {
        'user': {'request_username': False, 'min_password_length': 4,
                 'groups': ['wheel']},
        'hostname': None,
        'hostname_chosen': 'shanihost',
        'recovery_key': 'AAAA-BBBB-CCCC-DDDD-EEEE-FFFF-2222-3333',
        'use_tpm_pin': False,
        'tpm_pin': '',
        'time_sync': True,
        'copy_network': True,
        'disk_erase': 'quick',
        'skip_user': True,
        'skip_region': True,
        'install_policy': deepcopy(default_config['install_policy']),
        'mok_enroll': True,
        'mok_password': 'shanios',
        'mok_root_pw': False,
        'use_tpm': False,
        'desktop_chosen': ('gnome', 'GNOME'),
        'language_chosen': Language('en_US.UTF-8'),
        'keyboard_layout': ('us', 'English (US)'),
        'chosen_device': Disk('/dev/sda'),
        'disk_is_partition': False,
        'disk_efi_partition': '/dev/sda1',
        'use_encryption': True,
        'encryption_pin': '1234',
        'user_name': 'Shani User',
        'user_username': '',
        'user_autologin': True,
        'user_password': 'hunter2',
        'root_password': '',
        'formats': ('en_US.UTF-8', 'United States'),
        'timezone': 'Europe/Berlin',
        'software_choices': {},
        'feature_choices': {},
    }
    config.initialized = True
    config.run_mode = RunMode.default
    yield
    config.run_mode = RunMode.default


def envs(step):
    """create_envs() as a dict; the list ends with None for execve()."""
    result = envvar_creator.create_envs(step)
    assert result[-1] is None
    return dict(item.split('=', 1) for item in result[:-1])


@pytest.mark.parametrize('step', [InstallationStep.prepare, InstallationStep.none])
def test_prepare_gets_the_policy_but_not_the_install_values(step):
    values = envs(step)
    assert 'OSI_DEVICE_PATH' not in values
    assert 'OSI_USER_USERNAME' not in values
    assert values['OSI_ROOT_LABEL'] == 'shani_root'
    assert values['OSI_OS_NAME'] == 'shanios'


def test_install_envs_are_complete():
    values = envs(InstallationStep.install)
    expected = {
        'OSI_DESKTOP': 'gnome',
        'OSI_LOCALE': 'en_US.UTF-8',
        'OSI_KEYBOARD_LAYOUT': 'us',
        'OSI_DEVICE_PATH': '/dev/sda',
        'OSI_DEVICE_IS_PARTITION': '0',
        'OSI_DEVICE_EFI_PARTITION': '/dev/sda1',
        'OSI_USE_ENCRYPTION': '1',
        'OSI_ENCRYPTION_PIN': '1234',
    }
    for var, value in expected.items():
        assert values[var] == value, var


def test_install_policy_is_exported():
    """The values install.sh/configure.sh used to hardcode."""
    values = envs(InstallationStep.install)
    assert values['OSI_OS_NAME'] == 'shanios'
    assert values['OSI_ROOT_LABEL'] == 'shani_root'
    assert values['OSI_BOOT_LABEL'] == 'shani_boot'
    assert values['OSI_PARTITION_LAYOUT'] == '/etc/os-installer/bits/part.sfdisk'
    assert values['OSI_BTRFS_SUBVOLUMES'].split()[-1] == '@shani-chronoa'
    assert values['OSI_SWAPFILE_PATH'] == '@swap/swapfile'
    assert values['OSI_IMAGE_DIR'] == '/run/archiso/bootmnt/shanios/x86_64'
    assert values['OSI_KERNEL_CMDLINE_CURRENT'] == '/etc/kernel/install_cmdline_blue'
    assert values['OSI_UKI_BOOT_ENTRIES'] == '/boot/efi/loader/entries'
    assert values['OSI_SKIP_USER'] == '1'
    assert values['OSI_SKIP_REGION'] == '1'
    assert values['OSI_MIN_PASSWORD_LENGTH'] == '4'


def test_secure_boot_and_tpm_are_exported():
    values = envs(InstallationStep.configure)
    assert values['OSI_MOK_ENROLL'] == '1'
    assert values['OSI_MOK_PASSWORD'] == 'shanios'
    assert values['OSI_MOK_ROOT_PW'] == '0'
    assert values['OSI_USE_TPM'] == '0'

    config.variables['mok_root_pw'] = True
    config.variables['use_tpm'] = True
    values = envs(InstallationStep.configure)
    assert values['OSI_MOK_ROOT_PW'] == '1'
    assert values['OSI_USE_TPM'] == '1'


def test_security_envs_are_exported():
    values = envs(InstallationStep.configure)
    assert values['OSI_RECOVERY_KEY'] == 'AAAA-BBBB-CCCC-DDDD-EEEE-FFFF-2222-3333'
    assert values['OSI_TIME_SYNC'] == '1'
    assert values['OSI_COPY_NETWORK'] == '1'
    assert values['OSI_USE_TPM_PIN'] == '0'
    assert values['OSI_TPM_PIN'] == ''
    assert envs(InstallationStep.install)['OSI_DISK_ERASE'] == 'quick'

    config.variables['use_tpm_pin'] = True
    config.variables['tpm_pin'] = '4321'
    values = envs(InstallationStep.configure)
    assert values['OSI_USE_TPM_PIN'] == '1'
    assert values['OSI_TPM_PIN'] == '4321'


def test_hostname_and_groups_are_exported():
    values = envs(InstallationStep.configure)
    assert values['OSI_HOSTNAME'] == 'shanihost'
    assert values['OSI_USER_GROUPS'] == 'wheel'

    # A fixed hostname wins over the page.
    config.variables['hostname'] = 'fixed-host'
    assert envs(InstallationStep.configure)['OSI_HOSTNAME'] == 'fixed-host'


def test_policy_can_be_overridden_from_the_config():
    config.variables['install_policy'] = {
        **default_config['install_policy'],
        'root_label': 'fedora_root',
        'admin_groups': [],
    }
    values = envs(InstallationStep.install)
    assert values['OSI_ROOT_LABEL'] == 'fedora_root'


def test_install_policy_from_a_relative_layout_is_absolute():
    config.variables['install_policy'] = {
        **default_config['install_policy'],
        'partition_layout': 'bits/other.sfdisk',
    }
    assert envs(InstallationStep.install)['OSI_PARTITION_LAYOUT'] == \
        '/etc/os-installer/bits/other.sfdisk'


@pytest.mark.parametrize('euid,user,groups,expected', [
    (0, 'root', {'root'}, None),
    (1000, 'shani', {'wheel', 'users'}, None),
    (1000, 'shani', {'sudo'}, None),
    (1000, 'shani', {'users'}, 'administrator'),
    (1000, 'shani', set(), 'administrator'),
])
def test_admin_policy(euid, user, groups, expected):
    problem = _admin_problem({'admin_groups': ['wheel', 'sudo']},
                             euid, user, groups)
    if expected is None:
        assert problem is None
    else:
        assert expected in problem


def test_admin_check_can_be_disabled():
    assert _admin_problem({'admin_groups': []}, 1000, 'shani', set()) is None


def test_configure_envs_include_install_and_user_values():
    values = envs(InstallationStep.configure)
    assert values['OSI_DEVICE_PATH'] == '/dev/sda'
    assert values['OSI_USER_NAME'] == 'Shani User'
    assert values['OSI_USER_USERNAME'] == 'shaniuser'
    assert values['OSI_USER_AUTOLOGIN'] == '1'
    assert values['OSI_USER_PASSWORD'] == 'hunter2'
    assert values['OSI_ROOT_PASSWORD'] == ''
    assert values['OSI_FORMATS'] == 'en_US.UTF-8'
    assert values['OSI_TIMEZONE'] == 'Europe/Berlin'


def test_booleans_and_tuples_are_rendered_as_osi_expects():
    assert envvar_creator._get('use_encryption') == 1
    config.variables['use_encryption'] = False
    assert envvar_creator._get('use_encryption') == 0
    assert envvar_creator._get('keyboard_layout') == 'us'


def test_missing_variable_is_empty_string_not_a_crash(monkeypatch):
    monkeypatch.delitem(config.variables, 'use_encryption')
    assert envvar_creator._get('use_encryption') == ''


@pytest.mark.parametrize('name,expected', [
    ('Shani User', 'shaniuser'),
    ('José Pérez', 'joseperez'),
    ('9lives', 'lives'),
    ('123', 'user'),
    ('', 'user'),
    ('--weird--', 'weird--'),
])
def test_generated_username_follows_linux_rules(name, expected):
    config.variables['user_name'] = name
    assert envvar_creator._get_username() == expected


def test_requested_username_is_used_verbatim():
    config.variables['user']['request_username'] = True
    config.variables['user_username'] = 'custom_name'
    assert envvar_creator._get_username() == 'custom_name'


def test_requested_but_empty_username_falls_back_to_generated():
    # The user page can be skipped (skip_user: yes) while request_username
    # stays on, which only ever worked because the generated name is not used.
    config.variables['user']['request_username'] = True
    config.variables['user_username'] = ''
    config.variables['user_name'] = 'Shani User'
    assert envvar_creator._get_username() == 'shaniuser'


def test_missing_language_does_not_crash_the_install():
    config.variables['language_chosen'] = None
    assert envvar_creator._get_locale() == 'C.UTF-8'


def test_missing_chosen_device_does_not_crash_the_install():
    config.variables['chosen_device'] = None
    assert envvar_creator._get_device_path() == ''


def test_choices_are_keywords_for_both_row_kinds():
    """`feature_choices` is a list of Choice rows (see choices_provider)."""
    config.variables['feature_choices'] = [
        Choice('flatpak'),
        Choice('codecs', state=False),
        Choice('nested', state=Option('two'), options=[Option('one'), Option('two')]),
    ]
    # A plain row contributes when it is on; an expander row contributes the
    # selected option's keyword (not its own display name).
    assert envvar_creator._parse_choices('feature_choices') == 'flatpak two'
