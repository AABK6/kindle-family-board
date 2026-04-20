#!/bin/sh
set -eu

ROOT_DIR="${1:-/mnt/us/kindle-family-board}"
PID_FILE="$ROOT_DIR/cache/board-ss-watchdog.pid"
LOG_FILE="$ROOT_DIR/cache/board-ss-watchdog.log"
TOKEN_FILE="$ROOT_DIR/cache/board-ss-watchdog.token"

mkdir -p "$ROOT_DIR/cache"

log() {
  printf '%s %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$1" >> "$LOG_FILE"
}

watchdog_pid_matches() {
  candidate_pid="$1"

  if [ -z "$candidate_pid" ] || [ ! -f "/proc/$candidate_pid/cmdline" ]; then
    return 1
  fi

  cmdline="$(tr '\000' ' ' < "/proc/$candidate_pid/cmdline" 2>/dev/null || true)"
  case "$cmdline" in
    *"$ROOT_DIR/board_screensaver_watchdog.sh"*|*"board_screensaver_watchdog.sh"*)
      return 0
      ;;
  esac

  return 1
}

current_watchdog_pid() {
  candidate_pid="$(cat "$PID_FILE" 2>/dev/null || true)"
  if [ -n "$candidate_pid" ] && kill -0 "$candidate_pid" 2>/dev/null && watchdog_pid_matches "$candidate_pid"; then
    printf '%s\n' "$candidate_pid"
    return 0
  fi

  return 1
}

"$ROOT_DIR/stop_board_watchdog.sh" "$ROOT_DIR" >/dev/null 2>&1 || true

if [ -f "$PID_FILE" ]; then
  for pid in $(cat "$PID_FILE" 2>/dev/null); do
    if ps -fp "$pid" | grep -q "board_screensaver_watchdog.sh"; then
      exit 0
    fi
  done
  rm -f "$PID_FILE"
fi

TOKEN="$(date +%s)-$$"
printf '%s\n' "$TOKEN" > "$TOKEN_FILE"

if ! /sbin/start-stop-daemon -S -b -m -p "$PID_FILE" -x "$ROOT_DIR/board_screensaver_watchdog.sh" -- "$ROOT_DIR"; then
  log "failed to launch board screensaver watchdog"
  exit 1
fi

attempt=0
while [ "$attempt" -lt 5 ]; do
  WATCHDOG_PID="$(current_watchdog_pid || true)"
  if [ -n "$WATCHDOG_PID" ]; then
    log "started board screensaver watchdog pid=$WATCHDOG_PID token=$TOKEN"
    exit 0
  fi
  attempt="$(( attempt + 1 ))"
  sleep 1
done

rm -f "$PID_FILE"
log "board screensaver watchdog failed to stay running token=$TOKEN"
exit 1
