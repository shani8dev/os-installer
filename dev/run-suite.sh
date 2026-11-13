#!/bin/sh
# Runs the app inside the session dev/session.sh set up (Xvfb + session bus)
# and hands it to the AT-SPI walker. Inside dev/'s container:
#   SUITE=ui|a11y sh dev/run-suite.sh
set -u

REPO=${REPO:-/work}
OUT=${OUT:-$REPO/out}
SUITE=${SUITE:-ui}
CONFIG=${CONFIG:-$REPO/dev/config/config.yaml}

# Same steps the ISO's os-installer-config provides, but as stubs: they log the
# OSI_* contract and never touch a disk, so the walk can go all the way through
# the install and done pages safely.
export OSI_DEV_LOG="$OUT/logs/scripts.log"
export OSI_DEV_SCRATCH="$OUT/scratch"
rm -f "$OSI_DEV_LOG"
rm -rf "$OSI_DEV_SCRATCH"
mkdir -p "$OSI_DEV_SCRATCH"

echo "== build"
sh "$REPO/dev/build.sh" || exit 1

echo "== launch os-installer --config=$CONFIG --demo-mode"
os-installer --config="$CONFIG" --demo-mode >"$OUT/logs/app.log" 2>&1 &
app=$!
cleanup() {
    kill "$app" 2>/dev/null
    wait "$app" 2>/dev/null
}
trap cleanup EXIT

# Wait for the toplevel. No window manager runs here, so nothing gives the
# window the X input focus; do it by hand for the key shortcuts.
wid=
i=0
while [ $i -lt 240 ]; do
    if ! kill -0 "$app" 2>/dev/null; then
        echo "RESULT app FAIL exited before showing a window"
        cat "$OUT/logs/app.log"
        exit 1
    fi
    wid=$(xdotool search --onlyvisible --pid "$app" 2>/dev/null | head -1)
    [ -n "$wid" ] && break
    i=$((i + 1))
    sleep 0.5
done
if [ -z "$wid" ]; then
    echo "RESULT app FAIL no window after 120s"
    cat "$OUT/logs/app.log"
    exit 1
fi
xdotool windowfocus "$wid"

case "$SUITE" in
    ui)   python3 "$REPO/dev/a11y.py" walk "$OUT" ;;
    a11y) python3 "$REPO/dev/a11y.py" walk "$OUT" --lint ;;
    *)    echo "unknown suite: $SUITE"; exit 2 ;;
esac
rc=$?

if [ $rc -ne 0 ]; then
    echo "---- app log ----"
    cat "$OUT/logs/app.log"
    echo "---- script log ----"
    cat "$OSI_DEV_LOG" 2>/dev/null
fi
exit $rc
