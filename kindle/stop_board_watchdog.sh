#!/bin/sh
set -eu

ROOT_DIR="${1:-/mnt/us/kindle-family-board}"
PID_FILE="$ROOT_DIR/cache/board-ss-watchdog.pid"
LOG_FILE="$ROOT_DIR/cache/board-ss-watchdog.log"

if [ -f "$PID_FILE" ]; then
  for pid in $(cat "$PID_FILE" 2>/dev/null); do
    if ps -fp "$pid" | grep -q "board_screensaver_watchdog.sh"; then
      kill -TERM "$pid" 2>/dev/null || true
    fi
  done
  rm -f "$PID_FILE"
fi

printf '%s stopped board screensaver watchdog\n' "$(date '+%Y-%m-%d %H:%M:%S')" >> "$LOG_FILE"
