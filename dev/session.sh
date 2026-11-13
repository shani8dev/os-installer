#!/bin/sh
# One headless X session with a private session bus, the app installed the way
# a package installs it, and the AT-SPI accessibility bus. Runs inside dev/'s
# container (see dev/Containerfile), started by dev/check.sh:
#   SUITE=ui|a11y sh dev/session.sh
#
# Xvfb rather than a Wayland compositor: input injection (xdotool) and the
# AT-SPI tree both work without a window manager, and the window sits at 0,0,
# so window coordinates are screen coordinates.
set -u

REPO=${REPO:-/work}
OUT=${OUT:-$REPO/out}
mkdir -p "$OUT/logs" "$OUT/shots"

# Deterministic screen: bigger than the window (500x700 default), no WM.
export DISPLAY=:99
Xvfb :99 -screen 0 900x900x24 -nolisten tcp >"$OUT/logs/xvfb.log" 2>&1 &
xvfb=$!
trap 'kill $xvfb 2>/dev/null' EXIT
i=0
while [ ! -S /tmp/.X11-unix/X99 ]; do
    i=$((i + 1))
    [ $i -gt 100 ] && { echo "FAIL: Xvfb did not start"; cat "$OUT/logs/xvfb.log"; exit 1; }
    sleep 0.1
done

# GTK4 talks AT-SPI directly; NO_AT_BRIDGE is for GTK3 apps (kept so a stray
# one in the image would not silently vanish from the tree).
export GTK_A11Y=atspi NO_AT_BRIDGE=0
export GSETTINGS_BACKEND=memory
# A private runtime dir (Adw and the session bus both want one) and a fixed
# locale, so a run does not depend on the developer's LANG.
export XDG_RUNTIME_DIR=${XDG_RUNTIME_DIR:-/tmp/osi-runtime}
mkdir -p "$XDG_RUNTIME_DIR"; chmod 700 "$XDG_RUNTIME_DIR"
export LANG=${LANG:-C.UTF-8} LC_ALL=${LC_ALL:-C.UTF-8}

exec dbus-run-session -- sh "$REPO/dev/run-suite.sh"
