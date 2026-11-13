#!/bin/sh
# The one way in to the installer's tests. From anywhere, on the host:
#   sh dev/check.sh [--build] [suite...]          (no suite: all)
#
#   unit    pytest: config defaults and loader, the OSI_* contract, device model
#   ui      the whole installer in a headless X session, driven through AT-SPI
#           from Welcome to Restart Later, with a screenshot of every page
#   a11y    the same walk, failing on any on-screen control with no accessible
#           name (what a screen reader would announce as just "button")
#
# Everything a run writes is in out/ (git-ignored, yours to delete): each
# suite's log in out/logs/check-<suite>.log, screenshots in out/shots. The
# RESULT lines are counted into out/logs/check-summary.txt, and the exit
# status is non-zero if anything failed.
#
# The image is dev/Containerfile: archlinux plus the app's real dependencies
# (gtk4/libadwaita/vte), a headless X server, dbus and the AT-SPI bus, so the
# app under test is the one users get, not a mock.
REPO=$(cd "$(dirname "$0")/.." && pwd)
IMG=shani-os-installer-dev

# the containers write as root: hand what they wrote back to you
own() {
    docker run --rm -v "$REPO":/work "$IMG" sh -c \
        "mkdir -p /work/out/logs /work/out/shots && chown -R $(id -u):$(id -g) /work/out" \
        2>/dev/null || true
}

build() { docker build -t "$IMG" -f "$REPO/dev/Containerfile" "$REPO/dev" || exit 1; }

[ "${1:-}" = --build ] && { shift; build; }
docker image inspect "$IMG" >/dev/null 2>&1 || build
own
[ $# -eq 0 ] && set -- all
[ "$*" = all ] && set -- unit a11y

box() { docker run --rm -v "$REPO":/work "$@"; }

run() {
    case "$1" in
        unit) box "$IMG" sh -c 'cd /work && python3 -m pytest tests -q' ;;
        # one X server + session bus per suite (dev/session.sh); the walker is
        # dev/a11y.py, the app is the installed binary in a demo-mode session
        ui)   box -e SUITE=ui "$IMG" sh /work/dev/session.sh ;;
        a11y) box -e SUITE=a11y "$IMG" sh /work/dev/session.sh ;;
        *) echo "unknown suite: $1 (see the top of dev/check.sh)"; return 2 ;;
    esac
}

summary="$REPO/out/logs/check-summary.txt"
: > "$summary"
bad=0
for s in "$@"; do
    log="$REPO/out/logs/check-$s.log"
    echo "== $s"
    { run "$s"; echo $? > "$log.rc"; } 2>&1 | tee "$log"
    own
    rc=$(cat "$log.rc"); rm -f "$log.rc"
    pass=$(grep -c '^RESULT .* PASS' "$log")
    fail=$(grep -c '^RESULT .* FAIL' "$log")
    [ "$s" = unit ] && {
        pass=$(grep -oE '[0-9]+ passed' "$log" | grep -oE '[0-9]+' || echo 0)
        fail=$(grep -oE '[0-9]+ failed' "$log" | grep -oE '[0-9]+' || echo 0)
    }
    [ "$rc" = 0 ] && [ "${fail:-0}" = 0 ] && v=ok || { v=FAILED; bad=1; }
    printf "%-8s %-7s %4s pass %4s fail   out/logs/%s\n" \
        "$s" "$v" "${pass:-0}" "${fail:-0}" "${log##*/}" >> "$summary"
    grep '^RESULT .* FAIL' "$log" | sed 's/^/                 /' >> "$summary"
done
echo; cat "$summary"
exit $bad
