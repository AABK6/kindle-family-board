#!/bin/sh
set -eu

ROOT_DIR="${1:-/mnt/us/kindle-family-board}"
ENV_FILE="${KFB_ENV_FILE:-$ROOT_DIR/board.env}"
LOG_FILE="$ROOT_DIR/cache/morning.log"

if [ -f "$ENV_FILE" ]; then
  set -a
  . "$ENV_FILE"
  set +a
fi

HOLD_SECONDS="${KFB_MORNING_HOLD_SECONDS:-10800}"

mkdir -p "$ROOT_DIR/cache" "$ROOT_DIR/linkss-state"

log() {
  printf '%s %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$1" >> "$LOG_FILE"
}

KFB_ENV_FILE="$ENV_FILE" "$ROOT_DIR/fetch_and_display.sh" >> "$LOG_FILE" 2>&1
log "fetch_and_display completed"

if [ ! -f "$ROOT_DIR/cache/latest.png" ]; then
  log "latest.png missing after morning update"
  exit 1
fi

"$ROOT_DIR/persist_morning_screensaver.sh" "$ROOT_DIR" "$ROOT_DIR/cache/latest.png" >> "$LOG_FILE" 2>&1 || log "morning screensaver persistence failed"

if [ "$HOLD_SECONDS" -gt 0 ] && [ -x "$ROOT_DIR/restore_after_delay.sh" ]; then
  TOKEN="$(date +%s)"
  printf '%s\n' "$TOKEN" > "$ROOT_DIR/linkss-state/restore.token"
  rm -f "$ROOT_DIR/cache/restore.pid"
  /sbin/start-stop-daemon -S -b -m -p "$ROOT_DIR/cache/restore.pid" -x /bin/sh -- \
    -c "KFB_RESTORE_TOKEN=$TOKEN $ROOT_DIR/restore_after_delay.sh $ROOT_DIR $HOLD_SECONDS >/dev/null 2>&1"
  log "armed restore_after_delay for $HOLD_SECONDS seconds"
fi

log "morning board finished"
