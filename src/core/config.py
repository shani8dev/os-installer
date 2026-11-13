# SPDX-License-Identifier: GPL-3.0-or-later

from copy import deepcopy
from enum import Enum
from pathlib import Path
from threading import Lock
import traceback
import yaml


class RunMode(Enum):
    default = 0
    test = 1
    demo = 2


default_config = {
    # general
    'distribution_name': 'Untitled',
    'scripts': {'prepare': None, 'install': None, 'configure': None},
    # internet
    'internet': {
        'connection_required': True,
        'checker_url': 'http://nmcheck.gnome.org/check_network_status.txt'
    },
    # language
    'fixed_language': False,
    # welcome
    'welcome_page': {'usage': True, 'logo': None, 'text': None},
    # disk
    'disk': {'partition_ok': False, 'min_size': 5},
    'disk_encryption': {'offered': True, 'forced': False, 'generated': False, 'min_length': 1, 'confirmation': False},
    # desktop
    'desktop': [],
    # user
    'user': {'min_password_length': 1, 'request_username': False, 'provide_autologin': False, 'password_confirmation': False},
    # optional pages
    'skip_region': False,
    'skip_user': False,
    # installation policy: the distro-specific values the install scripts
    # used to hardcode. The installer validates them, exports them as OSI_*
    # and owns the decisions it can make itself (e.g. who may install).
    'install_policy': {
        'os_name': 'shanios',
        'root_label': 'shani_root',
        'boot_label': 'shani_boot',
        'partition_layout': 'bits/part.sfdisk',
        'btrfs_subvolumes': ['@root', '@home', '@data', '@nix', '@cache',
                             '@log', '@flatpak', '@snapd', '@waydroid',
                             '@containers', '@machines', '@lxc', '@lxd',
                             '@libvirt', '@qemu', '@swap', '@shani-chronoa'],
        'btrfs_top_options': 'defaults,noatime,compress=zstd,space_cache=v2,autodefrag',
        'swapfile_path': '@swap/swapfile',
        'image_dir': '/run/archiso/bootmnt/shanios/x86_64',
        'rootfs_image': 'rootfs.zst',
        'flatpak_image': 'flatpakfs.zst',
        'snap_image': 'snapfs.zst',
        'ai_models_image': 'aimodelsfs.zst',
        'kernel_cmdline_current': '/etc/kernel/install_cmdline_blue',
        'kernel_cmdline_candidate': '/etc/kernel/install_cmdline_green',
        'uki_boot_entries': '/boot/efi/loader/entries',
        # Groups allowed to run the install. Root is always allowed; an
        # empty list disables the check (a distro that uses polkit only).
        'admin_groups': ['wheel', 'sudo'],
    },
    # software
    'additional_software': [],
    # feature
    'additional_features': [],
    # install
    'install_slideshow': [],
    # fail
    'failure_help_url': 'https://duckduckgo.com/?q="os-installer {}"+"failed installation"',
    # commands
    'commands': {'browser': 'epiphany', 'disks': 'gnome-disks', 'reboot': 'reboot', 'wifi': 'gnome-control-center wifi'},
}

legacy_values = {
    'offer_disk_encryption': ['disk_encryption', 'offered'],
    'minimum_disk_size': ['disk', 'min_size'],
    'internet_connection_required': ['internet', 'connection_required'],
    'internet_checker_url': ['internet', 'checker_url'],
    'browser_cmd': ['commands', 'browser'],
    'disks_cmd': ['commands', 'disks'],
    'wifi_cmd': ['commands', 'wifi'],
    'skip_locale': ['skip_region'],
    'suggested_languages': None,
}

# not configurable via config file
internal_values = {
    # configurations
    'internet_connection': False,
    'use_encryption': False,
    'encryption_pin': '',
    'root_password': '',
    'desktop_chosen': ('', ''),
    'user_name': '',
    'user_username': '',
    'user_autologin': False,
    'user_password': '',
    'formats': ('en_US.UTF-8', 'United States'),
    'timezone': 'UTC',
    'feature_choices': {},
    'software_choices': {},
    # other
    'installation_running': False,
    'logged-error': None,
    'min_disk_size_str': '',
    'send_notification': None,
    'terminal-placeholder': None,
    'display-toast': None,
    'version': -1,
}

fallback_values = {
    'available_translations': ['en_US'],
    'language_use_fixed': False,
    'language_chosen': None,
    'keyboard_language': ('en_US', 'English (US)'),
    'keyboard_layout': ('us', 'English (US)'),
    'chosen_device': None,
    'disk_is_partition': False,
    'disk_efi_partition': '/dev/null',
    'internet_page_image': 'network-wireless-disabled-symbolic',
    'welcome_page_image': 'weather-clear-symbolic',
}


