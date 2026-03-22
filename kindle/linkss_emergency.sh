#!/bin/sh
set -eu

ROOT_DIR="/mnt/us/kindle-family-board"
LOG_FILE="$ROOT_DIR/cache/linkss-emergency.log"
ENV_FILE="${KFB_ENV_FILE:-$ROOT_DIR/board.env}"

if [ -f "$ENV_FILE" ]; then
  set -a
  . "$ENV_FILE"
  set +a
fi

RUNTIME_TZ="${KFB_RUNTIME_TZ:-CET-1CEST,M3.5.0,M10.5.0/3}"
export TZ="$RUNTIME_TZ"

mkdir -p "$ROOT_DIR/cache"

log() {
  printf '%s %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$1" >> "$LOG_FILE"
}

log "starting linkss emergency hook"

if [ -x "$ROOT_DIR/boot_reseed.sh" ]; then
  "$ROOT_DIR/boot_reseed.sh" "$ROOT_DIR" >> "$LOG_FILE" 2>&1 || log "boot reseed failed"
else
  log "boot_reseed.sh missing"
fi

if [ -x /mnt/us/linkss/bin/linkss ]; then
  log "starting regular linkss"
  exec /mnt/us/linkss/bin/linkss
fi

log "linkss binary missing"
exit 0
