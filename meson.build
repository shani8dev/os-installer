project('os-installer',
          version: '0.6.0',
    meson_version: '>= 0.56.0',
  default_options: [ 'warning_level=2',
                   ],
  license: 'GPL-3.0-or-later',
)

python = import('python')
python.find_installation(
  'python3',
  modules: ['yaml'],
  required: true
)
dependency('blueprint-compiler', version: '>= 0.16')
dependency('gio-2.0', version: '>= 2.60.0')
dependency('glib-2.0', version: '>= 2.60.0')
dependency('gnome-desktop-4', version: '>= 43')
dependency('gtk4', version: '>= 4.10.0')
dependency('gweather4', version: '>= 4.4.0')
dependency('libadwaita-1', version: '>= 1.6.0')
dependency('vte-2.91-gtk4', version: '>= 0.75.0')

i18n = import('i18n')

application_id = 'org.shani.OsInstaller'

subdir('misc-build-files')
subdir('data')
subdir('po')
subdir('src')

meson.add_install_script('misc-build-files/postinstall.py')
