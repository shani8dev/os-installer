# SPDX-License-Identifier: GPL-3.0-or-later
"""Detecting an install that is already on the target disk."""

from os_installer.install_detection import parse_lsblk


def test_labels_are_found_at_any_depth():
    data = {'blockdevices': [{
        'name': 'sda', 'children': [
            {'name': 'sda1', 'label': 'shani_boot'},
            {'name': 'sda2', 'label': 'shani_root', 'children': [
                {'name': 'luks-1', 'label': None},
            ]},
        ],
    }]}
    assert parse_lsblk(data) == {'shani_boot': '/dev/sda1',
                                 'shani_root': '/dev/sda2'}


def test_nvme_names_get_the_dev_prefix():
    data = {'blockdevices': [{'name': 'nvme0n1p3', 'label': 'shani_root'}]}
    assert parse_lsblk(data) == {'shani_root': '/dev/nvme0n1p3'}


def test_other_labels_are_ignored():
    data = {'blockdevices': [{'name': 'sda1', 'label': 'EFI system'},
                             {'name': 'sda2', 'label': 'Windows'}]}
    assert parse_lsblk(data) is None


def test_empty_output_is_not_an_install():
    assert parse_lsblk({}) is None
    assert parse_lsblk({'blockdevices': []}) is None