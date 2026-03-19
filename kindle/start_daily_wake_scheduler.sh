#!/bin/sh
set -eu
PATH="/usr/sbin:/usr/bin:/sbin:/bin:${PATH:-}"

ROOT_DIR="${1:-/mnt/us/kindle-family-board}"
PID_FILE="$ROOT_DIR/cache/daily-wake.pid"
LOG_FILE="$ROOT_DIR/cache/daily-wake.log"
ENV_FILE="${KFB_ENV_FILE:-$ROOT_DIR/board.env}"

mkdir -p "$ROOT_DIR/cache"

log() {
  printf '%s %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$1" >> "$LOG_FILE"
}

if [ -f "$PID_FILE" ]; then
  existing_pid="$(cat "$PID_FILE" 2>/dev/null || true)"
  if [ -n "$existing_pid" ] && kill -0 "$existing_pid" 2>/dev/null; then
    log "daily wake scheduler already running pid=$existing_pid"
    exit 0
  fi
fi

rm -f "$PID_FILE"
/sbin/start-stop-daemon -S -b -m -p "$PID_FILE" -x /bin/sh -- -c "KFB_ENV_FILE=$ENV_FILE $ROOT_DIR/daily_wake_scheduler.sh $ROOT_DIR >/dev/null 2>&1"
log "started daily wake scheduler"
