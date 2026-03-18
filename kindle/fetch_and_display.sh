#!/bin/sh
set -eu

SCRIPT_DIR=$(CDPATH= cd "$(dirname "$0")" && pwd)
ENV_FILE="${KFB_ENV_FILE:-$SCRIPT_DIR/board.env}"

if [ -z "${BOARD_URL:-}" ] && [ -f "$ENV_FILE" ]; then
  set -a
  . "$ENV_FILE"
  set +a
fi

BOARD_URL="${BOARD_URL:-}"
CACHE_DIR="${CACHE_DIR:-/mnt/us/kindle-family-board/cache}"
CURL_BIN="${CURL_BIN:-/mnt/us/usbnet/bin/curl}"
EIPS_BIN="${EIPS_BIN:-/usr/sbin/eips}"
TMP_IMAGE="$CACHE_DIR/latest.tmp.png"
FINAL_IMAGE="$CACHE_DIR/latest.png"
LOG_FILE="$CACHE_DIR/refresh.log"

mkdir -p "$CACHE_DIR"

log() {
  printf '%s %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$1" >> "$LOG_FILE"
}

if [ -z "$BOARD_URL" ]; then
  log "BOARD_URL is empty"
  exit 1
fi

if [ ! -x "$CURL_BIN" ]; then
  log "curl binary missing at $CURL_BIN"
  exit 1
fi

if [ ! -x "$EIPS_BIN" ]; then
  log "eips binary missing at $EIPS_BIN"
  exit 1
fi

if "$CURL_BIN" --fail --silent --show-error --location "$BOARD_URL" --output "$TMP_IMAGE"; then
  mv "$TMP_IMAGE" "$FINAL_IMAGE"
  log "downloaded $BOARD_URL"
else
  rm -f "$TMP_IMAGE"
  log "download failed, keeping cached image"
fi

if [ ! -f "$FINAL_IMAGE" ]; then
  log "no image available to display"
  exit 1
fi

"$EIPS_BIN" -f -g "$FINAL_IMAGE" >> "$LOG_FILE" 2>&1
log "displayed $FINAL_IMAGE"
