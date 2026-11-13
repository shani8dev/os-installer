pkgdatadir = join_paths(get_option('prefix'), get_option('datadir'), meson.project_name())
moduledir = join_paths(pkgdatadir, 'os_installer')

python = import('python')

conf = configuration_data()
conf.set('PYTHON', python.find_installation('python3').full_path())
conf.set('VERSION', meson.project_version())
conf.set('localedir', join_paths(get_option('prefix'), get_option('localedir')))
conf.set('pkgdatadir', pkgdatadir)
conf.set('available_translations', available_translations)

configure_file(
  input: 'os-installer.in',
  output: 'os-installer',
  configuration: conf,
  install: true,
  install_dir: get_option('bindir')
)

os_installer_sources = [
  '__init__.py',
  'main.py',
  'core/config.py',
  'core/installation_scripting.py',
  'core/navigation.py',
  'core/preload_manager.py',
  'core/state_machine.py',
  'core/system_calls.py',
  'core/translator.py',
  'provider/choices_provider.py',
  'provider/desktop_provider.py',
  'provider/disk_provider.py',
  'provider/format_provider.py',
  'provider/internet_provider.py',
  'provider/keyboard_layout_provider.py',
  'provider/language_provider.py',
  'provider/slideshow_provider.py',
  'provider/terminal_provider.py',
  'provider/timezone_provider.py',
  'provider/welcome_provider.py',
  'ui/buttons.py',
  'ui/confirm_quit_dialog.py',
  'ui/page_wrapper.py',
  'ui/pages/choices.py',
  'ui/pages/confirm.py',
  'ui/pages/desktop.py',
  'ui/pages/disk.py',
  'ui/pages/done.py',
  'ui/pages/encrypt.py',
  'ui/pages/failed.py',
  'ui/pages/hostname.py',
  'ui/pages/filter.py',
  'ui/pages/install.py',
  'ui/pages/internet.py',
  'ui/pages/keyboard.py',
  'ui/pages/language.py',
  'ui/pages/region.py',
  'ui/pages/restart.py',
  'ui/pages/secure_boot.py',
  'ui/pages/summary.py',
  'ui/pages/tpm.py',
  'ui/pages/user.py',
  'ui/pages/welcome.py',
  'ui/row/device_rows.py',
  'ui/row/progress_row.py',
  'ui/row/selection_row.py',
  'ui/row/summary_row.py',
  'ui/terminal_dialog.py',
  'ui/window.py',
  'util/device_info.py',
  'util/entry_error_enhancer.py',
  'util/envvar_creator.py',
  'util/filterable_object.py',
  'util/functions.py',
  'util/installation_step.py',
  'util/firmware.py',
  'util/logger.py',
  'util/password_strength.py',
  'util/power.py',
  'util/preloadable.py',
  'util/translations.py',
]

install_data(os_installer_sources, install_dir: moduledir)
