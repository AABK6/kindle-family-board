#!/bin/sh
set -eu

ROOT_DIR="${1:-/mnt/us/kindle-family-board}"
IMAGE_PATH="${2:-$ROOT_DIR/cache/latest.png}"
LOG_FILE="$ROOT_DIR/cache/one-shot-screensaver.log"
LOCK_DIR="/var/local/run"
LOCK_FILE="$LOCK_DIR/kfb-one-shot-ss.lock"
EIPS_BIN="${EIPS_BIN:-/usr/sbin/eips}"

mkdir -p "$ROOT_DIR/cache" "$LOCK_DIR"

log() {
  printf '%s %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$1" >> "$LOG_FILE"
}

if [ ! -f "$IMAGE_PATH" ]; then
  log "image missing: $IMAGE_PATH"
  exit 1
fi

lipc-wait-event -m -s 20 com.lab126.powerd goingToScreenSaver 2>/dev/null | while read line; do
  if echo "$line" | grep -q "goingToScreenSaver"; then
    if mkdir "$LOCK_FILE" 2>/dev/null; then
      sleep 2
      "$EIPS_BIN" -f -g "$IMAGE_PATH" >> "$LOG_FILE" 2>&1 || true
      rmdir "$LOCK_FILE" 2>/dev/null || true
      log "refreshed one-shot screensaver image=$IMAGE_PATH"
      exit 0
    fi
  fi
done

log "one-shot screensaver refresh timed out"