def _match(variables, var, *ok_types):
    if not var in variables:
        print(f'Config error: {var} does not exist.')
        return False
    elif type(variables[var]) not in ok_types:
        print(f'Config error: {var} not of expected type (expected ',
              f'{ok_types}, but got {type(variables[var])})')
        return False
    else:
        return True


def _validate_scripts(variables):
    scripts = variables.get('scripts', None)
    if (not _match(variables, 'scripts', dict) or
            (scripts['install'] is None and scripts['configure'] is None)):
        print('Config error: Either install or configure script must exist. '
              'This setup will not be able to install anything.')
        return False
    return True


def _validate(variables):
    assert not variables['fixed_language'] == True, 'Need to specify or disable fixed language.'

    return (
        _match(variables, 'welcome_page', dict) and
        _match(variables['welcome_page'], 'usage', bool) and
        _match(variables['welcome_page'], 'logo', str, type(None)) and
        _match(variables['welcome_page'], 'text', str, type(None)) and
        _match(variables, 'internet', dict) and
        _match(variables['internet'], 'connection_required', bool) and
        _match(variables['internet'], 'checker_url', str) and
        _match(variables, 'disk', dict) and
        _match(variables['disk'], 'min_size', int, float) and
        _match(variables['disk'], 'partition_ok', bool) and
        _match(variables, 'disk_encryption', dict) and
        _match(variables['disk_encryption'], 'offered', bool) and
        _match(variables['disk_encryption'], 'forced', bool) and
        _match(variables['disk_encryption'], 'generated', bool) and
        _match(variables['disk_encryption'], 'min_length', int) and
        _match(variables['disk_encryption'], 'confirmation', bool) and
        _match(variables, 'user', dict) and
        _match(variables['user'], 'min_password_length', int) and
        _match(variables['user'], 'request_username', bool) and
        _match(variables['user'], 'provide_autologin', bool) and
        _match(variables['user'], 'password_confirmation', bool) and
        _match(variables, 'additional_software', list) and
        _match(variables, 'additional_features', list) and
        _match(variables, 'install_slideshow', list) and
        _match(variables, 'distribution_name', str) and
        _match(variables, 'fixed_language', bool, str) and
        _validate_install_policy(variables))


def _validate_install_policy(variables):
    policy = variables.get('install_policy')
    if not _match(variables, 'install_policy', dict):
        return False

    text_keys = ('os_name', 'root_label', 'boot_label', 'partition_layout',
                 'btrfs_top_options', 'swapfile_path', 'image_dir',
                 'rootfs_image', 'flatpak_image', 'snap_image',
                 'ai_models_image', 'kernel_cmdline_current',
                 'kernel_cmdline_candidate', 'uki_boot_entries')
    for key in text_keys:
        if not _match(policy, key, str):
            return False

    for key in ('btrfs_subvolumes', 'admin_groups'):
        values = policy.get(key)
        if not isinstance(values, list) or not all(isinstance(v, str) for v in values):
            print(f'Config error: install_policy.{key} must be a list of strings')
            return False

    return True


