#!/bin/sh
set -eu

ROOT_DIR="${1:-/mnt/us/kindle-family-board}"
CRON_FILE="/etc/crontab/root"
CRON_LINE="0 7 * * * KFB_ENV_FILE=$ROOT_DIR/board.env $ROOT_DIR/fetch_and_display.sh >> $ROOT_DIR/cache/cron.log 2>&1"
BACKUP_FILE="$ROOT_DIR/root.crontab.backup"
TMP_FILE="/tmp/kindle-family-board.crontab"
LOG_FILE="$ROOT_DIR/cache/boot.log"

mkdir -p "$ROOT_DIR/cache"

log() {
  printf '%s %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$1" >> "$LOG_FILE"
}

if [ ! -f "$CRON_FILE" ]; then
  log "missing $CRON_FILE"
  exit 1
fi

if [ ! -f "$BACKUP_FILE" ]; then
  cp "$CRON_FILE" "$BACKUP_FILE"
fi

grep -v 'kindle-family-board/fetch_and_display.sh' "$CRON_FILE" > "$TMP_FILE" || true
printf '%s\n' "$CRON_LINE" >> "$TMP_FILE"

mntroot rw >/dev/null 2>&1 || true
cp "$TMP_FILE" "$CRON_FILE"
chmod 644 "$CRON_FILE"
mntroot ro >/dev/null 2>&1 || true
rm -f "$TMP_FILE"

/etc/init.d/cron restart >/dev/null 2>&1 || /etc/init.d/cron start >/dev/null 2>&1 || true
log "ensured cron entry in $CRON_FILE"

