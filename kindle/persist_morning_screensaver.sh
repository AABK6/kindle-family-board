#!/bin/sh
set -eu

ROOT_DIR="${1:-/mnt/us/kindle-family-board}"
IMAGE_PATH="${2:-$ROOT_DIR/cache/latest.png}"
LINKSS_DIR="${KFB_LINKSS_DIR:-/mnt/us/linkss}"
SCREENSAVER_DIR="$LINKSS_DIR/screensavers"
STATE_DIR="$ROOT_DIR/linkss-state"
MORNING_NAME="${KFB_LINKSS_SCREENSAVER_NAME:-bg_xsmall_ss00.png}"
MORNING_IMAGE="$SCREENSAVER_DIR/$MORNING_NAME"
LOG_FILE="$ROOT_DIR/cache/linkss.log"
CONFLICT_MARKERS="cover backdrop"

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

if [ ! -f "$STATE_DIR/active" ]; then
  rm -rf "$STATE_DIR"
  mkdir -p "$STATE_DIR"

  if [ -d "$SCREENSAVER_DIR" ]; then
    mv "$SCREENSAVER_DIR" "$STATE_DIR/original_screensavers"
  else
    mkdir -p "$STATE_DIR/original_screensavers"
  fi

  for marker in $CONFLICT_MARKERS; do
    if [ -e "$LINKSS_DIR/$marker" ]; then
      mv "$LINKSS_DIR/$marker" "$STATE_DIR/$marker"
    fi
  done

  touch "$STATE_DIR/active"
  log "captured existing linkss screensaver state"
fi

rm -rf "$SCREENSAVER_DIR"
mkdir -p "$SCREENSAVER_DIR"
cp "$IMAGE_PATH" "$MORNING_IMAGE"
chmod 644 "$MORNING_IMAGE" 2>/dev/null || true
log "installed morning screensaver $MORNING_IMAGE"

if lipc-get-prop com.lab126.powerd status 2>/dev/null | grep -q "Screen Saver"; then
  /usr/sbin/eips -f -g "$MORNING_IMAGE" >> "$LOG_FILE" 2>&1 || true
  log "refreshed visible screensaver"
fi
