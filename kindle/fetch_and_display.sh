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
FETCH_RETRY_COUNT="${KFB_FETCH_RETRY_COUNT:-6}"
FETCH_RETRY_DELAY="${KFB_FETCH_RETRY_DELAY:-10}"
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

REQUEST_URL="$BOARD_URL"
case "$REQUEST_URL" in
  *\?*)
    REQUEST_URL="${REQUEST_URL}&_ts=$(date +%Y%m%d%H%M%S)"
    ;;
  *)
    REQUEST_URL="${REQUEST_URL}?_ts=$(date +%Y%m%d%H%M%S)"
    ;;
esac

download_ok=0
attempt=1
while [ "$attempt" -le "$FETCH_RETRY_COUNT" ]; do
  if "$CURL_BIN" --fail --silent --show-error --location "$REQUEST_URL" --output "$TMP_IMAGE" 2>>"$LOG_FILE"; then
    mv "$TMP_IMAGE" "$FINAL_IMAGE"
    log "downloaded $REQUEST_URL on attempt $attempt/$FETCH_RETRY_COUNT"
    download_ok=1
    break
  fi

  rm -f "$TMP_IMAGE"
  log "download attempt $attempt/$FETCH_RETRY_COUNT failed"
  if [ "$attempt" -lt "$FETCH_RETRY_COUNT" ]; then
    sleep "$FETCH_RETRY_DELAY"
  fi
  attempt=$(( attempt + 1 ))
done

if [ "$download_ok" -ne 1 ]; then
  log "download failed after $FETCH_RETRY_COUNT attempts, keeping cached image"
fi

if [ ! -f "$FINAL_IMAGE" ]; then
  log "no image available to display"
  exit 1
fi

"$EIPS_BIN" -f -g "$FINAL_IMAGE" >> "$LOG_FILE" 2>&1
log "displayed $FINAL_IMAGE"
