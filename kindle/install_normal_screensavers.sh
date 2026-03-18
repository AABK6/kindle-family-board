#!/bin/sh
set -eu

ROOT_DIR="${1:-/mnt/us/kindle-family-board}"
SOURCE_DIR="${2:-$ROOT_DIR/normal-screensavers}"
LINKSS_DIR="${KFB_LINKSS_DIR:-/mnt/us/linkss}"
SCREENSAVER_DIR="$LINKSS_DIR/screensavers"
ACTIVE_DIR="${KFB_LINKSS_ACTIVE_DIR:-/opt/amazon/screen_saver/600x800}"
LOG_FILE="$ROOT_DIR/cache/linkss.log"

mkdir -p "$ROOT_DIR/cache"

log() {
  printf '%s %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$1" >> "$LOG_FILE"
}

sync_images() {
  SRC_DIR="$1"
  DEST_DIR="$2"

  if [ ! -d "$SRC_DIR" ] || [ ! -d "$DEST_DIR" ]; then
    return 0
  fi

  for existing in "$DEST_DIR"/*; do
    [ -f "$existing" ] || continue
    case "$existing" in
      *.png|*.PNG|*.jpg|*.JPG|*.jpeg|*.JPEG)
        rm -f "$existing" 2>/dev/null || true
        ;;
    esac
  done

  found_any=0
  for image in "$SRC_DIR"/*.png "$SRC_DIR"/*.PNG "$SRC_DIR"/*.jpg "$SRC_DIR"/*.JPG "$SRC_DIR"/*.jpeg "$SRC_DIR"/*.JPEG; do
    [ -f "$image" ] || continue
    found_any=1
    base="$(basename "$image")"
    cp "$image" "$DEST_DIR/$base"
    chmod 644 "$DEST_DIR/$base" 2>/dev/null || true
  done

  if [ "$found_any" -eq 0 ]; then
    log "no images found in $SRC_DIR"
    return 1
  fi

  return 0
}

if [ ! -d "$SOURCE_DIR" ]; then
  log "normal screensaver source missing: $SOURCE_DIR"
  exit 1
fi

mkdir -p "$SCREENSAVER_DIR"
sync_images "$SOURCE_DIR" "$SCREENSAVER_DIR"

if [ -d "$ACTIVE_DIR" ] && [ "$ACTIVE_DIR" != "$SCREENSAVER_DIR" ]; then
  sync_images "$SOURCE_DIR" "$ACTIVE_DIR" || log "active screensaver sync failed: $ACTIVE_DIR"
fi

sync
log "installed normal screensavers from $SOURCE_DIR"
