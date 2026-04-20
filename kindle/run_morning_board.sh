#!/bin/sh
set -eu

ROOT_DIR="${1:-/mnt/us/kindle-family-board}"
ENV_FILE="${KFB_ENV_FILE:-$ROOT_DIR/board.env}"
LOG_FILE="$ROOT_DIR/cache/morning.log"
HOLD_SECONDS_OVERRIDE="${KFB_MORNING_HOLD_SECONDS:-}"
RUNTIME_TZ_OVERRIDE="${KFB_RUNTIME_TZ:-}"

if [ -f "$ENV_FILE" ]; then
  set -a
  . "$ENV_FILE"
  set +a
fi

if [ -n "$HOLD_SECONDS_OVERRIDE" ]; then
  KFB_MORNING_HOLD_SECONDS="$HOLD_SECONDS_OVERRIDE"
fi
if [ -n "$RUNTIME_TZ_OVERRIDE" ]; then
  KFB_RUNTIME_TZ="$RUNTIME_TZ_OVERRIDE"
fi

HOLD_SECONDS="${KFB_MORNING_HOLD_SECONDS:-10800}"
RUNTIME_TZ="${KFB_RUNTIME_TZ:-CET-1CEST,M3.5.0,M10.5.0/3}"
export TZ="$RUNTIME_TZ"
EXPECTED_RENDER_DATE="${KFB_EXPECTED_RENDER_DATE:-$(date +%F)}"

mkdir -p "$ROOT_DIR/cache" "$ROOT_DIR/linkss-state"

log() {
  printf '%s %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$1" >> "$LOG_FILE"
}

pid_matches_pattern() {
  candidate_pid="$1"
  pattern="$2"

  if [ -z "$candidate_pid" ] || [ ! -f "/proc/$candidate_pid/cmdline" ]; then
    return 1
  fi

  cmdline="$(tr '\000' ' ' < "/proc/$candidate_pid/cmdline" 2>/dev/null || true)"
  case "$cmdline" in
    *"$pattern"*)
      return 0
      ;;
  esac

  return 1
}

wait_for_worker_start() {
  pid_file="$1"
  pattern="$2"
  label="$3"
  attempt=0

  while [ "$attempt" -lt 5 ]; do
    candidate_pid="$(cat "$pid_file" 2>/dev/null || true)"
    if [ -n "$candidate_pid" ] && kill -0 "$candidate_pid" 2>/dev/null && pid_matches_pattern "$candidate_pid" "$pattern"; then
      printf '%s\n' "$candidate_pid"
      return 0
    fi
    attempt="$(( attempt + 1 ))"
    sleep 1
  done

  log "$label failed to start pid_file=$pid_file"
  return 1
}

log "starting morning board expected_render_date=$EXPECTED_RENDER_DATE"
KFB_ENV_FILE="$ENV_FILE" KFB_EXPECTED_RENDER_DATE="$EXPECTED_RENDER_DATE" "$ROOT_DIR/fetch_and_display.sh" >> "$LOG_FILE" 2>&1
log "fetch_and_display completed"

if [ ! -f "$ROOT_DIR/cache/latest.png" ]; then
  log "latest.png missing after morning update"
  exit 1
fi

"$ROOT_DIR/persist_morning_screensaver.sh" "$ROOT_DIR" "$ROOT_DIR/cache/latest.png" >> "$LOG_FILE" 2>&1 || log "morning screensaver persistence failed"
if ! "$ROOT_DIR/start_board_watchdog.sh" "$ROOT_DIR" >> "$LOG_FILE" 2>&1; then
  log "board watchdog start failed"
  exit 1
fi

if [ -x "$ROOT_DIR/stop_restore_after_delay.sh" ]; then
  "$ROOT_DIR/stop_restore_after_delay.sh" "$ROOT_DIR" >> "$LOG_FILE" 2>&1 || log "failed to stop existing restore helpers"
fi

if [ "$HOLD_SECONDS" -gt 0 ] && [ -x "$ROOT_DIR/restore_after_delay.sh" ]; then
  TOKEN="$(date +%s)"
  printf '%s\n' "$TOKEN" > "$ROOT_DIR/linkss-state/restore.token"
  rm -f "$ROOT_DIR/cache/restore.pid"
  if ! /sbin/start-stop-daemon -S -b -m -p "$ROOT_DIR/cache/restore.pid" -x /bin/sh -- \
    -c "KFB_RESTORE_TOKEN=$TOKEN $ROOT_DIR/restore_after_delay.sh $ROOT_DIR $HOLD_SECONDS >/dev/null 2>&1"; then
    log "failed to launch restore_after_delay"
    exit 1
  fi

  RESTORE_PID="$(wait_for_worker_start "$ROOT_DIR/cache/restore.pid" "$ROOT_DIR/restore_after_delay.sh" "restore_after_delay" || true)"
  if [ -z "$RESTORE_PID" ]; then
    exit 1
  fi
  log "armed restore_after_delay for $HOLD_SECONDS seconds pid=$RESTORE_PID token=$TOKEN"
fi

log "morning board finished"
