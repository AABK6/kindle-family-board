#!/bin/sh
set -eu

ROOT_DIR="${1:-/mnt/us/kindle-family-board}"
DELAY_SECONDS="${2:-}"
TOKEN="${KFB_RESTORE_TOKEN:-}"
TOKEN_FILE="$ROOT_DIR/linkss-state/restore.token"
PID_FILE="$ROOT_DIR/cache/restore.pid"
LOG_FILE="$ROOT_DIR/cache/restore.log"
FRAMEWORK_INIT="/etc/init.d/framework"
FRAMEWORK_RESET_SETTLE_SECONDS="${KFB_FRAMEWORK_RESET_SETTLE_SECONDS:-15}"

if [ -z "$DELAY_SECONDS" ]; then
  echo "usage: $0 <root-dir> <delay-seconds>" >&2
  exit 1
fi

mkdir -p "$ROOT_DIR/cache" "$ROOT_DIR/linkss-state"

log() {
  printf '%s %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$1" >> "$LOG_FILE"
}

cleanup() {
  current_pid="$(cat "$PID_FILE" 2>/dev/null || true)"
  if [ "$current_pid" = "$$" ]; then
    rm -f "$PID_FILE"
  fi
}

fail() {
  log "$1"
  exit 1
}

power_status() {
  lipc-get-prop com.lab126.powerd status 2>/dev/null || true
}

run_photo_screensaver_cycle() {
  PHOTO_IMAGE="$ROOT_DIR/cache/latest.png"
  if [ ! -f "$PHOTO_IMAGE" ]; then
    log "photo screensaver cycle skipped, image missing: $PHOTO_IMAGE"
    return 0
  fi

  if [ -x "$ROOT_DIR/one_shot_screensaver_refresh.sh" ]; then
    if /sbin/start-stop-daemon -S -b -x "$ROOT_DIR/one_shot_screensaver_refresh.sh" -- "$ROOT_DIR" "$PHOTO_IMAGE"; then
      log "armed one-shot screensaver refresh image=$PHOTO_IMAGE"
    else
      log "failed to arm one-shot screensaver refresh image=$PHOTO_IMAGE"
    fi
  fi

  lipc-set-prop com.lab126.powerd wakeUp 1 >/dev/null 2>&1 || true
  sleep 3
  powerd_test -p >/dev/null 2>&1 || true
  log "completed photo screensaver cycle"
}

reset_framework_if_available() {
  if [ ! -x "$FRAMEWORK_INIT" ]; then
    log "framework init script missing, skipping reset"
    return 0
  fi

  if "$FRAMEWORK_INIT" reset >/dev/null 2>&1; then
    log "framework reset completed"
    sleep "$FRAMEWORK_RESET_SETTLE_SECONDS"
    return 0
  fi

  log "framework reset failed"
  return 1
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

trap cleanup EXIT SIGTERM

printf '%s\n' "$$" > "$PID_FILE"

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

STATUS_BEFORE="$(power_status)"
if ! "$ROOT_DIR/restore_screensavers.sh" "$ROOT_DIR" >> "$LOG_FILE" 2>&1; then
  fail "restore_screensavers failed status_before=${STATUS_BEFORE:-unknown}"
fi
log "restore invoked status_before=${STATUS_BEFORE:-unknown}"
if ! reset_framework_if_available; then
  fail "framework reset failed after restore status_before=${STATUS_BEFORE:-unknown}"
fi
if echo "$STATUS_BEFORE" | grep -qi "screen saver"; then
  run_photo_screensaver_cycle
fi
log "restore-after-delay finished"
