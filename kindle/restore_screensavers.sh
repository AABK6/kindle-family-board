#!/bin/sh
set -eu

ROOT_DIR="${1:-/mnt/us/kindle-family-board}"
LINKSS_DIR="${KFB_LINKSS_DIR:-/mnt/us/linkss}"
SCREENSAVER_DIR="$LINKSS_DIR/screensavers"
STATE_DIR="$ROOT_DIR/linkss-state"
LOG_FILE="$ROOT_DIR/cache/linkss.log"
CONFLICT_MARKERS="cover backdrop"

mkdir -p "$ROOT_DIR/cache"

log() {
  printf '%s %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$1" >> "$LOG_FILE"
}

if [ ! -f "$STATE_DIR/active" ]; then
  log "no active morning screensaver state to restore"
  exit 0
fi

rm -rf "$SCREENSAVER_DIR"
if [ -d "$STATE_DIR/original_screensavers" ]; then
  mv "$STATE_DIR/original_screensavers" "$SCREENSAVER_DIR"
else
  mkdir -p "$SCREENSAVER_DIR"
fi

for marker in $CONFLICT_MARKERS; do
  rm -f "$LINKSS_DIR/$marker"
  if [ -e "$STATE_DIR/$marker" ]; then
    mv "$STATE_DIR/$marker" "$LINKSS_DIR/$marker"
  fi
done

rm -f "$STATE_DIR/active" "$STATE_DIR/restore.token"
rmdir "$STATE_DIR" 2>/dev/null || true
log "restored original linkss screensaver state"

if lipc-get-prop com.lab126.powerd status 2>/dev/null | grep -q "Screen Saver"; then
  RESTORE_IMAGE="$(find "$SCREENSAVER_DIR" -maxdepth 1 -type f \( -name '*.png' -o -name '*.jpg' -o -name '*.jpeg' \) | sort | sed -n '1p')"
  if [ -n "$RESTORE_IMAGE" ]; then
    /usr/sbin/eips -f -g "$RESTORE_IMAGE" >> "$LOG_FILE" 2>&1 || true
    log "refreshed visible restored screensaver"
  fi
fi
