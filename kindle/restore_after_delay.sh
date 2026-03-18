#!/bin/sh
set -eu

ROOT_DIR="${1:-/mnt/us/kindle-family-board}"
DELAY_SECONDS="${2:-}"
TOKEN="${KFB_RESTORE_TOKEN:-}"
TOKEN_FILE="$ROOT_DIR/linkss-state/restore.token"
LOG_FILE="$ROOT_DIR/cache/restore.log"

if [ -z "$DELAY_SECONDS" ]; then
  echo "usage: $0 <root-dir> <delay-seconds>" >&2
  exit 1
fi

mkdir -p "$ROOT_DIR/cache" "$ROOT_DIR/linkss-state"

log() {
  printf '%s %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$1" >> "$LOG_FILE"
}

token_matches() {
  if [ -z "$TOKEN" ]; then
    return 0
  fi

  if [ ! -f "$TOKEN_FILE" ]; then
    return 1
  fi

  [ "$(cat "$TOKEN_FILE" 2>/dev/null)" = "$TOKEN" ]
}

now_epoch() {
  date +%s
}

set_rtc_wakeup() {
  lipc-set-prop -i com.lab126.powerd rtcWakeup "$1" >/dev/null 2>&1 || true
  log "set rtcWakeup=$1"
}

TARGET_EPOCH="$(( $(now_epoch) + DELAY_SECONDS ))"
log "armed restore delay_seconds=$DELAY_SECONDS target_epoch=$TARGET_EPOCH token=${TOKEN:-none}"

while :; do
  if ! token_matches; then
    log "restore token replaced, exiting"
    exit 0
  fi

  NOW="$(now_epoch)"
  REMAINING="$(( TARGET_EPOCH - NOW ))"
  if [ "$REMAINING" -le 0 ]; then
    break
  fi

  EVENT="$(lipc-wait-event -s "$REMAINING" com.lab126.powerd readyToSuspend,wakeupFromSuspend,resuming 2>/dev/null || true)"
  NOW="$(now_epoch)"
  REMAINING="$(( TARGET_EPOCH - NOW ))"
  log "event=${EVENT:-timeout} remaining=${REMAINING}"

  case "$EVENT" in
    readyToSuspend*)
      if [ "$REMAINING" -gt 0 ]; then
        set_rtc_wakeup "$REMAINING"
      fi
      ;;
    "")
      break
      ;;
    *)
      ;;
  esac
done

if ! token_matches; then
  log "restore token replaced before restore, exiting"
  exit 0
fi

"$ROOT_DIR/restore_screensavers.sh" "$ROOT_DIR" >> "$LOG_FILE" 2>&1 || true
log "restore-after-delay finished"
