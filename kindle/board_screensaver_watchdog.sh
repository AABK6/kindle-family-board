#!/bin/sh
set -eu

ROOT_DIR="${1:-/mnt/us/kindle-family-board}"
ENV_FILE="${KFB_ENV_FILE:-$ROOT_DIR/board.env}"
PID_FILE="$ROOT_DIR/cache/board-ss-watchdog.pid"
LOG_FILE="$ROOT_DIR/cache/board-ss-watchdog.log"
TOKEN_FILE="$ROOT_DIR/cache/board-ss-watchdog.token"
LOCK_DIR="/var/local/run"
LOCK_FILE="$LOCK_DIR/kfb-board-ss.lock"
LOCK_OWNER_FILE="$LOCK_FILE/pid"
SCRIPT_PATH="$ROOT_DIR/board_screensaver_watchdog.sh"
TOKEN="${KFB_BOARD_WATCHDOG_TOKEN:-}"

if [ -f "$ENV_FILE" ]; then
  set -a
  . "$ENV_FILE"
  set +a
fi

IMAGE_PATH="${KFB_BOARD_IMAGE_PATH:-$ROOT_DIR/cache/latest.png}"
EIPS_BIN="${EIPS_BIN:-/usr/sbin/eips}"

mkdir -p "$ROOT_DIR/cache" "$LOCK_DIR"

log() {
  printf '%s %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$1" >> "$LOG_FILE"
}

if [ -z "$TOKEN" ] && [ -f "$TOKEN_FILE" ]; then
  TOKEN="$(cat "$TOKEN_FILE" 2>/dev/null || true)"
fi

token_matches() {
  if [ -z "$TOKEN" ] || [ ! -f "$TOKEN_FILE" ]; then
    return 1
  fi

  [ "$(cat "$TOKEN_FILE" 2>/dev/null)" = "$TOKEN" ]
}

pid_matches_watchdog() {
  candidate_pid="$1"

  if [ -z "$candidate_pid" ] || [ ! -f "/proc/$candidate_pid/cmdline" ]; then
    return 1
  fi

  cmdline="$(tr '\000' ' ' < "/proc/$candidate_pid/cmdline" 2>/dev/null || true)"
  case "$cmdline" in
    *"$SCRIPT_PATH"*|*"board_screensaver_watchdog.sh"*)
      return 0
      ;;
  esac

  return 1
}

release_lock() {
  if [ ! -d "$LOCK_FILE" ]; then
    return 0
  fi

  owner_pid="$(cat "$LOCK_OWNER_FILE" 2>/dev/null || true)"
  if [ -n "$owner_pid" ] && [ "$owner_pid" != "$$" ]; then
    return 0
  fi

  rm -f "$LOCK_OWNER_FILE"
  rmdir "$LOCK_FILE" 2>/dev/null || true
}

clear_stale_lock() {
  if [ ! -d "$LOCK_FILE" ]; then
    return 0
  fi

  owner_pid="$(cat "$LOCK_OWNER_FILE" 2>/dev/null || true)"
  if [ -n "$owner_pid" ] && kill -0 "$owner_pid" 2>/dev/null && pid_matches_watchdog "$owner_pid"; then
    return 1
  fi

  rm -f "$LOCK_OWNER_FILE"
  if rmdir "$LOCK_FILE" 2>/dev/null; then
    log "cleared stale screensaver lock owner=${owner_pid:-unknown}"
    return 0
  fi

  log "failed to clear stale screensaver lock owner=${owner_pid:-unknown}"
  return 1
}

acquire_lock() {
  if mkdir "$LOCK_FILE" 2>/dev/null; then
    printf '%s\n' "$$" > "$LOCK_OWNER_FILE"
    return 0
  fi

  clear_stale_lock >/dev/null 2>&1 || true
  if mkdir "$LOCK_FILE" 2>/dev/null; then
    printf '%s\n' "$$" > "$LOCK_OWNER_FILE"
    return 0
  fi

  return 1
}

cleanup() {
  status="$?"
  release_lock
  if token_matches; then
    rm -f "$PID_FILE"
  fi
  exit "$status"
}

trap cleanup EXIT SIGTERM

echo "$$" > "$PID_FILE"

if ! token_matches; then
  log "watchdog token missing before start"
  exit 0
fi

clear_stale_lock >/dev/null 2>&1 || true

while true; do
  lipc-wait-event -m -s 0 com.lab126.powerd goingToScreenSaver 2>/dev/null | while read line; do
    if echo "$line" | grep -q "goingToScreenSaver"; then
      if ! token_matches; then
        log "watchdog token cleared, exiting before redraw"
        exit 0
      fi
      if acquire_lock; then
        sleep 2
        if ! token_matches; then
          release_lock
          log "watchdog token cleared, skipping redraw"
          exit 0
        fi
        if [ -f "$IMAGE_PATH" ]; then
          "$EIPS_BIN" -f -g "$IMAGE_PATH" >> "$LOG_FILE" 2>&1 || true
          log "reapplied board image on screensaver event"
        else
          log "board image missing: $IMAGE_PATH"
        fi
        release_lock
      else
        log "screensaver redraw already in progress"
      fi
    fi
  done
  sleep 1
done
