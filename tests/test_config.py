# SPDX-License-Identifier: GPL-3.0-or-later
"""Config loading: defaults, validation and the fallback to demo mode.

These are regressions for bugs that made a broken (or re-read) config change
the installer's behaviour in ways nothing on screen explains.
"""

import pytest
import yaml

from os_installer import config as config_module
from os_installer.config import Config, default_config


def test_init_does_not_mutate_the_module_defaults(fresh_config, config_file):
    fresh_config.init(str(config_file), False, False)
    # min_size is converted from GB to bytes during init.
    assert fresh_config.get('disk')['min_size'] == 1_000_000_000
    assert default_config['disk']['min_size'] == 5


def test_second_init_is_not_multiplied_again(fresh_config, config_file):
    fresh_config.init(str(config_file), False, False)
    second = Config()
    second.init(str(config_file), False, False)
    assert second.get('disk')['min_size'] == 1_000_000_000


def test_missing_config_falls_back_to_demo_without_touching_defaults(tmp_path):
    cfg = Config()
    cfg.init(str(tmp_path / 'nope.yaml'), False, False)
    assert cfg.is_demo()
    cfg.init(str(tmp_path / 'nope.yaml'), False, False)
    assert cfg.is_demo()
    assert default_config['disk']['min_size'] == 5


def test_yaml_loader_does_not_execute_python_objects(tmp_path):
    """A crafted config must never run code (safe_load, not Loader)."""
    marker = tmp_path / 'pwned'
    path = tmp_path / 'config.yaml'
    path.write_text(f'!!python/object/apply:os.system ["touch {marker}"]\n')

    cfg = Config()
    cfg.init(str(path), False, True)

    assert not marker.exists(), 'config file executed arbitrary Python'
    assert cfg.is_demo()


def test_non_mapping_config_is_rejected(fresh_config, tmp_path):
    path = tmp_path / 'config.yaml'
    path.write_text('- just\n- a list\n')
    fresh_config.init(str(path), False, True)
    assert fresh_config.is_demo()


def test_unknown_keys_are_ignored_not_fatal(fresh_config, config_file):
    data = yaml.safe_load(config_file.read_text())
    data['this_key_does_not_exist'] = 1
    config_file.write_text(yaml.safe_dump(data))

    fresh_config.init(str(config_file), False, False)
    assert not fresh_config.is_demo()
    assert not fresh_config.has('this_key_does_not_exist')


def test_invalid_disk_section_falls_back_to_demo(fresh_config, config_file):
    data = yaml.safe_load(config_file.read_text())
    data['disk'] = {'partition_ok': 'sometimes'}
    config_file.write_text(yaml.safe_dump(data))

    fresh_config.init(str(config_file), False, False)
    assert fresh_config.is_demo()


@pytest.mark.parametrize('section,bad', [
    ('secure_boot', {'offered': 'maybe'}),
    ('secure_boot', {'mok_password_min_length': 'four'}),
    ('tpm', {'offered': 'sometimes'}),
    ('tpm', {'pcrs': 7}),
])
def test_invalid_security_section_falls_back_to_demo(fresh_config, config_file,
                                                     section, bad):
    data = yaml.safe_load(config_file.read_text())
    data[section] = bad
    config_file.write_text(yaml.safe_dump(data))

    fresh_config.init(str(config_file), False, False)
    assert fresh_config.is_demo()


def test_offered_accepts_yaml_booleans(fresh_config, config_file):
    """`offered: yes` is the natural spelling; YAML 1.1 makes it a bool."""
    data = yaml.safe_load(config_file.read_text())
    data['secure_boot'] = {'offered': True}
    data['tpm'] = {'offered': False}
    config_file.write_text(yaml.safe_dump(data))

    fresh_config.init(str(config_file), False, False)

    assert not fresh_config.is_demo()
    assert fresh_config.get('secure_boot')['offered'] == 'yes'
    assert fresh_config.get('tpm')['offered'] == 'no'


def test_security_sections_merge_with_the_defaults(fresh_config, config_file):
    data = yaml.safe_load(config_file.read_text())
    data['secure_boot'] = {'offered': 'yes'}
    data['tpm'] = {'pcrs': '0+7'}
    config_file.write_text(yaml.safe_dump(data))

    fresh_config.init(str(config_file), False, False)
    assert not fresh_config.is_demo()
    assert fresh_config.get('secure_boot')['offered'] == 'yes'
    assert fresh_config.get('secure_boot')['mok_password_min_length'] == 1
    assert fresh_config.get('tpm')['pcrs'] == '0+7'
    assert fresh_config.get('tpm')['offered'] == 'auto'


def test_install_policy_defaults_are_valid():
    assert config_module._validate(config_module.default_config)


@pytest.mark.parametrize('bad', [
    {'root_label': 5},
    {'btrfs_subvolumes': '@root'},
    {'btrfs_subvolumes': ['@root', 2]},
    {'admin_groups': 'wheel'},
    {'image_dir': None},
])
def test_invalid_install_policy_falls_back_to_demo(fresh_config, config_file, bad):
    data = yaml.safe_load(config_file.read_text())
    data['install_policy'] = bad
    config_file.write_text(yaml.safe_dump(data))

    fresh_config.init(str(config_file), False, False)
    assert fresh_config.is_demo()


def test_install_policy_overrides_merge_with_the_defaults(fresh_config, config_file):
    data = yaml.safe_load(config_file.read_text())
    data['install_policy'] = {'root_label': 'test_root'}
    config_file.write_text(yaml.safe_dump(data))

    fresh_config.init(str(config_file), False, False)
    assert not fresh_config.is_demo()
    assert fresh_config.get('install_policy')['root_label'] == 'test_root'
    assert fresh_config.get('install_policy')['boot_label'] == 'shani_boot'


def test_demo_and_test_flags_are_exclusive(fresh_config, config_file):
    fresh_config.init(str(config_file), True, True)
    assert fresh_config.is_demo()
    assert not fresh_config.is_test()


def test_init_keeps_values_set_before_the_config_is_read(config_file):
    """The launcher sets available_translations before calling init()."""
    cfg = Config()
    cfg.variables['available_translations'] = ['en_US', 'de']
    cfg.init(str(config_file), False, False)
    assert cfg.get('available_translations') == ['en_US', 'de']


def test_subscribe_and_steal(monkeypatch):
    cfg = Config()
    # start from the internal defaults, as init() would leave them
    cfg.variables.update(config_module.internal_values)
    cfg.initialized = True

    seen = []
    cfg.subscribe('demo_event', seen.append)
    cfg.set('demo_event', 'value')
    assert seen and seen[-1] == 'value'

    cfg.set('demo_event', 'other')
    # steal returns once and removes it, like a one-shot queue
    assert cfg.steal('demo_event') == 'other'
    assert cfg.steal('demo_event') is None
