#!/bin/sh
set -eu

ROOT_DIR="${1:-/mnt/us/kindle-family-board}"
ENV_FILE="${KFB_ENV_FILE:-$ROOT_DIR/board.env}"
PID_FILE="$ROOT_DIR/cache/board-ss-watchdog.pid"
LOG_FILE="$ROOT_DIR/cache/board-ss-watchdog.log"
LOCK_DIR="/var/local/run"
LOCK_FILE="$LOCK_DIR/kfb-board-ss.lock"

if [ -f "$ENV_FILE" ]; then
  set -a
  . "$ENV_FILE"
  set +a
fi

IMAGE_PATH="${KFB_BOARD_IMAGE_PATH:-$ROOT_DIR/cache/latest.png}"
EIPS_BIN="${EIPS_BIN:-/usr/sbin/eips}"

mkdir -p "$ROOT_DIR/cache" "$LOCK_DIR"

log() {
  printf '%s %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$1" >> "$LOG_FILE"
}

cleanup() {
  rm -f "$PID_FILE"
  exit 0
}

trap cleanup EXIT SIGTERM

echo "$$" > "$PID_FILE"

while true; do
  lipc-wait-event -m -s 0 com.lab126.powerd goingToScreenSaver 2>/dev/null | while read line; do
    if echo "$line" | grep -q "goingToScreenSaver"; then
      if mkdir "$LOCK_FILE" 2>/dev/null; then
        sleep 2
        if [ -f "$IMAGE_PATH" ]; then
          "$EIPS_BIN" -f -g "$IMAGE_PATH" >> "$LOG_FILE" 2>&1 || true
          log "reapplied board image on screensaver event"
        else
          log "board image missing: $IMAGE_PATH"
        fi
        rmdir "$LOCK_FILE" 2>/dev/null || true
      else
        log "screensaver redraw already in progress"
      fi
    fi
  done
  sleep 1
done
