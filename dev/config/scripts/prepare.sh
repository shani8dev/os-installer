#!/bin/bash
# Dev stand-in for os-installer-config's prepare.sh. Logs the OSI_* contract
# and never touches the container's disks.
set -euo pipefail

log="${OSI_DEV_LOG:-/tmp/osi-dev.log}"
{
    echo "=== prepare pid=$$"
    env | grep '^OSI_' | sort
} >> "$log"
sleep 1
