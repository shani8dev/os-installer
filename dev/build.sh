#!/bin/sh
# Build and install the installer into the container's /usr, exactly as the
# package layout the ISO ships. Inside dev/'s container:
#   sh dev/build.sh
# The build directory is /tmp/osi-build (out/ is on the host and is shared with
# the run artifacts; keeping meson's files out of it avoids uid churn).
set -eu

SRC=${REPO:-/work}
BUILD=${BUILD:-/tmp/osi-build}

if [ ! -f "$BUILD/build.ninja" ]; then
    meson setup "$BUILD" "$SRC" --prefix=/usr --buildtype=debug
fi
ninja -C "$BUILD"
# Installs pkgdatadir, the GResource, the GSettings schema (compiled by
# misc-build-files/postinstall.py), the desktop file and the icons.
meson install -C "$BUILD" >/dev/null
