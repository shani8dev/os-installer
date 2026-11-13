# Developing Hints

## Development Setup
Consider developing with [`toolbx`](https://handbook.gnome.org/development/toolbx.html).
Install the dependencies (Arch; see README for the current list):
`meson blueprint-compiler appstream-glib gtk4 libadwaita gnome-desktop-4 libgweather-4 vte4 python-gobject python-yaml udisks2`
Then clone and install:

```
git clone --recursive https://github.com/shani8dev/os-installer.git
cd os-installer
meson setup build
sudo meson install -C build
```

To try the installer, without modifying any system settings, run it in test mode with `os-installer -t`.
Running in GNOME Builder uses the demo mode (`os-installer -d`) and shows test dummy disks.
Uninstall with `sudo ninja -C build uninstall `

## Structure
The app tries to follow the best practices of GNOME/libadwaita apps.
UI elements are described in Blueprint (.blp) files, which get used as templates by Python classes, that include the functionality.

The main UI consists of different pages (`src/ui/pages`) that are shown one after another.
Each page widget is put in a wrapper (`src/ui/page_wrapper.py`) which handles shared functionality like the page's headerbar.
For ad-hoc translating, some elements get translated on widget creation (`src/util/translations.py`).

Navigation of pages (`src/core/navigation.py`) is handled independent of the total progress tracking (`src/core/state_machine.py`).
For faster testing you can comment out pages in the state machine.
It also initializes running actual installation scripts (`src/core/installation_scripting`).

Distros can configure the installer via a YAML config file.
This gets read and can be accessed via a `Config` singleton (`src/core/config.py`).
Other parts of the app can also share state via this config and can react to changes by subscribing to specific entry variables.

Providers gather information about the system and process config values.
They are initialized in the background on startup (`src/core/preload_manager.py`). 

## Shortcuts
These shortcuts are not presented to the user in any way, but are always available:
* Show terminal with Ctrl+T
* Close app with Ctrl+W / Ctrl+Q
* Show about dialog with Alt+Enter
* Reload (supported) page with F5 / Ctrl+R

## Demo Mode
With `-d` the installer runs in demo mode, where it does not make any changes to the system.
This is used when running via as a flatpak, e.g. via Builder.
In this mode the installer does not show the actual available system disks, but placeholder data.

## Testing Mode
With `-t` the installer runs in testing mode (with `-t`).
Similar to demo mode this prevents the installer from making any changes to the system, but it still lists actually present disks.
It also slightly changes some behaviour:
* Disks are randomly pretended to not be available (12.5%)
* Additional shortcuts are available
    - Skip pages with Ctrl+S
    - Show failed page with Ctrl+F
