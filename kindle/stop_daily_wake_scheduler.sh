#!/bin/sh
set -eu
PATH="/usr/sbin:/usr/bin:/sbin:/bin:${PATH:-}"

ROOT_DIR="${1:-/mnt/us/kindle-family-board}"
PID_FILE="$ROOT_DIR/cache/daily-wake.pid"
CHILD_PID_FILE="$ROOT_DIR/cache/daily-wake-child.pid"
LOG_FILE="$ROOT_DIR/cache/daily-wake.log"

mkdir -p "$ROOT_DIR/cache"

log() {
  printf '%s %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$1" >> "$LOG_FILE"
}

kill_pid_if_running() {
  candidate_pid="$1"
  label="$2"
  if [ -n "$candidate_pid" ] && kill -0 "$candidate_pid" 2>/dev/null; then
    kill "$candidate_pid" 2>/dev/null || true
    sleep 1
    if kill -0 "$candidate_pid" 2>/dev/null; then
      kill -9 "$candidate_pid" 2>/dev/null || true
    fi
    log "stopped $label pid=$candidate_pid"
  fi
}

kill_matching_cmdlines() {
  for entry in /proc/[0-9]*/cmdline; do
    [ -f "$entry" ] || continue
    candidate_pid="$(basename "$(dirname "$entry")")"
    [ "$candidate_pid" != "$$" ] || continue
    cmdline="$(tr '\000' ' ' < "$entry" 2>/dev/null || true)"
    case "$cmdline" in
      *"$ROOT_DIR/daily_wake_scheduler.sh"*|*"$ROOT_DIR/one_shot_wake_test.sh"*)
        kill_pid_if_running "$candidate_pid" "matching wake process"
        ;;
    esac
  done
}

if [ -f "$PID_FILE" ]; then
  pid="$(cat "$PID_FILE" 2>/dev/null || true)"
  kill_pid_if_running "$pid" "daily wake scheduler"
fi

if [ -f "$CHILD_PID_FILE" ]; then
  child_pid="$(cat "$CHILD_PID_FILE" 2>/dev/null || true)"
  kill_pid_if_running "$child_pid" "wake child"
fi

kill_matching_cmdlines

rm -f "$PID_FILE"
rm -f "$CHILD_PID_FILE"
