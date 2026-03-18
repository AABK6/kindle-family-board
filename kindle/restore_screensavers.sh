#!/bin/sh
set -eu

ROOT_DIR="${1:-/mnt/us/kindle-family-board}"
LINKSS_DIR="${KFB_LINKSS_DIR:-/mnt/us/linkss}"
SCREENSAVER_DIR="$LINKSS_DIR/screensavers"
ACTIVE_DIR="${KFB_LINKSS_ACTIVE_DIR:-/opt/amazon/screen_saver/600x800}"
STATE_DIR="$ROOT_DIR/linkss-state"
LOG_FILE="$ROOT_DIR/cache/linkss.log"
CONFLICT_MARKERS="cover backdrop"
CONVERT_BIN="$LINKSS_DIR/bin/convert"
TMP_REFRESH_IMAGE="$ROOT_DIR/cache/restore-visible.png"

mkdir -p "$ROOT_DIR/cache"

log() {
  printf '%s %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$1" >> "$LOG_FILE"
}

prepare_refresh_image() {
  candidate="$(find "$TARGET_DIR" -maxdepth 1 -type f -iname '*.png' | sort | sed -n '1p')"
  if [ -n "$candidate" ]; then
    printf '%s\n' "$candidate"
    return 0
  fi

  candidate="$(find "$TARGET_DIR" -maxdepth 1 -type f \( -iname '*.jpg' -o -iname '*.jpeg' \) | sort | sed -n '1p')"
  if [ -n "$candidate" ] && [ -x "$CONVERT_BIN" ]; then
    rm -f "$TMP_REFRESH_IMAGE"
    if "$CONVERT_BIN" "$candidate" "$TMP_REFRESH_IMAGE" >/dev/null 2>&1; then
      printf '%s\n' "$TMP_REFRESH_IMAGE"
      return 0
    fi
  fi

  return 1
}

"$ROOT_DIR/stop_board_watchdog.sh" "$ROOT_DIR" >/dev/null 2>&1 || true

if [ ! -f "$STATE_DIR/active" ]; then
  log "no active morning screensaver state to restore"
  exit 0
fi

TARGET_DIR="$SCREENSAVER_DIR"
if [ -d "$ACTIVE_DIR" ]; then
  TARGET_DIR="$ACTIVE_DIR"
fi

rm -rf "$SCREENSAVER_DIR"
mkdir -p "$SCREENSAVER_DIR"
if [ -d "$STATE_DIR/original_screensavers" ]; then
  for original in "$STATE_DIR"/original_screensavers/*; do
    [ -f "$original" ] || continue
    base="$(basename "$original")"
    cp "$original" "$SCREENSAVER_DIR/$base"
    chmod 644 "$SCREENSAVER_DIR/$base" 2>/dev/null || true
    if [ "$TARGET_DIR" != "$SCREENSAVER_DIR" ]; then
      cp "$original" "$TARGET_DIR/$base"
      chmod 644 "$TARGET_DIR/$base" 2>/dev/null || true
    fi
  done
fi

for marker in $CONFLICT_MARKERS; do
  rm -f "$LINKSS_DIR/$marker"
  if [ -e "$STATE_DIR/$marker" ]; then
    mv "$STATE_DIR/$marker" "$LINKSS_DIR/$marker"
  fi
done

rm -rf "$STATE_DIR"
sync
log "restored original linkss screensaver state"
POWERD_STATUS="$(lipc-get-prop com.lab126.powerd status 2>/dev/null || true)"
RESTORE_IMAGE="$(prepare_refresh_image || true)"
if [ -n "$RESTORE_IMAGE" ]; then
  /usr/sbin/eips -f -g "$RESTORE_IMAGE" >> "$LOG_FILE" 2>&1 || true
  log "refreshed visible restored screensaver status=${POWERD_STATUS:-unknown} image=$RESTORE_IMAGE"
else
  log "no displayable restored screensaver found for visible refresh status=${POWERD_STATUS:-unknown}"
fi
