#!/bin/bash
# Dev stand-in for os-installer-config's configure.sh. Records the account and
# locale values the GUI collected, without writing to a real target system.
set -euo pipefail

log="${OSI_DEV_LOG:-/tmp/osi-dev.log}"
scratch="${OSI_DEV_SCRATCH:-/tmp/osi-dev-install}"

{
    echo "=== configure pid=$$"
    env | grep '^OSI_' | sort
} >> "$log"

mkdir -p "$scratch"
printf 'desktop=%s\nlocale=%s\ntimezone=%s\nuser=%s\nroot_password_set=%s\n' \
    "${OSI_DESKTOP:-}" "${OSI_LOCALE:-}" "${OSI_TIMEZONE:-}" \
    "${OSI_USER_USERNAME:-}" "$([ -n "${OSI_ROOT_PASSWORD:-}" ] && echo yes || echo no)" \
    > "$scratch/configured"
sleep 1
