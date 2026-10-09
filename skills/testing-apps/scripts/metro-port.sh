#!/usr/bin/env bash
# Picks and reserves a free Metro bundler port so parallel mobile QA runs
# (two devices, two Claude sessions) never build against the same port.
#
# Usage:
#   metro-port.sh reserve [label]   # prints a free, now-reserved port
#   metro-port.sh release <port>    # frees a reservation after the run
#   metro-port.sh list              # shows current reservations
#
# A port counts as taken if anything LISTENs on it, if a running expo/metro/
# react-native process was started with it (a build can compile for minutes
# before Metro binds), or if another run has reserved it. Reservation is an
# atomic mkdir, so two agents reserving at the same moment get different ports.
#
# Env: METRO_PORT_MIN (default 8100), METRO_PORT_MAX (default 8999),
#      METRO_PORT_LOCK_DIR (default /tmp/qa-agent-metro-ports — shared by every
#      session on this Mac), METRO_PORT_TTL_HOURS (default 12; an older
#      reservation whose port is idle is treated as stale and reclaimed).
set -euo pipefail

MIN="${METRO_PORT_MIN:-8100}"
MAX="${METRO_PORT_MAX:-8999}"
LOCK_DIR="${METRO_PORT_LOCK_DIR:-/tmp/qa-agent-metro-ports}"
TTL_SECONDS=$(( ${METRO_PORT_TTL_HOURS:-12} * 3600 ))

port_in_use() {
  local p="$1"
  lsof -nP -iTCP:"$p" -sTCP:LISTEN >/dev/null 2>&1 && return 0
  ps -axo command= 2>/dev/null \
    | grep -E '(expo|metro|react-native)' \
    | grep -Eq -- "--port[= ]$p( |$)" && return 0
  return 1
}

lock_age_seconds() {
  local mtime
  mtime=$(stat -f %m "$1" 2>/dev/null || stat -c %Y "$1" 2>/dev/null || echo 0)
  echo $(( $(date +%s) - mtime ))
}

reserve() {
  local label="${1:-unlabelled}" p lock
  mkdir -p "$LOCK_DIR"
  for (( p = MIN; p <= MAX; p++ )); do
    [ "$p" -eq 8081 ] && continue   # Metro's default — left for manual dev use
    port_in_use "$p" && continue
    lock="$LOCK_DIR/$p"
    if ! mkdir "$lock" 2>/dev/null; then
      # Reclaim only a stale reservation whose port is still idle.
      [ "$(lock_age_seconds "$lock")" -lt "$TTL_SECONDS" ] && continue
      rm -rf "$lock"
      mkdir "$lock" 2>/dev/null || continue
    fi
    printf '%s\t%s\n' "$label" "$(date '+%Y-%m-%d %H:%M:%S')" > "$lock/owner"
    # Re-check after reserving: a process may have grabbed it in between.
    if port_in_use "$p"; then rm -rf "$lock"; continue; fi
    echo "$p"
    return 0
  done
  echo "No free Metro port in $MIN-$MAX" >&2
  return 1
}

release() {
  local p="${1:?port is required}"
  rm -rf "${LOCK_DIR:?}/$p"
}

list() {
  [ -d "$LOCK_DIR" ] || return 0
  local d p
  for d in "$LOCK_DIR"/*/; do
    [ -d "$d" ] || continue
    p=$(basename "$d")
    printf '%s\t%s\t%s\n' "$p" "$(cat "$d/owner" 2>/dev/null || echo '?')" \
      "$(port_in_use "$p" && echo listening || echo idle)"
  done
}

case "${1:-}" in
  reserve) reserve "${2:-}" ;;
  release) release "${2:-}" ;;
  list)    list ;;
  *) sed -n '2,10p' "$0" >&2; exit 2 ;;
esac
