#!/usr/bin/env bash
# headersHelper for the Postman MCP server that only the postman-sync agent uses
# (agents/postman-sync.md). Claude Code runs it each time that agent connects and
# sends what it prints as HTTP headers, so the Postman API key is read from
# 1Password at that moment and never written to disk or shown in the chat.
#
# Where the key is: ~/.claude/environments/postman.json (see
# environments.example/postman.example.json), field "apiKeyRef", a 1Password
# secret reference such as op://<vault>/<item>/<field>. The field may hold the key
# alone or a note with the key in it: the first PMAK-... token is used.
#
# Claude Code gives a helper 10 seconds. On any failure this prints the reason to
# stderr and exits 1, so the server reports a failed connection instead of
# quietly falling back to a browser sign-in the agent can't complete.
set -euo pipefail

CLAUDE_DIR="${CLAUDE_CONFIG_DIR:-$HOME/.claude}"
CONFIG="$CLAUDE_DIR/environments/postman.json"

fail() {
  echo "postman-mcp-headers: $1" >&2
  exit 1
}

[ -f "$CONFIG" ] || fail "no $CONFIG; run 'update QA_Agent' to set where the Postman API key is"
command -v op >/dev/null 2>&1 || fail "1Password CLI (op) not found"

ref=$(python3 -I - "$CONFIG" <<'PY'
import json, sys
try:
    ref = json.load(open(sys.argv[1])).get("apiKeyRef", "")
except (OSError, ValueError, AttributeError):
    ref = ""
print(ref if isinstance(ref, str) and ref.startswith("op://") else "")
PY
)
[ -n "$ref" ] || fail "$CONFIG has no apiKeyRef of the form op://<vault>/<item>/<field>"

value=$(op read "$ref" 2>/dev/null) || fail "op read failed for the apiKeyRef; unlock 1Password and approve the CLI request"
key=$(printf '%s\n' "$value" | grep -oE 'PMAK-[A-Za-z0-9-]+' | head -1 || true)
[ -n "$key" ] || fail "the 1Password field holds no Postman API key (PMAK-...)"

printf '{"Authorization": "Bearer %s"}\n' "$key"
