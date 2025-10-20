# SPDX-License-Identifier: GPL-3.0-or-later

from gi.repository import Adw, GObject, Gtk

from .config import config
from .device_info import DeviceInfo
from .translations import translate_widgets


@Gtk.Template(resource_path='/com/github/p3732/os-installer/ui/row/device_choice_row.ui')
class DeviceChoiceRow(Adw.ExpanderRow):
    __gtype_name__ = __qualname__

    whole_disk_row = Gtk.Template.Child()

    def __init__(self, device, callback, **kwargs):
        self._device = device
        self.callback = callback
        super().__init__(**kwargs)

        translate_widgets(self.whole_disk_row)

    @Gtk.Template.Callback('use_whole_disk')
    def _use_whole_disk(self, row):
        self.callback(self)

    @GObject.Property(type=DeviceInfo)
    def device(self):
        return self._device


@Gtk.Template(resource_path='/com/github/p3732/os-installer/ui/row/device_mounted_row.ui')
class DeviceMountedRow(Adw.ActionRow):
    __gtype_name__ = __qualname__

    mounted_label = Gtk.Template.Child()
    unmount_button = Gtk.Template.Child()

    def __init__(self, device, unmount_callback, **kwargs):
        self._device = device
        self.unmount_callback = unmount_callback
        super().__init__(**kwargs)

        translate_widgets(self.mounted_label)

    @Gtk.Template.Callback('unmount_clicked')
    def _unmount_clicked(self, button):
        self.unmount_callback(self)

    @GObject.Property(type=DeviceInfo)
    def device(self):
        return self._device


@Gtk.Template(resource_path='/com/github/p3732/os-installer/ui/row/device_rootfs_disk_row.ui')
class DeviceRootfsDiskRow(Adw.ActionRow):
    __gtype_name__ = __qualname__

    rootfs_label = Gtk.Template.Child()

    def __init__(self, device, **kwargs):
        self._device = device
        super().__init__(**kwargs)
        translate_widgets(self.rootfs_label)

    @GObject.Property(type=DeviceInfo)
    def device(self):
        return self._device


@Gtk.Template(resource_path='/com/github/p3732/os-installer/ui/row/device_row.ui')
class DeviceRow(Adw.ActionRow):
    __gtype_name__ = __qualname__

    def __init__(self, device, **kwargs):
        self._device = device
        super().__init__(**kwargs)

    @GObject.Property(type=DeviceInfo)
    def device(self):
        return self._device


@Gtk.Template(resource_path='/com/github/p3732/os-installer/ui/row/device_summary_row.ui')
class DeviceSummaryRow(Adw.ExpanderRow):
    __gtype_name__ = __qualname__

    def __init__(self, device, nested_activatable=False, **kwargs):
        self._device = device
        super().__init__(**kwargs)

        translate_widgets(self)

        # Hacky workaround to make AdwExpanderRow have property style
        # box -> list_box -> action row
        first_row = self.get_child().get_first_child().get_first_child()
        first_row.add_css_class('property')

        row = DeviceRow(device)
        row.set_activatable(nested_activatable)
        row.connect('activated', self._row_activated)
        self.add_row(row)

    def _row_activated(self, _):
        config.set('displayed-page', 'disk')

    @GObject.Property(type=DeviceInfo)
    def device(self):
        return self._device


@Gtk.Template(resource_path='/com/github/p3732/os-installer/ui/row/device_too_small_row.ui')
class DeviceTooSmallRow(Adw.ActionRow):
    __gtype_name__ = __qualname__

    too_small_label = Gtk.Template.Child()

    def __init__(self, device, **kwargs):
        self._device = device
        super().__init__(**kwargs)

        translate_widgets(self.too_small_label)

        smol = self.too_small_label.get_label()
        required_size_str = config.get('min_disk_size_str')
        self.too_small_label.set_label(smol.format(required_size_str))

    @GObject.Property(type=DeviceInfo)
    def device(self):
        return self._device


@Gtk.Template(resource_path='/com/github/p3732/os-installer/ui/row/no_efi_partition_row.ui')
class NoEfiPartitionRow(Adw.ActionRow):
    __gtype_name__ = __qualname__

    label_1 = Gtk.Template.Child()
    label_2 = Gtk.Template.Child()
    label_3 = Gtk.Template.Child()
    label_4 = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        translate_widgets(self.label_1, self.label_2, self.label_3, self.label_4)
