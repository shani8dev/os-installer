#!/bin/bash
# Dev stand-in for os-installer-config's install.sh: proves the real scripting
# path (bash, pty, OSI_* only) without partitioning anything. Writes to a
# scratch path under /tmp so a walk can reach the install and done pages.
set -euo pipefail

log="${OSI_DEV_LOG:-/tmp/osi-dev.log}"
scratch="${OSI_DEV_SCRATCH:-/tmp/osi-dev-install}"

{
    echo "=== install pid=$$"
    env | grep '^OSI_' | sort
} >> "$log"

mkdir -p "$scratch"
echo "pretending to install to ${OSI_DEVICE_PATH:-?}" > "$scratch/installed"
sleep 2
