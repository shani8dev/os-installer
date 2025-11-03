#!/bin/python3

import gi                            # noqa: E402
gi.require_version('GLib', '2.0')    # noqa: E402
gi.require_version('UDisks', '2.0')  # noqa: E402
from gi.repository import GLib, UDisks


EFI_PARTITON_FLAGS = UDisks.PartitionTypeInfoFlags.SYSTEM.numerator
EFI_PARTITION_GUID = 'C12A7328-F81F-11D2-BA4B-00A0C93EC93B'
udisks_client = UDisks.Client.new_sync()


def size_to_str(size):
    return udisks_client.get_size_for_display(size, False, False)


dummy_var = GLib.Variant('a{sv}', None)
devices = udisks_client.get_manager().call_get_block_devices_sync(dummy_var, None)


print('Listing found devices:')

for device in devices:
    udisks_object = udisks_client.get_object(device)
    if not udisks_object:
        print(f'No udisks object: {device}')
        continue

    partition = udisks_object.get_partition()
    if partition:
        block = udisks_object.get_block()
        drive = udisks_client.get_drive_for_block(block)

        # Check filesystem for mount points
        if filesystem := udisks_object.get_filesystem():
            mount_points = f'mounted at {filesystem.props.mount_points}'
        else:
            mount_points = f'(not mounted)'

        name=f'{drive.props.vendor} {drive.props.model}'
        print(f'Is a partition: {name} {mount_points}')
        continue

    block = udisks_object.get_block()
    partition_table = udisks_object.get_partition_table()
    if not block:
        print(f'No block for {udisks_object}')
        print(f'  partition table: {partition_table}')
        continue

    if drive:= udisks_client.get_drive_for_block(block):
        drive_name = f'{drive.props.vendor} {drive.props.model}'
        if drive.props.optical:
            print(f'Drive ({drive_name}) is considered optical')
            continue
        if drive.props.size <= 0:
            print(f'ignored drive ({drive_name}) size {drive.props.size}')

        print(f'* Disk ({drive_name}), '
            f'size {size_to_str(block.props.size)}, path {block.props.device}:')

        if not partition_table:
            print('  drive has no partition table')
            continue
        for partition_name in partition_table.props.partitions:
            partition_object = udisks_client.get_object(partition_name)
            if not partition_object:
                print(f'  no udisks object for partition {partition_name}')
                continue

            block = partition_object.get_block()
            partition = partition_object.get_partition()
            if block and partition:
                efi = ''
                if partition.props.type.upper() == EFI_PARTITION_GUID:
                    efi = 'EFI '

                print(f'    * {efi}Partition #{partition.props.number} ("{block.props.id_label}"), size {size_to_str(block.props.size)}, path {block.props.device}')
            else:
                print('    * Unknow partition? Ignoring.')
    elif block.props.crypto_backing_device:
        if not udisks_object.get_loop():
            print(f'Device {device} is crypto backed by {block.props.crypto_backing_device}')
    else:
        print(f'Unhandled device {device}')
