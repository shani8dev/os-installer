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

## Testing

Everything below runs in a container; you need Docker and nothing else:

```
sh dev/check.sh              # unit + the full GUI walk
sh dev/check.sh unit         # pytest only (fast)
sh dev/check.sh a11y         # the walk, plus an accessible-name check per page
sh dev/check.sh --build      # rebuild the image first (after dependency changes)
```

`dev/check.sh` is the only entry point. Its image (`dev/Containerfile`) is
Arch Linux with the installer's real dependencies (gtk4, libadwaita, vte4,
gnome-desktop), a headless X server (`Xvfb`), a private session bus and the
AT-SPI broker. The app is built with meson and installed to `/usr`, i.e. the
layout the package ships, and `dev/config/config.yaml` mirrors the live ISO's
`/etc/os-installer/config.yaml` (fixed English, no user/region pages, no
desktop list, encryption offered), with the three scripts from
`os-installer-config` replaced by stubs that only log the `OSI_*` environment.

`dev/a11y.py` drives the app through its accessibility tree — the native-app
equivalent of a DOM — so pages are found by title and controls by role and
name, not by coordinates. It walks Welcome → Keyboard → Disk → Encryption →
Confirmation → Summary → Installing → Done → Restart Later, screenshots each
page into `out/shots/`, and asserts what the scripts received (device path,
encryption on, PIN, locale, username). A failure prints the tree at that
point.

The suites:

| suite | what it proves |
|---|---|
| `unit` | config defaults are not mutated by loading, the YAML loader cannot execute code, validation falls back to demo mode, the `OSI_*` contract, the device model does not share mutable state |
| `ui` | the pages above actually appear and advance in the ISO's configuration |
| `a11y` | additionally, every on-screen control has an accessible name |

