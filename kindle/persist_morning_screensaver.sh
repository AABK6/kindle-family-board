#!/bin/sh
set -eu

ROOT_DIR="${1:-/mnt/us/kindle-family-board}"
IMAGE_PATH="${2:-$ROOT_DIR/cache/latest.png}"
LINKSS_DIR="${KFB_LINKSS_DIR:-/mnt/us/linkss}"
STATE_DIR="$ROOT_DIR/linkss-state"
LOG_FILE="$ROOT_DIR/cache/linkss.log"

mkdir -p "$ROOT_DIR/cache"

log() {
  printf '%s %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$1" >> "$LOG_FILE"
}

if [ ! -d "$LINKSS_DIR" ]; then
  log "linkss is not installed, skipping morning screensaver persistence"
  exit 0
fi

if [ ! -f "$IMAGE_PATH" ]; then
  log "image missing: $IMAGE_PATH"
  exit 1
fi

rm -rf "$STATE_DIR"
mkdir -p "$STATE_DIR"
touch "$STATE_DIR/active"
log "armed morning board screensaver mode"

if lipc-get-prop com.lab126.powerd status 2>/dev/null | grep -qi "Screen Saver"; then
  /usr/sbin/eips -f -g "$IMAGE_PATH" >> "$LOG_FILE" 2>&1 || true
  log "refreshed visible board image"
fi
