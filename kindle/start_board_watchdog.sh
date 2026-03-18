#!/bin/sh
set -eu

ROOT_DIR="${1:-/mnt/us/kindle-family-board}"
PID_FILE="$ROOT_DIR/cache/board-ss-watchdog.pid"
LOG_FILE="$ROOT_DIR/cache/board-ss-watchdog.log"
TOKEN_FILE="$ROOT_DIR/cache/board-ss-watchdog.token"

mkdir -p "$ROOT_DIR/cache"

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

/sbin/start-stop-daemon -S -b -m -p "$PID_FILE" -x /bin/sh -- \
  -c "KFB_ENV_FILE=$ROOT_DIR/board.env KFB_BOARD_WATCHDOG_TOKEN=$TOKEN $ROOT_DIR/board_screensaver_watchdog.sh $ROOT_DIR >/dev/null 2>&1"

printf '%s started board screensaver watchdog\n' "$(date '+%Y-%m-%d %H:%M:%S')" >> "$LOG_FILE"