The live environment — the real `os-installer-config`, real udisks disks, a
real system bus — is shani-testbed's `app` command; see its README. Use it for
the parts this harness cannot honestly fake (real disk enumeration, the
distro's own scripts):

```
cd ../shani-install-media
./run_in_container.sh build.sh test app blue --local-pkg=<pkg.tar.zst> \
    --run="os-installer -d" --wait-window='ShaniOS Installer:120' \
    --a11y-lint --screenshot=@out/welcome.png \
    --click-element='button:^Continue$' --wait-element='label:^Keyboard Layout$'
```

## Install policy

The distro-specific install values used to be constants at the top of
`install.sh`/`configure.sh`, so the installer could not know, show or change
them. They are config now (`install_policy`), and the installer exports them
to every step as `OSI_*`:

| config key | environment |
|---|---|
| `os_name` | `OSI_OS_NAME` |
| `root_label` / `boot_label` | `OSI_ROOT_LABEL` / `OSI_BOOT_LABEL` |
| `partition_layout` | `OSI_PARTITION_LAYOUT` (absolute; relative to the config file) |
| `btrfs_subvolumes` | `OSI_BTRFS_SUBVOLUMES` (space separated) |
| `btrfs_top_options` | `OSI_BTRFS_TOP_OPTS` |
| `swapfile_path` | `OSI_SWAPFILE_PATH` |
| `image_dir`, `rootfs_image`, `flatpak_image`, `snap_image`, `ai_models_image` | `OSI_IMAGE_DIR`, `OSI_ROOTFS_IMAGE`, `OSI_FLATPAK_IMAGE`, `OSI_SNAP_IMAGE`, `OSI_AI_MODELS_IMAGE` |
| `kernel_cmdline_current` / `_candidate`, `uki_boot_entries` | `OSI_KERNEL_CMDLINE_CURRENT`, `OSI_KERNEL_CMDLINE_CANDIDATE`, `OSI_UKI_BOOT_ENTRIES` |
| `skip_user` / `skip_region` | `OSI_SKIP_USER` / `OSI_SKIP_REGION` |
| `user.min_password_length` | `OSI_MIN_PASSWORD_LENGTH` |
| `admin_groups` | — (the installer checks it before the first script) |

Defaults are the ShaniOS layout, so a config that does not mention
`install_policy` gets the values the scripts used to hardcode. A script reads
`${OSI_ROOT_LABEL:-shani_root}` and still works with an older installer.

`admin_groups` (default `wheel`, `sudo`) is the one decision the installer
makes itself: root may always install, and a user in one of the groups may.
Without it the first script used to exit 1 and print the reason into a
terminal the user had to open. An empty list disables the check.

## Hostname, groups, log, power

* `hostname` — `null` asks on a page, a string fixes it and hides the page.
  ShaniOS keeps the distro name and leaves the account, region and hostname
  to the first-run setup (gnome-initial-setup, plasma-setup, shani-shell's
  niri setup). Exported as `OSI_HOSTNAME`.
* `user.groups` — extra groups for the account (default `wheel`), exported as
  `OSI_USER_GROUPS` and added on top of the image's canonical list.
* Every install writes one log: the app's output and each script's output are
  teed into `/tmp/os-installer-<uid>.log` (the terminal still shows them), so
  a failed install can be reported.
* `power_warning` — a banner on the welcome page when the machine is on
  battery.
* The disk page states the configured minimum size; the user page and the
  root password show a strength hint (a small heuristic for now — see
  `src/util/password_strength.py`).

## Recovery key, TPM PIN, erase, time, network

* `disk_encryption.recovery_key` (default on): the installer generates a
  base32 key, configure.sh adds it as a LUKS keyslot with the PIN as the
  existing passphrase, and the done page shows it once (copy button, stored
  nowhere but `/run`, which a reboot clears). A failed add is a warning, not
  a failed install.
* The TPM page can require a PIN (`--tpm2-with-pin=yes`, `NEWPIN`), a second
  factor on top of the TPM.
* `disk_erase: quick|secure` — secure runs `blkdiscard` before partitioning.
* `time_sync` (default on) enables `systemd-timesyncd` in the target.
* `copy_network` (default on) copies the live session's NetworkManager
  connections to the installed system.

## Secure Boot and TPM

Two optional pages, both config-driven (`secure_boot.offered`, `tpm.offered`:
`auto`/`yes`/`no`; `auto` shows them only where the firmware/hardware can use
them — a bare `offered: yes` works too, YAML 1.1 reads it as a bool and the
loader turns it back into `"yes"`):

* **Secure Boot** offers to stage MOK enrollment and takes the one-time
  MokManager password. Two modes: a separate password, or
  `mokutil --root-pw` — the root password from the installed system's
  `/etc/shadow`, which needs the root password to be set (the page says so and
  blocks Continue if it is not). Exported as `OSI_MOK_ENROLL`,
  `OSI_MOK_PASSWORD`, `OSI_MOK_ROOT_PW`.
* **TPM** offers to let the TPM unlock the encrypted disk. The installer
  enrolls it during installation, against the target's LUKS mapper, with the
  same literal PCR policy `gen-efi` uses on a booted system (0+7 with Secure
  Boot, 0 without); the PIN slot stays as a fallback. Exported as
  `OSI_USE_TPM`; `configure.sh` does the enrollment (a pcrlock policy is left
  to `gen-efi.sh enroll-tpm2` after first boot, since it needs the booted
  initramfs).

`configure.sh` stages MOK in the target chroot; `gen-efi.sh` is the tool for
the live system (and owns the PCR policy).

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
It changes how the installer itself behaves — no system calls (reboot, EFI
entries) are made — and it still lists the disks that are actually present,
so a real disk can be selected.

It does **not** stop the configured scripts: prepare/install/configure are
run for real, exactly as in a normal install. Test it with a config whose
scripts only log their environment (`dev/config/` is one) or with no scripts
at all, never with the distro's own install script unless you mean to run it.
It also slightly changes some behaviour:
* Disks are randomly pretended to not be available (12.5%)
* Additional shortcuts are available
    - Skip pages with Ctrl+S
    - Show failed page with Ctrl+F
