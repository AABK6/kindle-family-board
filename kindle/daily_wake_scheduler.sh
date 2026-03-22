#!/bin/sh
set -eu
PATH="/usr/sbin:/usr/bin:/sbin:/bin:${PATH:-}"

ROOT_DIR="${1:-/mnt/us/kindle-family-board}"
ENV_FILE="${KFB_ENV_FILE:-$ROOT_DIR/board.env}"
LOG_FILE="$ROOT_DIR/cache/daily-wake.log"
CHILD_PID_FILE="$ROOT_DIR/cache/daily-wake-child.pid"
COOLDOWN_OVERRIDE="${KFB_WAKE_POST_RUN_COOLDOWN:-}"
TARGET_HOUR_OVERRIDE="${KFB_WAKE_TARGET_HOUR:-}"
TARGET_MINUTE_OVERRIDE="${KFB_WAKE_TARGET_MINUTE:-}"
RUNTIME_TZ_OVERRIDE="${KFB_RUNTIME_TZ:-}"

if [ -f "$ENV_FILE" ]; then
  set -a
  . "$ENV_FILE"
  set +a
fi

if [ -n "$COOLDOWN_OVERRIDE" ]; then
  KFB_WAKE_POST_RUN_COOLDOWN="$COOLDOWN_OVERRIDE"
fi
if [ -n "$TARGET_HOUR_OVERRIDE" ]; then
  KFB_WAKE_TARGET_HOUR="$TARGET_HOUR_OVERRIDE"
fi
if [ -n "$TARGET_MINUTE_OVERRIDE" ]; then
  KFB_WAKE_TARGET_MINUTE="$TARGET_MINUTE_OVERRIDE"
fi
if [ -n "$RUNTIME_TZ_OVERRIDE" ]; then
  KFB_RUNTIME_TZ="$RUNTIME_TZ_OVERRIDE"
fi

RAW_TARGET_HOUR="${KFB_WAKE_TARGET_HOUR:-7}"
RAW_TARGET_MINUTE="${KFB_WAKE_TARGET_MINUTE:-0}"
RAW_COOLDOWN_SECONDS="${KFB_WAKE_POST_RUN_COOLDOWN:-90}"
RUNTIME_TZ="${KFB_RUNTIME_TZ:-CET-1CEST,M3.5.0,M10.5.0/3}"

mkdir -p "$ROOT_DIR/cache"
export TZ="$RUNTIME_TZ"

log() {
  printf '%s %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$1" >> "$LOG_FILE"
}

stop_child() {
  if [ -f "$CHILD_PID_FILE" ]; then
    child_pid="$(cat "$CHILD_PID_FILE" 2>/dev/null || true)"
    if [ -n "$child_pid" ] && kill -0 "$child_pid" 2>/dev/null; then
      kill "$child_pid" 2>/dev/null || true
      sleep 1
      if kill -0 "$child_pid" 2>/dev/null; then
        kill -9 "$child_pid" 2>/dev/null || true
      fi
      log "stopped wake child pid=$child_pid"
    fi
    rm -f "$CHILD_PID_FILE"
  fi
}

cleanup() {
  stop_child
  exit 0
}

trap cleanup EXIT INT TERM

normalize_int() {
  value="$(printf '%s' "$1" | sed 's/^0*//')"
  if [ -z "$value" ]; then
    value=0
  fi
  printf '%s\n' "$value"
}

validate_target() {
  case "$TARGET_HOUR" in
    ''|*[!0-9]*)
      log "invalid target hour: $TARGET_HOUR"
      exit 1
      ;;
  esac
  case "$TARGET_MINUTE" in
    ''|*[!0-9]*)
      log "invalid target minute: $TARGET_MINUTE"
      exit 1
      ;;
  esac
  if [ "$TARGET_HOUR" -lt 0 ] || [ "$TARGET_HOUR" -gt 23 ]; then
    log "target hour out of range: $TARGET_HOUR"
    exit 1
  fi
  if [ "$TARGET_MINUTE" -lt 0 ] || [ "$TARGET_MINUTE" -gt 59 ]; then
    log "target minute out of range: $TARGET_MINUTE"
    exit 1
  fi
}

seconds_until_target() {
  hour_now="$(normalize_int "$(date +%H)")"
  minute_now="$(normalize_int "$(date +%M)")"
  second_now="$(normalize_int "$(date +%S)")"
  now_seconds=$(( hour_now * 3600 + minute_now * 60 + second_now ))
  target_seconds=$(( TARGET_HOUR * 3600 + TARGET_MINUTE * 60 ))

  if [ "$now_seconds" -lt "$target_seconds" ]; then
    printf '%s\n' $(( target_seconds - now_seconds ))
  else
    printf '%s\n' $(( 86400 - now_seconds + target_seconds ))
  fi
}

TARGET_HOUR="$(normalize_int "$RAW_TARGET_HOUR")"
TARGET_MINUTE="$(normalize_int "$RAW_TARGET_MINUTE")"
COOLDOWN_SECONDS="$(normalize_int "$RAW_COOLDOWN_SECONDS")"
validate_target
log "daily wake scheduler started target=$(printf '%02d:%02d' "$TARGET_HOUR" "$TARGET_MINUTE")"

while :; do
  delay_seconds="$(seconds_until_target)"
  log "arming next morning wake delay_seconds=$delay_seconds target=$(printf '%02d:%02d' "$TARGET_HOUR" "$TARGET_MINUTE")"
  rm -f "$CHILD_PID_FILE"
  KFB_WAKE_TEST_MODE=morning KFB_ENV_FILE="$ENV_FILE" "$ROOT_DIR/one_shot_wake_test.sh" "$ROOT_DIR" "$delay_seconds" >> "$LOG_FILE" 2>&1 &
  child_pid=$!
  printf '%s\n' "$child_pid" > "$CHILD_PID_FILE"
  if wait "$child_pid"; then
    :
  else
    log "one-shot wake cycle failed"
  fi
  rm -f "$CHILD_PID_FILE"
  sleep "$COOLDOWN_SECONDS"
done
