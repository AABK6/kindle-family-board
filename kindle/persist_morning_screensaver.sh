#!/bin/sh
set -eu

ROOT_DIR="${1:-/mnt/us/kindle-family-board}"
IMAGE_PATH="${2:-$ROOT_DIR/cache/latest.png}"
LINKSS_DIR="${KFB_LINKSS_DIR:-/mnt/us/linkss}"
SCREENSAVER_DIR="$LINKSS_DIR/screensavers"
ACTIVE_DIR="${KFB_LINKSS_ACTIVE_DIR:-/opt/amazon/screen_saver/600x800}"
STATE_DIR="$ROOT_DIR/linkss-state"
MORNING_NAME="${KFB_LINKSS_SCREENSAVER_NAME:-bg_xsmall_ss00.png}"
MORNING_IMAGE="$SCREENSAVER_DIR/$MORNING_NAME"
LOG_FILE="$ROOT_DIR/cache/linkss.log"
CONFLICT_MARKERS="cover backdrop"
CONVERT_BIN="$LINKSS_DIR/bin/convert"

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

TARGET_DIR="$SCREENSAVER_DIR"
if [ -d "$ACTIVE_DIR" ]; then
  TARGET_DIR="$ACTIVE_DIR"
fi

mkdir -p "$SCREENSAVER_DIR"

IMAGE_COUNT=0
for original in "$STATE_DIR"/original_screensavers/*; do
  [ -f "$original" ] || continue
  base="$(basename "$original")"
  target="$TARGET_DIR/$base"
  case "$base" in
    *.jpg|*.jpeg|*.JPG|*.JPEG)
      if [ -x "$CONVERT_BIN" ]; then
        "$CONVERT_BIN" "$IMAGE_PATH" "$target" >/dev/null 2>&1 || cp "$IMAGE_PATH" "$target"
      else
        cp "$IMAGE_PATH" "$target"
      fi
      ;;
    *)
      cp "$IMAGE_PATH" "$target"
      ;;
  esac
  chmod 644 "$target" 2>/dev/null || true
  IMAGE_COUNT=$(( IMAGE_COUNT + 1 ))
done

if [ "$IMAGE_COUNT" -eq 0 ]; then
  fallback_target="$TARGET_DIR/$MORNING_NAME"
  cp "$IMAGE_PATH" "$fallback_target"
  chmod 644 "$fallback_target" 2>/dev/null || true
  log "no original screensavers found, installed fallback $fallback_target"
else
  log "overwrote $IMAGE_COUNT active screensaver files with board image in $TARGET_DIR"
fi

sync

if lipc-get-prop com.lab126.powerd status 2>/dev/null | grep -q "Screen Saver"; then
  /usr/sbin/eips -f -g "$IMAGE_PATH" >> "$LOG_FILE" 2>&1 || true
  log "refreshed visible screensaver"
fi
