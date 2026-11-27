#!/usr/bin/env bash
# Runs the 1Password CLI for QA_Agent, without a Touch ID prompt when it can.
#
# With the 1Password app integration, every new shell Claude starts (and every
# 10 idle minutes) asks for Touch ID again, so one API run asked 2-5 times. A
# 1Password service account doesn't ask: when the user has stored its token in
# the macOS Keychain (service "qa-agent-1password", see
# references/onepassword-publish.md, "Signing in"), this exports it for this one
# `op` call. Claude never sees the token; it only runs this script. Without a
# stored token it runs plain `op`, i.e. the app integration as before.
#
# Usage: op.sh <op arguments>   e.g. op.sh item get "Mowaamah Bruno Collection" --vault X --format json
#        op.sh --auth           prints "service-account" or "app" (no op call)
set -euo pipefail
SERVICE="${QA_AGENT_OP_KEYCHAIN_SERVICE:-qa-agent-1password}"

token=""
if [ -z "${OP_SERVICE_ACCOUNT_TOKEN:-}" ] && command -v security >/dev/null 2>&1; then
  token="$(security find-generic-password -s "$SERVICE" -w 2>/dev/null || true)"
fi

if [ "${1:-}" = "--auth" ]; then
  if [ -n "$token" ] || [ -n "${OP_SERVICE_ACCOUNT_TOKEN:-}" ]; then echo service-account; else echo app; fi
  exit 0
fi

if [ -n "$token" ]; then
  export OP_SERVICE_ACCOUNT_TOKEN="$token"
fi
unset token
exec op "$@"
