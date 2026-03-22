#!/bin/sh
set -eu
PATH="/usr/sbin:/usr/bin:/sbin:/bin:${PATH:-}"

ROOT_DIR="${1:-/mnt/us/kindle-family-board}"
ENV_FILE="${KFB_ENV_FILE:-$ROOT_DIR/board.env}"
CRON_FILE="/etc/crontab/root"
CRON_LINE="0 7 * * * TZ=CET-1CEST,M3.5.0,M10.5.0/3 KFB_ENV_FILE=$ROOT_DIR/board.env $ROOT_DIR/run_morning_board.sh $ROOT_DIR >> $ROOT_DIR/cache/cron.log 2>&1"
BACKUP_FILE="$ROOT_DIR/root.crontab.backup"
TMP_FILE="/tmp/kindle-family-board.crontab"
LOG_FILE="$ROOT_DIR/cache/boot.log"
RUNTIME_TZ_OVERRIDE="${KFB_RUNTIME_TZ:-}"
RUNTIME_TZ_FILE="$ROOT_DIR/timezone/Europe-Amsterdam.tz"
POSIX_TZ_FILE="$ROOT_DIR/timezone/TZ.posix"

if [ -f "$ENV_FILE" ]; then
  set -a
  . "$ENV_FILE"
  set +a
fi

if [ -n "$RUNTIME_TZ_OVERRIDE" ]; then
  KFB_RUNTIME_TZ="$RUNTIME_TZ_OVERRIDE"
fi

RUNTIME_TZ="${KFB_RUNTIME_TZ:-CET-1CEST,M3.5.0,M10.5.0/3}"
export TZ="$RUNTIME_TZ"
CRON_LINE="0 7 * * * TZ=$RUNTIME_TZ KFB_ENV_FILE=$ROOT_DIR/board.env $ROOT_DIR/run_morning_board.sh $ROOT_DIR >> $ROOT_DIR/cache/cron.log 2>&1"

mkdir -p "$ROOT_DIR/cache"

log() {
  printf '%s %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$1" >> "$LOG_FILE"
}

apply_timezone_mounts() {
  if [ -f "$RUNTIME_TZ_FILE" ]; then
    if mount --bind "$RUNTIME_TZ_FILE" /var/local/system/tz >/dev/null 2>&1; then
      log "bound runtime timezone file onto /var/local/system/tz"
    else
      log "failed to bind runtime timezone file"
    fi
  else
    log "runtime timezone file missing: $RUNTIME_TZ_FILE"
  fi

  if [ -f "$POSIX_TZ_FILE" ]; then
    if mount --bind "$POSIX_TZ_FILE" /etc/TZ >/dev/null 2>&1; then
      log "bound POSIX timezone file onto /etc/TZ"
    else
      log "failed to bind POSIX timezone file"
    fi
  else
    log "POSIX timezone file missing: $POSIX_TZ_FILE"
  fi
}

if [ ! -f "$CRON_FILE" ]; then
  log "missing $CRON_FILE"
  exit 1
fi

if [ ! -f "$BACKUP_FILE" ]; then
  cp "$CRON_FILE" "$BACKUP_FILE"
fi

apply_timezone_mounts

grep -v 'kindle-family-board/run_morning_board.sh' "$CRON_FILE" | grep -v 'kindle-family-board/fetch_and_display.sh' > "$TMP_FILE" || true
printf '%s\n' "$CRON_LINE" >> "$TMP_FILE"

mntroot rw >/dev/null 2>&1 || true
cat "$TMP_FILE" > "$CRON_FILE"
chmod 644 "$CRON_FILE"
mntroot ro >/dev/null 2>&1 || true
rm -f "$TMP_FILE"

/etc/init.d/cron restart >/dev/null 2>&1 || /etc/init.d/cron start >/dev/null 2>&1 || true
log "ensured cron entry in $CRON_FILE"

if [ -x "$ROOT_DIR/stop_daily_wake_scheduler.sh" ]; then
  "$ROOT_DIR/stop_daily_wake_scheduler.sh" "$ROOT_DIR" >> "$LOG_FILE" 2>&1 || log "failed to stop existing daily wake scheduler"
fi

if [ -x "$ROOT_DIR/start_daily_wake_scheduler.sh" ]; then
  KFB_ENV_FILE="$ROOT_DIR/board.env" "$ROOT_DIR/start_daily_wake_scheduler.sh" "$ROOT_DIR" >> "$LOG_FILE" 2>&1 || log "failed to start daily wake scheduler"
else
  log "start_daily_wake_scheduler.sh missing"
fi
