#!/bin/sh
set -eu

ROOT_DIR="${1:-/mnt/us/kindle-family-board}"
LINKSS_DIR="${KFB_LINKSS_DIR:-/mnt/us/linkss}"
SCREENSAVER_DIR="$LINKSS_DIR/screensavers"
ACTIVE_DIR="${KFB_LINKSS_ACTIVE_DIR:-/opt/amazon/screen_saver/600x800}"
STATE_DIR="$ROOT_DIR/linkss-state"
LOG_FILE="$ROOT_DIR/cache/linkss.log"
CONVERT_BIN="$LINKSS_DIR/bin/convert"
LINKSS_BIN="$LINKSS_DIR/bin/linkss"
UNLINKSS_BIN="$LINKSS_DIR/bin/unlinkss"
TMP_REFRESH_IMAGE="$ROOT_DIR/cache/restore-visible.png"
BOARD_IMAGE_CACHE="$ROOT_DIR/cache/latest.png"
NORMAL_SCREENSAVER_DIR="${KFB_NORMAL_SCREENSAVER_DIR:-$ROOT_DIR/normal-screensavers}"
RESTORE_FAILED=0

mkdir -p "$ROOT_DIR/cache"

log() {
  printf '%s %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$1" >> "$LOG_FILE"
}

normalize_png_file() {
  source_path="$1"
  tmp_path="$ROOT_DIR/cache/normalize-$(basename "$source_path").tmp"

  [ -x "$CONVERT_BIN" ] || return 0
  [ -f "$source_path" ] || return 0

  rm -f "$tmp_path"
  if "$CONVERT_BIN" "$source_path" -colorspace sRGB "PNG8:$tmp_path" >/dev/null 2>&1; then
    if mv -f "$tmp_path" "$source_path" >/dev/null 2>&1; then
      chmod 644 "$source_path" 2>/dev/null || true
      log "normalized png for framework loader path=$source_path"
      return 0
    fi
  fi

  rm -f "$tmp_path"
  log "png normalization failed path=$source_path"
  return 1
}

normalize_png_dir() {
  dir_path="$1"
  [ -d "$dir_path" ] || return 0

  for png_path in "$dir_path"/*.png "$dir_path"/*.PNG; do
    [ -f "$png_path" ] || continue
    normalize_png_file "$png_path" || true
  done
}

first_existing() {
  for candidate in "$@"; do
    if [ -f "$candidate" ]; then
      printf '%s\n' "$candidate"
      return 0
    fi
  done

  return 1
}

prepare_refresh_image() {
  candidate="$(first_existing "$NORMAL_SCREENSAVER_DIR"/*.png "$NORMAL_SCREENSAVER_DIR"/*.PNG "$TARGET_DIR"/*.png "$TARGET_DIR"/*.PNG || true)"
  if [ -n "$candidate" ]; then
    printf '%s\n' "$candidate"
    return 0
  fi

  candidate="$(first_existing "$NORMAL_SCREENSAVER_DIR"/*.jpg "$NORMAL_SCREENSAVER_DIR"/*.JPG "$NORMAL_SCREENSAVER_DIR"/*.jpeg "$NORMAL_SCREENSAVER_DIR"/*.JPEG "$TARGET_DIR"/*.jpg "$TARGET_DIR"/*.JPG "$TARGET_DIR"/*.jpeg "$TARGET_DIR"/*.JPEG || true)"
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

if [ -x "$ROOT_DIR/install_normal_screensavers.sh" ] && [ -d "$NORMAL_SCREENSAVER_DIR" ]; then
  "$ROOT_DIR/install_normal_screensavers.sh" "$ROOT_DIR" "$NORMAL_SCREENSAVER_DIR" >> "$LOG_FILE" 2>&1 || log "normal screensaver install failed"
fi

TARGET_DIR="$SCREENSAVER_DIR"
if [ -d "$ACTIVE_DIR" ]; then
  TARGET_DIR="$ACTIVE_DIR"
fi

mkdir -p "$SCREENSAVER_DIR"
if [ -d "$STATE_DIR/original_screensavers" ]; then
  for original in "$STATE_DIR"/original_screensavers/*; do
    [ -f "$original" ] || continue
    base="$(basename "$original")"
    if [ ! -f "$SCREENSAVER_DIR/$base" ]; then
      cp "$original" "$SCREENSAVER_DIR/$base" 2>/dev/null || true
      chmod 644 "$SCREENSAVER_DIR/$base" 2>/dev/null || true
    fi
    if [ "$TARGET_DIR" != "$SCREENSAVER_DIR" ] && [ ! -f "$TARGET_DIR/$base" ]; then
      cp "$original" "$TARGET_DIR/$base" 2>/dev/null || true
      chmod 644 "$TARGET_DIR/$base" 2>/dev/null || true
    fi
  done
fi

normalize_png_dir "$NORMAL_SCREENSAVER_DIR"
normalize_png_dir "$SCREENSAVER_DIR"
if [ "$TARGET_DIR" != "$SCREENSAVER_DIR" ]; then
  normalize_png_dir "$TARGET_DIR"
fi

log "restored normal screensaver mode"
if [ -x "$LINKSS_BIN" ]; then
  if [ -x "$UNLINKSS_BIN" ]; then
    if "$UNLINKSS_BIN" >> "$LOG_FILE" 2>&1; then
      log "tore down regular linkss state"
    else
      log "regular linkss teardown failed"
    fi
  fi

  if "$LINKSS_BIN" >> "$LOG_FILE" 2>&1; then
    log "reinitialized regular linkss state"
  else
    log "regular linkss reinitialization failed"
    RESTORE_FAILED=1
  fi
else
  log "regular linkss binary missing, skipping reinitialization"
  RESTORE_FAILED=1
fi

POWERD_STATUS="$(lipc-get-prop com.lab126.powerd status 2>/dev/null || true)"
RESTORE_IMAGE="$(prepare_refresh_image || true)"
if [ -n "$RESTORE_IMAGE" ]; then
  cp "$RESTORE_IMAGE" "$BOARD_IMAGE_CACHE" >/dev/null 2>&1 || true
  /usr/sbin/eips -f -g "$RESTORE_IMAGE" >> "$LOG_FILE" 2>&1 || true
  log "refreshed visible restored screensaver status=${POWERD_STATUS:-unknown} image=$RESTORE_IMAGE cache=$BOARD_IMAGE_CACHE"
else
  log "no displayable restored screensaver found for visible refresh status=${POWERD_STATUS:-unknown}"
fi

if [ "$RESTORE_FAILED" -ne 0 ]; then
  log "restore_screensavers encountered critical failures; preserving state for retry"
  sync
  exit 1
fi

rm -rf "$STATE_DIR"
sync