class Config:
    def __init__(self):
        # A copy, never the module-level dict: init() and _preprocess_values()
        # mutate values (e.g. min_size is multiplied by 1000^3), so sharing it
        # would grow it again on every Config()/init(), and a fallback to the
        # defaults after a broken config would inherit the mutated values.
        self.variables = deepcopy(default_config)
        self.subscription_lock = Lock()
        self.subscriptions = {}
        self.initialized = False
        self.run_mode = RunMode.default

    def _internal_error(self, message):
        print(f'Internal error: {message}')
        if self.run_mode == RunMode.test:
            traceback.print_stack()

    def _load_from_file(self, file):
        # safe_load: the config file is data. The default Loader can build
        # arbitrary Python objects (!!python/object/apply), i.e. run code, and
        # /etc/os-installer/config.yaml is writable by anyone who can write to
        # /etc — no reason for the installer to accept more than YAML values.
        config_from_file = yaml.safe_load(file)
        if not isinstance(config_from_file, dict):
            raise ValueError('Config file must contain a mapping at the top level')
        for config_property in config_from_file:
            if config_property in legacy_values:
                self._handle_legacy(
                    config_property, config_from_file[config_property])
            elif not config_property in default_config:
                print(f'Ignoring unknown config for "{config_property}"')
            elif type(self.variables[config_property]) is dict:
                for key, value in config_from_file[config_property].items():
                    self.variables[config_property][key] = value
            else:
                self.variables[config_property] = config_from_file[config_property]

    def _handle_legacy(self, legacy_prop, legacy_val):
        replacement = legacy_values[legacy_prop]

        # moved
        if type(replacement) == list:
            # hardcoded for depth of 2, can be made variable if needed
            print(f'Developer hint: "{legacy_prop}" is deprecated, '
                  f'use "{str.join(" -> ", replacement)}" instead')
            vars = self.variables
            match len(replacement):
                case 1:
                    self.variables[replacement[0]] = legacy_val
                case 2:
                    self.variables[replacement[0]][replacement[1]] = legacy_val
                case _:
                    print('Internal error: Unhandled legacy replacement')
        # removed
        elif replacement == None:
            match legacy_prop:
                case 'suggested_languages':
                    reason = ', instead all languages with translations are listed'
                case _:
                    reason = ' without replacement'
            print(f'Developer hint: "{legacy_prop}" has been removed{reason}')
        # conditional replacement
        elif len(replacement) == 4:
            new_var, compare_val, new1, new2 = replacement
            print(f'Developer hint: "{legacy_prop}" is deprecated, '
                  f'use "{new_var}" instead')
            self.variables[new_var] = new1 if legacy_val == compare_val else new2

    def _preprocess_values(self):
        GIGABYTE_FACTOR = 1000 * 1000 * 1000
        self.variables['disk']['min_size'] *= GIGABYTE_FACTOR

    def _update_subscribers(self, variable, new_value):
        subscribers = []
        with self.subscription_lock:
            if variable in self.subscriptions:
                subscribers = self.subscriptions[variable]
        for func in subscribers:
            func(new_value)

    ### public methods ###

    def bump(self, variable):
        self._update_subscribers(variable, self.get(variable))

    def get(self, variable):
        if variable in self.variables:
            return self.variables[variable]
        elif variable in fallback_values:
            print(f'Using fallback value for {variable}')
            return fallback_values[variable]
        else:
            print(f'Requested "{variable}" not in config')
            return None

    def has(self, variable):
        return variable in self.variables

    def init(self, config_path, demo_mode, test_mode):
        # Start from a clean copy of the defaults every time, so a second
        # call (tests, a reload) cannot inherit the previous run's values or
        # multiply min_size again.
        #
        # Values set before the config was read are not part of the defaults
        # and must survive: the launcher sets available_translations between
        # importing this module and calling init().
        preset = {key: value for key, value in self.variables.items()
                  if key not in default_config}
        self.variables = deepcopy(default_config)
        self.variables.update(preset)

        if demo_mode and test_mode:
            print("Only one of demo and test mode can be set at a time! "
                  "Using demo mode.")
            self.run_mode = RunMode.demo
        elif demo_mode:
            self.run_mode = RunMode.demo
        elif test_mode:
            self.run_mode = RunMode.test

        self.base_path = Path('')

        use_default_error = None
        try:
            with open(config_path, 'r') as file:
                self._load_from_file(file)
            if not _validate(self.variables) or not _validate_scripts(self.variables):
                use_default_error = 'Config errors'
            else:
                self.base_path = Path(config_path).parent.absolute()
                print(f"Config base path is '{self.base_path}'")
        except FileNotFoundError as e:
            use_default_error = 'Could not find config file'
        except Exception as e:
            print(f'Error loading config: {e}')
            use_default_error = 'Check if the config contains syntax errors'

        if use_default_error:
            print(f'{use_default_error}. Running in demo mode.')
            self.variables = deepcopy(default_config)

            # Test default config to assure it doesn't contain errors
            if self.run_mode == RunMode.test and not _validate(default_config):
                print('Developer error: Default config contains errors!')
            self.run_mode = RunMode.demo

        self.variables.update(internal_values)
        self._preprocess_values()
        self.initialized = True

    def is_demo(self):
        return self.run_mode == RunMode.demo

    def is_test(self):
        return self.run_mode == RunMode.test

    def set(self, variable, new_value):
        '''Returns whether config was changed.'''
        if self.variables.get(variable, None) == new_value:
            return False

        if not self.initialized and not variable in fallback_values:
            # Non-config variables should have fallback values
            self._internal_error(f'Setting "{variable}" before config was read!')
        self.variables[variable] = new_value

        self._update_subscribers(variable, new_value)

        return True

    def set_next_page(self, page):
        '''Convenience function'''
        self.set('displayed-page', ('next', page))
        return False

    def steal(self, variable):
        if variable in self.variables:
            return self.variables.pop(variable)

    def subscribe(self, variable, func, delayed=False):
        with self.subscription_lock:
            if variable in self.subscriptions:
                self.subscriptions[variable].append(func)
            else:
                self.subscriptions[variable] = [func]
        if delayed:
            return
        if variable in self.variables:
            func(self.variables[variable])
        elif not variable in fallback_values:
            self._internal_error(f'Subscribing to unknown variable "{variable}"')

    def unsubscribe(self, obj):
        with self.subscription_lock:
            for subs in self.subscriptions.values():
                for func in subs:
                    if hasattr(func, '__self__') and func.__self__ == obj:
                        subs.remove(func)


config = Config()
