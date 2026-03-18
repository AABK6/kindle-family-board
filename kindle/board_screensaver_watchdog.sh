#!/bin/sh
set -eu

ROOT_DIR="${1:-/mnt/us/kindle-family-board}"
ENV_FILE="${KFB_ENV_FILE:-$ROOT_DIR/board.env}"
PID_FILE="$ROOT_DIR/cache/board-ss-watchdog.pid"
LOG_FILE="$ROOT_DIR/cache/board-ss-watchdog.log"
TOKEN_FILE="$ROOT_DIR/cache/board-ss-watchdog.token"
LOCK_DIR="/var/local/run"
LOCK_FILE="$LOCK_DIR/kfb-board-ss.lock"
TOKEN="${KFB_BOARD_WATCHDOG_TOKEN:-}"

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

if [ -z "$TOKEN" ] && [ -f "$TOKEN_FILE" ]; then
  TOKEN="$(cat "$TOKEN_FILE" 2>/dev/null || true)"
fi

token_matches() {
  if [ -z "$TOKEN" ] || [ ! -f "$TOKEN_FILE" ]; then
    return 1
  fi

  [ "$(cat "$TOKEN_FILE" 2>/dev/null)" = "$TOKEN" ]
}

cleanup() {
  if token_matches; then
    rm -f "$PID_FILE"
  fi
  exit 0
}

trap cleanup EXIT SIGTERM

echo "$$" > "$PID_FILE"

if ! token_matches; then
  log "watchdog token missing before start"
  exit 0
fi

while true; do
  lipc-wait-event -m -s 0 com.lab126.powerd goingToScreenSaver 2>/dev/null | while read line; do
    if echo "$line" | grep -q "goingToScreenSaver"; then
      if ! token_matches; then
        log "watchdog token cleared, exiting before redraw"
        exit 0
      fi
      if mkdir "$LOCK_FILE" 2>/dev/null; then
        sleep 2
        if ! token_matches; then
          rmdir "$LOCK_FILE" 2>/dev/null || true
          log "watchdog token cleared, skipping redraw"
          exit 0
        fi
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
