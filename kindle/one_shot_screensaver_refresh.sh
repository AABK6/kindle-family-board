#!/bin/sh
set -eu

ROOT_DIR="${1:-/mnt/us/kindle-family-board}"
IMAGE_PATH="${2:-$ROOT_DIR/cache/latest.png}"
LOG_FILE="$ROOT_DIR/cache/one-shot-screensaver.log"
LOCK_DIR="/var/local/run"
LOCK_FILE="$LOCK_DIR/kfb-one-shot-ss.lock"
LOCK_OWNER_FILE="$LOCK_FILE/pid"
SCRIPT_PATH="$ROOT_DIR/one_shot_screensaver_refresh.sh"
EIPS_BIN="${EIPS_BIN:-/usr/sbin/eips}"

mkdir -p "$ROOT_DIR/cache" "$LOCK_DIR"

log() {
  printf '%s %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$1" >> "$LOG_FILE"
}

pid_matches_refresh() {
  candidate_pid="$1"

  if [ -z "$candidate_pid" ] || [ ! -f "/proc/$candidate_pid/cmdline" ]; then
    return 1
  fi

  cmdline="$(tr '\000' ' ' < "/proc/$candidate_pid/cmdline" 2>/dev/null || true)"
  case "$cmdline" in
    *"$SCRIPT_PATH"*|*"one_shot_screensaver_refresh.sh"*)
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
  if [ -n "$owner_pid" ] && kill -0 "$owner_pid" 2>/dev/null && pid_matches_refresh "$owner_pid"; then
    return 1
  fi

  rm -f "$LOCK_OWNER_FILE"
  if rmdir "$LOCK_FILE" 2>/dev/null; then
    log "cleared stale one-shot lock owner=${owner_pid:-unknown}"
    return 0
  fi

  log "failed to clear stale one-shot lock owner=${owner_pid:-unknown}"
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
  exit "$status"
}

trap cleanup EXIT SIGTERM

if [ ! -f "$IMAGE_PATH" ]; then
  log "image missing: $IMAGE_PATH"
  exit 1
fi

clear_stale_lock >/dev/null 2>&1 || true

lipc-wait-event -m -s 20 com.lab126.powerd goingToScreenSaver 2>/dev/null | while read line; do
  if echo "$line" | grep -q "goingToScreenSaver"; then
    if acquire_lock; then
      sleep 2
      "$EIPS_BIN" -f -g "$IMAGE_PATH" >> "$LOG_FILE" 2>&1 || true
      release_lock
      log "refreshed one-shot screensaver image=$IMAGE_PATH"
      exit 0
    fi
  fi
done

log "one-shot screensaver refresh timed out"
