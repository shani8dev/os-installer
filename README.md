# ShaniOS Installer

The installer ShaniOS live images ship, forked from GNOME's
[os-installer](https://gitlab.gnome.org/p3732/os-installer) (GPL-3.0-or-later).

Upstream's last code change was in December 2025; everything after that is
Weblate translation drops. We carry a small, reviewable set of our own fixes
on top instead of maintaining a `patch -p1` stack in the PKGBUILD, and we keep
upstream fixes cherry-pickable.

The app keeps its upstream shape: GTK4/libadwaita, Python, Blueprint UI, pages
driven by `state_machine.py`, distro behaviour supplied by `/etc/os-installer`
(see [os-installer-config](https://github.com/shani8dev/os-installer-config)).

## What is different from upstream

* **App identity** — `org.shani.OsInstaller` (was `com.github.p3732.os_installer`),
  renamed desktop entry, metainfo, GSettings schema, GResource prefix and
  icons. The binary is still `os-installer` and the gettext domain is still
  `os-installer`, so upstream `.po` files keep working.
* **Install scripts run through bash** — upstream `exec`s `./<script>`, which
  needs the executable bit and a shebang. ShaniOS ships its scripts from
  `/etc/os-installer` and always runs them with `/bin/bash`.
* **Optional root password** — an extra field on the encryption page, exported
  as `OSI_ROOT_PASSWORD`, governed by `user.min_password_length` like the user
  password.
* **Encryption and root-password rows on the summary page** — the `encrypt`
  page has no `SummaryRow` of its own, so editions that skip the
  language/desktop/user/region pages could reach the summary with nothing but
  the keyboard layout listed.
* **Bug fixes** — generated usernames are actually used
  (`user.request_username` was tested instead of `user_username`); the
  fixed-language lookup no longer races config loading; the
  `keyboard_language` fallback is a real 2-tuple; the EFI partition is stored
  as its device path, not its name.

`NEWS` has the per-release detail.

## Building

Dependencies (Arch):

```
sudo pacman -S meson blueprint-compiler appstream-glib \
  gtk4 libadwaita gnome-desktop-4 libgweather-4 vte4 python-gobject python-yaml udisks2
```

Build and install:

```
meson setup build --prefix=/usr
ninja -C build
sudo meson install -C build
```

Try it without touching the system:

```
os-installer -d   # demo mode: dummy disks, no system calls
os-installer -t   # test mode: real disks and real scripts, no system calls
```

Neither mode stops the configured scripts (prepare/install/configure run as
configured), so point `-c` at a config whose scripts are safe — see
[docs/Hacking.md](docs/Hacking.md#testing-mode).

Test it without a desktop — unit tests and a full headless walk of every
page, driven through the accessibility tree (needs Docker):

```
sh dev/check.sh unit
sh dev/check.sh a11y
```

See [docs/Hacking.md](docs/Hacking.md#testing) for what the walk covers and
how to drive the live installer inside shani-testbed.

On ShaniOS, `os-installer-git` in
[shani-pkgbuilds](https://github.com/shani8dev/shani-pkgbuilds) builds this
repo; `os-installer` tracks the newest release tag.

## Configuration

The distro side lives outside this repo. `os-installer` reads
`/etc/os-installer/config.yaml` (or `--config <path>`) and runs the
`prepare`/`install`/`configure` scripts it names. ShaniOS's configuration,
partition layout, subvolume layout and first-boot handover are documented in
[os-installer-config](https://github.com/shani8dev/os-installer-config).

A config can also set `install_policy` (labels, subvolume list, image
directory, swapfile, boot entries) and `secure_boot` / `tpm` (`auto`/`yes`/
`no`): the installer validates them and exports them to the scripts as
`OSI_*`, so the distro no longer has to hardcode them — see
[docs/Hacking.md](docs/Hacking.md#install-policy).

## Translations

The gettext domain and the `po/` tree are upstream's, and translations are
still synced from
[upstream Weblate](https://hosted.weblate.org/projects/os-installer/). Our new
strings live in the same `.po` files; run `ninja -C build os-installer-update-po`
after changing translatable UI text.

## Upstream

Forked at commit `ba5b74d` (2026-09-30, `main`). To pull an upstream fix:

```
git remote add upstream https://gitlab.gnome.org/p3732/os-installer.git
git fetch upstream
git cherry-pick <commit>
```

Keep app-ID and resource-path churn out of cherry-picked commits so upstream
commits apply with minimal conflict.

## License

GPL-3.0-or-later, same as upstream. See `LICENSE`; authorship of the original
work is Peter Eisenmann and os-installer contributors.
