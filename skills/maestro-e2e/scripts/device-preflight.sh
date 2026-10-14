#!/usr/bin/env bash
# Finds the tools Maestro needs even when they are not on PATH, and lists what
# can run a flow: booted simulators/emulators, ones that exist but are off, and
# whether a given app id is installed. Read-only: boots and installs nothing.
#
#   device-preflight.sh [app-id]
#
# Prints `export ...` lines to prefix later commands with (JAVA_HOME,
# DEVELOPER_DIR, PATH), then the device state.
set -uo pipefail
APP_ID="${1:-}"

# --- tools ---
MAESTRO="$(command -v maestro || true)"
[ -z "$MAESTRO" ] && [ -x "$HOME/.maestro/bin/maestro" ] && MAESTRO="$HOME/.maestro/bin/maestro"

JAVA_HOME_FOUND="${JAVA_HOME:-}"
if [ -z "$JAVA_HOME_FOUND" ] || [ ! -x "$JAVA_HOME_FOUND/bin/java" ]; then
  JAVA_HOME_FOUND="$(/usr/libexec/java_home -v 17+ 2>/dev/null || true)"
  for c in /opt/homebrew/opt/openjdk@17 /opt/homebrew/opt/openjdk /usr/local/opt/openjdk@17 /usr/local/opt/openjdk; do
    [ -z "$JAVA_HOME_FOUND" ] && [ -x "$c/bin/java" ] && JAVA_HOME_FOUND="$c"
  done
fi

DEV_DIR="${DEVELOPER_DIR:-}"
if [ -z "$DEV_DIR" ] && ! xcrun --find simctl >/dev/null 2>&1; then
  [ -d /Applications/Xcode.app/Contents/Developer ] && DEV_DIR=/Applications/Xcode.app/Contents/Developer
fi

SDK="${ANDROID_HOME:-${ANDROID_SDK_ROOT:-$HOME/Library/Android/sdk}}"
ADB="$(command -v adb || true)"; [ -z "$ADB" ] && [ -x "$SDK/platform-tools/adb" ] && ADB="$SDK/platform-tools/adb"
EMULATOR="$(command -v emulator || true)"; [ -z "$EMULATOR" ] && [ -x "$SDK/emulator/emulator" ] && EMULATOR="$SDK/emulator/emulator"

echo "== env (prefix maestro/simctl/adb commands with these) =="
[ -n "$JAVA_HOME_FOUND" ] && echo "export JAVA_HOME=$JAVA_HOME_FOUND"
[ -n "$DEV_DIR" ] && echo "export DEVELOPER_DIR=$DEV_DIR"
P=""
[ -n "$MAESTRO" ] && P="$(dirname "$MAESTRO")"
[ -n "$JAVA_HOME_FOUND" ] && P="$P:$JAVA_HOME_FOUND/bin"
[ -n "$ADB" ] && P="$P:$(dirname "$ADB")"
[ -n "$EMULATOR" ] && P="$P:$(dirname "$EMULATOR")"
echo "export PATH=${P#:}:\$PATH"

echo "== tools =="
echo "maestro:  ${MAESTRO:-MISSING (brew install mobile-dev-inc/tap/maestro)}"
echo "java17+:  ${JAVA_HOME_FOUND:-MISSING (brew install openjdk@17)}"
SIMCTL_OK=no
DEVELOPER_DIR="$DEV_DIR" xcrun simctl help >/dev/null 2>&1 && SIMCTL_OK=yes
echo "simctl:   $SIMCTL_OK${DEV_DIR:+ (via DEVELOPER_DIR)}"
echo "adb:      ${ADB:-MISSING}"
echo "emulator: ${EMULATOR:-MISSING}"
[ -n "$JAVA_HOME_FOUND" ] && [ -n "$MAESTRO" ] && echo "maestro version: $(JAVA_HOME=$JAVA_HOME_FOUND "$MAESTRO" --version 2>/dev/null | tail -1)"

echo "== iOS simulators =="
if [ "$SIMCTL_OK" = yes ]; then
  echo "booted:"
  DEVELOPER_DIR="$DEV_DIR" xcrun simctl list devices booted | grep -E '\(Booted\)' | sed 's/^ */  /' || echo "  none"
  echo "available (shut down):"
  DEVELOPER_DIR="$DEV_DIR" xcrun simctl list devices available | grep -E '\(Shutdown\)' | grep -iE 'iphone|ipad' | sed 's/^ */  /' || echo "  none (no simulator or no iOS runtime installed: Xcode > Settings > Components)"
  if [ -n "$APP_ID" ]; then
    for udid in $(DEVELOPER_DIR="$DEV_DIR" xcrun simctl list devices booted | grep -oE '[0-9A-F-]{36}'); do
      if DEVELOPER_DIR="$DEV_DIR" xcrun simctl get_app_container "$udid" "$APP_ID" >/dev/null 2>&1; then
        echo "  $APP_ID installed on $udid"
      else
        echo "  $APP_ID NOT installed on $udid"
      fi
    done
  fi
fi

echo "== Android =="
if [ -n "$ADB" ]; then
  echo "running:"
  "$ADB" devices | tail -n +2 | grep -v '^$' | sed 's/^/  /' || echo "  none"
  if [ -n "$APP_ID" ]; then
    for serial in $("$ADB" devices | tail -n +2 | awk '$2=="device"{print $1}'); do
      if "$ADB" -s "$serial" shell pm list packages "$APP_ID" 2>/dev/null | grep -qx "package:$APP_ID"; then
        echo "  $APP_ID installed on $serial"
      else
        echo "  $APP_ID NOT installed on $serial"
      fi
    done
  fi
fi
if [ -n "$EMULATOR" ]; then
  echo "AVDs:"
  "$EMULATOR" -list-avds 2>/dev/null | sed 's/^/  /'
fi
