# SPDX-License-Identifier: GPL-3.0-or-later
"""Device model objects built from udisks data (and from demo placeholders).

Both bugs covered here are invisible until a second device exists: a mutable
default (`mount_points=[]`) and a class-level `Disk.partitions` list hand the
same list to every instance, so one disk's state leaks into another's.
"""

from os_installer.device_info import DeviceInfo, Disk


def test_devices_do_not_share_mount_points():
    first = DeviceInfo('First', 10, '10 GB', '/dev/first')
    second = DeviceInfo('Second', 10, '10 GB', '/dev/second')

    first.mount_points.append('/mnt/data')

    assert second.mount_points == []


def test_passed_mount_points_are_kept():
    info = DeviceInfo('Disk', 10, '10 GB', '/dev/x', mount_points=['/', '/home'])
    assert info.mount_points == ['/', '/home']


def test_disks_without_partitions_do_not_share_a_list():
    first = Disk('First', 10, '10 GB', '/dev/first', [])
    second = Disk('Second', 10, '10 GB', '/dev/second', [])

    first.partitions.append('leak')

    assert second.partitions == []


def test_disk_partitions_are_linked_to_the_efi_partition():
    partitions = [
        DeviceInfo('EFI', 512_000_000, '512 MB', '/dev/sda1', True),
        DeviceInfo('Root', 20_000_000_000, '20 GB', '/dev/sda2',
                   mount_points=['/']),
    ]
    disk = Disk('Disk', 100_000_000_000, '100 GB', '/dev/sda', partitions)

    assert disk.efi_partition == '/dev/sda1'
    assert all(p.efi_partition == '/dev/sda1' for p in partitions)
    assert disk.has_root_fs
    assert disk.has_mounted_fs
    assert disk.partitions is partitions


def test_disk_without_efi_partition():
    disk = Disk('Disk', 100, '100 GB', '/dev/sdb',
                [DeviceInfo('Data', 100, '100 GB', '/dev/sdb1')])

    assert disk.efi_partition == ''
    assert not disk.has_root_fs
    assert not disk.has_mounted_fs


def test_properties_are_readable_from_the_ui():
    info = DeviceInfo('My Disk', 123, '123 GB', '/dev/sdz', is_efi=True)
    assert (info.name, info.size, info.device_path) == ('My Disk', '123 GB', '/dev/sdz')
    assert info.size_number == 123
    assert info.is_efi
