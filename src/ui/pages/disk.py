# SPDX-License-Identifier: GPL-3.0-or-later

import os

from gi.repository import Gio, Gtk

from .config import config
from .device_info import DeviceInfo, Disk
from .device_rows import DeviceChoiceRow, DeviceRootfsDiskRow, DeviceRow, DeviceTooSmallRow, DeviceMountedRow, NoEfiPartitionRow
from .disk_provider import disk_provider
from .functions import reset_model
from .install_detection import find_existing
from .translator import config_gettext
from .translations import translate_widgets


@Gtk.Template(resource_path='/org/shani/os-installer/ui/pages/disk.ui')
class DiskPage(Gtk.Stack):
    __gtype_name__ = __qualname__

    disk_list = Gtk.Template.Child()
    min_size_label = Gtk.Template.Child()
    existing_box = Gtk.Template.Child()
    existing_label = Gtk.Template.Child()
    existing_mode = Gtk.Template.Child()
    existing_continue = Gtk.Template.Child()
    disks_button = Gtk.Template.Child()
    no_disks_page = Gtk.Template.Child()
    reload_button = Gtk.Template.Child()

    disk_list_model = Gio.ListStore()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        translate_widgets(self.disks_button, self.no_disks_page,
                          self.reload_button)

        disk_conf = config.get('disk')
        self.minimum_disk_size = disk_conf['min_size']
        self.partition_ok = disk_conf['partition_ok']

        self.min_size_label.set_label(
            # Translators: Followed by a size in GB.
            _("Requires at least {} GB free.").format(
                f'{self.minimum_disk_size / 1000000000:.0f}'))

        # The choices are built here, not in Blueprint: a Gtk.StringList in a
        # template needs the newer `strings:` syntax.
        mode_model = Gtk.StringList()
        mode_model.splice(0, 0, [
            # Translators: Option when an existing install is found.
            _("Repair the existing installation"),
            # Translators: Option when an existing install is found.
            _("Reinstall, keep /data"),
            # Translators: Option when an existing install is found.
            _("Erase the disk and install"),
        ])
        self.existing_mode.set_model(mode_model)

        # models
        self.disk_list.bind_model(
            self.disk_list_model, self._create_device_row)

        if disks := disk_provider.get_disks():
            reset_model(self.disk_list_model, disks)
            self.set_visible_child_name('disks')
        else:
            self.set_visible_child_name('no-disks')

    def _is_big_enough(self, size):
        return size <= 0 or size >= self.minimum_disk_size

    def _create_device_row(self, device: DeviceInfo):
        if not self._is_big_enough(device.size_number):
            return DeviceTooSmallRow(device)
        if device.has_root_fs:
            return DeviceRootfsDiskRow(device)
        if device.has_mounted_fs:
            return DeviceMountedRow(device, self._handle_unmount)
        if not self.partition_ok or not device.partitions:
            return DeviceRow(device)

        expander_row = DeviceChoiceRow(device, self._row_activated)

        can_use_partitions = True
        is_booted_with_uefi = os.path.isdir("/sys/firmware/efi/efivars")
        if is_booted_with_uefi and not device.efi_partition:
            expander_row.add_row(NoEfiPartitionRow())
            can_use_partitions = False

        for partition in device.partitions:
            if self._is_big_enough(partition.size_number):
                row = DeviceRow(partition)
                row.connect('activated', self._row_activated)
                row.set_sensitive(can_use_partitions and not partition.is_efi)
                expander_row.add_row(row)
            else:
                expander_row.add_row(DeviceTooSmallRow(partition))
        return expander_row

    def _handle_unmount(self, row):
        if error := disk_provider.unmount_filesystems(row.device):
            _ = config_gettext
            # Translators: Error when unmount fails. {} is replaced with error details
            config.set('display-toast', _("Failed to unmount filesystems: {}").format(error))
            print(error)
        else:
            root = self.get_root()
            if root:
                root.activate_action('win.reload-page', None)

    ### callbacks ###

    @Gtk.Template.Callback('disk_selected')
    def _disk_selected(self, list_box, row):
        self._row_activated(row)

    def _row_activated(self, row):
        config.set('chosen_device', row.device)
        config.set('disk_is_partition', not type(row.device) == Disk)
        config.set('disk_efi_partition', row.device.efi_partition)

        # Like the Windows/macOS installers: if the target already holds an
        # install, say so and ask what to do instead of erasing it silently.
        existing = None
        if (isinstance(row.device, Disk) and
                not config.is_demo() and not config.is_test()):
            existing = find_existing(row.device.device_path)

        if existing:
            self._show_existing(existing)
        else:
            self._hide_existing()
            config.set_next_page(self)

    def _show_existing(self, existing):
        self.existing_label.set_label(
            # Translators: {} is replaced by the root device path.
            _("An existing installation was found on this disk ({}).").format(
                existing.get('shani_root') or existing.get('shani_boot') or ''))
        self.existing_mode.set_selected(0)   # Repair is the safe default
        self.existing_box.set_visible(True)
        self.existing_continue.set_visible(True)
        self.existing_continue.grab_focus()

    def _hide_existing(self):
        self.existing_box.set_visible(False)
        self.existing_continue.set_visible(False)
        config.set('repair', False)
        config.set('keep_data', False)

    @Gtk.Template.Callback('existing_continue')
    def _existing_continue(self, _):
        # 0: repair, 1: reinstall keeping /data, 2: erase and install
        mode = self.existing_mode.get_selected()
        config.set('repair', mode == 0)
        config.set('keep_data', mode == 1)
        config.set_next_page(self)
