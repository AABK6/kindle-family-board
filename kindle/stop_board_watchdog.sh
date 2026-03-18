#!/bin/sh
set -eu

ROOT_DIR="${1:-/mnt/us/kindle-family-board}"
PID_FILE="$ROOT_DIR/cache/board-ss-watchdog.pid"
LOG_FILE="$ROOT_DIR/cache/board-ss-watchdog.log"
TOKEN_FILE="$ROOT_DIR/cache/board-ss-watchdog.token"

rm -f "$TOKEN_FILE"

if [ -f "$PID_FILE" ]; then
  for pid in $(cat "$PID_FILE" 2>/dev/null); do
    if ps -fp "$pid" | grep -q "board_screensaver_watchdog.sh"; then
      kill -TERM "$pid" 2>/dev/null || true
    fi
  done
  rm -f "$PID_FILE"
fi

ps | grep "board_screensaver_watchdog.sh" | grep -v grep | while read pid _; do
  kill -TERM "$pid" 2>/dev/null || true
done

printf '%s stopped board screensaver watchdog\n' "$(date '+%Y-%m-%d %H:%M:%S')" >> "$LOG_FILE"
