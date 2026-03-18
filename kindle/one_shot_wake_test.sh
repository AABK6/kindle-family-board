#!/bin/sh
set -eu

ROOT_DIR="${1:-/mnt/us/kindle-family-board}"
TARGET_EPOCH="${2:-}"
LOG_FILE="$ROOT_DIR/cache/wake-test.log"
MODE="${KFB_WAKE_TEST_MODE:-fetch}"

if [ -z "$TARGET_EPOCH" ]; then
  echo "usage: $0 <root-dir> <target-epoch>" >&2
  exit 1
fi

mkdir -p "$ROOT_DIR/cache"

log() {
  printf '%s %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$1" >> "$LOG_FILE"
}

now_epoch() {
  date +%s
}

set_rtc_wakeup() {
  lipc-set-prop -i com.lab126.powerd rtcWakeup "$1" >/dev/null 2>&1 || true
  log "set rtcWakeup=$1"
}

log "armed target_epoch=$TARGET_EPOCH"

while :; do
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

log "triggering wake/display"
lipc-set-prop com.lab126.powerd wakeUp 1 >/dev/null 2>&1 || true
sleep 1

if [ "$MODE" != "display-only" ] && [ -x "$ROOT_DIR/fetch_and_display.sh" ]; then
  KFB_ENV_FILE="$ROOT_DIR/board.env" "$ROOT_DIR/fetch_and_display.sh" >> "$LOG_FILE" 2>&1 || true
fi

if [ -f "$ROOT_DIR/cache/latest.png" ]; then
  /usr/sbin/eips -f -g "$ROOT_DIR/cache/latest.png" >> "$LOG_FILE" 2>&1 || true
fi

log "wake test finished"
