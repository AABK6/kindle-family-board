#!/bin/sh
set -eu

SCRIPT_DIR=$(CDPATH= cd "$(dirname "$0")" && pwd)
EXTENSION_DIR=$(CDPATH= cd "$SCRIPT_DIR/.." && pwd)
EXTENSION_ENV="$EXTENSION_DIR/familyboard.env"
ROOT_DIR="${KFB_ROOT_DIR:-/mnt/us/kindle-family-board}"

if [ -f "$EXTENSION_ENV" ]; then
  set -a
  . "$EXTENSION_ENV"
  set +a
fi

ROOT_DIR="${KFB_ROOT_DIR:-$ROOT_DIR}"
BOARD_ENV="$ROOT_DIR/board.env"
FETCH_SCRIPT="$ROOT_DIR/fetch_and_display.sh"
LOG_FILE="$ROOT_DIR/cache/kual-familyboard.log"
KUAL_DELAY_SECONDS="${KFB_KUAL_DELAY_SECONDS:-4}"

mkdir -p "$ROOT_DIR/cache"

log() {
  printf '%s %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$1" >> "$LOG_FILE"
}

ACTION="${1:-fetch_today}"

case "$ACTION" in
  fetch_today)
    ;;
  *)
    log "unknown action=$ACTION"
    exit 1
    ;;
esac

if [ ! -f "$BOARD_ENV" ]; then
  log "missing board env at $BOARD_ENV"
  exit 1
fi

if [ ! -x "$FETCH_SCRIPT" ]; then
  log "missing fetch script at $FETCH_SCRIPT"
  exit 1
fi

log "manual fetch/display requested from KUAL"
log "manual fetch/display scheduled delay_seconds=$KUAL_DELAY_SECONDS"
(
  sleep "$KUAL_DELAY_SECONDS"
  log "manual fetch/display background starting"
  KFB_ENV_FILE="$BOARD_ENV" "$FETCH_SCRIPT" >> "$LOG_FILE" 2>&1
  log "manual fetch/display completed"
) >/dev/null 2>&1 &
