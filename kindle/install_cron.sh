#!/bin/sh
set -eu

ROOT_DIR="${1:-/mnt/us/kindle-family-board}"
"$ROOT_DIR/boot_reseed.sh" "$ROOT_DIR"

echo "Installed cron entry in /etc/crontab/root"
