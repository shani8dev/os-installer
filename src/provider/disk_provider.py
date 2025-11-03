# SPDX-License-Identifier: GPL-3.0-or-later

from random import getrandbits

from gi.repository import GLib, GObject

from .config import config
from .device_info import DeviceInfo, Disk
from .preloadable import Preloadable

class DeviceMountInfo():
    def __init__(self, mount_points=None, cleartext_device=None):
        self.mount_points = mount_points or []
        self.cleartext_device = cleartext_device

class DiskProvider(Preloadable):

    EFI_PARTITION_GUID = 'C12A7328-F81F-11D2-BA4B-00A0C93EC93B'
    EFI_PARTITON_FLAGS = None

    def __init__(self):
        super().__init__(self._init_client)

    def _init_client(self):
        min_disk_size = config.get('disk')['min_size']

        # avoids initializing udisks client in demo mode
        self.use_dummy_implementation = config.is_demo()
        if self.use_dummy_implementation:
            # fake it till you make it
            min_disk_size_str = f'{min_disk_size / 1000000000:.1f} GB'
            config.set('min_disk_size_str', min_disk_size_str)
            return

        import gi                            # noqa: E402
        gi.require_version('UDisks', '2.0')  # noqa: E402
        from gi.repository import UDisks
        self.EFI_PARTITON_FLAGS = UDisks.PartitionTypeInfoFlags.SYSTEM.numerator
        self.udisks_client = UDisks.Client.new_sync()

        # Load LVM module in case it's configured to be on-demand
        manager = self.udisks_client.get_manager()
        modules = GLib.Variant('as', ['lvm2'])
        manager.call_enable_modules_sync(modules, None)

        config.set('min_disk_size_str', self._disk_size_to_str(min_disk_size))

    def _disk_size_to_str(self, size):
        return self.udisks_client.get_size_for_display(size, False, False)

    def _get_partition_info(self, partition_name, partition, block, device_mount_map):
        partition_label = block.props.id_label.strip()
        if not partition_label:
            # Translators: Fallback name for partitions that don't have a name
            name = _("Unnamed Partition")
        else:
            # Translators: Squiggly brackets are replaced with partition name
            partition_str = _("{} (Partition)")
            name = partition_str.format(partition_label)

        # Get mount points for this partition if any exist
        mount_points = []
        partition_object = self.udisks_client.get_object(partition_name)

        # Check direct filesystem
        if filesystem := partition_object.get_filesystem():
            mount_points.extend(filesystem.props.mount_points)

        # Check for mount points below this partition (via LUKS, LVM, etc.)
        if partition_name in device_mount_map:
            mount_points.extend(device_mount_map[partition_name].mount_points)

        return DeviceInfo(
            name=name,
            size=block.props.size,
            size_text=self._disk_size_to_str(block.props.size),
            device_path=block.props.device,
            is_efi=partition.props.type.upper() == self.EFI_PARTITION_GUID,
            mount_points=mount_points)

    def _get_partitions(self, partition_table, device_mount_map):
        if not partition_table:
            return None

        partitions = []
        for partition_name in partition_table.props.partitions:
            partition_object = self.udisks_client.get_object(partition_name)
            if not partition_object:
                continue
            block = partition_object.get_block()
            partition = partition_object.get_partition()
            if block and partition:
                partitions.append(self._get_partition_info(partition_name, partition, block, device_mount_map))
            else:
                print('Unhandled partiton in partition table, ignoring.')

        return partitions

    def _get_disk_info(self, block, drive, partition_table, device_mount_map):
        if not (name := (f'{drive.props.vendor} {drive.props.model}'.strip())):
            # Translators: Fallback name for partitions that don't have a name
            name = _("Unnamed Disk")
        return Disk(
            name=name,
            size=block.props.size,
            size_text=self._disk_size_to_str(block.props.size),
            device_path=block.props.device,
            partitions=self._get_partitions(partition_table, device_mount_map))

    def _get_dummy_disks(self):
        return [
            Disk("Dummy", 10000, "10 KB", "/dev/null",
                 [DeviceInfo("Too small partiton", 1000, "1 KB", "/dev/00null")]),
            Disk("Totally real device", 100000000000, "100 GB", "/dev/sda", [
                DeviceInfo("EFI", 200000000, "2 GB", "/dev/sda_efi", True),
                DeviceInfo("Previous Installation", 20000000000, "40 GB",
                           "/dev/sda_yes"),
                DeviceInfo(_("Unnamed Partition"), 20000000000, "30 GB", "/dev/sda_unnamed"),
                DeviceInfo(_("Unnamed Partition"), 20000000000, "20 GB", "/dev/sda_unnamed2"),
                DeviceInfo("Swap", 20000000000, "8 GB", '/dev/sda_swap'),
            ]),
            Disk("VERY BIG DISK", 1000000000000000, "1000 TB",
                 "/dev/sdb_very_big", []),
        ]

    def _build_device_mount_map(self):
        """Build a mapping of device paths to mount points found anywhere below them in the device stack."""
        mount_map = {}

        dummy_var = GLib.Variant('a{sv}', None)
        manager = self.udisks_client.get_manager()
        devices = manager.call_get_block_devices_sync(dummy_var, None)

        # First pass: collect direct filesystems
        for device in devices:
            if not (udisks_object := self.udisks_client.get_object(device)):
                continue
            if not (block := udisks_object.get_block()):
                continue
            if udisks_object.get_loop():
                continue

            # If device has filesystem, store its mount points
            if (fs := udisks_object.get_filesystem()) and fs.props.mount_points:
                mount_map[device] = DeviceMountInfo(mount_points=list(fs.props.mount_points))

        # Second pass: handle LVM
        vg_mount_map = {}
        for device in devices:
            if not (udisks_object := self.udisks_client.get_object(device)):
                continue
            if not (block := udisks_object.get_block()):
                continue
            if udisks_object.get_loop():
                continue

            if not (block_lvm2 := udisks_object.get_block_lvm2()):
                continue

            lv_path = block_lvm2.props.logical_volume
            if not lv_path or lv_path == '/':
                continue

            if device not in mount_map:
                continue

            if not (lv_object := self.udisks_client.get_object(lv_path)):
                continue
            if not (lv := lv_object.get_logical_volume()):
                continue

            vg_path = lv.props.volume_group
            if vg_path not in vg_mount_map:
                vg_mount_map[vg_path] = []
            vg_mount_map[vg_path].extend(mount_map[device].mount_points)

        # Propagate VG mount points to PVs
        for device in devices:
            if not (udisks_object := self.udisks_client.get_object(device)):
                continue

            if not (pv := udisks_object.get_physical_volume()):
                continue

            vg_path = pv.props.volume_group
            if vg_path in vg_mount_map:
                if device not in mount_map:
                    mount_map[device] = DeviceMountInfo()
                mount_map[device].mount_points.extend(vg_mount_map[vg_path])

        # Third pass: handle LUKS (propagate cleartext mount points to backing device)
        for device in devices:
            if not (udisks_object := self.udisks_client.get_object(device)):
                continue
            if not (block := udisks_object.get_block()):
                continue
            if udisks_object.get_loop():
                continue

            if backing_device := block.props.crypto_backing_device:
                if device in mount_map:
                    if backing_device not in mount_map:
                        mount_map[backing_device] = DeviceMountInfo()
                    mount_map[backing_device].mount_points.extend(mount_map[device].mount_points)
                    mount_map[backing_device].cleartext_device = device

        return mount_map

    ### public methods ###

    def disk_exists(self, dev_info: DeviceInfo):
        self.assert_preloaded()

        if self.use_dummy_implementation:
            return True

        # check against all available devices
        dummy_var = GLib.Variant('a{sv}', None)
        manager = self.udisks_client.get_manager()
        devices = manager.call_get_block_devices_sync(dummy_var, None)
        for device in devices:
            if ((udisks_object := self.udisks_client.get_object(device)) and
                (block := udisks_object.get_block()) and
                    block.props.device == dev_info.device_path):
                return True

        return False

    def unmount_filesystems(self, dev_info: DeviceInfo) -> str:
        """Unmount all filesystems on device. Returns error message or empty string on success."""
        self.assert_preloaded()

        if self.use_dummy_implementation:
            return ""

        device_mount_map = self._build_device_mount_map()

        # Find the block device
        dummy_var = GLib.Variant('a{sv}', None)
        manager = self.udisks_client.get_manager()
        devices = manager.call_get_block_devices_sync(dummy_var, None)

        for device in devices:
            udisks_object = self.udisks_client.get_object(device)
            if not udisks_object:
                continue

            block = udisks_object.get_block()
            if not block or block.props.device != dev_info.device_path:
                continue

            # Get partition table and unmount all partitions
            if not (partition_table := udisks_object.get_partition_table()):
                continue

            for partition_name in partition_table.props.partitions:
                if not (partition_object := self.udisks_client.get_object(partition_name)):
                    continue

                if partition_object.get_encrypted() and partition_name in device_mount_map:
                    # For encrypted partitions, unmount the cleartext device filesystem
                    mount_info = device_mount_map[partition_name]
                    if not mount_info.cleartext_device:
                        continue

                    if not (cleartext_obj := self.udisks_client.get_object(mount_info.cleartext_device)):
                        continue

                    fs = cleartext_obj.get_filesystem()
                    if not (fs and fs.props.mount_points):
                        continue

                    try:
                        fs.call_unmount_sync(GLib.Variant('a{sv}', {}), None)
                    except Exception as e:
                        return str(e)
                else:
                    # For non-encrypted partitions, unmount direct filesystem
                    filesystem = partition_object.get_filesystem()
                    if not (filesystem and filesystem.props.mount_points):
                        continue

                    try:
                        filesystem.call_unmount_sync(GLib.Variant('a{sv}', {}), None)
                    except Exception as e:
                        return str(e)

            # Process dbus event queue so filesystem property changes are
            # visible to the caller
            context = GLib.MainContext.default()
            while context.pending():
                context.iteration(False)

            return ""

        return "Device not found"

    def get_disks(self):
        self.assert_preloaded()

        if self.use_dummy_implementation:
            return self._get_dummy_disks()

        if config.is_test() and getrandbits(3) == 7:
            print("test-mode: randomly chose that no disks are available")
            return []

        # get available devices
        dummy_var = GLib.Variant('a{sv}', None)
        manager = self.udisks_client.get_manager()
        devices = manager.call_get_block_devices_sync(dummy_var, None)
        device_mount_map = self._build_device_mount_map()

        # get device information
        disks = []
        for device in devices:
            udisks_object = self.udisks_client.get_object(device)
            if not udisks_object:
                continue

            # skip partitions
            partition = udisks_object.get_partition()
            if partition:
                continue

            block = udisks_object.get_block()
            if not block:
                continue

            partition_table = udisks_object.get_partition_table()

            drive = self.udisks_client.get_drive_for_block(block)
            if drive and not drive.props.optical:
                disk_info = self._get_disk_info(block, drive, partition_table, device_mount_map)
                disks.append(disk_info)

        return disks


disk_provider = DiskProvider()
