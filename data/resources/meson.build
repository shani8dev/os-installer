subdir('ui')

blueprints = custom_target('blueprints',
  input: files(
    'ui/pages/choices.blp',
    'ui/pages/confirm.blp',
    'ui/pages/desktop.blp',
    'ui/pages/disk.blp',
    'ui/pages/done.blp',
    'ui/pages/encrypt.blp',
    'ui/pages/failed.blp',
    'ui/pages/filter.blp',
    'ui/pages/install.blp',
    'ui/pages/internet.blp',
    'ui/pages/keyboard_language.blp',
    'ui/pages/keyboard_layout.blp',
    'ui/pages/keyboard_overview.blp',
    'ui/pages/language.blp',
    'ui/pages/region.blp',
    'ui/pages/restart.blp',
    'ui/pages/summary.blp',
    'ui/pages/user.blp',
    'ui/pages/welcome.blp',
    'ui/row/device_choice_row.blp',
    'ui/row/device_mounted_row.blp',
    'ui/row/device_rootfs_disk_row.blp',
    'ui/row/device_row.blp',
    'ui/row/device_summary_row.blp',
    'ui/row/device_too_small_row.blp',
    'ui/row/multi_selection_row.blp',
    'ui/row/no_efi_partition_row.blp',
    'ui/row/progress_row.blp',
    'ui/row/selection_row.blp',
    'ui/row/summary_row.blp',
    'ui/terminal_dialog.blp',
    'ui/widgets/desktop_entry.blp',
    'ui/widgets/page_wrapper.blp',
    'ui/window.blp',
  ),
  output: '.',
  command: [find_program('blueprint-compiler'), 'batch-compile', '@OUTPUT@', '@CURRENT_SOURCE_DIR@', '@INPUT@'],
)
pkgdatadir = join_paths(get_option('prefix'), get_option('datadir'), meson.project_name())
gnome = import('gnome')

gnome.compile_resources(
  meson.project_name(),
  meson.project_name() + '.gresource.xml',
  gresource_bundle: true,
  dependencies: blueprints,
  install: true,
  install_dir: pkgdatadir
)
